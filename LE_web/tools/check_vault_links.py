"""ตรวจลิงก์ [[...]] ที่ชี้ไปยังโน้ตที่ไม่มีอยู่จริงในวอลต์ (SRS: VR-03)

ใช้:  python tools/check_vault_links.py
ออกด้วย exit code 1 เมื่อพบลิงก์เสีย เพื่อใช้ใน CI หรือ npm run check
ข้ามลิงก์ที่อยู่ในบล็อกโค้ด ``` เพราะเป็นตัวอย่างใน Prompt
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "LE_Vault"
LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

notes = {p.stem for p in VAULT.rglob("*.md")}
broken = []
for p in sorted(VAULT.rglob("*.md")):
    text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)          # inline code ก็เป็นตัวอย่าง ไม่ใช่ลิงก์จริง
    for m in LINK.finditer(text):
        target = m.group(1).strip().replace("\\", "")
        name = target.split("/")[-1]
        if name.endswith(".md"):
            name = name[:-3]
        if name not in notes:
            broken.append((p.relative_to(ROOT).as_posix(), target))

print(f"notes={len(notes)} broken={len(broken)}")
for f, t in broken:
    print(f"  {f}: [[{t}]]")
sys.exit(1 if broken else 0)
