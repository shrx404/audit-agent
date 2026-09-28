import type {
  Analysis,
  ConfirmationRequest,
  ConfirmationResult,
  FindingRequest,
  MemoryHit,
  ReadinessReport,
  SourceRecord,
} from "../types/audit";

type JsonObject = Record<string, unknown>;
function object(value: unknown): value is JsonObject {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function strings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((v) => typeof v === "string");
}
function resolveSchema(
  value: unknown,
  document: JsonObject,
  depth = 0,
): JsonObject {
  if (!object(value) || depth > 8) return {};
  if (typeof value.$ref === "string" && value.$ref.startsWith("#/")) {
    const target = value.$ref
      .slice(2)
      .split("/")
      .reduce<unknown>((v, key) => (object(v) ? v[key] : undefined), document);
    return resolveSchema(target, document, depth + 1);
  }
  return value;
}
function validAnalysis(value: unknown): value is Analysis {
  if (
    !object(value) ||
    typeof value.analysis_id !== "string" ||
    value.status !== "suspected" ||
    typeof value.explanation !== "string" ||
    typeof value.possible_recurrence !== "boolean" ||
    !strings(value.warnings)
  )
    return false;
  if (
    !Array.isArray(value.memories_used) ||
    !value.memories_used.every(
      (m) =>
        object(m) &&
        typeof m.mem_id === "string" &&
        typeof m.text === "string" &&
        typeof m.type === "string" &&
        typeof m.trust === "string" &&
        typeof m.as_of === "string",
    )
  )
    return false;
  if (
    !Array.isArray(value.related_past_findings) ||
    !value.related_past_findings.every(
      (f) =>
        object(f) &&
        typeof f.finding_id === "string" &&
        typeof f.summary === "string" &&
        strings(f.memory_ids) &&
        object(f.comparison) &&
        Object.values(f.comparison).every(
          (d) =>
            object(d) &&
            typeof d.reason === "string" &&
            typeof d.rating === "string",
        ),
    )
  )
    return false;
  if (
    !Array.isArray(value.deterministic_checks) ||
    !value.deterministic_checks.every(
      (f) =>
        object(f) && typeof f.explanation === "string" && strings(f.sources),
    )
  )
    return false;
  for (const key of ["previous_root_cause", "previous_remediation"]) {
    const claim = value[key];
    if (
      claim !== null &&
      (!object(claim) ||
        typeof claim.text !== "string" ||
        !strings(claim.source_mem_ids))
    )
      return false;
  }
  if (
    value.references !== undefined &&
    (!Array.isArray(value.references) ||
      !value.references.every(
        (r) =>
          object(r) &&
          typeof r.source_id === "string" &&
          typeof r.filename === "string" &&
          typeof r.category === "string" &&
          typeof r.snippet === "string",
      ))
  )
    return false;
  return true;
}

// All network contracts live here. Analysis never calls the confirmation/write path.
export class AuditApi {
  private base: string;
  private fetcher: typeof fetch;
  constructor(base: string, fetcher: typeof fetch = fetch) {
    this.base = base.replace(/\/$/, "");
    this.fetcher = fetcher;
  }
  private async request(path: string, init?: RequestInit): Promise<unknown> {
    if (!this.base)
      throw new Error(
        "The audit agent is not connected yet. Your sources are available to browse; analysis will be available once the backend is connected.",
      );
    let response: Response;
    try {
      response = await this.fetcher(`${this.base}${path}`, {
        ...init,
        signal: AbortSignal.timeout(45000),
      });
    } catch {
      throw new Error(
        "The audit agent could not be reached. Check the connection and try again.",
      );
    }
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      throw new Error("The audit agent returned an invalid response.");
    }
    if (!response.ok)
      throw new Error(
        object(data) && typeof data.error === "string"
          ? data.error
          : `The request could not be completed (${response.status}). Please try again.`,
      );
    return data;
  }
  async analyze(input: FindingRequest, useMemory: boolean): Promise<Analysis> {
    let supportsMemory = false;
    try {
      const spec = await this.request("/openapi.json");
      if (object(spec) && object(spec.paths)) {
        const path = spec.paths["/analyze-finding"];
        const operation = object(path) && object(path.post) ? path.post : {};
        const body = resolveSchema(operation.requestBody, spec);
        const content =
          object(body.content) && object(body.content["application/json"])
            ? body.content["application/json"]
            : {};
        const schema = resolveSchema(content.schema, spec);
        supportsMemory =
          object(schema.properties) &&
          object(schema.properties.use_memory) &&
          schema.properties.use_memory.type === "boolean";
      }
    } catch (error) {
      if (!useMemory) throw error;
    }
    if (!useMemory && !supportsMemory)
      throw new Error(
        "This backend does not support analysis without historical recall yet. No analysis was sent.",
      );
    const payload = supportsMemory
      ? { ...input, use_memory: useMemory }
      : input;
    const result = await this.request("/analyze-finding", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!validAnalysis(result))
      throw new Error("The audit agent returned an invalid analysis response.");
    if (
      !useMemory &&
      (result.memories_used.length ||
        result.related_past_findings.length ||
        result.possible_recurrence ||
        result.previous_root_cause ||
        result.previous_remediation)
    )
      throw new Error(
        "The backend returned historical context for a source-only request. This response has been withheld.",
      );
    return result;
  }
  async confirm(input: ConfirmationRequest): Promise<ConfirmationResult> {
    const result = await this.request("/confirm-finding", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    if (
      !object(result) ||
      result.ok !== true ||
      result.trust !== "verified" ||
      !strings(result.retained_mem_ids) ||
      !result.retained_mem_ids.length ||
      typeof result.retrievable !== "boolean" ||
      typeof result.message !== "string"
    )
      throw new Error(
        "The backend did not acknowledge a verified retained memory. Nothing has been marked confirmed.",
      );
    return result as unknown as ConfirmationResult;
  }
  async upload(file: File): Promise<{ source_id: string }> {
    // No ingestion route exists in the current MVP contract. Configure the real route and field after integrating the backend.
    const path = process.env.NEXT_PUBLIC_SOURCE_UPLOAD_PATH;
    const field = process.env.NEXT_PUBLIC_SOURCE_UPLOAD_FIELD;
    if (!path || !field || !path.startsWith("/") || path.startsWith("//"))
      throw new Error(
        "Source indexing is not connected yet. The file is available locally but has not been indexed.",
      );
    const body = new FormData();
    body.append(field, file);
    const result = await this.request(path, { method: "POST", body });
    if (
      !object(result) ||
      result.indexed !== true ||
      typeof result.source_id !== "string"
    )
      throw new Error(
        "The backend has not confirmed that this file was indexed. You can retry when indexing is available.",
      );
    return { source_id: result.source_id };
  }
  async ask(question: string, useMemory: boolean): Promise<{ answer: string; sources: string[]; memories: MemoryHit[] }> {
    const result = await this.request("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, use_memory: useMemory }),
    });
    return result as { answer: string; sources: string[]; memories: MemoryHit[] };
  }
  async getReadiness(): Promise<ReadinessReport> {
    const result = await this.request("/readiness");
    return result as ReadinessReport;
  }
  async getSources(): Promise<SourceRecord[]> {
    try {
      const result = await this.request("/sources");
      return Array.isArray(result) ? result : [];
    } catch {
      return [];
    }
  }
}
export const auditApi = new AuditApi(
  process.env.NEXT_PUBLIC_API_URL || "/api",
);
