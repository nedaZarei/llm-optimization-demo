import streamlit as st
import json
import threading
import queue as _queue
import time as _time
from pathlib import Path
import plotly.graph_objects as go

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
/* ─ Base ─ */
[data-testid="stAppViewContainer"] { background: #ededed; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }
.block-container {
    padding: 2.5rem 3rem 4rem 3rem !important;
    max-width: 1060px !important;
    margin: 0 auto;
}

/* ─ Hide default Streamlit chrome ─ */
footer { display: none; }
#MainMenu { display: none; }

/* ─ Section label (CONFIGURATION, VALIDATED BENCHMARK, …) ─ */
.slabel {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    color: #7C73FF;
    margin: 0 0 0.8rem 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* ─ Spec bar ─ */
.spec-bar {
    background: white;
    border: 1px solid #e0dede;
    border-radius: 8px;
    padding: 0.85rem 1.25rem;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.35rem;
    font-size: 0.85rem;
    color: #333;
    margin-top: 0.85rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.spec-bar .lbl {
    color: #bbb;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
.spec-bar .val { color: #111; font-weight: 600; }
.spec-bar .sep { color: #ddd; margin: 0 0.5rem; font-size: 1rem; line-height: 1; }
.spec-bar .specs-muted { color: #999; font-weight: 400; font-size: 0.82rem; }

/* ─ Spec tier badges ─ */
.badge-high {
    display: inline-block;
    background: #eeecff;
    color: #7C73FF;
    border: 1px solid #c8c4ff;
    border-radius: 4px;
    padding: 0.12rem 0.45rem;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-mid {
    display: inline-block;
    background: #fffbea;
    color: #a16207;
    border: 1px solid #fde68a;
    border-radius: 4px;
    padding: 0.12rem 0.45rem;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-low {
    display: inline-block;
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 0.12rem 0.45rem;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ─ Section divider ─ */
.section-sep {
    border: none;
    border-top: 1.5px solid #e0dede;
    margin: 2.25rem 0 1.75rem 0;
}

/* ─ Benchmark table ─ */
.bm-wrap {
    border: 1px solid #e2e0de;
    border-radius: 8px;
    overflow: visible;   /* must be visible for tooltips to escape */
    background: white;
    /* keep rounded corners visible via clipping on thead first/last cells */
}
.bm-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    border-radius: 8px;
    overflow: hidden;
}
.bm-table thead tr {
    border-bottom: 2px solid #eeecff;
}
.bm-table thead th {
    padding: 0.65rem 1.1rem;
    text-align: left;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.7px;
    text-transform: uppercase;
    color: #bbb;
    background: white;
}
.bm-table thead th:first-child { border-radius: 8px 0 0 0; }
.bm-table thead th:last-child  { border-radius: 0 8px 0 0; }
.bm-table thead th.col-artemis { color: #7C73FF; }
.bm-table tbody td {
    padding: 0.65rem 1.1rem;
    border-bottom: 1px solid #f0effe;
    color: #333;
    vertical-align: middle;
}
.bm-table tbody tr:last-child td { border-bottom: none; }
.bm-table .type-cell {
    font-weight: 700;
    color: #111;
    font-size: 0.875rem;
    border-right: 1px solid #eeecf8;
    white-space: nowrap;
    padding-left: 0.9rem;
}
.bm-table .metric-cell { color: #666; }

/* ─ Group separator between scenario blocks ─ */
.bm-table tr.g-sep td {
    border-top: 2px solid #e8e6f8 !important;
}

/* ─ Tooltip ─ */
.tt {
    cursor: help;
    border-bottom: 1px dashed #c0bce8;
    position: relative;
    display: inline-block;
}
.tt::after {
    content: attr(data-tip);
    position: absolute;
    left: 0;
    top: calc(100% + 7px);
    background: #040442;
    color: #e8e6ff;
    border-radius: 7px;
    padding: 0.45rem 0.75rem;
    font-size: 0.76rem;
    font-weight: 400;
    line-height: 1.45;
    width: 230px;
    white-space: normal;
    z-index: 9999;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.18s ease;
    box-shadow: 0 6px 20px rgba(4, 4, 66, 0.25);
}
.tt:hover::after { opacity: 1; }

/* ─ Delta values ─ */
.d-pos  { color: #1AD598; font-weight: 700; }
.d-neg  { color: #e03131; font-weight: 700; }
.d-neut { color: #aaa;    font-weight: 600; }

/* ─ Cross-hardware table ─ */
.hw-wrap {
    border: 1px solid #e2e0de;
    border-radius: 8px;
    overflow: hidden;
    background: white;
}
.hw-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.hw-table thead tr { border-bottom: 1.5px solid #f0efed; }
.hw-table thead th {
    padding: 0.65rem 1.1rem;
    text-align: left;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.7px;
    text-transform: uppercase;
    color: #bbb;
    background: white;
}
.hw-table tbody td {
    padding: 0.7rem 1.1rem;
    border-bottom: 1px solid #f5f4f2;
    vertical-align: middle;
}
.hw-table tbody tr:last-child td { border-bottom: none; }
.hw-table tbody tr:hover td { background: #fafaf9; }
.hw-name { font-weight: 600; color: #111; }
.hw-class { color: #888; font-size: 0.82rem; }

/* ─ Progress bar ─ */
.pbar-row { display: flex; align-items: center; gap: 0.6rem; }
.pbar-bg  { background: #e8e8e6; border-radius: 3px; height: 5px; width: 80px; flex-shrink: 0; }
.pbar-fg  { background: #1AD598; border-radius: 3px; height: 5px; }

/* ─ Verdict ─ */
.verd-pass { color: #1AD598; font-weight: 700; font-size: 0.82rem; }
.verd-warn { color: #b45309; font-weight: 600; font-size: 0.82rem; }
.verd-fail { color: #e03131; font-weight: 600; font-size: 0.82rem; }

/* ─ Validation list ─ */
.val-card {
    background: white;
    border: 1px solid #e2e0de;
    border-radius: 8px;
    padding: 0.3rem 1.1rem 0.3rem 1.1rem;
}
.val-row {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.65rem 0;
    border-bottom: 1px solid #f5f4f2;
}
.val-row:last-child { border-bottom: none; }
.val-icon { font-size: 0.95rem; margin-top: 0.1rem; flex-shrink: 0; line-height: 1.4; }
.val-name { font-weight: 600; color: #111; font-size: 0.875rem; line-height: 1.35; }
.val-note { font-size: 0.78rem; color: #aaa; margin-top: 0.08rem; }

/* ─ View link ─ */
a.view-link {
    color: #7C73FF;
    font-weight: 600;
    text-decoration: none;
    font-size: 0.83rem;
}
a.view-link:hover { text-decoration: underline; }

/* ─ Share box ─ */
.share-url {
    background: white;
    border: 1px solid #e2e0de;
    border-radius: 7px;
    padding: 0.7rem 1rem;
    font-family: "Menlo", "Monaco", "Courier New", monospace;
    font-size: 0.8rem;
    color: #555;
    word-break: break-all;
    margin: 0.35rem 0 0.4rem 0;
}

/* ─ Tabs ─ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1.5px solid #e0dede;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0;
    font-size: 0.82rem;
    font-weight: 600;
    color: #aaa;
    padding: 0.55rem 1.1rem;
    border-bottom: 2px solid transparent;
    background: transparent;
    letter-spacing: 0.1px;
}
.stTabs [aria-selected="true"] {
    color: #7C73FF !important;
    border-bottom: 2px solid #7C73FF !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 1rem 0 0 0;
}

/* ─ Download button ─ */
.stDownloadButton > button {
    background: #040442 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.55rem 1.2rem !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
}
.stDownloadButton > button:hover {
    background: #0a0a6e !important;
}

/* ─ Selectbox labels ─ */
[data-testid="stSelectbox"] label {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: #555 !important;
}

/* ─ Run comparison button ─ */
[data-testid="stButton"] > button {
    background: #040442 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.5rem !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
}
[data-testid="stButton"] > button:hover {
    background: #0a0a6e !important;
}

/* ─ Live side-by-side ─ */
.why-box {
    background: #f7f6ff;
    border: 1px solid #dcd9ff;
    border-radius: 7px;
    padding: 0.5rem 0.9rem;
    font-size: 0.81rem;
    color: #555;
    margin: 0.5rem 0 0.8rem 0;
    line-height: 1.5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}


.live-col-hdr {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #f0efed;
    margin-bottom: 0.9rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.live-col-title { font-weight: 700; color: #111; font-size: 0.88rem; }
.live-lbl-base  {
    font-size: 0.64rem; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #bbb;
}
.live-lbl-opt   {
    font-size: 0.64rem; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: #1AD598;
}


.live-meta {
    font-size: 0.78rem;
    color: #aaa;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid #f0efed;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    line-height: 1.5;
}
.live-meta strong { color: #555; }

/* ─ Force readable text inside assistant chat bubbles ─ */
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] em {
    color: #111 !important;
}

.speedup-callout {
    text-align: center;
    font-size: 1.15rem;
    font-weight: 500;
    color: #333;
    margin: 2rem 0 0.4rem 0;
    padding: 1.4rem 2rem;
    background: linear-gradient(135deg, #f4fef9 0%, #faf9ff 100%);
    border: 1px solid #d0f5e8;
    border-radius: 12px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.speedup-num {
    color: #1AD598;
    font-size: 2.8rem;
    font-weight: 900;
    line-height: 1;
    display: block;
    margin: 0.3rem 0;
    letter-spacing: -1px;
}
.sim-note {
    text-align: center;
    font-size: 0.72rem;
    color: #bbb;
    margin-top: 0.25rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
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
_GROUP_BG      = ["#faf9ff", "#f4fef9", "#faf9ff", "#f4fef9"]
_ACCENT_TAIL   = "#94a3b8"   # neutral for Accuracy / Cost groups
_BG_TAIL       = "#f8fafc"


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
                tps_str = f" · **{tps1:.1f} tok/s**" if tps1 else ""
                ph_m1.markdown(f'<p class="live-meta">TTFT <strong>{ttft1:.0f} ms</strong>{tps_str}</p>',
                               unsafe_allow_html=True)
            if ttft2:
                tps_str = f" · **{tps2:.1f} tok/s**" if tps2 else ""
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

    with col1:
        st.markdown(
            f'<div class="live-col-hdr">'
            f'<span class="live-col-title">Stock {framework}</span>'
            f'<span class="live-lbl-base">Baseline</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
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
        with st.chat_message("assistant"):
            ph_t2 = st.empty()
            ph_m2 = st.empty()

    ph_speedup = st.empty()

    # ── Run or restore ─────────────────────────────────────────────────────
    if run:
        result = _run_comparison(prompt, services, meta, ph_t1, ph_t2, ph_m1, ph_m2)
        st.session_state["_live_result"] = result
        _show_speedup(result, ph_speedup, ph_m1, ph_m2, data)

    elif st.session_state.get("_live_result"):
        r = st.session_state["_live_result"]
        ph_t1.markdown(r["text1"])
        ph_t2.markdown(r["text2"])
        _show_speedup(r, ph_speedup, ph_m1, ph_m2, data)


def _show_speedup(r: dict, ph_speedup, ph_m1, ph_m2, data: dict):
    ttft1, ttft2 = r.get("ttft1"), r.get("ttft2")
    tps1,  tps2  = r.get("tps1"),  r.get("tps2")
    sim          = r.get("simulated", True)

    if ttft1:
        s = f" · **{tps1:.1f} tok/s**" if tps1 else ""
        ph_m1.markdown(f'<p class="live-meta">TTFT <strong>{ttft1:.0f} ms</strong>{s}</p>',
                       unsafe_allow_html=True)
    if ttft2:
        s = f" · **{tps2:.1f} tok/s**" if tps2 else ""
        ph_m2.markdown(f'<p class="live-meta">TTFT <strong>{ttft2:.0f} ms</strong>{s}</p>',
                       unsafe_allow_html=True)
    if ttft1 and ttft2:
        ratio = ttft1 / max(ttft2, 0.001)
        note  = '<p class="sim-note">replaying recorded benchmark run</p>' if sim else ""
        ph_speedup.markdown(
            f'<div class="speedup-callout">'
            f'<span class="speedup-num">{ratio:.2f}×</span>'
            f'faster with Artemis on this prompt'
            f'</div>{note}',
            unsafe_allow_html=True,
        )
        render_performance_charts(data)
        render_accuracy(data)


# ── Token race component ──────────────────────────────────────────────────────

_RACE_HTML = """<!DOCTYPE html>
<html><head><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:transparent;padding:0 1px}
.card{background:white;border:1px solid #e2e0de;border-radius:10px;padding:1.1rem 1.4rem 0.9rem}
.top-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.1rem}
.race-lbl{font-size:0.63rem;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;color:#7C73FF}
.speed-wrap{display:flex;align-items:center;gap:4px}
.speed-hint{font-size:0.7rem;color:#bbb;margin-right:4px}
.sbtn{background:#f5f4f2;border:none;border-radius:5px;padding:2px 9px;font-size:0.75rem;font-weight:600;color:#888;cursor:pointer}
.sbtn.on{background:#eeecff;color:#7C73FF}
.cols{display:grid;grid-template-columns:1fr 1px 1fr;gap:0 1.4rem;margin-bottom:0.8rem}
.dvr{background:#f0efed}
.hdr{display:flex;justify-content:space-between;align-items:center;padding-bottom:0.55rem;border-bottom:1px solid #f0efed;margin-bottom:0.75rem}
.hdr-artemis{border-bottom:1px solid #d0f5e8!important}
.htitle{font-weight:700;font-size:0.87rem;color:#111}
.lbl-b{font-size:0.62rem;font-weight:700;letter-spacing:1.1px;text-transform:uppercase;color:#bbb}
.lbl-a{font-size:0.62rem;font-weight:700;letter-spacing:1.1px;text-transform:uppercase;color:#1AD598}
.ttft-line{font-size:0.71rem;height:1.05rem;margin-bottom:0.35rem;font-weight:600}
.wait{color:#ddd;font-weight:400;font-style:italic}
.hit-b{color:#7C73FF}.hit-a{color:#1AD598}
.cnt-row{display:flex;align-items:baseline;gap:0.35rem;margin-bottom:0.55rem}
.cnt{font-size:2.5rem;font-weight:800;color:#111;line-height:1;min-width:3ch;font-variant-numeric:tabular-nums}
.unit{font-size:0.74rem;color:#bbb;text-transform:uppercase;letter-spacing:0.5px;font-weight:500}
.bar-bg{background:#f0efed;border-radius:4px;height:6px;overflow:hidden;margin-bottom:0.6rem}
.bar{height:6px;border-radius:4px;width:0%}
.bar-b{background:#c8c4ff}.bar-a{background:#1AD598}
.meta{font-size:0.76rem;color:#bbb;display:flex;gap:1rem}
.mv{font-weight:700;color:#555}
.bottom{display:flex;align-items:center;justify-content:space-between;margin-top:0.65rem;padding-top:0.65rem;border-top:1px solid #f5f4f2}
.su{font-size:0.88rem;color:#333;font-weight:500;min-height:1.5rem}
.su-big{color:#1AD598;font-size:1.3rem;font-weight:800}
.playbtn{background:#040442;color:white;border:none;border-radius:7px;padding:0.42rem 1.2rem;font-size:0.875rem;font-weight:600;cursor:pointer;transition:background .15s;white-space:nowrap}
.playbtn:hover:not(:disabled){background:#0a0a6e}
.playbtn:disabled{background:#c8c4ff;cursor:default}
</style></head><body>
<div class="card">
  <div class="top-row">
    <span class="race-lbl">Token Race</span>
    <div class="speed-wrap">
      <span class="speed-hint">Speed</span>
      <button class="sbtn on" id="s1" onclick="setSpd(1)">1×</button>
      <button class="sbtn"    id="s2" onclick="setSpd(2)">2×</button>
      <button class="sbtn"    id="s4" onclick="setSpd(4)">4×</button>
    </div>
  </div>
  <div class="cols">
    <div>
      <div class="hdr">
        <span class="htitle">Stock __FW__</span>
        <span class="lbl-b">Baseline</span>
      </div>
      <div class="ttft-line" id="tb"><span class="wait">waiting for first token…</span></div>
      <div class="cnt-row"><span class="cnt" id="cb">0</span><span class="unit">tokens</span></div>
      <div class="bar-bg"><div class="bar bar-b" id="bb"></div></div>
      <div class="meta">
        <span>TTFT <span class="mv" id="tftb">—</span></span>
        <span><span class="mv" id="spb">—</span> tok/s</span>
      </div>
    </div>
    <div class="dvr"></div>
    <div>
      <div class="hdr hdr-artemis">
        <span class="htitle">__FW__ + Artemis</span>
        <span class="lbl-a">+ Artemis</span>
      </div>
      <div class="ttft-line" id="ta"><span class="wait">waiting for first token…</span></div>
      <div class="cnt-row"><span class="cnt" id="ca">0</span><span class="unit">tokens</span></div>
      <div class="bar-bg"><div class="bar bar-a" id="ba"></div></div>
      <div class="meta">
        <span>TTFT <span class="mv" id="tfta">—</span></span>
        <span><span class="mv" id="spa">—</span> tok/s</span>
      </div>
    </div>
  </div>
  <div class="bottom">
    <div class="su" id="su"></div>
    <button class="playbtn" id="pb" onclick="start()">&#9654; Play race</button>
  </div>
</div>
<script>
var BT=__BT__,BS=__BS__,AT=__AT__,AS=__AS__,TOT=__TOT__;
var spd=1,t0=null,raf=null,bdone=false,adone=false,blit=false,alit=false;
function setSpd(s){
  spd=s;
  ['s1','s2','s4'].forEach(function(id){document.getElementById(id).classList.remove('on')});
  document.getElementById('s'+s).classList.add('on');
}
function reset(){
  ['cb','ca'].forEach(function(id){document.getElementById(id).textContent='0'});
  ['bb','ba'].forEach(function(id){document.getElementById(id).style.width='0%'});
  document.getElementById('tb').innerHTML='<span class="wait">waiting for first token\u2026</span>';
  document.getElementById('ta').innerHTML='<span class="wait">waiting for first token\u2026</span>';
  ['tftb','tfta','spb','spa'].forEach(function(id){document.getElementById(id).textContent='\u2014'});
  document.getElementById('su').innerHTML='';
  bdone=false;adone=false;blit=false;alit=false;
}
function start(){
  if(raf)cancelAnimationFrame(raf);
  reset();t0=null;
  document.getElementById('pb').disabled=true;
  document.getElementById('pb').textContent='\u23f3 Racing\u2026';
  raf=requestAnimationFrame(tick);
}
function tick(ts){
  if(!t0)t0=ts;
  var e=(ts-t0)/1000*spd;
  // baseline
  var be=Math.max(0,e-BT/1000);
  var btok=Math.min(Math.floor(be*BS),TOT);
  document.getElementById('cb').textContent=btok;
  document.getElementById('bb').style.width=(btok/TOT*100)+'%';
  if(!blit&&e>=BT/1000){blit=true;document.getElementById('tb').innerHTML='<span class="hit-b">\u26a1 First token at '+BT+' ms</span>';document.getElementById('tftb').textContent=BT+' ms';}
  if(btok>0)document.getElementById('spb').textContent=BS.toFixed(1);
  if(btok>=TOT&&!bdone)bdone=true;
  // optimised
  var ae=Math.max(0,e-AT/1000);
  var atok=Math.min(Math.floor(ae*AS),TOT);
  document.getElementById('ca').textContent=atok;
  document.getElementById('ba').style.width=(atok/TOT*100)+'%';
  if(!alit&&e>=AT/1000){alit=true;document.getElementById('ta').innerHTML='<span class="hit-a">\u26a1 First token at '+AT+' ms</span>';document.getElementById('tfta').textContent=AT+' ms';}
  if(atok>0)document.getElementById('spa').textContent=AS.toFixed(1);
  if(atok>=TOT&&!adone){
    adone=true;
    var bTotal=BT/1000+TOT/BS, aTotal=AT/1000+TOT/AS;
    var ratio=(bTotal/aTotal).toFixed(2);
    document.getElementById('su').innerHTML='Optimised model ran <span class="su-big">'+ratio+'\u00d7</span> faster \u2014 __PL__';
  }
  if(!bdone||!adone){raf=requestAnimationFrame(tick);}
  else{document.getElementById('pb').disabled=false;document.getElementById('pb').textContent='\u21ba Play again';}
}
</script></body></html>"""


def render_token_race(data: dict):
    demo_prompts = data.get("demo_prompts", [])
    if not demo_prompts:
        return

    prompt_idx = st.session_state.get("live_prompt_sel", 0)
    if prompt_idx >= len(demo_prompts):
        prompt_idx = 0

    prompt    = demo_prompts[prompt_idx]
    recorded  = prompt.get("recorded", {})
    base_rec  = recorded.get("baseline", {})
    opt_rec   = recorded.get("optimized", {})
    framework = data.get("meta", {}).get("framework", "Model")
    prompt_label = prompt.get("label", "this prompt")

    base_ttft = float(base_rec.get("ttft_ms", 1000))
    base_tps  = float(base_rec.get("tps", 40))
    opt_ttft  = float(opt_rec.get("ttft_ms", 800))
    opt_tps   = float(opt_rec.get("tps", 60))
    # approx total tokens from word count of the recorded text
    total_tok = max(len(base_rec.get("text", "").split()), 1)

    html = (
        _RACE_HTML
        .replace("__FW__",  framework)
        .replace("__BT__",  str(base_ttft))
        .replace("__BS__",  str(base_tps))
        .replace("__AT__",  str(opt_ttft))
        .replace("__AS__",  str(opt_tps))
        .replace("__TOT__", str(total_tok))
        .replace("__PL__",  prompt_label)
    )

    st.markdown('<hr style="border:none;border-top:1px solid #eeecff;margin:1.5rem 0 1.25rem">', unsafe_allow_html=True)
    st.components.v1.html(html, height=310, scrolling=False)


# ── Section renderers ─────────────────────────────────────────────────────────

def render_config_section(configs: list, active_id: str):
    st.markdown('<p class="slabel">Configuration</p>', unsafe_allow_html=True)

    cur = next((c for c in configs if c["config_id"] == active_id), configs[0])

    # Cascade: Hardware → Framework → Model
    hw_opts = sorted(set(c["hardware"] for c in configs))
    col_hw, col_fw, col_m = st.columns(3)

    with col_hw:
        def_hw = cur["hardware"] if cur["hardware"] in hw_opts else hw_opts[0]
        sel_hw = st.selectbox("Hardware", hw_opts, index=hw_opts.index(def_hw))

    fw_opts = sorted(set(c["framework"] for c in configs if c["hardware"] == sel_hw))
    with col_fw:
        def_fw = cur["framework"] if (cur["hardware"] == sel_hw and cur["framework"] in fw_opts) else (fw_opts[0] if fw_opts else "")
        sel_fw = st.selectbox("Framework", fw_opts, index=fw_opts.index(def_fw) if def_fw in fw_opts else 0)

    m_opts = sorted(set(c["model"] for c in configs if c["hardware"] == sel_hw and c["framework"] == sel_fw))
    with col_m:
        def_m = cur["model"] if (cur["hardware"] == sel_hw and cur["framework"] == sel_fw and cur["model"] in m_opts) else (m_opts[0] if m_opts else "")
        sel_m = st.selectbox("Model", m_opts, index=m_opts.index(def_m) if def_m in m_opts else 0)

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

    html = (
        f'<div class="spec-bar">'
        f'<span class="lbl">Model</span>&nbsp;<span class="val">{meta.get("model","")}</span>'
        f'<span class="sep">·</span>'
        f'<span class="lbl">Hardware</span>&nbsp;<span class="val">{meta.get("hardware","")}</span>'
        f'&nbsp;{tier}'
        f'<span class="sep">·</span>'
    )
    if spec_str:
        html += f'<span class="specs-muted">{spec_str}</span><span class="sep">·</span>'
    html += (
        f'<span class="lbl">Framework</span>&nbsp;<span class="val">{meta.get("framework","")}</span>'
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
        f'<p style="font-size:0.82rem;color:#aaa;margin:0 0 1rem 0;'
        f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">{note}</p>',
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
    st.markdown('<p class="slabel">Cross-Hardware Results</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.82rem;color:#aaa;margin:0 0 1rem 0;'
        'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'
        'Same model on every hardware Artemis has tuned — proves the optimization is safe to merge.'
        '</p>',
        unsafe_allow_html=True,
    )

    entries = data.get("cross_hardware", [])
    max_delta = max((e.get("throughput_delta_pct", 0) for e in entries), default=60)

    tbody = ""
    for hw in entries:
        d_pct    = hw.get("throughput_delta_pct", 0)
        acc_d    = hw.get("accuracy_delta", 0)
        acc_str  = f"±{abs(acc_d):.2f} MMLU" if acc_d == 0 else (f"+{acc_d:.2f} MMLU" if acc_d > 0 else f"{acc_d:.2f} MMLU")
        pbar     = progress_bar_html(d_pct, max_delta)
        link     = f'<a class="view-link" href="?config={hw["config_id"]}">View →</a>' if hw.get("config_id") else ""
        tbody += (
            f'<tr>'
            f'<td class="hw-class">{hw.get("class","")}</td>'
            f'<td><span class="hw-name">{hw["hardware"]}</span>&nbsp;{tier_badge(hw.get("spec_tier",""))}</td>'
            f'<td style="color:#666">{hw.get("framework","")}</td>'
            f'<td>{pbar}</td>'
            f'<td style="color:#888;font-size:0.82rem">{acc_str}</td>'
            f'<td>{verdict_html(hw.get("verdict",""))}</td>'
            f'<td>{link}</td>'
            f'</tr>'
        )

    table_html = (
        '<div class="hw-wrap">'
        '<table class="hw-table">'
        '<thead><tr>'
        '<th>Class</th><th>Hardware</th><th>Framework</th>'
        '<th>Throughput Δ</th><th>Accuracy</th><th>Verdict</th><th></th>'
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
_COL_BASE = "#9D98FF"
_COL_OPT  = "#1AD598"

def _bar_chart(labels, base_vals, opt_vals, title, unit, lower_is_better=False):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Baseline",
        x=labels,
        y=base_vals,
        marker_color=_COL_BASE,
        text=[f"{v} {unit}" for v in base_vals],
        textposition="outside",
        textfont=dict(size=11, color="#555"),
    ))
    fig.add_trace(go.Bar(
        name="+ Artemis",
        x=labels,
        y=opt_vals,
        marker_color=_COL_OPT,
        text=[f"{v} {unit}" for v in opt_vals],
        textposition="outside",
        textfont=dict(size=11, color="#1AD598"),
    ))
    note = "lower is better" if lower_is_better else "higher is better"
    fig.update_layout(
        title=dict(text=f"{title} <sup style='color:#aaa;font-size:11px'>({note})</sup>",
                   font=dict(size=14, color="#111"), x=0),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"),
        yaxis=dict(showgrid=True, gridcolor="#f0efed", zeroline=False,
                   tickfont=dict(color="#aaa", size=11)),
        xaxis=dict(tickfont=dict(color="#555", size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=12, color="#333")),
        margin=dict(t=60, b=20, l=20, r=20),
        height=280,
    )
    return fig


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

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            _bar_chart(labels, tput_base, tput_opt, "Throughput", "tok/s", lower_is_better=False),
            use_container_width=True, config={"displayModeBar": False},
        )
    with col2:
        st.plotly_chart(
            _bar_chart(labels, ttft_base, ttft_opt, "Time to First Token", "ms", lower_is_better=True),
            use_container_width=True, config={"displayModeBar": False},
        )


def render_accuracy(data: dict):
    validations = data.get("correctness", {}).get("validations", [])
    if not validations:
        return

    all_pass = all(v.get("pass", False) for v in validations)
    n_pass   = sum(1 for v in validations if v.get("pass", False))
    n_total  = len(validations)

    banner_bg    = "#f4fef9" if all_pass else "#fff5f5"
    banner_border = "#d0f5e8" if all_pass else "#ffc8c8"
    banner_color  = "#0ea86e" if all_pass else "#e03c3c"
    banner_icon   = "✓" if all_pass else "✗"
    banner_text   = f"All {n_total} checks passed — outputs verified identical" if all_pass else f"{n_pass} / {n_total} checks passed"

    layer_icons = ["①", "②", "③", "④", "⑤", "⑥"]

    st.markdown('<hr class="section-sep">', unsafe_allow_html=True)
    st.markdown('<p class="slabel">Output Correctness</p>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:0.85rem;color:#888;margin:-0.5rem 0 1.2rem;'
        'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'
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

    # ── Layer cards ───────────────────────────────────────────────────────────
    cols = st.columns(len(validations))
    for i, (col, v) in enumerate(zip(cols, validations)):
        passed      = v.get("pass", False)
        card_border = "#d0f5e8" if passed else "#ffc8c8"
        icon_bg     = "#d0f5e8" if passed else "#ffc8c8"
        icon_color  = "#0ea86e" if passed else "#e03c3c"
        check       = "✓" if passed else "✗"
        layer_num   = layer_icons[i] if i < len(layer_icons) else str(i + 1)

        col.markdown(
            f'<div style="background:white;border:1px solid {card_border};border-radius:10px;'
            f'padding:1.1rem 1rem;height:100%;'
            f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif">'

            f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.7rem">'
            f'<span style="font-size:0.8rem;color:#ccc;font-weight:600">{layer_num}</span>'
            f'<div style="margin-left:auto;width:22px;height:22px;border-radius:50%;'
            f'background:{icon_bg};display:flex;align-items:center;justify-content:center;'
            f'font-size:0.75rem;font-weight:800;color:{icon_color}">{check}</div>'
            f'</div>'

            f'<div style="font-size:0.8rem;font-weight:700;color:#111;margin-bottom:0.3rem">'
            f'{v.get("name","")}</div>'

            f'<div style="font-size:0.72rem;color:#aaa;line-height:1.45;margin-bottom:0.6rem">'
            f'{v.get("description","")}</div>'

            f'<div style="font-size:0.72rem;color:#555;background:#f9f9f9;'
            f'border-radius:5px;padding:0.4rem 0.55rem;line-height:1.4">'
            f'{v.get("note","")}</div>'

            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Model accuracy (MMLU / HellaSwag) ─────────────────────────────────────


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    url_config = st.query_params.get("config", "")
    configs    = list_configs()

    if not configs:
        st.error("No JSON configs found in `data/`. Create one to get started.")
        st.stop()

    valid_ids = {c["config_id"] for c in configs}
    active_id = url_config if url_config in valid_ids else configs[0]["config_id"]

    # ── Section 1: Configuration ──────────────────────────────────────────
    selected_id = render_config_section(configs, active_id)

    if not selected_id:
        st.warning("No matching configuration found.")
        st.stop()

    # Sync URL param
    if selected_id != url_config:
        st.query_params["config"] = selected_id

    data = load_config(selected_id)
    if not data:
        st.error(f"Could not load config: `{selected_id}`")
        st.stop()

    # Spec summary bar
    render_spec_bar(data)

    # ── Sections ─────────────────────────────────────────────────────────
    render_live_section(data)
    render_cross_hardware(data)


main()
