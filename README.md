# LE_EN_KSU · หลักสูตร วศ.บ. วิศวกรรมโลจิสติกส์ (ปรับปรุง พ.ศ. 2570)

เว็บไซต์และ Obsidian vault ของหลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมโลจิสติกส์ มหาวิทยาลัยกาฬสินธุ์ ซึ่งสร้างจากเล่มหลักสูตรโดยตรง และใช้ template จาก [KSU-AI-EN](https://github.com/babankbro/KSU-AI-EN)

> ร่างเพื่อพิจารณา — ยังไม่ใช่ฉบับที่ผ่านการอนุมัติจากสภามหาวิทยาลัย

## โครงสร้าง

| โฟลเดอร์ | เนื้อหา |
|---|---|
| `doc_ref/` | เล่มหลักสูตร (.docx/.pdf) และภาคผนวก ก–ง — **แหล่งข้อมูลต้นทาง · ไม่รวมใน repo** (ขอไฟล์จากผู้รับผิดชอบหลักสูตร แล้ววางในโฟลเดอร์นี้ก่อนรันตัวดึงข้อมูล) |
| `doc_notes/` | บันทึกการอ่านเล่มทีละหมวด |
| `LE_web/` | ราก Obsidian vault + เว็บ |
| `LE_web/LE_Vault/` | Requirements (checklist · SRS · ทะเบียนข้อสังเกต) · Build Tutorial 14 ขั้น · โน้ตรายวิชา/PLO/YLO ที่สร้างอัตโนมัติ |
| `LE_web/web/` | เว็บ React 18 + Vite 5 (20 เส้นทาง · สลับวิชาเอก IE/SC) |
| `LE_web/tools/` | ตัวดึงข้อมูลจากเล่ม · ตัวสร้างโน้ตในวอลต์ · ตัวตรวจลิงก์ |
| `LE_web/data/curriculum.json` | ข้อมูลหลักสูตรเชิงโครงสร้าง (แหล่งข้อมูลเดียวของวอลต์และเว็บ) |

## ไปป์ไลน์ข้อมูล

```text
doc_ref/*.docx ──extract_curriculum.py──▶ data/curriculum.json ──build_vault.py──▶ LE_Vault/10_Curriculum/
                                                    └──web/scripts/build-data.mjs──▶ web/src/generated/ ──▶ เว็บ
```

## คำสั่ง (รันที่ `LE_web/`)

```bash
pip install python-docx
python tools/extract_curriculum.py     # เล่ม → data/curriculum.json
python tools/build_vault.py            # → โน้ตใน LE_Vault/10_Curriculum/
python tools/check_vault_links.py      # ตรวจลิงก์เสียในวอลต์
npm install --prefix web
npm run dev --prefix web               # เว็บสำหรับพัฒนา
npm run build --prefix web             # build → web/dist
```

เปิดวอลต์: Obsidian → Open folder as vault → เลือกโฟลเดอร์ `LE_web/`
