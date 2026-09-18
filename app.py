"""
EPOCH | Command Center
High-density single-screen dashboard with dark cyber-medical aesthetic.
"""

import streamlit as st
import plotly.graph_objects as go
import requests
import json
import random
import time
from datetime import datetime

# ─────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="EPOCH | Command Center",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS  — zero-scroll viewport lock
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & viewport lock ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0B0F19 !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
    overflow: hidden !important;
    height: 100vh !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]        { display: none !important; }

/* Crush default padding */
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding: 0 0.6rem 0 0.6rem !important;
    max-width: 100% !important;
    height: 100vh !important;
    overflow: hidden !important;
}

/* Column gaps */
[data-testid="column"] { padding: 0 0.25rem !important; }

/* Element spacing */
div.element-container { margin-bottom: 0 !important; }
div.stMarkdown { margin: 0 !important; }

/* ── Top Navbar ── */
.cp-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #0D1220;
    border-bottom: 1px solid #1E293B;
    padding: 0.35rem 1rem;
    margin: 0 -0.6rem 0.4rem -0.6rem;
    position: sticky;
    top: 0;
    z-index: 999;
}
.cp-navbar-brand {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 600;
    color: #00F2FE;
    letter-spacing: 0.04em;
    text-shadow: 0 0 12px rgba(0,242,254,0.5);
}
.cp-navbar-brand span {
    color: #64748B;
    font-weight: 400;
    margin: 0 6px;
}
.cp-live-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.35);
    border-radius: 20px;
    padding: 2px 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    color: #10B981;
    letter-spacing: 0.08em;
    text-shadow: 0 0 8px rgba(16,185,129,0.6);
    box-shadow: 0 0 12px rgba(16,185,129,0.15);
}
.cp-live-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #10B981;
    animation: pulse-green 1.5s infinite;
}
@keyframes pulse-green {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16,185,129,0.6); }
    50%       { opacity: 0.7; box-shadow: 0 0 0 4px rgba(16,185,129,0); }
}

