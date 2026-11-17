"""ดึงข้อมูลเชิงโครงสร้างจากเล่มหลักสูตร วศ.บ. วิศวกรรมโลจิสติกส์ (ปรับปรุง 2570) .docx
→ data/curriculum.json  (แหล่งข้อมูลเดียวสำหรับทั้ง Obsidian vault และเว็บ)

ใช้:  python tools/extract_curriculum.py [path/to/curriculum.docx]
ค่าเริ่มต้นอ่านจาก ../doc_ref/วศ.บ.โลจิสติกส์ 70.docx

หลักการ: แปลงเอกสารเป็นลำดับบรรทัด (ย่อหน้า = 1 บรรทัด, ตาราง = แถวละ 1 บรรทัดแบบ | a | b |)
แล้วแยกส่วนตามหัวข้อหมวด/หัวข้อย่อยที่ปรากฏในเล่ม ทุกค่าที่ดึงได้จะเก็บข้อความตามต้นฉบับ
ไม่แก้คำผิด — ข้อสังเกตเรื่องความไม่สอดคล้องจะถูกบันทึกไว้ใน issues[] แทน
"""
import json, re, sys
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "doc_ref" / "วศ.บ.โลจิสติกส์ 70.docx"
OUT = ROOT / "data" / "curriculum.json"

CODE_RE = re.compile(r"^[A-Z]{2}-\d{3}-\d{5}$")
CREDIT_RE = re.compile(r"^\d+\(\d+-\d+-\d+\)$")
WS = re.compile(r"\s+")


def clean(s):
    return WS.sub(" ", s or "").strip()


# ---------------------------------------------------------------- docx → lines
def doc_lines(path):
    d = docx.Document(str(path))
    out = []
    for el in d.element.body.iterchildren():
        tag = el.tag.split("}")[1]
        if tag == "p":
            t = clean(Paragraph(el, d).text)
            if t:
                out.append(t)
        elif tag == "tbl":
            out.append("<TABLE>")
            for r in Table(el, d).rows:
                cells, prev = [], None
                for c in r.cells:
                    if c._tc is prev:
                        continue
                    prev = c._tc
                    cells.append(clean(c.text))
                if any(cells):
                    out.append(cells)          # แถวตาราง = list
            out.append("</TABLE>")
    return out


L = doc_lines(SRC)
issues = []


def find(pred, start=0, end=None):
    end = len(L) if end is None else end
    for i in range(start, end):
        if isinstance(L[i], str) and pred(L[i]):
            return i
    raise ValueError("heading not found")


def is_row(x):
    return isinstance(x, list)


# ---------------------------------------------------------------- section anchors
ch = {n: find(lambda s, n=n: s == f"หมวดที่ {n}") for n in range(1, 10)}
s42 = find(lambda s: s.startswith("4.2 รายวิชา"), ch[4])
s43 = find(lambda s: s.startswith("4.3 คำอธิบายรายวิชา"), s42)
s44 = find(lambda s: s.startswith("4.4 แผนการเรียน"), s43)
s45 = find(lambda s: s.startswith("4.5 แผนที่แสดงความเชื่อมโยง"), s44)
s46 = find(lambda s: s.startswith("4.6 ชุดทักษะ"), s45)


def split_name(s):
    """'เคมีพื้นฐาน Fundamentals of Chemistry' / 'ชื่อไทย (English)' → (th, en)"""
    m = re.search(r"[A-Za-z]", s)
    if not m:
        return s.strip(), ""
    th, en = s[: m.start()].strip(), s[m.start():].strip()
    if th.endswith("("):
        th = th[:-1].strip()
        en = en[:-1] if en.endswith(")") else en
    return th, en.strip()


# ---------------------------------------------------------------- 4.2 course list
GROUP_RULES = [  # (prefix of heading, group id)
    ("กลุ่มวิชาบังคับ", "ge-req"),
    ("กลุ่มวิชาเลือก", "ge-elec"),
    ("กลุ่มวิชาพื้นฐานวิทยาศาสตร์", "sci"),
    ("กลุ่มวิชาพื้นฐานวิศวกรรมศาสตร์", "engfund"),
    ("วิชาชีพบังคับร่วม", "core"),
    ("(1) วิชาบังคับเอกวิศวกรรมอุตสาหการ", "ie"),
    ("(2) วิชาบังคับเอกวิศวกรรมการจัดการโซ่อุปทาน", "sc"),
    ("กลุ่มวิชาเสริมสร้างประสบการณ์", "exp"),
    ("กลุ่มวิชาการจัดการโลจิสติกส์และโซ่อุปทาน", "el-lsc"),
    ("กลุ่มวิชาวิศวกรรมการขนส่ง", "el-trans"),
    ("กลุ่มวิชาวิศวกรรมการจัดการอุตสาหกรรม", "el-indmgmt"),
    ("กลุ่มวิชาวิศวกรรมการผลิต", "el-mfg"),
]


