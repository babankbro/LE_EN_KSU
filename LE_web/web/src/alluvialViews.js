/* ชุดข้อมูลแผนภาพสายธาร (Alluvial) ของหลักสูตรวิศวกรรมโลจิสติกส์ — สร้างเฉพาะเส้นที่ "เชื่อมได้จริง" จากเล่ม
   แหล่ง: ภาคผนวก ง (แหล่งหลักฐาน · N01–N14 · ความต้องการ→PLO · เครื่องมือ P3) · หมวด 3.2 (YLO→PLO)
          หมวด 4.5 (CLO→YLO→PLO) · หมวด 5.2 (กลยุทธ์การสอน) · หมวด 6.1 (วิธีประเมิน น้ำหนัก ช่วงเวลา)
   ทุกมุมมองรับ major ("IE" | "SC" | "ALL") แล้วกรอง PLO/YLO/แผนที่ให้ตรงวิชาเอก */
import { SOURCES, NEEDS, PLO_NEEDS, TOOLS } from "./generated/obe.js";
import { STRATEGIES, ASSESSMENT } from "./generated/teaching.js";
import { plosOf, ylosOf, mapRows, majorsOf, ploColor, ploShort, YEAR_COLOR, GROUP, GROUP_SHORT, COURSE } from "./lib.js";

const TYPE = {
  direct: { label: "ผู้มีส่วนได้ส่วนเสียโดยตรง", color: "var(--sc)" },
  standard: { label: "มาตรฐาน/กรอบคุณวุฒิ", color: "var(--ie)" },
  occupation: { label: "ข้อมูลอาชีพและกำลังคน", color: "var(--g-el)" },
  policy: { label: "นโยบาย/ทิศทางสถาบัน", color: "var(--g-core)" },
};
const PRIO_COLOR = { P0: "var(--navy)", P1: "var(--navy2)", P2: "var(--g-core)" };
const cut = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

const ploNode = p => ({ id: `p:${p.id}`, col: "plo", label: ploShort(p.id), sub: cut(p.en || p.th, 34),
  color: ploColor(p.id), href: `/plo/${p.id}`, title: `${p.id} ${p.th}` });
const needNode = n => ({ id: `n:${n.id}`, col: "need", label: n.id, sub: cut(n.text, 36),
  color: PRIO_COLOR[n.prio], title: `${n.id} [${n.prio}] ${n.text}` });
const needsOf = plos => NEEDS.filter(n => plos.some(p => (PLO_NEEDS[p.id] || []).includes(n.id)));

/* ① แหล่งหลักฐาน → ความต้องการ → PLO */
function viewEvidence(major) {
  const plos = plosOf(major);
  const needs = needsOf(plos);
  const nodes = [], links = [];
  const srcs = SOURCES.filter(s => needs.some(n => n.ev.includes(s.id)) || s.type === "direct");
  srcs.forEach(s => nodes.push({ id: `s:${s.id}`, col: "src", label: cut(s.name, 30), sub: s.id,
    color: TYPE[s.type].color, title: `${s.id} ${s.name} · ${TYPE[s.type].label}` }));
  needs.forEach(n => nodes.push(needNode(n)));
  plos.forEach(p => nodes.push(ploNode(p)));
  needs.forEach(n => n.ev.forEach(e => links.push({ s: `s:${e}`, t: `n:${n.id}`, v: 1 })));
  plos.forEach(p => (PLO_NEEDS[p.id] || []).forEach(n => links.push({ s: `n:${n}`, t: `p:${p.id}`, v: 1 })));
  return {
    columns: [{ key: "src", label: "① แหล่งหลักฐาน" }, { key: "need", label: "② ความต้องการ N01–N14" }, { key: "plo", label: "③ PLO" }],
    nodes, links, height: 760,
  };
}

