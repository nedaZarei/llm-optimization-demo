import streamlit as st
import json
import base64
import threading
import queue as _queue
import time as _time
from pathlib import Path
import plotly.graph_objects as go

def _b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()

_ROOT = Path(__file__).parent
_TURINTECH_B64 = _b64(_ROOT / "logos/TurinTech-light-no Background.svg")
_ARTEMIS_WM    = _b64(_ROOT / "logos/artemis-logo-wordmark.png")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Artemis — LLM Optimization Demo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ─ Base dark theme ─ */
[data-testid="stAppViewContainer"] {
    background: #07071a;
    background-image:
        linear-gradient(rgba(124,115,255,0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(124,115,255,0.055) 1px, transparent 1px),
        radial-gradient(ellipse 80% 55% at 15% 0%, rgba(91,82,232,0.22) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 90% 100%, rgba(26,213,152,0.1) 0%, transparent 50%);
    background-size: 60px 60px, 60px 60px, 100% 100%, 100% 100%;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { display: none; }
.stApp { background: transparent !important; }
.block-container {
    padding: 2.5rem 3.5rem 6rem !important;
    max-width: 1100px !important;
    margin: 0 auto;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ─ Hide default chrome ─ */
footer { display: none; }
#MainMenu { display: none; }

/* ─ Global text ─ */
.stMarkdown p, .stMarkdown li, .stMarkdown strong, .stMarkdown em,
[data-testid="stMarkdownContainer"] p { color: rgba(255,255,255,0.82) !important; }

/* ─ Section label ─ */
.slabel {
    font-size: 0.62rem;
    font-weight: 800;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #7C73FF;
    margin: 0 0 0.9rem 0;
    padding-left: 0.65rem;
    border-left: 3px solid #7C73FF;
    line-height: 1.5;
    font-family: 'Inter', sans-serif;
}

/* ─ Spec bar ─ */
.spec-bar {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(124,115,255,0.22);
    border-radius: 14px;
    padding: 1.1rem 1.6rem;
    display: flex;
    align-items: stretch;
    gap: 0;
    margin-top: 0.85rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    font-family: 'Inter', sans-serif;
}
.spec-bar-item {
    flex: 1;
    padding: 0 1.4rem;
    border-right: 1px solid rgba(124,115,255,0.12);
}
.spec-bar-item:first-child { padding-left: 0; }
.spec-bar-item:last-child { border-right: none; }
.spec-bar .lbl {
    color: rgba(255,255,255,0.28);
    font-size: 0.6rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin-bottom: 0.35rem;
    display: block;
}
.spec-bar .val {
    color: #ffffff;
    font-weight: 700;
    font-size: 0.95rem;
    display: block;
    letter-spacing: -0.2px;
}
.spec-bar .specs-muted {
    color: rgba(255,255,255,0.33);
    font-weight: 400;
    font-size: 0.74rem;
    display: block;
    margin-top: 0.2rem;
}

/* ─ Spec tier badges ─ */
.badge-high {
    display: inline-block;
    background: rgba(124,115,255,0.18);
    color: #b0aaff;
    border: 1px solid rgba(124,115,255,0.35);
    border-radius: 5px;
    padding: 0.1rem 0.45rem;
    font-size: 0.62rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.8px;
}
.badge-mid {
    display: inline-block;
    background: rgba(251,191,36,0.1);
    color: #fbbf24;
    border: 1px solid rgba(251,191,36,0.3);
    border-radius: 5px;
    padding: 0.1rem 0.45rem;
    font-size: 0.62rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.8px;
}
.badge-low {
    display: inline-block;
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.45);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 5px;
    padding: 0.1rem 0.45rem;
    font-size: 0.62rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.8px;
}

/* ─ Section divider ─ */
.section-sep {
    border: none; height: 1px;
    background: linear-gradient(90deg, rgba(124,115,255,0.4) 0%, rgba(26,213,152,0.2) 60%, transparent 100%);
    margin: 2.25rem 0 1.75rem;
}

/* ─ Benchmark table ─ */
.bm-wrap {
    border: 1px solid rgba(124,115,255,0.2);
    border-radius: 12px; overflow: hidden;
    background: rgba(255,255,255,0.03);
    box-shadow: 0 2px 20px rgba(0,0,0,0.3);
}
.bm-table {
    width: 100%; border-collapse: collapse;
    font-size: 0.875rem; font-family: 'Inter', sans-serif;
}
.bm-table thead tr { border-bottom: 1.5px solid rgba(124,115,255,0.15); }
.bm-table thead th {
    padding: 0.7rem 1.1rem; text-align: left;
    font-size: 0.62rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    color: rgba(255,255,255,0.28); background: transparent;
}
.bm-table thead th.col-artemis { color: #7C73FF; }
.bm-table tbody td {
    padding: 0.65rem 1.1rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: rgba(255,255,255,0.82); vertical-align: middle;
}
.bm-table tbody tr:last-child td { border-bottom: none; }
.bm-table .type-cell {
    font-weight: 700; color: #ffffff; font-size: 0.875rem;
    border-right: 1px solid rgba(255,255,255,0.06);
    white-space: nowrap; padding-left: 0.9rem;
}
.bm-table .metric-cell { color: rgba(255,255,255,0.5); }
.bm-table tr.g-sep td { border-top: 1.5px solid rgba(124,115,255,0.15) !important; }

/* ─ Tooltip ─ */
.tt { cursor: help; border-bottom: 1px dashed rgba(124,115,255,0.45); position: relative; display: inline-block; }
.tt::after {
    content: attr(data-tip); position: absolute; left: 0; top: calc(100% + 7px);
    background: #12123a; color: rgba(255,255,255,0.88);
    border: 1px solid rgba(124,115,255,0.3);
    border-radius: 8px; padding: 0.5rem 0.85rem;
    font-size: 0.75rem; font-weight: 400; line-height: 1.5;
    width: 230px; white-space: normal; z-index: 9999;
    opacity: 0; pointer-events: none; transition: opacity 0.18s ease;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}
.tt:hover::after { opacity: 1; }

/* ─ Delta values ─ */
.d-pos  { color: #1AD598; font-weight: 700; }
.d-neg  { color: #f87171; font-weight: 700; }
.d-neut { color: rgba(255,255,255,0.35); font-weight: 600; }

/* ─ Built for your stack table ─ */
.hw-wrap {
    border: 1px solid rgba(124,115,255,0.2);
    border-radius: 12px; overflow: hidden;
    background: rgba(255,255,255,0.03);
    box-shadow: 0 2px 20px rgba(0,0,0,0.3);
}
.hw-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; font-family: 'Inter', sans-serif; }
.hw-table thead tr { border-bottom: 1.5px solid rgba(124,115,255,0.15); }
.hw-table thead th {
    padding: 0.7rem 1.1rem; text-align: left;
    font-size: 0.62rem; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; color: rgba(255,255,255,0.28); background: transparent;
}
.hw-table tbody td { padding: 0.75rem 1.1rem; border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle; }
.hw-table tbody tr:last-child td { border-bottom: none; }
.hw-table tbody tr:hover td { background: rgba(124,115,255,0.07); }
.hw-name { font-weight: 700; color: #ffffff; }
.hw-class { color: rgba(255,255,255,0.38); font-size: 0.82rem; }

/* ─ Progress bar ─ */
.pbar-row { display: flex; align-items: center; gap: 0.6rem; }
.pbar-bg  { background: rgba(255,255,255,0.1); border-radius: 4px; height: 6px; width: 80px; flex-shrink: 0; }
.pbar-fg  { background: linear-gradient(90deg, #7C73FF, #1AD598); border-radius: 4px; height: 6px; }

/* ─ Verdict ─ */
.verd-pass { color: #1AD598; font-weight: 700; font-size: 0.82rem; }
.verd-warn { color: #fbbf24; font-weight: 600; font-size: 0.82rem; }
.verd-fail { color: #f87171; font-weight: 600; font-size: 0.82rem; }

/* ─ View link ─ */
a.view-link { color: #7C73FF; font-weight: 600; text-decoration: none; font-size: 0.83rem; }
a.view-link:hover { text-decoration: underline; }

/* ─ Share box ─ */
.share-url {
    background: rgba(255,255,255,0.05); border: 1px solid rgba(124,115,255,0.2);
    border-radius: 8px; padding: 0.7rem 1rem;
    font-family: "Menlo", "Monaco", monospace; font-size: 0.8rem;
    color: rgba(255,255,255,0.6); word-break: break-all; margin: 0.35rem 0 0.4rem 0;
}

/* ─ Tabs ─ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0; border-bottom: 1.5px solid rgba(124,115,255,0.2) !important; background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0; font-size: 0.82rem; font-weight: 600;
    color: rgba(255,255,255,0.33) !important; padding: 0.55rem 1.1rem;
    border-bottom: 2px solid transparent; background: transparent !important;
}
.stTabs [aria-selected="true"] { color: #7C73FF !important; border-bottom: 2px solid #7C73FF !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 1rem 0 0 0; }

/* ─ Buttons ─ */
.stDownloadButton > button {
    background: rgba(124,115,255,0.15) !important; color: #b0aaff !important;
    border: 1px solid rgba(124,115,255,0.3) !important; border-radius: 50px !important;
    font-weight: 600 !important; font-size: 0.875rem !important;
    padding: 0.55rem 1.2rem !important; width: 100% !important; cursor: pointer !important;
}
.stDownloadButton > button:hover { background: rgba(124,115,255,0.25) !important; }

[data-testid="stSelectbox"] label {
    font-size: 0.78rem !important; font-weight: 600 !important;
    color: rgba(255,255,255,0.4) !important; letter-spacing: 0.2px !important;
}
[data-testid="stSlider"] label {
    font-size: 0.78rem !important; font-weight: 600 !important; color: rgba(255,255,255,0.4) !important;
}
[data-testid="stButton"] > button {
    background: #7C73FF !important; color: white !important; border: none !important;
    border-radius: 50px !important; font-weight: 700 !important; font-size: 0.9rem !important;
    padding: 0.6rem 1.6rem !important; cursor: pointer !important; transition: opacity 0.15s !important;
}
[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }

/* ─ Selectbox dark ─ */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(124,115,255,0.25) !important; color: white !important;
}
[data-testid="stSelectbox"] span { color: rgba(255,255,255,0.85) !important; }
[data-baseweb="popover"] > div, [data-baseweb="menu"] {
    background: #12123a !important; border: 1px solid rgba(124,115,255,0.3) !important;
}
[role="option"] { color: rgba(255,255,255,0.82) !important; background: transparent !important; }
[role="option"]:hover { background: rgba(124,115,255,0.15) !important; }

/* ─ Live side-by-side ─ */
.why-box {
    background: rgba(124,115,255,0.08); border: 1px solid rgba(124,115,255,0.2);
    border-radius: 8px; padding: 0.5rem 0.9rem; font-size: 0.81rem;
    color: rgba(255,255,255,0.55); margin: 0.5rem 0 0.8rem 0; line-height: 1.5;
}
.live-col-hdr {
    display: flex; justify-content: space-between; align-items: center;
    padding-bottom: 0.6rem; border-bottom: 1px solid rgba(124,115,255,0.14);
    margin-bottom: 0.9rem;
}
.live-col-title { font-weight: 700; color: #ffffff; font-size: 0.9rem; }
.live-lbl-base  { font-size: 0.6rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(255,255,255,0.28); }
.live-lbl-opt   { font-size: 0.6rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; color: #7C73FF; }
.live-meta {
    font-size: 0.72rem; color: rgba(255,255,255,0.4); margin-top: 0.6rem;
    padding: 0.45rem 0.8rem; background: rgba(255,255,255,0.04);
    border-radius: 7px; border: 1px solid rgba(124,115,255,0.14);
    line-height: 1.5; letter-spacing: 0.1px;
}
.live-meta strong { color: #ffffff; font-weight: 700; }

[data-testid="stChatMessage"] { margin-top: 0 !important; padding-top: 0.3rem !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: rgba(124,115,255,0.08) !important; border-radius: 10px !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] em {
    color: rgba(255,255,255,0.85) !important;
}

/* ─ Speedup callout ─ */
.speedup-callout {
    text-align: center; font-size: 1.05rem; font-weight: 500;
    color: rgba(255,255,255,0.55); margin: 1.2rem 0 0.4rem 0;
    padding: 2rem 2rem 1.6rem;
    background: rgba(255,255,255,0.03); border: 1px solid rgba(124,115,255,0.25);
    border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.speedup-num {
    background: linear-gradient(135deg, #7C73FF 0%, #1AD598 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    font-size: 5.5rem; font-weight: 900; line-height: 1; display: block;
    margin: 0.2rem 0 0.5rem; letter-spacing: -3px;
}
.speedup-sub {
    font-size: 0.78rem; color: rgba(255,255,255,0.28); margin-top: 0.7rem;
    display: block; letter-spacing: 0.5px; font-weight: 500;
}

/* ─ Results reveal box ─ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1.5px solid rgba(124,115,255,0.22) !important;
    border-radius: 16px !important; box-shadow: 0 4px 24px rgba(0,0,0,0.25) !important;
}

/* ─ Caption ─ */
[data-testid="stCaptionContainer"] p { color: rgba(255,255,255,0.3) !important; }

.sim-note { text-align: center; font-size: 0.72rem; color: rgba(255,255,255,0.25); margin-top: 0.25rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Data layer ────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"


def list_configs():
    configs = []
    if not DATA_DIR.exists():
        return configs
    for fpath in sorted(DATA_DIR.glob("*.json")):
        try:
            d = json.loads(fpath.read_text())
            m = d.get("meta", {})
            configs.append({
                "config_id": fpath.stem,
                "model":     m.get("model", fpath.stem),
                "hardware":  m.get("hardware", ""),
                "framework": m.get("framework", ""),
            })
        except Exception:
            pass
    return configs


def load_config(config_id: str):
    p = DATA_DIR / f"{config_id}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def pct_delta(baseline, optimized):
    if baseline == 0:
        return 0.0
    return (optimized - baseline) / abs(baseline) * 100.0


def delta_html(baseline, optimized, lower_is_better=False):
    d = pct_delta(baseline, optimized)
    if abs(d) < 0.05:
        return '<span class="d-neut">±0.0%</span>'
    sign = "+" if d > 0 else ""
    text = f"{sign}{d:.1f}%"
    improvement = (d < 0) if lower_is_better else (d > 0)
    cls = "d-pos" if improvement else "d-neg"
    return f'<span class="{cls}">{text}</span>'


def tier_badge(tier: str) -> str:
    t = (tier or "").lower()
    mapping = {
        "high": ("badge-high", "High Spec"),
        "mid":  ("badge-mid",  "Mid Spec"),
    }
    cls, label = mapping.get(t, ("badge-low", "Low Spec"))
    return f'<span class="{cls}">{label}</span>'


def verdict_html(v: str) -> str:
    v = (v or "").lower()
    if v == "pass":
        return '<span class="verd-pass">✓ Pass</span>'
    if "warn" in v or "regression" in v:
        return '<span class="verd-warn">⚠ Regression</span>'
    return '<span class="verd-fail">✗ Fail</span>'


def progress_bar_html(pct: float, max_pct: float = 70) -> str:
    w = min(100, round(pct / max_pct * 100)) if max_pct > 0 else 0
    sign = "+" if pct >= 0 else ""
    return (
        f'<div class="pbar-row">'
        f'<span class="d-pos">{sign}{pct:.1f}%</span>'
        f'<div class="pbar-bg"><div class="pbar-fg" style="width:{w}%"></div></div>'
        f'</div>'
    )


# ── Benchmark table builder ───────────────────────────────────────────────────

BENCH_METRICS = [
    ("Throughput", "throughput_tps", "tok/s", False),
    ("TTFT",       "ttft_ms",        "ms",    True),
]

# Scenarios excluded from the demo table (still present in JSON / markdown export)
_HIDDEN_SCENARIOS = {"control_prompt"}


def _fmt_val(v, unit):
    if unit:
        return f"{v:g} {unit}"
    return f"{v:g}"


# Accent colors cycling per group (scenario blocks then accuracy/cost)
_GROUP_ACCENTS = ["#7C73FF", "#1AD598", "#7C73FF", "#1AD598"]
_GROUP_BG      = ["rgba(124,115,255,0.07)", "rgba(26,213,152,0.05)", "rgba(124,115,255,0.07)", "rgba(26,213,152,0.05)"]
_ACCENT_TAIL   = "rgba(255,255,255,0.25)"
_BG_TAIL       = "rgba(255,255,255,0.02)"


def _group_rows(metric_rows, label, desc, accent, bg, is_first_group):
    """Render one group of <tr> elements with accent border, tint, and tooltip."""
    span = len(metric_rows)
    sep_class = "" if is_first_group else ' class="g-sep"'
    type_style = (
        f"border-left: 3px solid {accent}; "
        f"background: {bg}; "
        f"padding-left: 0.85rem;"
    )
    row_style = f'style="background:{bg}"'

    # Escape quotes in tooltip text
    safe_desc = desc.replace('"', "&quot;")
    tooltip_label = (
        f'<span class="tt" data-tip="{safe_desc}">{label}</span>'
        if desc else label
    )

    m = metric_rows[0]
    html = (
        f'<tr{sep_class} {row_style}>'
        f'<td class="type-cell" rowspan="{span}" style="{type_style}">{tooltip_label}</td>'
        f'<td class="metric-cell">{m[0]}</td>'
        f'<td>{m[1]}</td>'
        f'<td>{m[2]}</td>'
        f'<td>{m[3]}</td>'
        f'</tr>'
    )
    for m in metric_rows[1:]:
        html += (
            f'<tr {row_style}>'
            f'<td class="metric-cell">{m[0]}</td>'
            f'<td>{m[1]}</td>'
            f'<td>{m[2]}</td>'
            f'<td>{m[3]}</td>'
            f'</tr>'
        )
    return html


def benchmark_table_html(data: dict, mode: str) -> str:
    scenarios = data.get("benchmark", {}).get("scenarios", {})
    correctness = data.get("correctness", {})
    accuracy = correctness.get("accuracy", {})

    tbody = ""
    group_idx = 0

    # ── Per-scenario rows ──────────────────────────────────────────────────
    for sc_key, sc in scenarios.items():
        if sc_key in _HIDDEN_SCENARIOS or mode not in sc:
            continue
        md    = sc[mode]
        label = sc.get("label", sc_key)
        desc  = sc.get("description", "")

        metric_rows = []
        for lbl, key, unit, lib in BENCH_METRICS:
            if key not in md:
                continue
            b = md[key]["baseline"]
            o = md[key]["optimized"]
            metric_rows.append((
                lbl,
                _fmt_val(b, unit),
                _fmt_val(o, unit),
                delta_html(b, o, lib),
            ))

        if not metric_rows:
            continue

        accent = _GROUP_ACCENTS[group_idx % len(_GROUP_ACCENTS)]
        bg     = _GROUP_BG[group_idx % len(_GROUP_BG)]
        tbody += _group_rows(metric_rows, label, desc, accent, bg, group_idx == 0)
        group_idx += 1

    # ── Accuracy rows ──────────────────────────────────────────────────────
    acc_rows = []
    for key, lbl, unit, lib in [
        ("mmlu", "MMLU", "%", False),
    ]:
        a = accuracy.get(key)
        if a:
            b, o = a["baseline"], a["optimized"]
            acc_rows.append((lbl, f"{b}{unit}", f"{o}{unit}", delta_html(b, o, lib)))

    if acc_rows:
        tbody += _group_rows(
            acc_rows, "Accuracy",
            "MMLU and HellaSwag scores — measures whether optimization shifts model accuracy",
            _ACCENT_TAIL, _BG_TAIL, False,
        )

    # ── Cost row ───────────────────────────────────────────────────────────
    c = accuracy.get("cost_per_1m")
    if c:
        b, o = c["baseline"], c["optimized"]
        tbody += _group_rows(
            [("Cost / 1M tok", f"${b}", f"${o}", delta_html(b, o, lower_is_better=True))],
            "Cost",
            "Estimated infrastructure cost per 1 million output tokens at this throughput",
            _ACCENT_TAIL, _BG_TAIL, False,
        )

    return (
        '<div class="bm-wrap">'
        '<table class="bm-table">'
        '<thead><tr>'
        '<th>Type</th><th>Metric</th>'
        '<th>Baseline</th>'
        '<th class="col-artemis">+ Artemis</th>'
        '<th>Δ</th>'
        '</tr></thead>'
        f'<tbody>{tbody}</tbody>'
        '</table></div>'
    )


# ── Live streaming helpers ────────────────────────────────────────────────────

def _simulate_stream(recorded: dict, q):
    """Replay a recorded response at the original TTFT + tok/s speed."""
    text    = recorded.get("text", "")
    tps     = float(recorded.get("tps", 40))
    ttft_ms = float(recorded.get("ttft_ms", 1000))

    _time.sleep(ttft_ms / 1000.0)

    if not text:
        q.put(("done", None, None, tps, 0))
        return

    words = text.split(" ")
    chars_per_sec = tps * 3.5                        # ~3.5 chars per token
    avg_chars = max(1, len(text) / max(len(words), 1))
    delay = avg_chars / chars_per_sec

    for i, word in enumerate(words):
        piece = word if i == len(words) - 1 else word + " "
        q.put(("token", piece, ttft_ms if i == 0 else None, None, i + 1))
        _time.sleep(delay)

    q.put(("done", None, None, tps, len(words)))


def _real_stream(url: str, model_id: str, system: str, user: str, q):
    """Stream from a live OpenAI-compatible endpoint."""
    try:
        import httpx as _httpx, json as _json
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream": True,
            "temperature": 1.0,
        }
        t0 = _time.perf_counter()
        ttft = None
        n = 0
        with _httpx.stream("POST", f"{url}/chat/completions",
                           json=payload, timeout=120) as r:
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                chunk = line[6:].strip()
                if chunk == "[DONE]":
                    elapsed = _time.perf_counter() - t0
                    decode = elapsed - (ttft / 1000 if ttft else 0)
                    q.put(("done", None, None, n / max(decode, 0.001), n))
                    return
                try:
                    text = _json.loads(chunk)["choices"][0]["delta"].get("content", "")
                    if text:
                        n += 1
                        first_ttft = None
                        if ttft is None:
                            ttft = (_time.perf_counter() - t0) * 1000
                            first_ttft = ttft
                        q.put(("token", text, first_ttft, None, n))
                except Exception:
                    pass
    except Exception as exc:
        q.put(("error", str(exc), None, None, None))
        q.put(("done", None, None, 0, 0))


def _run_comparison(prompt: dict, services: dict, meta: dict,
                    ph_t1, ph_t2, ph_m1, ph_m2):
    """Fire both streams in threads; poll queues; update placeholders live."""
    q1, q2 = _queue.Queue(), _queue.Queue()
    baseline_url  = (services or {}).get("baseline_url")
    optimized_url = (services or {}).get("optimized_url")
    model_id      = (services or {}).get("model_id", "")
    recorded      = prompt.get("recorded", {})
    simulated     = not (baseline_url and optimized_url)

    if simulated:
        t1 = threading.Thread(target=_simulate_stream,
                              args=(recorded.get("baseline", {}), q1), daemon=True)
        t2 = threading.Thread(target=_simulate_stream,
                              args=(recorded.get("optimized", {}), q2), daemon=True)
    else:
        sys_msg = prompt.get("system", "")
        usr_msg = prompt.get("user", "")
        t1 = threading.Thread(target=_real_stream,
                              args=(baseline_url,  model_id, sys_msg, usr_msg, q1), daemon=True)
        t2 = threading.Thread(target=_real_stream,
                              args=(optimized_url, model_id, sys_msg, usr_msg, q2), daemon=True)

    t1.start(); t2.start()

    text1 = text2 = ""
    ttft1 = ttft2 = tps1 = tps2 = n1 = n2 = None
    done1 = done2 = False

    while not (done1 and done2):
        changed = False
        for q, is1 in [(q1, True), (q2, False)]:
            try:
                while True:
                    kind, tok, ttft, tps, n = q.get_nowait()
                    changed = True
                    if kind == "done":
                        if is1: done1 = True; tps1 = tps; n1 = n
                        else:   done2 = True; tps2 = tps; n2 = n
                    elif kind == "token":
                        if is1:
                            if tok:  text1 += tok
                            if ttft: ttft1 = ttft
                        else:
                            if tok:  text2 += tok
                            if ttft: ttft2 = ttft
            except _queue.Empty:
                pass

        if changed:
            cur1 = "" if done1 else " ▌"
            cur2 = "" if done2 else " ▌"
            ph_t1.write(text1 + cur1)
            ph_t2.write(text2 + cur2)
            if ttft1:
                tps_str = f" · <strong>{tps1:.1f} tok/s</strong>" if tps1 else ""
                ph_m1.markdown(f'<p class="live-meta">TTFT <strong>{ttft1:.0f} ms</strong>{tps_str}</p>',
                               unsafe_allow_html=True)
            if ttft2:
                tps_str = f" · <strong>{tps2:.1f} tok/s</strong>" if tps2 else ""
                ph_m2.markdown(f'<p class="live-meta">TTFT <strong>{ttft2:.0f} ms</strong>{tps_str}</p>',
                               unsafe_allow_html=True)

        _time.sleep(0.025)

    # Final render
    ph_t1.markdown(text1)
    ph_t2.markdown(text2)

    return dict(text1=text1, text2=text2,
                ttft1=ttft1, ttft2=ttft2,
                tps1=tps1,  tps2=tps2,
                n1=n1, n2=n2, simulated=simulated)


def render_live_section(data: dict):
    demo_prompts = data.get("demo_prompts", [])
    if not demo_prompts:
        return

    services  = data.get("services", {})
    meta      = data.get("meta", {})
    framework = meta.get("framework", "Model")

    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Live Side-by-Side</p>', unsafe_allow_html=True)

    # ── Prompt selector ────────────────────────────────────────────────────
    prompt_idx = st.selectbox(
        "Curated prompt",
        range(len(demo_prompts)),
        format_func=lambda i: demo_prompts[i]["label"],
        key="live_prompt_sel",
    )
    prompt = demo_prompts[prompt_idx]

    # ── Single user message above both columns ──────────────────────────────
    with st.chat_message("user"):
        st.write(prompt["user"])

    btn_col, _ = st.columns([1, 3])
    with btn_col:
        run = st.button("▶  Run comparison", key="live_run")

    # ── Session state for result persistence ───────────────────────────────
    result_key = f"live_{meta.get('config_id','')}_{prompt_idx}"
    if st.session_state.get("_live_key") != result_key:
        # prompt or config changed — clear old result
        st.session_state["_live_key"]    = result_key
        st.session_state["_live_result"] = None

    # ── Response columns (assistant only) ──────────────────────────────────
    col1, col2 = st.columns(2, gap="medium")

    has_result = bool(st.session_state.get("_live_result"))
    frame_h = 420 if (has_result or run) else "content"

    with col1:
        st.markdown(
            f'<div class="live-col-hdr">'
            f'<span class="live-col-title">Stock {framework}</span>'
            f'<span class="live-lbl-base">Baseline</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.container(height=frame_h, border=False):
            with st.chat_message("assistant"):
                ph_t1 = st.empty()
        ph_m1 = st.empty()

    with col2:
        st.markdown(
            f'<div class="live-col-hdr" style="border-bottom:1px solid #d0f5e8">'
            f'<span class="live-col-title">{framework} + Artemis</span>'
            f'<span class="live-lbl-opt">+ Artemis</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.container(height=frame_h, border=False):
            with st.chat_message("assistant"):
                ph_t2 = st.empty()
        ph_m2 = st.empty()

    ph_speedup = st.empty()

    # ── Run or restore ─────────────────────────────────────────────────────
    if run:
        result = _run_comparison(prompt, services, meta, ph_t1, ph_t2, ph_m1, ph_m2)
        st.session_state["_live_result"] = result
        st.rerun()

    elif st.session_state.get("_live_result"):
        r = st.session_state["_live_result"]
        ph_t1.markdown(r["text1"])
        ph_t2.markdown(r["text2"])
        _show_speedup(r, ph_speedup, ph_m1, ph_m2, data, speedup_in_box=True)


def _show_speedup(r: dict, ph_speedup, ph_m1, ph_m2, data: dict, speedup_in_box: bool = False):
    ttft1, ttft2 = r.get("ttft1"), r.get("ttft2")
    tps1,  tps2  = r.get("tps1"),  r.get("tps2")
    if ttft1:
        s = f" · <strong>{tps1:.1f} tok/s</strong>" if tps1 else ""
        ph_m1.markdown(f'<p class="live-meta">TTFT <strong>{ttft1:.0f} ms</strong>{s}</p>',
                       unsafe_allow_html=True)
    if ttft2:
        s = f" · <strong>{tps2:.1f} tok/s</strong>" if tps2 else ""
        ph_m2.markdown(f'<p class="live-meta">TTFT <strong>{ttft2:.0f} ms</strong>{s}</p>',
                       unsafe_allow_html=True)
    if tps1 and tps2 and not speedup_in_box:
        ratio = tps2 / max(tps1, 0.001)
        ph_speedup.markdown(
            f'<div class="speedup-callout">'
            f'<span class="speedup-num">{ratio:.2f}×</span>'
            f'<span style="display:block;font-size:1.1rem;font-weight:600;color:#333;margin-bottom:0.3rem">Optimised model ran faster on this prompt</span>'
            f'<span class="speedup-sub">Same prompt &nbsp;·&nbsp; Same model &nbsp;·&nbsp; Same hardware</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Token race component ──────────────────────────────────────────────────────

_RACE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:transparent;padding:0 1px 4px}
.race-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
.rcard{background:rgba(255,255,255,0.05);border:1px solid rgba(124,115,255,0.22);border-radius:12px;padding:1rem 1.1rem;display:flex;flex-direction:column;min-height:148px}
.rcard-opt{border-color:rgba(26,213,152,0.28);background:rgba(26,213,152,0.04)}
.rcard-hdr{display:flex;align-items:center;justify-content:space-between;padding-bottom:0.5rem;border-bottom:1px solid rgba(124,115,255,0.14);margin-bottom:0.6rem}
.rcard-hdr-opt{border-bottom-color:rgba(26,213,152,0.18)}
.rtitle{font-size:0.87rem;font-weight:700;color:rgba(255,255,255,0.88)}
.rtitle-opt{color:#7C73FF}
.hdr-r{display:flex;align-items:center;gap:6px}
.badge{border-radius:20px;padding:0.12rem 0.6rem;font-size:0.68rem;font-weight:700}
.br{background:rgba(124,115,255,0.18);color:#a09aff}
.bd-b{background:rgba(124,115,255,0.18);color:#b0aaff;display:none}
.bd-a{background:rgba(26,213,152,0.18);color:#1AD598;display:none}
.rtime{font-size:0.82rem;font-weight:700;color:rgba(255,255,255,0.45);display:none}
.ttft-hit{font-size:0.69rem;font-weight:600;min-height:0.95rem;margin-bottom:5px}
.cnt-row{display:flex;align-items:baseline;gap:5px;margin:2px 0 5px}
.cnt{font-size:2rem;font-weight:800;color:rgba(255,255,255,0.95);min-width:3ch;font-variant-numeric:tabular-nums;line-height:1}
.cunit{font-size:0.68rem;color:rgba(255,255,255,0.28);text-transform:uppercase;letter-spacing:0.4px}
.bar-bg{background:rgba(255,255,255,0.08);border-radius:3px;height:4px;overflow:hidden}
.bar{height:4px;border-radius:3px;width:0%}
.bar-b{background:#7C73FF}.bar-a{background:#1AD598}
.txt-ph{display:none;font-size:0.78rem;color:rgba(255,255,255,0.75);line-height:1.5;max-height:90px;overflow-y:auto;margin-bottom:4px;flex:1}
.txt-ph strong{color:rgba(255,255,255,0.95)}
.rcard-foot{display:flex;gap:10px;font-size:0.71rem;color:rgba(255,255,255,0.28);padding-top:6px;margin-top:auto;border-top:1px solid rgba(124,115,255,0.1)}
.rcard-foot-opt{border-top-color:rgba(26,213,152,0.12)}
.fv{font-weight:700;color:rgba(255,255,255,0.82)}
.metrics{display:none;grid-template-columns:1fr 1fr 1fr;gap:9px;margin-bottom:10px}
.mc{background:rgba(255,255,255,0.05);border:1px solid rgba(124,115,255,0.2);border-radius:10px;padding:0.85rem 1rem}
.mc-lbl{font-size:0.57rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.28);margin-bottom:8px}
.mc-pct{font-size:2.2rem;font-weight:900;line-height:1;letter-spacing:-1px;margin-bottom:6px}
.mc-pct-up{color:#1AD598}
.mc-pct-dn{color:#7C73FF}
.mc-arrow{font-size:0.72rem;color:rgba(255,255,255,0.38);line-height:1.4}
.mc-arrow .arr-old{color:rgba(255,255,255,0.28);text-decoration:line-through}
.mc-arrow .arr-new{color:rgba(255,255,255,0.75);font-weight:600}
.mc-arrow .arr-sep{margin:0 3px;color:rgba(255,255,255,0.2)}
.callout{display:none;background:rgba(26,213,152,0.04);border:1.5px solid rgba(26,213,152,0.3);border-radius:12px;padding:1rem 1.4rem;margin-bottom:10px;text-align:center}
.cal-pills{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;justify-content:center}
.cal-pill{background:rgba(26,213,152,0.12);color:#1AD598;border:1px solid rgba(26,213,152,0.25);border-radius:20px;padding:0.18rem 0.75rem;font-size:0.7rem;font-weight:700}
.cal-headline{font-size:1.05rem;font-weight:800;color:#ffffff;margin-bottom:6px;letter-spacing:-0.3px}
.cal-note{font-size:0.68rem;color:rgba(255,255,255,0.28);line-height:1.4}
.play-bar{display:flex;justify-content:center;padding-top:4px}
.playbtn{background:#7C73FF;color:white;border:none;border-radius:50px;padding:0.44rem 1.5rem;font-size:0.84rem;font-weight:600;cursor:pointer;transition:opacity .15s}
.playbtn:hover:not(:disabled){opacity:0.85}
.playbtn:disabled{background:rgba(124,115,255,0.3);color:rgba(255,255,255,0.35);cursor:default}
.dummy-keep{color:#bbb}
.speed-wrap{display:flex;align-items:center;gap:4px}
</style></head><body>
<div class="race-grid">
  <div class="rcard">
    <div class="rcard-hdr">
      <span class="rtitle">Stock __FW__</span>
      <div class="hdr-r">
        <span class="badge br" id="br-b">Racing…</span>
        <span class="badge bd-b" id="bd-b">Done</span>
        <span class="rtime" id="tm-b"></span>
      </div>
    </div>
    <div id="cp-b">
      <div class="ttft-hit" id="tf-b" style="color:rgba(255,255,255,0.2);font-style:italic">waiting for first token…</div>
      <div class="cnt-row"><span class="cnt" id="cb">0</span><span class="cunit">tokens</span></div>
      <div class="bar-bg"><div class="bar bar-b" id="bb"></div></div>
    </div>
    <div class="txt-ph" id="tx-b">__BASE_TEXT__</div>
    <div class="rcard-foot">
      <span>TTFT <span class="fv">__BT_D__ ms</span></span>
      <span>Speed <span class="fv">__BS_D__ tok/s</span></span>
    </div>
  </div>
  <div class="rcard rcard-opt">
    <div class="rcard-hdr rcard-hdr-opt">
      <span class="rtitle rtitle-opt">⚡ Artemis-optimised</span>
      <div class="hdr-r">
        <span class="badge br" id="br-a">Racing…</span>
        <span class="badge bd-a" id="bd-a">Done</span>
        <span class="rtime" id="tm-a"></span>
      </div>
    </div>
    <div id="cp-a">
      <div class="ttft-hit" id="tf-a" style="color:rgba(255,255,255,0.2);font-style:italic">waiting for first token…</div>
      <div class="cnt-row"><span class="cnt" id="ca">0</span><span class="cunit">tokens</span></div>
      <div class="bar-bg"><div class="bar bar-a" id="ba"></div></div>
    </div>
    <div class="txt-ph" id="tx-a">__OPT_TEXT__</div>
    <div class="rcard-foot rcard-foot-opt">
      <span>TTFT <span class="fv">__AT_D__ ms</span></span>
      <span>Speed <span class="fv">__AS_D__ tok/s</span></span>
    </div>
  </div>
</div>
<div class="metrics" id="metrics">
  <div class="mc"><div class="mc-lbl">Throughput</div><div class="mc-pct mc-pct-up">__TPUT_PCT__</div><div class="mc-arrow"><span class="arr-old">__BS_D__ tok/s</span><span class="arr-sep">→</span><span class="arr-new">__AS_D__ tok/s</span></div></div>
  <div class="mc"><div class="mc-lbl">Time to First Token</div><div class="mc-pct mc-pct-dn">__TTFT_PCT__</div><div class="mc-arrow"><span class="arr-old">__BT_D__ ms</span><span class="arr-sep">→</span><span class="arr-new">__AT_D__ ms</span></div></div>
  <div class="mc"><div class="mc-lbl">Cost per 1M Tokens</div><div class="mc-pct mc-pct-dn">__COST_PCT__</div><div class="mc-arrow"><span class="arr-old">$__COST_B__</span><span class="arr-sep">→</span><span class="arr-new">$__COST_O__</span></div></div>
</div>
<div class="callout" id="callout">
  <div class="cal-pills"><span class="cal-pill">✓ Same model</span><span class="cal-pill">✓ Same hardware</span><span class="cal-pill">✓ Quality intact</span></div>
  <div class="cal-headline">No tradeoffs. Just faster, cheaper inference.</div>
  <div class="cal-note">Quality validated via semantic similarity ≥ 0.92 (all-MiniLM-L6-v2, 50 runs per scenario)</div>
</div>
<div class="play-bar"><button class="playbtn" id="pb" onclick="start()">&#9654; Play race</button></div>
<script>
var BT=__BT__,BS=__BS__,AT=__AT__,AS=__AS__,TOT=__TOT__;
var t0=null,raf=null,bdone=false,adone=false,blit=false,alit=false;
function reset(){
  document.getElementById('cb').textContent='0';document.getElementById('ca').textContent='0';
  document.getElementById('bb').style.width='0%';document.getElementById('ba').style.width='0%';
  document.getElementById('tf-b').innerHTML='<span style="color:rgba(255,255,255,0.2);font-style:italic">waiting\u2026</span>';
  document.getElementById('tf-a').innerHTML='<span style="color:rgba(255,255,255,0.2);font-style:italic">waiting\u2026</span>';
  ['b','a'].forEach(function(s){
    document.getElementById('cp-'+s).style.display='';document.getElementById('tx-'+s).style.display='none';
    document.getElementById('br-'+s).style.display='';document.getElementById('bd-'+s).style.display='none';
    document.getElementById('tm-'+s).style.display='none';
  });
  document.getElementById('metrics').style.display='none';document.getElementById('callout').style.display='none';
  try{var u=new URL(window.parent.location.href);u.searchParams.delete('_rd');window.parent.history.replaceState({},'',u.toString());}catch(e){}
  bdone=false;adone=false;blit=false;alit=false;
}
function fin(s,sec){
  document.getElementById('br-'+s).style.display='none';document.getElementById('bd-'+s).style.display='inline-block';
  var tm=document.getElementById('tm-'+s);tm.textContent=sec.toFixed(1)+'s';tm.style.display='inline-block';
  document.getElementById('cp-'+s).style.display='none';document.getElementById('tx-'+s).style.display='block';
}
function start(){
  if(raf)cancelAnimationFrame(raf);reset();t0=null;
  document.getElementById('pb').disabled=true;document.getElementById('pb').textContent='\u23f3 Racing\u2026';
  raf=requestAnimationFrame(tick);
}
function tick(ts){
  if(!t0)t0=ts;var e=(ts-t0)/1000;
  var be=Math.max(0,e-BT/1000),btok=Math.min(Math.floor(be*BS),TOT);
  document.getElementById('cb').textContent=btok;document.getElementById('bb').style.width=(btok/TOT*100)+'%';
  if(!blit&&e>=BT/1000){blit=true;document.getElementById('tf-b').innerHTML='<span style="color:#7C73FF;font-weight:700">\u26a1 First token \u2014 '+BT+' ms</span>';}
  if(btok>=TOT&&!bdone){bdone=true;fin('b',BT/1000+TOT/BS);}
  var ae=Math.max(0,e-AT/1000),atok=Math.min(Math.floor(ae*AS),TOT);
  document.getElementById('ca').textContent=atok;document.getElementById('ba').style.width=(atok/TOT*100)+'%';
  if(!alit&&e>=AT/1000){alit=true;document.getElementById('tf-a').innerHTML='<span style="color:#1AD598;font-weight:700">\u26a1 First token \u2014 '+AT+' ms</span>';}
  if(atok>=TOT&&!adone){adone=true;fin('a',AT/1000+TOT/AS);}
  if(!bdone||!adone){raf=requestAnimationFrame(tick);}
  else{document.getElementById('metrics').style.display='grid';document.getElementById('callout').style.display='block';document.getElementById('pb').disabled=false;document.getElementById('pb').textContent='\u21ba Play again';try{var u=new URL(window.parent.location.href);u.searchParams.set('_rd','1');window.parent.history.replaceState({},'',u.toString());}catch(e){}}
}
</script></body></html>"""


def _prep_response_text(text: str) -> str:
    import re
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n\n', '<br><br>').replace('\n', ' ')
    return text


def render_token_race(data: dict):
    demo_prompts = data.get("demo_prompts", [])
    if not demo_prompts:
        return

    meta      = data.get("meta", {})
    framework = meta.get("framework", "Model")
    fw_short  = framework.split()[0] if framework else "Model"

    st.markdown('<hr style="border:none;border-top:1px solid rgba(124,115,255,0.18);margin:1rem 0 0.5rem">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Token Race</p>', unsafe_allow_html=True)
    prompt_idx = st.selectbox(
        "Curated prompt",
        range(len(demo_prompts)),
        format_func=lambda i: demo_prompts[i]["label"],
        key="live_prompt_sel",
    )
    prompt = demo_prompts[prompt_idx]

    with st.chat_message("user"):
        st.write(prompt["user"])

    recorded  = prompt.get("recorded", {})
    base_rec  = recorded.get("baseline", {})
    opt_rec   = recorded.get("optimized", {})

    base_ttft = float(base_rec.get("ttft_ms", 1000))
    base_tps  = float(base_rec.get("tps", 40))
    opt_ttft  = float(opt_rec.get("ttft_ms", 800))
    opt_tps   = float(opt_rec.get("tps", 60))
    total_tok = max(len(base_rec.get("text", "").split()), 1)

    base_text = _prep_response_text(base_rec.get("text", ""))
    opt_text  = _prep_response_text(opt_rec.get("text", ""))

    tput_pct = f"+{(opt_tps - base_tps) / base_tps * 100:.0f}%"
    ttft_pct = f"\u2212{(base_ttft - opt_ttft) / base_ttft * 100:.0f}%"
    ttft_abs = f"{(base_ttft - opt_ttft) / base_ttft * 100:.0f}%"
    ratio    = f"{opt_tps / base_tps:.2f}"

    acc    = data.get("correctness", {}).get("accuracy", {})
    cost_b = acc.get("cost_per_1m", {}).get("baseline") or 0
    cost_o = acc.get("cost_per_1m", {}).get("optimized") or 0
    cost_pct = f"\u2212{(cost_b - cost_o) / cost_b * 100:.0f}%" if cost_b else "\u2014"
    cost_abs = f"{(cost_b - cost_o) / cost_b * 100:.0f}%"      if cost_b else "\u2014"

    html_out = (
        _RACE_HTML
        .replace("__FW__",        fw_short)
        .replace("__BT_D__",      str(int(base_ttft)))
        .replace("__AT_D__",      str(int(opt_ttft)))
        .replace("__BS_D__",      f"{base_tps:.1f}")
        .replace("__AS_D__",      f"{opt_tps:.1f}")
        .replace("__BT__",        str(int(base_ttft)))
        .replace("__BS__",        str(base_tps))
        .replace("__AT__",        str(int(opt_ttft)))
        .replace("__AS__",        str(opt_tps))
        .replace("__TOT__",       str(total_tok))
        .replace("__BASE_TEXT__", base_text)
        .replace("__OPT_TEXT__",  opt_text)
        .replace("__TPUT_PCT__",  tput_pct)
        .replace("__TTFT_PCT__",  ttft_pct)
        .replace("__TTFT_ABS__",  ttft_abs)
        .replace("__COST_B__",    f"{cost_b:.2f}")
        .replace("__COST_O__",    f"{cost_o:.2f}")
        .replace("__COST_PCT__",  cost_pct)
        .replace("__COST_ABS__",  cost_abs)
        .replace("__RATIO__",     ratio)
    )

    st.components.v1.html(html_out, height=500, scrolling=False)


# ── Section renderers ─────────────────────────────────────────────────────────

def render_config_section(configs: list, active_id: str):
    st.markdown('<p class="slabel">Configuration</p>', unsafe_allow_html=True)

    cur = next((c for c in configs if c["config_id"] == active_id), configs[0])

    # Cascade: Model → Framework → Hardware
    m_opts = sorted(set(c["model"] for c in configs))
    col_m, col_fw, col_hw = st.columns(3)

    with col_m:
        def_m = cur["model"] if cur["model"] in m_opts else m_opts[0]
        sel_m = st.selectbox("Model", m_opts, index=m_opts.index(def_m))

    fw_opts = sorted(set(c["framework"] for c in configs if c["model"] == sel_m))
    with col_fw:
        def_fw = cur["framework"] if (cur["model"] == sel_m and cur["framework"] in fw_opts) else (fw_opts[0] if fw_opts else "")
        sel_fw = st.selectbox("Framework", fw_opts, index=fw_opts.index(def_fw) if def_fw in fw_opts else 0)

    hw_opts = sorted(set(c["hardware"] for c in configs if c["model"] == sel_m and c["framework"] == sel_fw))
    with col_hw:
        def_hw = cur["hardware"] if (cur["model"] == sel_m and cur["framework"] == sel_fw and cur["hardware"] in hw_opts) else (hw_opts[0] if hw_opts else "")
        sel_hw = st.selectbox("Hardware", hw_opts, index=hw_opts.index(def_hw) if def_hw in hw_opts else 0)

    matched = next(
        (c for c in configs if c["hardware"] == sel_hw and c["framework"] == sel_fw and c["model"] == sel_m),
        None,
    )
    return matched["config_id"] if matched else None


def render_spec_bar(data: dict):
    meta  = data.get("meta", {})
    specs = meta.get("hardware_specs", {})
    tier  = tier_badge(specs.get("spec_tier", ""))

    spec_parts = []
    if specs.get("cores"):     spec_parts.append(f'{specs["cores"]} cores')
    if specs.get("ram_gb"):    spec_parts.append(f'{specs["ram_gb"]} GB RAM')
    if specs.get("bandwidth_gbs"): spec_parts.append(f'{specs["bandwidth_gbs"]} GB/s')
    if specs.get("tdp_w"):     spec_parts.append(f'{specs["tdp_w"]} W')
    spec_str = " · ".join(spec_parts)

    hw_sub = f'<span class="specs-muted">{spec_str}</span>' if spec_str else ""
    html = (
        f'<div class="spec-bar">'
        f'<div class="spec-bar-item">'
        f'<span class="lbl">Model</span>'
        f'<span class="val">{meta.get("model","")}</span>'
        f'</div>'
        f'<div class="spec-bar-item">'
        f'<span class="lbl">Framework</span>'
        f'<span class="val">{meta.get("framework","")}</span>'
        f'</div>'
        f'<div class="spec-bar-item">'
        f'<span class="lbl">Hardware</span>'
        f'<span class="val">{meta.get("hardware","")}&nbsp;{tier}</span>'
        f'{hw_sub}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_benchmark(data: dict):
    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Validated Benchmark</p>', unsafe_allow_html=True)

    note = data.get("benchmark", {}).get(
        "description_note",
        "Averaged over N=20 runs. Baseline vs Artemis-rewritten configuration.",
    )
    st.markdown(
        f'<p style="font-size:0.82rem;color:rgba(255,255,255,0.4);margin:0 0 1rem 0;'
        f'font-family:Inter,-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">{note}</p>',
        unsafe_allow_html=True,
    )

    tab_seq, tab_con = st.tabs([
        "Sequential — validation mode",
        "Concurrent — throughput mode",
    ])
    with tab_seq:
        st.markdown(benchmark_table_html(data, "sequential"), unsafe_allow_html=True)
    with tab_con:
        st.markdown(benchmark_table_html(data, "concurrent"), unsafe_allow_html=True)


def render_correctness(data: dict):
    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Correctness Validation</p>', unsafe_allow_html=True)

    validations = data.get("correctness", {}).get("validations", [])
    items_html = ""
    for v in validations:
        icon = "✅" if v.get("pass") else "❌"
        items_html += (
            f'<div class="val-row">'
            f'<span class="val-icon">{icon}</span>'
            f'<div>'
            f'<div class="val-name">{v["name"]}</div>'
            f'<div class="val-note">{v.get("note", "")}</div>'
            f'</div></div>'
        )
    st.markdown(f'<div class="val-card">{items_html}</div>', unsafe_allow_html=True)


def render_cross_hardware(data: dict):
    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Built for Your Stack</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.82rem;color:rgba(255,255,255,0.4);margin:0 0 1rem 0;'
        'font-family:Inter,-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'
        'Each optimization is purpose-built for a specific hardware + model combo — '
        'we have a version for your exact setup.'
        '</p>',
        unsafe_allow_html=True,
    )

    entries = data.get("cross_hardware", [])
    max_delta = max((e.get("throughput_delta_pct", 0) for e in entries), default=60)

    tbody = ""
    for hw in entries:
        d_pct    = hw.get("throughput_delta_pct", 0)
        pbar     = progress_bar_html(d_pct, max_delta)
        link     = f'<a class="view-link" href="?config={hw["config_id"]}">View →</a>' if hw.get("config_id") else ""
        tbody += (
            f'<tr>'
            f'<td><span class="hw-name">{hw.get("model","")}</span></td>'
            f'<td><span class="hw-name">{hw.get("hardware","")}</span>&nbsp;{tier_badge(hw.get("spec_tier",""))}</td>'
            f'<td style="color:#666">{hw.get("framework","")}</td>'
            f'<td style="color:#888;font-size:0.82rem">{hw.get("optimization","")}</td>'
            f'<td>{pbar}</td>'
            f'<td>{verdict_html(hw.get("verdict",""))}</td>'
            f'<td>{link}</td>'
            f'</tr>'
        )

    table_html = (
        '<div class="hw-wrap">'
        '<table class="hw-table">'
        '<thead><tr>'
        '<th>Model</th><th>Hardware</th><th>Framework</th>'
        '<th>Optimization</th><th>Throughput Δ</th><th>Verdict</th><th></th>'
        '</tr></thead>'
        f'<tbody>{tbody}</tbody>'
        '</table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_share_export(data: dict, config_id: str):
    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Share & Export</p>', unsafe_allow_html=True)

    col_url, col_dl = st.columns([3, 1])

    with col_url:
        st.markdown(
            f'<div class="share-url">?config={config_id}</div>',
            unsafe_allow_html=True,
        )
        st.caption("Append this to the dashboard URL to share the current view.")

    with col_dl:
        st.download_button(
            label="Download as markdown",
            data=build_markdown_report(data, config_id),
            file_name=f"artemis-{config_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )


# ── Markdown report builder ───────────────────────────────────────────────────

def build_markdown_report(data: dict, config_id: str) -> str:
    meta = data.get("meta", {})
    lines = [
        "# Artemis LLM Optimization Report",
        "",
        f"**Config:** `{config_id}`",
        f"**Model:** {meta.get('model', '')}",
        f"**Hardware:** {meta.get('hardware', '')}",
        f"**Framework:** {meta.get('framework', '')}",
        "",
        "---",
        "",
        "## Benchmark Results",
        "",
    ]

    metrics_map = [
        ("Throughput (tok/s)", "throughput_tps", False),
        ("TTFT (ms)",          "ttft_ms",        True),
        ("P95 Latency (ms)",   "p95_ms",         True),
        ("P99 Latency (ms)",   "p99_ms",         True),
        ("Variance CV",        "variance_cv",    True),
    ]

    for sc_key, sc in data.get("benchmark", {}).get("scenarios", {}).items():
        lines.append(f"### {sc.get('label', sc_key)}")
        lines.append(f"> {sc.get('description', '')}")
        lines.append("")
        for mode in ["sequential", "concurrent"]:
            if mode not in sc:
                continue
            lines += [
                f"**{mode.title()}**",
                "",
                "| Metric | Baseline | + Artemis | Δ |",
                "|--------|----------|-----------|---|",
            ]
            for lbl, key, lib in metrics_map:
                if key not in sc[mode]:
                    continue
                b = sc[mode][key]["baseline"]
                o = sc[mode][key]["optimized"]
                d = pct_delta(b, o)
                sign = "+" if d > 0 else ""
                lines.append(f"| {lbl} | {b} | {o} | {sign}{d:.1f}% |")
            lines.append("")

    acc = data.get("correctness", {}).get("accuracy", {})
    lines += [
        "## Accuracy & Cost",
        "",
        "| Metric | Baseline | + Artemis | Δ |",
        "|--------|----------|-----------|---|",
    ]
    for key, lbl, unit, lib in [
        ("mmlu",        "MMLU",          "%",  False),
        ("hellaswag",   "HellaSwag",     "%",  False),
        ("cost_per_1m", "Cost / 1M tok", "$",  True),
    ]:
        a = acc.get(key)
        if a:
            b, o = a["baseline"], a["optimized"]
            d = pct_delta(b, o)
            sign = "+" if d > 0 else ""
            lines.append(f"| {lbl} | {b}{unit} | {o}{unit} | {sign}{d:.1f}% |")

    lines += [
        "",
        "## Correctness Validation",
        "",
    ]
    for v in data.get("correctness", {}).get("validations", []):
        mark = "✅" if v.get("pass") else "❌"
        lines.append(f"- {mark} **{v['name']}**: {v.get('note', '')}")

    lines += [
        "",
        "## Cross-Hardware Results",
        "",
        "| Class | Hardware | Framework | Throughput Δ | Accuracy | Verdict |",
        "|-------|----------|-----------|--------------|----------|---------|",
    ]
    for hw in data.get("cross_hardware", []):
        d = hw.get("throughput_delta_pct", 0)
        sign = "+" if d >= 0 else ""
        acc_d = hw.get("accuracy_delta", 0)
        lines.append(
            f"| {hw.get('class','')} | {hw['hardware']} | {hw.get('framework','')} "
            f"| {sign}{d}% | ±{abs(acc_d):.2f} MMLU | {hw.get('verdict','').title()} |"
        )

    return "\n".join(lines)


# ── Performance charts ────────────────────────────────────────────────────────

_CHART_SCENARIOS = ["small_prompt", "large_prompt", "long_context"]
_SCENARIO_LABELS = {"small_prompt": "Small Prompt", "large_prompt": "Large Prompt", "long_context": "Long Context"}
_COL_BASE = "#1AD598"
_COL_OPT  = "#7C73FF"

def _bar_chart(labels, base_vals, opt_vals, title, unit):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Baseline",
        x=labels,
        y=base_vals,
        marker_color=_COL_BASE,
        text=[f"{v} {unit}" for v in base_vals],
        textposition="outside",
        textfont=dict(size=11, color="#1AD598"),
    ))
    fig.add_trace(go.Bar(
        name="+ Artemis",
        x=labels,
        y=opt_vals,
        marker_color=_COL_OPT,
        text=[f"{v} {unit}" for v in opt_vals],
        textposition="outside",
        textfont=dict(size=11, color="#7C73FF"),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.75)"), x=0),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color="rgba(255,255,255,0.75)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)", zeroline=False,
                   tickfont=dict(color="rgba(255,255,255,0.35)", size=11)),
        xaxis=dict(tickfont=dict(color="rgba(255,255,255,0.65)", size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=12, color="rgba(255,255,255,0.75)")),
        margin=dict(t=60, b=20, l=20, r=20),
        height=280,
    )
    return fig


def render_cost_savings(data: dict):
    accuracy = data.get("correctness", {}).get("accuracy", {})
    cost_base = accuracy.get("cost_per_1m", {}).get("baseline")
    cost_opt  = accuracy.get("cost_per_1m", {}).get("optimized")
    if not cost_base or not cost_opt:
        return

    monthly_m = st.session_state.get("monthly_tokens_m", 500)
    saving_per_1m   = cost_base - cost_opt
    saving_pct      = saving_per_1m / cost_base * 100
    monthly_saving  = saving_per_1m * monthly_m
    annual_saving   = monthly_saving * 12

    F = "font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    st.markdown(
        f'<p style="font-size:0.85rem;color:rgba(255,255,255,0.4);margin:0 0 1.2rem;{F}">'
        f'Based on <strong style="color:rgba(255,255,255,0.85)">{monthly_m}M tokens/month</strong></p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    def _card(col, label, value, sub, accent="#ffffff"):
        col.markdown(
            f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(124,115,255,0.2);border-radius:12px;'
            f'box-shadow:0 4px 20px rgba(0,0,0,0.25);padding:1.1rem 1.2rem;{F}">'
            f'<div style="font-size:0.6rem;font-weight:700;letter-spacing:1.6px;'
            f'text-transform:uppercase;color:rgba(255,255,255,0.28);margin-bottom:0.55rem">{label}</div>'
            f'<div style="font-size:1.85rem;font-weight:900;color:{accent};line-height:1;letter-spacing:-0.5px">{value}</div>'
            f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.33);margin-top:0.45rem">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _card(c1, "Cost per 1M tokens",   f"${cost_opt:.2f}",         f"down from ${cost_base:.2f}", "#ffffff")
    _card(c2, "Saving per 1M tokens", f"${saving_per_1m:.2f}",    f"{saving_pct:.0f}% reduction", "#1AD598")
    _card(c3, "Monthly saving",        f"${monthly_saving:,.0f}", f"at {monthly_m}M tok/mo",      "#1AD598")
    _card(c4, "Annual saving",         f"${annual_saving:,.0f}",  "projected over 12 months",     "#1AD598")


def render_performance_charts(data: dict):
    scenarios = data.get("benchmark", {}).get("scenarios", {})
    if not scenarios:
        return

    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Performance Results</p>', unsafe_allow_html=True)

    labels     = [_SCENARIO_LABELS.get(s, s) for s in _CHART_SCENARIOS if s in scenarios]
    tput_base  = [scenarios[s]["sequential"]["throughput_tps"]["baseline"]  for s in _CHART_SCENARIOS if s in scenarios]
    tput_opt   = [scenarios[s]["sequential"]["throughput_tps"]["optimized"] for s in _CHART_SCENARIOS if s in scenarios]
    ttft_base  = [scenarios[s]["sequential"]["ttft_ms"]["baseline"]         for s in _CHART_SCENARIOS if s in scenarios]
    ttft_opt   = [scenarios[s]["sequential"]["ttft_ms"]["optimized"]        for s in _CHART_SCENARIOS if s in scenarios]

    ch1, ch2 = st.columns(2, gap="medium")
    with ch1:
        st.plotly_chart(
            _bar_chart(labels, tput_base, tput_opt, "Throughput (higher is better)", "tok/s"),
            use_container_width=True, config={"displayModeBar": False},
        )
    with ch2:
        st.plotly_chart(
            _bar_chart(labels, ttft_base, ttft_opt, "Time to First Token (lower is better)", "ms"),
            use_container_width=True, config={"displayModeBar": False},
        )


def render_accuracy(data: dict):
    validations = data.get("correctness", {}).get("validations", [])
    if not validations:
        return

    all_pass = all(v.get("pass", False) for v in validations)
    n_pass   = sum(1 for v in validations if v.get("pass", False))
    n_total  = len(validations)

    banner_bg    = "rgba(26,213,152,0.08)" if all_pass else "rgba(248,113,113,0.08)"
    banner_border = "rgba(26,213,152,0.3)" if all_pass else "rgba(248,113,113,0.3)"
    banner_color  = "#1AD598" if all_pass else "#f87171"
    banner_icon   = "✓" if all_pass else "✗"
    banner_text   = f"All {n_total} checks passed — semantic equivalence verified" if all_pass else f"{n_pass} / {n_total} checks passed"

    layer_icons = ["①", "②", "③", "④", "⑤", "⑥"]

    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Output Correctness</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.85rem;color:rgba(255,255,255,0.4);margin:-0.5rem 0 1.2rem;'
        'font-family:Inter,-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'
        'Independent validation layers confirm the optimised model produces '
        'semantically identical outputs to the baseline.</p>',
        unsafe_allow_html=True,
    )

    # ── Banner ────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="background:{banner_bg};border:1.5px solid {banner_border};'
        f'border-radius:10px;padding:1rem 1.4rem;margin-bottom:1.1rem;'
        f'display:flex;align-items:center;gap:0.8rem;'
        f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'
        f'<span style="font-size:1.4rem;color:{banner_color};font-weight:900">{banner_icon}</span>'
        f'<span style="font-size:0.95rem;font-weight:700;color:{banner_color}">{banner_text}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Layer cards (single row) ──────────────────────────────────────────────
    grid_cols = st.columns(len(validations), gap="small")
    for i, v in enumerate(validations):
            col = grid_cols[i]
            passed      = v.get("pass", False)
            card_border = "#d0f5e8" if passed else "#ffc8c8"
            icon_bg     = "#d0f5e8" if passed else "#ffc8c8"
            icon_color  = "#0ea86e" if passed else "#e03c3c"
            check       = "✓" if passed else "✗"
            layer_num   = layer_icons[i] if i < len(layer_icons) else str(i + 1)

            col.markdown(
                f'<div style="background:rgba(255,255,255,0.04);border:1.5px solid {card_border};border-radius:12px;'
                f'box-shadow:0 4px 20px rgba(0,0,0,0.25);padding:1.1rem 1rem;height:100%;'
                f'font-family:Inter,-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'

                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.7rem">'
                f'<span style="font-size:0.8rem;color:rgba(255,255,255,0.25);font-weight:600">{layer_num}</span>'
                f'<div style="margin-left:auto;width:22px;height:22px;border-radius:50%;'
                f'background:{icon_bg};display:flex;align-items:center;justify-content:center;'
                f'font-size:0.75rem;font-weight:800;color:{icon_color}">{check}</div>'
                f'</div>'

                f'<div style="font-size:0.8rem;font-weight:700;color:#ffffff;margin-bottom:0.3rem">'
                f'{v.get("name","")}</div>'

                f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.38);line-height:1.45;margin-bottom:0.6rem">'
                f'{v.get("description","")}</div>'

                f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.6);background:rgba(255,255,255,0.05);'
                f'border-radius:5px;padding:0.4rem 0.55rem;line-height:1.4">'
                f'{v.get("note","")}</div>'

                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Model accuracy (MMLU / HellaSwag) ─────────────────────────────────────


def _race_results_fragment():
    _d = st.session_state.get("_race_data")
    if _d:
        render_performance_charts(_d)
        render_accuracy(_d)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # ── Logo header ───────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'padding-bottom:2rem;border-bottom:1px solid rgba(124,115,255,0.18);margin-bottom:2rem">'
        f'<img src="data:image/svg+xml;base64,{_TURINTECH_B64}" style="height:32px;object-fit:contain">'
        f'<img src="data:image/png;base64,{_ARTEMIS_WM}" style="height:32px;object-fit:contain">'
        f'</div>',
        unsafe_allow_html=True,
    )

    url_config = st.query_params.get("config", "")
    configs    = list_configs()

    if not configs:
        st.error("No JSON configs found in `data/`. Create one to get started.")
        st.stop()

    valid_ids = {c["config_id"] for c in configs}
    active_id = url_config if url_config in valid_ids else configs[0]["config_id"]

    # ── Top: Configuration ────────────────────────────────────────────────
    selected_id = render_config_section(configs, active_id)

    if not selected_id:
        st.warning("No matching configuration found.")
        st.stop()

    if selected_id != url_config:
        st.query_params["config"] = selected_id

    data = load_config(selected_id)
    if not data:
        st.error(f"Could not load config: `{selected_id}`")
        st.stop()

    render_spec_bar(data)

    st.session_state["_race_data"] = data

    render_token_race(data)
    _race_results_fragment()

    # ── HIDDEN: Live comparison (kept for future use) ─────────────────────
    # render_live_section(data)

    # ── Cost savings ─────────────────────────────────────────────────────
    st.markdown('<hr style="border:none;border-top:1px solid rgba(124,115,255,0.18);margin:1.5rem 0 1rem">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Inference Cost Savings</p>', unsafe_allow_html=True)
    with st.container(border=True):
        monthly_tokens_m = st.slider(
            "Monthly tokens (millions)",
            min_value=10, max_value=5000, value=500, step=10,
        )
        st.session_state["monthly_tokens_m"] = monthly_tokens_m
        render_cost_savings(data)

    # ── Cross-hardware (only when ≥2 results exist for the same framework) ──
    framework = data.get("meta", {}).get("framework", "")
    hw_entries = data.get("cross_hardware", [])
    fw_results = [e for e in hw_entries if e.get("framework", "") == framework]
    if len(fw_results) >= 2:
        st.markdown('<hr style="border:none;border-top:1px solid rgba(124,115,255,0.18);margin:1.5rem 0 1rem">', unsafe_allow_html=True)
        render_cross_hardware(data)


main()
