---
tags: [tutorial, build]
step: 2/14
---

# ขั้นที่ 2 · ดึงข้อมูลจากเล่ม → curriculum.json → วอลต์และเว็บ

> **เป้าหมาย: ให้เล่ม .docx กลายเป็นข้อมูลที่นับได้ตรงกับเล่ม แล้วกระจายเป็นหนึ่งโน้ตต่อหนึ่งรหัส โดยไม่แก้คำผิดของเล่มแบบเงียบ ๆ**

## หลังจบขั้นนี้ต้องได้อะไร

| เมนู | เส้นทาง | เนื้อหา |
|---|---|---|
| (ยังไม่มีหน้าใหม่) | ทุกหน้า | ชิปบนหัวเว็บอ่านจากข้อมูลจริง · tooltip รหัส (FR-20) เริ่มทำงาน |
| วอลต์ | `LE_Vault/10_Curriculum/**` | โน้ตอัตโนมัติ 90 รายวิชา · 13 PLO · 27 YLO · 6 ชุดทักษะ · 7 อาจารย์ |
| ข้อมูลเว็บ | `web/src/generated/*.js` | โมดูลข้อมูลทุกตัวที่ขั้น 3–14 ใช้ |

**SRS ที่ครอบคลุม:** DP-01 · DP-02 · DP-03 · DP-07 · DP-08 · VR-01 · VR-02 · VR-03 · VR-06 · NFR-06 · NFR-08 ดู [[03_SRS_Curriculum_Website]] และสถานะ field ใน [[02_Checklist_Web_Data]]

---

## ข้อมูลจริงของหลักสูตรนี้

**ต้นทาง** `../doc_ref/วศ.บ.โลจิสติกส์ 70.docx` (นอก `LE_web/` หนึ่งชั้น) → ตัวดึง `tools/extract_curriculum.py` → `data/curriculum.json`

**วิธีของตัวดึง (ทำซ้ำได้ทุกครั้งที่เล่มเปลี่ยน)**

1. **แปลงเอกสารเป็นลำดับบรรทัด** เดินตาม `body` ของ docx ตามลำดับจริง ย่อหน้า = string หนึ่งบรรทัด ตาราง = `"<TABLE>"` ตามด้วยแถวละหนึ่ง list ของเซลล์ แล้ว `"</TABLE>"` เซลล์ที่ merge กันจะถูกตัดซ้ำด้วยการเทียบ `_tc`
2. **หาหัวข้อเป็นจุดยึด (anchor)** แล้วตัดช่วงบรรทัดระหว่างหัวข้อ

| anchor (ข้อความขึ้นต้นตรงตามเล่ม) | ได้อะไร |
|---|---|
| `หมวดที่ 1` … `หมวดที่ 9` | ขอบเขตของแต่ละหมวด |
| `4.2 รายวิชา` | รหัส ชื่อ หน่วยกิต และกลุ่มวิชา |
| `4.3 คำอธิบายรายวิชา` | คำอธิบายไทย/อังกฤษ วิชาบังคับก่อน **และ CLO + Bloom** |
| `4.4 แผนการเรียน` | แผน 8 ภาค × 2 วิชาเอก พร้อมยอดรายภาค/สะสม |
| `4.5 แผนที่แสดงความเชื่อมโยง` | แถว CLO → YLO → PLO (ระดับ) แยกวิชาเอก |
| `4.6 ชุดทักษะ` | แถวชุดทักษะ `LE-SK` `IE-SK` `SC-SK` |
| `3.1 ปรัชญา` · `3.2 ผลลัพธ์การเรียนรู้ระดับหลักสูตร` · `3.3` · `3.4 กิจกรรมเสริม` | ปรัชญา วัตถุประสงค์ PLO YLO ตารางความสอดคล้อง กิจกรรม |
| `1.2 แผนการรับนักศึกษา` · `1) อาจารย์ผู้รับผิดชอบหลักสูตร` · `อาจารย์ประจำหลักสูตรและคุณสมบัติ` · `7) อาชีพที่สามารถประกอบได้` | แผนรับ อาจารย์ อาชีพ |

