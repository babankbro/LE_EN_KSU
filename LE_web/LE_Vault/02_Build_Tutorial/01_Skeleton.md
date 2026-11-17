---
tags: [tutorial, build]
step: 1/14
---

# ขั้นที่ 1 · โครง LE_web จาก template และตัวสลับวิชาเอก

> **เป้าหมาย: ได้เว็บที่รันได้ มีเมนูครบทุกขั้นแต่ยังว่าง และไม่เหลือร่องรอยหลักสูตร AI จาก template ก่อนข้อมูลจริงจะเข้ามา**

## หลังจบขั้นนี้ต้องได้อะไร

| เมนู | เส้นทาง | เนื้อหา |
|---|---|---|
| ทุกเมนู | ทุก route ในตารางของ [[00_Tutorial_Home]] | หน้า placeholder "รอข้อมูลขั้นที่ N" โดย N อ่านจาก `navConfig.js` |
| หัวเว็บ | ทุกหน้า | ชื่อหลักสูตร · ตัวเลขสำคัญ · ตัวสลับวิชาเอก **IE / SC / ทั้งหมด** |
| ท้ายเว็บ | ทุกหน้า | คณะ · มหาวิทยาลัย · สถานะ "ฉบับร่าง" |
| วอลต์ | `LE_Vault/10_Curriculum/` · `LE_Vault/overrides/` | โฟลเดอร์และดัชนีเปล่าพร้อมป้าย `[!todo]` |

**SRS ที่ครอบคลุม:** FR-01 (URL ของทุกหน้าและ refresh ไม่ 404) · FR-02 (ตัวสลับวิชาเอกผูกกับ `?major=`) · วางโครงให้ FR-20 และ VR-04 · ดู [[03_SRS_Curriculum_Website]]

---

## ข้อมูลจริงของหลักสูตรนี้

ค่าที่หัวเว็บต้องใช้มาจาก `meta` ใน `data/curriculum.json` (ห้ามพิมพ์ลง `.js` เอง)

| field | ค่าในเล่ม |
|---|---|
| `meta.nameTh` | หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโลจิสติกส์ |
| `meta.degreeThShort` · `degreeEnShort` | วศ.บ. (วิศวกรรมโลจิสติกส์) · B.Eng. (Logistics Engineering) |
| `meta.revision` · `basedOn` | หลักสูตรปรับปรุง พ.ศ. 2570 · ปรับจากฉบับ พ.ศ. 2566 |
| `meta.faculty` · `university` | คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม · มหาวิทยาลัยกาฬสินธุ์ |
| `meta.majors` | `IE` วิชาเอกวิศวกรรมอุตสาหการ · `SC` วิชาเอกวิศวกรรมการจัดการโซ่อุปทาน |
| ตัวเลขบนหัวเว็บ (คำนวณ) | 122 หน่วยกิต · 2 วิชาเอก · PLO 13 ข้อ · 90 รายวิชา |

**สิ่งที่ต้องเก็บไว้และสิ่งที่ต้องตัดออกจาก template** (`web/` คัดลอกมาจาก `KSU-AI-EN/curriculum-graph`)

| เก็บไว้ (แก้ import ให้ไม่พึ่งข้อมูล AI) | ตัดออก |
|---|---|
| `main.jsx` · `App.jsx` (layout) · `SiteNav.jsx` · `Sidebar.jsx` · `navConfig.js` | `CareerGraph.jsx` · `careers.css` · `pages/AiEngineerJobs.jsx` · `jobs.css` · `jobsIndex.json`/`jobsRuntime/`/`jobsData.json` (ถ้ามี) |
| `CodeTip.jsx` · `tip.css` · `codeInfo.js` (ล้างทะเบียนให้ว่าง) | `pages/KsecPedagogy.jsx` · `ksecData.js` · `ksecPedagogyData.js` · `courseKsecData.js` |
| `DependencyGraph.jsx` (ใช้ในขั้นที่ 8) · `PlanBoard.jsx` (ขั้นที่ 9) · `Alluvial.jsx` (ขั้นที่ 10) | `data.js` · `cloData.js` · `cloRevisionData.js` · `courseRevisionData.js` · `obeData.js` · `refData.js` · `teachingData.js` · `facultyData.js` · `alluvialViews.js` |
| `styles.css` · `obe.css` · `clo.css` · `planboard.css` · `alluvial.css` | script ใน `package.json`: `jobs:*` `build:ksec` `build:db` `db:*` `draft:bloom` `build:elective-clo` `build:section8` `build:mapping` `build:plan` `sync:curriculum` และ **`prebuild`** · devDependency `exceljs` |
| `pages/ui.jsx` · `pages/NotFound.jsx` · `vercel.json` · `vite.config.js` | `.env.example` (คีย์ Gemini) · `public/hero-banner.jpg` · `public/tracks-banner.jpg` |