/* ② ความต้องการ → PLO → YLO → ชั้นปี */
function viewNeedPloYlo(major) {
  const plos = plosOf(major);
  const ylos = ylosOf(major);
  const nodes = [], links = [];
  needsOf(plos).forEach(n => nodes.push(needNode(n)));
  plos.forEach(p => nodes.push(ploNode(p)));
  ylos.forEach(y => nodes.push({ id: `y:${y.id}`, col: "ylo", label: y.id, color: YEAR_COLOR[y.year],
    href: `/ylo/${y.id}`, title: `${y.id} ${y.th}` }));
  [1, 2, 3, 4].forEach(y => nodes.push({ id: `yr:${y}`, col: "year", label: `ชั้นปีที่ ${y}`, color: YEAR_COLOR[y] }));
  plos.forEach(p => (PLO_NEEDS[p.id] || []).forEach(n => links.push({ s: `n:${n}`, t: `p:${p.id}`, v: 1 })));
  ylos.forEach(y => y.plos.filter(p => plos.some(x => x.id === p)).forEach(p => links.push({ s: `p:${p}`, t: `y:${y.id}`, v: 1 })));
  ylos.forEach(y => links.push({ s: `y:${y.id}`, t: `yr:${y.year}`, v: Math.max(1, y.plos.length) }));
  return {
    columns: [{ key: "need", label: "① ความต้องการ" }, { key: "plo", label: "② PLO" }, { key: "ylo", label: "③ YLO (นิยามหมวด 3.2)" }, { key: "year", label: "④ ชั้นปี" }],
    nodes, links, height: 820,
  };
}

/* ③ PLO → YLO → กลุ่มรายวิชา (นับ CLO จากแผนที่ 4.5) */
function viewPloYloGroup(major) {
  const rows = mapRows(major).map(r => ({ ...r, group: COURSE[r.code]?.group || "ge-req" }));
  const plos = plosOf(major).filter(p => rows.some(r => r.plo === p.id));
  const ylos = [...new Set(rows.map(r => r.ylo))].sort();
  const groups = [...new Set(rows.map(r => r.group))];
  const nodes = [], links = [];
  plos.forEach(p => nodes.push(ploNode(p)));
  ylos.forEach(y => {
    const yr = Number((y.match(/YLO(\d)/) || [])[1]) || 1;
    nodes.push({ id: `y:${y}`, col: "ylo", label: y, color: YEAR_COLOR[yr], href: `/ylo/${y}` });
  });
  groups.forEach(g => nodes.push({ id: `g:${g}`, col: "grp", label: GROUP_SHORT[g] || g, color: GROUP[g] ? `var(--g-${g.startsWith("el") ? "el" : g.startsWith("ge") ? "ge" : g})` : "var(--g-ge)",
    href: `/structure/${g}` }));
  const add = (map, k, v = 1) => map.set(k, (map.get(k) || 0) + v);
  const py = new Map(), yg = new Map();
  rows.forEach(r => { add(py, `${r.plo}|${r.ylo}`); add(yg, `${r.ylo}|${r.group}`); });
  py.forEach((v, k) => { const [p, y] = k.split("|"); links.push({ s: `p:${p}`, t: `y:${y}`, v }); });
  yg.forEach((v, k) => { const [y, g] = k.split("|"); links.push({ s: `y:${y}`, t: `g:${g}`, v }); });
  return {
    columns: [{ key: "plo", label: "① PLO" }, { key: "ylo", label: "② YLO (ตามแผนที่ 4.5)" }, { key: "grp", label: "③ กลุ่มรายวิชา" }],
    nodes, links, height: 900, unit: "CLO",
  };
}

/* ④ ความต้องการระดับเครื่องมือ (P3) → PLO → กลยุทธ์การสอน */
function viewToolPloStrategy(major) {
  const plos = plosOf(major);
  const nodes = [], links = [];
  const tools = TOOLS.filter(t => t.plos.some(p => plos.some(x => x.id === p)));
  tools.forEach(t => nodes.push({ id: `t:${t.id}`, col: "tool", label: cut(t.text, 30), sub: t.id, color: "var(--g-el)",
    title: `${t.id} ${t.text} → ${t.act}` }));
  plos.forEach(p => nodes.push(ploNode(p)));
  STRATEGIES.forEach((s, i) => nodes.push({ id: `st:${i}`, col: "strat", label: s.name.replace(/\s*\(.*$/, ""),
    sub: (s.name.match(/\(([^)]+)\)/) || [])[1] || "", color: "var(--navy2)", href: `/teaching#st-${i}`, title: s.name }));
  tools.forEach(t => t.plos.filter(p => plos.some(x => x.id === p)).forEach(p => links.push({ s: `t:${t.id}`, t: `p:${p}`, v: 1 })));
  STRATEGIES.forEach((s, i) => s.plos.filter(p => plos.some(x => x.id === p)).forEach(p => links.push({ s: `p:${p}`, t: `st:${i}`, v: 1 })));
  return {
    columns: [{ key: "tool", label: "① ความต้องการระดับเครื่องมือ (P3)" }, { key: "plo", label: "② PLO" }, { key: "strat", label: "③ กลยุทธ์การสอน (หมวด 5.2)" }],
    nodes, links, height: 720,
  };
}