3. **จับแถวด้วย pattern** รหัสวิชา `^[A-Z]{2}-\d{3}-\d{5}$` · หน่วยกิต `^\d+\(\d+-\d+-\d+\)$` · CLO `^CLO\s*(\d+)` · ระดับในช่อง PLO `\(([IRMA])\)` · PLO `^PLO_(LE|IE|SC)(\d)\s+` · YLO `^((IE|SC)-)?YLO(\d)\.(\d)\s+` · บรรทัดแผน "ปีการศึกษาที่ n" "ภาคการศึกษาที่ n" "รวมหน่วยกิตลงทะเบียนเรียน n" "รวมจำนวนหน่วยกิตสะสม n" · ชื่ออาจารย์ลงท้าย `*` = ผู้รับผิดชอบหลักสูตร
4. **ไม่แก้ข้อความของเล่ม** สิ่งที่ผิดให้บันทึกลง `issues[]` แทน

**ตัวเลขอ้างอิงที่ต้องได้ (ตรวจจาก curriculum.json รอบล่าสุด)**

| รายการ | ค่า | รายการ | ค่า |
|---|---:|---|---:|
| `courses` | 90 | `plans.IE` / `plans.SC` | 8 / 8 ภาค |
| CLO รวม | 254 | `mapping.IE` / `mapping.SC` | 137 / 120 แถว |
| `plos` | 13 | `faculty` | 7 |
| `ylos` | 27 | `skillSets.rows` | 18 แถว (6 ชุด × 3) |
| `activities.rows` | 3 | `issues` | 19 |

`issues[]` ทั้ง 19 ข้อ = 2 ข้อจาก 4.2 (`NS-531-1100` รหัสขาดหลัก, `EN-788-13009` ซ้ำในกลุ่ม ie) + 17 ข้อ "ไม่มีรายวิชาที่ระบุระดับ M" (IE 9 PLO + SC 8 PLO)

**สิ่งที่ตัวดึงยังไม่บันทึกเป็น issue** (ให้ `build-data.mjs` ตรวจเพิ่มเป็น issue ประเภท `derived`)

| ตรวจอะไร | ผลในเล่มนี้ |
|---|---|
| `descTh`/`descEn` ว่าง | `GE-002-14003`, `GE-002-14013` (ไทย+อังกฤษ) · `GE-002-14015` (อังกฤษ) |
| `cloText` ใน 4.5 ≠ ข้อความ CLO ใน 4.3 | `EN-788-13018` 5 แถว (เป็น CLO ของ 13010) |
| CLO ข้อความเหมือนกันข้ามรายวิชา | `EN-788-13012#CLO2` = `13013#CLO2` · `NS-531-11002` กับ `NS-533-11002` CLO3–4 (ต้องให้คนตัดสิน) |
| แถว 4.5 ที่ไม่มีรหัสวิชา | 1 แถวใน SC (CLO2 ของ 13012) |
| ค่า YLO สะกดเพี้ยน | `"YLO4.3 ("` 1 แถวใน IE |
| วิชาบังคับก่อนที่รหัสไม่ครบรูป | `EN-788-14006` อ้าง `EN-001-007` (regex `\d{4,5}` จับไม่ได้ จึงไม่มีทั้งลิงก์และ issue) |
| คำอธิบายอังกฤษซ้ำสองรอบ | `EN-788-13015` (ซ้ำที่ตำแหน่ง 669 จาก 1,338 ตัวอักษร) |

---

## Prompt A · วอลต์

