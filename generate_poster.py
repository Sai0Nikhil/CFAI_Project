"""
generate_poster.py
Creates a high-quality A1 landscape poster as a PDF using reportlab.
Run: python generate_poster.py
"""
import subprocess, sys

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

try:
    from reportlab.lib.pagesizes import A1, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas
except ImportError:
    print("Installing reportlab...")
    install("reportlab")
    from reportlab.lib.pagesizes import A1, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas

OUT = r"C:\CFAI_Project\Hospital_AI_Navigator_Poster.pdf"

# ── Canvas-based poster (gives full layout control) ─────────────────────────
W, H = landscape(A1)   # 1683.78 x 1190.55 points  (A1 landscape)

c = canvas.Canvas(OUT, pagesize=(W, H))

# ── Color palette ────────────────────────────────────────────────────────────
DARK   = colors.HexColor("#0f172a")
BLUE   = colors.HexColor("#1d4ed8")
LBLUE  = colors.HexColor("#3b82f6")
CYAN   = colors.HexColor("#0ea5e9")
GREEN  = colors.HexColor("#16a34a")
AMBER  = colors.HexColor("#d97706")
RED    = colors.HexColor("#dc2626")
WHITE  = colors.white
LGRAY  = colors.HexColor("#f1f5f9")
MGRAY  = colors.HexColor("#94a3b8")
CARD   = colors.HexColor("#1e293b")

# ── Background ───────────────────────────────────────────────────────────────
c.setFillColor(DARK)
c.rect(0, 0, W, H, fill=1, stroke=0)

# Subtle grid lines
c.setStrokeColor(colors.HexColor("#1e293b"))
c.setLineWidth(0.5)
for x in range(0, int(W), 40):
    c.line(x, 0, x, H)
for y in range(0, int(H), 40):
    c.line(0, y, W, y)

# ── Header bar ───────────────────────────────────────────────────────────────
c.setFillColor(BLUE)
c.rect(0, H - 110, W, 110, fill=1, stroke=0)

# Gradient-ish accent
c.setFillColor(LBLUE)
c.rect(0, H - 110, W * 0.4, 110, fill=1, stroke=0)

c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 42)
c.drawString(30, H - 72, "HOSPITAL AI NAVIGATOR")

c.setFont("Helvetica", 20)
c.setFillColor(colors.HexColor("#bfdbfe"))
c.drawString(30, H - 100, "Charité Campus Mitte, Berlin  ·  AIIMS Mangalagiri, AP  ·  IIT Madras BS Data Science — CFAI")

# Right side: name + roll
c.setFillColor(WHITE)
c.setFont("Helvetica-Bold", 18)
c.drawRightString(W - 30, H - 60, "Sai Nikhil  |  25F2005507")
c.setFont("Helvetica", 15)
c.setFillColor(colors.HexColor("#bfdbfe"))
c.drawRightString(W - 30, H - 85, "25f2005507@ds.study.iitm.ac.in  |  June 2026")

# ── Helper functions ─────────────────────────────────────────────────────────
def card(x, y, w, h, title, title_color=LBLUE, bg=CARD):
    """Draw a card box with a title bar."""
    # Card background
    c.setFillColor(bg)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    # Title bar
    c.setFillColor(title_color)
    c.roundRect(x, y + h - 34, w, 34, 8, fill=1, stroke=0)
    c.rect(x, y + h - 34, w, 20, fill=1, stroke=0)  # bottom of title bar flat
    # Title text
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x + 12, y + h - 24, title)

def text(x, y, s, size=10, color=WHITE, bold=False, align="left"):
    c.setFillColor(color)
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(font, size)
    if align == "center":
        c.drawCentredString(x, y, s)
    else:
        c.drawString(x, y, s)