**เมนูของเว็บนี้** (กลุ่ม → route → ขั้นที่เติมข้อมูล)

| กลุ่ม | route (ขั้นที่) |
|---|---|
| หน้าแรก | `/` (6) |
| หลักสูตร | `/structure` (6) · `/courses` (7) · `/graph` (8) · `/plan` (9) · `/faculty` (6) |
| ผลลัพธ์การเรียนรู้ | `/obe` (3) · `/plo` (4) · `/ylo` (5) · `/clo` (10) · `/skills` (11) |
| การเรียนการสอนและคุณภาพ | `/teaching` (12) · `/assessment` (12) · `/quality` (13) |
| ตรวจข้อมูล | `/data-quality` (14) · `/refs` (3, ลำดับ C) |

---

## Prompt A · วอลต์

```text
เตรียมโครงวอลต์ของระบบ LE_web (ราก = LE_web/) โดยยังไม่สร้างโน้ตรายวิชา
โฟลเดอร์ LE_Vault/00_Home.md, 01_Requirements/, 02_Build_Tutorial/, 03_Source_Notes/ มีอยู่แล้ว ห้ามแก้

1. สร้างโฟลเดอร์ย่อยใน LE_Vault/10_Curriculum/
   Courses/  PLO/  YLO/  skills/  Faculty/  Needs/  Structure/
   แต่ละโฟลเดอร์มีไฟล์ดัชนี 00_<ชื่อโฟลเดอร์>_Index.md ที่มี
   - frontmatter: tags: [curriculum, index] · generated: false
   - H1 และ blockquote หนึ่งบรรทัดบอกว่าโฟลเดอร์นี้เก็บอะไร
   - หัวข้อแยก "วิชาเอก IE" "วิชาเอก SC" "ร่วมทั้งสองวิชาเอก" (ต้องรองรับ 2 วิชาเอกตั้งแต่ตอนนี้)
   - ปิดท้ายด้วย > [!todo] รอสร้างอัตโนมัติในขั้นที่ 2
2. สร้าง LE_Vault/10_Curriculum/00_Curriculum_Index.md ลิงก์ไปทุกดัชนีด้วย [[...]]
   และอ่านชื่อหลักสูตร/ชื่อวิชาเอกจาก data/curriculum.json (meta.nameTh, meta.majors)
   ถ้า meta.majors มี 0 รายการ ให้ throw error ห้ามเขียนไฟล์
3. สร้างไฟล์ override เปล่าใน LE_Vault/overrides/ ตามรายการใน overrides/README.md
   plo_names.md · clo_levels.md · clo_fixes.md · course_fixes.md · elective_majors.md
   แต่ละไฟล์มีเฉพาะ frontmatter (tags: [overrides]) และ H1 ยังไม่มีตาราง
   (หัวตารางของแต่ละไฟล์กำหนดในขั้นที่ 2 ส่วนที่ 3)
4. ตรวจ LE_web/.obsidian/app.json ว่า userIgnoreFilters มี web/node_modules/ web/dist/ data/
5. พิมพ์สรุป: จำนวนโฟลเดอร์ที่สร้าง · จำนวนไฟล์ดัชนี · จำนวนไฟล์ override
อย่าใส่ตัวเลขหรือข้อเท็จจริงของหลักสูตรที่ไม่ได้อ่านจาก curriculum.json
```

> [!tip] ทำไมสร้างดัชนีที่แยก IE/SC ตั้งแต่ไฟล์เปล่า
> ถ้าเริ่มด้วยดัชนีแบบรายการเดียว ผู้ช่วยจะคัดลอกโครงหลักสูตรเดียวจาก template มาทุกขั้นต่อจากนี้ การมีหัวข้อ "IE / SC / ร่วม" รออยู่ก่อนช่วยบังคับรูปแบบไว้ล่วงหน้า

---

## Prompt B · เว็บ

