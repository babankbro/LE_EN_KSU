---
tags: [tutorial, build]
step: 4/14
---

# ขั้นที่ 4 · PLO 13 ข้อ (ร่วม 4 + IE 5 + SC 4)

> **เป้าหมาย: แสดง PLO ของแต่ละวิชาเอกให้ถูกชุด พร้อมรายวิชาและ CLO ที่ส่งเข้า และบอกตรง ๆ ว่ายังไม่มี PLO ใดถึงระดับ M**

## หลังจบขั้นนี้ต้องได้อะไร

| เมนู | เส้นทาง | เนื้อหา |
|---|---|---|
| ผลลัพธ์การเรียนรู้ → PLO | `/plo` | ข้อความนำ · PLO ร่วม/IE/SC ตามวิชาเอกที่เลือก · ชื่อภาษาอังกฤษ · Generic/Subject Specific |
| ผลลัพธ์การเรียนรู้ → PLO | `/plo/:id` | ถ้อยคำเต็ม · ความต้องการ · แหล่งข้อมูล · นโยบาย · รายวิชาและ CLO ที่ส่งเข้าแยกชั้นปีและระดับ I/R/M |

**SRS ที่ครอบคลุม:** FR-11 · FR-12 · FR-21 (ป้าย "ยังไม่กำหนดระดับ") · DP-07 (ชื่ออังกฤษจาก override) ดู [[03_SRS_Curriculum_Website]]

---

## ข้อมูลจริงของหลักสูตรนี้

ข้อความนำ (`meta.ploIntro`): หลักสูตรกำหนด PLO 13 ข้อ = ร่วม 4 ข้อ + เฉพาะ IE 5 ข้อ **หรือ** เฉพาะ SC 4 ข้อ นักศึกษา IE จึงรับผิดชอบ 9 ข้อ และ SC 8 ข้อ

| id | ขอบเขต | ประเภท (`outcomeType`) | ชื่ออังกฤษ | ที่มาของชื่อ |
|---|:-:|---|---|---|
| PLO_LE1 | LE | Subject Specific | Engineering Knowledge and Problem Analysis | `[...]` ในเล่ม → `en` |
| PLO_LE2 | LE | Generic | Ethics, Safety and Sustainability | `[...]` |
| PLO_LE3 | LE | Generic | Professional Communication and Teamwork | `[...]` |
| PLO_LE4 | LE | Generic | Lifelong Learning and Adaptability | `[...]` |
| PLO_IE1 | IE | Subject Specific | Engineering Design | `(...)` ท้ายถ้อยคำไทย → `en` |
| PLO_IE2 | IE | Subject Specific | Engineering Investigation | `(...)` |
| PLO_IE3 | IE | Subject Specific | Modern Engineering Tools | `(...)` |
| PLO_IE4 | IE | Subject Specific | Engineering Project Management | `(...)` |
| PLO_IE5 | IE | Subject Specific | Industrial Innovation and Improvement | `(...)` |
| PLO_SC1 | SC | Subject Specific | Integrated Supply Chain System Design | `(...)` |
| PLO_SC2 | SC | Subject Specific | Logistics Operations Planning and Improvement | `(...)` |
| PLO_SC3 | SC | Subject Specific | Supply Chain Data Analytics and Digital Technology | `(...)` |
| PLO_SC4 | SC | Subject Specific | Sustainable Supply Chain Innovation | `(...)` |

- Generic 3 : Subject Specific 10 (23.08% : 76.92% ตามเล่ม นับรวม 13 ข้อ) · ต่อวิชาเอก IE = 6/9 Subject Specific (66.67%) · SC = 5/8 (62.50%) ซึ่งเล่มไม่ได้แสดง
- ทุก PLO มี `needs` 2–3 ข้อความ · `sources` 3–5 รายการ · `policy.plans` 2 รายการ · `focus` หนึ่งประโยค

**แถวแผนที่ 4.5 ที่ส่งเข้าแต่ละ PLO** (นับจาก `mapping`)