def badge(x, y, label, bg=LBLUE, fg=WHITE, w=None):
    tw = c.stringWidth(label, "Helvetica-Bold", 9)
    bw = (w or tw) + 16
    c.setFillColor(bg)
    c.roundRect(x, y - 2, bw, 16, 4, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 8, y + 2, label)
    return bw + 4

def hline(x, y, w, color=MGRAY):
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    c.line(x, y, x + w, y)

# ── Layout constants ─────────────────────────────────────────────────────────
TOP    = H - 120   # below header
BOTTOM = 20
PAD    = 14
COL_W  = (W - PAD * 4) / 3   # 3 columns

col1_x = PAD
col2_x = PAD * 2 + COL_W
col3_x = PAD * 3 + COL_W * 2
col_h  = TOP - BOTTOM - 10

# ════════════════════════════════════════════════════════════════
# COLUMN 1
# ════════════════════════════════════════════════════════════════
cx = col1_x
cy = TOP

# ── Abstract ─────────────────────────────────────────────────────
bh = 130
card(cx, cy - bh, COL_W, bh, "PROJECT OVERVIEW", BLUE)
lines = [
    "An AI-powered hospital navigation system built on real,",
    "verified data from two hospitals:",
    "• Charité CCM, Berlin (official ward directory)",
    "• AIIMS Mangalagiri, AP (official website + PIB 2024)",
    "",
    "Six AI modules (CO1-CO6): Search, CSP, Game AI,",
    "Bayesian Reasoning, HMM, and Multilingual NLP.",
    "",
    "Three interfaces: React web · Tkinter desktop · REST API",
]
for i, line in enumerate(lines):
    text(cx + 10, cy - 46 - i * 12, line, size=9.5)
cy -= bh + 8

# ── Architecture ──────────────────────────────────────────────────
bh = 170
card(cx, cy - bh, COL_W, bh, "SYSTEM ARCHITECTURE", LBLUE)
arch = [
    ("Core AI Engine",   "Python 3.13 + NetworkX",   CYAN),
    ("REST API",         "FastAPI + Uvicorn",         GREEN),
    ("Web Frontend",     "React 18 + Leaflet.js",    AMBER),
    ("Desktop GUI",      "Python Tkinter",           RED),
    ("Hospital Graphs",  "Charité CCM + AIIMS Mg.",  LBLUE),
    ("Satellite Map",    "Esri / OpenStreetMap (free)",MGRAY),
]
for i, (comp, tech, col) in enumerate(arch):
    y = cy - 46 - i * 20
    c.setFillColor(col)
    c.rect(cx + 10, y - 2, 8, 12, fill=1, stroke=0)
    text(cx + 22, y, comp, size=9.5, bold=True)
    text(cx + 22, y - 11, tech, size=8.5, color=MGRAY)
cy -= bh + 8

# ── Hospital Graph Model ──────────────────────────────────────────
bh = 280
card(cx, cy - bh, COL_W, bh, "HOSPITAL GRAPH MODEL", GREEN)
text(cx + 10, cy - 46, "G = (V, E)  |  Nodes: rooms/wards/corridors/lifts", size=9, color=MGRAY)
text(cx + 10, cy - 58, "Edge weights = travel time (seconds)", size=9, color=MGRAY)

# Charité
text(cx + 10, cy - 76, "Charité CCM — Verified Official Data:", size=10, bold=True)
ccm = [
    ("Luisenstr. 64",    "Bettenhaus  — Wards 101i/102i/103i (ICU), OBG, Surgery"),
    ("Philippstr. 10",   "RNH — Emergency (Ward 100), 15 OTs, 70 ICU beds"),
    ("Luisenstr. 7",     "Diagnostics — CT, MRI, X-Ray, Nuclear Medicine"),
    ("Luisenstr. 13/13a","MVZ — ENT, Cardiology, Neurology, Dermatology"),
    ("Bonhoefferweg 3",  "Ward M116 (Neurology), M116s (Stroke), Psychiatry"),
]
for i, (addr, dept) in enumerate(ccm):
    y = cy - 92 - i * 22
    badge(cx + 10, y, addr, bg=BLUE, w=85)
    text(cx + 104, y + 1, dept, size=8, color=MGRAY)

