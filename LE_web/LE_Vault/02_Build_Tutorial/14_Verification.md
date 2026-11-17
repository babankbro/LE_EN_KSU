---
tags: [tutorial, build]
step: 14/14
---

# ขั้นที่ 14 · ตรวจข้อมูล ลิงก์ build และหน้า data-quality

> **เป้าหมาย: พิสูจน์ด้วยคำสั่งเดียวว่าตัวเลขทุกตัวบนเว็บมาจากเล่ม และทำหน้า `/data-quality` ให้กรรมการหลักสูตรใช้ไล่แก้เล่มได้จริง**

## หลังจบขั้นนี้ต้องได้อะไร

| เมนู | route | เนื้อหา |
|---|---|---|
| ข้อมูลอ้างอิง → คุณภาพข้อมูล | `/data-quality` | ข้อสังเกตทั้งหมด จัดกลุ่มตามหมวดของเล่มและความรุนแรง P0/P1/P2 ลิงก์ไปหน้าที่เกี่ยวข้อง |
| — (คำสั่ง) | `npm run check` | ตรวจข้อมูล · snapshot ของ issue · กราฟไม่ทับกัน · ลิงก์ในวอลต์ |

**SRS:** FR-22 (หลัก) · NFR-01 · NFR-02 · NFR-05 · NFR-08 · NFR-09 · FR-01 · VR-03 · หัวข้อ 6 การทวนสอบ — ดู [[03_SRS_Curriculum_Website]]

---

## ข้อมูลจริงของหลักสูตรนี้

**ค่าอ้างอิงที่ `npm run check` ต้องยืนยัน** (จาก [[02_Checklist_Web_Data]] และขั้นที่ 8–13)

| รายการ | ค่า |
|---|---|
| รายวิชา · CLO · PLO · YLO | 90 · 254 · 13 · 27 |
| ภาคในแผน IE / SC | 8 / 8 · รวม 122 / 122 |
| ยอดรายภาค IE | 21 · 22 · 21 · 21 · 17 · 5 · 6 · 9 |
| ยอดรายภาค SC | 20 · 22 · 21 · 18 · 19 · 7 · 6 · 9 |
| แถวแผนที่ IE / SC | 137 / 120 |
| PLO ที่ต้องมี CLO | IE 9 (LE1–4 + IE1–5) · SC 8 (LE1–4 + SC1–4) |
| ชุดทักษะ · ทักษะย่อย | 6 · 18 |
| อาจารย์ประจำหลักสูตร | 7 |
| `issues[]` จากตัวดึงรุ่นแรก | 19 (4.2 = 2 · 4.5 "ไม่มีระดับ M" = 17) — จะเพิ่มขึ้นหลังขั้นที่ 8–13 |
| ทะเบียนข้อสังเกต | ISS-01–08 (P0) · ISS-10–32 (P1) · ISS-40–56 (P2) ใน [[04_Issues_Register]] |
| Checklist เล่ม | 66 รายการ: ✅ 33 · ⚠️ 24 · ❌ 9 ใน [[01_Checklist_Curriculum_Data]] |

---

## Prompt A · วอลต์

```text
งาน: สร้างการตรวจทั้งระบบ รองรับ 2 วิชาเอก (IE, SC)  ราก = LE_web/

1. tools/check_vault_links.py มีอยู่แล้ว (ข้ามลิงก์ในบล็อกโค้ด) ให้รันหลัง build_vault.py ทุกครั้ง
   ผลที่ต้องได้: broken=0  ถ้าไม่เป็น 0 ห้ามแก้ด้วยการลบลิงก์ ให้แก้ตัวสร้างโน้ตหรือเพิ่มโน้ตที่ขาด

2. tools/build_vault.py เพิ่มการสร้าง LE_Vault/10_Curriculum/Issues_by_Chapter.md
   - อ่าน issues[] ของ curriculum.json และตารางใน LE_Vault/01_Requirements/04_Issues_Register.md
     (คอลัมน์ ID | ตำแหน่ง | ข้อสังเกต | แนวทางแก้ | ที่มา) แล้ว normalise CRLF ก่อน parse
   - จับคู่ issue อัตโนมัติกับ ISS ด้วย (code, where) ถ้าไม่พบให้ติดป้าย "ยังไม่ลงทะเบียน"
   - จัดกลุ่มตามหมวดของเล่ม (เลขตัวแรกของตำแหน่ง: 1–9 หรือ ภาคผนวก) แล้วตามความรุนแรง P0/P1/P2
   - แถวที่มีค่าใน LE_Vault/overrides/ ทับแล้ว ให้ระบุสถานะ "แก้ใน overrides" และชื่อไฟล์
   - พิมพ์จำนวนต่อหมวด ต่อระดับ และจำนวนที่ยังไม่ลงทะเบียน; throw ถ้าอ่านทะเบียนได้ 0 แถว

3. สร้าง LE_Vault/10_Curriculum/Acceptance_Report.md จาก 01_Checklist_Curriculum_Data.md
   คอลัมน์: # | รายการ | สถานะในเล่ม | แสดงบนเว็บที่ (route) | ป้ายเตือน/ISS | ผ่านการตรวจรับ
   ทุกแถวที่เป็น ⚠️ หรือ ❌ ต้องมี route ที่แสดงป้ายหรือมีรายการใน /data-quality
   ถ้าไม่มี ให้เขียน "ยังไม่แสดง" (ห้ามเว้นว่าง) แล้วพิมพ์จำนวนแถวที่ยังไม่แสดง
```

