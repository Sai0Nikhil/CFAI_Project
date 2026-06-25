"""
Hospital AI Navigator — Tkinter Desktop GUI
Mirrors the React web frontend with a dark theme.
Run: python gui.py
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json

BASE = "http://localhost:8000/api"

# ─── Colour palette (dark theme, matches web warm-cream / dark sidebar) ───────
BG        = "#111827"   # page background
CARD      = "#1f2937"   # card background
CARD2     = "#374151"   # secondary card / row alt
BORDER    = "#374151"   # border
TEXT      = "#f9fafb"   # primary text
MUTED     = "#9ca3af"   # muted text
ACCENT    = "#b45309"   # amber / primary
ACCENT2   = "#0891b2"   # cyan / secondary
SUCCESS   = "#10b981"   # green
ERROR     = "#ef4444"   # red
WARNING   = "#f59e0b"   # yellow
BTN_FG    = "#ffffff"
ENTRY_BG  = "#374151"
ENTRY_FG  = "#f9fafb"
SEL_BG    = "#b45309"

FONT_BODY  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_LABEL = ("Segoe UI", 9, "bold")
FONT_H1    = ("Segoe UI", 18, "bold")
FONT_H2    = ("Segoe UI", 13, "bold")
FONT_H3    = ("Segoe UI", 11, "bold")
FONT_MONO  = ("Consolas", 9)

HOSPITALS = [
    {"id": "charite", "name": "Charité Berlin", "flag": "🇩🇪",
     "default_start": "ENTRANCE_MAIN", "default_goal": "Node_302_ICU_Tower"},
    {"id": "aiims",   "name": "AIIMS Mangalagiri", "flag": "🇮🇳",
     "default_start": "ENTRANCE_MAIN", "default_goal": "ICU_Ward"},
]

PROFILES = [
    ("staff",     "🩺 Staff"),
    ("emergency", "🚨 Emergency"),
    ("visitor",   "👤 Visitor"),
    ("patient",   "♿ Patient"),
]

ALGOS = [
    ("astar", "⭐ A*"),
    ("ucs",   "💰 UCS"),
    ("bfs",   "🌊 BFS"),
    ("dfs",   "🔦 DFS"),
]

CMPLX   = {"bfs":"O(V+E)", "dfs":"O(V+E)", "ucs":"O((V+E)logV)", "astar":"O((V+E)logV)"}
OPTIMAL = {"bfs":"Hops only", "dfs":"❌ No", "ucs":"✅ Cost", "astar":"✅ Cost + h(n)"}


# ─── HTTP helpers ─────────────────────────────────────────────────────────────
def api_get(path, params=None):
    return requests.get(BASE + path, params=params, timeout=30).json()

def api_post(path, body):
    return requests.post(BASE + path, json=body, timeout=30).json()


# ─── Reusable widget builders ─────────────────────────────────────────────────
def make_label(parent, text, font=FONT_LABEL, fg=MUTED, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=CARD, **kw)

def make_card(parent, **kw):
    f = tk.Frame(parent, bg=CARD, bd=0, relief="flat", **kw)
    f.configure(highlightbackground=BORDER, highlightthickness=1)
    return f

def make_btn(parent, text, cmd, color=ACCENT, **kw):
    b = tk.Button(parent, text=text, command=cmd,
                  bg=color, fg=BTN_FG, activebackground=color,
                  activeforeground=BTN_FG, relief="flat",
                  font=FONT_LABEL, cursor="hand2",
                  padx=14, pady=7, bd=0, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_darken(color)))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

def _darken(hex_col):
    h = hex_col.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(max(0,r-30), max(0,g-30), max(0,b-30))

def make_combo(parent, values, default=None, width=28):
    v = tk.StringVar(value=default or (values[0] if values else ""))
    cb = ttk.Combobox(parent, textvariable=v, values=values,
                      width=width, state="readonly", font=FONT_BODY)
    cb.configure(style="Dark.TCombobox")
    return cb, v

def make_output(parent, height=14):
    t = scrolledtext.ScrolledText(parent, bg="#0d1117", fg=TEXT,
                                  font=FONT_MONO, height=height,
                                  relief="flat", bd=0, wrap="word",
                                  insertbackground=TEXT)
    t.configure(state="disabled")
    return t

def out_write(widget, text, tag=None):
    widget.configure(state="normal")
    if tag:
        widget.insert("end", text + "\n", tag)
    else:
        widget.insert("end", text + "\n")
    widget.see("end")
    widget.configure(state="disabled")

def out_clear(widget):
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.configure(state="disabled")

def style_output(widget):
    widget.tag_config("ok",      foreground=SUCCESS)
    widget.tag_config("err",     foreground=ERROR)
    widget.tag_config("warn",    foreground=WARNING)
    widget.tag_config("path",    foreground=ACCENT)
    widget.tag_config("header",  foreground=ACCENT2, font=FONT_H3)
    widget.tag_config("muted",   foreground=MUTED)
    widget.tag_config("bold",    font=("Consolas", 9, "bold"), foreground=TEXT)


# ═══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🏥 Hospital AI Navigator")
        self.configure(bg=BG)
        self.geometry("1100x760")
        self.minsize(900, 600)
        self.resizable(True, True)

        # shared state
        self.hospital_var = tk.StringVar(value="charite")
        self._nodes_cache = {}

        self._apply_styles()
        self._build_ui()
        self._load_nodes()

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",        background=BG,   borderwidth=0)
        style.configure("TNotebook.Tab",    background=CARD,  foreground=MUTED,
                        padding=[18, 8],    font=FONT_LABEL,  borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BTN_FG)])
        style.configure("Dark.TCombobox",   fieldbackground=ENTRY_BG,
                        background=ENTRY_BG, foreground=ENTRY_FG,
                        arrowcolor=TEXT,    selectbackground=SEL_BG,
                        selectforeground=BTN_FG)
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", ENTRY_BG)],
                  foreground=[("readonly", ENTRY_FG)])
        style.configure("TScrollbar",       background=CARD2, troughcolor=BG,
                        arrowcolor=MUTED)
        style.configure("Horizontal.TScale",background=CARD, troughcolor=CARD2,
                        sliderlength=18)

    # ── Top bar ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        top = tk.Frame(self, bg=CARD, pady=10)
        top.pack(fill="x")

        tk.Label(top, text="🏥  Hospital AI Navigator",
                 font=FONT_H1, fg=TEXT, bg=CARD).pack(side="left", padx=20)

        # Hospital toggle
        htog = tk.Frame(top, bg=CARD)
        htog.pack(side="right", padx=20)
        tk.Label(htog, text="Hospital:", font=FONT_LABEL, fg=MUTED, bg=CARD).pack(side="left", padx=(0,6))
        for h in HOSPITALS:
            rb = tk.Radiobutton(htog, text=f"{h['flag']} {h['name']}",
                                variable=self.hospital_var, value=h["id"],
                                command=self._on_hospital_change,
                                bg=CARD, fg=TEXT, selectcolor=CARD,
                                activebackground=CARD, activeforeground=ACCENT,
                                font=FONT_LABEL, indicatoron=0,
                                relief="flat", padx=10, pady=6,
                                cursor="hand2")
            rb.pack(side="left", padx=2)

        # Status bar
        self.status_var = tk.StringVar(value="⚡ Ready — make sure backend is running on :8000")
        status = tk.Label(self, textvariable=self.status_var,
                          font=FONT_SMALL, fg=MUTED, bg=BG, anchor="w")
        status.pack(fill="x", padx=16, pady=(4, 0))

        # Notebook tabs
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        self._tab_home    = HomeTab(self.nb, self)
        self._tab_search  = SearchTab(self.nb, self)
        self._tab_csp     = CSPTab(self.nb, self)
        self._tab_game    = GameTab(self.nb, self)
        self._tab_bayes   = BayesTab(self.nb, self)
        self._tab_nlp     = NLPTab(self.nb, self)

        self.nb.add(self._tab_home,   text="🏠 Home")
        self.nb.add(self._tab_search, text="🔍 Search  CO2")
        self.nb.add(self._tab_csp,    text="🧩 CSP  CO3")
        self.nb.add(self._tab_game,   text="♟ Game AI  CO4")
        self.nb.add(self._tab_bayes,  text="🎲 Bayesian  CO5")
        self.nb.add(self._tab_nlp,    text="🌐 NLP  CO6")

    def _on_hospital_change(self):
        hid = self.hospital_var.get()
        self.status_var.set(f"Switched to {hid.upper()} — reloading nodes…")
        self._load_nodes()

    def _load_nodes(self):
        def _do():
            hid = self.hospital_var.get()
            try:
                data = api_get("/nodes", {"hospital": hid})
                self._nodes_cache[hid] = data
                labels = [n["label"] for n in data]
                ids    = [n["id"]    for n in data]
                self.after(0, lambda: self._distribute_nodes(labels, ids))
                self.after(0, lambda: self.status_var.set(f"✅ {len(data)} nodes loaded for {hid}"))
            except Exception as e:
                self.after(0, lambda: self.status_var.set(f"⚠️ Could not load nodes: {e}"))
        threading.Thread(target=_do, daemon=True).start()

    def _distribute_nodes(self, labels, ids):
        hid = self.hospital_var.get()
        h_info = next(h for h in HOSPITALS if h["id"] == hid)
        for tab in [self._tab_search, self._tab_csp, self._tab_game, self._tab_nlp]:
            if hasattr(tab, "update_nodes"):
                tab.update_nodes(labels, ids, h_info)

    @property
    def hospital(self):
        return self.hospital_var.get()

    @property
    def hospital_info(self):
        return next(h for h in HOSPITALS if h["id"] == self.hospital)


# ═══════════════════════════════════════════════════════════════════════════════
# ── HOME TAB ──────────────────────────────────────────────────────────────────
class HomeTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        # Hero
        tk.Label(self, text="Hospital AI Navigator",
                 font=("Segoe UI", 26, "bold"), fg=TEXT, bg=BG).pack(pady=(40, 4))
        tk.Label(self, text="CO1 · CO2 · CO3 · CO4 · CO5 · CO6",
                 font=FONT_BODY, fg=ACCENT, bg=BG).pack()
        tk.Label(self,
                 text="A full-stack AI routing system built on verified hospital graphs.\n"
                      "Switch between Charité Berlin 🇩🇪 and AIIMS Mangalagiri 🇮🇳 using the toggle above.",
                 font=FONT_BODY, fg=MUTED, bg=BG, justify="center").pack(pady=12)

        # Stats strip
        stats_frame = tk.Frame(self, bg=CARD, pady=8)
        stats_frame.pack(padx=60, pady=6)
        self._stat_frames = {}
        for i, (val, lbl) in enumerate([("41/55", "Nodes"), ("52/70", "Edges"),
                                         ("3", "Languages"), ("6", "AI Modules")]):
            f = tk.Frame(stats_frame, bg=CARD, padx=28, pady=8)
            f.grid(row=0, column=i, padx=1)
            if i < 3:
                tk.Frame(stats_frame, bg=BORDER, width=1).grid(row=0, column=i, sticky="nse")
            tk.Label(f, text=val, font=("Segoe UI", 22, "bold"), fg=ACCENT, bg=CARD).pack()
            tk.Label(f, text=lbl.upper(), font=("Segoe UI", 7, "bold"), fg=MUTED, bg=CARD).pack()

        # Feature cards
        cards_frame = tk.Frame(self, bg=BG)
        cards_frame.pack(fill="x", padx=40, pady=20)
        features = [
            ("🎙️", "Navigate",   "Speak or type in Telugu, Hindi, English.\nAI routes you to the right ward.",     ACCENT),
            ("🔍", "Search",     "BFS · DFS · UCS · A* with full step traces\nand algorithm comparison matrix.",   "#0891b2"),
            ("🧩", "CSP",        "AC-3 arc consistency · Forward Checking\nprofile & time-window constraints.",    "#7c3aed"),
            ("♟",  "Game AI",    "Minimax + Alpha-Beta pruning for\nadversarial ambulance routing.",               "#b91c1c"),
            ("🎲", "Bayesian",   "Variable Elimination · HMM Forward\nActive Belief POMDP routing.",              "#065f46"),
            ("🌐", "NLP",        "Multilingual intent parsing: Telugu,\nHindi, English — urgency detection.",      "#92400e"),
        ]
        for i, (icon, title, desc, color) in enumerate(features):
            c = tk.Frame(cards_frame, bg=CARD, bd=0, padx=16, pady=16)
            c.configure(highlightbackground=color, highlightthickness=1)
            c.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="nsew")
            cards_frame.columnconfigure(i%3, weight=1)
            tk.Label(c, text=icon, font=("Segoe UI", 22), bg=CARD, fg=TEXT).pack(anchor="w")
            tk.Label(c, text=title, font=FONT_H3, bg=CARD, fg=color).pack(anchor="w", pady=(2,0))
            tk.Label(c, text=desc, font=FONT_SMALL, bg=CARD, fg=MUTED,
                     justify="left", wraplength=220).pack(anchor="w", pady=(4,0))

        # Footer
        tk.Label(self,
                 text="Sai Nikhil · 2500032630 · 25SC136E Computational Foundations For AI · KL University",
                 font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="bottom", pady=12)


# ═══════════════════════════════════════════════════════════════════════════════
# ── SEARCH TAB ────────────────────────────────────────────────────────────────
class SearchTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app  = app
        self._ids = []
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14,4))
        tk.Label(hdr, text="🔍 Graph Search", font=FONT_H2, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(hdr, text=" CO2 ", font=FONT_SMALL, bg=ACCENT, fg=BTN_FG,
                 padx=6, pady=2).pack(side="left", padx=6)
        tk.Label(hdr, text="BFS · DFS · UCS · A*  on the hospital graph",
                 font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")

        # Controls card
        ctrl = make_card(self)
        ctrl.pack(fill="x", padx=16, pady=6)

        row1 = tk.Frame(ctrl, bg=CARD)
        row1.pack(fill="x", padx=14, pady=12)

        # Algorithm
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Algorithm").pack(anchor="w")
        self.algo_cb, self.algo_var = make_combo(col, [a[1] for a in ALGOS], ALGOS[0][1], 16)
        self.algo_cb.pack(anchor="w", pady=3)

        # Profile
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Profile").pack(anchor="w")
        self.prof_cb, self.prof_var = make_combo(col, [p[1] for p in PROFILES], PROFILES[0][1], 16)
        self.prof_cb.pack(anchor="w", pady=3)

        # Start
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Start Node").pack(anchor="w")
        self.start_cb, self.start_var = make_combo(col, [], width=22)
        self.start_cb.pack(anchor="w", pady=3)

        # Goal
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Goal Node").pack(anchor="w")
        self.goal_cb, self.goal_var = make_combo(col, [], width=22)
        self.goal_cb.pack(anchor="w", pady=3)

        # Buttons
        btn_row = tk.Frame(ctrl, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(0,12))
        make_btn(btn_row, "▶  Run Search", self._run_search).pack(side="left", padx=(0,8))
        make_btn(btn_row, "⚡  Compare All 4", self._run_compare, ACCENT2).pack(side="left")

        # Output
        self.out = make_output(self, height=20)
        style_output(self.out)
        self.out.pack(fill="both", expand=True, padx=16, pady=(4,12))

    def update_nodes(self, labels, ids, h_info):
        self._ids = ids
        self.start_cb["values"] = labels
        self.goal_cb["values"]  = labels
        if labels:
            # pick defaults
            ds = h_info.get("default_start", "")
            dg = h_info.get("default_goal",  "")
            si = ids.index(ds) if ds in ids else 0
            gi = ids.index(dg) if dg in ids else min(5, len(ids)-1)
            self.start_var.set(labels[si])
            self.goal_var.set(labels[gi])

    def _get_id(self, label, cb_values):
        try:
            i = list(cb_values).index(label)
            return self._ids[i] if i < len(self._ids) else label
        except ValueError:
            return label

    def _algo_id(self):
        label = self.algo_var.get()
        return next((a[0] for a in ALGOS if a[1] == label), "astar")

    def _prof_id(self):
        label = self.prof_var.get()
        return next((p[0] for p in PROFILES if p[1] == label), "staff")

    def _run_search(self):
        algo  = self._algo_id()
        prof  = self._prof_id()
        start = self._get_id(self.start_var.get(), self.start_cb["values"])
        goal  = self._get_id(self.goal_var.get(),  self.goal_cb["values"])
        out_clear(self.out)
        out_write(self.out, f"Running {algo.upper()} [{prof}]  {start} → {goal} …", "muted")

        def _do():
            try:
                r = api_post("/search", {"algorithm": algo, "profile": prof,
                                         "start": start, "goal": goal,
                                         "hospital": self.app.hospital})
                self.after(0, lambda: self._show_search(r, algo))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ Error: {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_search(self, r, algo):
        path = r.get("path", [])
        cost = r.get("cost", 0)
        stats = r.get("stats", {})
        trace = r.get("trace", [])
        out_clear(self.out)
        if path:
            out_write(self.out, "─── RESULT ───────────────────────────────", "header")
            out_write(self.out, f"✅  Path found!  Hops: {len(path)}   Cost: {cost:.0f}s   Expansions: {stats.get('expansions','—')}", "ok")
            out_write(self.out, "PATH:  " + " → ".join(path), "path")
            out_write(self.out, f"Complexity: {CMPLX.get(algo,'?')}   Optimal: {OPTIMAL.get(algo,'?')}", "muted")
            out_write(self.out, "\n─── STEP TRACE ────────────────────────────", "header")
            for t in trace[:50]:
                line = f"  [{t.get('step',''):>3}] {t.get('action',''):12}  {t.get('node','')}"
                if algo == "astar":
                    line += f"   f={t.get('f',0):.1f}  g={t.get('g',0):.1f}  h={t.get('h',0):.1f}"
                if t.get("note"):
                    line += f"   # {t['note']}"
                out_write(self.out, line)
            if len(trace) > 50:
                out_write(self.out, f"  … {len(trace)-50} more steps …", "muted")
        else:
            out_write(self.out, f"❌  No path found for profile [{self._prof_id()}].", "err")
            out_write(self.out, "Try Staff or Emergency profile.", "muted")

    def _run_compare(self):
        prof  = self._prof_id()
        start = self._get_id(self.start_var.get(), self.start_cb["values"])
        goal  = self._get_id(self.goal_var.get(),  self.goal_cb["values"])
        out_clear(self.out)
        out_write(self.out, "⚡ Running all 4 algorithms simultaneously…", "warn")

        def _do():
            try:
                r = api_post("/compare", {"profile": prof, "start": start,
                                          "goal": goal, "hospital": self.app.hospital})
                self.after(0, lambda: self._show_compare(r))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_compare(self, r):
        out_clear(self.out)
        out_write(self.out, "─── ALGORITHM COMPARISON ──────────────────", "header")
        header = f"{'Algorithm':18} {'Found':6} {'Hops':5} {'Cost(s)':8} {'Expansions':11} {'Optimal':18} {'Complexity'}"
        out_write(self.out, header, "bold")
        out_write(self.out, "─" * 80, "muted")
        for aid, label in [("bfs","🌊 BFS"),("dfs","🔦 DFS"),("ucs","💰 UCS"),("astar","⭐ A*")]:
            d = r.get(aid, {})
            p = d.get("path", [])
            found = "✅" if p else "❌"
            hops  = str(len(p)) if p else "—"
            cost  = f"{d.get('cost',0):.0f}" if p else "—"
            exp   = str(d.get("stats",{}).get("expansions","—")) if p else "—"
            opt   = OPTIMAL.get(aid,"?")
            cmplx = CMPLX.get(aid,"?")
            line  = f"{label:18} {found:6} {hops:5} {cost:8} {exp:11} {opt:18} {cmplx}"
            tag   = "ok" if p else "err"
            out_write(self.out, line, tag)


# ═══════════════════════════════════════════════════════════════════════════════
# ── CSP TAB ───────────────────────────────────────────────────────────────────
class CSPTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app  = app
        self._ids = []
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14,4))
        tk.Label(hdr, text="🧩 Constraint Satisfaction", font=FONT_H2, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(hdr, text=" CO3 ", font=FONT_SMALL, bg="#7c3aed", fg=BTN_FG,
                 padx=6, pady=2).pack(side="left", padx=6)
        tk.Label(hdr, text="Backtracking · Forward Checking · AC-3",
                 font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")

        ctrl = make_card(self)
        ctrl.pack(fill="x", padx=16, pady=6)

        row1 = tk.Frame(ctrl, bg=CARD)
        row1.pack(fill="x", padx=14, pady=12)

        # Profile
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Access Profile").pack(anchor="w")
        self.prof_cb, self.prof_var = make_combo(col, [p[1] for p in PROFILES], PROFILES[2][1], 16)
        self.prof_cb.pack(anchor="w", pady=3)

        # Start
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Start Node").pack(anchor="w")
        self.start_cb, self.start_var = make_combo(col, [], width=22)
        self.start_cb.pack(anchor="w", pady=3)

        # Goal
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Goal Node").pack(anchor="w")
        self.goal_cb, self.goal_var = make_combo(col, [], width=22)
        self.goal_cb.pack(anchor="w", pady=3)

        # Hour slider
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        self.hour_lbl = make_label(col, "Hour of Day (10:00)")
        self.hour_lbl.pack(anchor="w")
        self.hour_var = tk.IntVar(value=10)
        sl = ttk.Scale(col, from_=0, to=23, variable=self.hour_var,
                       orient="horizontal", command=self._update_hour_label,
                       style="Horizontal.TScale")
        sl.pack(fill="x", pady=3)

        btn_row = tk.Frame(ctrl, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(0,12))
        make_btn(btn_row, "▶  Validate Path (CSP)", self._run_csp).pack(side="left", padx=(0,8))
        make_btn(btn_row, "🕐  Check Time Window", self._run_timewindow, "#065f46").pack(side="left")

        self.out = make_output(self, height=20)
        style_output(self.out)
        self.out.pack(fill="both", expand=True, padx=16, pady=(4,12))

    def _update_hour_label(self, _=None):
        self.hour_lbl.config(text=f"Hour of Day ({self.hour_var.get():02d}:00)")

    def update_nodes(self, labels, ids, h_info):
        self._ids = ids
        self.start_cb["values"] = labels
        self.goal_cb["values"]  = labels
        if labels:
            ds = h_info.get("default_start","")
            dg = h_info.get("default_goal","")
            si = ids.index(ds) if ds in ids else 0
            gi = ids.index(dg) if dg in ids else min(5, len(ids)-1)
            self.start_var.set(labels[si])
            self.goal_var.set(labels[gi])

    def _get_id(self, label):
        try:
            i = list(self.start_cb["values"]).index(label)
            return self._ids[i]
        except ValueError:
            return label

    def _prof_id(self):
        label = self.prof_var.get()
        return next((p[0] for p in PROFILES if p[1] == label), "visitor")

    def _run_csp(self):
        prof  = self._prof_id()
        start = self._get_id(self.start_var.get())
        goal  = self._get_id(self.goal_var.get())
        hour  = self.hour_var.get()
        out_clear(self.out)
        out_write(self.out, f"Finding path then validating CSP [{prof}]  {start} → {goal}  @{hour:02d}:00 …", "muted")

        def _do():
            try:
                sr = api_post("/search", {"algorithm":"astar","profile":prof,
                                          "start":start,"goal":goal,
                                          "hospital":self.app.hospital})
                path = sr.get("path",[])
                if not path:
                    self.after(0, lambda: out_write(self.out, "❌ No path found for this profile.", "err"))
                    return
                r = api_post("/csp/validate", {"path":path,"profile":prof,
                                               "hour":hour,"hospital":self.app.hospital})
                self.after(0, lambda: self._show_csp(r, path, sr.get("cost",0)))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_csp(self, r, path, cost):
        out_clear(self.out)
        valid  = r.get("valid", False)
        steps  = r.get("steps", [])
        blocked = r.get("blocked_nodes", [])
        out_write(self.out, "─── CSP VALIDATION ────────────────────────", "header")
        out_write(self.out, f"Path ({len(path)} nodes, {cost:.0f}s): " + " → ".join(path), "path")
        out_write(self.out, "")
        if valid:
            out_write(self.out, "✅  All constraints SATISFIED — path is valid!", "ok")
        else:
            out_write(self.out, f"❌  CONSTRAINT VIOLATION — {len(blocked)} node(s) blocked", "err")
            for b in blocked:
                out_write(self.out, f"  🚫 Blocked: {b}", "err")
        out_write(self.out, "\n─── STEP-BY-STEP CHECK ────────────────────", "header")
        for s in steps:
            icon = "✅" if s.get("allowed") else "🚫"
            tag  = "ok" if s.get("allowed") else "err"
            out_write(self.out, f"  {icon}  {s.get('node',''):<35} {s.get('reason','')}", tag)

    def _run_timewindow(self):
        prof = self._prof_id()
        goal = self._get_id(self.goal_var.get())
        def _do():
            try:
                r = api_get("/csp/time-window", {"profile": prof, "node": goal})
                self.after(0, lambda: self._show_tw(r, prof, goal))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_tw(self, r, prof, node):
        out_write(self.out, f"\n─── TIME WINDOW  [{prof}] → {node} ──────────", "header")
        windows = r.get("windows", [])
        if windows:
            for w in windows:
                out_write(self.out, f"  🕐  {w}", "ok")
        else:
            out_write(self.out, "  ⚠️  No specific time restrictions for this profile/node.", "warn")


# ═══════════════════════════════════════════════════════════════════════════════
# ── GAME AI TAB ───────────────────────────────────────────────────────────────
class GameTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app  = app
        self._ids = []
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14,4))
        tk.Label(hdr, text="♟ Adversarial Game AI", font=FONT_H2, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(hdr, text=" CO4 ", font=FONT_SMALL, bg="#b91c1c", fg=BTN_FG,
                 padx=6, pady=2).pack(side="left", padx=6)
        tk.Label(hdr, text="Minimax · Alpha-Beta Pruning · MCTS",
                 font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")

        ctrl = make_card(self)
        ctrl.pack(fill="x", padx=16, pady=6)

        row1 = tk.Frame(ctrl, bg=CARD)
        row1.pack(fill="x", padx=14, pady=12)

        # Start
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Start Node").pack(anchor="w")
        self.start_cb, self.start_var = make_combo(col, [], width=22)
        self.start_cb.pack(anchor="w", pady=3)

        # Goal
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Goal Node").pack(anchor="w")
        self.goal_cb, self.goal_var = make_combo(col, [], width=22)
        self.goal_cb.pack(anchor="w", pady=3)

        # Depth
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        self.depth_lbl = make_label(col, "Minimax Depth (3)")
        self.depth_lbl.pack(anchor="w")
        self.depth_var = tk.IntVar(value=3)
        sl = ttk.Scale(col, from_=1, to=6, variable=self.depth_var,
                       orient="horizontal", command=self._update_depth_label,
                       style="Horizontal.TScale")
        sl.pack(fill="x", pady=3)

        # Profile
        col = tk.Frame(row1, bg=CARD)
        col.pack(side="left", padx=8, fill="x", expand=True)
        make_label(col, "Profile").pack(anchor="w")
        self.prof_cb, self.prof_var = make_combo(col, [p[1] for p in PROFILES], PROFILES[1][1], 14)
        self.prof_cb.pack(anchor="w", pady=3)

        btn_row = tk.Frame(ctrl, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(0,12))
        make_btn(btn_row, "♟  Run Minimax + α-β", self._run_game).pack(side="left", padx=(0,8))
        make_btn(btn_row, "🌳  Run MCTS", self._run_mcts, "#b91c1c").pack(side="left")

        self.out = make_output(self, height=20)
        style_output(self.out)
        self.out.pack(fill="both", expand=True, padx=16, pady=(4,12))

    def _update_depth_label(self, _=None):
        self.depth_lbl.config(text=f"Minimax Depth ({self.depth_var.get()})")

    def update_nodes(self, labels, ids, h_info):
        self._ids = ids
        self.start_cb["values"] = labels
        self.goal_cb["values"]  = labels
        if labels:
            ds = h_info.get("default_start","")
            dg = h_info.get("default_goal","")
            si = ids.index(ds) if ds in ids else 0
            gi = ids.index(dg) if dg in ids else min(5, len(ids)-1)
            self.start_var.set(labels[si])
            self.goal_var.set(labels[gi])

    def _get_id(self, label):
        try:
            i = list(self.start_cb["values"]).index(label)
            return self._ids[i]
        except ValueError:
            return label

    def _prof_id(self):
        label = self.prof_var.get()
        return next((p[0] for p in PROFILES if p[1] == label), "emergency")

    def _run_game(self):
        start = self._get_id(self.start_var.get())
        goal  = self._get_id(self.goal_var.get())
        depth = self.depth_var.get()
        prof  = self._prof_id()
        out_clear(self.out)
        out_write(self.out, f"Running Minimax α-β depth={depth}  {start} → {goal} …", "muted")

        def _do():
            try:
                r = api_post("/game", {"start":start,"goal":goal,
                                       "depth":depth,"profile":prof,
                                       "hospital":self.app.hospital})
                self.after(0, lambda: self._show_game(r))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_game(self, r):
        out_clear(self.out)
        out_write(self.out, "─── MINIMAX + ALPHA-BETA RESULT ────────────", "header")
        path     = r.get("path", [])
        cost     = r.get("cost", 0)
        pruned   = r.get("pruned_count", 0)
        total    = r.get("total_nodes", 0)
        pct      = r.get("pruning_ratio", 0)
        out_write(self.out, f"✅  Best path ({len(path)} hops, cost {cost:.0f}s)", "ok")
        out_write(self.out, "PATH:  " + " → ".join(path), "path")
        out_write(self.out, "")
        out_write(self.out, f"Nodes expanded  : {total}", "muted")
        out_write(self.out, f"Branches pruned : {pruned}  ({pct:.0%} reduction)", "ok")
        log = r.get("log", [])
        if log:
            out_write(self.out, "\n─── SEARCH LOG ─────────────────────────────", "header")
            for entry in log[:40]:
                out_write(self.out, f"  {entry}")

    def _run_mcts(self):
        start = self._get_id(self.start_var.get())
        goal  = self._get_id(self.goal_var.get())
        out_clear(self.out)
        out_write(self.out, "Running MCTS…", "muted")

        def _do():
            try:
                r = api_post("/game/mcts", {"start":start,"goal":goal,
                                            "hospital":self.app.hospital})
                self.after(0, lambda: self._show_mcts(r))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_mcts(self, r):
        out_clear(self.out)
        out_write(self.out, "─── MCTS RESULT ────────────────────────────", "header")
        path = r.get("path",[])
        out_write(self.out, f"✅  MCTS path ({len(path)} hops)", "ok")
        out_write(self.out, "PATH:  " + " → ".join(path), "path")
        for k,v in r.items():
            if k != "path":
                out_write(self.out, f"  {k}: {v}", "muted")


# ═══════════════════════════════════════════════════════════════════════════════
# ── BAYESIAN TAB ──────────────────────────────────────────────────────────────
class BayesTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14,4))
        tk.Label(hdr, text="🎲 Bayesian Reasoning", font=FONT_H2, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(hdr, text=" CO5 ", font=FONT_SMALL, bg="#065f46", fg=BTN_FG,
                 padx=6, pady=2).pack(side="left", padx=6)
        tk.Label(hdr, text="Variable Elimination · HMM Forward · Active Belief POMDP",
                 font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")

        # ── Bayesian Inference ──
        sec1 = make_card(self)
        sec1.pack(fill="x", padx=16, pady=6)
        tk.Label(sec1, text="Variable Elimination — Occupancy Inference",
                 font=FONT_H3, fg=ACCENT2, bg=CARD).pack(anchor="w", padx=14, pady=(10,4))

        r1 = tk.Frame(sec1, bg=CARD)
        r1.pack(fill="x", padx=14, pady=4)

        col = tk.Frame(r1, bg=CARD)
        col.pack(side="left", padx=8, expand=True, fill="x")
        make_label(col, "Time of Day").pack(anchor="w")
        self.tod_cb, self.tod_var = make_combo(col, ["Morning","Afternoon","Night"], "Morning", 14)
        self.tod_cb.pack(anchor="w", pady=3)

        col = tk.Frame(r1, bg=CARD)
        col.pack(side="left", padx=8, expand=True, fill="x")
        make_label(col, "Day Type").pack(anchor="w")
        self.day_cb, self.day_var = make_combo(col, ["Weekday","Weekend"], "Weekday", 14)
        self.day_cb.pack(anchor="w", pady=3)

        col = tk.Frame(r1, bg=CARD)
        col.pack(side="left", padx=8, expand=True, fill="x")
        make_label(col, "Sensor Read").pack(anchor="w")
        self.sensor_cb, self.sensor_var = make_combo(col, ["Clear","Busy","Jammed"], "Busy", 14)
        self.sensor_cb.pack(anchor="w", pady=3)

        btn_row = tk.Frame(sec1, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(4,10))
        make_btn(btn_row, "🎲  Run Variable Elimination", self._run_infer, ACCENT2).pack(side="left")

        # ── HMM ──
        sec2 = make_card(self)
        sec2.pack(fill="x", padx=16, pady=6)
        tk.Label(sec2, text="HMM Forward Algorithm — Belief Tracking",
                 font=FONT_H3, fg=ACCENT2, bg=CARD).pack(anchor="w", padx=14, pady=(10,4))

        r2 = tk.Frame(sec2, bg=CARD)
        r2.pack(fill="x", padx=14, pady=4)
        make_label(r2, "Observation Sequence (comma-separated: clear, busy, busy, jammed)").pack(anchor="w")
        self.hmm_entry = tk.Entry(r2, bg=ENTRY_BG, fg=ENTRY_FG, font=FONT_BODY,
                                  insertbackground=TEXT, relief="flat", width=50)
        self.hmm_entry.insert(0, "clear, busy, busy, jammed")
        self.hmm_entry.pack(fill="x", pady=4)

        btn_row2 = tk.Frame(sec2, bg=CARD)
        btn_row2.pack(fill="x", padx=14, pady=(0,10))
        make_btn(btn_row2, "📡  Run HMM Forward", self._run_hmm, "#065f46").pack(side="left")

        # Output
        self.out = make_output(self, height=14)
        style_output(self.out)
        self.out.pack(fill="both", expand=True, padx=16, pady=(4,12))

    def _run_infer(self):
        body = {"time_of_day": self.tod_var.get(),
                "day_type":    self.day_var.get(),
                "sensor_read": self.sensor_var.get(),
                "hospital":    self.app.hospital}
        out_clear(self.out)
        out_write(self.out, "Running Variable Elimination…", "muted")

        def _do():
            try:
                r = api_post("/bayes/infer", body)
                self.after(0, lambda: self._show_infer(r))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_infer(self, r):
        out_clear(self.out)
        out_write(self.out, "─── BAYESIAN INFERENCE RESULT ──────────────", "header")
        dist = r.get("occupancy_distribution", r.get("distribution", {}))
        for state, prob in dist.items():
            bar_len = int(prob * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            out_write(self.out, f"  {state:12}  {bar}  {prob:.1%}", "ok")
        most_likely = r.get("most_likely", "")
        if most_likely:
            out_write(self.out, f"\n  Most Likely: {most_likely}", "bold")
        for k, v in r.items():
            if k not in ("occupancy_distribution","distribution","most_likely"):
                out_write(self.out, f"  {k}: {v}", "muted")

    def _run_hmm(self):
        obs_raw = self.hmm_entry.get()
        obs = [o.strip() for o in obs_raw.split(",") if o.strip()]
        body = {"observations": obs, "hospital": self.app.hospital}
        out_clear(self.out)
        out_write(self.out, f"Running HMM Forward on: {obs} …", "muted")

        def _do():
            try:
                r = api_post("/bayes/hmm", body)
                self.after(0, lambda: self._show_hmm(r))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_hmm(self, r):
        out_clear(self.out)
        out_write(self.out, "─── HMM FORWARD BELIEF STATE ───────────────", "header")
        belief = r.get("final_belief", r.get("belief_state", {}))
        for state, prob in belief.items():
            bar_len = int(prob * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            out_write(self.out, f"  {state:12}  {bar}  {prob:.1%}", "ok")
        for k, v in r.items():
            if k not in ("final_belief","belief_state"):
                out_write(self.out, f"  {k}: {v}", "muted")


# ═══════════════════════════════════════════════════════════════════════════════
# ── NLP TAB ───────────────────────────────────────────────────────────────────
class NLPTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app  = app
        self._ids = []
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14,4))
        tk.Label(hdr, text="🌐 Multilingual NLP", font=FONT_H2, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(hdr, text=" CO6 ", font=FONT_SMALL, bg="#92400e", fg=BTN_FG,
                 padx=6, pady=2).pack(side="left", padx=6)
        tk.Label(hdr, text="Telugu · Hindi · English  —  Intent Extraction & Urgency Detection",
                 font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")

        ctrl = make_card(self)
        ctrl.pack(fill="x", padx=16, pady=6)

        tk.Label(ctrl, text="Type your query in English, Telugu, or Hindi:",
                 font=FONT_LABEL, fg=MUTED, bg=CARD).pack(anchor="w", padx=14, pady=(10,2))

        self.query_entry = tk.Text(ctrl, bg=ENTRY_BG, fg=ENTRY_FG, font=FONT_BODY,
                                   insertbackground=TEXT, relief="flat",
                                   height=3, padx=8, pady=6)
        self.query_entry.insert("1.0", "I need to go to the ICU ward urgently")
        self.query_entry.pack(fill="x", padx=14, pady=4)

        btn_row = tk.Frame(ctrl, bg=CARD)
        btn_row.pack(fill="x", padx=14, pady=(4,6))
        make_btn(btn_row, "🌐  Parse Query", self._run_nlp).pack(side="left", padx=(0,6))

        # Quick demo buttons
        demos = [
            ("🇮🇳 Telugu",  "నాకు ICU వార్డుకు వెళ్ళాలి, అత్యవసరం"),
            ("🇮🇳 Hindi",   "मुझे ICU वार्ड जाना है, बहुत जरूरी है"),
            ("🇬🇧 English", "Where is the emergency trauma ward?"),
        ]
        for label, text in demos:
            make_btn(btn_row, label, lambda t=text: self._set_query(t),
                     CARD2).pack(side="left", padx=3)

        self.out = make_output(self, height=22)
        style_output(self.out)
        self.out.pack(fill="both", expand=True, padx=16, pady=(4,12))

    def _set_query(self, text):
        self.query_entry.delete("1.0", "end")
        self.query_entry.insert("1.0", text)
        self._run_nlp()

    def update_nodes(self, labels, ids, h_info):
        self._ids = ids

    def _run_nlp(self):
        query = self.query_entry.get("1.0", "end").strip()
        if not query:
            return
        out_clear(self.out)
        out_write(self.out, f"Parsing: '{query}' …", "muted")

        def _do():
            try:
                r = api_post("/nlp", {"query": query, "hospital": self.app.hospital})
                self.after(0, lambda: self._show_nlp(r, query))
            except Exception as e:
                self.after(0, lambda: out_write(self.out, f"❌ {e}", "err"))
        threading.Thread(target=_do, daemon=True).start()

    def _show_nlp(self, r, query):
        out_clear(self.out)
        out_write(self.out, "─── NLP PARSE RESULT ───────────────────────", "header")
        out_write(self.out, f"Query      : {query}", "bold")
        lang    = r.get("language", r.get("detected_language","?"))
        intent  = r.get("intent",   r.get("target_node","?"))
        urgency = r.get("urgency",  r.get("urgency_level","?"))
        node    = r.get("node",     r.get("target_node", intent))
        conf    = r.get("confidence", r.get("score", None))
        out_write(self.out, f"Language   : {lang}", "ok")
        out_write(self.out, f"Intent     : {intent}", "ok")
        out_write(self.out, f"Node       : {node}", "path")
        urg_tag = "err" if str(urgency).lower() in ("high","critical","emergency") else "warn"
        out_write(self.out, f"Urgency    : {urgency}", urg_tag)
        if conf is not None:
            out_write(self.out, f"Confidence : {conf:.1%}" if isinstance(conf,float) else f"Confidence : {conf}", "muted")
        out_write(self.out, "\n─── RAW RESPONSE ───────────────────────────", "muted")
        out_write(self.out, json.dumps(r, indent=2), "muted")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
