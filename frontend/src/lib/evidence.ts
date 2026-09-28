import type { Analysis, Reference, SourceRecord } from '../types/audit';
export function referencesFor(analysis: Analysis, sources: SourceRecord[]): Reference[] {
  const refs: Reference[] = (analysis.references || []).map(r=>({id:r.source_id,sourceId:r.source_id,title:r.filename,category:r.category,location:location(r),snippet:r.snippet,historical:false}));
  for (const memory of analysis.memories_used) {
    const sourceId = memory.source_id || memory.subject || memory.mem_id;
    const source = sources.find(s=>s.id===sourceId);
    const existing = refs.find(r=>r.sourceId===sourceId);
    if (existing) continue;
    refs.push({id:memory.mem_id,sourceId,title:memory.filename || source?.title || memory.mem_id,category:source?.category || memory.type.replaceAll('_',' '),location:location(memory),snippet:memory.text,historical:true});
  }
  return refs;
}
function location(reference: { page?: number; lines?: string; section?: string }) { return [reference.page ? `Page ${reference.page}` : '', reference.lines ? `Lines ${reference.lines}` : '', reference.section ? `Section ${reference.section}` : ''].filter(Boolean).join(' · '); }
export function relatedCases(analysis: Analysis) {
  const known = new Set(analysis.memories_used.map(m=>m.mem_id));
  return analysis.related_past_findings.filter(f=>f.memory_ids.length && f.memory_ids.every(id=>known.has(id))).slice(0,3);
}
export function sourcedClaim(ids: string[], analysis: Analysis) { const known = new Set(analysis.memories_used.map(m=>m.mem_id)); return ids.length > 0 && ids.every(id=>known.has(id)); }