---

## Prompt B · เว็บ

```text
1. web/package.json คง "data" / "predev" / "prebuild" ของขั้นที่ 1 ไว้ แล้วเพิ่ม
   "check": "node scripts/check-data.mjs && node scripts/check-graph.mjs && python ../tools/check_vault_links.py"
   ลำดับเต็มเมื่อเล่มเปลี่ยน (รันจาก LE_web/):
   python tools/extract_curriculum.py && python tools/build_vault.py && cd web && npm run data && npm run check

2. web/scripts/check-data.mjs อ่าน data/curriculum.json และ web/src/generated/*.js
   ตรวจ (ทุกข้อพิมพ์ ✓/✗ พร้อมค่าจริงกับค่าที่คาด แล้ว exit 1 ถ้ามี ✗)
   - จำนวนตามตาราง DP-01: 90 · 254 · 13 · 27 · 8+8 · 137/120 · 7 · 18
   - ยอดรายภาคที่คำนวณจากรายวิชา = ยอดที่เล่มระบุ ทั้ง 16 ภาค และยอดสุดท้าย = meta.totalCredits ทั้งสองวิชาเอก
   - ทุกแถวใน mapping มี code และ (code, clo) อยู่ใน courses[].clos
   - ทุก PLO ในขอบเขตของวิชาเอกมี CLO อย่างน้อย 1 แถว (IE 9 ข้อ · SC 8 ข้อ) และทุก YLO มี CLO
   - ทุกค่า ylo/plo ใน generated อยู่ในทะเบียน ylos[] / plos[]
   - น้ำหนักประเมินต่อ (PLO, วิชาเอก) = 100 เมื่อมี assessment แล้ว
   - snapshot: เทียบ ISSUES (ทั้ง extractor และ derived) กับ web/scripts/__snapshots__/issues.json
     ถ้ามีรายการเพิ่มหรือหายให้แสดง diff แล้ว fail จนกว่าจะรัน "npm run check -- --update-snapshot" โดยตั้งใจ
   - ไม่มีเลข 13 หลักติดกัน (\b\d{13}\b) หรือรูปแบบเบอร์โทรใน generated/*.js (C3)
   - ไม่มีไฟล์ใน src/ ที่ยัง import ../data.js, obeData.js, ksecData.js ของ template

3. web/scripts/build-data.mjs ขยาย ISSUES ใน web/src/generated/issues.js ของขั้นที่ 2
   { id, origin: "extractor"|"derived"|"register", kind, where, code, note, severity,
     iss, chapter, fix, route, overridden, overrideFile }
   - origin "register" = ข้อสังเกต 👁 ในทะเบียน ISS ที่ไม่มีตัวตรวจอัตโนมัติ
   - จับคู่กับทะเบียนด้วย (code, where) ถ้าจับคู่ได้ severity ใช้ระดับของทะเบียน ถ้าไม่ได้ iss = null
   route กำหนดจากตำแหน่ง: 4.2/4.3 + code → /courses/:code · 4.4 → /plan · prereq → /graph ·
   4.5 → /clo · 4.6 → /skills · 5.x → /teaching · 6.x → /assessment · 1.2, 7–9 → /quality ·
   3.x → /plo หรือ /ylo · ภาคผนวก → /faculty หรือ /obe

4. สร้าง web/src/pages/DataQuality.jsx และ route /data-quality
   - แถบสรุป: P0 / P1 / P2 / ยังไม่ลงทะเบียน / แก้ใน overrides แล้ว
   - ตัวกรองหมวด (1–9, ภาคผนวก) · ความรุนแรง · origin · วิชาเอกจาก useMajor()
   - ตารางจัดกลุ่มตามหมวด: ID | ตำแหน่ง | ข้อสังเกต | แนวทางแก้ | ไปที่หน้า (ลิงก์ route ผ่าน withMajor())
   - แถวที่ override แล้วแสดง <OverrideBadge/> พร้อมชื่อไฟล์ใน overrides/
   - <WarnBadge/> ทุกจุดบนเว็บ ให้ลิงก์กลับมาที่ /data-quality#<id> (แก้ใน pages/ui.jsx ที่เดียว)
   - ปุ่มส่งออก CSV สำหรับแนบรายงานการประชุมกรรมการ

5. ตรวจหลัง build
   npm run data && npm run build && npm run check && npm run preview
   เปิดทุก route ในเบราว์เซอร์แล้วจด console error ลงตาราง (ต้องเป็น 0)
```