def group_of(heading):
    for p, g in GROUP_RULES:
        if heading.startswith(p):
            return g
    return None


courses = {}          # code → dict
order = 0
g = None
for x in L[s42:s43]:
    if isinstance(x, str):
        g = group_of(x) or g
        continue
    if is_row(x) and len(x) >= 3 and CODE_RE.match(x[0]) and CREDIT_RE.match(x[-1]):
        code = x[0]
        th, en = split_name(x[1])
        if code in courses:
            issues.append({"where": "4.2", "code": code, "note": f"รหัสซ้ำในรายการกลุ่ม {g}"})
            continue
        order += 1
        courses[code] = dict(code=code, th=th, en=en, credits=x[-1], group=g, order=order,
                             descTh="", descEn="", prereqTh="", prereqEn="", clos=[])
    elif is_row(x) and x and re.match(r"^[A-Z]{2}-\d{3}-\d{3,4}$", x[0]):
        issues.append({"where": "4.2", "code": x[0], "note": "รหัสวิชาไม่ครบหลัก"})
        fixed = x[0] + "1"
        th, en = split_name(x[1])
        order += 1
        courses[fixed] = dict(code=fixed, th=th, en=en, credits=x[-1], group=g, order=order,
                              descTh="", descEn="", prereqTh="", prereqEn="", clos=[],
                              codeAsPrinted=x[0])

# ---------------------------------------------------------------- 4.3 descriptions + CLOs
THAI = re.compile(r"[฀-๿]")
cur = None
desc_group = None
DESC_GROUP_RULES = [
    ("วิชาชีพบังคับของวิชาเอกวิศวกรรมอุตสาหการ", "ie"),
    ("วิชาชีพบังคับของวิชาเอกวิศวกรรมการจัดการโซ่อุปทา", "sc"),
]
for x in L[s43:s44]:
    if isinstance(x, str):
        continue
    if not is_row(x):
        continue
    c0 = x[0]
    key = c0 if c0 in courses else (c0 + "1" if c0 + "1" in courses and len(c0) == 11 else None)
    if key and len(x) >= 2:
        cur = courses[key]
        cur["_descSeen"] = True
        # บางวิชา (เช่น GE-002-14003, 14013) เล่มพิมพ์คำอธิบายไทย+อังกฤษรวมไว้ในช่องชื่อวิชา
        # → ตัดชื่อวิชาออก แล้วแยกส่วนไทย (ถึงอักษรไทยตัวสุดท้าย) กับส่วนอังกฤษที่ตามมา
        cell = x[1]
        name_full = f"{cur['th']} ({cur['en']})" if cur["en"] else cur["th"]
        for prefix in (name_full, f"{cur['th']} {cur['en']}", cur["th"]):
            if cell.startswith(prefix) and len(cell) > len(prefix) + 40:
                rest = cell[len(prefix):].strip()
                last_th = max((i for i, ch in enumerate(rest) if "฀" <= ch <= "๿"), default=-1)
                if last_th > 0:
                    cur["descTh"] = rest[: last_th + 1].strip()
                    cur["descEn"] = rest[last_th + 1:].strip()
                    cur["descInNameCell"] = True
                break
        continue
    if CODE_RE.match(c0) and c0 not in courses:
        issues.append({"where": "4.3", "code": c0, "note": "มีคำอธิบายรายวิชาแต่ไม่อยู่ในรายการ 4.2"})
        cur = None
        continue
    if cur is None:
        continue
    m = re.match(r"^CLO\s*(\d+)", c0)
    if m and len(x) >= 2:
        cur["clos"].append({"n": int(m.group(1)), "th": x[1], "bloom": x[2] if len(x) > 2 else ""})
        continue
    if c0 == "" and len(x) >= 2:
        t = x[1]
        if not t:
            continue
        if re.match(r"^(วิชาบังคับก่อน|รายวิชาบังคับก่อน)", t):
            cur["prereqTh"] = t
        elif re.match(r"^(Prerequisite|Pre-requisite|Corequisite)", t, re.I):
            cur["prereqEn"] = t
        elif THAI.search(t[:40]):
            cur["descTh"] = (cur["descTh"] + " " + t).strip() if cur["descTh"] else t
        else:
            if not cur.get("_enNameSeen") and len(t) < 120 and not t.endswith((".", ";")) and t.lower().replace(" ", "") == cur["en"].lower().replace(" ", ""):
                cur["_enNameSeen"] = True
            elif not cur.get("_enNameSeen") and len(t) < 120 and ";" not in t:
                cur["_enNameSeen"] = True
                cur["enFromDesc"] = t
            else:
                cur["descEn"] = (cur["descEn"] + " " + t).strip() if cur["descEn"] else t

