"""สร้างโน้ต Obsidian ของหลักสูตรจาก data/curriculum.json → LE_Vault/10_Curriculum/  (SRS: VR-01…VR-06)

ใช้ (จากโฟลเดอร์ LE_web):  python -E -P tools/build_vault.py

- เขียนเฉพาะใต้ LE_Vault/10_Curriculum/ เท่านั้น: ลบทั้งโฟลเดอร์แล้วสร้างใหม่ทุกครั้ง (ห้ามเขียนมือในโฟลเดอร์นี้)
- ผลลัพธ์ไม่มีเวลา/วันที่ที่เปลี่ยนทุกรอบ รันซ้ำแล้วไฟล์ต้องเหมือนเดิม
- ข้อสังเกตต่อรายการดึงจาก issues[] ใน JSON และจากแถว | ISS-xx | ใน 01_Requirements/04_Issues_Register.md
  ที่อ้างรหัสวิชา / PLO / YLO / ชุดทักษะ
- ลิงก์ในตารางใช้ [[target\\|alias]] เพราะ | ปกติจะตัดคอลัมน์ของตาราง Markdown
"""
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "curriculum.json"
VAULT = ROOT / "LE_Vault"
OUT = VAULT / "10_Curriculum"
REGISTER = VAULT / "01_Requirements" / "04_Issues_Register.md"
REGISTER_NOTE = "04_Issues_Register"

CODE_RE = re.compile(r"[A-Z]{2}-\d{3}-\d{5}")
CODE4_RE = re.compile(r"[A-Z]{2}-\d{3}-\d{4}(?!\d)")          # รหัสที่พิมพ์ขาดหลักในเล่ม
SHORT_RE = re.compile(r"(?<![\d\-.])1[1-7]\d{3}(?![\d.])")     # อ้างแบบย่อ เช่น 13012
PLO_RE = re.compile(r"PLO_(LE|IE|SC)(\d)((?:\s*[–-]\s*\d)?)((?:/(?:PLO_)?(?:LE|IE|SC)\d)*)")
YLO_RE = re.compile(r"(?:(?:IE|SC)-)?YLO\d+\.\d+")
SKILL_RE = re.compile(r"(?:LE|IE|SC)-SK\d{2}")

INFO = "> [!info] สร้างอัตโนมัติจากเล่มหลักสูตร — ห้ามแก้ไฟล์นี้ แก้ที่ overrides/ หรือเล่ม .docx"
MAJOR_TH = {"IE": "วิศวกรรมอุตสาหการ", "SC": "วิศวกรรมการจัดการโซ่อุปทาน"}
SCOPE_TH = {"LE": "ร่วมทั้งสองวิชาเอก", "IE": "วิชาเอกวิศวกรรมอุตสาหการ", "SC": "วิชาเอกวิศวกรรมการจัดการโซ่อุปทาน"}
CAT_TH = {"ge": "หมวดวิชาศึกษาทั่วไป", "spec": "หมวดวิชาเฉพาะ", "pe": "กลุ่มวิชาชีพเลือก"}


# ---------------------------------------------------------------- helpers
def norm(x):
    """แปลง CRLF/CR → LF ในทุกสตริงของข้อมูล"""
    if isinstance(x, str):
        return x.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    return x


def cell(s):
    """ข้อความที่ปลอดภัยสำหรับช่องตาราง Markdown"""
    s = "" if s is None else str(s)
    return re.sub(r"\s*\n\s*", "<br>", s.strip()).replace("|", "\\|")


def alias_safe(s):
    return re.sub(r"\s+", " ", str(s)).replace("|", "/").replace("[", "(").replace("]", ")").strip()


def wl(target, alias=None, table=False):
    if not alias or alias == target:
        return f"[[{target}]]"
    sep = "\\|" if table else "|"
    return f"[[{target}{sep}{alias_safe(alias)}]]"


def ylo_id(raw):
    """'YLO4.3 (' → 'YLO4.3'"""
    raw = (raw or "").strip()
    m = YLO_RE.match(raw)
    return m.group(0) if m else raw


def credit_units(s):
    m = re.match(r"\s*(\d+)", s or "")
    return int(m.group(1)) if m else 0


