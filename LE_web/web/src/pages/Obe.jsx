import { useState } from "react";
import { Link } from "react-router-dom";
import Alluvial from "../Alluvial.jsx";
import { VIEWS, TYPE, PRIO_COLOR } from "../alluvialViews.js";
import { SOURCES, NEEDS, PRIORITY, PLO_NEEDS } from "../generated/obe.js";
import { PageHead, Section, PloChip, Warn } from "./ui.jsx";
import { useMajor } from "../major.jsx";
import { plosOf, ylosOf, mapRows } from "../lib.js";
import { ACTIVITIES } from "../generated/program.js";

/* สายธาร OBE: ความต้องการ → PLO → YLO → CLO (SRS: FR-10) */
export default function Obe() {
  const { major } = useMajor();
  const plos = plosOf(major);
  const ylos = ylosOf(major);
  const rows = mapRows(major);
  const [view, setView] = useState(VIEWS[0].id);
  const cur = VIEWS.find(v => v.id === view);
  const vd = cur.fn(major);
  const unused = SOURCES.filter(s => !NEEDS.some(n => n.ev.includes(s.id)));

  return (
    <main>
      <PageHead eyebrow="ผลลัพธ์การเรียนรู้" title="ขั้นตอน OBE"
        lead="ความต้องการของผู้มีส่วนได้ส่วนเสียและนโยบายระดับชาติ ถูกแปลงเป็น PLO แล้วกระจายลง YLO รายชั้นปี และ CLO รายวิชา"
        crumbs={[{ label: "ขั้นตอน OBE" }]} />
      <div className="wrap">
        <Section id="flow" title="ภาพรวม">
          <div className="statgrid">
            <div className="statbox"><b>{SOURCES.filter(s => s.type === "direct").length} + {SOURCES.filter(s => s.type !== "direct").length}</b><span>ผู้มีส่วนได้ส่วนเสียโดยตรง + แหล่งหลักฐานอื่น</span></div>
            <div className="statbox"><b>{NEEDS.length}</b><span>ความต้องการ (N01–N14)</span></div>
            <div className="statbox"><b>{plos.length}</b><span>PLO</span></div>
            <div className="statbox"><b>{ylos.length}</b><span>YLO</span></div>
            <div className="statbox"><b>{rows.length}</b><span>CLO ในแผนที่</span></div>
          </div>
          <div className="warnlist"><Warn iss="ISS-25">เล่มไม่ระบุวิธีเก็บข้อมูล ขนาดตัวอย่าง และช่วงเวลาสำรวจผู้มีส่วนได้ส่วนเสีย</Warn></div>
        </Section>

        <Section id="alluvial" title="แผนภาพสายธารความเชื่อมโยง (Alluvial Diagram)"
          sub={`เลือกมุมมองเพื่อดูว่าแต่ละองค์ประกอบไหลเชื่อมกันอย่างไร · ${major === "ALL" ? "ทุกวิชาเอก" : `วิชาเอก ${major}`}`}>
          <div className="alv-pick" role="tablist">
            {VIEWS.map(v => (
              <button key={v.id} role="tab" aria-selected={view === v.id} className={`alv-tab${view === v.id ? " on" : ""}`}
                onClick={() => setView(v.id)}>{v.name}</button>
            ))}
          </div>
          <p className="alv-desc">{cur.desc}</p>
          <Alluvial key={view + major} columns={vd.columns} nodes={vd.nodes} links={vd.links} height={vd.height} />
          {view === "evidence" && unused.length > 0 && (
            <div className="warnlist"><Warn iss="ISS-34">{unused.map(s => s.name).join(", ")} ไม่ถูกอ้างเป็นหลักฐานของความต้องการข้อใด (แท่งที่ไม่มีสายออก)</Warn></div>
          )}
        </Section>

        <Section id="sources" title="① แหล่งหลักฐาน" sub="ภาคผนวก ง ข้อ 2 — แยกผู้มีส่วนได้ส่วนเสียโดยตรงออกจากมาตรฐาน ข้อมูลอาชีพ และนโยบาย">
          <div className="tblwrap">
            <table className="tbl">
              <thead><tr><th>รหัส</th><th>แหล่งหลักฐาน</th><th>ประเภท</th><th className="r">ความต้องการที่รองรับ</th></tr></thead>
              <tbody>
                {SOURCES.map(s => {
                  const ns = NEEDS.filter(n => n.ev.includes(s.id));
                  return (
                    <tr key={s.id}>
                      <td className="mono">{s.id}</td><td>{s.name}</td>
                      <td><span className="tags"><i className="gdot" style={{ background: TYPE[s.type].color }} /> {TYPE[s.type].label}</span></td>
                      <td className="r">{ns.length ? ns.map(n => n.id).join(", ") : <span className="warn-badge">ไม่มี</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Section>

        <Section id="n14" title="② ความต้องการ 14 ประเด็น" sub="ภาคผนวก ง ข้อ 6–8 — ข้อกำหนดสมรรถนะ หลักฐาน ระดับความสำคัญ และ PLO ที่รับไป">
          <div className="tags" style={{ marginBottom: 10 }}>
            {PRIORITY.filter(p => p.id !== "P3").map(p => <span key={p.id} className="pill" style={{ "--pc": PRIO_COLOR[p.id] }}>{p.id} · {p.label}</span>)}
          </div>
          <div className="tblwrap">
            <table className="tbl">
              <thead><tr><th>ประเด็น</th><th>ความต้องการ</th><th>ข้อกำหนดสมรรถนะ</th><th>หลักฐาน</th><th>PLO</th></tr></thead>
              <tbody>
                {NEEDS.map(n => {
                  const ps = plos.filter(p => (PLO_NEEDS[p.id] || []).includes(n.id));
                  const direct = n.ev.some(e => SOURCES.find(s => s.id === e)?.type === "direct");
                  return (
                    <tr key={n.id}>
                      <td><span className="sev" style={{ background: PRIO_COLOR[n.prio] }}>{n.id}</span><span className="sub">{n.prio}</span></td>
                      <td>{n.text}</td><td className="mut">{n.comp}</td>
                      <td>{n.ev.join(", ")}{!direct && <span className="sub">⚠ ไม่มีหลักฐานโดยตรง</span>}</td>
                      <td><span className="tags">{ps.map(p => <PloChip key={p.id} id={p.id} small />)}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="hint">{PRIORITY.find(p => p.id === "P3")?.id} · {PRIORITY.find(p => p.id === "P3")?.label}: {PRIORITY.find(p => p.id === "P3")?.items}</p>
        </Section>

        <Section id="needs" title="③ ความคาดหวังรายข้อ PLO" sub="ตารางที่ 1 หมวด 3.3 ของเล่ม">
          <div className="tblwrap">
            <table className="tbl">
              <thead><tr><th>PLO</th><th>ความต้องการ/ความคาดหวัง</th><th>แหล่งข้อมูล</th></tr></thead>
              <tbody>
                {plos.map(p => (
                  <tr key={p.id}>
                    <td><PloChip id={p.id} small /></td>
                    <td><ul className="numlist">{(p.needs || []).map((n, i) => <li key={i}>{n}</li>)}</ul></td>
                    <td>{(p.sources || []).join(" · ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section id="cascade" title="④ PLO → YLO → CLO" sub="จำนวนที่กระจายลงแต่ละชั้น">
          <div className="tblwrap">
            <table className="tbl">
              <thead><tr><th>PLO</th><th>Generic/Specific</th><th className="r">YLO</th><th className="r">รายวิชา</th><th className="r">CLO</th></tr></thead>
              <tbody>
                {plos.map(p => {
                  const r = rows.filter(x => x.plo === p.id);
                  return (
                    <tr key={p.id}>
                      <td><Link className="lnk" to={`/plo/${p.id}`}>{p.id}</Link><span className="sub">{p.en}</span></td>
                      <td>{p.outcomeType}</td>
                      <td className="r">{p.ylos.filter(y => ylos.some(o => o.id === y)).length}</td>
                      <td className="r">{new Set(r.map(x => x.code)).size}</td>
                      <td className="r">{r.length}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Section>

        <Section id="activities" title="⑤ กิจกรรมเสริมหลักสูตร" sub="หมวด 3.4 ของเล่ม">
          {ACTIVITIES.rows.map(r => (
            <div key={r[0]} className="box">
              <h3>ชั้นปีที่ {r[0]} · {r[1].split(" - ")[0]}</h3>
              <p className="hint">{r[1].split(" - ").slice(1).join(" - ").split("ที่มา:")[0]}</p>
              {r[2] && <p style={{ fontSize: ".85rem", margin: "6px 0 0" }}><b>ผลลัพธ์ที่เกิด:</b> {r[2]}</p>}
            </div>
          ))}
          <div className="warnlist"><Warn iss="ISS-46">ข้อความในเล่มยังมีโน้ตร่างค้าง เช่น "N13"</Warn></div>
        </Section>
      </div>
    </main>
  );
}