for c in courses.values():
    if not c.pop("_descSeen", False):
        issues.append({"where": "4.3", "code": c["code"], "note": "ไม่พบคำอธิบายรายวิชา"})
    c.pop("_enNameSeen", None)
    enD = c.pop("enFromDesc", None)
    if enD and c["en"] and enD.lower() != c["en"].lower():
        c["enAlt"] = enD

# ---------------------------------------------------------------- 4.4 study plans
plans = {"IE": [], "SC": []}
major = None
year = sem = None
sem_rec = None
for x in L[s44:s45]:
    if isinstance(x, str):
        if "แผนการเรียนปกติ" in x:
            major = "IE" if "อุตสาหการ" in x else "SC"
        elif m := re.match(r"^ปีการศึกษาที่ (\d)", x):
            year = int(m.group(1))
        elif m := re.match(r"^ภาคการศึกษาที่ (\d)", x):
            sem = int(m.group(1))
            sem_rec = {"year": year, "sem": sem, "courses": [], "credits": None, "cumulative": None}
            plans[major].append(sem_rec)
        elif m := re.match(r"^รวมหน่วยกิตลงทะเบียนเรียน (\d+)", x):
            sem_rec["credits"] = int(m.group(1))
        elif m := re.match(r"^รวมจำนวนหน่วยกิตสะสม (\d+)", x):
            sem_rec["cumulative"] = int(m.group(1))
        continue
    if is_row(x) and sem_rec is not None and len(x) >= 4 and x[0] != "หมวดวิชา":
        code = x[1]
        entry = {"code": code, "name": x[2], "prereq": x[3] if len(x) > 4 else "",
                 "credits": x[-1], "category": x[0]}
        sem_rec["courses"].append(entry)

for mj, sems in plans.items():
    for s in sems:
        tot = 0
        for e in s["courses"]:
            m = re.match(r"^(\d+)", e["credits"])
            tot += int(m.group(1)) if m else 0
        s["computed"] = tot
        if s["credits"] is not None and tot != s["credits"]:
            issues.append({"where": "4.4", "note": f"{mj} ปี {s['year']} ภาค {s['sem']}: รวมจากรายการ {tot} ≠ ที่ระบุ {s['credits']}"})

# ---------------------------------------------------------------- 4.5 CLO→YLO→PLO map
mapping = {"IE": [], "SC": []}
major = None
year = sem = None
for x in L[s45:s46]:
    if isinstance(x, str):
        if "แผนการเรียนปกติ" in x:
            major = "IE" if "อุตสาหการ" in x else "SC"
        elif m := re.match(r"^ปีที่ (\d) ภาคการศึกษาที่ (\d)", x):
            year, sem = int(m.group(1)), int(m.group(2))
        continue
    if is_row(x) and len(x) >= 5 and x[0] != "รหัสวิชา":
        clo_txt = x[2]
        m = re.match(r"^CLO\s*(\d+)\s*:?\s*(.*)$", clo_txt)
        plo_raw = x[4]
        lvl = re.search(r"\(([IRMA])\)", plo_raw)
        mapping[major].append({
            "year": year, "sem": sem, "code": x[0], "name": x[1],
            "clo": int(m.group(1)) if m else None, "cloText": m.group(2) if m else clo_txt,
            "ylo": x[3], "plo": re.sub(r"\s*\([IRMA]\)", "", plo_raw).strip(),
            "level": lvl.group(1) if lvl else "",
        })

# ---------------------------------------------------------------- 4.6 skill sets
skills = []
for x in L[s46: ch[5]]:
    if is_row(x) and x and re.match(r"^(LE|IE|SC)-SK\d+", x[0]):
        skills.append({"cells": x})
skill_header = next((x for x in L[s46: ch[5]] if is_row(x)), None)