```text
ส่วนที่ 1 — ตัวดึง tools/extract_curriculum.py (ราก = LE_web/)
ถ้ามีไฟล์อยู่แล้ว ให้ตรวจว่าผ่านข้อกำหนดนี้ ถ้าไม่ผ่านให้แก้เฉพาะจุด
- python tools/extract_curriculum.py [path.docx] ค่าเริ่มต้น ../doc_ref/วศ.บ.โลจิสติกส์ 70.docx
- แปลง docx เป็นลำดับบรรทัด แล้วตัดช่วงด้วย anchor ตามตารางในขั้นที่ 2
- ถ้าหา anchor ไม่พบ ให้ raise ValueError ที่ "ระบุข้อความหัวข้อที่หาไม่พบ" (DP-02)
- throw error ถ้า parse ได้ 0 รายการในส่วนใดส่วนหนึ่ง (courses, clos, plans, mapping, plos, ylos, faculty)
- ไม่แก้คำผิดของเล่ม ให้บันทึกลง issues[] เป็น {where, code?, note}
- รหัสที่ขาดหลัก (^[A-Z]{2}-\d{3}-\d{3,4}$) ให้เก็บรหัสที่แก้แล้วพร้อม codeAsPrinted และบันทึก issue
- รหัสซ้ำในตาราง 4.2 ให้ข้ามแถวที่สองและบันทึก issue
- รองรับ 2 วิชาเอก: plans และ mapping เป็น {IE:[], SC:[]} · CLO.map เป็น {IE:{ylo,plo,level}, SC:{...}}
- เขียน data/curriculum.json (UTF-8, ensure_ascii=False) แล้วพิมพ์บรรทัดสรุป
  courses= clos= plos= ylos= planIE= planSC= mapIE= mapSC= faculty= skills= activities= issues=

ส่วนที่ 2 — สร้าง tools/build_vault.py
อ่าน data/curriculum.json (และ LE_Vault/overrides/*.md) แล้วเขียนโน้ตลง LE_Vault/10_Curriculum/
- Courses/<code>.md 90 ไฟล์ · PLO/<id>.md 13 · YLO/<id>.md 27 · skills/<code>.md 6 · Faculty/FAC-0n.md 7
- ชื่อไฟล์ = รหัส (VR-01) เช่น EN-788-12001.md, PLO_IE3.md, IE-YLO2.1.md, YLO4.3.md, SC-SK01.md
- frontmatter ทุกโน้ต (VR-02)
    type: course|plo|ylo|skillset|faculty · code · major: [IE, SC] หรือ [IE] หรือ [ALL]
    year: [ชั้นปีจากแผนของแต่ละวิชาเอก] · plo: [PLO_...] · source: "เล่ม 4.3/4.5" · generated: true
- บรรทัดแรกหลัง frontmatter: > [!warning] ห้ามแก้ — สร้างจากเล่ม แก้ที่ LE_Vault/overrides/ (VR-06)
- ลิงก์ไขว้ (VR-03): โน้ตวิชามีตาราง CLO | Bloom | YLO (IE) | PLO (IE) | YLO (SC) | PLO (SC)
  โดยทุกรหัสเป็น [[...]] · วิชาบังคับก่อนเป็น [[รหัส]] · โน้ต PLO/YLO ลิสต์วิชาที่ส่งเข้าแยกวิชาเอก
- normalise ค่า YLO ก่อนสร้างลิงก์: ตัดช่องว่างและวงเล็บค้างท้าย เช่น "YLO4.3 (" → "YLO4.3"
- ลิงก์ไปรหัสที่ไม่มีโน้ตจริง (เช่น EN-001-007) ให้เขียนเป็นข้อความธรรมดา พร้อม > [!warning]
- ลบเฉพาะไฟล์ที่ frontmatter มี generated: true ก่อนเขียนใหม่ ไฟล์ที่คนเขียนเองห้ามแตะ
- เขียนดัชนี 00_<โฟลเดอร์>_Index.md ใหม่ทุกครั้ง (generated: true) แยกหัวข้อ IE / SC / ร่วม
- throw error ถ้าข้อมูลส่วนใดมี 0 รายการ · พิมพ์จำนวนโน้ตที่เขียนต่อโฟลเดอร์และจำนวนลิงก์เสีย

ส่วนที่ 3 — รูปแบบ LE_Vault/overrides/*.md (DP-07)
ทุกไฟล์มีตาราง markdown หนึ่งตาราง และทุกตารางต้องมีคอลัมน์ ISS (รหัสใน 04_Issues_Register)
หัวตารางต่อไฟล์ (ตัวอ่านต้องมี SCHEMA ต่อไฟล์ และ throw ถ้าหัวตารางไม่ตรง)
  plo_names.md      target | field | value | ISS | หมายเหตุ            (ขั้นที่ 4)
  clo_fixes.md      target | field | value | ISS | หมายเหตุ            (ขั้นที่ 7 · target = รหัสวิชา#CLOn)
  course_fixes.md   code | field | ค่าในเล่ม | ค่าที่ใช้ | ISS          (ขั้นที่ 7–8)
  clo_levels.md     major | code | clo | plo | level | ISS | เหตุผล    (ขั้นที่ 10)
  elective_majors.md  กำหนดในขั้นที่ 6 · plan_rules.md กำหนดในขั้นที่ 9
  supplement_*.md   ข้อมูลเสริมที่ตัวดึงยังไม่อ่าน ใช้คอลัมน์ source แทน ISS (ขั้นที่ 3)
  field = ชื่อ field ใน curriculum.json เช่น en, descTh, prereq
เขียนตาราง SCHEMA นี้ต่อท้าย LE_Vault/overrides/README.md
```

