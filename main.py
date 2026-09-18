"""ICU Early Warning System: FastAPI server, late-fusion engine, deterministic safety override."""
import logging
import math
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from model_2 import load_xray_model, predict_ecg_risk, predict_xray_risk
from model_1 import load_sepsis_model, run_sepsis_inference

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("icu.main")

DATA_DIR = Path(__file__).parent / "data"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
PATIENT_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")

W_SEPSIS, W_ECG, W_XRAY, BIAS = 2.45, 1.82, 1.15, -2.10
OVERRIDE_FLOOR = 0.94
STATUS_CRITICAL = "CRITICAL - IMMEDIATE INTERVENTION REQUIRED"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading models...")
    app.state.sepsis_model = await run_in_threadpool(load_sepsis_model)
    app.state.xray_model = await run_in_threadpool(load_xray_model)
    logger.info("Models ready.")
    yield
    app.state.sepsis_model = None
    app.state.xray_model = None

app = FastAPI(title="Multi-Modal ICU Early Warning System", version="1.0.0", lifespan=lifespan)

# Enable CORS for Streamlit / Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MissingDataFlags(BaseModel):
    xray_imputed: bool
    ecg_imputed: bool

class ModalityBreakdown(BaseModel):
    sepsis_temporal_risk: float
    ecg_telemetry_risk: float
    xray_opacity_score: float

class SepsisHorizons(BaseModel):
    risk_3h: float
    risk_6h: float
    risk_12h: float
    sepsis_score_100: float

class AssessmentResponse(BaseModel):
    patient_id: str
    unified_emergency_index: float
    status: str
    safety_override_triggered: bool
    missing_data_flags: MissingDataFlags
    modality_breakdown: ModalityBreakdown
    sepsis_horizons: SepsisHorizons

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

async def _read_upload(f: Optional[UploadFile]) -> Optional[bytes]:
    if f is None or not f.filename:
        return None
    data = await f.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"{f.filename} exceeds size limit.")
    return data or None

@app.get("/health")
async def health():
    return {"status": "ok", "models_loaded": app.state.sepsis_model is not None}

@app.post("/api/patient-assessment", response_model=AssessmentResponse)
async def patient_assessment(
    patient_id: str = Form(...),
    xray_file: Optional[UploadFile] = File(None),
    ecg_file: Optional[UploadFile] = File(None),
):
    if not PATIENT_ID_RE.match(patient_id):
        raise HTTPException(status_code=422, detail="Invalid patient_id.")
    csv_path = DATA_DIR / f"{patient_id}.csv"
    if not csv_path.is_file():
        raise HTTPException(status_code=404, detail=f"No tabular data for patient '{patient_id}'.")

    xray_bytes = await _read_upload(xray_file)
    ecg_bytes = await _read_upload(ecg_file)

    try:
        sepsis = await run_in_threadpool(run_sepsis_inference, str(csv_path), app.state.sepsis_model)
    except Exception as exc:
        logger.exception("Sepsis inference failed")
        raise HTTPException(status_code=422, detail=f"Unusable patient data: {exc}")

    ecg = await run_in_threadpool(predict_ecg_risk, ecg_bytes)
    xray = await run_in_threadpool(predict_xray_risk, xray_bytes, app.state.xray_model)

    logit = W_SEPSIS * sepsis["risk_3h"] + W_ECG * ecg["score"] + W_XRAY * xray["score"] + BIAS
    edi = _sigmoid(logit)
    risk_3h = sepsis["risk_3h"]
    status = None
    override = False

    hr, map_ = sepsis["latest_hr"], sepsis["latest_map"]
    if (hr is not None and hr > 120) or (map_ is not None and map_ < 55):
        override = True
        risk_3h = max(risk_3h, OVERRIDE_FLOOR)
        edi = max(edi, OVERRIDE_FLOOR)
        status = STATUS_CRITICAL
    if status is None:
        status = ("HIGH RISK - URGENT CLINICAL REVIEW" if edi >= 0.75
                  else "ELEVATED RISK - CLOSE MONITORING" if edi >= 0.50
                  else "STABLE - ROUTINE MONITORING")

    return AssessmentResponse(
        patient_id=patient_id,
        unified_emergency_index=round(edi, 3),
        status=status,
        safety_override_triggered=override,
        missing_data_flags=MissingDataFlags(xray_imputed=bool(xray["imputed"]), ecg_imputed=bool(ecg["imputed"])),
        modality_breakdown=ModalityBreakdown(
            sepsis_temporal_risk=round(risk_3h, 3),
            ecg_telemetry_risk=round(ecg["score"], 3),
            xray_opacity_score=round(xray["score"], 3)),
        sepsis_horizons=SepsisHorizons(
            risk_3h=round(risk_3h, 3),
            risk_6h=round(sepsis["risk_6h"], 3),
            risk_12h=round(sepsis["risk_12h"], 3),
            sepsis_score_100=round(risk_3h * 100.0, 1)),
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