/* ⑤ ความต้องการ → PLO → ชั้นปีที่ประเมิน (น้ำหนักจากหมวด 6.1) */
function viewNeedPloAssess(major) {
  const mjs = majorsOf(major);
  const plos = plosOf(major);
  const nodes = [], links = [];
  needsOf(plos).forEach(n => nodes.push(needNode(n)));
  plos.forEach(p => nodes.push(ploNode(p)));
  [1, 2, 3, 4].forEach(y => nodes.push({ id: `ay:${y}`, col: "when", label: `ประเมินปี ${y}`, color: YEAR_COLOR[y], href: `/assessment#ylo` }));
  plos.forEach(p => {
    const nn = PLO_NEEDS[p.id] || [];
    nn.forEach(n => links.push({ s: `n:${n}`, t: `p:${p.id}`, v: 100 / Math.max(nn.length, 1) }));
    const byYear = new Map();
    ASSESSMENT.filter(a => a.plo === p.id && a.majors.some(m => mjs.includes(m))).forEach(a => {
      const y = Number((a.when.match(/ปีการศึกษาที่\s*(\d)/) || [])[1]);
      if (y) byYear.set(y, (byYear.get(y) || 0) + (a.weight || 0) / (major === "ALL" && p.scope === "LE" ? 2 : 1));
    });
    byYear.forEach((v, y) => links.push({ s: `p:${p.id}`, t: `ay:${y}`, v }));
  });
  return {
    columns: [{ key: "need", label: "① ความต้องการ" }, { key: "plo", label: "② PLO" }, { key: "when", label: "③ ชั้นปีที่ประเมิน (น้ำหนัก %)" }],
    nodes, links, height: 760,
  };
}

export const VIEWS = [
  { id: "evidence", name: "① หลักฐาน → ความต้องการ → PLO", fn: viewEvidence,
    desc: "แหล่งหลักฐานแต่ละแหล่งรองรับความต้องการข้อใด (ภาคผนวก ง ข้อ 6) และความต้องการถูกแปลงเป็น PLO ข้อใด (ข้อ 8) — สีของแหล่ง: เขียว = ผู้มีส่วนได้ส่วนเสียโดยตรง · น้ำเงิน = มาตรฐาน · ม่วง = ข้อมูลอาชีพ · น้ำตาล = ทิศทางสถาบัน" },
  { id: "ylo", name: "② ความต้องการ → PLO → YLO → ชั้นปี", fn: viewNeedPloYlo,
    desc: "ไล่จากความต้องการลงไปถึงผลลัพธ์รายชั้นปีตามนิยาม YLO ในหมวด 3.2 — ช่วยให้เห็นว่า PLO ใดเริ่มพัฒนาตั้งแต่ปีไหน" },
  { id: "group", name: "③ PLO → YLO → กลุ่มรายวิชา", fn: viewPloYloGroup,
    desc: "ความหนาของสาย = จำนวน CLO ในแผนที่หมวด 4.5 ที่ส่งเข้า PLO ผ่าน YLO และมาจากกลุ่มรายวิชาใด (ไม่รวมวิชาศึกษาทั่วไปและวิชาเลือก ซึ่งเล่มไม่ได้ผูก CLO)" },
  { id: "tool", name: "④ เครื่องมือ (P3) → PLO → กลยุทธ์การสอน", fn: viewToolPloStrategy,
    desc: "ความต้องการระดับเครื่องมือ เช่น Excel/Power BI หรืองานคลังสินค้า ถูกส่งไปเป็นกิจกรรมของ PLO ใด (ภาคผนวก ง ข้อ 9) แล้ว PLO นั้นสอนด้วยกลยุทธ์ใด (หมวด 5.2)" },
  { id: "assess", name: "⑤ ความต้องการ → PLO → ชั้นปีที่ประเมิน", fn: viewNeedPloAssess,
    desc: "ความหนาของสายฝั่งขวา = น้ำหนักการประเมิน PLO ในแต่ละชั้นปี (หมวด 6.1) — เห็นได้ชัดว่า PLO_LE2–LE4 ถูกประเมินครั้งเดียวในปี 4" },
];

export { TYPE, PRIO_COLOR };
