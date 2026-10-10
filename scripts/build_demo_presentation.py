from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "deliverables" / "AIOps_Guardian_Pro_Demo_Oct_10_2026.pptx"

W = 13.333
H = 7.5
FONT = "Aptos"
BG = "111820"
PANEL = "1C2832"
PANEL_ALT = "24323D"
WHITE = "F3F5F2"
MUTED = "AEBBC4"
FAINT = "71808B"
TEAL = "42D6C2"
BLUE = "72ABFF"
AMBER = "F4BD59"
RED = "FF776E"
GREEN = "A4D77A"
PURPLE = "C09BE8"


def color(value):
    return RGBColor.from_string(value)


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    item = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    item.fill.solid()
    item.fill.fore_color.rgb = color(fill)
    item.line.color.rgb = color(line or fill)
    item.line.width = Pt(1)
    return item


def text(slide, value, x, y, w, h, size=16, fg=WHITE, bold=False,
         align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, font=FONT):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.04)
    frame.margin_right = Inches(0.04)
    frame.margin_top = Inches(0.02)
    frame.margin_bottom = Inches(0.02)
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    paragraph.space_before = Pt(0)
    paragraph.space_after = Pt(0)
    paragraph.line_spacing = 1.05
    run = paragraph.add_run()
    run.text = value
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color(fg)
    return box


def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color(BG)
    return slide


def header(slide, section, title, subtitle, number):
    text(slide, section.upper(), 0.62, 0.30, 7.0, 0.26, 10, TEAL, True)
    text(slide, title, 0.62, 0.64, 12.1, 0.52, 28, WHITE, True)
    text(slide, subtitle, 0.64, 1.18, 12.0, 0.32, 13, MUTED)
    rect(slide, 0.64, 1.62, 12.05, 0.015, "384650")
    rect(slide, 0.64, 7.08, 12.05, 0.015, "384650")
    text(slide, "AIOPS GUARDIAN PRO  |  MAYA'S INCIDENT STORY", 0.64, 7.12, 8.0, 0.20, 8, FAINT)
    text(slide, f"{number:02d}", 12.1, 7.10, 0.55, 0.22, 9, MUTED, True, PP_ALIGN.RIGHT)


def card(slide, x, y, w, h, title, body, accent=TEAL, title_size=16, body_size=12):
    rect(slide, x, y, w, h, PANEL, "34434F")
    rect(slide, x, y, 0.055, h, accent)
    text(slide, title, x + 0.20, y + 0.16, w - 0.36, 0.34, title_size, WHITE, True)
    text(slide, body, x + 0.20, y + 0.56, w - 0.36, h - 0.68, body_size, MUTED,
         valign=MSO_ANCHOR.TOP)


def metric_card(slide, x, label, value, detail, accent, fill_ratio):
    y, w, h = 2.25, 2.92, 3.25
    rect(slide, x, y, w, h, PANEL, "34434F")
    text(slide, label.upper(), x + 0.22, y + 0.20, w - 0.42, 0.30, 10, MUTED, True)
    text(slide, value, x + 0.22, y + 0.66, w - 0.42, 0.75, 32, accent, True)
    text(slide, detail, x + 0.22, y + 1.48, w - 0.42, 0.62, 12, WHITE)
    rect(slide, x + 0.22, y + 2.49, w - 0.44, 0.16, "34434F")
    rect(slide, x + 0.22, y + 2.49, (w - 0.44) * fill_ratio, 0.16, accent)


def add_cover(prs):
    slide = new_slide(prs)
    rect(slide, 0, 0, 0.18, H, TEAL)
    text(slide, "AIOPS GUARDIAN PRO  /  AN INCIDENT STORY", 0.84, 0.78, 7.6, 0.32, 11, TEAL, True)
    text(slide, "02:07 AM.\nCheckout is failing.", 0.80, 1.48, 7.5, 1.65, 37, WHITE, True)
    text(slide, "Maya is on call. Guardian helps her investigate -\nwithout taking control of production.",
         0.84, 3.48, 7.2, 0.82, 19, MUTED)

    rect(slide, 9.10, 1.48, 3.35, 2.60, PANEL, "34434F")
    rect(slide, 9.10, 1.48, 3.35, 0.10, RED)
    text(slide, "PAGER ALERT", 9.40, 1.84, 2.7, 0.26, 10, MUTED, True)
    text(slide, "checkout-api", 9.40, 2.30, 2.7, 0.42, 19, WHITE, True)
    text(slide, "5xx rate rising", 9.40, 2.88, 2.7, 0.34, 16, RED, True)
    text(slide, "production  /  customer impact", 9.40, 3.44, 2.7, 0.28, 10, MUTED)

    rect(slide, 0.84, 5.18, 11.61, 0.02, "384650")
    text(slide, "A simple story about evidence, uncertainty, and a human decision.",
         0.84, 5.62, 10.8, 0.44, 17, AMBER, True)
    text(slide, "LIVE DEMO  /  10 OCTOBER 2026", 0.84, 6.68, 6.3, 0.26, 10, FAINT, True)