| วิชาเอก IE | แถว / วิชา | วิชาเอก SC | แถว / วิชา |
|---|---:|---|---:|
| PLO_LE1 | 60 / 21 | PLO_LE1 | 60 / 21 |
| PLO_LE2 | 10 / 6 | PLO_LE2 | 10 / 6 |
| PLO_LE3 | 15 / 7 | PLO_LE3 | 15 / 7 |
| PLO_LE4 | 10 / 7 | PLO_LE4 | 10 / 7 |
| PLO_IE1 | 14 / 6 | PLO_SC1 | 6 / 4 |
| PLO_IE2 | 10 / 4 | PLO_SC2 | 7 / 3 |
| PLO_IE3 | 6 / 3 | PLO_SC3 | 6 / 4 |
| PLO_IE4 | 5 / 2 | PLO_SC4 | 6 / 4 |
| PLO_IE5 | 7 / 7 | **รวม** | **120** |
| **รวม** | **137** | | |

ระดับ I/R/M มีเพียง 2 แถว: `EN-788-13005` → PLO_IE3 **(R)** และ `EN-788-12006` → PLO_LE4 **(I)** ทั้งคู่ในแผน IE · แผน SC ไม่มีระดับเลย · **ไม่มี PLO ใดมีระดับ M** (17 issue ใน `issues[]`)

---

## Prompt A · วอลต์

```text
1. ตรวจว่า data/curriculum.json มี plos[].en ครบ 13 ข้อ
   เล่มใช้ [...] กับ PLO_LE แต่ใช้ (...) กับ PLO_IE/SC — ตัวดึงต้อง regex ได้ทั้งสองแบบ
   ถ้ายังว่างแม้แต่ข้อเดียว ให้แก้ regex ใน tools/extract_curriculum.py ไม่ใช่เติมด้วยมือ
   (overrides/plo_names.md ใช้เฉพาะเมื่อกรรมการต้องการเปลี่ยนชื่อจากที่เล่มเขียน)
2. ขยายโน้ต LE_Vault/10_Curriculum/PLO/<id>.md ที่สร้างโดย tools/build_vault.py
   - frontmatter: type: plo · code · scope (LE|IE|SC) · major ([IE, SC] สำหรับ LE) · outcomeType · en
   - ถ้อยคำเต็ม · focus · ความต้องการจากตารางที่ 1 (plos[].needs) · [[N0x]] จากขั้นที่ 3
   - แหล่งข้อมูล (plos[].sources) · นโยบาย (policy.plans + contribution)
   - ตาราง "รายวิชาที่ส่ง CLO เข้า" แยกหัวข้อวิชาเอก IE และ SC (PLO ร่วมต้องมีทั้งสอง)
     คอลัมน์: ปี/ภาค | [[รหัสวิชา]] | CLO | [[YLO]] | ระดับ (ว่าง = "ยังไม่กำหนด")
   - > [!danger] ถ้าวิชาเอกนั้นไม่มีแถวระดับ M
3. เขียน LE_Vault/10_Curriculum/PLO/00_PLO_Index.md ใหม่ (generated: true)
   ตาราง id | ขอบเขต | ชื่ออังกฤษ | ประเภท | แถว IE | แถว SC | มี M?
   และตารางสัดส่วน Generic/Subject Specific ทั้งแบบรวม 13 ข้อ และแบบต่อวิชาเอก
4. ไม่มีตารางเทียบ ABET/Washington Accord ในเล่ม → ห้ามสร้างตารางนี้ และเขียนไว้ใน
   หัวข้อ "สิ่งที่เล่มไม่มี" ของดัชนี (ข้อ 3.10 ใน 01_Checklist_Curriculum_Data)
5. throw ถ้า PLO ได้ไม่ครบ 13 หรือ PLO ใดไม่มีแถวในแผนที่ของวิชาเอกที่ควรมี
   พิมพ์จำนวน PLO ต่อขอบเขต · จำนวน override ที่ใช้ · จำนวน PLO ที่ไม่มี M ต่อวิชาเอก
```

---

## Prompt B · เว็บ