# ---------------------------------------------------------------- 3.2 PLO / YLO
s32 = find(lambda s: s.startswith("3.2 ผลลัพธ์การเรียนรู้ระดับหลักสูตร"), ch[3])
s33 = find(lambda s: s.startswith("3.3 "), s32)
plos, ylos = [], []
ylo_major = None
year_intro = {}
last = None
cur_year = None
for x in L[s32:s33]:
    if not isinstance(x, str):
        continue
    if m := re.match(r"^PLO_(LE|IE|SC)(\d)\s+(.*)$", x):
        body = m.group(3)
        en = ""
        # ชื่อสั้นภาษาอังกฤษท้ายข้อ: PLO_LE ใช้ [..] ส่วน PLO_IE/SC ใช้ (..)
        if mm := re.search(r"[\[(]([A-Za-z][^\[\]()]+)[\])]\s*$", body):
            en, body = mm.group(1).strip(), body[: mm.start()].strip()
        last = {"id": f"PLO_{m.group(1)}{m.group(2)}", "scope": m.group(1), "th": body, "en": en}
        plos.append(last)
    elif m := re.match(r"^((IE|SC)-)?YLO(\d)\.(\d)\s+(.*)$", x):
        body = m.group(5)
        sup = re.findall(r"PLO_(?:LE|IE|SC)\d", body)
        last = {"id": x.split()[0], "major": (m.group(2) or "ALL"), "year": int(m.group(3)),
                "th": body, "plos": sup}
        ylos.append(last)
    elif x.startswith("2.1 ผลลัพธ์การเรียนรู้รายปีของวิชาเอกวิศวกรรมอุตสาหการ"):
        ylo_major, last = "IE", None
    elif x.startswith("2.2 ผลลัพธ์การเรียนรู้รายปีของวิชาเอกวิศวกรรมการจัดการ"):
        ylo_major, last = "SC", None
    elif x.startswith("2.3 ผลลัพธ์การเรียนรู้รายปีชั้นปีที่ 4"):
        ylo_major, last = "ALL", None
    elif m := re.match(r"^ปีที่ (\d) Yearly", x):
        cur_year, last = int(m.group(1)), None
    elif x.startswith("เมื่อสิ้นสุด") and ylo_major:
        year_intro[f"{ylo_major}-{cur_year}"] = x
        last = ("intro", f"{ylo_major}-{cur_year}")
    elif last is not None:
        # บรรทัดต่อเนื่อง (ข้อความถูกตัดขึ้นย่อหน้าใหม่)
        if isinstance(last, tuple):
            year_intro[last[1]] += " " + x
        elif isinstance(last, dict) and not re.match(r"^(ผลลัพธ์|\d\))", x):
            last["th"] += " " + x
            if "plos" in last:
                last["plos"] = re.findall(r"PLO_(?:LE|IE|SC)\d", last["th"])

plo_intro = next((x for x in L[s32:s33] if isinstance(x, str) and x.startswith("หลักสูตรกำหนดผลลัพธ์")), "")

# 3.3 ตารางที่ 1: PLO ↔ ความต้องการ/ผู้มีส่วนได้ส่วนเสีย
needs = {}
tab_on = False
for x in L[s33: ch[4]]:
    if isinstance(x, str) and x.startswith("ตารางที่ 1"):
        tab_on = True
    elif isinstance(x, str) and x.startswith("ตารางที่ 2"):
        tab_on = False
    if tab_on and is_row(x) and x and x[0].startswith("PLO_") and len(x) >= 4:
        needs[x[0]] = {"needs": [s.strip() for s in x[2].split("•") if s.strip()],
                       "sources": [s.strip() for s in x[3].split("•") if s.strip()]}
# ตารางที่ 2: PLO ↔ นโยบาย/แผนระดับชาติ
policy = {}
tab_on = False
for x in L[s33: ch[4]]:
    if isinstance(x, str) and x.startswith("ตารางที่ 2"):
        tab_on = True
    elif isinstance(x, str) and re.match(r"^(ตารางที่ 3|3\)|2\) ความสอดคล้องของผลลัพธ์การเรียนรู้ระดับหลักสูตรกับวิสัย)", x):
        tab_on = False
    if tab_on and is_row(x) and x and x[0].startswith("PLO_") and len(x) >= 3:
        policy[x[0]] = {"plans": [s.strip() for s in x[2].split("•") if s.strip()],
                        "contribution": x[3] if len(x) > 3 else ""}
# Generic / Subject specific
gen_spec = {}
for x in L[s33: ch[4]]:
    if is_row(x) and len(x) >= 3 and x[0].startswith("PLO_") and ("Specific" in x[1] or "Generic" in x[1]):
        gen_spec[x[0]] = {"type": x[1], "focus": x[2]}
for p in plos:
    p.update(needs.get(p["id"], {}))
    if p["id"] in policy:
        p["policy"] = policy[p["id"]]
    if p["id"] in gen_spec:
        p["outcomeType"] = gen_spec[p["id"]]["type"]
        p["focus"] = gen_spec[p["id"]]["focus"]

