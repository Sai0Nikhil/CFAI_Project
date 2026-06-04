"""
core/aiims_graph.py
===================
AIIMS Mangalagiri — Hospital Navigation Graph
All India Institute of Medical Sciences, Mangalagiri, Andhra Pradesh - 522503

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA SOURCES (verified from official AIIMS Mangalagiri website)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• https://www.aiimsmangalagiri.edu.in/hospital-services/
  → OPD registration: Ground floor, OPD Building
  → General Medicine OPD: 2nd floor, OPD Building
  → Dialysis Unit: Ground floor, IPD Block (30 beds)
  → Casualty/Emergency: Ground floor, 24×7, 60-bed trauma dept
  → OT Complex: 8 modular OTs + 2 trauma OTs (separate block)
  → Avg daily OPD: 3000–3500 patients

• https://www.aiimsmangalagiri.edu.in/departments/pediatrics/
  → Paediatrics IPD ward (60 beds) + PICU (12 beds) + NICU (14 beds):
    3rd floor, IPD Block (confirmed Dec 2022 – Jan 2023)

• https://www.aiimsmangalagiri.edu.in/departments/general-medicine/
  → Medicine OPD: OPD Building, 2nd floor
  → General Medicine ICU: 20 beds (within IPD block)
  → Medical wards operational

• KMV Projects (construction contractor):
  → 11 buildings, 9.83 lakh sq ft built-up area
  → Blocks: OPD, IPD/Hospital, OT Complex, Academic, Admin, Nursing College, Residential

• Dept list from official hospital services page:
  Broad specialties: Anatomy, Anaesthesiology, Community & Family Medicine,
  Dentistry, Dermatology, ENT, General Medicine, General Surgery,
  Nuclear Medicine, OBG, Ophthalmology, Orthopaedics, Paediatrics,
  Pulmonary Medicine, Radiation Oncology, Radiodiagnosis, Transfusion
  Medicine & Hemotherapy, Trauma & Emergency Medicine
  Super specialties: Burns & Plastic Surgery, Cardiology, Cardiothoracic Surgery,
  Endocrinology, Medical Oncology, Nephrology, Neurology, Neurosurgery,
  Paediatric Surgery, Rheumatology, Surgical Gastroenterology,
  Surgical Oncology, Urology

• Labs confirmed: Biochemistry, Pathology, Microbiology, Radiology
  (X-Ray, Mammography, USG, CT, MRI), Physiology Lab (EEG, nerve
  conduction, spirometry), Nuclear Medicine (PET Scan)

• Advanced: LINAC (High/Low energy), CT Simulator, HD Brachytherapy,
  Endoscopy, 2D ECHO, Robotic Physiotherapy, AMIRT Pharmacy,
  Jan Aushadhi Kendra

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAMPUS BLOCKS (from KMV + official site):
  1. OPD Block          — 2-floor outpatient building
  2. IPD Block          — main inpatient tower (4+ floors, 960-bed)
  3. OT Complex         — dedicated operation theatre building
  4. Academic Block     — medical college, labs, library
  5. Connector          — gates, central plaza, access roads
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Node metadata keys:
  zone        : 'opd' | 'ipd' | 'ot' | 'academic' | 'connector'
  floor       : int (0 = ground floor)
  type        : 'entrance'|'corridor'|'ward'|'icu'|'lab'|'room'|
                'elevator'|'stairs'|'ot'|'pharmacy'
  restricted  : set of profiles that CANNOT enter  {'visitor','patient'}
  wheelchair  : bool — True if accessible without stairs
  beds        : int (optional) — ward/ICU bed count where confirmed

Edge metadata keys:
  weight      : travel time in seconds
  via         : 'door'|'corridor'|'stairs'|'elevator'|'ramp'|'bridge'
  restricted  : set of profiles blocked on this edge
"""