```text
ปรับ web/ (คัดลอกจาก template KSU-AI-EN/curriculum-graph) ให้เป็นโครงของ LE_web
ต้องรองรับ 2 วิชาเอก (IE, SC) ทุกจุด และห้ามพิมพ์ข้อมูลหลักสูตรลงไฟล์ .js ด้วยมือ

1. ลบไฟล์ตามรายการ "ตัดออก" ของขั้นนี้ แล้วรัน grep ใน web/src
   หาคำ ปัญญาประดิษฐ์ | KSEC | AISK | careers | jobs | 125 หน่วยกิต | PLO 7
   ต้องเหลือ 0 จุด (ไม่นับ web/src/generated/)
2. web/package.json: name "le-web", description ภาษาไทยของหลักสูตรนี้
   scripts เหลือ dev · build · preview · data ("node scripts/build-data.mjs")
   เพิ่ม predev และ prebuild = "npm run data" · ลบ devDependency exceljs
3. web/scripts/build-data.mjs (รุ่นแรก จะขยายในขั้นที่ 2)
   - อ่าน ../data/curriculum.json
   - เขียน web/src/generated/meta.js ที่ export META (nameTh, nameEn, degreeThShort,
     degreeEnShort, revision, faculty, university), MAJORS และ COUNTS ที่คำนวณจากข้อมูล
     { credits: meta.totalCredits, majors, plos, ylos, courses, clos, faculty }
   - บรรทัดแรกของไฟล์: // AUTO-GENERATED by scripts/build-data.mjs — ห้ามแก้ด้วยมือ
   - throw error ถ้า courses หรือ majors เป็น 0 รายการ (ห้ามเขียนไฟล์ทับ)
   - พิมพ์ COUNTS ทุกครั้งที่รัน
4. web/src/navConfig.js เป็นแหล่งเมนูแหล่งเดียว ใช้ทั้ง SiteNav และ Sidebar
   NAV_GROUPS = [{ id, label, hint?, solo?, to?, items: [{ to, label, desc, step, sections? }] }]
   ใส่กลุ่มและ route ตามตาราง "เมนูของเว็บนี้" ทุก item ต้องมี step (เลขขั้นที่เติมข้อมูล)
   และ export stepOf(pathname) คืนเลขขั้นของ route นั้น (รวม /plo/:id → ขั้นของ /plo)
   ข้อความ desc ห้ามมีตัวเลขหลักสูตร (ตัวเลขให้หน้าเว็บคำนวณเอง)
5. web/src/major.js
   - MAJOR_IDS = ["ALL","IE","SC"] · ค่าเริ่มต้น ALL
   - useMajor(): อ่าน ?major= ด้วย useSearchParams ค่าที่ไม่รู้จักให้ถือเป็น ALL และลบ param ทิ้ง
   - setMajor(m): ใช้ replace: true และคงพารามิเตอร์อื่นไว้ · ALL = ลบ param
   - withMajor(to, major): คืน { pathname, search, hash } ให้ลิงก์ภายในพก ?major= ไปด้วย
6. web/src/MajorSwitch.jsx ปุ่มกลุ่ม 3 ปุ่ม "IE" "SC" "ทั้งหมด" ใช้ aria-pressed
   ชื่อเต็มของวิชาเอกอ่านจาก MAJORS ใน generated/meta.js
   ให้ SiteNav, Sidebar และ Link ภายในทุกจุดใช้ withMajor() เพื่อไม่ให้วิชาเอกหลุดเมื่อเปลี่ยนหน้า
7. web/src/App.jsx
   - หัวเว็บ: brand-mark "LE" · ชื่อจาก META · ชิป 3 อันจาก COUNTS · <MajorSwitch/>
   - ท้ายเว็บ: META.nameTh + META.revision + META.faculty + META.university
     และหมายเหตุ "ข้อมูลจากเล่ม มคอ.2 ฉบับร่าง ยังไม่ผ่านการอนุมัติสภามหาวิทยาลัย"
   - Routes: ทุก route ในตาราง + /structure/:id /courses/:code /plo/:id /ylo/:id และ * → NotFound
8. web/src/pages/Pending.jsx แสดงชื่อหน้าและ "รอข้อมูลขั้นที่ N" โดย N = stepOf(pathname)
   ทุกหน้า (Home, Structure, Courses, ... , Skills, Quality, DataQuality) ให้ render <Pending/> ไปก่อน
9. web/src/pages/ui.jsx ลบการ import data.js · เก็บ PageHead, Section
   เพิ่ม <WarnBadge kind text/> และ <OverrideBadge/> เป็นโครงเปล่า (เติมความหมายในขั้นที่ 2)
10. codeInfo.js ให้ lookup() คืน null ทุกรหัสไปก่อน · CodeTip.jsx ห้าม import data.js
11. index.html: <title> และ meta description เป็นของหลักสูตรนี้ · ฟอนต์ IBM Plex Sans Thai คงไว้
    เพิ่ม fallback Noto Sans Thai ใน --font-sans ของ styles.css
12. คง vercel.json ที่ rewrite ทุก path → /index.html
```

