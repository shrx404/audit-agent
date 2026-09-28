import { DocumentIcon, Icon } from '../Icon';
import type { Analysis, Reference, MemoryHit } from '../../types/audit';
import { relatedCases } from '../../lib/evidence';
export function MemoryPanel({references,analysis,memories,allowHistory,onReference,onCase}:{references:Reference[];analysis?:Analysis;memories?:MemoryHit[];allowHistory:boolean;onReference:(r:Reference)=>void;onCase:(id:string)=>void}) {
  const visible=references.filter(r=>allowHistory||!r.historical);
  const cases=analysis&&allowHistory?relatedCases(analysis):[];
  const uniqueMemories: MemoryHit[] = [];
  const sortedMem = (memories || []).slice().sort((a, b) => b.text.length - a.text.length);
  for (const m of sortedMem) {
    if (!uniqueMemories.some(u => {
      const minLen = Math.min(u.text.length, m.text.length, 30);
      return u.text.substring(0, minLen) === m.text.substring(0, minLen);
    })) {
      uniqueMemories.push(m);
    }
  }
  return <aside className="references-panel" aria-label="References used">

    <header className="references-header"><h2>References used</h2>{!!visible.length&&<span>{visible.length}</span>}</header><div className="references-scroll">{visible.length ? <div className="reference-list">{visible.map((r,i)=><button className="reference-item" key={r.id} onClick={()=>onReference(r)}><span className="reference-heading"><DocumentIcon filename={r.title}/><strong>{r.title}</strong><span className="reference-number">{i+1}</span></span><span className="reference-meta">{r.category}{r.location&&` · ${r.location}`}</span><span className="reference-snippet">{r.snippet.length>185?`${r.snippet.slice(0,182)}…`:r.snippet}</span></button>)}</div> : <div className="references-empty"><Icon name="file" size={21}/><p>Sources cited in your answer<br/>will appear here.</p></div>}
    
    <section className="past-cases">
      <h3>Recalled Context</h3>
      {uniqueMemories.length ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
          {uniqueMemories.map((m, i) => (
            <div key={i} style={{ padding: '0.75rem', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '6px', fontSize: '0.8125rem', lineHeight: '1.4', color: 'rgba(255,255,255,0.8)' }}>
              {m.text}
            </div>
          ))}
        </div>
      ) : <p className="cases-empty">No recalled context.</p>}
    </section>

    <section className="past-cases"><h3>Past similar cases</h3>{cases.length ? cases.map(c=><button key={c.finding_id} className="past-case" onClick={()=>onCase(c.finding_id)}><Icon name="history" size={14}/><span><strong>{c.finding_id}</strong><span>{c.summary}</span></span><Icon name="chevron-right" size={12}/></button>):<p className="cases-empty">No related cases to show.</p>}</section></div></aside>;
}
