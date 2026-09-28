import test from 'node:test';
import assert from 'node:assert/strict';
import { AuditApi } from '../src/lib/api.ts';

const analysis = { analysis_id: 'AN-1', status: 'suspected', possible_recurrence: false, recurrence_confidence: null, related_past_findings: [], previous_root_cause: null, previous_remediation: null, explanation: 'No history found.', memories_used: [], deterministic_checks: [], warnings: ['no_history'] };
const request = { control_id: 'CC6.2', department: 'Support', finding: 'Review omitted', evidence_ref: null };
function fakeServer(properties, result = analysis) {
  const calls = [];
  const fetcher = async (url, options) => {
    calls.push({url, options});
    if (url.endsWith('/openapi.json')) return Response.json({paths:{'/analyze-finding':{post:{requestBody:{content:{'application/json':{schema:{properties}}}}}}}});
    return Response.json(result);
  };
  return { api: new AuditApi('http://audit.test', fetcher), calls };
}
test('memory off fails closed when backend does not advertise a memory flag', async () => {
  const {api,calls} = fakeServer({});
  await assert.rejects(api.analyze(request, false), /does not support/i);
  assert.equal(calls.filter(c=>c.url.endsWith('/analyze-finding')).length, 0);
});
test('memory off is transmitted when supported and never calls confirmation', async () => {
  const {api,calls} = fakeServer({use_memory:{type:'boolean'}});
  await api.analyze(request, false);
  const sent = calls.find(c=>c.url.endsWith('/analyze-finding'));
  assert.equal(JSON.parse(sent.options.body).use_memory, false);
  assert.equal(calls.some(c=>c.url.endsWith('/confirm-finding')), false);
});
test('memory off rejects historical data accidentally returned by backend', async () => {
  const {api} = fakeServer({use_memory:{type:'boolean'}}, {...analysis, memories_used:[{mem_id:'M-1',subject:'F-1',text:'History',type:'finding',trust:'verified',as_of:'2024-01-01',is_current:true,superseded_by:null,relevance:null}]});
  await assert.rejects(api.analyze(request, false), /historical/i);
});
test('legacy analysis contract is preserved when memory is on', async () => {
  const {api,calls} = fakeServer({});
  await api.analyze(request, true);
  assert.deepEqual(JSON.parse(calls.find(c=>c.url.endsWith('/analyze-finding')).options.body),request);
});
test('malformed analysis is rejected rather than rendered', async () => {
  const {api} = fakeServer({}, {answer:'Invented response'});
  await assert.rejects(api.analyze(request,true),/invalid/i);
});
test('confirmation requires an actual verified acknowledgement', async () => {
  const {api} = fakeServer({}, {ok:true,trust:'suspected',retained_mem_ids:[],retrievable:false,message:'Saved'});
  await assert.rejects(api.confirm({analysis_id:'AN-1',decision:'not_recurrence',analyst:'Analyst',linked_finding_ids:[],outcome:'open'}),/verified/i);
});