> [!important] วอลต์กับเว็บต้องเห็น override ชุดเดียวกัน
> ทั้ง `build_vault.py` และ `build-data.mjs` ต้องอ่าน `overrides/` ด้วยกฎเดียวกัน ถ้าเว็บแสดงชื่อ PLO ที่แก้แล้วแต่โน้ตในวอลต์ยังเป็นค่าเดิม กรรมการจะไม่รู้ว่าฉบับไหนถูก

---

## Prompt B · เว็บ

```text
ขยาย web/scripts/build-data.mjs จากขั้นที่ 1 ให้เป็นตัวสร้างข้อมูลเว็บตัวเดียว (DP-08)

1. อ่าน ../data/curriculum.json และ ../LE_Vault/overrides/*.md
   normalise CRLF ก่อน parse: readFileSync(...).replaceAll("\r\n", "\n")  (NFR-08)
2. ใช้ override ทีละแถว
   - target ที่ไม่มีจริงหรือ field ที่ไม่รู้จัก → throw error พร้อมชื่อไฟล์และเลขบรรทัด
   - แถวที่ไม่มี ISS → throw
   - ค่าที่ตรงกับเล่มอยู่แล้ว → พิมพ์ warning ว่า override นี้ไม่จำเป็นแล้ว
   - เก็บทุกการแก้เป็น { target, field, from, to, iss, file } (NFR-06)
3. ตรวจเพิ่ม (derived) ตามตาราง "สิ่งที่ตัวดึงยังไม่บันทึก" แล้วรวมกับ issues[] ของเล่ม
   ISSUES = [{ id, origin: "extractor"|"derived", where, code?, note, severity }]
   และติด flags ให้รายวิชา/CLO เช่น "noDescTh" "noDescEn" "cloMapMismatch" "cloDuplicate"
4. เขียนโมดูลใน web/src/generated/ (ทุกไฟล์มีหัว AUTO-GENERATED)
   meta.js       META · MAJORS · COUNTS
   courses.js    COURSES · COURSE_BY_CODE
   structure.js  STRUCTURE (ต้นไม้หมวด→กลุ่ม) · GROUPS
   plos.js       PLOS · PLO_BY_ID
   ylos.js       YLOS · YLO_BY_ID · YLO_INTRO
   mapping.js    MAPPING = { IE: [...], SC: [...] }  (YLO normalise แล้ว)
   plans.js      PLANS = { IE: [...], SC: [...] }
   skills.js     SKILL_SETS
   faculty.js    FACULTY
   issues.js     ISSUES
   overrides.js  OVERRIDES · isOverridden(target, field)
   ห้าม export อาร์เรย์ว่าง: ถ้าโมดูลใดได้ 0 รายการ ให้ throw และไม่เขียนไฟล์ทับ
5. พิมพ์สรุป: จำนวนต่อโมดูล · จำนวน override · issue แยก extractor/derived
6. web/src/warnings.js รวมข้อความป้ายเตือนทั้งหมดไว้ที่เดียว { [kind]: { label, tone } }
   แล้วให้ <WarnBadge kind/> และ <OverrideBadge target field/> ใน pages/ui.jsx อ่านจากที่นี่
   OverrideBadge แสดง "แก้ไขจากเล่ม" และ tooltip บอกค่าเดิม ค่าใหม่ และ ISS
7. web/src/codeInfo.js สร้างทะเบียน tooltip จาก PLOS, YLOS, COURSES, SKILL_SETS (FR-20)
   ห้ามเก็บข้อความซ้ำ ให้ lookup จากโมดูล generated
8. ชิปบนหัวเว็บอ่านจาก COUNTS และ package.json มี "data", "predev", "prebuild" ตามขั้นที่ 1
```

**ตารางเชื่อมโยง**

| ใช้ที่ | โมดูล | ต้นทาง |
|---|---|---|
| ทุกหน้า | `generated/*.js` | `data/curriculum.json` + `LE_Vault/overrides/` |
| วอลต์ | — | `tools/build_vault.py` → `LE_Vault/10_Curriculum/` |
| หน้าตรวจข้อมูล (ขั้น 14) | `ISSUES` · `OVERRIDES` | [[04_Issues_Register]] |

---

## ตรวจรับ

