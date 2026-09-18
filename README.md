# Team Epoch
CardioPulmo-Sepsis AI is a real-time multi-modal emergency triage system that fuses 1D ECG telemetry, 2D chest radiographs, and continuous patient vitals. It drives a late-fusion architecture to predict systemic sepsis and organ deterioration cascades hours before clinical failure.
Datasets used: 
Sepsis(Model 1): https://www.kaggle.com/datasets/tea340yashjoshi/sepsis-prediction-dataset?resource=download
ECG/XRay (Model 2): Provided dataset by TAM Club

========================================================================================
                           MASTER MULTI-MODAL PIPELINE ARCHITECTURE
========================================================================================

 [ STREAM 1: IMAGING & TELEMETRY MODALITIES ]          [ STREAM 2: CLINICAL VITALS MODALITY ]
 -------------------------------------------          --------------------------------------
┌──────────────────────────────────────────┐        ┌──────────────────────────────────────┐
│ 1. Local Data Directories                │        │ 1. Raw Clinical Data (CSV)           │
│    • ECG Signals / MLII (.mat files)     │        │    • Patient Vitals & Labs           │
│    • NORMAL X-Rays                       │        │      (HR, Temp, MAP, Lactate, etc.)  │
└────────────────────┬─────────────────────┘        └──────────────────┬───────────────────┘
                     │                                                 │
                     ▼                                                 ▼
┌──────────────────────────────────────────┐        ┌──────────────────────────────────────┐
│ 2. Execution Entry Point (__main__)      │        │ 2. Preprocessing & Imputation Layer  │
│    • Part 1: Single Patient Simulation   │        │    • Forward/Backward Fill Impute    │
│    • Part 2: Batch Metrics Evaluation    │        │    • Binary Missingness Masks        │
│    • Part 3: Continuous ICU Monitor Loop │        │ 3. Time-Series Sequence Builder      │
└────────────────────┬─────────────────────┘        └──────────────────┬───────────────────┘
                     │                                                 │
                     ▼                                                 ▼
┌──────────────────────────────────────────┐        ┌──────────────────────────────────────┐
│ 4. Modality Inference Engine             │        │ 4. PyTorch Temporal GRU Model        │
│    • 20s Window RMSSD (ECG Risk)         │        │    • 2-Layer Gated Recurrent Unit    │
│    • MobileNetV3 (X-Ray Opacity Score)   │        │    • Multi-Horizon Prediction Heads  │
│    • Volumetric Extractor (Lesion Vol)   │        │      (+3h, +6h, +12h Sepsis Risk)    │
└────────────────────┬─────────────────────┘        └──────────────────┬───────────────────┘
                     │                                                 │
                     ▼                                                 ▼
┌──────────────────────────────────────────┐        ┌──────────────────────────────────────┐
│ Auxiliary JSON Payload                   │        │ Sepsis API Response                  │
│ {'ecg_risk': float,                      │        │ {'sepsis_score': float,              │
│  'xray_opacity': float,                  │        │  'risk_3h': float,                   │
│  'lesion_volume': float}                 │        │  'risk_6h': float,                   │
└────────────────────┬─────────────────────┘        │  'risk_12h': float}                  │
                     │                              └──────────────────┬───────────────────┘
                     │                                                 │
                     └────────────────────────┬────────────────────────┘
                                              │
                                              ▼
                      ┌────────────────────────────────────────────────────┐
                      │         5. UNIFIED LATE-FUSION AGGREGATOR          │
                      │  Combines all independent modality risk scores     │
                      │  to compute the Emergency Deterioration Index      │
                      └───────────────────────┬────────────────────────────┘
                                              │
                                              ▼
                      ┌────────────────────────────────────────────────────┤
                      │           6. READY FOR BACKEND & JUDGES            │
                      │   (FastAPI Endpoints & 10-Min Live ICU Monitor)    │
                      └────────────────────────────────────────────────────┘