# 3.1 ปรัชญาและวัตถุประสงค์
s31 = find(lambda s: s.startswith("3.1 ปรัชญา"), ch[3])
philosophy = L[find(lambda s: s.startswith("1) ปรัชญาของหลักสูตร"), s31) + 1].strip('"“”')
i_imp = find(lambda s: s.startswith("2) ความสำคัญของหลักสูตร"), s31)
i_obj = find(lambda s: s.startswith("3) วัตถุประสงค์ของหลักสูตร"), s31)
importance = [x for x in L[i_imp + 1: i_obj] if isinstance(x, str)]
objectives = [re.sub(r"^\d+\.\s*", "", x) for x in L[i_obj + 1: s32] if isinstance(x, str) and re.match(r"^\d+\.", x)]
objectives_lead = next((x for x in L[i_obj + 1: s32] if isinstance(x, str) and not re.match(r"^\d+\.", x)), "")

# 3.4 กิจกรรมเสริมหลักสูตร
s34 = find(lambda s: s.startswith("3.4 กิจกรรมเสริม"), s33)
activities = [x for x in L[s34: ch[4]] if is_row(x) and x and re.match(r"^\d+$", x[0])]
act_header = next((x for x in L[s34: ch[4]] if is_row(x)), None)

# ---------------------------------------------------------------- หมวด 1: faculty
faculty = []
i_fac = find(lambda s: s.startswith("อาจารย์ประจำหลักสูตรและคุณสมบัติ"), ch[1])
for x in L[i_fac: ch[2]]:
    if is_row(x) and len(x) >= 7 and re.match(r"^\d+$", x[0]):
        name = x[2]
        faculty.append({
            "no": int(x[0]), "position": x[1], "name": name.rstrip("*").strip(),
            "responsible": name.endswith("*"),
            "degrees": x[3], "institutions": x[4], "years": x[5], "match": x[6],
        })
resp_major = {}
cur_major = None
i_resp = find(lambda s: s.startswith("1) อาจารย์ผู้รับผิดชอบหลักสูตร"), ch[1])
for x in L[i_resp:i_fac]:
    if is_row(x) and len(x) == 1:
        cur_major = "IE" if "อุตสาหการ" in x[0] else "SC"
    elif is_row(x) and len(x) >= 7 and re.match(r"^\d+$", x[0]):
        resp_major[x[2].strip()] = cur_major
for f in faculty:
    f["major"] = resp_major.get(f["name"], "")
    f["chair"] = "ประธานหลักสูตร" in f["position"]

# ---------------------------------------------------------------- หมวด 1: intake + budget (เก็บตารางดิบ)
def tables_between(a, b):
    out, cur_t = [], None
    for x in L[a:b]:
        if x == "<TABLE>":
            cur_t = []
        elif x == "</TABLE>":
            out.append(cur_t)
            cur_t = None
        elif cur_t is not None and is_row(x):
            cur_t.append(x)
    return out


i_intake = find(lambda s: s.startswith("1.2 แผนการรับนักศึกษา"), ch[1])
i_fac0 = find(lambda s: s.startswith("1.3 อาจารย์"), ch[1])
t_intake = tables_between(i_intake, i_fac0)

careers = []
i_car = find(lambda s: s.startswith("7) อาชีพที่สามารถประกอบได้"), ch[1])
for x in L[i_car + 1:]:
    if isinstance(x, str) and re.match(r"^8\)", x):
        break
    if isinstance(x, str):
        careers.append(x)

# ---------------------------------------------------------------- หมวด 5–9 : เอกสารเชิงโครง + ตารางหลัก
# เก็บทุกย่อหน้าและตารางตามลำดับในเล่ม (ไม่ตัดเนื้อหา) เป็น blocks แล้วดึงตารางหลักเป็นข้อมูลเชิงโครงเพิ่ม
HEAD_RE = re.compile(r"^(?:(\d+\.\d+(?:\.\d+)*)\.?\s|(\d+)\)\s|\((\d+)\)\s|(ปีที่ \d)$)")


def doc_blocks(a, b):
    blocks, tbl = [], None
    for x in L[a:b]:
        if x == "<TABLE>":
            tbl = []
        elif x == "</TABLE>":
            if tbl:
                blocks.append({"t": "table", "header": tbl[0], "rows": tbl[1:]})
            tbl = None
        elif tbl is not None:
            tbl.append(x)
        elif isinstance(x, str):
            m = HEAD_RE.match(x)
            if m and len(x) <= 140:
                lvl = (m.group(1).count(".") + 1) if m.group(1) else (4 if m.group(2) else 5 if m.group(3) else 4)
                blocks.append({"t": "h", "lvl": lvl, "text": x})
            else:
                blocks.append({"t": "p", "text": x})
    return blocks


