import streamlit as st
import plotly.graph_objects as go
import requests
import json
import math
from datetime import datetime, timezone

# ─────────────────────────────────────────────
#  PAGE CONFIG (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="EPOCH | Command Center",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS — Cyber-Medical Aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0B0F19 !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

[data-testid="stAppViewContainer"] > .main > .block-container {
    padding: 1rem 1.2rem !important;
    max-width: 100% !important;
}

[data-testid="column"] { padding: 0 0.25rem !important; }

.cp-navbar {
    display: flex; align-items: center; justify-content: space-between;
    background: #0D1220; border-bottom: 1px solid #1E293B;
    padding: 0.5rem 1rem; margin: -1rem -1.2rem 1rem -1.2rem;
}
.cp-navbar-brand {
    font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600;
    color: #00F2FE; letter-spacing: 0.04em; text-shadow: 0 0 12px rgba(0,242,254,0.5);
}
.cp-navbar-brand span { color: #64748B; font-weight: 400; margin: 0 6px; }

.cp-card {
    background: #131B2E; border: 1px solid #1E293B; border-radius: 8px;
    padding: 0.75rem 0.9rem; height: 100%;
}
.cp-card-label {
    font-size: 10px; font-weight: 600; color: #94A3B8; letter-spacing: 0.1em;
    text-transform: uppercase; margin-bottom: 0.35rem;
}
.cp-hero-score {
    font-family: 'JetBrains Mono', monospace; font-size: 48px; font-weight: 700;
    color: #EF4444; line-height: 1;
}
.cp-status-pill {
    display: inline-flex; align-items: center; border-radius: 4px; padding: 2px 9px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-left: 10px;
}
.pill-critical { background: rgba(239,68,68,0.18); border: 1px solid rgba(239,68,68,0.45); color: #EF4444; }
.pill-warning  { background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.4); color: #F59E0B; }
.pill-stable   { background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.35); color: #10B981; }
.pill-pending  { background: rgba(100,116,139,0.18); border: 1px solid rgba(100,116,139,0.45); color: #94A3B8; }

.safety-banner {
    background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.5);
    border-radius: 8px; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;
}
.cp-ts { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #64748B; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "scenario" not in st.session_state: st.session_state.scenario = "Normal Baseline"
if "hour" not in st.session_state: st.session_state.hour = 24

# ─────────────────────────────────────────────
#  VITALS CHART GENERATION (Visual Mock for Timeline Scrubber)
# ─────────────────────────────────────────────
def generate_vitals(scenario_name: str):
    pts = []
    for h in range(37):
        hr, map_val = 72, 85
        if scenario_name == "Gradual High Risk":
            hr = 72 + (h / 36) * 43 + (math.sin(h * 0.8) * 3)
            map_val = 85 - (h / 36) * 25 + (math.sin(h * 0.6) * 2)
        elif scenario_name == "Acute Spike":
            if h < 24:
                hr = 74 + math.sin(h * 0.5) * 4; map_val = 84 + math.sin(h * 0.4) * 3
            elif h < 29:
                hr = 74 + (h - 24) * 6 + math.sin(h * 0.8) * 3; map_val = 84 - (h - 24) * 4 + math.sin(h * 0.6) * 2
            elif h < 32:
                hr = 104 + (h - 29) * 12 + math.sin(h * 1.2) * 5; map_val = 68 - (h - 29) * 7 + math.sin(h * 0.9) * 3
            else:
                hr = 142 - (h - 32) * 1.5 + math.sin(h * 0.7) * 4; map_val = 47 + (h - 32) * 1 + math.sin(h * 0.5) * 2
        else:
            hr = 72 + math.sin(h * 0.4) * 4; map_val = 85 + math.sin(h * 0.3) * 3
        pts.append({"hour": h, "hr": round(hr), "map": round(map_val)})
    return pts

def send_assessment_to_backend(scenario_name: str, xray_upload=None, ecg_upload=None):
    id_map = {"Normal Baseline": "normal", "Gradual High Risk": "high_risk", "Acute Spike": "spike"}
    pid = id_map.get(scenario_name, "normal")
    url = "http://127.0.0.1:8000/api/patient-assessment"
    
    files = {}
    if xray_upload is not None: files["xray_file"] = (xray_upload.name, xray_upload.getvalue(), xray_upload.type)
    if ecg_upload is not None: files["ecg_file"] = (ecg_upload.name, ecg_upload.getvalue(), ecg_upload.type)
        
    try:
        response = requests.post(url, data={"patient_id": pid}, files=files if files else None, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, f"Server Error ({response.status_code}): {response.text}"
    except Exception as e:
        return False, str(e)

vitals_data = generate_vitals(st.session_state.scenario)
current_vitals = vitals_data[st.session_state.hour] if st.session_state.hour < len(vitals_data) else vitals_data[-1]
visible_vitals = vitals_data[:st.session_state.hour + 1]
now_ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

# ─────────────────────────────────────────────
#  TOP NAVBAR & CONTROLS
# ─────────────────────────────────────────────
st.markdown(f"""<div class="cp-navbar"><div class="cp-navbar-brand">EPOCH <span>|</span> ICU Command Center</div><div style="display:flex;align-items:center;gap:14px;"><span class="cp-ts">{now_ts}</span><div style="font-family:'JetBrains Mono';font-size:11px;color:#00F2FE;">PATIENT: ICU-2047-F (58F)</div></div></div>""", unsafe_allow_html=True)

col_ctrl1, col_ctrl2 = st.columns([0.4, 0.6], gap="small")
with col_ctrl1:
    st.session_state.scenario = st.selectbox("Simulation Scenario", ["Normal Baseline", "Gradual High Risk", "Acute Spike"], index=["Normal Baseline", "Gradual High Risk", "Acute Spike"].index(st.session_state.scenario), label_visibility="collapsed")
with col_ctrl2:
    st.session_state.hour = st.slider("Timeline Scrubber (Hours 0–36)", min_value=0, max_value=36, value=st.session_state.hour, label_visibility="collapsed")

st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  REAL-TIME BACKEND SYNC (Executes automatically)
# ─────────────────────────────────────────────
banner_placeholder = st.empty()
col_hero_l, col_hero_r = st.columns([0.65, 0.35], gap="small")

# Render right column first to gather file uploads before hitting the backend
with col_hero_r:
    st.markdown("""<div class="cp-card"><div class="cp-card-label">Multi-Modal Assessment & Sync</div>""", unsafe_allow_html=True)
    uploaded_xray = st.file_uploader("Upload X-Ray / DICOM", type=["png", "jpg", "jpeg", "dcm"], key="xray_up")
    uploaded_ecg = st.file_uploader("Upload ECG (.mat)", type=["mat"], key="ecg_up")
    
    # 🔥 AUTOMATIC API CALL: Triggers seamlessly on any UI interaction 🔥
    success, res_data = send_assessment_to_backend(st.session_state.scenario, uploaded_xray, uploaded_ecg)
    st.markdown("</div>", unsafe_allow_html=True)

# Parse real data directly from backend
edi, is_critical, sepsis_3h, sepsis_6h, sepsis_12h = 0.0, False, 0.0, 0.0, 0.0
edi_label, edi_color, pill_class = "ERROR/OFFLINE", "#94A3B8", "pill-pending"

if success and res_data:
    edi = res_data.get("unified_emergency_index", 0.0)
    is_critical = res_data.get("safety_override_triggered", False)
    if "sepsis_horizons" in res_data:
        sepsis_3h = res_data["sepsis_horizons"].get("risk_3h", 0.0)
        sepsis_6h = res_data["sepsis_horizons"].get("risk_6h", 0.0)
        sepsis_12h = res_data["sepsis_horizons"].get("risk_12h", 0.0)
        
    edi_color = "#10B981" if edi < 0.4 else "#F59E0B" if edi < 0.7 else "#EF4444"
    edi_label = "STABLE" if edi < 0.4 else "WARNING" if edi < 0.7 else "CRITICAL"
    pill_class = 'pill-critical' if edi >= 0.7 else 'pill-warning' if edi >= 0.4 else 'pill-stable'

# Render Banner
with banner_placeholder:
    if is_critical or current_vitals["hr"] > 120 or current_vitals["map"] < 55:
        breaches = []
        if current_vitals["hr"] > 120: breaches.append(f"HR > 120 (current: {current_vitals['hr']} bpm)")
        if current_vitals["map"] < 55: breaches.append(f"MAP < 55 (current: {current_vitals['map']} mmHg)")
        if is_critical and not breaches: breaches.append("Triggered by Backend AI Engine")
        breach_str = " · ".join(breaches)
        st.markdown(f"""<div class="safety-banner"><span style="font-size: 20px;">⚠️</span><div><div style="font-size: 13px; font-weight: 700; color: #EF4444;">DETERMINISTIC SAFETY OVERRIDE ACTIVE</div><div style="font-size: 11px; font-family: 'JetBrains Mono'; color: #FCA5A5;">Vital threshold breached — {breach_str}</div></div></div>""", unsafe_allow_html=True)

# Render Left Hero Column
with col_hero_l:
    st.markdown(f"""<div class="cp-card" style="border-left: 3px solid {edi_color}; display: flex; justify-content: space-between; align-items: center;"><div><div class="cp-card-label">Unified Emergency Deterioration Index (EDI)</div><div style="display:flex;align-items:baseline;gap:8px;margin-top:4px;"><div class="cp-hero-score" style="color: {edi_color};">{edi:.3f}</div><span class="cp-status-pill {pill_class}">{edi_label}</span></div><div style="font-size: 11px; color: #64748B; margin-top: 8px; font-family:'JetBrains Mono';">Source: <span style="color: #00F2FE;">Real-Time Backend Inference</span></div></div><div style="text-align: right; padding-right: 1rem; border-left: 1px solid #1E293B; padding-left: 1.5rem;"><div class="cp-card-label">Overall EDI Status</div><div style="font-family:'JetBrains Mono';font-size:16px;font-weight:700;color:{edi_color}; margin-top: 8px;">{edi_label}</div></div></div>""", unsafe_allow_html=True)

st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TEMPORAL SEPSIS HORIZONS ROW (3H, 6H, 12H)
# ─────────────────────────────────────────────
h_col1, h_col2, h_col3 = st.columns(3, gap="small")
def get_horizon_color(val): return '#64748B' if not success else '#EF4444' if val > 0.7 else '#F59E0B' if val > 0.4 else '#10B981'

with h_col1:
    c = get_horizon_color(sepsis_3h)
    st.markdown(f"""<div class="cp-card" style="border-top: 2px solid {c}; text-align: center;"><div class="cp-card-label">3-Hour Sepsis Risk</div><div style="font-family:'JetBrains Mono';font-size:24px;font-weight:700;color:{c};">{sepsis_3h:.3f}</div><div style="font-size: 10px; color: #64748B; margin-top: 4px;">Immediate Horizon</div></div>""", unsafe_allow_html=True)
with h_col2:
    c = get_horizon_color(sepsis_6h)
    st.markdown(f"""<div class="cp-card" style="border-top: 2px solid {c}; text-align: center;"><div class="cp-card-label">6-Hour Sepsis Risk</div><div style="font-family:'JetBrains Mono';font-size:24px;font-weight:700;color:{c};">{sepsis_6h:.3f}</div><div style="font-size: 10px; color: #64748B; margin-top: 4px;">Mid-Term Horizon</div></div>""", unsafe_allow_html=True)
with h_col3:
    c = get_horizon_color(sepsis_12h)
    st.markdown(f"""<div class="cp-card" style="border-top: 2px solid {c}; text-align: center;"><div class="cp-card-label">12-Hour Sepsis Risk</div><div style="font-family:'JetBrains Mono';font-size:24px;font-weight:700;color:{c};">{sepsis_12h:.3f}</div><div style="font-size: 10px; color: #64748B; margin-top: 4px;">Long-Term Horizon</div></div>""", unsafe_allow_html=True)

st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  VITAL CARDS ROW
# ─────────────────────────────────────────────
v_col1, v_col2, v_col3, v_col4 = st.columns(4, gap="small")

with v_col1: st.markdown(f"""<div class="cp-card" style="border-left: 2px solid {'#EF4444' if current_vitals["hr"] > 120 else '#00F2FE'};"><div class="cp-card-label">Heart Rate</div><div style="font-family:'JetBrains Mono';font-size:26px;font-weight:700;color:{'#EF4444' if current_vitals["hr"] > 120 else '#00F2FE'};">{current_vitals['hr']} <span style="font-size:12px;color:#64748B;">bpm</span></div><div style="font-size:10px;color:{'#F87171' if current_vitals["hr"] > 120 else '#64748B'};margin-top:2px;">{'▲ TACHYCARDIA' if current_vitals["hr"] > 120 else 'Normal sinus'}</div></div>""", unsafe_allow_html=True)
with v_col2: st.markdown(f"""<div class="cp-card" style="border-left: 2px solid {'#EF4444' if current_vitals["map"] < 55 else '#A855F7'};"><div class="cp-card-label">Mean Arterial Pressure</div><div style="font-family:'JetBrains Mono';font-size:26px;font-weight:700;color:{'#EF4444' if current_vitals["map"] < 55 else '#A855F7'};">{current_vitals['map']} <span style="font-size:12px;color:#64748B;">mmHg</span></div><div style="font-size:10px;color:{'#F87171' if current_vitals["map"] < 55 else '#64748B'};margin-top:2px;">{'▼ HYPOTENSION' if current_vitals["map"] < 55 else 'Adequate perfusion'}</div></div>""", unsafe_allow_html=True)
with v_col3: st.markdown(f"""<div class="cp-card" style="border-left: 2px solid {'#EF4444' if is_critical else '#10B981'};"><div class="cp-card-label">Blood Oxygen (SpO₂)</div><div style="font-family:'JetBrains Mono';font-size:26px;font-weight:700;color:{'#EF4444' if is_critical else '#10B981'};">{91 if is_critical else 98} <span style="font-size:12px;color:#64748B;">%</span></div><div style="font-size:10px;color:#64748B;margin-top:2px;">{'Desaturation flag' if is_critical else 'Stable'}</div></div>""", unsafe_allow_html=True)
with v_col4: st.markdown(f"""<div class="cp-card" style="border-left: 2px solid {'#F59E0B' if is_critical else '#00F2FE'};"><div class="cp-card-label">Core Temperature</div><div style="font-family:'JetBrains Mono';font-size:26px;font-weight:700;color:{'#F59E0B' if is_critical else '#00F2FE'};">{38.9 if is_critical else 36.8} <span style="font-size:12px;color:#64748B;">°C</span></div><div style="font-size:10px;color:#64748B;margin-top:2px;">{'▲ FEBRILE' if is_critical else 'Normothermic'}</div></div>""", unsafe_allow_html=True)

st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ANALYTICS CHARTS ROW (HR & MAP Trend Lines)
# ─────────────────────────────────────────────
col_chart_l, col_chart_r = st.columns(2, gap="small")
with col_chart_l:
    st.markdown("""<div class="cp-card"><div class="cp-card-label">Heart Rate Trend (36h)</div>""", unsafe_allow_html=True)
    fig_hr = go.Figure()
    fig_hr.add_trace(go.Scatter(x=[p["hour"] for p in visible_vitals], y=[p["hr"] for p in visible_vitals], mode="lines", line=dict(color="#EF4444" if current_vitals["hr"] > 120 else "#00F2FE", width=2.5)))
    fig_hr.add_hline(y=120, line=dict(color="rgba(239,68,68,0.4)", dash="dot"))
    fig_hr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0B0F19", margin=dict(l=25, r=10, t=10, b=20), height=140, font=dict(family="JetBrains Mono", size=9, color="#64748B"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1A2236", range=[40, 160]))
    st.plotly_chart(fig_hr, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with col_chart_r:
    st.markdown("""<div class="cp-card"><div class="cp-card-label">Mean Arterial Pressure Trend (36h)</div>""", unsafe_allow_html=True)
    fig_map = go.Figure()
    fig_map.add_trace(go.Scatter(x=[p["hour"] for p in visible_vitals], y=[p["map"] for p in visible_vitals], mode="lines", line=dict(color="#EF4444" if current_vitals["map"] < 55 else "#A855F7", width=2.5)))
    fig_map.add_hline(y=55, line=dict(color="rgba(239,68,68,0.4)", dash="dot"))
    fig_map.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0B0F19", margin=dict(l=25, r=10, t=10, b=20), height=140, font=dict(family="JetBrains Mono", size=9, color="#64748B"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1A2236", range=[30, 110]))
    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  BACKEND SYNC LOGS
# ─────────────────────────────────────────────
if success and res_data:
    st.success(f"Backend Sync Successful | Status: {res_data.get('status')}")
    st.json({"Modality Breakdown": res_data.get("modality_breakdown", {}), "Sepsis Horizons": res_data.get("sepsis_horizons", {})})
elif not success:
    st.error(res_data)