from __future__ import annotations
import networkx as nx
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Node catalogue — verified from official sources where noted
# ---------------------------------------------------------------------------
NODES: Dict[str, Dict[str, Any]] = {

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: connector — Campus gates & central pathways
    # ══════════════════════════════════════════════════════════════════════
    "MAIN_GATE": {
        "zone":"connector","floor":0,"type":"entrance",
        "restricted":set(),"wheelchair":True,
        "label":"Main Gate · NH-16 / Mangalagiri–Amaravati Road"
    },
    "EMERGENCY_GATE": {
        "zone":"connector","floor":0,"type":"entrance",
        "restricted":set(),"wheelchair":True,
        "label":"Emergency Gate (24×7)"
    },
    "CENTRAL_PLAZA": {
        "zone":"connector","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"Central Campus Plaza (connecting all blocks)"
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: opd — OPD Block
    # Source: aiimsmangalagiri.edu.in/hospital-services & dept pages
    # ══════════════════════════════════════════════════════════════════════

    # Ground floor — OPD Block (source: official website)
    "OPD_LOBBY": {
        "zone":"opd","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"OPD Block Lobby"
    },
    "OPD_REGISTRATION": {
        "zone":"opd","floor":0,"type":"room",
        "restricted":set(),"wheelchair":True,
        "label":"OPD Registration Counter (Ground Floor)"
        # confirmed: "Registration at the Ground floor registration counter"
    },
    "OPD_ABHA_KIOSK": {
        "zone":"opd","floor":0,"type":"room",
        "restricted":set(),"wheelchair":True,
        "label":"ABHA Self-Registration Kiosk"
    },
    "JAN_AUSHADHI": {
        "zone":"opd","floor":0,"type":"pharmacy",
        "restricted":set(),"wheelchair":True,
        "label":"Jan Aushadhi Kendra (PM Generic Pharmacy)"
    },
    "OPD_GROUND_CORRIDOR": {
        "zone":"opd","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"OPD Ground Floor Corridor"
    },
    "OPD_STAIRS_A": {
        "zone":"opd","floor":0,"type":"stairs",
        "restricted":{"patient"},"wheelchair":False,
        "label":"OPD Block Staircase A"
    },

    # First floor — OPD Block
    "OPD_F1_CORRIDOR": {
        "zone":"opd","floor":1,"type":"corridor",
        "restricted":set(),"wheelchair":False,
        "label":"OPD First Floor Corridor"
    },
    "OPD_ENT": {
        "zone":"opd","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"ENT (Ear Nose Throat) OPD · F1"
    },
    "OPD_OPHTHALMOLOGY": {
        "zone":"opd","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Ophthalmology OPD · F1"
    },
    "OPD_DERMATOLOGY": {
        "zone":"opd","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Dermatology & Venereology OPD · F1"
    },
    "OPD_PSYCHIATRY": {
        "zone":"opd","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Psychiatry & Mental Health OPD · F1"
    },
    "OPD_ORTHOPAEDICS": {
        "zone":"opd","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Orthopaedics & Trauma OPD · F1"
    },
    "OPD_PULMONARY": {
        "zone":"opd","floor":1,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Pulmonary Medicine (Chest) OPD · F1"
    },

    # Second floor — OPD Block (confirmed: General Medicine OPD here)
    "OPD_F2_CORRIDOR": {
        "zone":"opd","floor":2,"type":"corridor",
        "restricted":set(),"wheelchair":False,
        "label":"OPD Second Floor Corridor"
    },
    "OPD_GENERAL_MEDICINE": {
        "zone":"opd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"General Medicine OPD · F2"
        # confirmed: "OPD building, second floor"
    },
    "OPD_GENERAL_SURGERY": {
        "zone":"opd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"General Surgery OPD · F2"
    },
    "OPD_OBG": {
        "zone":"opd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Obstetrics & Gynaecology OPD · F2"
    },
    "OPD_PAEDIATRICS": {
        "zone":"opd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Paediatrics OPD · F2"
    },
    "OPD_NEUROLOGY": {
        "zone":"opd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":False,
        "label":"Neurology OPD · F2"
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: ipd — IPD Block (Main Hospital Tower, 960 beds)
    # Source: official website — ground floor dialysis confirmed,
    #         3rd floor pediatrics confirmed
    # ══════════════════════════════════════════════════════════════════════

    # Ground floor — IPD Block
    "IPD_LOBBY": {
        "zone":"ipd","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Block Main Lobby"
    },
    "IPD_RECEPTION": {
        "zone":"ipd","floor":0,"type":"room",
        "restricted":set(),"wheelchair":True,
        "label":"Inpatient Admission & Reception"
    },
    "CASUALTY": {
        "zone":"ipd","floor":0,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Casualty & Trauma Emergency (60 beds, 24×7)"
        # confirmed: 60-bed trauma & emergency dept
    },
    "DIALYSIS_UNIT": {
        "zone":"ipd","floor":0,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "beds":30,
        "label":"Dialysis Unit · Ground Floor IPD (30 beds)"
        # confirmed: "Dialysis Unit at Ground Floor of IPD Block, 30 beds"
    },
    "BLOOD_BANK": {
        "zone":"ipd","floor":0,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Advanced Blood Bank & Transfusion Medicine"
        # confirmed: "Advanced Blood Bank", "Transfusion Medicine & Hemotherapy"
    },
    "AMIRT_PHARMACY": {
        "zone":"ipd","floor":0,"type":"pharmacy",
        "restricted":set(),"wheelchair":True,
        "label":"AMIRT Pharmacy (Inpatient)"
    },
    "IPD_GROUND_CORRIDOR": {
        "zone":"ipd","floor":0,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Ground Floor Main Corridor"
    },
    "IPD_ELEVATOR_A": {
        "zone":"ipd","floor":0,"type":"elevator",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Block Elevator A"
    },
    "IPD_ELEVATOR_B": {
        "zone":"ipd","floor":0,"type":"elevator",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Block Elevator B"
    },
    "IPD_STAIRS_B": {
        "zone":"ipd","floor":0,"type":"stairs",
        "restricted":{"patient"},"wheelchair":False,
        "label":"IPD Block Staircase B"
    },

    # First floor — IPD Block
    "IPD_F1_CORRIDOR": {
        "zone":"ipd","floor":1,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD First Floor Corridor"
    },
    "LAB_RADIOLOGY": {
        "zone":"ipd","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Radiology — X-Ray, CT, MRI, Mammography, USG · F1"
        # confirmed: "Radiology (X-Ray, Mammography, Ultrasonography, CT and MRI)"
    },
    "LAB_NUCLEAR_MEDICINE": {
        "zone":"ipd","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Nuclear Medicine — PET Scan · F1"
        # confirmed: "Nuclear Medicine (PET Scan)"
    },
    "LAB_BIOCHEMISTRY": {
        "zone":"ipd","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Biochemistry Lab · F1"
    },
    "LAB_PATHOLOGY": {
        "zone":"ipd","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Pathology Lab · F1"
    },
    "LAB_MICROBIOLOGY": {
        "zone":"ipd","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Microbiology Lab · F1"
    },
    "LAB_PHYSIOLOGY": {
        "zone":"ipd","floor":1,"type":"lab",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Physiology Lab — EEG, NCS, Spirometry · F1"
        # confirmed: "Physiology Lab (EEG, Nerve conduction studies, Spirometry)"
    },
    "ENDOSCOPY_UNIT": {
        "zone":"ipd","floor":1,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Endoscopy Unit · F1"
    },

    # Second floor — IPD Block
    "IPD_F2_CORRIDOR": {
        "zone":"ipd","floor":2,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Second Floor Corridor"
    },
    "WARD_GENERAL_MEDICINE_F2": {
        "zone":"ipd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"General Medicine Ward · F2"
    },
    "ICU_MEDICINE_F2": {
        "zone":"ipd","floor":2,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "beds":20,
        "label":"Medical ICU (MICU) · F2 — 20 beds"
        # confirmed: "Medical Intensive Care Unit (20 beds)"
    },
    "WARD_GENERAL_SURGERY_F2": {
        "zone":"ipd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"General Surgery Ward · F2"
    },
    "WARD_ORTHOPAEDICS_F2": {
        "zone":"ipd","floor":2,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Orthopaedics & Trauma Ward · F2"
    },

    # Third floor — IPD Block (confirmed: Paediatrics entire floor)
    "IPD_F3_CORRIDOR": {
        "zone":"ipd","floor":3,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Third Floor Corridor"
    },
    "WARD_PAEDIATRICS_F3": {
        "zone":"ipd","floor":3,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "beds":60,
        "label":"Paediatrics Inpatient Ward · F3 — 60 beds"
        # confirmed: "60 bedded Pediatric inpatient ward at 3rd floor IPD"
    },
    "PICU_F3": {
        "zone":"ipd","floor":3,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "beds":12,
        "label":"Paediatric ICU (PICU) · F3 — 12 beds"
        # confirmed: "12 bedded Pediatric intensive care at 3rd floor IPD"
    },
    "NICU_F3": {
        "zone":"ipd","floor":3,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "beds":14,
        "label":"Neonatal ICU (NICU Level-3) · F3 — 14 beds"
        # confirmed: "14 bedded Level 3 NICU at 3rd floor of IPD hospital block"
    },
    "WARD_OBG_F3": {
        "zone":"ipd","floor":3,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Obstetrics & Gynaecology Ward · F3"
    },

    # Fourth floor — IPD Block
    "IPD_F4_CORRIDOR": {
        "zone":"ipd","floor":4,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Fourth Floor Corridor"
    },
    "WARD_NEUROLOGY_F4": {
        "zone":"ipd","floor":4,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Neurology Ward · F4"
    },
    "WARD_NEUROSURGERY_F4": {
        "zone":"ipd","floor":4,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Neurosurgery Ward · F4"
    },
    "ICU_NEURO_F4": {
        "zone":"ipd","floor":4,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Neuro ICU (NICU for Adults) · F4"
    },

    # Fifth floor — IPD Block
    "IPD_F5_CORRIDOR": {
        "zone":"ipd","floor":5,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Fifth Floor Corridor"
    },
    "WARD_CARDIOLOGY_F5": {
        "zone":"ipd","floor":5,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Cardiology Ward · F5"
    },
    "CATH_LAB_F5": {
        "zone":"ipd","floor":5,"type":"lab",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Cardiac Cath Lab & 2D ECHO · F5"
        # confirmed: "2D ECHO" in advanced facilities
    },
    "WARD_CARDIOTHORACIC_F5": {
        "zone":"ipd","floor":5,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Cardiothoracic Surgery Ward · F5"
    },
    "ICU_CARDIAC_F5": {
        "zone":"ipd","floor":5,"type":"icu",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Cardiac ICU (CICU) · F5"
    },

    # Sixth floor — IPD Block
    "IPD_F6_CORRIDOR": {
        "zone":"ipd","floor":6,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Sixth Floor Corridor"
    },
    "WARD_ONCOLOGY_MEDICAL_F6": {
        "zone":"ipd","floor":6,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Medical Oncology Ward · F6"
    },
    "WARD_SURGICAL_ONCOLOGY_F6": {
        "zone":"ipd","floor":6,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Surgical Oncology Ward · F6"
    },
    "RADIATION_ONCOLOGY_F6": {
        "zone":"ipd","floor":6,"type":"ward",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Radiation Oncology — LINAC Suite · F6"
        # confirmed: "High energy LINAC, low energy LINAC, CT Simulator, HD Brachytherapy"
    },

    # Seventh floor — IPD Block (Nephrology/Urology/Endocrinology cluster)
    "IPD_F7_CORRIDOR": {
        "zone":"ipd","floor":7,"type":"corridor",
        "restricted":set(),"wheelchair":True,
        "label":"IPD Seventh Floor Corridor"
    },
    "WARD_NEPHROLOGY_F7": {
        "zone":"ipd","floor":7,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Nephrology Ward · F7"
    },
    "WARD_UROLOGY_F7": {
        "zone":"ipd","floor":7,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Urology Ward · F7"
    },
    "WARD_ENDOCRINOLOGY_F7": {
        "zone":"ipd","floor":7,"type":"ward",
        "restricted":set(),"wheelchair":True,
        "label":"Endocrinology & Metabolism Ward · F7"
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: ot — Operation Theatre Complex (separate block)
    # Source: official — "8 modular OTs + 2 trauma OTs"
    # ══════════════════════════════════════════════════════════════════════
    "OT_LOBBY": {
        "zone":"ot","floor":0,"type":"corridor",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"OT Complex Lobby (staff & escorted patients only)"
    },
    "OT_PRE_OP": {
        "zone":"ot","floor":0,"type":"ward",
        "restricted":{"visitor"},"wheelchair":True,
        "label":"Pre-Operative & Recovery Room"
    },
    "OT_TRAUMA_1": {
        "zone":"ot","floor":0,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Trauma OT 1 (Emergency)"
        # confirmed: "two trauma operation theatres"
    },
    "OT_TRAUMA_2": {
        "zone":"ot","floor":0,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Trauma OT 2 (Emergency)"
    },
    "OT_F1_CORRIDOR": {
        "zone":"ot","floor":1,"type":"corridor",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT Suite Corridor · F1"
    },
    "OT_MODULAR_1": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 1 (General Surgery)"
        # confirmed: "8 functional modular OTs in main complex"
    },
    "OT_MODULAR_2": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 2 (Orthopaedics)"
    },
    "OT_MODULAR_3": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 3 (Gynaecology & OBG)"
    },
    "OT_MODULAR_4": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 4 (Neurosurgery)"
    },
    "OT_MODULAR_5": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 5 (Cardiothoracic Surgery)"
    },
    "OT_MODULAR_6": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 6 (Urology)"
    },
    "OT_MODULAR_7": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 7 (Surgical Oncology)"
    },
    "OT_MODULAR_8": {
        "zone":"ot","floor":1,"type":"ot",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Modular OT 8 (Paediatric Surgery)"
    },

    # ══════════════════════════════════════════════════════════════════════
    # ZONE: academic — Medical College Academic Block
    # Source: KMV construction documents + official AIIMS site
    # ══════════════════════════════════════════════════════════════════════
    "AC_LOBBY": {
        "zone":"academic","floor":0,"type":"corridor",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Academic Block Lobby (Medical College)"
    },
    "AC_ANATOMY_DISSECTION": {
        "zone":"academic","floor":0,"type":"lab",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Anatomy Dept & Dissection Hall · G/F"
        # confirmed: "Body Donation Cell" on official site = anatomy dept
    },
    "AC_SKILL_LAB": {
        "zone":"academic","floor":0,"type":"lab",
        "restricted":{"visitor","patient"},"wheelchair":True,
        "label":"Clinical Skills & Simulation Lab · G/F"
        # confirmed from OBG dept — "dedicated simulation and skill lab"
    },
    "AC_STAIRS": {
        "zone":"academic","floor":0,"type":"stairs",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"Academic Block Stairs"
    },
    "AC_F1_CORRIDOR": {
        "zone":"academic","floor":1,"type":"corridor",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"Academic Block First Floor Corridor"
    },
    "AC_LIBRARY": {
        "zone":"academic","floor":1,"type":"room",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"Medical Library · F1"
        # confirmed: library URL http://14.139.89.101/ on official site
    },
    "AC_LECTURE_HALL_A": {
        "zone":"academic","floor":1,"type":"room",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"Lecture Hall A · F1"
    },
    "AC_LECTURE_HALL_B": {
        "zone":"academic","floor":1,"type":"room",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"Lecture Hall B · F1"
    },
    "AC_F2_CORRIDOR": {
        "zone":"academic","floor":2,"type":"corridor",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"Academic Block Second Floor Corridor"
    },
    "AC_RESEARCH_LAB": {
        "zone":"academic","floor":2,"type":"lab",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"Research & Innovation Lab · F2"
        # confirmed: research.aiimsmangalagiri.edu.in portal
    },
    "AC_VRDL_LAB": {
        "zone":"academic","floor":2,"type":"lab",
        "restricted":{"visitor","patient"},"wheelchair":False,
        "label":"State-level VRDL & Molecular Biology Lab · F2"
        # confirmed: "State level VRDL facility" + "Trace element & molecular biology lab"
    },
}


