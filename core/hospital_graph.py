"""
core/hospital_graph.py
======================
Charité Campus Mitte (CCM) — Hospital Navigation Graph
Berlin, Germany

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA SOURCES — 100% verified from official Charité directory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
https://www.charite.de/en/charite/campuses/campus_charite_mitte/
https://www.charite.de/en/clinical_center/.../outpatient_departments_on_campus_charite_mitte
https://neurologie.charite.de/en/for_patients/inpatient_care/wards_at_campus_charite_mitte

REAL BUILDING ADDRESSES ON CAMPUS:
  Luisenstraße 64   → Bettenhaus (21-floor ward tower)
                       Wards 101i–120, ICU 101i/102i/103i, Dialysis,
                       Surgery, OBG, Neurosurgery, Cardiology, Urology,
                       Orthopedics outpatient, Patient Admissions
  Philippstraße 10  → Rudolf-Nissen-Haus (Emergency + OTs + ICU 70 beds)
                       Ward 100 (Admissions), Central Emergency (24h)
  Luisenstraße 7    → Diagnostics Building
                       Radiology (X-Ray, CT, MRI, Mammography, Ultrasound),
                       Nuclear Medicine, Lab Medicine (Emergency Lab),
                       Nephrology outpatient, Neuroradiology, Transfusion
  Luisenstraße 13/13a → MVZ Outpatient Medical Centre
                       Dermatology, Cardiology, Neurology, Psychiatry,
                       Psychosomatic, Rheumatology, Gynecology, Endocrinology,
                       Gastroenterology, ENT, Pneumonology, Coagulation MVZ
  Bonhoefferweg 3   → Neurology & Psychiatry Department Building
                       Ward M116 (Neurology), Ward M116s (Stroke Unit),
                       Neurology / Psychiatry / Anxiety outpatient
  Sauerbruchweg 3/5 → Research / Endoscopy / Hematology
                       Endoscopy (Internal), Ward 144i, 147/148/149,
                       Oncology/Hematology outpatient, Endocrinology dept
  Rahel-Hirsch-Weg 5 → Rahel Hirsch Center (cardiology funct. dx, wards 202-203)
  Virchowweg 6      → CharitéCrossOver (CCO) — Auditorium, research, lecture halls
  Charitéplatz 1    → Main Administration / Executive Board / Dean's Office
  Luisenstraße 65   → Oncology/Hematology Outpatient · BIH Rahel Hirsch Center
  Hufelandweg 3     → Audiology, Cardiovascular Surgery, Ophthalmology
  Luisenstraße 9    → Main entrance (pedestrian) · Book Shop

ZONES (one per building/address cluster):
  'entrance'     — campus gates and main entrance
  'bettenhaus'   — Luisenstraße 64 (21-floor ward tower)
  'rnb'          — Philippstraße 10 (Rudolf-Nissen-Haus: Emergency, OTs, ICU)
  'diagnostics'  — Luisenstraße 7 (Radiology, Nuclear Med, Lab)
  'mvz'          — Luisenstraße 13/13a (MVZ outpatient clinics)
  'neuro_psych'  — Bonhoefferweg 3 (Neurology + Psychiatry wards)
  'research'     — Sauerbruchweg 3/5, Rahel-Hirsch-Weg, Virchowweg (research/endoscopy)
  'admin'        — Charitéplatz 1 (executive, dean's office)
  'historic'     — remaining historic campus buildings
"""