/* ── Generic card ── */
.cp-card {
    background: #131B2E;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
    height: 100%;
}
.cp-card-label {
    font-size: 10px;
    font-weight: 600;
    color: #94A3B8;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.cp-card-label::before {
    content: '';
    display: inline-block;
    width: 2px; height: 10px;
    border-radius: 1px;
}
.accent-green::before  { background: #10B981; }
.accent-amber::before  { background: #F59E0B; }
.accent-red::before    { background: #EF4444; }
.accent-cyan::before   { background: #00F2FE; }
.accent-purple::before { background: #A855F7; }

/* ── Hero – risk score ── */
.cp-hero-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 62px;
    font-weight: 700;
    color: #EF4444;
    line-height: 1;
    text-shadow: 0 0 30px rgba(239,68,68,0.55);
    letter-spacing: -0.02em;
}
.cp-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border-radius: 4px;
    padding: 2px 9px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-left: 10px;
    vertical-align: middle;
}
.pill-critical {
    background: rgba(239,68,68,0.18);
    border: 1px solid rgba(239,68,68,0.45);
    color: #EF4444;
    text-shadow: 0 0 6px rgba(239,68,68,0.6);
}
.pill-warning {
    background: rgba(245,158,11,0.15);
    border: 1px solid rgba(245,158,11,0.4);
    color: #F59E0B;
}
.pill-stable {
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.35);
    color: #10B981;
}

/* Patient metadata */
.cp-meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px 10px;
    margin-top: 0.5rem;
}
.cp-meta-item { font-size: 11px; color: #64748B; }
.cp-meta-item span { color: #CBD5E1; font-weight: 500; }

/* ── Modality score cards ── */
.cp-mod-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    line-height: 1.1;
}
.score-red    { color: #EF4444; text-shadow: 0 0 16px rgba(239,68,68,0.5); }
.score-amber  { color: #F59E0B; text-shadow: 0 0 16px rgba(245,158,11,0.5); }
.score-cyan   { color: #00F2FE; text-shadow: 0 0 16px rgba(0,242,254,0.5); }

.cp-score-bar-wrap {
    background: #0B0F19;
    border-radius: 3px;
    height: 5px;
    margin-top: 6px;
    overflow: hidden;
}
.cp-score-bar {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

/* ── Bed badges ── */
.cp-bed-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 0;
    border-bottom: 1px solid #1E293B;
    font-size: 11px;
}
.cp-bed-row:last-child { border-bottom: none; }
.cp-bed-id {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #CBD5E1;
    font-weight: 600;
}
.bed-badge {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.07em;
    padding: 1px 7px;
    border-radius: 3px;
}
.badge-critical { background: rgba(239,68,68,0.18); color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }
.badge-warning  { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
.badge-stable   { background: rgba(16,185,129,0.12); color: #10B981; border: 1px solid rgba(16,185,129,0.3); }
.badge-empty    { background: rgba(100,116,139,0.12); color: #64748B; border: 1px solid #1E293B; }

/* ── Emergency button ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.08)) !important;
    border: 1px solid rgba(239,68,68,0.5) !important;
    color: #EF4444 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    border-radius: 5px !important;
    padding: 0.35rem 0.5rem !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    text-shadow: 0 0 8px rgba(239,68,68,0.5) !important;
    box-shadow: 0 0 12px rgba(239,68,68,0.1) !important;
    margin-top: 4px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(239,68,68,0.35), rgba(239,68,68,0.15)) !important;
    box-shadow: 0 0 20px rgba(239,68,68,0.3) !important;
    border-color: #EF4444 !important;
}

/* ── File uploader compact ── */
[data-testid="stFileUploader"] {
    background: #0B0F19 !important;
    border: 1px dashed #1E293B !important;
    border-radius: 6px !important;
    padding: 0.4rem !important;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] p    { font-size: 11px !important; color: #64748B !important; }
[data-testid="stFileUploader"] section { padding: 0.3rem !important; min-height: unset !important; }

/* Collapse expanders / alerts */
.stAlert { padding: 0.3rem 0.5rem !important; font-size: 11px !important; }

/* ── Divider ── */
.cp-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #1E293B 30%, #1E293B 70%, transparent);
    margin: 0.3rem 0;
}

/* Timestamp */
.cp-ts {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #334155;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE  —  persistent mock data
# ─────────────────────────────────────────────
def _init_state():
    if "sepsis_score"  not in st.session_state: st.session_state.sepsis_score  = 0.85
    if "cardiac_score" not in st.session_state: st.session_state.cardiac_score = 0.70
    if "pulm_score"    not in st.session_state: st.session_state.pulm_score    = 0.90
    if "patient_id"    not in st.session_state: st.session_state.patient_id    = "PT-20394"
    if "patient_age"   not in st.session_state: st.session_state.patient_age   = 67
    if "patient_sex"   not in st.session_state: st.session_state.patient_sex   = "M"
    if "admit_time"    not in st.session_state: st.session_state.admit_time    = "14:32 UTC"
    if "ward"          not in st.session_state: st.session_state.ward          = "ICU-02"
    if "api_response"  not in st.session_state: st.session_state.api_response  = None
    if "api_status"    not in st.session_state: st.session_state.api_status    = None
    if "beds" not in st.session_state:
        st.session_state.beds = [
            {"id": "ICU-01", "status": "critical", "patient": "PT-20391", "risk": 0.91},
            {"id": "ICU-02", "status": "critical", "patient": "PT-20394", "risk": 0.82},
            {"id": "ICU-03", "status": "warning",  "patient": "PT-20388", "risk": 0.61},
            {"id": "ICU-04", "status": "stable",   "patient": "PT-20380", "risk": 0.33},
            {"id": "ICU-05", "status": "warning",  "patient": "PT-20402", "risk": 0.57},
            {"id": "ICU-06", "status": "empty",    "patient": "—",        "risk": 0.00},
        ]

_init_state()

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def late_fusion_score():
    """Weighted late fusion of three modality scores."""
    w = [0.40, 0.30, 0.30]
    s = [st.session_state.sepsis_score,
         st.session_state.cardiac_score,
         st.session_state.pulm_score]
    return round(sum(w[i]*s[i] for i in range(3)), 3)


def risk_level(score: float) -> tuple[str, str]:
    """Return (label, css_class) for a given risk score."""
    if score >= 0.80: return "CRITICAL", "pill-critical"
    if score >= 0.55: return "WARNING",  "pill-warning"
    return "STABLE", "pill-stable"


def score_bar_color(score: float) -> str:
    if score >= 0.80: return "#EF4444"
    if score >= 0.55: return "#F59E0B"
    return "#10B981"


def trajectory_chart(fused: float) -> go.Figure:
    times  = ["Now", "+3h", "+6h", "+12h"]
    deltas = [0, 0.03, 0.05, -0.02]
    scores = [min(max(fused + d + random.uniform(-0.01, 0.01), 0), 1) for d in deltas]
    scores[0] = fused   # anchor current value

    fig = go.Figure()

    # glow shadow
    fig.add_trace(go.Scatter(
        x=times, y=scores, mode="lines",
        line=dict(color="rgba(239,68,68,0.15)", width=14),
        showlegend=False, hoverinfo="skip",
    ))
    # main line
    fig.add_trace(go.Scatter(
        x=times, y=scores, mode="lines+markers",
        name="Fused Risk",
        line=dict(color="#EF4444", width=2.5),
        marker=dict(size=7, color="#EF4444",
                    line=dict(color="#0B0F19", width=2)),
        hovertemplate="%{x}: <b>%{y:.3f}</b><extra></extra>",
    ))
    # threshold band
    fig.add_hrect(y0=0.80, y1=1.0,
                  fillcolor="rgba(239,68,68,0.06)",
                  line_width=0)
    fig.add_hline(y=0.80, line=dict(color="rgba(239,68,68,0.3)",
                  width=1, dash="dot"),
                  annotation_text="Critical threshold",
                  annotation_font=dict(size=9, color="#94A3B8"),
                  annotation_position="top right")

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0B0F19",
        margin=dict(l=28, r=10, t=8, b=24),
        height=148,
        font=dict(family="JetBrains Mono", size=10, color="#64748B"),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickfont=dict(size=9), linecolor="#1E293B"),
        yaxis=dict(showgrid=True, gridcolor="#1A2236",
                   zeroline=False, range=[0, 1.05],
                   tickfont=dict(size=9), linecolor="#1E293B"),
        showlegend=False,
        hovermode="x unified",
    )
    return fig


def call_fuse_api(patient_payload: dict) -> tuple[bool, dict | str]:
    try:
        r = requests.post(
            "http://localhost:8000/api/fuse_triage",
            json=patient_payload,
            timeout=4,
        )
        r.raise_for_status()
        return True, r.json()
    except requests.exceptions.ConnectionError:
        return False, "Connection refused — ensure backend is running on :8000"
    except requests.exceptions.Timeout:
        return False, "Request timed out after 4s"
    except Exception as exc:
        return False, str(exc)


# ─────────────────────────────────────────────
#  COMPUTED VALUES
# ─────────────────────────────────────────────
fused      = late_fusion_score()
risk_lbl, risk_cls = risk_level(fused)
now_ts     = datetime.utcnow().strftime("%H:%M:%S UTC")


# ═════════════════════════════════════════════
#  LAYOUT
# ═════════════════════════════════════════════

# ── [1] TOP NAVBAR ──────────────────────────
st.markdown(f"""
<div class="cp-navbar">
  <div class="cp-navbar-brand">
    EPOCH
    <span>|</span>
    Command Center
  </div>
  <div style="display:flex;align-items:center;gap:14px;">
    <span class="cp-ts">{now_ts}</span>
    <div class="cp-live-pill">
      <div class="cp-live-dot"></div>
      LIVE TELEMETRY
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── [2] HERO ROW  (65 / 35) ─────────────────
col_hero_l, col_hero_r = st.columns([0.65, 0.35], gap="small")

with col_hero_l:
    st.markdown(f"""
    <div class="cp-card" style="border-left: 3px solid #EF4444;">
        <div class="cp-card-label accent-red">Unified Late Fusion Risk Score</div>
        <div style="display:flex;align-items:baseline;gap:4px;margin-top:2px;">
            <div class="cp-hero-score">{fused}</div>
            <span class="cp-status-pill {risk_cls}">{risk_lbl}</span>
        </div>
        <div class="cp-divider" style="margin:0.45rem 0;"></div>
        <div class="cp-meta-grid">
            <div class="cp-meta-item">Patient ID <span>{st.session_state.patient_id}</span></div>
            <div class="cp-meta-item">Age / Sex <span>{st.session_state.patient_age}y {st.session_state.patient_sex}</span></div>
            <div class="cp-meta-item">Admitted <span>{st.session_state.admit_time}</span></div>
            <div class="cp-meta-item">Ward <span>{st.session_state.ward}</span></div>
            <div class="cp-meta-item">Attending <span>Dr. K. Arunachalam</span></div>
            <div class="cp-meta-item">Protocol <span>SEPSIS-3 / ARDS</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_hero_r:
    st.markdown("""
    <div class="cp-card" style="height:100%;">
        <div class="cp-card-label accent-cyan">Scan Visualizer — DICOM / CXR</div>
    """, unsafe_allow_html=True)
    uploaded_scan = st.file_uploader(
        label="",
        type=["dcm", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
        help="Upload DICOM or chest X-ray image",
    )
    if uploaded_scan:
        st.image(uploaded_scan, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── [3] MODALITY TELEMETRY ROW  (3×33%) ─────
st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True)
col_m1, col_m2, col_m3 = st.columns(3, gap="small")

MODALITIES = [
    {
        "col": col_m1,
        "label": "Sepsis Risk  ·  EHR / Vitals",
        "accent": "accent-red",
        "score": st.session_state.sepsis_score,
        "score_cls": "score-red",
        "icon": "🩸",
        "sub": "qSOFA+: 3/3  |  Lactate: 4.2",
        "bar_color": "#EF4444",
    },
    {
        "col": col_m2,
        "label": "Cardiac Risk  ·  ECG Signal",
        "accent": "accent-amber",
        "score": st.session_state.cardiac_score,
        "score_cls": "score-amber",
        "icon": "💓",
        "sub": "ST-elev: Yes  |  QTc: 488ms",
        "bar_color": "#F59E0B",
    },
    {
        "col": col_m3,
        "label": "Pulmonary Risk  ·  Vision CT",
        "accent": "accent-cyan",
        "score": st.session_state.pulm_score,
        "score_cls": "score-cyan",
        "icon": "🫁",
        "sub": "ARDS Stage: III  |  PF: 88",
        "bar_color": "#00F2FE",
    },
]

for m in MODALITIES:
    pct = int(m["score"] * 100)
    rl, rc = risk_level(m["score"])
    with m["col"]:
        st.markdown(f"""
        <div class="cp-card">
            <div class="cp-card-label {m['accent']}">{m['icon']} &nbsp; {m['label']}</div>
            <div style="display:flex;align-items:baseline;justify-content:space-between;margin-top:3px;">
                <span class="cp-mod-score {m['score_cls']}">{m['score']:.2f}</span>
                <span class="cp-status-pill {rc}" style="font-size:9px;">{rl}</span>
            </div>
            <div class="cp-score-bar-wrap">
                <div class="cp-score-bar"
                     style="width:{pct}%;background:{m['bar_color']};
                            box-shadow:0 0 8px {m['bar_color']}55;">
                </div>
            </div>
            <div style="font-size:10px;color:#475569;margin-top:5px;
                        font-family:'JetBrains Mono',monospace;">{m['sub']}</div>
        </div>
        """, unsafe_allow_html=True)


# ── [4] BOTTOM ANALYTICS ROW  (65 / 35) ─────
st.markdown('<div style="height:5px;"></div>', unsafe_allow_html=True)
col_btm_l, col_btm_r = st.columns([0.65, 0.35], gap="small")

# ── LEFT — Risk trajectory chart ──
with col_btm_l:
    st.markdown("""
    <div class="cp-card" style="border-left:3px solid #EF4444;">
        <div class="cp-card-label accent-red">Risk Trajectory Projection</div>
    """, unsafe_allow_html=True)
    fig = trajectory_chart(fused)
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# ── RIGHT — ICU Bed Monitoring ──
with col_btm_r:
    st.markdown("""
    <div class="cp-card" style="border-left:3px solid #00F2FE;">
        <div class="cp-card-label accent-cyan">ICU Bed Monitoring</div>
    """, unsafe_allow_html=True)

    bed_rows_html = ""
    for bed in st.session_state.beds:
        badge_cls = f"badge-{bed['status']}"
        badge_lbl = bed["status"].upper()
        risk_str  = (f"{bed['risk']:.2f}" if bed["risk"] > 0 else "—")
        pt_disp   = bed["patient"] if bed["status"] != "empty" else "AVAILABLE"
        pt_color  = "#475569" if bed["status"] == "empty" else "#94A3B8"
        bed_rows_html += f"""
        <div class="cp-bed-row">
            <span class="cp-bed-id">{bed['id']}</span>
            <span style="font-size:10px;color:{pt_color};font-family:'JetBrains Mono',monospace;">
                {pt_disp}
            </span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:10px;
                         color:#64748B;">{risk_str}</span>
            <span class="bed-badge {badge_cls}">{badge_lbl}</span>
        </div>
        """

    st.markdown(bed_rows_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Emergency simulation button ──
    if st.button("⚡  SIMULATE EMERGENCY PATIENT", key="sim_btn"):
        # Randomise new patient scores
        st.session_state.sepsis_score  = round(random.uniform(0.60, 0.99), 2)
        st.session_state.cardiac_score = round(random.uniform(0.50, 0.95), 2)
        st.session_state.pulm_score    = round(random.uniform(0.65, 0.99), 2)
        st.session_state.patient_id    = f"PT-{random.randint(20000,29999)}"
        st.session_state.patient_age   = random.randint(42, 85)
        st.session_state.patient_sex   = random.choice(["M", "F"])
        st.session_state.admit_time    = datetime.utcnow().strftime("%H:%M UTC")

        payload = {
            "patient_id":    st.session_state.patient_id,
            "sepsis_score":  st.session_state.sepsis_score,
            "cardiac_score": st.session_state.cardiac_score,
            "pulm_score":    st.session_state.pulm_score,
            "timestamp":     datetime.utcnow().isoformat(),
        }

        ok, result = call_fuse_api(payload)
        st.session_state.api_response = result
        st.session_state.api_status   = ok

        # Update a random non-empty bed with new patient
        target = random.choice([b for b in st.session_state.beds
                                 if b["status"] != "empty"])
        target["patient"] = st.session_state.patient_id
        target["risk"]    = late_fusion_score()
        target["status"]  = "critical" if late_fusion_score() >= 0.80 else "warning"

        st.rerun()

    # API response status strip
    if st.session_state.api_status is not None:
        if st.session_state.api_status:
            st.markdown(
                f'<div style="font-size:10px;color:#10B981;font-family:JetBrains Mono,monospace;'
                f'padding:3px 6px;background:rgba(16,185,129,0.08);border-radius:4px;'
                f'border:1px solid rgba(16,185,129,0.2);margin-top:4px;">'
                f'✓ API OK — {json.dumps(st.session_state.api_response)[:80]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="font-size:10px;color:#F59E0B;font-family:JetBrains Mono,monospace;'
                f'padding:3px 6px;background:rgba(245,158,11,0.08);border-radius:4px;'
                f'border:1px solid rgba(245,158,11,0.25);margin-top:4px;">'
                f'⚠ {str(st.session_state.api_response)[:100]}</div>',
                unsafe_allow_html=True,
            )