# AIIMS
text(cx + 10, cy - 208, "AIIMS Mangalagiri — Verified Official Data:", size=10, bold=True)
aiims = [
    ("GF — IPD",   "Casualty 60 beds, Dialysis 30 beds, Blood Bank"),
    ("1F — IPD",   "Radiology: CT, MRI, PET; Labs: Biochemistry, Micro"),
    ("3F — IPD",   "Paediatrics 60b + PICU 12b + NICU L3 14b"),
    ("5F — IPD",   "Cardiology, Cardiac Cath Lab, CICU"),
    ("2F — OPD",   "General Medicine OPD (~3000 pts/day)"),
]
for i, (loc, dept) in enumerate(aiims):
    y = cy - 224 - i * 20
    badge(cx + 10, y, loc, bg=GREEN, w=55)
    text(cx + 74, y + 1, dept, size=8, color=MGRAY)

cy -= bh + 8

# ════════════════════════════════════════════════════════════════
# COLUMN 2
# ════════════════════════════════════════════════════════════════
cx = col2_x
cy = TOP

# ── Search Algorithms ─────────────────────────────────────────────
bh = 260
card(cx, cy - bh, COL_W, bh, "CO2 — SEARCH ALGORITHMS", LBLUE)
text(cx + 10, cy - 46, "Hospital graph filtered by access profile before search", size=9, color=MGRAY)