## ตรวจรับ

- [ ] `npm run check` ผ่านครบทุกข้อ และพิมพ์ overlap = 0 กับ broken=0
- [ ] แก้ยอดภาคหนึ่งใน `curriculum.json` ฉบับทดสอบ → `check-data.mjs` fail พร้อมบอกภาคและวิชาเอก
- [ ] เพิ่ม issue ปลอมหนึ่งรายการ → snapshot fail และแสดง diff
- [ ] `npm run build` ผ่าน และ JS bundle หลักไม่เกิน 400 KB gzip (NFR-01) — ไฟล์ข้อมูลหนักของ template ถูกลบหมด
- [ ] เปิดทุก route ใน `npm run preview` แล้ว console ไม่มี error: `/` `/structure` `/structure/el-trans` `/courses` `/courses/EN-788-13018` `/plan` `/graph` `/faculty` `/obe` `/plo` `/plo/PLO_IE4` `/ylo` `/ylo/YLO4.3` `/clo` `/skills` `/teaching` `/assessment` `/quality` `/refs` `/data-quality`
- [ ] แต่ละ route ข้างบนทดลองกับ `?major=IE`, `?major=SC`, `?major=ALL` และกด refresh แล้วไม่ 404 (FR-01, FR-02)
- [ ] บนจอกว้าง 375px ไม่มี horizontal scroll ของทั้งหน้า ยกเว้นในกล่องตาราง/กระดาน/กราฟ (NFR-02)
- [ ] `/data-quality` มีรายการครบทุก ISS ใน [[04_Issues_Register]] จัดกลุ่มตามหมวดและระดับ และทุกแถวลิงก์ไปหน้าที่เกี่ยวข้องได้
- [ ] `Acceptance_Report.md` ไม่มีแถว ⚠️/❌ ที่ "ยังไม่แสดง"
- [ ] ไม่มี analytics หรือ tracker ภายนอกใน `index.html` และ bundle (NFR-09)
- [ ] ลบ `web/src/generated/` ทั้งโฟลเดอร์แล้วรัน `npm run data` → ได้ไฟล์กลับมาเหมือนเดิมทุกไฟล์ (NFR-07)

> [!warning] กับดักที่พบในเล่มนี้
> - **snapshot ไม่ใช่ตัวเลขคงที่:** ขั้นที่ 8–13 เพิ่ม issue ใหม่หลายชนิด (prereq, YLO สะกดเพี้ยน, แถวไม่มีรหัส, CLO ข้อความไม่ตรง, เกณฑ์ขัดกัน) ให้อัปเดต snapshot ครั้งเดียวหลังขั้นที่ 13 แล้วจึงล็อก
> - **ความรุนแรงสองแหล่ง:** `issues[]` ของตัวดึงมีแค่ `where` `code` `note` ส่วน severity ที่ build-data กำหนดในขั้นที่ 2 อาจไม่ตรงกับทะเบียน ISS ให้ทะเบียนชนะเสมอ และ issue ที่จับคู่ไม่ได้ต้องแสดง "ยังไม่ลงทะเบียน"
> - **"ทุก PLO มี CLO" ผ่านได้ทั้งที่ไม่มีระดับ M เลย** ต้องแยกเป็นสองการตรวจ และให้ข้อหลังเป็นคำเตือน (ข้อมูลเล่ม) ไม่ใช่ error ของโค้ด
> - **route ที่มีจุด** เช่น `/ylo/YLO4.3` และ `/plo/PLO_IE4` ต้องทดสอบ refresh บน static hosting เพราะบางเซิร์ฟเวอร์มองว่าเป็นไฟล์
> - **ข้อมูลส่วนบุคคล:** รหัสหลักสูตร `25551401105424` มี 14 หลัก ตัวตรวจเลข 13 หลักต้องใช้ขอบเขตคำ มิฉะนั้นจะแจ้งเตือนผิด
> - **ไฟล์ template ที่ค้าง** (`data.js`, `cloRevisionData.js`, `ksecPedagogyData.js` ฯลฯ) ทำให้ bundle เกินเกณฑ์ แม้หน้าเว็บจะไม่ได้ใช้ ถ้ายังมีหน้าใด import อยู่

---

⬅ [[13_Quality_and_Management|ขั้นที่ 13]] · ➡ [[00_Tutorial_Home|กลับสารบัญ]]