def table_after(heading_prefix, start, end):
    """ตารางแรกหลังบรรทัดที่ขึ้นต้นด้วย heading_prefix"""
    i = find(lambda s: s.startswith(heading_prefix), start, end)
    j = L.index("<TABLE>", i)
    k = L.index("</TABLE>", j)
    rows = [r for r in L[j + 1:k] if is_row(r)]
    return rows[0], rows[1:]


chapter_end = {5: ch[6], 6: ch[7], 7: ch[8], 8: ch[9], 9: find(lambda s: s == "ภาคผนวก", ch[9])}
docs = {n: {"title": L[ch[n] + 1], "blocks": doc_blocks(ch[n] + 2, chapter_end[n])} for n in range(5, 10)}
plo_id = lambda s: (re.match(r"^(PLO_(?:LE|IE|SC)\d)", s or "") or [None, None])[1]

# 5.1 PLO → วิธีสอน / วิธีประเมิน
_, rows = table_after("5.1 ", ch[5], ch[6])
teach_by_plo = [{"plo": plo_id(r[0]), "teach": r[1], "assess": r[2] if len(r) > 2 else ""} for r in rows if plo_id(r[0])]

# 5.2 กลยุทธ์การสอน 5 แบบ
hdr, rows = table_after("1) วิธีการจัดการเรียนการสอนที่มุ่งเน้น", ch[5], ch[6])
strategies = []
for r in rows:
    r = r + [""] * (6 - len(r))
    strategies.append({"name": r[0], "detail": r[1], "courses": r[2],
                       "plos": sorted(set(re.findall(r"PLO_(?:LE|IE|SC)\d", r[3])), key=lambda p: (p[4:6] != "LE", p)),
                       "ploText": r[3], "tools": r[4], "outcome": r[5]})

# 6.1 วิธีประเมินราย PLO พร้อมน้ำหนัก
hdr, rows = table_after("6.1 ", ch[6], ch[7])
assessment = []
for r in rows:
    p = plo_id(r[0])
    if not p or len(r) < 7:
        continue
    w = r[3]
    pct = re.search(r"(\d+)\s*%", w)
    if "IE และ SC" in w or not re.search(r"\((IE|SC)\)", w):
        mjs = ["IE", "SC"] if p.startswith("PLO_LE") else [p[4:6]]
    else:
        mjs = re.findall(r"\((IE|SC)\)", w)
    assessment.append({"plo": p, "method": r[1], "format": r[2], "weightText": w,
                       "weight": int(pct.group(1)) if pct else None, "majors": mjs,
                       "when": r[4], "assessor": r[5], "pass": r[6]})
for mj in ("IE", "SC"):
    for p in plos:
        if p["scope"] not in ("LE", mj):
            continue
        tot = sum(a["weight"] or 0 for a in assessment if a["plo"] == p["id"] and mj in a["majors"])
        if tot != 100:
            issues.append({"where": "6.1", "note": f"{mj}: น้ำหนักการประเมิน {p['id']} รวม {tot}% (ไม่เท่ากับ 100%)"})

# 8.2 การประเมิน YLO รายปี
s82 = find(lambda s: s.startswith("8.2 "), ch[8], ch[9])
s83 = find(lambda s: s.startswith("8.3 "), s82, ch[9])
ylo_assessment = []
yr = None
for x in L[s82:s83]:
    if isinstance(x, str) and (m := re.match(r"^ปีที่ (\d)$", x)):
        yr = int(m.group(1))
    elif is_row(x) and len(x) >= 5 and re.match(r"^((IE|SC)-)?YLO\d", x[0]):
        ylo_assessment.append({"ylo": x[0], "year": yr, "text": x[1], "method": x[2], "tool": x[3], "criteria": x[4]})

# 8.4 การประเมิน PLO ระดับหลักสูตร
hdr84, rows = table_after("8.4 ", ch[8], ch[9])
plo_assessment = {"header": hdr84, "rows": rows}

# ---------------------------------------------------------------- course → majors / plan semester
for mj, sems in plans.items():
    for s in sems:
        for e in s["courses"]:
            c = courses.get(e["code"])
            if c is None:
                if CODE_RE.match(e["code"]):
                    issues.append({"where": "4.4", "code": e["code"], "note": f"อยู่ในแผน {mj} แต่ไม่อยู่ในรายการ 4.2"})
                continue
            c.setdefault("plan", {})[mj] = {"year": s["year"], "sem": s["sem"]}
            if e["prereq"] and not c.get("planPrereq"):
                c["planPrereq"] = e["prereq"]