def yaml_val(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(yaml_val(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def frontmatter(d):
    lines = ["---"] + [f"{k}: {yaml_val(v)}" for k, v in d.items()] + ["---", ""]
    return "\n".join(lines)


def callout(kind, title, items):
    out = [f"> [!{kind}] {title}"]
    out += [f"> - {it}" for it in items]
    return "\n".join(out)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


written = []


def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    text = text.rstrip("\n") + "\n"
    p.write_text(text, encoding="utf-8", newline="\n")
    written.append(rel)


# ---------------------------------------------------------------- load
data = norm(json.loads(DATA.read_text(encoding="utf-8")))
SOURCE_DOC = data.get("source", "curriculum.docx")
for key in ("courses", "plos", "ylos"):
    if not data.get(key):
        raise SystemExit(f"ERROR: curriculum.json ไม่มีข้อมูล '{key}' (ว่าง) — รัน tools/extract_curriculum.py ก่อน")


def src(section):
    return f"data/curriculum.json ← {SOURCE_DOC} {section}"


meta = data["meta"]
courses = data["courses"]
C = {c["code"]: c for c in courses}
PRINTED = {c["codeAsPrinted"]: c["code"] for c in courses if c.get("codeAsPrinted")}
G = {g["id"]: g for g in data["groups"]}
PLOS = data["plos"]
P = {p["id"]: p for p in PLOS}
YLOS = data["ylos"]
Y = {y["id"]: y for y in YLOS}
MAJORS = [m["id"] for m in meta["majors"]]
NAME2CODE = {re.sub(r"\s+", "", c["th"]): c["code"] for c in courses}

# mapping (normalised)
MAP = {mj: [] for mj in MAJORS}
for mj in MAJORS:
    for r in data["mapping"].get(mj, []):
        r = dict(r)
        r["ylo"] = ylo_id(r["ylo"])
        r["code"] = (r.get("code") or "").strip()
        MAP[mj].append(r)
MAP_BY = {(mj, r["code"], r["clo"]): r for mj in MAJORS for r in MAP[mj]}


def ylo_mismatch(r):
    y = Y.get(r["ylo"])
    return bool(y and r["plo"] and r["plo"] not in y["plos"])


oddities = defaultdict(int)
for mj in MAJORS:
    for r in MAP[mj]:
        if ylo_mismatch(r):
            oddities[f"แผนที่ {mj}: PLO ที่จับคู่ไม่อยู่ใน PLO ที่ YLO ระบุในข้อ 3.2"] += 1
        if not r["code"]:
            oddities[f"แผนที่ {mj}: แถวไม่มีรหัสวิชา"] += 1
        elif r["code"] not in C:
            oddities[f"แผนที่ {mj}: รหัสวิชาไม่อยู่ในรายการ 4.2"] += 1
        if r["ylo"] not in Y:
            oddities[f"แผนที่ {mj}: YLO ไม่รู้จัก"] += 1
        if r["plo"] and r["plo"] not in P:
            oddities[f"แผนที่ {mj}: PLO ไม่รู้จัก"] += 1

# ---------------------------------------------------------------- issues (JSON + register)
json_issues = defaultdict(list)
for it in data.get("issues", []):
    code = it.get("code")
    if code:
        json_issues[PRINTED.get(code, code)].append(f"ตัวดึงข้อมูล ({it.get('where', '')}): {it['note']}")
    for pid in re.findall(r"PLO_(?:LE|IE|SC)\d", it.get("note", "")):
        json_issues[pid].append(f"ตัวดึงข้อมูล ({it.get('where', '')}): {it['note']}")


def split_row(line):
    parts = re.split(r"(?<!\\)\|", line.strip())
    return [p.strip() for p in parts[1:-1]]


def plo_targets(text):
    out = []
    for m in PLO_RE.finditer(text):
        scope, a, rng, more = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        b = int(re.sub(r"\D", "", rng)) if rng.strip() else a
        out += [f"PLO_{scope}{n}" for n in range(a, b + 1)]
        out += ["PLO_" + x for x in re.findall(r"(?:LE|IE|SC)\d", more)]
    return out


reg_issues = defaultdict(list)     # entity id → [(ISS, text)]
REG_IDS = []
if REGISTER.exists():
    for line in REGISTER.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        if not re.match(r"^\|\s*(~~)?ISS-\d+", line):
            continue
        cells = split_row(line)
        iss = re.sub(r"~", "", cells[0]).strip()
        closed = "~~" in line
        where = cells[1].replace("~~", "") if len(cells) > 1 else ""
        note = cells[2].replace("~~", "") if len(cells) > 2 else ""
        fix = cells[3].replace("~~", "") if len(cells) > 4 else ""
        whole = " ".join(cells)
        REG_IDS.append(iss)
        targets = set()
        for code in CODE_RE.findall(whole):
            if code in C:
                targets.add(code)
        for code in CODE4_RE.findall(whole):
            if code in PRINTED:
                targets.add(PRINTED[code])
        for short in SHORT_RE.findall(whole):
            hits = [c for c in C if c.endswith("-" + short)]
            if len(hits) == 1:
                targets.add(hits[0])
        targets.update(t for t in plo_targets(whole) if t in P)
        targets.update(t for t in (ylo_id(x) for x in YLO_RE.findall(whole)) if t in Y)
        targets.update(SKILL_RE.findall(whole))
        if re.search(r"(?<![\d.])4\.4(?![\d.])", where) and not targets:
            targets.add("PLAN")                 # ข้อสังเกตของแผนการเรียน (หัวข้อ 4.4) ที่ไม่ได้อ้างรายวิชาใด
        clean = lambda t: t.replace(r"\|", "/")
        text = f"{wl(REGISTER_NOTE, iss)} ({clean(where)}) {clean(note)}" + (f" — แนวทางแก้: {clean(fix)}" if fix else "")
        if closed:
            text += " *(ปิดแล้ว)*"
        for t in targets:
            reg_issues[t].append(text)


def issue_lines(entity):
    return [*json_issues.get(entity, []), *reg_issues.get(entity, [])]


# ---------------------------------------------------------------- shared links
def clink(code, table=True, show_code=False):
    c = C.get(code)
    if not c:
        return cell(code) if table else code
    alias = f"{code} {c['th']}" if show_code else c["th"]
    return wl(code, alias, table)


def plan_label(c, mj):
    p = c.get("plan", {}).get(mj)
    return f"ปี {p['year']} ภาค {p['sem']}" if p else ""


def plan_link(c, mj, table=True):
    p = c.get("plan", {}).get(mj)
    if not p:
        return "—"
    return wl(f"Plan_{mj}#ปีที่ {p['year']} ภาคการศึกษาที่ {p['sem']}", f"ปี {p['year']}/{p['sem']}", table)


def link_codes_in(text, table=True):
    """แทนรหัสวิชาในข้อความด้วยลิงก์ (เฉพาะรหัสที่มีโน้ต)"""
    def rep(m):
        code = m.group(0)
        return f"[[{code}]] " if code in C else code
    t = CODE_RE.sub(rep, text)
    t = re.sub(r"\]\] +", "]] ", t).strip()
    return cell(t) if table else t


def group_link(gid, table=True):
    g = G.get(gid)
    return wl(gid, g["th"], table) if g else (gid or "—")


def majors_of_scope(scope):
    return list(MAJORS) if scope in ("LE", "ALL") else [scope]


# ---------------------------------------------------------------- 0. reset output folder (เฉพาะ 10_Curriculum)
if OUT.resolve().parent != VAULT.resolve() or OUT.name != "10_Curriculum":
    raise SystemExit(f"ERROR: โฟลเดอร์ปลายทางไม่ถูกต้อง {OUT}")
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

# reverse prerequisites
successors = defaultdict(list)
for c in courses:
    for p in c.get("prereq", []):
        successors[p].append(c["code"])

# ---------------------------------------------------------------- 1. courses
n_course_warn = 0
for c in courses:
    code = c["code"]
    years = sorted({p["year"] for p in c.get("plan", {}).values()})
    fm = {
        "type": "course", "code": code, "name_th": c["th"], "name_en": c["en"],
        "credits": c["credits"], "credit_units": credit_units(c["credits"]),
        "group": c["group"], "major": c["majors"],
        "year": years[0] if len(years) == 1 else (years or None),
    }
    for mj in MAJORS:
        p = c.get("plan", {}).get(mj)
        fm[f"plan_{mj}"] = f"{p['year']}/{p['sem']}" if p else None
    fm.update({"plo": c.get("plos", []), "prereq": [p for p in c.get("prereq", []) if p in C],
               "clo_count": len(c["clos"]), "generated": True, "source": src("§4.2–4.5")})

    rows = [["ชื่อภาษาไทย", cell(c["th"])], ["ชื่อภาษาอังกฤษ", cell(c["en"] or "—")]]
    if c.get("enAlt"):
        rows.append(["ชื่ออังกฤษในคำอธิบายรายวิชา", cell(c["enAlt"])])
    rows += [["หน่วยกิต", cell(c["credits"])], ["กลุ่มวิชา", group_link(c["group"])],
             ["วิชาเอก", " · ".join(f"{m} ({MAJOR_TH[m]})" for m in c["majors"])]]
    for mj in MAJORS:
        rows.append([f"แผนการเรียน {mj}", plan_link(c, mj) if mj in c["majors"] else "—"])
    pre_links = [clink(p, show_code=True) if p in C else cell(p) + " ⚠" for p in c.get("prereq", [])]
    rows.append(["วิชาบังคับก่อน", ", ".join(pre_links) or "—"])
    pre_txt = [t for t in (c.get("prereqTh"), c.get("prereqEn")) if t]
    if pre_txt:
        rows.append(["ข้อความวิชาบังคับก่อนในเล่ม", "<br>".join(cell(t) for t in pre_txt)])
    succ = [clink(s, show_code=True) for s in successors.get(code, [])]
    rows.append(["วิชาที่ต่อยอด", ", ".join(succ) or "—"])
    rows.append(["PLO ที่เชื่อมโยง", ", ".join(wl(p) for p in c.get("plos", []) if p in P) or "—"])

    warns = []
    if c.get("codeAsPrinted"):
        warns.append(f"รหัสในตาราง 4.2 พิมพ์เป็น `{c['codeAsPrinted']}` (ขาดหลัก) ใช้ `{code}` แทน")
    if not c["descTh"]:
        warns.append("ไม่มีคำอธิบายรายวิชาภาษาไทย")
    if not c["descEn"]:
        warns.append("ไม่มีคำอธิบายรายวิชาภาษาอังกฤษ")
    if not c["clos"]:
        warns.append("ไม่มี CLO ในเล่ม")
    for p in c.get("prereq", []):
        if p not in C:
            warns.append(f"วิชาบังคับก่อน `{p}` ไม่อยู่ในรายการวิชา")
    for pre in re.findall(r"[A-Z]{2}-\d{3}-\d{3}(?!\d)", " ".join(pre_txt)):
        warns.append(f"วิชาบังคับก่อนอ้างรหัสที่ไม่มีในหลักสูตร `{pre}`")
    if c["clos"]:
        for mj in c["majors"]:
            missing = [cl["n"] for cl in c["clos"] if (mj, code, cl["n"]) not in MAP_BY]
            if len(missing) == len(c["clos"]):
                warns.append(f"CLO ทั้งหมดยังไม่เชื่อมกับ YLO/PLO ในแผนที่ของวิชาเอก {mj} (4.5)")
            elif missing:
                warns.append(f"CLO {', '.join(map(str, missing))} ไม่พบในแผนที่ของวิชาเอก {mj} (4.5)")
        mism = sorted({(mj, cl["n"]) for mj in c["majors"] for cl in c["clos"]
                       if (r := MAP_BY.get((mj, code, cl["n"]))) and ylo_mismatch(r)})
        for mj in c["majors"]:
            diff = [cl["n"] for cl in c["clos"] if (r := MAP_BY.get((mj, code, cl["n"])))
                    and re.sub(r"\s+", "", r["cloText"]) != re.sub(r"\s+", "", cl["th"])]
            if diff:
                warns.append(f"ข้อความ CLO {', '.join(map(str, diff))} ในแผนที่ 4.5 ของวิชาเอก {mj} "
                             "ไม่ตรงกับ CLO ในคำอธิบายรายวิชา 4.3 (ตารางนี้แสดงข้อความจาก 4.3)")
        if mism:
            warns.append("PLO ที่จับคู่ไม่อยู่ใน PLO ที่ YLO นั้นระบุไว้ในข้อ 3.2 (ช่องที่มี ⚠): "
                         + ", ".join(f"{mj} CLO{n}" for mj, n in mism))
    warns = list(dict.fromkeys(warns + issue_lines(code)))
    n_course_warn += bool(warns)

    clo_rows = []
    for cl in c["clos"]:
        r_cells = [str(cl["n"]), cell(cl["th"]), cell(cl.get("bloom", ""))]
        for mj in MAJORS:
            if mj not in c["majors"]:
                r_cells.append("—")
                continue
            r = MAP_BY.get((mj, code, cl["n"]))
            if not r:
                r_cells.append("ยังไม่เชื่อม")
                continue
            y = wl(r["ylo"]) if r["ylo"] in Y else cell(r["ylo"])
            p = wl(r["plo"]) if r["plo"] in P else cell(r["plo"] or "—")
            lvl = f" ({r['level']})" if r.get("level") else ""
            r_cells.append(f"{y} → {p}{lvl}" + (" ⚠" if ylo_mismatch(r) else ""))
        clo_rows.append(r_cells)

    parts = [frontmatter(fm), INFO, "", f"# {code} {c['th']}", ""]
    if c["en"]:
        parts += [f"*{c['en']}*", ""]
    parts += [table(["รายการ", "ข้อมูล"], rows), ""]
    if warns:
        parts += [callout("warning", "ข้อสังเกต", warns), ""]
    parts += ["## คำอธิบายรายวิชา", "", "### ภาษาไทย", "", c["descTh"] or "*ไม่มีในเล่ม*", "",
              "### English", "", c["descEn"] or "*Not provided in the curriculum document*", ""]
    parts += ["## ผลลัพธ์การเรียนรู้รายวิชา (CLO)", ""]
    if clo_rows:
        parts += [table(["n", "CLO", "Bloom"] + [f"{mj}: YLO → PLO" for mj in MAJORS], clo_rows), ""]
        parts += ["*— = ไม่เปิดในวิชาเอกนั้น · ⚠ = PLO ไม่ตรงกับที่ YLO ระบุในข้อ 3.2 · (I/R/M) = ระดับการเรียนรู้ถ้าเล่มระบุ*", ""]
    else:
        parts += ["*ไม่มี CLO ในเล่ม*", ""]
    parts += [f"ดูเพิ่ม: {wl('00_Curriculum_Index', 'ดัชนีหลักสูตร')} · {group_link(c['group'], table=False)}"]
    write(f"Courses/{code}.md", "\n".join(parts))

# ---------------------------------------------------------------- 2. PLO
for p in PLOS:
    pid = p["id"]
    majors = majors_of_scope(p["scope"])
    fm = {"type": "plo", "id": pid, "scope": p["scope"], "major": majors, "name_en": p.get("en") or None,
          "outcome_type": p.get("outcomeType"), "plo": [pid], "generated": True, "source": src("§3.2–3.3, 4.5")}
    rows = [["ขอบเขต", f"{p['scope']} ({SCOPE_TH.get(p['scope'], '')})"],
            ["ชื่อภาษาอังกฤษ", cell(p.get("en")) or "—"],
            ["ประเภทผลลัพธ์", cell(p.get("outcomeType")) or "—"],
            ["จุดเน้น", cell(p.get("focus")) or "—"]]
    warns = []
    if not p.get("en"):
        warns.append("ยังไม่มีชื่อภาษาอังกฤษในเล่ม")
    supp = [y for y in YLOS if pid in y["plos"]]
    by_major = {}
    for mj in majors:
        rws = [r for r in MAP[mj] if r["plo"] == pid]
        by_major[mj] = rws
        if not rws:
            warns.append(f"{mj}: ไม่มี CLO ใดเชื่อมโยงกับ {pid}")
        if not any(r.get("level") == "M" for r in rws):
            warns.append(f"{mj}: ไม่มีรายวิชาที่ระบุระดับ M (Mastery)")
    warns += [x for x in issue_lines(pid) if "ระดับ M" not in x]   # ข้อความ M ซ้ำกับด้านบน

    parts = [frontmatter(fm), INFO, "", f"# {pid}" + (f" {p['en']}" if p.get("en") else ""), "",
             table(["รายการ", "ข้อมูล"], rows), ""]
    if warns:
        parts += [callout("warning", "ข้อสังเกต", warns), ""]
    parts += ["## ผลลัพธ์การเรียนรู้", "", p["th"], ""]
    if p.get("needs") or p.get("sources"):
        parts += ["## ความต้องการของผู้มีส่วนได้ส่วนเสีย", ""]
        parts += [f"- {x}" for x in p.get("needs", [])] + [""]
        if p.get("sources"):
            parts += ["**แหล่งข้อมูล:** " + " · ".join(p["sources"]), ""]
    if p.get("policy"):
        parts += ["## ความสอดคล้องกับนโยบายและแผน", ""]
        parts += [f"- {x}" for x in p["policy"].get("plans", [])] + [""]
        if p["policy"].get("contribution"):
            parts += [f"**การมีส่วนสนับสนุน:** {p['policy']['contribution']}", ""]
    parts += ["## YLO ที่สนับสนุน", ""]
    if supp:
        parts += [table(["YLO", "วิชาเอก", "ชั้นปี", "ผลลัพธ์"],
                        [[wl(y["id"]), y["major"], str(y["year"]), cell(y["th"])] for y in supp]), ""]
    else:
        parts += ["*ไม่มี YLO ที่ระบุว่าสนับสนุน PLO นี้*", ""]
    parts += ["## รายวิชาและ CLO ที่เชื่อมโยง (แผนที่ 4.5)", ""]
    for mj in majors:
        rws = by_major[mj]
        n_courses = len({r["code"] for r in rws})
        lv = defaultdict(int)
        for r in rws:
            lv[r.get("level") or "ไม่ระบุ"] += 1
        lv_txt = " · ".join(f"{k}={v}" for k, v in sorted(lv.items()))
        parts += [f"### วิชาเอก {mj} — {len(rws)} CLO จาก {n_courses} รายวิชา (ระดับ: {lv_txt or '—'})", ""]
        if not rws:
            parts += ["*ไม่มี*", ""]
            continue
        for yr in sorted({r["year"] for r in rws}):
            yr_rows = [r for r in rws if r["year"] == yr]
            parts += [f"#### ปีที่ {yr} — {len(yr_rows)} CLO · {len({r['code'] for r in yr_rows})} วิชา", ""]
            trs = []
            for r in yr_rows:
                trs.append([f"{r['year']}/{r['sem']}",
                            clink(r["code"], show_code=True) if r["code"] else "*(ไม่ระบุรหัสวิชาในเล่ม)*",
                            f"CLO{r['clo']}" if r["clo"] else "—", cell(r["cloText"]),
                            wl(r["ylo"]) if r["ylo"] in Y else cell(r["ylo"]),
                            (r.get("level") or "—") + (" ⚠" if ylo_mismatch(r) else "")])
            parts += [table(["ภาค", "รายวิชา", "CLO", "ข้อความ CLO", "YLO", "ระดับ"], trs), ""]
    parts += ["*⚠ = YLO ที่จับคู่ไม่ได้ระบุว่าสนับสนุน PLO นี้ในข้อ 3.2*", "",
              f"ดูเพิ่ม: {wl('00_Curriculum_Index', 'ดัชนีหลักสูตร')}"]
    write(f"PLO/{pid}.md", "\n".join(parts))

# ---------------------------------------------------------------- 3. YLO
for y in YLOS:
    yid = y["id"]
    majors = majors_of_scope(y["major"])
    fm = {"type": "ylo", "id": yid, "major": majors, "year": y["year"], "plo": y["plos"],
          "generated": True, "source": src("§3.2, 4.5")}
    intro = data.get("yloIntro", {}).get(f"{y['major']}-{y['year']}", "")
    warns = []
    feeds = {mj: [r for r in MAP[mj] if r["ylo"] == yid] for mj in majors}
    for mj in majors:
        if not feeds[mj]:
            warns.append(f"{mj}: ไม่มี CLO ใดเชื่อมโยงกับ YLO นี้ในแผนที่ 4.5")
        other = sorted({r["plo"] for r in feeds[mj] if ylo_mismatch(r)})
        if other:
            warns.append(f"{mj}: แผนที่ 4.5 จับคู่ YLO นี้กับ {', '.join(wl(x) if x in P else x for x in other)} "
                         f"ซึ่งไม่อยู่ใน PLO ที่ระบุในข้อ 3.2")
    warns += issue_lines(yid)
    parts = [frontmatter(fm), INFO, "", f"# {yid}", "",
             table(["รายการ", "ข้อมูล"], [
                 ["วิชาเอก", "ทั้งสองวิชาเอก (IE · SC)" if y["major"] == "ALL" else f"{y['major']} ({MAJOR_TH[y['major']]})"],
                 ["ชั้นปี", str(y["year"])],
                 ["PLO ที่สนับสนุน", ", ".join(wl(x) if x in P else x for x in y["plos"]) or "—"]]), ""]
    if warns:
        parts += [callout("warning", "ข้อสังเกต", warns), ""]
    parts += ["## ผลลัพธ์การเรียนรู้รายปี", "", y["th"], ""]
    if intro:
        parts += [f"> {intro}", ""]
    parts += ["## รายวิชาและ CLO ที่ส่งผลต่อ YLO นี้", ""]
    for mj in majors:
        rws = feeds[mj]
        parts += [f"### วิชาเอก {mj} — {len(rws)} CLO จาก {len({r['code'] for r in rws})} รายวิชา", ""]
        if not rws:
            parts += ["*ไม่มี*", ""]
            continue
        trs = [[f"{r['year']}/{r['sem']}",
                clink(r["code"], show_code=True) if r["code"] else "*(ไม่ระบุรหัสวิชาในเล่ม)*",
                f"CLO{r['clo']}" if r["clo"] else "—", cell(r["cloText"]),
                (wl(r["plo"]) if r["plo"] in P else cell(r["plo"] or "—")) + (" ⚠" if ylo_mismatch(r) else ""),
                r.get("level") or "—"] for r in rws]
        parts += [table(["ภาค", "รายวิชา", "CLO", "ข้อความ CLO", "PLO", "ระดับ"], trs), ""]
    parts += [f"ดูเพิ่ม: {wl('00_Curriculum_Index', 'ดัชนีหลักสูตร')}"]
    write(f"YLO/{yid}.md", "\n".join(parts))

# ---------------------------------------------------------------- 4. plans
ELECTIVE_GROUPS = [g["id"] for g in data["groups"] if g["cat"] == "pe"]


def placeholder_note(e):
    code = e["code"]
    if code.startswith("GE-002"):
        return "เลือกจาก " + group_link("ge-elec")
    if "ชีพเลือก" in e.get("category", "") or code.startswith("EN-788-14"):
        return "เลือกจาก " + ", ".join(group_link(g) for g in ELECTIVE_GROUPS)
    if "เสรี" in e.get("category", "") or "เสรี" in e.get("name", ""):
        return "วิชาใดก็ได้ในมหาวิทยาลัย"
    return ""


plan_totals = {}
for mj in MAJORS:
    sems = data["plans"].get(mj, [])
    cum = 0
    parts_body = []
    warns = []
    for s in sems:
        tot = sum(credit_units(e["credits"]) for e in s["courses"])
        cum += tot
        trs = []
        for e in s["courses"]:
            if e["code"] in C:
                code_cell, name_cell = wl(e["code"]), cell(C[e["code"]]["th"])
            else:
                code_cell = cell(e["code"])
                extra = placeholder_note(e)
                name_cell = cell(e["name"]) + (f" ({extra})" if extra else "")
            trs.append([code_cell, name_cell, link_codes_in(e.get("prereq") or "") or "—", cell(e["credits"])])
        parts_body += [f"## ปีที่ {s['year']} ภาคการศึกษาที่ {s['sem']}", "",
                       table(["รหัสวิชา", "ชื่อวิชา", "วิชาบังคับก่อน", "หน่วยกิต"], trs), "",
                       f"**รวม {tot} หน่วยกิต** · สะสม {cum} หน่วยกิต"
                       + (f" (เล่มระบุ {s['credits']}/{s['cumulative']})" if (s.get("credits"), s.get("cumulative")) != (tot, cum) else ""),
                       ""]
        if s.get("credits") is not None and s["credits"] != tot:
            warns.append(f"ปี {s['year']} ภาค {s['sem']}: รวมจากรายการ {tot} ≠ เล่มระบุ {s['credits']}")
        if s.get("cumulative") is not None and s["cumulative"] != cum:
            warns.append(f"ปี {s['year']} ภาค {s['sem']}: สะสมคำนวณได้ {cum} ≠ เล่มระบุ {s['cumulative']}")
    plan_totals[mj] = cum
    if cum != meta.get("totalCredits"):
        warns.append(f"หน่วยกิตรวมทั้งแผน {cum} ≠ {meta.get('totalCredits')}")
    warns += issue_lines("PLAN")
    fm = {"type": "plan", "id": f"Plan_{mj}", "major": [mj], "semesters": len(sems), "total_credits": cum,
          "generated": True, "source": src("§4.4")}
    srows, c2 = [], 0
    for s in sems:
        t = sum(credit_units(e["credits"]) for e in s["courses"])
        c2 += t
        srows.append([wl(f"Plan_{mj}#ปีที่ {s['year']} ภาคการศึกษาที่ {s['sem']}", f"ปี {s['year']} ภาค {s['sem']}", True),
                      str(t), str(c2)])
    parts = [frontmatter(fm), INFO, "", f"# แผนการเรียนปกติ วิชาเอก{MAJOR_TH[mj]} ({mj})", "",
             table(["ชั้นปี/ภาค", "หน่วยกิต", "สะสม"], srows), ""]
    if warns:
        parts += [callout("warning", "ข้อสังเกต", warns), ""]
    parts += parts_body + [f"ดูเพิ่ม: {wl('00_Curriculum_Index', 'ดัชนีหลักสูตร')}"]
    write(f"Plans/Plan_{mj}.md", "\n".join(parts))

# ---------------------------------------------------------------- 5. faculty
fac = data.get("faculty", [])
frows = [[str(f["no"]), cell(f["position"]), cell(f["name"]), cell(f["degrees"]), cell(f["institutions"]),
          cell(f["years"]), cell(f["match"]), "✓" if f["responsible"] else "—", f.get("major") or "—",
          "✓" if f.get("chair") else "—"] for f in fac]
fm = {"type": "faculty", "id": "Faculty", "major": MAJORS, "count": len(fac),
      "responsible_count": sum(1 for f in fac if f["responsible"]), "generated": True, "source": src("หมวด 1 ข้อ 1.3")}
fwarns = []
for f in fac:
    if f["responsible"] and not f.get("major"):
        fwarns.append(f"ลำดับ {f['no']} เป็นผู้รับผิดชอบหลักสูตรแต่ไม่ระบุวิชาเอก")
parts = [frontmatter(fm), INFO, "", "# อาจารย์ประจำหลักสูตร", "",
         "ข้อมูลเฉพาะตำแหน่งวิชาการ ชื่อ และคุณวุฒิตามเล่ม (ไม่มีและไม่เก็บเลขประจำตัวหรือข้อมูลติดต่อส่วนบุคคล)", "",
         table(["ลำดับ", "ตำแหน่งวิชาการ", "ชื่อ", "คุณวุฒิ", "สถาบัน", "ปีที่จบ", "ตรงสาขา",
                "ผู้รับผิดชอบหลักสูตร", "วิชาเอก", "ประธานหลักสูตร"], frows), ""]
if fwarns:
    parts += [callout("warning", "ข้อสังเกต", fwarns), ""]
parts += [f"ผู้รับผิดชอบหลักสูตร {fm['responsible_count']} คน · "
          + " · ".join(f"{mj} {sum(1 for f in fac if f.get('major') == mj)} คน" for mj in MAJORS), "",
          f"ดูเพิ่ม: {wl('00_Curriculum_Index', 'ดัชนีหลักสูตร')}"]
write("Faculty/Faculty.md", "\n".join(parts))

# ---------------------------------------------------------------- 6. skill sets
hdr = data["skillSets"].get("header") or []
COLS = {"code": 0, "name": 1, "group": 2, "type": 3, "sub": 4, "clos": 5, "assess": 6}
for i, h in enumerate(hdr):
    for key, kw in (("code", "รหัสทักษะ"), ("name", "ชื่อชุดทักษะ"), ("group", "กลุ่มทักษะ"), ("type", "ประเภท"),
                    ("sub", "ทักษะย่อย"), ("clos", "CLO"), ("assess", "วิธีการวัด")):
        if kw in h and key not in [k for k, v in COLS.items() if v == i and k != key]:
            COLS[key] = i
HLABEL = {k: (hdr[i] if i < len(hdr) else k) for k, i in COLS.items()}

skills = defaultdict(list)
for row in data["skillSets"].get("rows", []):
    skills[row[COLS["code"]].strip()].append(row)


def parse_clo_refs(text):
    refs, bad = [], []
    for m in re.finditer(r"([^,()]+?)\s*\(\s*((?:CLO\s*\d+\s*,?\s*)+)\)", text):
        name = m.group(1).strip()
        nums = [int(x) for x in re.findall(r"\d+", m.group(2))]
        code = NAME2CODE.get(re.sub(r"\s+", "", name))
        if not code:
            bad.append(f"ไม่พบรายวิชาชื่อ \"{name}\"")
            continue
        for n in nums:
            refs.append((code, n))
            if n not in [cl["n"] for cl in C[code]["clos"]]:
                bad.append(f"{code} ไม่มี CLO{n}")
    return refs, bad


def split_subskills(text):
    items = [t.strip() for t in re.split(r"(?:^|\s)(?=\d+\.\s)", text) if t.strip()]
    return items or [text]


SUB_RE = re.compile(r"^(\d+)\.\s*(.*?)\s*[—–-]\s*(ระดับ\s*\d+(?:\s*\([^)]*\))?)\s*:\s*(.*)$", re.S)
for code in sorted(skills, key=lambda k: (["LE", "IE", "SC"].index(k[:2]) if k[:2] in ("LE", "IE", "SC") else 9, k)):
    rows = skills[code]
    first = rows[0]
    scope = code[:2]
    majors = majors_of_scope(scope if scope != "LE" else "LE")
    subs_out, all_refs, warns = [], [], []
    for row in rows:
        refs, bad = parse_clo_refs(row[COLS["clos"]])
        warns += bad
        all_refs += refs
        assess = row[COLS["assess"]] if COLS["assess"] < len(row) else ""
        for item in split_subskills(row[COLS["sub"]]):
            m = SUB_RE.match(item)
            if m:
                title, level, desc = f"{m.group(1)}. {m.group(2)}", m.group(3), m.group(4)
            else:
                title, level, desc = item, "", ""
            block = [f"### {title}", ""]
            if level:
                block += [f"- **ระดับความเชี่ยวชาญ:** {level}"]
            if desc:
                block += [f"- **คำอธิบาย:** {desc}"]
            block += ["- **CLO ที่เกี่ยวข้อง:**"]
            for (cc, n) in refs:
                cl = next((x for x in C[cc]["clos"] if x["n"] == n), None)
                block += [f"    - {wl(cc, C[cc]['th'])} CLO{n}" + (f" — {cl['th']}" if cl else " ⚠ ไม่มี CLO นี้ในรายวิชา")]
            if not refs:
                block += [f"    - {row[COLS['clos']] or '—'}"]
            am = re.match(r"^\s*เครื่องมือ\s*:\s*(.*?)\s*การประเมิน\s*:\s*(.*)$", assess, re.S)
            if am:
                block += [f"- **เครื่องมือ:** {am.group(1)}", f"- **การประเมิน:** {am.group(2)}"]
            elif assess:
                block += [f"- **{HLABEL['assess']}:** {assess}"]
            subs_out += block + [""]
    plos = sorted({MAP_BY[(mj, cc, n)]["plo"] for (cc, n) in all_refs for mj in majors
                   if (mj, cc, n) in MAP_BY and MAP_BY[(mj, cc, n)]["plo"] in P})
    rcourses = list(dict.fromkeys(cc for cc, _ in all_refs))
    warns += issue_lines(code)
    fm = {"type": "skill", "code": code, "name": first[COLS["name"]], "skill_group": first[COLS["group"]],
          "skill_type": first[COLS["type"]], "major": majors, "plo": plos, "courses": rcourses,
          "generated": True, "source": src("§4.6")}
    parts = [frontmatter(fm), INFO, "", f"# {code} {first[COLS['name']]}", "",
             table(["รายการ", "ข้อมูล"], [
                 [cell(HLABEL["group"]), cell(first[COLS["group"]])],
                 [cell(HLABEL["type"]), cell(first[COLS["type"]])],
                 ["วิชาเอก", "ทั้งสองวิชาเอก (IE · SC)" if scope == "LE" else f"{scope} ({MAJOR_TH.get(scope, '')})"],
                 ["รายวิชาที่เกี่ยวข้อง", ", ".join(clink(cc) for cc in rcourses) or "—"],
                 ["PLO (ผ่าน CLO ในแผนที่ 4.5)", ", ".join(wl(x) for x in plos) or "—"]]), ""]
    if warns:
        parts += [callout("warning", "ข้อสังเกต", list(dict.fromkeys(warns))), ""]
    parts += [f"## {HLABEL['sub']}", ""] + subs_out + [f"ดูเพิ่ม: {wl('00_Curriculum_Index', 'ดัชนีหลักสูตร')}"]
    write(f"Skills/{code}.md", "\n".join(parts))

# ---------------------------------------------------------------- 7. groups
for g in data["groups"]:
    gc = [C[x] for x in g["courses"] if x in C]
    listed = sum(credit_units(c["credits"]) for c in gc)
    fm = {"type": "group", "id": g["id"], "category": g["cat"], "major": [g["major"]] if g.get("major") else MAJORS,
          "credits_required": g["credits"], "course_count": len(gc), "generated": True, "source": src("§4.2")}
    trs = [[wl(c["code"]), cell(c["th"]), cell(c["en"]), cell(c["credits"]),
            plan_link(c, "IE") if "IE" in c["majors"] else "—",
            plan_link(c, "SC") if "SC" in c["majors"] else "—", str(len(c["clos"]))] for c in gc]
    info = [["หมวด", CAT_TH.get(g["cat"], g["cat"])], ["หน่วยกิตที่ต้องเรียน", str(g["credits"])],
            ["หน่วยกิตรวมของรายวิชาในกลุ่ม", str(listed)], ["จำนวนรายวิชา", str(len(gc))]]
    if g.get("pick"):
        info.append(["เงื่อนไข", cell(g["pick"])])
    if g.get("major"):
        info.append(["วิชาเอก", f"{g['major']} ({MAJOR_TH[g['major']]})"])
    warns = []
    if not g.get("pick") and g["cat"] != "pe" and listed != g["credits"]:
        warns.append(f"หน่วยกิตรวมของรายวิชา {listed} ≠ หน่วยกิตที่กำหนด {g['credits']}")
    if g["cat"] == "pe":
        warns.append("กลุ่มวิชาชีพเลือกทั้ง 4 กลุ่มใช้เงื่อนไขร่วม เลือกเรียนรวม 3 หน่วยกิต และไม่ได้ผูกกับวิชาเอก")
    parts = [frontmatter(fm), INFO, "", f"# {g['th']}", "", table(["รายการ", "ข้อมูล"], info), ""]
    if warns:
        parts += [callout("warning", "ข้อสังเกต", warns), ""]
    parts += ["## รายวิชา", "", table(["รหัสวิชา", "ชื่อวิชา", "English", "หน่วยกิต", "แผน IE", "แผน SC", "CLO"], trs), "",
              f"ดูเพิ่ม: {wl('00_Curriculum_Index', 'ดัชนีหลักสูตร')}"]
    write(f"Groups/{g['id']}.md", "\n".join(parts))

# ---------------------------------------------------------------- 7b. หมวด 5–9 : การสอน · การประเมิน · เนื้อหาเล่ม
extra_links = []
STRATS = data.get("strategies") or []
ASSESS = data.get("assessment") or []
TEACH = data.get("teachByPlo") or []
YASSESS = data.get("yloAssessment") or []
DOCS = data.get("docs") or {}
if not (STRATS and ASSESS and TEACH and DOCS):
    raise SystemExit("ERROR: curriculum.json ไม่มีข้อมูลหมวด 5–9 — รัน tools/extract_curriculum.py รุ่นล่าสุดก่อน")
plo_ids = [p["id"] for p in PLOS]
gen_head = lambda typ, sec: frontmatter({"type": typ, "generated": True, "source": src(sec)}) + \
    "> [!info] สร้างอัตโนมัติจากเล่มหลักสูตร — ห้ามแก้ไฟล์นี้ แก้ที่ overrides/ หรือเล่ม .docx\n\n"
short_name = lambda s: re.sub(r"\s*\(.*$", "", s)

# กลยุทธ์การสอน
rows = [[cell(short_name(s["name"]))] + ["●" if p in s["plos"] else "" for p in plo_ids] for s in STRATS]
rows.append(["**จำนวนกลยุทธ์**"] + [str(sum(p in s["plos"] for s in STRATS)) for p in plo_ids])
body = [gen_head("teaching-strategies", "หมวด 5.2"), "# กลยุทธ์การจัดการเรียนการสอน (หมวด 5.2)", "",
        "## ความครอบคลุม PLO", "", table(["กลยุทธ์"] + [wl(p, p.replace("PLO_", ""), table=True) for p in plo_ids], rows), ""]
for i, s in enumerate(STRATS, 1):
    body += [f"## {i}. {s['name']}", "",
             "PLO: " + (" · ".join(wl(p) for p in s["plos"]) or "—"), "",
             f"- **การดำเนินการ:** {s['detail']}", f"- **รายวิชาที่เกี่ยวข้อง:** {link_codes_in(s['courses'], table=False)}",
             f"- **เครื่องมือ/กิจกรรม:** {s['tools']}", f"- **ผลลัพธ์ที่คาดหวัง:** {s['outcome']}", ""]
write("Teaching/Teaching_Strategies.md", "\n".join(body))

# วิธีสอน/ประเมินราย PLO (5.1)
body = [gen_head("teaching-by-plo", "หมวด 5.1"), "# วิธีสอนและวิธีประเมินราย PLO (หมวด 5.1)", "",
        table(["PLO", "วิธีการจัดการเรียนการสอน", "วิธีการประเมินผล"],
              [[wl(t["plo"], table=True), cell(t["teach"]), cell(t["assess"])] for t in TEACH])]
write("Teaching/Teaching_by_PLO.md", "\n".join(body))

# การประเมินราย PLO แยกวิชาเอก (6.1)
for mj in MAJORS:
    body = [frontmatter({"type": "assessment", "major": mj, "generated": True, "source": src("หมวด 6.1")}),
            "> [!info] สร้างอัตโนมัติจากเล่มหลักสูตร — ห้ามแก้ไฟล์นี้ แก้ที่ overrides/ หรือเล่ม .docx\n",
            f"# วิธีประเมินราย PLO · วิชาเอก {mj} (หมวด 6.1)", ""]
    for p in PLOS:
        if p["scope"] not in ("LE", mj):
            continue
        rs = [a for a in ASSESS if a["plo"] == p["id"] and mj in a["majors"]]
        tot = sum(a["weight"] or 0 for a in rs)
        body += [f"## {wl(p['id'])} · รวม {tot}%", "",
                 table(["วิธีการประเมิน", "รูปแบบ", "น้ำหนัก", "ช่วงเวลา", "ผู้ประเมิน", "เกณฑ์ผ่าน"],
                       [[cell(a["method"]), cell(a["format"]), f"{a['weight']}%", cell(a["when"]), cell(a["assessor"]), cell(a["pass"])] for a in rs]), ""]
        if tot != 100:
            body += [callout("warning", "น้ำหนักรวมไม่เท่ากับ 100%", [f"รวม {tot}%"]), ""]
    write(f"Teaching/Assessment_{mj}.md", "\n".join(body))

# จุดประเมิน YLO (8.2)
body = [gen_head("ylo-assessment", "หมวด 8.2"), "# จุดประเมิน YLO รายชั้นปี (หมวด 8.2)", ""]
for y in (1, 2, 3, 4):
    rs = [a for a in YASSESS if a["year"] == y]
    if rs:
        body += [f"## ชั้นปีที่ {y}", "", table(["YLO", "วิธีวัดผล", "เครื่องมือประเมิน", "เกณฑ์"],
                 [[wl(ylo_id(a["ylo"]), table=True), cell(a["method"]), cell(a["tool"]), cell(a["criteria"])] for a in rs]), ""]
write("Teaching/YLO_Assessment.md", "\n".join(body))

# เนื้อหาหมวด 5–9 ตามลำดับในเล่ม
for n in ("5", "6", "7", "8", "9"):
    doc = DOCS[n]
    body = [gen_head("book-chapter", f"หมวดที่ {n}"), f"# หมวดที่ {n} {doc['title']}", ""]
    for b in doc["blocks"]:
        if b["t"] == "h":
            body += ["#" * min(b["lvl"] + 1, 5) + " " + b["text"], ""]
        elif b["t"] == "p":
            body += [b["text"], ""]
        else:
            w = len(b["header"])
            body += [table([cell(h) for h in b["header"]], [[cell(c) for c in (r + [""] * w)[:w]] for r in b["rows"]]), ""]
    write(f"Book/Book_Ch{n}.md", "\n".join(body))

extra_links = [
    f"- {wl('Teaching_Strategies', f'กลยุทธ์การสอน {len(STRATS)} แบบ')} · {wl('Teaching_by_PLO', 'วิธีสอน/ประเมินราย PLO')}",
    f"- {wl('Assessment_IE', 'วิธีประเมินราย PLO · IE')} · {wl('Assessment_SC', 'วิธีประเมินราย PLO · SC')} · {wl('YLO_Assessment', 'จุดประเมิน YLO')}",
    "- เนื้อหาเล่ม: " + " · ".join(wl(f"Book_Ch{n}", f"หมวด {n}") for n in ("5", "6", "7", "8", "9")),
]

# ---------------------------------------------------------------- 8. index
STRUCT_GROUPS = {
    "กลุ่มวิชาบังคับ": ["ge-req"], "กลุ่มวิชาเลือก": ["ge-elec"],
    "กลุ่มวิชาพื้นฐานวิทยาศาสตร์และคณิตศาสตร์": ["sci"], "กลุ่มวิชาพื้นฐานวิศวกรรมศาสตร์": ["engfund"],
    "วิชาชีพบังคับร่วม": ["core"], "วิชาชีพบังคับของวิชาเอก": ["ie", "sc"],
    "กลุ่มวิชาเสริมสร้างประสบการณ์ในวิชาชีพ": ["exp"], "กลุ่มวิชาชีพเลือก": ELECTIVE_GROUPS,
}
LEVEL3 = {"วิชาชีพบังคับร่วม", "วิชาชีพบังคับของวิชาเอก"}
srows, top_sum = [], 0
for s in data["structure"]:
    top = bool(re.match(r"^\d+\.\d+\s", s["label"]))
    if top:
        top_sum += s["credits"]
    indent = "" if top else ("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" if s["label"] in LEVEL3 else "&nbsp;&nbsp;&nbsp;")
    label = f"**{s['label']}**" if top else indent + cell(s["label"])
    links = ", ".join(group_link(g) for g in STRUCT_GROUPS.get(s["label"], []) if g in G)
    srows.append([label, f"**{s['credits']}**" if top else str(s["credits"]), links or ("—" if not top else "")])
srows.append(["**รวมตลอดหลักสูตร**", f"**{top_sum}**", ""])
if top_sum != meta.get("totalCredits"):
    raise SystemExit(f"ERROR: หน่วยกิตระดับหมวดรวม {top_sum} ≠ {meta.get('totalCredits')}")

n_clo = sum(len(c["clos"]) for c in courses)
counts = {
    "รายวิชา (Courses)": len(courses), "CLO": n_clo, "PLO": len(PLOS), "YLO": len(YLOS),
    "แผนการเรียน (Plans)": len(MAJORS), "ชุดทักษะ (Skills)": len(skills), "กลุ่มวิชา (Groups)": len(data["groups"]),
    "อาจารย์ (Faculty)": len(fac), "รายวิชาที่มีข้อสังเกต": n_course_warn,
}
mrows = []
for m in meta["majors"]:
    mj = m["id"]
    mrows.append([mj, cell(m["th"]), cell(m["en"]), wl(f"Plan_{mj}", f"แผน {mj}", True),
                  str(sum(1 for c in courses if mj in c["majors"])),
                  str(sum(1 for p in PLOS if p["scope"] in ("LE", mj))),
                  str(sum(1 for y in YLOS if y["major"] in ("ALL", mj))), str(len(MAP[mj])), str(plan_totals.get(mj, 0))])
grows = [[group_link(g["id"]), CAT_TH.get(g["cat"], g["cat"]), str(g["credits"]), str(len(g["courses"])),
          g.get("major") or "IE · SC"] for g in data["groups"]]
crows = [[wl(c["code"]), cell(c["th"]), cell(c["credits"]), group_link(c["group"]),
          plan_link(c, "IE") if "IE" in c["majors"] else "—", plan_link(c, "SC") if "SC" in c["majors"] else "—",
          str(len(c["clos"]))] for c in courses]
prows = [[wl(p["id"]), p["scope"], cell(p.get("en")) or "*(ยังไม่มีชื่อภาษาอังกฤษ)*", cell(p.get("outcomeType")),
          str(sum(1 for mj in MAJORS for r in MAP[mj] if r["plo"] == p["id"]))] for p in PLOS]
yrows = [[wl(y["id"]), y["major"], str(y["year"]), ", ".join(wl(x, table=True) for x in y["plos"] if x in P),
          str(sum(1 for mj in MAJORS for r in MAP[mj] if r["ylo"] == y["id"]))] for y in YLOS]
krows = [[wl(k), cell(v[0][COLS["name"]]), cell(v[0][COLS["type"]]), str(sum(len(split_subskills(r[COLS["sub"]])) for r in v))]
         for k, v in sorted(skills.items(), key=lambda kv: (["LE", "IE", "SC"].index(kv[0][:2]), kv[0]))]

fm = {"type": "index", "id": "00_Curriculum_Index", "major": MAJORS, "total_credits": top_sum,
      "courses": len(courses), "clos": n_clo, "plos": len(PLOS), "ylos": len(YLOS), "generated": True,
      "source": src("หมวด 1, 3, 4")}
parts = [frontmatter(fm), INFO, "",
         f"# {meta['nameTh']}", "",
         f"*{meta['nameEn']}* · {meta['degreeThShort']} · {meta['revision']} · {meta['faculty']} {meta['university']}", "",
         f"กลับ {wl('00_Home', 'หน้าแรกวอลต์')} · ข้อสังเกตทั้งหมด {wl(REGISTER_NOTE, 'ทะเบียนข้อสังเกต')}", "",
         "## จำนวนโน้ต", "", table(["รายการ", "จำนวน"], [[k, str(v)] for k, v in counts.items()]), "",
         "## โครงสร้างหลักสูตร", "", table(["หมวด/กลุ่มวิชา", "หน่วยกิต", "โน้ตกลุ่มวิชา"], srows), "",
         f"หน่วยกิตรวมระดับหมวด = {' + '.join(str(s['credits']) for s in data['structure'] if re.match(r'^\d+\.\d+\s', s['label']))} = **{top_sum}**", "",
         "## วิชาเอก", "",
         table(["รหัส", "วิชาเอก", "English", "แผนการเรียน", "รายวิชาที่เรียนได้", "PLO", "YLO", "แถวแผนที่ CLO", "หน่วยกิตตามแผน"], mrows), "",
         "## แผนการเรียนและอาจารย์", "",
         f"- {wl('Plan_IE', 'แผนการเรียน วิชาเอก IE')}",
         f"- {wl('Plan_SC', 'แผนการเรียน วิชาเอก SC')}",
         f"- {wl('Faculty', 'อาจารย์ประจำหลักสูตร')} ({len(fac)} คน)", "",
         "## การสอน การประเมิน และเนื้อหาหมวด 5–9", "", *extra_links, "",
         "## กลุ่มวิชา", "", table(["กลุ่มวิชา", "หมวด", "หน่วยกิตที่ต้องเรียน", "จำนวนวิชา", "วิชาเอก"], grows), "",
         "## ผลลัพธ์การเรียนรู้ระดับหลักสูตร (PLO)", "", table(["PLO", "ขอบเขต", "ชื่อภาษาอังกฤษ", "ประเภท", "แถวแผนที่"], prows), "",
         "## ผลลัพธ์การเรียนรู้รายปี (YLO)", "", table(["YLO", "วิชาเอก", "ชั้นปี", "PLO", "แถวแผนที่"], yrows), "",
         "## ชุดทักษะ (Skill Sets)", "", table(["รหัส", "ชื่อชุดทักษะ", "ประเภท", "ทักษะย่อย"], krows), "",
         "## รายวิชาทั้งหมด", "", table(["รหัสวิชา", "ชื่อวิชา", "หน่วยกิต", "กลุ่มวิชา", "แผน IE", "แผน SC", "CLO"], crows), ""]
if oddities:
    parts += [callout("warning", "ข้อสังเกตจากแผนที่ CLO→YLO→PLO (4.5)", [f"{k}: {v} แถว" for k, v in sorted(oddities.items())]), ""]
write("00_Curriculum_Index.md", "\n".join(parts))

# ---------------------------------------------------------------- summary
names = [Path(r).stem for r in written]
dups = {n for n in names if names.count(n) > 1}
others = {p.stem for p in VAULT.rglob("*.md") if OUT not in p.parents}
clash = sorted(set(names) & others)
if dups or clash:
    raise SystemExit(f"ERROR: ชื่อไฟล์ซ้ำ {sorted(dups)} {clash}")

by_dir = defaultdict(int)
for r in written:
    by_dir[r.split("/")[0] if "/" in r else "(root)"] += 1
print("build_vault: wrote", len(written), "notes →", OUT.relative_to(ROOT).as_posix())
print("  " + " ".join(f"{k}={v}" for k, v in sorted(by_dir.items())))
print(f"  courses={len(courses)} clos={n_clo} plos={len(PLOS)} ylos={len(YLOS)} skills={len(skills)} "
      f"groups={len(data['groups'])} faculty={len(fac)} plans={len(MAJORS)} credits={top_sum} "
      f"courses_with_warnings={n_course_warn} register_rows={len(REG_IDS)}")
for k, v in sorted(oddities.items()):
    print(f"  oddity: {k}: {v}")