> [!important] ตัวสลับวิชาเอกคือสัญญาของทั้งเว็บ
> ทุกขั้นต่อจากนี้ต้องอ่านวิชาเอกจาก `useMajor()` เท่านั้น ห้ามเก็บใน `useState` ของหน้าใดหน้าหนึ่ง มิฉะนั้นลิงก์ที่แชร์ เช่น `/plan?major=SC` จะเปิดมาเป็นแผน IE

---

## ตรวจรับ

- [ ] `npm run data` พิมพ์ `courses=90 plos=13 ylos=27 faculty=7` และสร้าง `web/src/generated/meta.js`
- [ ] `npm run build` ผ่านโดยไม่เรียก script ของ jobs/ksec/db
- [ ] grep คำต้องห้ามในข้อ 1 ของ Prompt B ใน `web/src` (ไม่นับ `generated/`) ได้ 0 จุด
- [ ] เปิดครบทุก route ในตาราง "เมนูของเว็บนี้" แต่ละหน้าขึ้นเลขขั้นถูกต้อง เช่น `/clo` → "รอข้อมูลขั้นที่ 10"
- [ ] `/plo/PLO_LE1` ขึ้น "รอข้อมูลขั้นที่ 4" และ `/abc` ขึ้นหน้า NotFound
- [ ] เปิด `/plo?major=IE` แล้วคลิกเมนูไป `/ylo` URL ยังมี `?major=IE` · กด refresh แล้วยังเป็น IE
- [ ] เปิด `/plo?major=XYZ` แล้วตัวสลับแสดง "ทั้งหมด" และ param ถูกลบ
- [ ] แก้ label ใน `navConfig.js` หนึ่งจุด แล้วเมนูบนและเมนูข้างเปลี่ยนพร้อมกัน
- [ ] ที่ความกว้าง 375px หัวเว็บและตัวสลับไม่ทำให้หน้าเลื่อนแนวนอน
- [ ] เปิดวอลต์ใน Obsidian แล้ว `00_Curriculum_Index` ไม่มีลิงก์เสีย

> [!warning] กับดักที่พบในเล่มนี้ (และใน template)
> - `package.json` ของ template มี **`prebuild` ที่เรียก `jobs:build-runtime` และ `build:ksec`** แต่ `web/scripts/` ที่คัดลอกมาว่าง `npm run build` จึงล้มทันทีจนกว่าจะลบ
> - `pages/AiEngineerJobs.jsx` import `../jobsIndex.json` ซึ่งไม่มีในโฟลเดอร์ แม้จะเป็น lazy import ก็ยังทำให้ build ล้ม
> - template hard-code ตัวเลขของหลักสูตร AI ไว้หลายจุด: ชิป "125 หน่วยกิต / PLO 7 ข้อ", `TOTAL_CREDITS = 125`, desc "คณาจารย์ 5 ท่าน" และ meta description "133 หน่วยกิต" ต้องกลายเป็นค่าที่คำนวณ (NFR-05)
> - template ใช้คีย์ PLO เป็นตัวเลข 1–7 (`PLO_COLOR`, `PLO_NAME`) แต่เล่มนี้ใช้ `PLO_LE1` ฯลฯ ห้ามคัดลอกโครง object เดิม
> - เล่มเขียนวิชาเอกโซ่อุปทานทั้ง "SCME" และ "SC" (ISS-40) ให้ใช้ `SC` เป็นรหัสเดียวทั้งระบบ และแสดงชื่อเต็มจาก `meta.majors`
> - `NavLink to="/plo"` ทิ้ง query string เสมอ ถ้าไม่ผ่าน `withMajor()` วิชาเอกจะหลุดทุกครั้งที่คลิกเมนู
> - วันที่และครั้งที่อนุมัติของสภาวิชาการและสภามหาวิทยาลัยในเล่มยังว่าง (ISS-08) ท้ายเว็บจึงต้องบอกว่าเป็นฉบับร่าง

---

⬅ [[00_Tutorial_Home|สารบัญ]] · ➡ [[02_Source_Extraction|ขั้นที่ 2 · ดึงข้อมูลจากเล่ม]]