for c in courses.values():
    if c["group"] == "ie":
        c["majors"] = ["IE"]
    elif c["group"] == "sc":
        c["majors"] = ["SC"]
    else:
        c["majors"] = ["IE", "SC"]
    # CLO → YLO/PLO จากแผนที่ 4.5 (แยกตามวิชาเอก)
    for mj in ("IE", "SC"):
        rows = [r for r in mapping[mj] if r["code"] == c["code"]]
        for r in rows:
            for clo in c["clos"]:
                if clo["n"] == r["clo"]:
                    clo.setdefault("map", {})[mj] = {"ylo": r["ylo"], "plo": r["plo"], "level": r["level"]}
    c["plos"] = sorted({clo_map["plo"] for clo in c["clos"] for clo_map in clo.get("map", {}).values() if clo_map["plo"]})

# prerequisite codes → links
for c in courses.values():
    txt = " ".join([c.get("prereqTh", ""), c.get("prereqEn", ""), c.get("planPrereq", "")])
    pre = []
    for code in re.findall(r"[A-Z]{2}-\d{3}-\d{4,5}", txt):
        if code not in pre and code != c["code"]:
            pre.append(code)
    c["prereq"] = pre
    for p in pre:
        if p not in courses:
            issues.append({"where": "prereq", "code": c["code"], "note": f"วิชาบังคับก่อน {p} ไม่อยู่ในรายการวิชา"})

# ---------------------------------------------------------------- structure (4.1/4.2 headings)
structure = []
for x in L[s42:s43]:
    if isinstance(x, str) and (m := re.search(r"จำนวน (\d+) หน่วยกิต", x)):
        structure.append({"label": re.sub(r"\s*จำนวน \d+ หน่วยกิต.*$", "", x), "credits": int(m.group(1))})

GROUPS = [
    {"id": "ge-req", "cat": "ge", "th": "หมวดวิชาศึกษาทั่วไป · กลุ่มวิชาบังคับ", "credits": 15},
    {"id": "ge-elec", "cat": "ge", "th": "หมวดวิชาศึกษาทั่วไป · กลุ่มวิชาเลือก", "credits": 9, "pick": "เลือกเรียน 9 หน่วยกิต"},
    {"id": "sci", "cat": "spec", "th": "กลุ่มวิชาพื้นฐานวิทยาศาสตร์และคณิตศาสตร์", "credits": 14},
    {"id": "engfund", "cat": "spec", "th": "กลุ่มวิชาพื้นฐานวิศวกรรมศาสตร์", "credits": 25},
    {"id": "core", "cat": "spec", "th": "วิชาชีพบังคับร่วม", "credits": 15},
    {"id": "ie", "cat": "spec", "th": "วิชาบังคับเอกวิศวกรรมอุตสาหการ", "credits": 24, "major": "IE"},
    {"id": "sc", "cat": "spec", "th": "วิชาบังคับเอกวิศวกรรมการจัดการโซ่อุปทาน", "credits": 24, "major": "SC"},
    {"id": "exp", "cat": "spec", "th": "กลุ่มวิชาเสริมสร้างประสบการณ์ในวิชาชีพ", "credits": 11},
    {"id": "el-lsc", "cat": "pe", "th": "วิชาชีพเลือก · การจัดการโลจิสติกส์และโซ่อุปทาน", "credits": 3, "pick": "เลือก 3 หน่วยกิตจากกลุ่มวิชาชีพเลือก"},
    {"id": "el-trans", "cat": "pe", "th": "วิชาชีพเลือก · วิศวกรรมการขนส่ง", "credits": 3},
    {"id": "el-indmgmt", "cat": "pe", "th": "วิชาชีพเลือก · วิศวกรรมการจัดการอุตสาหกรรม", "credits": 3},
    {"id": "el-mfg", "cat": "pe", "th": "วิชาชีพเลือก · วิศวกรรมการผลิต", "credits": 3},
]
for gr in GROUPS:
    gr["courses"] = [c["code"] for c in sorted(courses.values(), key=lambda c: c["order"]) if c["group"] == gr["id"]]

