export type SourceCategory = 'Policies' | 'Findings' | 'Remediations' | 'Access Reviews' | 'Past Cases';
export interface SourceRecord {
  id: string;
  title: string;
  category: SourceCategory;
  kind: 'Documents' | 'Cases' | 'Tables';
  tone: string;
  date: string;
  description: string;
  details: Record<string, unknown>;
  content: string;
  origin: 'seed' | 'local' | 'indexed';
  status?: 'pending' | 'indexing' | 'indexed' | 'failed';
}
export interface FindingRequest { control_id: string; department: string; finding: string; evidence_ref: string | null }
export interface RecalledMemory { mem_id: string; type: string; trust: string; as_of: string; subject: string; is_current: boolean; superseded_by: string | null; text: string; relevance: number | null; filename?: string; source_id?: string; page?: number; lines?: string; section?: string }
export interface DimensionMatch { rating: 'match' | 'partial' | 'none' | 'unknown'; reason: string }
export interface RelatedFinding { finding_id: string; control_id: string; department: string; raised_date: string; summary: string; same_control_id: boolean; is_recurrence_candidate: boolean; comparison: Record<string, DimensionMatch>; memory_ids: string[] }
export interface DirectReference { source_id: string; filename: string; category: string; snippet: string; page?: number; lines?: string; section?: string }
export interface Analysis {
  analysis_id: string;
  status: 'suspected';
  possible_recurrence: boolean;
  recurrence_confidence: 'low' | 'medium' | 'high' | null;
  related_past_findings: RelatedFinding[];
  previous_root_cause: { text: string; as_of: string; source_mem_ids: string[] } | null;
  previous_remediation: { text: string; outcome: string; evidence_ref: string | null; source_mem_ids: string[] } | null;
  explanation: string;
  memories_used: RecalledMemory[];
  deterministic_checks: {kind: string; control_id: string; severity: string; explanation: string; sources: string[]}[];
  warnings: string[];
  references?: DirectReference[];
}
export interface ConfirmationRequest { analysis_id: string; decision: 'confirm_recurrence' | 'not_recurrence' | 'correct'; linked_finding_ids: string[]; confirmed_root_cause?: string | null; confirmed_remediation?: string | null; outcome: 'open' | 'remediated_with_evidence' | 'remediated_no_evidence' | 'accepted_risk'; analyst: string; note?: string | null }
export interface ConfirmationResult { ok: true; trust: 'verified'; retained_mem_ids: string[]; retrievable: boolean; message: string }
export interface Reference { id: string; sourceId: string; title: string; category: string; location: string; snippet: string; historical: boolean }
export interface MemoryHit { id: string; text: string; type: string; date: string | null; relevance: string; }
export interface Flag { id: string; control_id: string; kind: string; description: string; severity: "critical" | "high" | "medium" | "low"; state: "open" | "resolved" | "false_alarm"; explanation: string; sources: string[]; }
export interface ReadinessReport { score: number; total_controls: number; flags: Flag[]; }
export interface Message { id: string; role: 'user' | 'assistant'; text: string; error?: boolean; analysis?: Analysis; references?: Reference[]; memoryEnabled?: boolean; confirmation?: ConfirmationResult; sources?: string[]; memories?: MemoryHit[]; }