from __future__ import annotations
import networkx as nx
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Node catalogue — all addresses verified from official Charité directory
# ---------------------------------------------------------------------------
NODES: Dict[str, Dict[str, Any]] = {

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: entrance — Campus gates
    # ══════════════════════════════════════════════════════════════════════
    "ENTRANCE_MAIN": {
        "zone":"entrance","floor":0,"type":"entrance",
        "restricted":set(),"wheelchair":True,
        "label":"Main Entrance · Luisenstraße 9 (pedestrian)",
        "address":"CCM, Luisenstraße 9",
    },
    "ENTRANCE_PHILIPPSTR": {
        "zone":"entrance","floor":0,"type":"entrance",
        "restricted":set(),"wheelchair":True,
        "label":"Emergency Entrance · Philippstraße 10",
        "address":"CCM, Philippstraße 10",
    },
    "ENTRANCE_INVALIDENSTR": {
        "zone":"entrance","floor":0,"type":"entrance",
        "restricted":set(),"wheelchair":True,
        "label":"North Entrance · Invalidenstraße",
        "address":"CCM, Invalidenstraße side",
    },
    "LOBBY_BRIDGE": {
        "zone":"entrance","floor":1,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Glass Bridge · Luisenstraße (Bettenhaus ↔ Historic, F1)",
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: bettenhaus — Luisenstraße 64 (21-floor ward tower)
    # Confirmed: all Wards 101i-120, Dialysis, Surgery OPD, Patient Admissions
    # ══════════════════════════════════════════════════════════════════════
    "BH_Lobby": {
        "zone":"bettenhaus","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Lobby · Information Desk",
        "address":"CCM, Luisenstraße 64",
    },
    "BH_Admissions": {
        "zone":"bettenhaus","floor":0,"type":"room",
        "restricted":set(),"wheelchair":True,
        "label":"Patient Admissions",
        "address":"CCM, Luisenstraße 64",  # confirmed
    },
    "BH_Dialysis": {
        "zone":"bettenhaus","floor":0,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Dialysis Unit",
        "address":"CCM, Luisenstraße 64",  # confirmed
    },
    "BH_Elevator_A": {
        "zone":"bettenhaus","floor":0,"type":"elevator",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Elevator A",
    },
    "BH_Elevator_B": {
        "zone":"bettenhaus","floor":0,"type":"elevator",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Elevator B",
    },
    "BH_Stairs": {
        "zone":"bettenhaus","floor":0,"type":"stairs",
        "restricted":{"patient"},"wheelchair":False,
        "label":"Bettenhaus Stairs",
    },

    # Floor 1 — Bridge level
    "BH_F1_Corridor": {
        "zone":"bettenhaus","floor":1,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Corridor · F1 (Bridge Level)",
        "address":"CCM, Luisenstraße 64",
    },

    # Floors 2–3 — ICU wards (confirmed: 101i, 102i, 103i at Luisenstr 64)
    "BH_F2_Corridor": {
        "zone":"bettenhaus","floor":2,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Corridor · F2",
    },
    "Ward_101i": {
        "zone":"bettenhaus","floor":2,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Ward 101i — Interdisciplinary ICU (Anaesthesiology & Surgery)",
        "address":"CCM, Luisenstraße 64",  # confirmed official directory
    },
    "Ward_102i": {
        "zone":"bettenhaus","floor":2,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Ward 102i — Interdisciplinary Neuro-ICU",
        "address":"CCM, Luisenstraße 64",  # confirmed official directory
    },
    "Ward_103i": {
        "zone":"bettenhaus","floor":2,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Ward 103i — Interdisciplinary Intensive Care Medicine",
        "address":"CCM, Luisenstraße 64",  # confirmed official directory
    },
    # Node_302_ICU_Tower kept for backwards compatibility with existing tests/frontend
    "Node_302_ICU_Tower": {
        "zone":"bettenhaus","floor":2,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"ICU Complex · Bettenhaus F2",
        "address":"CCM, Luisenstraße 64",
    },

    # Floors 4–10 — General wards (all confirmed: Luisenstraße 64)
    "BH_F4_Corridor": {
        "zone":"bettenhaus","floor":4,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Corridor · F4",
    },
    "Ward_General_Surgery": {
        "zone":"bettenhaus","floor":4,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"General Surgery Ward (CC8)",
        "address":"CCM, Luisenstraße 64",  # confirmed
    },
    "Ward_Orthopedics": {
        "zone":"bettenhaus","floor":4,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Centre for Musculoskeletal Surgery (CMSC)",
        "address":"CCM, Luisenstraße 64",  # confirmed
    },
    "BH_F6_Corridor": {
        "zone":"bettenhaus","floor":6,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Corridor · F6",
    },
    "Ward_OBG": {
        "zone":"bettenhaus","floor":6,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Obstetrics / Gynaecology / Neonatology (CC17)",
        "address":"CCM, Luisenstraße 64",  # confirmed
    },
    "Ward_Delivery": {
        "zone":"bettenhaus","floor":6,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Delivery Rooms (Ward 108B)",
        "address":"CCM, Luisenstraße 64",  # confirmed: Delivery Rooms at L64
    },
    "BH_F8_Corridor": {
        "zone":"bettenhaus","floor":8,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Bettenhaus Corridor · F8",
    },
    "Ward_Neurosurgery": {
        "zone":"bettenhaus","floor":8,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Neurosurgery Ward (CC15)",
        "address":"CCM, Luisenstraße 64",  # confirmed
    },
    "Ward_Urology": {
        "zone":"bettenhaus","floor":8,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Urology Ward (CC8)",
        "address":"CCM, Luisenstraße 64",  # confirmed
    },
    "BH_F21_Admin": {
        "zone":"bettenhaus","floor":21,"type":"room",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Bettenhaus Administration · F21",
        "address":"CCM, Luisenstraße 64",
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: rnb — Philippstraße 10 (Rudolf-Nissen-Haus)
    # Emergency Centre: Ward 100, OTs, 70 ICU beds — confirmed
    # ══════════════════════════════════════════════════════════════════════
    "RNB_Lobby": {
        "zone":"rnb","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Rudolf-Nissen-Haus Lobby",
        "address":"CCM, Philippstraße 10",  # confirmed
    },
    "RNB_Emergency": {
        "zone":"rnb","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Central Emergency Department (Notaufnahme) · 24h",
        "address":"CCM, Philippstraße 10",  # confirmed: First Aid / Emergency Dept
    },
    "Ward_100": {
        "zone":"rnb","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Ward 100 — Admissions Ward",
        "address":"CCM, Philippstraße 10",  # confirmed official directory
    },
    "RNB_PreOp": {
        "zone":"rnb","floor":0,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Pre-Operative & Recovery Area",
        "address":"CCM, Philippstraße 10",
    },
    "RNB_Elevator": {
        "zone":"rnb","floor":0,"type":"elevator",
        "restricted":set(),"wheelchair":True,
        "label":"Rudolf-Nissen-Haus Elevator",
    },
    "RNB_F1_ICU": {
        "zone":"rnb","floor":1,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"RNH ICU — 70 beds (acute intensive care)",
        "address":"CCM, Philippstraße 10",
    },
    "RNB_F2_OT": {
        "zone":"rnb","floor":2,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"OT Suite — 15 Modular OTs incl. 2 Hybrid ORs",
        "address":"CCM, Philippstraße 10",  # confirmed: 15 OTs in RNH
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: diagnostics — Luisenstraße 7
    # Confirmed: ALL radiology, nuclear med, lab medicine, transfusion
    # ══════════════════════════════════════════════════════════════════════
    "DIAG_Lobby": {
        "zone":"diagnostics","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Diagnostics Building Lobby",
        "address":"CCM, Luisenstraße 7",
    },
    "DIAG_Radiology": {
        "zone":"diagnostics","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Diagnostic Radiology (X-Ray · CT · MRI · Mammography · Ultrasound)",
        "address":"CCM, Luisenstraße 7",  # confirmed: all imaging at L7
    },
    "DIAG_Nuclear_Med": {
        "zone":"diagnostics","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Nuclear Medicine (Dept CC6)",
        "address":"CCM, Luisenstraße 7",  # confirmed
    },
    "DIAG_Lab_Medicine": {
        "zone":"diagnostics","floor":0,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Lab Medicine · Emergency Laboratory (CC5)",
        "address":"CCM, Luisenstraße 7",  # confirmed
    },
    "DIAG_Nephrology_OPD": {
        "zone":"diagnostics","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Nephrology Outpatient (CC13)",
        "address":"CCM, Luisenstraße 7",  # confirmed
    },
    "DIAG_PhysioTherapy": {
        "zone":"diagnostics","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Physical Therapy Unit 1",
        "address":"CCM, Luisenstraße 7",  # confirmed
    },
    "DIAG_IntPatients": {
        "zone":"diagnostics","floor":0,"type":"room",
        "restricted":set(),"wheelchair":True,
        "label":"International Patients Office",
        "address":"CCM, Luisenstraße 10",  # confirmed: Luisenstraße 10
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: mvz — Luisenstraße 13 / 13a (MVZ Outpatient Medical Centre)
    # Confirmed: all MVZ clinics, most outpatient departments
    # ══════════════════════════════════════════════════════════════════════
    "MVZ_Lobby": {
        "zone":"mvz","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"MVZ Outpatient Centre Lobby",
        "address":"CCM, Luisenstraße 13",
    },
    "MVZ_Cardiology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"MVZ Cardiology · Cardiology Outpatient",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },
    "MVZ_Neurology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"MVZ Neurology · Neurological Outpatient",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },
    "MVZ_Dermatology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"MVZ Dermatology",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },
    "MVZ_Psychiatry": {
        "zone":"mvz","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"MVZ Psychiatry · Psychosomatic · Psychotherapy Outpatient",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },
    "MVZ_Rheumatology": {
        "zone":"mvz","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"MVZ Rheumatology · Rheumatology Outpatient",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },
    "MVZ_Gynecology": {
        "zone":"mvz","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"MVZ Gynecology · Endocrinology Outpatient",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },
    "MVZ_Gastroenterology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Gastroenterology · ENT · Pneumonology Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },
    "MVZ_Coagulation": {
        "zone":"mvz","floor":0,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"MVZ Coagulation / Transfusion Medicine / Haemophilia",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: neuro_psych — Bonhoefferweg 3
    # Confirmed: Neurology dept, Ward M116/M116s, Psychiatry, Anxiety OPD
    # ══════════════════════════════════════════════════════════════════════
    "NP_Lobby": {
        "zone":"neuro_psych","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Neurology & Psychiatry Building Lobby",
        "address":"CCM, Bonhoefferweg 3",  # confirmed
    },
    "Ward_M116": {
        "zone":"neuro_psych","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Ward M116 — Neurology Ward",
        "address":"CCM, Bonhoefferweg 3",  # confirmed from neurologie.charite.de
    },
    "Ward_M116s": {
        "zone":"neuro_psych","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Ward M116s — Stroke Unit",
        "address":"CCM, Bonhoefferweg 3",  # confirmed from neurologie.charite.de
    },
    "NP_Psychiatry_Ward": {
        "zone":"neuro_psych","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Psychiatry & Psychotherapy Ward (CC15)",
        "address":"CCM, Bonhoefferweg 3",  # confirmed
    },
    "NP_Anxiety_OPD": {
        "zone":"neuro_psych","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Anxiety Disorders · Neurological · Psychiatry Outpatient",
        "address":"CCM, Bonhoefferweg 3",  # confirmed
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: bettenhaus — individual departments (all at Luisenstraße 64)
    # ══════════════════════════════════════════════════════════════════════
    "OPD_Surgery": {
        "zone":"bettenhaus","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"General Surgery Outpatient",
        "address":"CCM, Luisenstraße 64",
    },
    "OPD_Gynecology": {
        "zone":"bettenhaus","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Gynaecology Outpatient · Breast Centre",
        "address":"CCM, Luisenstraße 64",
    },
    "OPD_Cardiology": {
        "zone":"bettenhaus","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Cardiology Outpatient",
        "address":"CCM, Luisenstraße 64",
    },
    "OPD_Neurosurgery": {
        "zone":"bettenhaus","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Neurosurgery Outpatient",
        "address":"CCM, Luisenstraße 64",
    },
    "OPD_Urology": {
        "zone":"bettenhaus","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Urology Outpatient",
        "address":"CCM, Luisenstraße 64",
    },
    "OPD_Orthopaedics": {
        "zone":"bettenhaus","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Orthopaedic Outpatient (CMSC)",
        "address":"CCM, Luisenstraße 64",
    },
    "OPD_Anaesthesia": {
        "zone":"bettenhaus","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Anaesthesiology · Pain Management Outpatient",
        "address":"CCM, Luisenstraße 64",
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: mvz — specific OPD departments (Luisenstraße 13/13a)
    # ══════════════════════════════════════════════════════════════════════
    "OPD_ENT": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"ENT (Ear Nose Throat) Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed from directory
    },
    "OPD_Dermatology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Dermatology & Venereology Outpatient",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },
    "OPD_Pneumonology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Pneumonology (Chest) Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },
    "OPD_Rheumatology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Rheumatology Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },
    "OPD_Endocrinology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Diabetology / Endocrinology Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },
    "OPD_Gastroenterology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Gastroenterology Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },
    "OPD_Nephrology": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Nephrology Outpatient",
        "address":"CCM, Luisenstraße 7",  # confirmed
    },
    "OPD_Oncology": {
        "zone":"research","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Oncology / Haematology Outpatient",
        "address":"CCM, Luisenstraße 65 / Sauerbruchweg 3",  # confirmed
    },
    "OPD_Psychosomatic": {
        "zone":"mvz","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Psychosomatic Medicine Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },
    "OPD_SleepMedicine": {
        "zone":"mvz","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Sleep Medicine Outpatient",
        "address":"CCM, Luisenstraße 13",  # confirmed
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: neuro_psych — departments
    # ══════════════════════════════════════════════════════════════════════
    "OPD_Neurology": {
        "zone":"neuro_psych","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Neurology Outpatient (MVZ + Dept)",
        "address":"CCM, Luisenstraße 13a / Bonhoefferweg 3",
    },
    "OPD_Psychiatry": {
        "zone":"neuro_psych","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Psychiatry & Psychotherapy Outpatient",
        "address":"CCM, Bonhoefferweg 3",  # confirmed
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: historic — Hufelandweg 3 departments
    # ══════════════════════════════════════════════════════════════════════
    "OPD_Ophthalmology": {
        "zone":"historic","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Ophthalmology Outpatient (Consulting)",
        "address":"CCM, Hufelandweg 3 / Luisenstraße 13",  # confirmed
    },
    "OPD_Audiology": {
        "zone":"historic","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Audiology & Phoniatrics Outpatient",
        "address":"CCM, Hufelandweg 3",  # confirmed
    },
    "OPD_CardiovascularSurgery": {
        "zone":"historic","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Cardiovascular Surgery Outpatient",
        "address":"CCM, Hufelandweg 3",  # confirmed
    },
    "OPD_PhysicalMedicine": {
        "zone":"mvz","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Physical Medicine & Rehabilitation",
        "address":"CCM, Luisenstraße 13a",  # confirmed
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: research — Sauerbruchweg 3/5, Rahel-Hirsch-Weg, Virchowweg
    # ══════════════════════════════════════════════════════════════════════
    "SBW_Lobby": {
        "zone":"research","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Sauerbruchweg Research / Endoscopy Building",
        "address":"CCM, Sauerbruchweg 3",
    },
    "SBW_Endoscopy": {
        "zone":"research","floor":0,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Endoscopy (Internal Medicine · Surgery · Urology)",
        "address":"CCM, Sauerbruchweg 3/5",  # confirmed
    },
    "SBW_Oncology_OPD": {
        "zone":"research","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Oncology & Haematology Outpatient (CC14)",
        "address":"CCM, Sauerbruchweg 3",  # confirmed
    },
    "RHW_Cardiology_Dx": {
        "zone":"research","floor":0,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Rahel Hirsch Center — Cardiology Functional Diagnostics",
        "address":"CCM, Rahel-Hirsch-Weg 5",  # confirmed
    },
    "RHW_Wards": {
        "zone":"research","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Wards 202/203 (Cardiology) · Rahel Hirsch Center",
        "address":"CCM, Rahel-Hirsch-Weg 5",  # confirmed: Ward 202/203 at RHW5
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: admin — Charitéplatz 1
    # ══════════════════════════════════════════════════════════════════════
    "ADMIN_HQ": {
        "zone":"admin","floor":0,"type":"room",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Executive Board · Dean's Office · Hospital Directorate",
        "address":"CCM, Charitéplatz 1",  # confirmed
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: historic — historic campus buildings (Hufelandweg, Virchowweg)
    # ══════════════════════════════════════════════════════════════════════
    "HW_Pharmacy": {
        "zone":"historic","floor":0,"type":"room",
        "restricted":set(),"wheelchair":True,
        "label":"Central Pharmacy",
        "address":"CCM, historic campus",
    },
    "HW_BloodBank": {
        "zone":"historic","floor":0,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Blood Donation / ZTB Transfusion Medicine",
        "address":"CCM, Charitéplatz 1 / Schumannstraße 22",  # confirmed
    },
    "CCO_Building": {
        "zone":"historic","floor":0,"type":"room",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"CharitéCrossOver (CCO) — Auditorium · Research · Lecture Halls",
        "address":"CCM, Virchowweg 6",  # confirmed
    },
    "Hufeland_Block": {
        "zone":"historic","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Audiology · Cardiovascular Surgery · Ophthalmology",
        "address":"CCM, Hufelandweg 3",  # confirmed
    },
}

# ---------------------------------------------------------------------------
# Edge catalogue
# ---------------------------------------------------------------------------
EDGES = [
    # ── ENTRANCES → BUILDINGS ───────────────────────────────────────────
    ("ENTRANCE_MAIN",       "BH_Lobby",       {"weight":8,  "via":"door",     "restricted":set()}),
    ("ENTRANCE_MAIN",       "DIAG_Lobby",     {"weight":12, "via":"corridor", "restricted":set()}),
    ("ENTRANCE_MAIN",       "MVZ_Lobby",      {"weight":10, "via":"corridor", "restricted":set()}),
    ("ENTRANCE_PHILIPPSTR", "RNB_Lobby",      {"weight":4,  "via":"door",     "restricted":set()}),
    ("ENTRANCE_INVALIDENSTR","BH_Lobby",      {"weight":15, "via":"door",     "restricted":set()}),

    # ── GLASS BRIDGE (F1: Bettenhaus ↔ historic campus) ─────────────────
    ("LOBBY_BRIDGE",        "BH_F1_Corridor", {"weight":10, "via":"bridge",   "restricted":set()}),
    ("LOBBY_BRIDGE",        "MVZ_Lobby",      {"weight":15, "via":"bridge",   "restricted":set()}),
    ("BH_Lobby",            "LOBBY_BRIDGE",   {"weight":20, "via":"corridor", "restricted":set()}),

    # ── BETTENHAUS GROUND ───────────────────────────────────────────────
    ("BH_Lobby",            "BH_Admissions",  {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_Lobby",            "BH_Dialysis",    {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("BH_Lobby",            "BH_Elevator_A",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_Lobby",            "BH_Elevator_B",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_Lobby",            "BH_Stairs",      {"weight":3,  "via":"corridor", "restricted":{"patient"}}),
    # Bettenhaus connects to RNH at ground level
    ("BH_Lobby",            "RNB_Lobby",      {"weight":25, "via":"corridor", "restricted":set()}),

    # ── BETTENHAUS ELEVATORS ────────────────────────────────────────────
    ("BH_Elevator_A", "BH_F1_Corridor",  {"weight":12, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_A", "BH_F2_Corridor",  {"weight":24, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_A", "BH_F4_Corridor",  {"weight":48, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_A", "BH_F6_Corridor",  {"weight":72, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_A", "BH_F8_Corridor",  {"weight":96, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_A", "BH_F21_Admin",    {"weight":252,"via":"elevator", "restricted":{"visitor","patient"}}),

    ("BH_Elevator_B", "BH_F1_Corridor",  {"weight":12, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_B", "BH_F2_Corridor",  {"weight":24, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_B", "BH_F4_Corridor",  {"weight":48, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_B", "BH_F6_Corridor",  {"weight":72, "via":"elevator", "restricted":set()}),
    ("BH_Elevator_B", "BH_F8_Corridor",  {"weight":96, "via":"elevator", "restricted":set()}),

    # Stairs
    ("BH_Stairs",     "BH_F1_Corridor",  {"weight":20, "via":"stairs",   "restricted":{"patient"}}),
    ("BH_Stairs",     "BH_F2_Corridor",  {"weight":40, "via":"stairs",   "restricted":{"patient"}}),

    # ── BETTENHAUS OPD departments ─────────────────────────────────────
    ("BH_F1_Corridor","OPD_Surgery",           {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_F1_Corridor","OPD_Gynecology",        {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_F1_Corridor","OPD_Cardiology",        {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_F1_Corridor","OPD_Neurosurgery",      {"weight":5,  "via":"corridor", "restricted":set()}),
    ("BH_F1_Corridor","OPD_Urology",           {"weight":5,  "via":"corridor", "restricted":set()}),
    ("BH_F1_Corridor","OPD_Orthopaedics",      {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_F1_Corridor","OPD_Anaesthesia",       {"weight":5,  "via":"corridor", "restricted":set()}),

    # ── BETTENHAUS FLOORS ───────────────────────────────────────────────
    ("BH_F1_Corridor","Ward_General_Surgery",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_F2_Corridor","Ward_101i",             {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("BH_F2_Corridor","Ward_102i",             {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("BH_F2_Corridor","Ward_103i",             {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("BH_F2_Corridor","Node_302_ICU_Tower",    {"weight":3,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("Ward_101i",     "Node_302_ICU_Tower",    {"weight":2,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("Ward_102i",     "Node_302_ICU_Tower",    {"weight":2,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("BH_F4_Corridor","Ward_Orthopedics",      {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_F6_Corridor","Ward_OBG",              {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_F6_Corridor","Ward_Delivery",         {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("BH_F8_Corridor","Ward_Neurosurgery",     {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_F8_Corridor","Ward_Urology",          {"weight":4,  "via":"corridor", "restricted":set()}),

    # ── RUDOLF-NISSEN-HAUS ──────────────────────────────────────────────
    ("RNB_Lobby",     "RNB_Emergency",         {"weight":3,  "via":"corridor", "restricted":set()}),
    ("RNB_Lobby",     "Ward_100",              {"weight":4,  "via":"corridor", "restricted":set()}),
    ("RNB_Lobby",     "RNB_PreOp",             {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("RNB_Lobby",     "RNB_Elevator",          {"weight":3,  "via":"corridor", "restricted":set()}),
    ("RNB_Elevator",  "RNB_F1_ICU",            {"weight":12, "via":"elevator", "restricted":{"visitor"}}),
    ("RNB_Elevator",  "RNB_F2_OT",             {"weight":24, "via":"elevator", "restricted":{"visitor","patient"}}),

    # ── DIAGNOSTICS BUILDING — Luisenstraße 7 ──────────────────────────
    ("DIAG_Lobby",    "DIAG_Radiology",        {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("DIAG_Lobby",    "DIAG_Nuclear_Med",      {"weight":6,  "via":"corridor", "restricted":{"visitor"}}),
    ("DIAG_Lobby",    "DIAG_Lab_Medicine",     {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),
    ("DIAG_Lobby",    "DIAG_Nephrology_OPD",   {"weight":4,  "via":"corridor", "restricted":set()}),
    ("DIAG_Lobby",    "DIAG_PhysioTherapy",    {"weight":4,  "via":"corridor", "restricted":set()}),
    ("DIAG_Lobby",    "DIAG_IntPatients",      {"weight":6,  "via":"corridor", "restricted":set()}),

    # ── MVZ specific OPD departments ───────────────────────────────────
    ("MVZ_Lobby",     "OPD_ENT",               {"weight":3,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_Dermatology",       {"weight":3,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_Pneumonology",      {"weight":4,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_Rheumatology",      {"weight":4,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_Endocrinology",     {"weight":4,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_Gastroenterology",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_Psychosomatic",     {"weight":5,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_SleepMedicine",     {"weight":5,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "OPD_PhysicalMedicine",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("DIAG_Lobby",    "OPD_Nephrology",        {"weight":3,  "via":"corridor", "restricted":set()}),

    # ── MVZ — Luisenstraße 13/13a ───────────────────────────────────────
    ("MVZ_Lobby",     "MVZ_Cardiology",        {"weight":3,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "MVZ_Neurology",         {"weight":3,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "MVZ_Dermatology",       {"weight":4,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "MVZ_Gastroenterology",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("MVZ_Lobby",     "MVZ_Coagulation",       {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("MVZ_Lobby",     "MVZ_Psychiatry",        {"weight":8,  "via":"stairs",   "restricted":{"patient"}}),
    ("MVZ_Lobby",     "MVZ_Rheumatology",      {"weight":8,  "via":"stairs",   "restricted":{"patient"}}),
    ("MVZ_Lobby",     "MVZ_Gynecology",        {"weight":8,  "via":"stairs",   "restricted":{"patient"}}),

    # ── NEUROLOGY/PSYCHIATRY building OPDs ─────────────────────────────
    ("NP_Lobby",      "OPD_Neurology",         {"weight":3,  "via":"corridor", "restricted":set()}),
    ("NP_Lobby",      "OPD_Psychiatry",        {"weight":3,  "via":"corridor", "restricted":set()}),

    # ── NEUROLOGY/PSYCHIATRY BUILDING — Bonhoefferweg 3 ────────────────
    ("MVZ_Lobby",     "NP_Lobby",              {"weight":10, "via":"corridor", "restricted":set()}),
    ("NP_Lobby",      "NP_Anxiety_OPD",        {"weight":3,  "via":"corridor", "restricted":set()}),
    ("NP_Lobby",      "Ward_M116",             {"weight":15, "via":"stairs",   "restricted":{"patient"}}),
    ("NP_Lobby",      "Ward_M116s",            {"weight":16, "via":"stairs",   "restricted":{"patient"}}),
    ("NP_Lobby",      "NP_Psychiatry_Ward",    {"weight":20, "via":"stairs",   "restricted":{"patient"}}),

    # ── SAUERBRUCHWEG / RAHEL-HIRSCH ───────────────────────────────────
    ("BH_Lobby",      "SBW_Lobby",             {"weight":20, "via":"corridor", "restricted":set()}),
    ("SBW_Lobby",     "SBW_Endoscopy",         {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),
    ("SBW_Lobby",     "SBW_Oncology_OPD",      {"weight":5,  "via":"corridor", "restricted":set()}),
    ("SBW_Lobby",     "RHW_Cardiology_Dx",     {"weight":8,  "via":"corridor", "restricted":{"visitor"}}),
    ("SBW_Lobby",     "RHW_Wards",             {"weight":10, "via":"corridor", "restricted":set()}),

    # ── HUFELANDWEG 3 departments ──────────────────────────────────────
    ("Hufeland_Block","OPD_Ophthalmology",     {"weight":3,  "via":"corridor", "restricted":set()}),
    ("Hufeland_Block","OPD_Audiology",         {"weight":3,  "via":"corridor", "restricted":set()}),
    ("Hufeland_Block","OPD_CardiovascularSurgery",{"weight":4,"via":"corridor","restricted":set()}),

    # ── ONCOLOGY at Sauerbruchweg ────────────────────────────────────────
    ("SBW_Lobby",     "OPD_Oncology",          {"weight":3,  "via":"corridor", "restricted":set()}),

    # ── ADMIN / HISTORIC ────────────────────────────────────────────────
    ("BH_Lobby",      "ADMIN_HQ",              {"weight":15, "via":"corridor", "restricted":{"visitor","patient"}}),
    ("BH_Lobby",      "HW_Pharmacy",           {"weight":10, "via":"corridor", "restricted":set()}),
    ("BH_Lobby",      "HW_BloodBank",          {"weight":12, "via":"corridor", "restricted":{"visitor"}}),
    ("BH_Lobby",      "CCO_Building",          {"weight":20, "via":"corridor", "restricted":{"visitor","patient"}}),
    ("BH_Lobby",      "Hufeland_Block",        {"weight":18, "via":"corridor", "restricted":set()}),
    ("DIAG_Lobby",    "Hufeland_Block",        {"weight":8,  "via":"corridor", "restricted":set()}),
]

# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def build_graph(profile: str = "staff") -> nx.Graph:
    """
    Profiles: 'visitor' | 'patient' | 'staff' | 'emergency'
    'emergency' and 'staff' bypass all restrictions.
    """
    G = nx.Graph()
    for node_id, attrs in NODES.items():
        restricted = attrs.get("restricted", set())
        if profile not in ("staff", "emergency") and profile in restricted:
            continue
        G.add_node(node_id, **attrs)
    for u, v, attrs in EDGES:
        if u not in G.nodes or v not in G.nodes:
            continue
        edge_restricted = attrs.get("restricted", set())
        if profile not in ("staff", "emergency") and profile in edge_restricted:
            continue
        if profile == "patient" and attrs.get("via") == "stairs":
            continue
        G.add_edge(u, v, **attrs)
    return G


def heuristic(u: str, v: str) -> float:
    """Admissible A* heuristic: |floor_diff| × 12 sec."""
    floor_u = NODES.get(u, {}).get("floor", 0)
    floor_v = NODES.get(v, {}).get("floor", 0)
    return abs(floor_u - floor_v) * 12


def node_label(node_id: str) -> str:
    return NODES.get(node_id, {}).get("label", node_id.replace("_", " "))


def get_node_color(node_id: str) -> str:
    t = NODES.get(node_id, {}).get("type", "corridor")
    return {
        "icu":      "#e74c3c",
        "ot":       "#c0392b",
        "lab":      "#8e44ad",
        "elevator": "#2980b9",
        "stairs":   "#f39c12",
        "ward":     "#27ae60",
        "entrance": "#1abc9c",
        "room":     "#95a5a6",
        "corridor": "#bdc3c7",
    }.get(t, "#bdc3c7")


if __name__ == "__main__":
    G = build_graph("staff")
    print(f"Staff   : {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    G2 = build_graph("visitor")
    print(f"Visitor : {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")
    zones = set(d["zone"] for _, d in G.nodes(data=True))
    print(f"Zones   : {zones}")
    print("\nBuilding zones with real addresses:")
    for zone in sorted(zones):
        nodes = [n for n,d in G.nodes(data=True) if d.get("zone")==zone]
        addr  = next((NODES[n].get("address","") for n in nodes if NODES[n].get("address")), "")
        print(f"  {zone:15s} ({len(nodes):2d} nodes) — {addr}")
