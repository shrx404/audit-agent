import test from 'node:test';
import assert from 'node:assert/strict';
import { referencesFor, relatedCases } from '../src/lib/evidence.ts';
const memory=(id,subject,text)=>({mem_id:id,subject,text,type:'finding',trust:'verified',as_of:'2024-01-01',is_current:true,superseded_by:null,relevance:null});
test('references contain only evidence used, preserve locators, and group a source once',()=>{
 const result={references:[{source_id:'direct',filename:'current.pdf',category:'Findings',snippet:'Current evidence',page:3}],memories_used:[memory('M-1','F-1','First fact'),memory('M-2','F-1','Another fact')]};
 const refs=referencesFor(result,[{id:'F-1',title:'F-1.md',category:'Findings'},{id:'unused',title:'never-used.md'}]);
 assert.equal(refs.length,2);assert.equal(refs[0].location,'Page 3');assert.equal(refs[1].title,'F-1.md');assert.equal(refs[1].location,'');assert.equal(refs.some(r=>r.title==='never-used.md'),false);
});
test('similar cases are capped at three with no fabricated padding or unsourced links',()=>{
 const result={memories_used:[memory('M-1','F-1','fact')],related_past_findings:[1,2,3,4].map(i=>({finding_id:`F-${i}`,memory_ids:['M-1']}))};
 assert.equal(relatedCases(result).length,3);
 assert.equal(relatedCases({...result,related_past_findings:[{finding_id:'unbacked',memory_ids:['M-unknown']}]}).length,0);
 assert.equal(relatedCases({...result,related_past_findings:[]}).length,0);
});
