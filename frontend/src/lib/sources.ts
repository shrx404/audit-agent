import corpus from './corpus.json';
import type { SourceCategory, SourceRecord } from '../types/audit';

function record(id: string, title: string, category: SourceCategory, description: string, date: string, details: Record<string, unknown>, file: string): SourceRecord {
  const content = `# ${title.replace(/\.md$/, '')}\n\n${description}\n\n${Object.entries(details).map(([key,value])=>`- ${key.replaceAll('_',' ')}: ${value ?? 'Not recorded'}`).join('\n')}\n`;
  return { id, title, category, kind:'Documents', tone:'muted', description, date, details:{...details, source_file:`backend/data/${file}.json`}, content, origin:'seed' };
}
// Markdown views of actual seed records, not invented PDF/Word documents or Hindsight results.
export const sources: SourceRecord[] = [
  ...corpus.policy_changes.map((p,i)=>record(`policy_changes:${i}`,'access_review_policy_v3.md','Policies',p.description,p.date,p,'policy_changes')),
  ...corpus.findings.map(f=>record(f.id,`${f.id}.md`,f.audit_cycle < 2024 ? 'Past Cases' : 'Findings',f.auditor_note,f.raised_date,f,'findings')),
  ...corpus.remediations.map(r=>record(r.id,`${r.id}.md`,'Remediations',`Remediation for ${r.finding_id}. Owner: ${r.owner}. Status: ${r.status}.`,r.opened_date,r,'remediations')),
  ...corpus.controls.filter(c=>c.id==='CC6.2').map(c=>record(c.id,'user_access_reviews.md','Access Reviews',c.description,'',c,'controls')),
];
export const supportedExtensions = ['txt','md','doc','docx','pdf'];
export function fileExtension(name: string) { return name.split('.').pop()?.toLowerCase() || ''; }
export function isSupportedFile(name: string) { return supportedExtensions.includes(fileExtension(name)); }