def add_problem_solution(prs):
    slide = new_slide(prs)
    header(slide, "THE PROBLEM  /  THE PROMISE", "Maya has signals everywhere - but no joined-up answer.",
           "AIOps Guardian Pro helps the on-call engineer move from scattered evidence to a safer decision.", 1)

    text(slide, "THE PROBLEM", 0.86, 2.05, 2.1, 0.28, 10, RED, True)
    text(slide, "Incident diagnosis is slow because the evidence is scattered.",
         0.86, 2.42, 5.05, 0.86, 22, WHITE, True, valign=MSO_ANCHOR.TOP)
    sources = [
        (0.86, "Metrics", "5xx / latency", TEAL),
        (3.22, "Changes", "deploys / config", BLUE),
        (0.86, "Runtime", "pods / events", AMBER),
        (3.22, "History", "cases / runbooks", PURPLE),
    ]
    for i, (x, title, detail, accent) in enumerate(sources):
        y = 3.66 + (i // 2) * 0.88
        x = x + (1.18 if i % 2 else 0)
        rect(slide, x, y, 2.07, 0.66, PANEL, "34434F")
        rect(slide, x, y, 0.055, 0.66, accent)
        text(slide, title, x + 0.17, y + 0.07, 1.72, 0.24, 12, WHITE, True)
        text(slide, detail, x + 0.17, y + 0.35, 1.72, 0.20, 9, MUTED)

    rect(slide, 6.40, 2.10, 0.02, 3.62, "384650")
    text(slide, "THE SOLUTION", 7.02, 2.05, 2.4, 0.28, 10, TEAL, True)
    text(slide, "One investigation.\nA human-owned decision.",
         7.02, 2.42, 5.0, 0.88, 22, WHITE, True, valign=MSO_ANCHOR.TOP)
    for i, (title, detail, accent) in enumerate([
        ("Correlate", "Scoped metrics, runtime, changes, and history", TEAL),
        ("Explain", "Evidence, uncertainty, and the next useful check", BLUE),
        ("Constrain", "Deterministic guardrails; approval for risky actions", AMBER),
    ]):
        y = 3.63 + i * 0.72
        rect(slide, 7.02, y + 0.07, 0.18, 0.18, accent, shape=MSO_SHAPE.OVAL)
        text(slide, title, 7.38, y, 1.25, 0.30, 13, accent, True)
        text(slide, detail, 8.56, y, 3.72, 0.40, 11, MUTED)


def add_architecture(prs):
    slide = new_slide(prs)
    header(slide, "THE ARCHITECTURE", "One orchestrator connects agents to governed tools.",
           "The model helps interpret evidence; deterministic code controls operational authority.", 2)

    nodes = [
        (0.78, 2.16, 1.68, "ON-CALL SRE", "React UI", BLUE),
        (2.98, 2.16, 1.92, "APP API", "FastAPI", BLUE),
        (5.42, 2.16, 2.08, "ORCHESTRATE", "LangGraph", PURPLE),
        (8.02, 2.16, 2.06, "INVESTIGATE", "Specialist agents", TEAL),
        (10.62, 2.16, 1.95, "CONNECT", "MCP tool plane", AMBER),
    ]
    for x, y, w, label, title, accent in nodes:
        rect(slide, x, y, w, 0.95, PANEL, "3A4A56")
        rect(slide, x, y, w, 0.07, accent)
        text(slide, label, x + 0.14, y + 0.19, w - 0.28, 0.20, 8, accent, True)
        text(slide, title, x + 0.14, y + 0.48, w - 0.28, 0.28, 13, WHITE, True)
    for x in (2.55, 4.98, 7.58, 10.18):
        text(slide, ">", x, 2.42, 0.30, 0.34, 19, FAINT, True, PP_ALIGN.CENTER)

    text(slide, "REASONING + MEMORY", 0.82, 3.48, 2.35, 0.23, 9, MUTED, True)
    support = [
        (3.00, "Local LLM", "Qwen via Ollama", PURPLE),
        (5.84, "Operational memory", "PostgreSQL + FAISS", BLUE),
        (8.68, "Observability", "Prometheus + Loki", TEAL),
        (11.05, "Runtime + delivery", "Kubernetes / CI", AMBER),
    ]
    for x, title, detail, accent in support:
        rect(slide, x, 3.82, 2.17, 0.88, PANEL_ALT, "34434F")
        text(slide, title, x + 0.14, 3.96, 1.90, 0.26, 11, accent, True)
        text(slide, detail, x + 0.14, 4.29, 1.90, 0.23, 9, MUTED)
    text(slide, "|", 6.76, 3.48, 0.24, 0.24, 12, FAINT)

    rect(slide, 0.82, 5.18, 11.45, 0.93, "302C24", "725D36")
    text(slide, "SAFETY BOUNDARY", 1.06, 5.42, 1.74, 0.22, 9, AMBER, True)
    text(slide, "Recommendation  ->  Python guardrails  ->  ALLOW / REQUIRE APPROVAL / BLOCK",
         2.96, 5.35, 8.90, 0.36, 12, WHITE, True)
    text(slide, "OpenTelemetry + Langfuse provide traces and audit context across the flow.",
         0.86, 6.43, 10.5, 0.28, 10, MUTED)


def add_workflow(prs):
    slide = new_slide(prs)
    header(slide, "THE INVESTIGATION FLOW", "From alert to verified, human-owned decision.",
           "A bounded workflow: gather evidence first; only then decide what action is safe.", 3)

    stages = [
        (0.78, "1", "ALERT", "Incident\narrives", RED),
        (3.20, "2", "PLAN", "Choose scoped\nchecks", BLUE),
        (5.62, "3", "CORRELATE", "Metrics + tools\n+ history", TEAL),
        (8.04, "4", "VALIDATE", "Cause supported?\nEvidence sufficient?", PURPLE),
        (10.46, "5", "GOVERN", "Policy routes\nthe action", AMBER),
    ]
    for i, (x, num, title, body, accent) in enumerate(stages):
        rect(slide, x, 2.24, 2.02, 1.52, PANEL, "3A4A56")
        rect(slide, x + 0.16, 2.43, 0.36, 0.36, accent, shape=MSO_SHAPE.OVAL)
        text(slide, num, x + 0.16, 2.44, 0.36, 0.32, 11, BG, True, PP_ALIGN.CENTER)
        text(slide, title, x + 0.62, 2.46, 1.22, 0.25, 10, accent, True)
        text(slide, body, x + 0.16, 2.98, 1.70, 0.60, 13, WHITE, True, valign=MSO_ANCHOR.TOP)
        if i < len(stages) - 1:
            text(slide, ">", x + 2.08, 2.78, 0.30, 0.40, 20, FAINT, True, PP_ALIGN.CENTER)

    text(slide, "IF EVIDENCE IS THIN", 0.88, 4.32, 2.75, 0.24, 9, MUTED, True)
    rect(slide, 0.88, 4.72, 4.78, 1.08, "1C302F", "2D736C")
    text(slide, "READ-ONLY", 1.14, 4.92, 1.25, 0.25, 10, TEAL, True)
    text(slide, "Ask for the next check; do not invent a cause.", 2.48, 4.88, 2.88, 0.46, 12, WHITE, True)

    text(slide, "IF A CHANGE IS RISKY", 6.08, 4.32, 2.75, 0.24, 9, MUTED, True)
    rect(slide, 6.08, 4.72, 5.55, 1.08, "352C1A", "8F6A2F")
    text(slide, "HUMAN APPROVAL", 6.34, 4.92, 1.78, 0.25, 10, AMBER, True)
    text(slide, "Approve or reject; then verify and audit.", 8.20, 4.88, 3.12, 0.46, 12, WHITE, True)
    text(slide, "Maya remains the incident commander. Guardian shortens the search, not the chain of accountability.",
         0.90, 6.28, 11.20, 0.38, 13, AMBER, True)


def add_problem(prs):
    slide = new_slide(prs)
    header(slide, "01  /  WHY", "Incidents arrive as fragments, not answers",
           "The on-call engineer still has to connect signals, changes, runbooks, and past outcomes.", 2)
    text(slide, "EVIDENCE IS SPREAD ACROSS TOOLS", 0.72, 1.95, 5.0, 0.28, 10, MUTED, True)
    items = [
        (0.72, 2.38, "METRICS", "5xx, latency, burn", TEAL),
        (3.24, 2.38, "CHANGES", "Deploys, config, releases", BLUE),
        (0.72, 3.82, "RUNTIME", "Pods, events, logs", AMBER),
        (3.24, 3.82, "HISTORY", "Incidents, runbooks", PURPLE),
    ]
    for x, y, title, body, accent in items:
        card(slide, x, y, 2.26, 1.15, title, body, accent, 13, 11)
    text(slide, "+", 3.02, 2.76, 0.18, 0.28, 18, FAINT, True, PP_ALIGN.CENTER)
    text(slide, "+", 3.02, 4.20, 0.18, 0.28, 18, FAINT, True, PP_ALIGN.CENTER)

    rect(slide, 6.18, 2.05, 6.15, 3.75, PANEL_ALT, "3A4A56")
    text(slide, "THE DESIGN PROMISE", 6.48, 2.34, 4.5, 0.28, 10, TEAL, True)
    rows = [
        ("01", "Facts before claims", "Every conclusion points back to collected evidence.", TEAL),
        ("02", "Uncertainty is explicit", "Thin evidence means ask for the next check.", BLUE),
        ("03", "Policy before action", "Production changes require deterministic gates.", AMBER),
    ]
    for i, (number, title, body, accent) in enumerate(rows):
        y = 2.83 + i * 0.88
        text(slide, number, 6.48, y, 0.42, 0.34, 12, accent, True)
        text(slide, title, 7.00, y, 4.75, 0.30, 16, WHITE, True)
        text(slide, body, 7.00, y + 0.34, 4.8, 0.32, 11, MUTED)
    text(slide, "Goal: shorten time-to-decision, not remove the incident commander.",
         0.75, 5.98, 11.4, 0.44, 17, WHITE, True)


def add_flow(prs):
    slide = new_slide(prs)
    header(slide, "02  /  HOW IT WORKS", "A bounded path from signal to decision",
           "The LLM helps interpret evidence; code and people govern operational authority.", 3)
    steps = [
        ("01", "SIGNALS", "Prometheus\nKubernetes\nLogs + deploys", TEAL),
        ("02", "PLAN", "LangGraph\nScoped intent\nDynamic agent plan", BLUE),
        ("03", "INVESTIGATE", "Specialist agents\nEvidence + history\nRunbook retrieval", PURPLE),
        ("04", "VALIDATE", "Evidence sufficiency\nConfidence + checks\nAsk for more data", AMBER),
        ("05", "GOVERN", "Python policy\nALLOW / APPROVAL / BLOCK\nAudit trail", RED),
    ]
    xs = [0.62, 3.13, 5.64, 8.15, 10.66]
    for i, (num, title, body, accent) in enumerate(steps):
        rect(slide, xs[i], 2.22, 2.05, 2.40, PANEL, "384650")
        rect(slide, xs[i], 2.22, 2.05, 0.07, accent)
        text(slide, num, xs[i] + 0.18, 2.46, 0.50, 0.28, 11, accent, True)
        text(slide, title, xs[i] + 0.18, 2.86, 1.72, 0.32, 14, WHITE, True)
        text(slide, body, xs[i] + 0.18, 3.31, 1.72, 1.02, 11, MUTED, valign=MSO_ANCHOR.TOP)
        if i < len(steps) - 1:
            text(slide, ">", xs[i] + 2.13, 3.14, 0.32, 0.42, 20, FAINT, True, PP_ALIGN.CENTER)
    rect(slide, 1.05, 5.14, 11.22, 0.95, "1C302F", "2D736C")
    text(slide, "HUMAN GATE", 1.34, 5.36, 1.65, 0.25, 10, TEAL, True)
    text(slide, "Approve if required  ->  execute through governed tools  ->  verify  ->  audit",
         3.00, 5.30, 8.75, 0.42, 14, WHITE, True)
    text(slide, "The model has no direct production-mutation tool.", 1.36, 6.27, 9.5, 0.28, 11, MUTED)


def add_forced_incident(prs):
    slide = new_slide(prs)
    header(slide, "MAYA'S STORY  /  THE SIGNAL", "The alert is loud. The evidence is mixed.",
           "Recorded forced run: 40 failed orders. The cause is not in the metrics alone.", 5)
    metrics = [
        (0.82, "100%", "HTTP 5xx", "40 injected failures", RED),
        (4.72, "500x", "Error-budget burn", "Far above the 1x baseline", AMBER),
        (8.62, "487 ms", "p95 latency", "Below the 500 ms threshold", BLUE),
    ]
    for x, value, label, detail, accent in metrics:
        rect(slide, x, 2.30, 3.52, 2.20, PANEL, "34434F")
        rect(slide, x, 2.30, 3.52, 0.08, accent)
        text(slide, value, x + 0.24, 2.70, 3.02, 0.64, 31, accent, True)
        text(slide, label, x + 0.24, 3.46, 3.02, 0.30, 14, WHITE, True)
        text(slide, detail, x + 0.24, 3.88, 3.02, 0.38, 11, MUTED)
    rect(slide, 0.82, 5.18, 11.32, 0.86, "352C1A", "8F6A2F")
    text(slide, "MISSING", 1.10, 5.48, 1.02, 0.24, 10, AMBER, True)
    text(slide, "No deployment, logs, or traces were collected for this live investigation.",
         2.20, 5.40, 9.50, 0.40, 14, WHITE, True)
    text(slide, "Recorded measurements: 2026-10-03", 0.84, 6.42, 5.4, 0.24, 9, FAINT)


def add_live_decision(prs):
    slide = new_slide(prs)
    header(slide, "MAYA'S STORY  /  THE RESPONSE", "Guardian refuses to guess.",
         "It tells Maya what is known, what is missing, and what to check next.", 6)
    rect(slide, 0.82, 2.12, 4.08, 3.78, "30242B", "7B4542")
    text(slide, "LIVE INVESTIGATION", 1.14, 2.48, 3.35, 0.26, 10, MUTED, True)
    text(slide, "NEEDS REVIEW", 1.12, 2.98, 3.40, 0.58, 25, RED, True)
    text(slide, "Root cause: unconfirmed", 1.14, 3.82, 3.35, 0.36, 16, WHITE, True)
    text(slide, "Confidence  0.0", 1.14, 4.42, 3.35, 0.32, 14, MUTED)
    text(slide, "Next action  collect_evidence", 1.14, 4.91, 3.35, 0.40, 14, TEAL, True)

    text(slide, "MAYA'S NEXT STEP", 5.62, 2.45, 4.6, 0.28, 10, BLUE, True)
    text(slide, "Check the deployment.\nCorrelate logs and traces.\nThen decide.",
        5.62, 2.98, 6.20, 1.64, 24, WHITE, True, valign=MSO_ANCHOR.TOP)
    rect(slide, 5.62, 5.18, 6.13, 0.72, PANEL_ALT, "3A4A56")
    text(slide, "For now: read-only. No production change.", 5.90, 5.39, 5.50, 0.30, 13, AMBER, True)


def add_synthetic_scenario(prs):
    slide = new_slide(prs)
    header(slide, "MAYA'S STORY  /  A REPLAY, NOT LIVE EVIDENCE", "A past incident offers a lead - not proof.",
           "Maya switches to a controlled replay to show how retrieval helps.", 7)
    rect(slide, 0.82, 2.05, 11.32, 0.72, "352C1A", "8F6A2F")
    text(slide, "SIMULATED SCENARIO", 1.10, 2.29, 2.10, 0.24, 10, AMBER, True)
    text(slide, "Not the cause of the live incident", 3.30, 2.24, 6.80, 0.34, 13, WHITE, True)
    timeline = [
        ("CHANGE", "1Gi -> 128Mi\nmemory limit", BLUE),
        ("SYMPTOM", "Pods restart\nOOMKilled", RED),
        ("PAST CASE", "SYN-K8S-001\nmatched", PURPLE),
    ]
    xs = [1.00, 5.04, 9.08]
    for i, (title, body, accent) in enumerate(timeline):
        rect(slide, xs[i], 3.25, 3.15, 1.62, PANEL, "384650")
        text(slide, title, xs[i] + 0.24, 3.51, 2.66, 0.26, 10, accent, True)
        text(slide, body, xs[i] + 0.24, 3.92, 2.66, 0.70, 16, WHITE, True)
        if i < len(timeline) - 1:
            text(slide, ">", xs[i] + 3.35, 3.88, 0.38, 0.38, 20, FAINT, True, PP_ALIGN.CENTER)
    text(slide, "The runbook suggests restoring a validated memory limit.",
         1.02, 5.42, 10.60, 0.42, 17, TEAL, True)


def add_safety(prs):
    slide = new_slide(prs)
    header(slide, "MAYA'S STORY  /  THE DECISION", "The rollback waits for Maya.",
           "Guardian can recommend; deterministic policy decides what is allowed.", 8)
    actions = [
        (0.92, "GUARDIAN", "Recommend\nrollback", BLUE),
        (5.00, "POLICY", "Require\nhuman approval", AMBER),
        (9.08, "MAYA", "Review, then\napprove or reject", TEAL),
    ]
    for i, (x, title, body, accent) in enumerate(actions):
        rect(slide, x, 2.62, 3.16, 1.86, PANEL, "384650")
        rect(slide, x, 2.62, 3.16, 0.08, accent)
        text(slide, title, x + 0.24, 2.96, 2.66, 0.26, 10, accent, True)
        text(slide, body, x + 0.24, 3.42, 2.66, 0.76, 17, WHITE, True)
        if i < len(actions) - 1:
            text(slide, ">", x + 3.42, 3.37, 0.38, 0.40, 21, FAINT, True, PP_ALIGN.CENTER)
    rect(slide, 0.92, 5.15, 11.32, 0.88, "1C302F", "2D736C")
    text(slide, "RECORDED RESULT", 1.20, 5.45, 1.62, 0.22, 9, TEAL, True)
    text(slide, "Approval was created. The action was NOT executed.",
         2.98, 5.38, 8.70, 0.34, 14, WHITE, True)
    text(slide, "Maya leaves with evidence, a next check, and authority still in human hands.",
         0.94, 6.35, 11.0, 0.36, 16, AMBER, True)


def add_engineering_results(prs):
    slide = new_slide(prs)
    header(slide, "07  /  ENGINEERING RESULTS", "Fix measurable failure modes at their source",
           "Evidence from the evaluation report dated 2026-10-03; re-run checks for the latest build.", 8)
    rows = [
        ("RETRIEVAL", "Wrong precedent ranked first", "Excluded prior retrieval results from follow-up queries.",
         "Top-1: SYN-K8S-002 (wrong) -> SYN-K8S-001 (correct)", TEAL),
        ("EVALUATION", "Scores were constants", "Replaced placeholders with six state-derived deterministic checks.",
         "Weak investigation can now fail with an explicit reason.", BLUE),
        ("TESTING", "Regression protection", "Labelled retrieval cases plus end-to-end agent scenario.",
         "104 backend tests passing in the recorded report.", AMBER),
    ]
    for i, (label, before, fix, result, accent) in enumerate(rows):
        y = 2.04 + i * 1.30
        rect(slide, 0.76, y, 11.50, 1.08, PANEL, "34434F")
        text(slide, label, 0.98, y + 0.15, 1.22, 0.25, 9, accent, True)
        text(slide, before, 2.25, y + 0.12, 2.40, 0.30, 12, WHITE, True)
        text(slide, fix, 4.82, y + 0.11, 3.45, 0.60, 11, MUTED)
        text(slide, result, 8.44, y + 0.11, 3.50, 0.62, 11, accent, True)
    text(slide, "The key change: failures are visible, reproducible, and covered by checks.",
         0.82, 6.16, 11.25, 0.38, 14, WHITE, True)


def add_prompt_eval(prs):
    slide = new_slide(prs)
    header(slide, "08  /  PROMPT EVALUATION", "Compare prompts on the same five cases",
           "Qwen 2.5 1.5B, temperature 0; deterministic checks. Scores are regression signals, not guarantees.", 9)
    variants = [
        (0.82, "P1  MINIMAL", "3 / 5", "Baseline\nShort answers\nMisses action + demo-label checks", BLUE),
        (4.53, "P2  STRUCTURED", "2 / 5", "Worsened\nFormat alone encouraged agreement\nwith a leading question", AMBER),
        (8.24, "P3  PRODUCTION", "4 / 5", "Best measured\nGrounding rules improved refusal\nand simulated-data labeling", TEAL),
    ]
    for x, title, score, detail, accent in variants:
        rect(slide, x, 2.20, 3.28, 2.55, PANEL, "384650")
        text(slide, title, x + 0.20, 2.45, 2.86, 0.28, 10, accent, True)
        text(slide, score, x + 0.20, 2.90, 2.86, 0.66, 28, WHITE, True)
        text(slide, detail, x + 0.20, 3.68, 2.86, 0.83, 11, MUTED, valign=MSO_ANCHOR.TOP)
    rect(slide, 0.82, 5.15, 10.70, 0.90, "352C1A", "8F6A2F")
    text(slide, "LIMIT", 1.08, 5.43, 0.80, 0.24, 10, AMBER, True)
    text(slide, "P3 still accepted the healthy-service leading question. Regex checks can over-credit wording.",
         2.04, 5.34, 8.95, 0.39, 12, WHITE, True)
    text(slide, "Safety comes from code-enforced policy and tool boundaries, not prompt compliance.",
         0.84, 6.24, 11.2, 0.30, 12, MUTED)


def add_run_of_show(prs):
    slide = new_slide(prs)
    header(slide, "09  /  LIVE WALKTHROUGH", "A five-minute demo with a clean mode switch",
           "Keep Live Prometheus evidence and the scripted OOM scenario clearly separated.", 10)
    rows = [
        ("00:00", "Baseline", "Open the sample store; place one normal mock order."),
        ("00:30", "Force fault", "Send the synthetic 503 burst; wait one scrape window."),
        ("01:15", "Investigate live", "Ask why checkout-api is failing; inspect PromQL + measured signals."),
        ("02:15", "Show uncertainty", "Point out unconfirmed RCA, confidence 0, and collect_evidence."),
        ("03:00", "Switch to Demo mode", "Run the OOM scenario; show SYN-K8S-001 and the runbook."),
        ("04:15", "Show the gate", "Rollback requires human approval; action has not executed."),
    ]
    for i, (when, title, body) in enumerate(rows):
        y = 1.98 + i * 0.63
        accent = TEAL if i < 4 else AMBER
        text(slide, when, 0.84, y, 0.82, 0.27, 11, accent, True)
        text(slide, title, 1.82, y - 0.01, 2.12, 0.30, 12, WHITE, True)
        text(slide, body, 4.10, y - 0.01, 7.65, 0.34, 11, MUTED)
        if i < len(rows) - 1:
            rect(slide, 0.84, y + 0.42, 10.94, 0.01, "34434F")
    rect(slide, 0.82, 5.99, 11.06, 0.62, PANEL_ALT, "384650")
    text(slide, "LOCAL", 1.02, 6.17, 0.70, 0.20, 9, TEAL, True)
    text(slide, "UI :30081  |  Store :18081  |  Grafana :3002  |  Prometheus :19090  |  Langfuse :3000",
         1.90, 6.12, 9.60, 0.30, 10, WHITE, True)
    text(slide, "Close: faster investigation, with production authority still governed by people and policy.",
         0.84, 6.69, 11.0, 0.28, 11, AMBER, True)


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    prs.core_properties.title = "AIOps Guardian Pro - Incident Story"
    prs.core_properties.subject = "A simple story of evidence-first incident response"
    prs.core_properties.author = "AIOps Guardian Pro"
    prs.core_properties.keywords = "AIOps, incident response, Prometheus, guardrails, demo"

    add_cover(prs)
    add_problem_solution(prs)
    add_architecture(prs)
    add_workflow(prs)
    add_forced_incident(prs)
    add_live_decision(prs)
    add_synthetic_scenario(prs)
    add_safety(prs)

    prs.save(OUTPUT)
    print(f"Created {OUTPUT}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    build()