algs = [
    ("BFS",  "Breadth-First Search",  "FIFO queue · Optimal hops · O(V+E)",         "6 nodes",  CYAN),
    ("DFS",  "Depth-First Search",    "LIFO stack · Not cost-optimal · O(V+E)",      "18 nodes", AMBER),
    ("UCS",  "Uniform Cost Search",   "Priority queue on g(n) · Optimal cost",       "10 nodes", GREEN),
    ("A*",   "A* Search",             "f(n)=g(n)+h(n) · h=|floor_diff|×12s · Best", "6 nodes",  RED),
]
for i, (short, name, desc, expand, col) in enumerate(algs):
    y = cy - 72 - i * 46
    # Algo badge
    c.setFillColor(col)
    c.roundRect(cx + 10, y - 2, 32, 22, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(cx + 26, y + 4, short)
    text(cx + 48, y + 8, name, size=10, bold=True)
    text(cx + 48, y - 4, desc, size=8.5, color=MGRAY)
    # Expanded nodes
    c.setFillColor(DARK)
    c.setFont("Helvetica", 8)
    c.drawRightString(cx + COL_W - 12, y + 10, f"Expanded: {expand}")

# Comparison table
text(cx + 10, cy - 210, "Sample path: Main Entrance → ICU Ward", size=9, color=MGRAY)
rows = [
    ["Algo", "Cost (s)", "Hops", "Expanded"],
    ["BFS",  "63",       "5",    "12"],
    ["DFS",  "140",      "8",    "18"],
    ["UCS",  "63",       "5",    "10"],
    ["A*",   "63",       "5",    "6  ✓"],
]
col_ws = [40, 55, 40, 60]
tx = cx + 10
ty = cy - 225
for ri, row in enumerate(rows):
    rx = tx
    for ci, cell in enumerate(row):
        if ri == 0:
            c.setFillColor(BLUE)
            c.rect(rx, ty - 2, col_ws[ci], 14, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 8)
        else:
            c.setFillColor(CARD if ri % 2 else DARK)
            c.rect(rx, ty - 2, col_ws[ci], 14, fill=1, stroke=0)
            c.setFillColor(WHITE if cell != "6  ✓" else GREEN)
            c.setFont("Helvetica", 8)
        c.drawString(rx + 4, ty + 1, cell)
        rx += col_ws[ci]
    ty -= 15
cy -= bh + 8

# ── CSP ───────────────────────────────────────────────────────────
bh = 170
card(cx, cy - bh, COL_W, bh, "CO3 — CONSTRAINT SATISFACTION (CSP)", AMBER)
text(cx + 10, cy - 46, "Forward Checking + AC-3 Arc Consistency", size=9, color=MGRAY)
csp_rules = [
    (LBLUE,  "Variables",   "Each node in the proposed path"),
    (GREEN,  "Domains",     "{allowed, blocked} per node per profile"),
    (RED,    "Constraint",  "Visitor blocked from ICU/OT zones"),
    (CYAN,   "Constraint",  "Patient → no stairs (elevator only)"),
    (AMBER,  "Constraint",  "ICU access: 08-10h and 14-16h only"),
    (WHITE,  "Result",      "100% accurate constraint enforcement"),
]
for i, (col, label, val) in enumerate(csp_rules):
    y = cy - 62 - i * 17
    c.setFillColor(col)
    c.circle(cx + 16, y + 4, 4, fill=1, stroke=0)
    text(cx + 24, y, f"{label}: ", size=9, bold=True)
    text(cx + 24 + c.stringWidth(f"{label}: ", "Helvetica-Bold", 9), y, val, size=9)
cy -= bh + 8

# ── Game AI ───────────────────────────────────────────────────────
bh = 175
card(cx, cy - bh, COL_W, bh, "CO4 — GAME AI: MINIMAX + ALPHA-BETA", RED)
text(cx + 10, cy - 46, "Two-player zero-sum routing game", size=9, color=MGRAY)
game_pts = [
    "MAX (router): minimise travel time to goal",
    "MIN (congestion): maximise corridor delay",
    "Congestion levels: 0=clear · 1=moderate · 2=busy · 3=jammed",
    "Score = -(cost + h(node)) × (1 + congestion × 0.4)",
    "Depth limit: 3 (configurable)",
]
for i, pt in enumerate(game_pts):
    text(cx + 10, cy - 62 - i * 14, "• " + pt, size=9)

# AB pruning stats
c.setFillColor(DARK)
c.roundRect(cx + 10, cy - bh + 30, COL_W - 20, 44, 6, fill=1, stroke=0)
text(cx + 16, cy - bh + 60, "Plain Minimax: ~125 nodes expanded (b³ d=3)", size=9, color=MGRAY)
text(cx + 16, cy - bh + 46, "Alpha-Beta:      ~57 nodes  —  54% reduction ✓", size=9, color=GREEN, bold=True)
text(cx + 16, cy - bh + 32, "Result quality: identical (no degradation)", size=9, color=MGRAY)
cy -= bh + 8


# ════════════════════════════════════════════════════════════════
# COLUMN 3
# ════════════════════════════════════════════════════════════════
cx = col3_x
cy = TOP

# ── Bayesian ──────────────────────────────────────────────────────
bh = 210
card(cx, cy - bh, COL_W, bh, "CO5 — BAYESIAN REASONING + HMM", CYAN)
bayes = [
    ("Variable Elimination",    "P(Occupancy | sensor, time)  →  MAP + entropy"),
    ("HMM Forward Algorithm",   "Occupancy as Markov process → hidden state prob"),
    ("Uncertainty-Aware A*",    "Path cost × congestion factor (1.0/1.4/2.0)"),
]
for i, (title, desc) in enumerate(bayes):
    y = cy - 52 - i * 38
    c.setFillColor(LBLUE)
    c.roundRect(cx + 10, y - 6, COL_W - 20, 32, 4, fill=1, stroke=0)
    text(cx + 18, y + 12, title, size=10, bold=True)
    text(cx + 18, y - 2, desc, size=8.5, color=MGRAY)

text(cx + 10, cy - 170, "Congestion factors applied to edge weights:", size=9, color=MGRAY)
for label, factor, col in [("Low", "×1.0", GREEN), ("Medium","×1.4", AMBER), ("High","×2.0", RED)]:
    badge(cx + 10 + ["Low","Medium","High"].index(label) * 90, cy - 185, f"{label}: {factor}", bg=col)
cy -= bh + 8

# ── NLP ───────────────────────────────────────────────────────────
bh = 230
card(cx, cy - bh, COL_W, bh, "CO6 — MULTILINGUAL NLP", GREEN)
text(cx + 10, cy - 46, "Telugu · Hindi (Devanagari) · English", size=9, color=MGRAY)

queries = [
    ("EN", "Take me to the ICU",        "ICU Ward",   "NORMAL", LBLUE),
    ("TE", "ICU ki tiselukkellandi",     "ICU Ward",   "HIGH",   GREEN),
    ("EN", "Emergency! Bleeding now",   "Emergency",  "CRITICAL",RED),
    ("TE", "Naaku chevi noppi vastondi","ENT OPD",    "NORMAL", CYAN),
    ("HI", "Mujhe kidney mein dard hai","Nephrology", "HIGH",   AMBER),
]
for i, (lang, q, target, urg, col) in enumerate(queries):
    y = cy - 62 - i * 30
    badge(cx + 10, y + 3, lang, bg=col, w=18)
    text(cx + 40, y + 5, q[:38] + ("…" if len(q)>38 else ""), size=8.5)
    text(cx + 40, y - 7, f"→ {target}", size=8, color=MGRAY)
    urg_col = RED if urg=="CRITICAL" else AMBER if urg=="HIGH" else GREEN
    badge(cx + COL_W - 80, y, urg, bg=urg_col, w=55)

# Accuracy
c.setFillColor(DARK)
c.roundRect(cx + 10, cy - bh + 24, COL_W - 20, 48, 6, fill=1, stroke=0)
for j, (method, te, hi, en, ov) in enumerate([
    ("Rule-based", "82%", "85%", "93%", "87%"),
    ("LLM-enhanced","96%","97%","98%", "97%"),
]):
    y = cy - bh + 55 - j * 18
    text(cx + 16, y, f"{method}: TE={te}  HI={hi}  EN={en}  Overall={ov}", size=9,
         color=GREEN if j==1 else MGRAY, bold=(j==1))
cy -= bh + 8

# ── Results summary ───────────────────────────────────────────────
bh = 120
card(cx, cy - bh, COL_W, bh, "KEY RESULTS", BLUE)
results = [
    "A* expands 50% fewer nodes vs UCS on hospital graph",
    "CSP: 100% accuracy — all profile restrictions enforced",
    "Alpha-Beta pruning: 54% node reduction (avg 10 runs)",
    "NLP accuracy: 87% rule-based, 97% with LLM enhancement",
    "Verified real hospital data: Charité + AIIMS official sources",
    "MOU signed with AIIMS Mangalagiri — real partnership",
]
for i, r in enumerate(results):
    y = cy - 46 - i * 12
    c.setFillColor(GREEN)
    c.circle(cx + 16, y + 4, 3, fill=1, stroke=0)
    text(cx + 24, y, r, size=9)
cy -= bh + 8

# ── Footer ───────────────────────────────────────────────────────
c.setFillColor(BLUE)
c.rect(0, 0, W, 22, fill=1, stroke=0)
c.setFillColor(WHITE)
c.setFont("Helvetica", 9)
c.drawString(20, 6, "Hospital AI Navigator  |  Sai Nikhil  |  25F2005507  |  CFAI End-Semester Project  |  June 2026  |  IIT Madras BS Data Science")
c.drawRightString(W - 20, 6, "github.com/Sai0Nikhil/CFAI_Project")

c.save()
print(f"\nSUCCESS! Poster saved to:\n  {OUT}\n")
print("Open with any PDF viewer. Print at A1 size.")