```text
1. web/src/theme.js (เขียนมือได้ เพราะเป็นการออกแบบ ไม่ใช่ข้อมูลหลักสูตร)
   PLO_COLOR = { PLO_LE1: ..., PLO_IE1: ..., PLO_SC1: ... } คีย์เป็น string ทั้ง 13 ข้อ
   ใช้โทนเดียวกันต่อขอบเขต (LE / IE / SC) แต่แยกเฉดรายข้อ · contrast ข้อความ ≥ 4.5:1
   MAJOR_COLOR = { IE, SC, ALL }
   build-data.mjs ต้อง throw ถ้ามี PLO ใดใน PLOS ที่ไม่มีสีใน PLO_COLOR
2. web/src/outcomes.js (ฟังก์ชันคำนวณ ไม่เก็บข้อมูล)
   plosOfMajor(major)   ALL → 13 · IE → LE+IE (9) · SC → LE+SC (8)
   rowsOfPlo(id, major)  แถว MAPPING[major] ที่ plo === id · ALL = รวมสองวิชาเอกโดยมีคอลัมน์วิชาเอก
   typeShare(major)      สัดส่วน Generic/Subject Specific คำนวณจาก PLOS
3. หน้า web/src/pages/Plos.jsx (/plo)
   - แถบข้อความนำจาก META.ploIntro
   - สามส่วน "PLO ร่วม" "เฉพาะ IE" "เฉพาะ SC" แสดงตาม useMajor() (เลือก IE ต้องไม่เห็นส่วน SC)
   - การ์ด: รหัส · ชื่ออังกฤษ (ถ้ามาจาก override ให้มี <OverrideBadge target={id} field="en"/>) ·
     ถ้อยคำ · ป้ายประเภท · จำนวนแถว CLO ที่ส่งเข้า · ป้าย "ไม่มีระดับ M" จาก ISSUES
   - ตารางสัดส่วน Generic/Subject Specific จาก typeShare() ทั้งแบบรวมและต่อวิชาเอก
   - ไม่มีส่วนเทียบ ABET/WA: ห้าม render หัวข้อเปล่า (ซ่อนทั้งส่วน)
4. หน้า web/src/pages/PloDetail.jsx (/plo/:id)
   - ยอมรับ PLO_IE3 · plo_ie3 · IE3 แล้ว redirect (replace) ไป /plo/PLO_IE3 โดยคง ?major=
   - ไม่พบ → NotFound
   - ถ้า PLO อยู่นอกวิชาเอกที่เลือก (เช่น PLO_IE2 ขณะ ?major=SC) แสดงแถบ "PLO นี้ไม่อยู่ในวิชาเอก SC"
   - หัวข้อ: ถ้อยคำ · focus · ความต้องการ (ข้อความจากเล่ม + ป้าย N จากขั้นที่ 3) · แหล่งข้อมูล · นโยบาย
   - "รายวิชาที่ส่งเข้า" จาก rowsOfPlo() จัดกลุ่ม ชั้นปี → ภาค → รายวิชา → CLO
     แต่ละ CLO แสดงข้อความ ป้าย YLO และระดับ ถ้าระดับว่างใช้ <WarnBadge kind="noLevel"/>
     ข้อความ "ยังไม่กำหนดระดับ I/R/M" (FR-21) · ห้ามแสดงช่องว่างเปล่า
   - สรุปท้าย: จำนวนแถว จำนวนวิชา ชั้นปีที่ปรากฏ และแถบแดงถ้าไม่มีระดับ M
5. เพิ่ม PLO ทั้ง 13 ข้อใน codeInfo.js ให้ป้าย PLO ทุกจุดคลิกไป /plo/:id (คง ?major=)
```

---

## ตรวจรับ

