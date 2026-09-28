import { DocumentIcon, Icon } from '../Icon';
import type { Analysis, Reference, ReadinessReport } from '../../types/audit';
import { relatedCases } from '../../lib/evidence';
export function MemoryPanel({references,analysis,readiness,allowHistory,onReference,onCase}:{references:Reference[];analysis?:Analysis;readiness?:ReadinessReport|null;allowHistory:boolean;onReference:(r:Reference)=>void;onCase:(id:string)=>void}) {
  const visible=references.filter(r=>allowHistory||!r.historical);
  const cases=analysis&&allowHistory?relatedCases(analysis):[];
  return <aside className="references-panel" aria-label="References used">
    {readiness && (
      <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'rgba(255,255,255,0.7)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Icon name="check" size={14} /> READINESS SCORE
        </h3>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
          <span style={{ fontSize: '3.75rem', fontWeight: 900, lineHeight: 1 }}>{readiness.score}</span>
          <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'rgba(255,255,255,0.5)', paddingBottom: '0.5rem' }}>/ 100</span>
        </div>
        <div style={{ width: '100%', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '9999px', height: '0.5rem', marginTop: '1.5rem', overflow: 'hidden' }}>
          <div style={{ backgroundColor: '#6366f1', height: '100%', width: `${readiness.score}%` }}></div>
        </div>
        <div style={{ marginTop: '1rem', fontSize: '0.75rem', fontWeight: 500, color: 'rgba(255,255,255,0.5)' }}>
          {readiness.total_controls} Total Controls Validated
        </div>
      </div>
    )}
    <header className="references-header"><h2>References used</h2>{!!visible.length&&<span>{visible.length}</span>}</header><div className="references-scroll">{visible.length ? <div className="reference-list">{visible.map((r,i)=><button className="reference-item" key={r.id} onClick={()=>onReference(r)}><span className="reference-heading"><DocumentIcon filename={r.title}/><strong>{r.title}</strong><span className="reference-number">{i+1}</span></span><span className="reference-meta">{r.category}{r.location&&` · ${r.location}`}</span><span className="reference-snippet">{r.snippet.length>185?`${r.snippet.slice(0,182)}…`:r.snippet}</span></button>)}</div> : <div className="references-empty"><Icon name="file" size={21}/><p>Sources cited in your answer<br/>will appear here.</p></div>}<section className="past-cases"><h3>Past similar cases</h3>{cases.length ? cases.map(c=><button key={c.finding_id} className="past-case" onClick={()=>onCase(c.finding_id)}><Icon name="history" size={14}/><span><strong>{c.finding_id}</strong><span>{c.summary}</span></span><Icon name="chevron-right" size={12}/></button>):<p className="cases-empty">No related cases to show.</p>}</section></div></aside>;
}
