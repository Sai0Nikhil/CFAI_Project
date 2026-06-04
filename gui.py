"""
gui.py — Hospital AI Navigator · Tkinter Desktop App
======================================================
Connects to FastAPI backend on http://localhost:8000
Run: python gui.py  (make sure backend is running first)

Tabs:
  1. 🏥 Hospital     — select Charité or AIIMS, view node count
  2. 🔍 Search       — BFS / DFS / UCS / A* with trace
  3. 🧩 CSP          — path constraint validation
  4. ♟  Game AI      — Minimax / Alpha-Beta triage routing
  5. 🎲 Bayesian     — occupancy inference + HMM
  6. 🌐 NLP          — multilingual query parser
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
try:
    import requests
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

BASE = "http://localhost:8000/api"

# ── Colour palette ─────────────────────────────────────────────────────────────
BG       = "#1e293b"
BG2      = "#0f172a"
CARD     = "#243448"
ACCENT   = "#3b82f6"
ACCENT2  = "#10b981"
RED      = "#ef4444"
YELLOW   = "#f59e0b"
TEXT     = "#f1f5f9"
SUBTEXT  = "#94a3b8"
BORDER   = "#334155"
SUCCESS  = "#22c55e"
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_H   = ("Segoe UI", 14, "bold")
FONT_SM  = ("Segoe UI", 9)

# ── Helpers ────────────────────────────────────────────────────────────────────

def api(method, path, **kwargs):
    try:
        r = getattr(requests, method)(BASE + path, timeout=30, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "❌ Backend not running. Start it with:\n  cd C:\\CFAI_Project\n  python -m uvicorn backend.main:app --reload --port 8000"
    except Exception as e:
        return None, str(e)

def styled_btn(parent, text, cmd, color=ACCENT, width=18):
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg=TEXT, font=FONT_B,
                     relief="flat", bd=0, padx=12, pady=6,
                     activebackground=color, activeforeground=TEXT,
                     cursor="hand2", width=width)

def label(parent, text, font=FONT, fg=TEXT, **kw):
    return tk.Label(parent, text=text, bg=CARD, fg=fg, font=font, **kw)

def section(parent, text):
    f = tk.Frame(parent, bg=BORDER, height=1)
    f.pack(fill="x", pady=(14,2))
    tk.Label(parent, text=text, bg=CARD, fg=SUBTEXT,
             font=("Segoe UI", 9, "bold")).pack(anchor="w")

def card(parent, **kw):
    f = tk.Frame(parent, bg=CARD, bd=0, relief="flat", padx=16, pady=14)
    f.pack(fill="both", expand=True, padx=12, pady=8, **kw)
    return f

def output_box(parent, height=12):
    t = scrolledtext.ScrolledText(parent, height=height, bg=BG2, fg=TEXT,
                                  font=("Consolas", 9), relief="flat",
                                  bd=0, insertbackground=TEXT,
                                  selectbackground=ACCENT)
    t.pack(fill="both", expand=True, pady=(6,0))
    return t

def clear_and_write(box, text):
    box.config(state="normal")
    box.delete("1.0", tk.END)
    box.insert(tk.END, text)
    box.config(state="disabled")

def combo(parent, values, default=0, width=32):
    var = tk.StringVar()
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      width=width, state="readonly", font=FONT)
    if values:
        cb.current(default)
    cb.pack(anchor="w", pady=3)
    return var, cb

# ── App ────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hospital AI Navigator")
        self.geometry("900x680")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(780, 560)

        # Shared state
        self.hospital   = tk.StringVar(value="charite")
        self.nodes_list = []   # [(id, label), ...]

        self._build_header()
        self._build_notebook()
        self._load_nodes()

    # ── Header ─────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG2, pady=10, padx=20)
        hdr.pack(fill="x")

        tk.Label(hdr, text="🏥 Hospital AI Navigator",
                 bg=BG2, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(side="left")

        # Hospital toggle
        tog = tk.Frame(hdr, bg=BG2)
        tog.pack(side="right")
        tk.Label(tog, text="Hospital:", bg=BG2, fg=SUBTEXT, font=FONT).pack(side="left", padx=(0,6))
        for val, lbl in [("charite","🇩🇪 Charité CCM"), ("aiims","🇮🇳 AIIMS Mangalagiri")]:
            tk.Radiobutton(tog, text=lbl, variable=self.hospital, value=val,
                           command=self._load_nodes,
                           bg=BG2, fg=TEXT, selectcolor=BG2,
                           activebackground=BG2, activeforeground=ACCENT,
                           font=FONT).pack(side="left", padx=4)

        # Status bar
        self.status_var = tk.StringVar(value="Connecting to backend…")
        tk.Label(hdr, textvariable=self.status_var,
                 bg=BG2, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=20)

    # ── Notebook tabs ──────────────────────────────────────────────────────────

    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.TNotebook",      background=BG,  borderwidth=0)
        style.configure("Custom.TNotebook.Tab",  background=BG2, foreground=SUBTEXT,
                        padding=[14,8], font=FONT_B)
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", TEXT)])

        self.nb = ttk.Notebook(self, style="Custom.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=8, pady=(4,8))

        self.tab_search    = self._mk_tab("🔍 Search")
        self.tab_csp       = self._mk_tab("🧩 CSP")
        self.tab_game      = self._mk_tab("♟ Game AI")
        self.tab_bayesian  = self._mk_tab("🎲 Bayesian")
        self.tab_nlp       = self._mk_tab("🌐 NLP")

        self._build_search(self.tab_search)
        self._build_csp(self.tab_csp)
        self._build_game(self.tab_game)
        self._build_bayesian(self.tab_bayesian)
        self._build_nlp(self.tab_nlp)

    def _mk_tab(self, name):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text=name)
        return frame

    # ── Load nodes ─────────────────────────────────────────────────────────────

    def _load_nodes(self):
        def task():
            data, err = api("get", f"/nodes?hospital={self.hospital.get()}")
            if err:
                self.status_var.set(f"⚠ {err[:60]}")
                return
            self.nodes_list = [(n["id"], n["label"]) for n in data]
            labels = [n["label"] for n in data]
            h_data, _ = api("get", f"/health")
            count = h_data["hospitals"][self.hospital.get()]["nodes"] if h_data else len(labels)
            self.status_var.set(f"✅ Connected  ·  {count} nodes  ·  {self.hospital.get().upper()}")
            # Refresh all combos
            self.after(0, lambda: self._refresh_combos(labels))
        threading.Thread(target=task, daemon=True).start()

    def _refresh_combos(self, labels):
        for cb in getattr(self, "_node_combos", []):
            cb["values"] = labels
            if labels: cb.current(0)

    # ── TAB 1: Search ──────────────────────────────────────────────────────────

    def _build_search(self, parent):
        c = card(parent)

        tk.Label(c, text="🔍 Graph Search — BFS · DFS · UCS · A*",
                 bg=CARD, fg=TEXT, font=FONT_H).pack(anchor="w", pady=(0,10))

        # Controls row
        ctrl = tk.Frame(c, bg=CARD)
        ctrl.pack(fill="x")

        # Algorithm
        tk.Label(ctrl, text="Algorithm", bg=CARD, fg=SUBTEXT, font=FONT_SM).grid(row=0,column=0,sticky="w",padx=(0,10))
        self.search_algo = tk.StringVar(value="astar")
        for i,(v,l) in enumerate([("astar","⭐ A*"),("ucs","💰 UCS"),("bfs","🌊 BFS"),("dfs","🔦 DFS")]):
            tk.Radiobutton(ctrl, text=l, variable=self.search_algo, value=v,
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=FONT).grid(row=0,column=i+1,padx=4)

        # Profile
        tk.Label(ctrl, text="Profile", bg=CARD, fg=SUBTEXT, font=FONT_SM).grid(row=1,column=0,sticky="w",pady=(8,0))
        self.search_profile = tk.StringVar(value="staff")
        for i,(v,l) in enumerate([("staff","🩺 Staff"),("emergency","🚨 Emergency"),("visitor","👤 Visitor"),("patient","♿ Patient")]):
            tk.Radiobutton(ctrl, text=l, variable=self.search_profile, value=v,
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=FONT).grid(row=1,column=i+1,padx=4)

        # Start / Goal dropdowns
        row2 = tk.Frame(c, bg=CARD)
        row2.pack(fill="x", pady=(10,0))
        tk.Label(row2, text="Start:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,6))
        self.search_start = tk.StringVar()
        cb_start = ttk.Combobox(row2, textvariable=self.search_start, width=35, state="readonly", font=FONT)
        cb_start.pack(side="left", padx=(0,16))
        tk.Label(row2, text="Goal:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,6))
        self.search_goal = tk.StringVar()
        cb_goal = ttk.Combobox(row2, textvariable=self.search_goal, width=35, state="readonly", font=FONT)
        cb_goal.pack(side="left")
        self._node_combos = getattr(self, "_node_combos", []) + [cb_start, cb_goal]

        # Buttons
        btn_row = tk.Frame(c, bg=CARD)
        btn_row.pack(anchor="w", pady=(10,0))
        styled_btn(btn_row, "▶  Run Search",   self._run_search, ACCENT).pack(side="left", padx=(0,8))
        styled_btn(btn_row, "⚡ Compare All 4", self._run_compare, ACCENT2, width=16).pack(side="left")

        section(c, "RESULTS")
        self.search_out = output_box(c, 16)

    def _run_search(self):
        start_label = self.search_start.get()
        goal_label  = self.search_goal.get()
        start_id = next((n[0] for n in self.nodes_list if n[1]==start_label), start_label)
        goal_id  = next((n[0] for n in self.nodes_list if n[1]==goal_label),  goal_label)
        body = {"algorithm": self.search_algo.get(),
                "profile":   self.search_profile.get(),
                "start": start_id, "goal": goal_id,
                "hospital":  self.hospital.get()}
        clear_and_write(self.search_out, "⏳ Running…")
        def task():
            data, err = api("post", "/search", json=body)
            if err: self.after(0, lambda: clear_and_write(self.search_out, err)); return
            lines = [
                f"Algorithm  : {data.get('algorithm','')}",
                f"Profile    : {data.get('profile','')}",
                f"Start      : {data.get('start','')}",
                f"Goal       : {data.get('goal','')}",
                f"",
                f"{'✅ PATH FOUND' if data.get('path') else '❌ NO PATH'}",
                f"Hops       : {len(data.get('path',[]))}",
                f"Cost       : {data.get('cost',0):.1f}s  (~{data.get('cost',0)/60:.1f} min)",
                f"Expansions : {data.get('stats',{}).get('expansions','—')}",
                f"Peak Front : {data.get('stats',{}).get('peak_frontier','—')}",
                f"",
                f"PATH:",
                "  →  ".join(data.get('path',[])) or "None",
                f"",
                f"STEP TRACE (first 30 steps):",
            ]
            for t in data.get("trace",[])[:30]:
                lines.append(f"  [{t.get('step',''):>3}] {t.get('action',''):10} {t.get('node','')}  {t.get('note','')}")
            self.after(0, lambda: clear_and_write(self.search_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()

    def _run_compare(self):
        start_label = self.search_start.get()
        goal_label  = self.search_goal.get()
        start_id = next((n[0] for n in self.nodes_list if n[1]==start_label), start_label)
        goal_id  = next((n[0] for n in self.nodes_list if n[1]==goal_label),  goal_label)
        body = {"profile": self.search_profile.get(),
                "start": start_id, "goal": goal_id,
                "hospital": self.hospital.get()}
        clear_and_write(self.search_out, "⏳ Running all 4 algorithms…")
        def task():
            data, err = api("post", "/compare", json=body)
            if err: self.after(0, lambda: clear_and_write(self.search_out, err)); return
            lines = ["ALGORITHM COMPARISON", "="*60,
                     f"{'Algorithm':<12} {'Found':>6} {'Hops':>5} {'Cost(s)':>9} {'Expand':>8} {'Optimal':>10}",
                     "-"*60]
            for alg in ["bfs","dfs","ucs","astar"]:
                r = data.get(alg,{})
                found = "✅" if r.get("path") else "❌"
                hops  = len(r.get("path",[]))
                cost  = f"{r.get('cost',0):.0f}"
                exp   = r.get("stats",{}).get("expansions","—")
                opt   = {"bfs":"Hops only","dfs":"❌ No","ucs":"✅ Cost","astar":"✅ Cost+h"}[alg]
                lines.append(f"{alg.upper():<12} {found:>6} {hops:>5} {cost:>9} {str(exp):>8} {opt:>10}")
            self.after(0, lambda: clear_and_write(self.search_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()

    # ── TAB 2: CSP ─────────────────────────────────────────────────────────────

    def _build_csp(self, parent):
        c = card(parent)
        tk.Label(c, text="🧩 CSP — Constraint Satisfaction Path Validator",
                 bg=CARD, fg=TEXT, font=FONT_H).pack(anchor="w", pady=(0,10))

        ctrl = tk.Frame(c, bg=CARD)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Profile", bg=CARD, fg=SUBTEXT, font=FONT_SM).grid(row=0,column=0,sticky="w",padx=(0,10))
        self.csp_profile = tk.StringVar(value="visitor")
        for i,(v,l) in enumerate([("staff","🩺 Staff"),("emergency","🚨 Emergency"),("visitor","👤 Visitor"),("patient","♿ Patient")]):
            tk.Radiobutton(ctrl, text=l, variable=self.csp_profile, value=v,
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=FONT).grid(row=0,column=i+1,padx=4)

        row2 = tk.Frame(c, bg=CARD)
        row2.pack(fill="x", pady=(10,0))
        tk.Label(row2, text="Start:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,6))
        self.csp_start = tk.StringVar()
        cb_s = ttk.Combobox(row2, textvariable=self.csp_start, width=30, state="readonly", font=FONT)
        cb_s.pack(side="left", padx=(0,12))
        tk.Label(row2, text="Goal:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,6))
        self.csp_goal = tk.StringVar()
        cb_g = ttk.Combobox(row2, textvariable=self.csp_goal, width=30, state="readonly", font=FONT)
        cb_g.pack(side="left", padx=(0,12))
        tk.Label(row2, text="Hour:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,4))
        self.csp_hour = tk.StringVar(value="10")
        tk.Spinbox(row2, from_=0, to=23, textvariable=self.csp_hour,
                   width=4, bg=BG2, fg=TEXT, font=FONT,
                   buttonbackground=BG2).pack(side="left")
        self._node_combos += [cb_s, cb_g]

        btn_row = tk.Frame(c, bg=CARD)
        btn_row.pack(anchor="w", pady=(10,0))
        styled_btn(btn_row, "▶  Validate Path", self._run_csp, ACCENT).pack(side="left")

        section(c, "CSP VALIDATION RESULT")
        self.csp_out = output_box(c, 16)

    def _run_csp(self):
        start_label = self.csp_start.get()
        goal_label  = self.csp_goal.get()
        start_id = next((n[0] for n in self.nodes_list if n[1]==start_label), start_label)
        goal_id  = next((n[0] for n in self.nodes_list if n[1]==goal_label),  goal_label)
        hospital = self.hospital.get()
        hour     = int(self.csp_hour.get() or 10)
        profile  = self.csp_profile.get()
        clear_and_write(self.csp_out, "⏳ Finding path then validating constraints…")

        def task():
            # First find path via A*
            sr, err = api("post", "/search", json={"algorithm":"astar","profile":profile,
                                                    "start":start_id,"goal":goal_id,"hospital":hospital})
            if err: self.after(0, lambda: clear_and_write(self.csp_out, err)); return
            path = sr.get("path", [])
            if not path:
                self.after(0, lambda: clear_and_write(self.csp_out,
                    "❌ No path found — cannot validate CSP.\nTry a different profile or nodes.")); return

            data, err = api("post", "/csp/validate",
                            json={"path":path,"profile":profile,"hour":hour,"hospital":hospital})
            if err: self.after(0, lambda: clear_and_write(self.csp_out, err)); return

            result = "✅ PATH IS VALID" if data.get("overall_valid") else "⚠️  CONSTRAINTS VIOLATED"
            lines = [
                result, "="*55,
                f"Profile   : {profile}",
                f"Hour      : {hour:02d}:00",
                f"Path      : {' → '.join(path)}",
                f"Cost      : {sr.get('cost',0):.0f}s",
                f"",
                f"Forward Check : {'✅ PASS' if data.get('forward_check_passed') else '❌ FAIL'}",
                f"AC-3          : {'✅ PASS' if data.get('ac3_consistent') else '❌ FAIL'}",
                f"",
                f"CONSTRAINT TRACE:",
            ]
            for t in data.get("trace", []):
                icon = "✅" if t.get("result")=="PASS" else "❌" if t.get("result")=="FAIL" else "↩"
                lines.append(f"  {icon} [{t.get('phase',''):14}] {t.get('node',''):30} {t.get('reason','')}")
            self.after(0, lambda: clear_and_write(self.csp_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()

    # ── TAB 3: Game AI ─────────────────────────────────────────────────────────

    def _build_game(self, parent):
        c = card(parent)
        tk.Label(c, text="♟ Game AI — Minimax + Alpha-Beta Pruning",
                 bg=CARD, fg=TEXT, font=FONT_H).pack(anchor="w", pady=(0,10))
        tk.Label(c, text="MAX = Ambulance (minimise travel time)   MIN = Congestion (maximise delay)",
                 bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(anchor="w", pady=(0,8))

        ctrl = tk.Frame(c, bg=CARD)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Profile", bg=CARD, fg=SUBTEXT, font=FONT_SM).grid(row=0,column=0,sticky="w",padx=(0,10))
        self.game_profile = tk.StringVar(value="emergency")
        for i,(v,l) in enumerate([("emergency","🚨 Emergency"),("staff","🩺 Staff")]):
            tk.Radiobutton(ctrl, text=l, variable=self.game_profile, value=v,
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=FONT).grid(row=0,column=i+1,padx=4)

        row2 = tk.Frame(c, bg=CARD)
        row2.pack(fill="x", pady=(10,0))
        tk.Label(row2, text="Start:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,6))
        self.game_start = tk.StringVar()
        cb_s = ttk.Combobox(row2, textvariable=self.game_start, width=30, state="readonly", font=FONT)
        cb_s.pack(side="left", padx=(0,12))
        tk.Label(row2, text="Goal:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,6))
        self.game_goal = tk.StringVar()
        cb_g = ttk.Combobox(row2, textvariable=self.game_goal, width=30, state="readonly", font=FONT)
        cb_g.pack(side="left", padx=(0,12))
        tk.Label(row2, text="Depth:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(side="left", padx=(0,4))
        self.game_depth = tk.StringVar(value="3")
        tk.Spinbox(row2, from_=1, to=6, textvariable=self.game_depth,
                   width=4, bg=BG2, fg=TEXT, font=FONT,
                   buttonbackground=BG2).pack(side="left")
        self._node_combos += [cb_s, cb_g]

        btn_row = tk.Frame(c, bg=CARD)
        btn_row.pack(anchor="w", pady=(10,0))
        styled_btn(btn_row, "▶  Run Minimax", self._run_game, ACCENT).pack(side="left")

        section(c, "MINIMAX RESULT")
        self.game_out = output_box(c, 16)

    def _run_game(self):
        start_label = self.game_start.get()
        goal_label  = self.game_goal.get()
        start_id = next((n[0] for n in self.nodes_list if n[1]==start_label), start_label)
        goal_id  = next((n[0] for n in self.nodes_list if n[1]==goal_label),  goal_label)
        body = {"start":start_id,"goal":goal_id,
                "profile":self.game_profile.get(),
                "depth":int(self.game_depth.get()),
                "use_alpha_beta":True,
                "hospital":self.hospital.get()}
        clear_and_write(self.game_out, "⏳ Running Minimax…")
        def task():
            data, err = api("post", "/game", json=body)
            if err: self.after(0, lambda: clear_and_write(self.game_out, err)); return
            if "error" in data:
                self.after(0, lambda: clear_and_write(self.game_out, f"❌ {data['error']}")); return
            lines = [
                f"MINIMAX RESULT", "="*55,
                f"Best Value    : {data.get('best_value','—')}",
                f"Prune Events  : {data.get('stats',{}).get('pruning_events','—')}",
                f"Trace Steps   : {data.get('stats',{}).get('trace_steps','—')}",
                f"Depth Limit   : {data.get('stats',{}).get('depth_limit','—')}",
                f"",
                f"EXPLANATION:",
                data.get("explanation",""),
                f"",
                f"BOUNDED RATIONALITY:",
                data.get("bounded_rationality",""),
                f"",
                f"ALPHA-BETA PRUNE LOG (first 10):",
            ]
            for p in data.get("prune_log",[])[:10]:
                lines.append(f"  ✂  {p.get('note','')}")
            self.after(0, lambda: clear_and_write(self.game_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()

    # ── TAB 4: Bayesian ────────────────────────────────────────────────────────

    def _build_bayesian(self, parent):
        c = card(parent)
        tk.Label(c, text="🎲 Bayesian Inference + HMM",
                 bg=CARD, fg=TEXT, font=FONT_H).pack(anchor="w", pady=(0,10))

        # Sub-tabs inside
        nb2 = ttk.Notebook(c)
        nb2.pack(fill="both", expand=True)

        t_infer = tk.Frame(nb2, bg=CARD)
        t_hmm   = tk.Frame(nb2, bg=CARD)
        t_route = tk.Frame(nb2, bg=CARD)
        nb2.add(t_infer, text="Variable Elimination")
        nb2.add(t_hmm,   text="HMM Forward")
        nb2.add(t_route, text="Uncertainty Route")

        # --- Inference ---
        tk.Label(t_infer, text="Corridor Sensor:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(anchor="w", pady=(10,2))
        self.bayes_sensor = tk.StringVar(value="busy")
        sens_f = tk.Frame(t_infer, bg=CARD)
        sens_f.pack(anchor="w")
        for s in ["clear","busy","jammed"]:
            tk.Radiobutton(sens_f, text=s, variable=self.bayes_sensor, value=s,
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=FONT).pack(side="left", padx=6)
        tk.Label(t_infer, text="Time of Day:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(anchor="w", pady=(8,2))
        self.bayes_tod = tk.StringVar(value="morning")
        tod_f = tk.Frame(t_infer, bg=CARD)
        tod_f.pack(anchor="w")
        for s in ["morning","afternoon","evening","night"]:
            tk.Radiobutton(tod_f, text=s, variable=self.bayes_tod, value=s,
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=FONT).pack(side="left", padx=6)
        styled_btn(t_infer, "▶  Run Inference", self._run_bayes_infer, ACCENT).pack(anchor="w", pady=(10,0))
        self.bayes_infer_out = output_box(t_infer, 10)

        # --- HMM ---
        tk.Label(t_hmm, text="Observation sequence (comma-separated, values: clear/busy/jammed):",
                 bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(anchor="w", pady=(10,2))
        self.hmm_obs = tk.StringVar(value="clear,busy,busy,jammed")
        tk.Entry(t_hmm, textvariable=self.hmm_obs, width=40,
                 bg=BG2, fg=TEXT, font=FONT, relief="flat",
                 insertbackground=TEXT).pack(anchor="w", pady=4)
        styled_btn(t_hmm, "▶  Run HMM Forward", self._run_hmm, ACCENT).pack(anchor="w", pady=(6,0))
        self.hmm_out = output_box(t_hmm, 10)

        # --- Uncertainty Route ---
        tk.Label(t_route, text="Start:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(anchor="w", pady=(10,2))
        self.bayes_start = tk.StringVar()
        cb_s = ttk.Combobox(t_route, textvariable=self.bayes_start, width=40, state="readonly", font=FONT)
        cb_s.pack(anchor="w", pady=3)
        tk.Label(t_route, text="Goal:", bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(anchor="w")
        self.bayes_goal = tk.StringVar()
        cb_g = ttk.Combobox(t_route, textvariable=self.bayes_goal, width=40, state="readonly", font=FONT)
        cb_g.pack(anchor="w", pady=3)
        self._node_combos += [cb_s, cb_g]
        styled_btn(t_route, "▶  Run Uncertainty Route", self._run_bayes_route, ACCENT).pack(anchor="w", pady=(6,0))
        self.bayes_route_out = output_box(t_route, 10)

    def _run_bayes_infer(self):
        body = {"sensor": self.bayes_sensor.get(),
                "time_of_day": self.bayes_tod.get()}
        clear_and_write(self.bayes_infer_out, "⏳ Running Bayesian inference…")
        def task():
            data, err = api("post", "/bayes/infer", json=body)
            if err: self.after(0, lambda: clear_and_write(self.bayes_infer_out, err)); return
            lines = [
                "BAYESIAN VARIABLE ELIMINATION", "="*45,
                f"Sensor      : {self.bayes_sensor.get()}",
                f"Time of Day : {self.bayes_tod.get()}",
                f"",
                f"POSTERIOR DISTRIBUTION (Occupancy):",
            ]
            for k,v in data.get("posterior",{}).items():
                bar = "█" * int(v * 30)
                lines.append(f"  {k:<12} {v:.3f}  {bar}")
            lines += ["", f"MAP Estimate  : {data.get('map_estimate','—')}",
                      f"Entropy       : {data.get('entropy',0):.4f}",
                      f"Confidence    : {data.get('confidence',0)*100:.1f}%"]
            self.after(0, lambda: clear_and_write(self.bayes_infer_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()

    def _run_hmm(self):
        obs = [o.strip() for o in self.hmm_obs.get().split(",")]
        body = {"observations": obs}
        clear_and_write(self.hmm_out, "⏳ Running HMM forward pass…")
        def task():
            data, err = api("post", "/bayes/hmm", json=body)
            if err: self.after(0, lambda: clear_and_write(self.hmm_out, err)); return
            lines = [
                "HMM FORWARD ALGORITHM", "="*45,
                f"Observations : {' → '.join(obs)}",
                f"",
                "FORWARD PROBABILITIES PER STEP:",
            ]
            for i, step in enumerate(data.get("forward_pass", [])):
                lines.append(f"\n  Step {i+1} | obs={obs[i] if i<len(obs) else '?'}")
                for state, prob in step.items():
                    bar = "█" * int(prob * 25)
                    lines.append(f"    {state:<18} {prob:.4f}  {bar}")
            lines += ["", f"Most Likely Final State : {data.get('most_likely_state','—')}"]
            self.after(0, lambda: clear_and_write(self.hmm_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()

    def _run_bayes_route(self):
        start_label = self.bayes_start.get()
        goal_label  = self.bayes_goal.get()
        start_id = next((n[0] for n in self.nodes_list if n[1]==start_label), start_label)
        goal_id  = next((n[0] for n in self.nodes_list if n[1]==goal_label),  goal_label)
        body = {"start":start_id,"goal":goal_id,"hospital":self.hospital.get()}
        clear_and_write(self.bayes_route_out, "⏳ Running uncertainty-aware routing…")
        def task():
            data, err = api("post", "/bayes/route", json=body)
            if err: self.after(0, lambda: clear_and_write(self.bayes_route_out, err)); return
            lines = [
                "UNCERTAINTY-AWARE ROUTING (Bayesian A*)", "="*50,
                f"Base Cost     : {data.get('total_base_cost',0):.0f}s",
                f"Adjusted Cost : {data.get('total_adjusted_cost',0):.0f}s",
                f"Overhead      : +{data.get('total_adjusted_cost',0)-data.get('total_base_cost',0):.0f}s",
                "",
                f"{'Node':<35} {'Sensor':<10} {'Occupancy':<12} {'Factor':<8} {'Cost'}",
                "-"*75,
            ]
            for seg in data.get("adjusted_path",[]):
                lines.append(
                    f"  {seg.get('node',''):<33} {seg.get('sensor',''):<10} "
                    f"{seg.get('occupancy',''):<12} ×{seg.get('factor',1):.1f}    "
                    f"{seg.get('adjusted_cost',0):.0f}s"
                )
            self.after(0, lambda: clear_and_write(self.bayes_route_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()

    # ── TAB 5: NLP ─────────────────────────────────────────────────────────────

    def _build_nlp(self, parent):
        c = card(parent)
        tk.Label(c, text="🌐 Multilingual NLP — Telugu · Hindi · English",
                 bg=CARD, fg=TEXT, font=FONT_H).pack(anchor="w", pady=(0,6))
        tk.Label(c, text="Type a symptom or department name in any language:",
                 bg=CARD, fg=SUBTEXT, font=FONT_SM).pack(anchor="w", pady=(0,10))

        # Input
        inp_f = tk.Frame(c, bg=CARD)
        inp_f.pack(fill="x")
        self.nlp_query = tk.StringVar()
        entry = tk.Entry(inp_f, textvariable=self.nlp_query, width=55,
                         bg=BG2, fg=TEXT, font=("Segoe UI", 12),
                         relief="flat", insertbackground=TEXT)
        entry.pack(side="left", padx=(0,10), ipady=6)
        entry.bind("<Return>", lambda e: self._run_nlp())
        styled_btn(inp_f, "➤  Parse", self._run_nlp, ACCENT, width=10).pack(side="left")

        # Demo queries
        section(c, "DEMO QUERIES — click to try")
        demos = tk.Frame(c, bg=CARD)
        demos.pack(anchor="w", pady=(4,0))
        samples = [
            ("🌐 ICU",           "Take me to the ICU please"),
            ("🌐 Ear pain",      "I have ear pain"),
            ("🌐 Chest pain",    "Severe chest pain emergency"),
            ("🇮🇳 ICU కి",      "ICU కి తీసుకెళ్ళండి"),
            ("🇮🇳 చెవి నొప్పి", "నాకు చెవి నొప్పి వస్తోంది"),
            ("🇮🇳 गुर्दा",       "मुझे किडनी में दर्द है"),
            ("🚨 Emergency",     "Emergency! bleeding help now"),
        ]
        for lbl, q in samples:
            btn = tk.Button(demos, text=lbl, font=FONT_SM,
                            bg=BG2, fg=SUBTEXT, relief="flat",
                            bd=0, padx=8, pady=4, cursor="hand2",
                            activebackground=ACCENT,
                            command=lambda qt=q: (self.nlp_query.set(qt), self._run_nlp()))
            btn.pack(side="left", padx=3, pady=2)

        section(c, "NLP PARSE RESULT")
        self.nlp_out = output_box(c, 12)

    def _run_nlp(self):
        q = self.nlp_query.get().strip()
        if not q: return
        body = {"query": q, "use_llm": False, "hospital": self.hospital.get()}
        clear_and_write(self.nlp_out, f"⏳ Parsing: {q}")
        def task():
            data, err = api("post", "/nlp", json=body)
            if err: self.after(0, lambda: clear_and_write(self.nlp_out, err)); return
            urg = data.get("urgency", {})
            lines = [
                "NLP PARSE RESULT", "="*50,
                f"Query          : {q}",
                f"",
                f"Language       : {data.get('language','—').upper()}",
                f"Intent         : {data.get('intent','—')}",
                f"",
                f"Target Dept    : {data.get('target_friendly','—')}",
                f"Target Node    : {data.get('target_node','—')}",
                f"",
                f"Urgency Level  : {urg.get('level','—')}",
                f"Urgency Score  : {urg.get('score','—')}",
                f"Urgency Reason : {urg.get('reason','—')}",
                f"",
                f"Route Strategy : {'Emergency A* (fastest)' if urg.get('level')=='CRITICAL' else 'Standard A*'}",
                f"",
                f"METHOD         : {'LLM-enhanced' if data.get('llm_used') else 'Rule-based NLP (keyword + pattern matching)'}",
            ]
            if data.get("keywords"):
                lines += ["", f"Keywords found : {', '.join(data.get('keywords',[]))}"]
            self.after(0, lambda: clear_and_write(self.nlp_out, "\n".join(lines)))
        threading.Thread(target=task, daemon=True).start()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