- [ ] ตัวดึงพิมพ์ `courses=90 clos=254 plos=13 ylos=27 planIE=8 planSC=8 mapIE=137 mapSC=120 faculty=7 skills=18 activities=3 issues=19`
- [ ] ทดสอบ DP-02: ใช้สำเนาเล่มที่แก้หัวข้อ "4.4 แผนการเรียน" ให้ผิด แล้วตัวดึงล้มพร้อมข้อความที่บอกชื่อหัวข้อนั้น
- [ ] `issues[]` มี `NS-531-1100` และ `EN-788-13009` (DP-03) และ `courses` มี `NS-531-11001` ที่มี `codeAsPrinted`
- [ ] `build_vault.py` พิมพ์ Courses 90 · PLO 13 · YLO 27 · skills 6 · Faculty 7 และลิงก์เสีย 0
- [ ] ใน Obsidian คลิก `[[EN-788-12001]]`, `[[PLO_SC2]]` และ `[[IE-YLO1.1]]` (ชื่อมีจุด) แล้วเปิดได้ทั้งหมด
- [ ] รัน `build_vault.py` สองรอบติดกัน ไฟล์ไม่เปลี่ยน · โน้ตที่เขียนมือใน `10_Curriculum/` ไม่ถูกลบ
- [ ] ใส่แถว override ที่ target เป็น `EN-999-99999` แล้ว `npm run data` throw พร้อมเลขบรรทัด
- [ ] `npm run data` พิมพ์ ISSUES แยก extractor 19 และ derived (อย่างน้อยครอบคลุมทุกแถวในตาราง derived)
- [ ] ลบโฟลเดอร์ `web/src/generated/` แล้ว `npm run dev` สร้างกลับมาเอง
- [ ] ชี้ที่ป้าย `PLO_LE1` ที่ไหนก็ได้ (ทดสอบในหน้า Pending) แล้ว tooltip ขึ้นถ้อยคำเต็มของ PLO

> [!warning] กับดักที่พบในเล่มนี้
> - **หัวข้อ "คำอธิบายระดับการเรียนรู้" ว่าง** แล้วตามด้วยตารางแผนที่ทันที และระดับ I/R/M มีเพียง 2 จาก 257 แถว ห้ามเดาค่าว่างเป็น I หรือ R
> - **`NS-531-1100`** ขาดหลัก ถ้าใช้ `\d{4,5}` จะได้วิชาผีเพิ่มหนึ่งวิชา ต้องบังคับ 5 หลักแล้วแยกกรณีเป็น issue
> - **`EN-788-13009` อยู่ในตารางวิชาเอก IE สองแถว** ถ้าไม่ข้ามแถวซ้ำ กลุ่ม ie จะรวมได้ 25 แทน 24 หน่วยกิต
> - **CLO อยู่ใน 4.3 แต่ YLO/PLO อยู่ใน 4.5** ต้อง join ด้วย (รหัสวิชา, เลข CLO) แยกวิชาเอก แถว 4.5 ที่ช่องรหัสว่างจะ join ไม่ติด (13012 CLO2 ฝั่ง SC)
> - **ชื่อภาษาอังกฤษของ PLO ใช้วงเล็บต่างกัน** LE ใช้ `[...]` แต่ IE/SC ใช้ `(...)` ท้ายถ้อยคำไทย ตัวดึงจับเฉพาะ `[...]` จึงได้ `en` ว่าง 9 ข้อ (จัดการในขั้นที่ 4)
> - **คำอธิบาย GE 3 วิชาที่ "ว่าง"** บันทึกอ่านเล่ม ([[04a_ch4_structure_GE_foundation]] ข้อ 32) ระบุว่าข้อความอาจถูกรวมอยู่ในเซลล์ชื่อวิชาของ docx ให้เปิดเล่มตรวจก่อนสรุปว่า "ไม่มีในเล่ม"
> - **ข้อความที่ถูกตัดขึ้นย่อหน้าใหม่** ใน PLO/YLO และช่องว่างจากการจัดชิดขอบ เช่น "ผู้ใช้บัณฑิตด้าน โลจิสติกส์" ให้ต่อบรรทัดตอน parse และ normalise ช่องว่างตอนเทียบ แต่เก็บข้อความต้นฉบับไว้แสดง

---

⬅ [[01_Skeleton|ขั้นที่ 1]] · [[00_Tutorial_Home|สารบัญ]] · ➡ [[03_Stakeholders_and_Needs|ขั้นที่ 3 · ผู้มีส่วนได้ส่วนเสีย]]