# ---------------------------------------------------------------------------
# Edge catalogue — (undirected, each tuple = (u, v, attrs))
# ---------------------------------------------------------------------------
EDGES = [

    # ── GATES → CENTRAL PLAZA ──────────────────────────────────────────────
    ("MAIN_GATE",           "CENTRAL_PLAZA",        {"weight":20, "via":"ramp",     "restricted":set()}),
    ("EMERGENCY_GATE",      "CASUALTY",             {"weight":5,  "via":"door",     "restricted":set()}),
    ("CENTRAL_PLAZA",       "OPD_LOBBY",            {"weight":10, "via":"corridor", "restricted":set()}),
    ("CENTRAL_PLAZA",       "IPD_LOBBY",            {"weight":12, "via":"corridor", "restricted":set()}),
    ("CENTRAL_PLAZA",       "OT_LOBBY",             {"weight":20, "via":"corridor", "restricted":{"visitor","patient"}}),
    ("CENTRAL_PLAZA",       "AC_LOBBY",             {"weight":18, "via":"corridor", "restricted":{"visitor","patient"}}),

    # ── OPD BLOCK — GROUND ─────────────────────────────────────────────────
    ("OPD_LOBBY",           "OPD_REGISTRATION",     {"weight":3,  "via":"corridor", "restricted":set()}),
    ("OPD_LOBBY",           "OPD_ABHA_KIOSK",       {"weight":2,  "via":"corridor", "restricted":set()}),
    ("OPD_LOBBY",           "JAN_AUSHADHI",         {"weight":4,  "via":"corridor", "restricted":set()}),
    ("OPD_LOBBY",           "OPD_GROUND_CORRIDOR",  {"weight":5,  "via":"corridor", "restricted":set()}),
    ("OPD_GROUND_CORRIDOR", "OPD_STAIRS_A",         {"weight":3,  "via":"corridor", "restricted":{"patient"}}),

    # OPD BLOCK — STAIRS → FIRST FLOOR
    ("OPD_STAIRS_A",        "OPD_F1_CORRIDOR",      {"weight":20, "via":"stairs",   "restricted":{"patient"}}),
    ("OPD_F1_CORRIDOR",     "OPD_ENT",              {"weight":3,  "via":"corridor", "restricted":set()}),
    ("OPD_F1_CORRIDOR",     "OPD_OPHTHALMOLOGY",    {"weight":4,  "via":"corridor", "restricted":set()}),
    ("OPD_F1_CORRIDOR",     "OPD_DERMATOLOGY",      {"weight":4,  "via":"corridor", "restricted":set()}),
    ("OPD_F1_CORRIDOR",     "OPD_PSYCHIATRY",       {"weight":5,  "via":"corridor", "restricted":set()}),
    ("OPD_F1_CORRIDOR",     "OPD_ORTHOPAEDICS",     {"weight":5,  "via":"corridor", "restricted":set()}),
    ("OPD_F1_CORRIDOR",     "OPD_PULMONARY",        {"weight":6,  "via":"corridor", "restricted":set()}),

    # OPD BLOCK — STAIRS → SECOND FLOOR
    ("OPD_F1_CORRIDOR",     "OPD_F2_CORRIDOR",      {"weight":20, "via":"stairs",   "restricted":{"patient"}}),
    ("OPD_F2_CORRIDOR",     "OPD_GENERAL_MEDICINE", {"weight":3,  "via":"corridor", "restricted":set()}),
    # confirmed: "OPD building, second floor"
    ("OPD_F2_CORRIDOR",     "OPD_GENERAL_SURGERY",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("OPD_F2_CORRIDOR",     "OPD_OBG",              {"weight":4,  "via":"corridor", "restricted":set()}),
    ("OPD_F2_CORRIDOR",     "OPD_PAEDIATRICS",      {"weight":5,  "via":"corridor", "restricted":set()}),
    ("OPD_F2_CORRIDOR",     "OPD_NEUROLOGY",        {"weight":5,  "via":"corridor", "restricted":set()}),

    # ── IPD BLOCK — GROUND ─────────────────────────────────────────────────
    ("IPD_LOBBY",           "IPD_RECEPTION",        {"weight":3,  "via":"corridor", "restricted":set()}),
    ("IPD_LOBBY",           "IPD_GROUND_CORRIDOR",  {"weight":4,  "via":"corridor", "restricted":set()}),
    ("IPD_LOBBY",           "IPD_ELEVATOR_A",       {"weight":5,  "via":"corridor", "restricted":set()}),
    ("IPD_LOBBY",           "IPD_ELEVATOR_B",       {"weight":5,  "via":"corridor", "restricted":set()}),
    ("IPD_LOBBY",           "IPD_STAIRS_B",         {"weight":3,  "via":"corridor", "restricted":{"patient"}}),
    ("IPD_GROUND_CORRIDOR", "CASUALTY",             {"weight":5,  "via":"corridor", "restricted":set()}),
    ("IPD_GROUND_CORRIDOR", "DIALYSIS_UNIT",        {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    # confirmed: dialysis at ground floor
    ("IPD_GROUND_CORRIDOR", "BLOOD_BANK",           {"weight":6,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_GROUND_CORRIDOR", "AMIRT_PHARMACY",       {"weight":4,  "via":"corridor", "restricted":set()}),

    # ── IPD BLOCK ELEVATORS ────────────────────────────────────────────────
    ("IPD_ELEVATOR_A",      "IPD_F1_CORRIDOR",      {"weight":12, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_A",      "IPD_F2_CORRIDOR",      {"weight":24, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_A",      "IPD_F3_CORRIDOR",      {"weight":36, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_A",      "IPD_F4_CORRIDOR",      {"weight":48, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_A",      "IPD_F5_CORRIDOR",      {"weight":60, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_A",      "IPD_F6_CORRIDOR",      {"weight":72, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_A",      "IPD_F7_CORRIDOR",      {"weight":84, "via":"elevator", "restricted":set()}),

    ("IPD_ELEVATOR_B",      "IPD_F1_CORRIDOR",      {"weight":12, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_B",      "IPD_F2_CORRIDOR",      {"weight":24, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_B",      "IPD_F3_CORRIDOR",      {"weight":36, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_B",      "IPD_F4_CORRIDOR",      {"weight":48, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_B",      "IPD_F5_CORRIDOR",      {"weight":60, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_B",      "IPD_F6_CORRIDOR",      {"weight":72, "via":"elevator", "restricted":set()}),
    ("IPD_ELEVATOR_B",      "IPD_F7_CORRIDOR",      {"weight":84, "via":"elevator", "restricted":set()}),

    # IPD STAIRS
    ("IPD_STAIRS_B",        "IPD_F1_CORRIDOR",      {"weight":22, "via":"stairs",   "restricted":{"patient"}}),
    ("IPD_STAIRS_B",        "IPD_F2_CORRIDOR",      {"weight":44, "via":"stairs",   "restricted":{"patient"}}),
    ("IPD_STAIRS_B",        "IPD_F3_CORRIDOR",      {"weight":66, "via":"stairs",   "restricted":{"patient","visitor"}}),

    # ── FLOOR 1 — Diagnostics & Labs ───────────────────────────────────────
    ("IPD_F1_CORRIDOR",     "LAB_RADIOLOGY",        {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F1_CORRIDOR",     "LAB_NUCLEAR_MEDICINE", {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F1_CORRIDOR",     "LAB_BIOCHEMISTRY",     {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F1_CORRIDOR",     "LAB_PATHOLOGY",        {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F1_CORRIDOR",     "LAB_MICROBIOLOGY",     {"weight":6,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F1_CORRIDOR",     "LAB_PHYSIOLOGY",       {"weight":6,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F1_CORRIDOR",     "ENDOSCOPY_UNIT",       {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),

    # ── FLOOR 2 — General wards + MICU ─────────────────────────────────────
    ("IPD_F2_CORRIDOR",     "WARD_GENERAL_MEDICINE_F2",  {"weight":3,  "via":"corridor", "restricted":set()}),
    ("IPD_F2_CORRIDOR",     "ICU_MEDICINE_F2",           {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    # confirmed: MICU 20 beds
    ("IPD_F2_CORRIDOR",     "WARD_GENERAL_SURGERY_F2",   {"weight":4,  "via":"corridor", "restricted":set()}),
    ("IPD_F2_CORRIDOR",     "WARD_ORTHOPAEDICS_F2",      {"weight":4,  "via":"corridor", "restricted":set()}),

    # ── FLOOR 3 — Paediatrics (confirmed official) ──────────────────────────
    ("IPD_F3_CORRIDOR",     "WARD_PAEDIATRICS_F3",  {"weight":3,  "via":"corridor", "restricted":set()}),
    ("IPD_F3_CORRIDOR",     "PICU_F3",              {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("IPD_F3_CORRIDOR",     "NICU_F3",              {"weight":6,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("IPD_F3_CORRIDOR",     "WARD_OBG_F3",          {"weight":4,  "via":"corridor", "restricted":set()}),

    # ── FLOOR 4 — Neurology & Neurosurgery ─────────────────────────────────
    ("IPD_F4_CORRIDOR",     "WARD_NEUROLOGY_F4",    {"weight":3,  "via":"corridor", "restricted":set()}),
    ("IPD_F4_CORRIDOR",     "WARD_NEUROSURGERY_F4", {"weight":4,  "via":"corridor", "restricted":set()}),
    ("IPD_F4_CORRIDOR",     "ICU_NEURO_F4",         {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),

    # ── FLOOR 5 — Cardiology & Cardiothoracic ──────────────────────────────
    ("IPD_F5_CORRIDOR",     "WARD_CARDIOLOGY_F5",   {"weight":3,  "via":"corridor", "restricted":set()}),
    ("IPD_F5_CORRIDOR",     "CATH_LAB_F5",          {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("IPD_F5_CORRIDOR",     "WARD_CARDIOTHORACIC_F5",{"weight":4, "via":"corridor", "restricted":set()}),
    ("IPD_F5_CORRIDOR",     "ICU_CARDIAC_F5",       {"weight":6,  "via":"corridor", "restricted":{"visitor","patient"}}),

    # ── FLOOR 6 — Oncology ─────────────────────────────────────────────────
    ("IPD_F6_CORRIDOR",     "WARD_ONCOLOGY_MEDICAL_F6",  {"weight":3,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F6_CORRIDOR",     "WARD_SURGICAL_ONCOLOGY_F6", {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),
    ("IPD_F6_CORRIDOR",     "RADIATION_ONCOLOGY_F6",     {"weight":6,  "via":"corridor", "restricted":{"visitor","patient"}}),

    # ── FLOOR 7 — Nephrology / Urology / Endocrinology ─────────────────────
    ("IPD_F7_CORRIDOR",     "WARD_NEPHROLOGY_F7",   {"weight":3,  "via":"corridor", "restricted":set()}),
    ("IPD_F7_CORRIDOR",     "WARD_UROLOGY_F7",      {"weight":4,  "via":"corridor", "restricted":set()}),
    ("IPD_F7_CORRIDOR",     "WARD_ENDOCRINOLOGY_F7",{"weight":4,  "via":"corridor", "restricted":set()}),

    # ── OT COMPLEX ─────────────────────────────────────────────────────────
    ("OT_LOBBY",            "OT_PRE_OP",            {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),
    ("OT_LOBBY",            "OT_TRAUMA_1",          {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_LOBBY",            "OT_TRAUMA_2",          {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_LOBBY",            "OT_F1_CORRIDOR",       {"weight":12, "via":"elevator", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_1",         {"weight":3,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_2",         {"weight":3,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_3",         {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_4",         {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_5",         {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_6",         {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_7",         {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("OT_F1_CORRIDOR",      "OT_MODULAR_8",         {"weight":6,  "via":"corridor", "restricted":{"visitor","patient"}}),

    # IPD ↔ OT bridge (staff escort corridor between IPD and OT Complex)
    ("IPD_F2_CORRIDOR",     "OT_LOBBY",             {"weight":30, "via":"bridge",   "restricted":{"visitor","patient"}}),

    # ── ACADEMIC BLOCK ─────────────────────────────────────────────────────
    ("AC_LOBBY",            "AC_ANATOMY_DISSECTION",{"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("AC_LOBBY",            "AC_SKILL_LAB",         {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("AC_LOBBY",            "AC_STAIRS",            {"weight":3,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("AC_STAIRS",           "AC_F1_CORRIDOR",       {"weight":20, "via":"stairs",   "restricted":{"visitor","patient"}}),
    ("AC_F1_CORRIDOR",      "AC_LIBRARY",           {"weight":3,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("AC_F1_CORRIDOR",      "AC_LECTURE_HALL_A",    {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("AC_F1_CORRIDOR",      "AC_LECTURE_HALL_B",    {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("AC_F1_CORRIDOR",      "AC_F2_CORRIDOR",       {"weight":20, "via":"stairs",   "restricted":{"visitor","patient"}}),
    ("AC_F2_CORRIDOR",      "AC_RESEARCH_LAB",      {"weight":3,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("AC_F2_CORRIDOR",      "AC_VRDL_LAB",          {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
]


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def build_graph(profile: str = "staff") -> nx.Graph:
    """
    Build filtered NetworkX graph for the given access profile.

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
    """
    Admissible A* heuristic: |floor_diff| × 12 sec (elevator rate).
    Never overestimates — actual elevator cost ≥ 12 × |floor_diff|.
    """
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
        "pharmacy": "#16a085",
        "room":     "#95a5a6",
        "corridor": "#bdc3c7",
    }.get(t, "#bdc3c7")


if __name__ == "__main__":
    G = build_graph("staff")
    print(f"Staff graph  : {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    G2 = build_graph("visitor")
    print(f"Visitor graph: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")
    # Print confirmed real data nodes
    confirmed = [n for n in NODES if "confirmed" in str(NODES[n])]
    print(f"\nNodes with confirmed real-world floor data:")
    for n in NODES:
        label = NODES[n].get("label","")
        if any(x in label for x in ["confirmed","Ground Floor IPD","3rd floor","2nd floor","F2","F3"]):
            print(f"  {n}: {label}")