# ---------------------------------------------------------------- ตรวจความสอดคล้องของแผนที่ 4.5
_norm = lambda s: re.sub(r"\s+", "", s or "")[:25]
_ylo = {y["id"]: y for y in ylos}
for mj in ("IE", "SC"):
    # (1) ข้อความ CLO ในแผนที่ต้องตรงกับ CLO ของรายวิชาในหมวด 4.3
    for code in sorted({r["code"] for r in mapping[mj]}):
        c = courses.get(code)
        if not c:
            continue
        diff = [r["clo"] for r in mapping[mj] if r["code"] == code and not any(
            k["n"] == r["clo"] and _norm(k["th"]) == _norm(r["cloText"]) for k in c["clos"])]
        if diff:
            issues.append({"where": "4.5", "code": code,
                           "note": f"{mj}: ข้อความ CLO{','.join(map(str, diff))} ในแผนที่ไม่ตรงกับหมวด 4.3"})
    # (2) PLO ในแถวแผนที่ต้องเป็น PLO ที่ YLO นั้นรองรับตามหมวด 3.2
    bad = [r for r in mapping[mj] if r["ylo"].rstrip(" (") in _ylo and r["plo"] not in _ylo[r["ylo"].rstrip(" (")]["plos"]]
    if bad:
        pairs = sorted({f"{r['ylo'].rstrip(' (')}→{r['plo']}" for r in bad})
        issues.append({"where": "4.5", "note": f"{mj}: {len(bad)} แถวผูก YLO กับ PLO ที่ YLO นั้นไม่ได้รองรับตามหมวด 3.2 ({', '.join(pairs)})"})

# ---------------------------------------------------------------- PLO coverage check
for mj in ("IE", "SC"):
    for p in plos:
        if p["scope"] not in ("LE", mj):
            continue
        rows = [r for r in mapping[mj] if r["plo"] == p["id"]]
        if not rows:
            issues.append({"where": "4.5", "note": f"{mj}: {p['id']} ไม่มี CLO ใดเชื่อมโยง"})
        if not any(r["level"] == "M" for r in rows):
            issues.append({"where": "4.5", "note": f"{mj}: {p['id']} ไม่มีรายวิชาที่ระบุระดับ M (Mastery)"})

meta = {
    "programCode": next((x.split()[-1] for x in L[ch[1]:ch[2]] if isinstance(x, str) and x.startswith("รหัสหลักสูตร")), ""),
    "nameTh": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโลจิสติกส์",
    "nameEn": "Bachelor of Engineering Program in Logistics Engineering",
    "degreeTh": "วิศวกรรมศาสตรบัณฑิต (วิศวกรรมโลจิสติกส์)", "degreeThShort": "วศ.บ. (วิศวกรรมโลจิสติกส์)",
    "degreeEn": "Bachelor of Engineering (Logistics Engineering)", "degreeEnShort": "B.Eng. (Logistics Engineering)",
    "revision": "หลักสูตรปรับปรุง พ.ศ. 2570", "basedOn": "หลักสูตรปรับปรุง พ.ศ. 2566",
    "faculty": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม", "university": "มหาวิทยาลัยกาฬสินธุ์",
    "totalCredits": 122, "years": 4, "language": "ภาษาไทย",
    "majors": [
        {"id": "IE", "th": "วิชาเอกวิศวกรรมอุตสาหการ", "en": "Industrial Engineering"},
        {"id": "SC", "th": "วิชาเอกวิศวกรรมการจัดการโซ่อุปทาน", "en": "Supply Chain Management Engineering"},
    ],
    "isced": ["07 Engineering, manufacturing and construction", "071 Engineering and engineering trades",
              "0719 Engineering and engineering trades not elsewhere classified"],
    "qa": "AUN-QA",
    "careers": careers,
    "philosophy": philosophy, "importance": importance,
    "objectivesLead": objectives_lead, "objectives": objectives,
    "ploIntro": plo_intro, "tuitionPerSemester": 10200,
}

data = {
    "source": SRC.name,
    "meta": meta,
    "structure": structure,
    "groups": GROUPS,
    "courses": sorted(courses.values(), key=lambda c: c["order"]),
    "plans": plans,
    "mapping": mapping,
    "plos": plos,
    "ylos": ylos,
    "yloIntro": year_intro,
    "skillSets": {"header": skill_header, "rows": [s["cells"] for s in skills]},
    "activities": {"header": act_header, "rows": activities},
    "faculty": faculty,
    "intakeTables": t_intake,
    "teachByPlo": teach_by_plo,
    "strategies": strategies,
    "assessment": assessment,
    "yloAssessment": ylo_assessment,
    "ploAssessment": plo_assessment,
    "docs": docs,
    "issues": issues,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

n_clo = sum(len(c["clos"]) for c in courses.values())
print(f"courses={len(courses)} clos={n_clo} plos={len(plos)} ylos={len(ylos)} "
      f"planIE={len(plans['IE'])} planSC={len(plans['SC'])} mapIE={len(mapping['IE'])} mapSC={len(mapping['SC'])} "
      f"faculty={len(faculty)} skills={len(skills)} activities={len(activities)} issues={len(issues)}")
print("→", OUT)