- [ ] `/plo` แสดง 13 การ์ด · `/plo?major=IE` แสดง 9 · `/plo?major=SC` แสดง 8
- [ ] สัดส่วนบนหน้า: รวม 3 : 10 · IE 66.67% Subject Specific · SC 62.50%
- [ ] การ์ด IE1–IE5 และ SC1–SC4 มีชื่ออังกฤษพร้อมป้าย "แก้ไขจากเล่ม" ส่วน LE1–LE4 ไม่มีป้าย
- [ ] `/plo/PLO_LE1?major=IE` นับได้ 60 แถว 21 วิชา · `/plo/PLO_IE4?major=IE` ได้ 5 แถว 2 วิชา
- [ ] `/plo/PLO_SC2?major=SC` ได้ 7 แถว 3 วิชา
- [ ] มีป้ายระดับจริงเพียงสองจุด: 13005 (R) ใน PLO_IE3 และ 12006 (I) ใน PLO_LE4 นอกนั้นเป็นป้าย "ยังไม่กำหนดระดับ"
- [ ] `/plo/ie3` เปลี่ยนเป็น `/plo/PLO_IE3` และ `/plo/PLO_XX` ขึ้น NotFound
- [ ] ไม่มีหัวข้อ ABET หรือ Washington Accord ทั้งในหน้าเว็บและในโน้ตวอลต์
- [ ] ชี้ที่ป้าย `PLO_SC3` แล้ว tooltip ขึ้นถ้อยคำเดียวกับบนการ์ด

> [!warning] กับดักที่พบในเล่มนี้
> - **ชื่ออังกฤษไม่ได้ "ไม่มี" แต่ใช้วงเล็บคนละแบบ** LE ใช้ `[...]` ส่วน IE/SC ใช้ `(...)` ต่อท้ายถ้อยคำไทย ([[03_ch3_design]] ข้อ 10) ให้ยกค่าจากเล่มผ่าน override ห้ามตั้งชื่อเอง และเวลาแสดงถ้อยคำไทยอาจตัดวงเล็บท้ายออกเฉพาะตอนที่ค่าเท่ากับ `en`
> - **ถ้อยคำ PLO_IE1/IE3/IE4 ในตารางที่ 2 ข้อ 3.3 ไม่ตรงกับข้อ 3.2** (ขาดคำว่า "อุตสาหการ", ISS-43) ให้ถือข้อ 3.2 เป็นถ้อยคำทางการ
> - **ไม่มี PLO ใดมีระดับ M ทั้งสองวิชาเอก** และระดับ 2 แถวที่มีก็ขัดกันเอง: LE4 ได้ (I) ที่ปี 3 ทั้งที่ปรากฏตั้งแต่ปี 1 · IE3 ได้ (R) ตั้งแต่ครั้งแรกที่ปรากฏ
> - **PLO_IE4 มีเพียง 2 รายวิชา** และ PLO ของวิชาเอกไม่ปรากฏในปี 4 เลย (สหกิจและโครงงานผูกเฉพาะ PLO ร่วม, ISS-18)
> - **PLO_LE1 รับ 60 จาก 137 แถวของ IE (44%)** ขณะที่ IE4 รับ 5 แถว (ISS-19) หน้าเว็บควรทำให้เห็นความไม่สมดุลนี้ ไม่ใช่ซ่อนด้วยการเรียงตามรหัส
> - **LE2 ถูกจัดเป็น Generic** แม้เนื้อหาเป็นกฎหมาย ความปลอดภัย และจรรยาบรรณวิศวกรรม แสดงตามเล่ม แต่ไม่ควรใช้เป็นเหตุผลอธิบายสัดส่วน
> - **ไม่มีตารางเทียบ ABET/WA ราย PLO** แม้ชื่ออังกฤษ (Engineering Design, Investigation, Modern Tools) จะคล้ายคุณลักษณะของ WA/ABET ห้ามสร้างตารางเทียบขึ้นเอง
> - **IE มี 5 ข้อ แต่ SC มี 4 ข้อ** layout แบบสองคอลัมน์ที่จับคู่ IE_n กับ SC_n จะชวนให้เข้าใจผิดว่าเป็นคู่เทียบกัน

---

⬅ [[03_Stakeholders_and_Needs|ขั้นที่ 3]] · [[00_Tutorial_Home|สารบัญ]] · ➡ [[05_YLO|ขั้นที่ 5 · YLO]]
