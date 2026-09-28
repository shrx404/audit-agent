"use client";
import { useEffect, useRef, useState } from "react";
import { Header } from "../components/layout/Header";
import { SourceDataCorpus } from "../components/left-panel/SourceDataCorpus";
import { ChatWindow } from "../components/middle-panel/ChatWindow";
import { MemoryPanel } from "../components/right-panel/MemoryPanel";
import { ConfirmationForm } from "../components/ConfirmationForm";
import { DocumentIcon, Icon } from "../components/Icon";
import { auditApi } from "../lib/api";
import {
  sources as seedSources,
  isSupportedFile,
  fileExtension,
} from "../lib/sources";
import type {
  ConfirmationRequest,
  Message,
  Reference,
  SourceCategory,
  SourceRecord,
  ReadinessReport,
} from "../types/audit";

type Modal =
  | "settings"
  | "source"
  | "upload"
  | "context"
  | "confirm"
  | "reference"
  | "case"
  | null;
export default function Home() {
  const [sources, setSources] = useState(seedSources);
  const [memory, setMemory] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [readiness, setReadiness] = useState<ReadinessReport | null>(null);
  const [activeId, setActiveId] = useState("");
  const [selected, setSelected] = useState<SourceRecord | null>(null);
  const [modal, setModal] = useState<Modal>(null);
  const [mobileTab, setMobileTab] = useState("chat");
  const [pendingQuestion, setPendingQuestion] = useState("");
  const [control, setControl] = useState("");
  const [department, setDepartment] = useState("");
  const [uploadCategory, setUploadCategory] =
    useState<SourceCategory>("Findings");
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadIds, setUploadIds] = useState<string[]>([]);
  const [reviewMessage, setReviewMessage] = useState<Message | null>(null);
  const [confirmationBusy, setConfirmationBusy] = useState(false);
  const [confirmationError, setConfirmationError] = useState("");
  const [reference, setReference] = useState<Reference | null>(null);
  const [caseId, setCaseId] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const localFiles = useRef(new Map<string, File>());
  const active = messages.find((m) => m.id === activeId);
  useEffect(() => {
    if (modal) dialog.current?.showModal();
    else dialog.current?.close();
  }, [modal]);
  useEffect(() => {
    const fetchReadiness = async () => {
      try {
        const res = await fetch("/api/readiness");
        if (res.ok) {
          setReadiness(await res.json());
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchReadiness();
  }, []);
  const busy = confirmationBusy || uploading;
  function closeModal() {
    if (!busy) setModal(null);
  }
  function selectSource(source: SourceRecord) {
    setSelected(source);
    setModal("source");
  }
  function showReference(ref: Reference) {
    setReference(ref);
    setModal("reference");
  }
  function beginQuestion(question: string) {
    if (loading) return;
    const mentioned = sources.find(
      (s) => question.includes(s.id) && s.origin !== "local",
    );
    const source = mentioned || selected;
    const sourceControl = source?.details.control_id;
    if (typeof sourceControl === "string") setControl(sourceControl);
    void analyze(question);
  }
  async function analyze(question: string) {
    if (loading) return;
    const userId = crypto.randomUUID();
    const useMemory = memory;
    setMessages((m) => [...m, { id: userId, role: "user", text: question }]);
    setLoading(true);
    setActiveId("");
    setModal(null);

    // Create finding input
    const mentioned = sources.find(
      (s) => question.includes(s.id) && s.origin !== "local",
    );
    const current = mentioned || selected;
    let finalQuestion = question;
    if (current?.content) {
      finalQuestion = `${question}\n\nCurrent source (${current.title}, ${current.id}):\n${current.content.slice(0, 12000)}`;
    }

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: finalQuestion,
          use_memory: useMemory,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "An error occurred");
      }

      const id = crypto.randomUUID();
      setMessages((m) => [
        ...m,
        {
          id,
          role: "assistant",
          text: data.answer,
          sources: data.sources,
          memories: data.memories,
          memoryEnabled: useMemory,
        },
      ]);
      setActiveId(id);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to fetch response.";
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant", // Using assistant so it shows up on the left side
          text: errorMessage,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }
  async function confirm(input: ConfirmationRequest) {
    if (confirmationBusy || !reviewMessage) return;
    setConfirmationBusy(true);
    setConfirmationError("");
    try {
      const result = await auditApi.confirm(input);
      setMessages((m) =>
        m.map((item) =>
          item.id === reviewMessage.id
            ? { ...item, confirmation: result }
            : item,
        ),
      );
      setModal(null);
    } catch (error) {
      setConfirmationError(
        error instanceof Error
          ? error.message
          : "Confirmation could not be saved. Please try again.",
      );
    } finally {
      setConfirmationBusy(false);
    }
  }
  async function indexSource(source: SourceRecord, file: File) {
    setSources((items) =>
      items.map((s) => (s.id === source.id ? { ...s, status: "indexing" } : s)),
    );
    try {
      const result = await auditApi.upload(file);
      setSources((items) =>
        items.map((s) =>
          s.id === source.id
            ? {
                ...s,
                id: result.source_id,
                origin: "indexed",
                status: "indexed",
              }
            : s,
        ),
      );
      setUploadIds((ids) =>
        ids.map((id) => (id === source.id ? result.source_id : id)),
      );
    } catch (error) {
      setSources((items) =>
        items.map((s) => (s.id === source.id ? { ...s, status: "failed" } : s)),
      );
      setUploadError(
        error instanceof Error ? error.message : "Source indexing failed.",
      );
    }
  }
  async function addFiles(files: FileList | null) {
    if (!files?.length || uploading) return;
    setUploadError("");
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        if (file.size > 10 * 1024 * 1024) {
          setUploadError(
            "Files must be 10 MB or smaller. Larger files were skipped.",
          );
          continue;
        }
        const text = ["txt", "md"].includes(fileExtension(file.name))
          ? await file.text()
          : "";
        const source: SourceRecord = {
          id: `local:${crypto.randomUUID()}`,
          title: file.name,
          category: uploadCategory,
          kind: "Documents",
          tone: "muted",
          date: "",
          description: text || "Text extraction is pending.",
          details: { size: file.size },
          content: text,
          origin: "local",
          status: "pending",
        };
        localFiles.current.set(source.id, file);
        setSources((s) => [...s, source]);
        setUploadIds((ids) => [...ids, source.id]);
        if (process.env.NEXT_PUBLIC_SOURCE_UPLOAD_PATH)
          await indexSource(source, file);
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }
  const caseRecord = active?.analysis?.related_past_findings.find(
    (c) => c.finding_id === caseId,
  );
  const modalTitle =
    modal === "settings"
      ? "Settings"
      : modal === "upload"
        ? "Add sources"
        : modal === "context"
          ? "Finding context"
          : modal === "confirm"
            ? "Review finding"
            : modal === "case"
              ? caseId
              : modal === "reference"
                ? reference?.title
                : selected?.title;
  return (
    <>
      <nav className="mobile-nav" aria-label="Workspace panels">
        {["sources", "chat", "references"].map((t) => (
          <button
            key={t}
            className={mobileTab === t ? "active" : ""}
            onClick={() => setMobileTab(t)}
          >
            {t === "chat" ? "Audit Memory" : t}
          </button>
        ))}
      </nav>
      <main className={`workspace show-${mobileTab}`}>
        <SourceDataCorpus
          sources={sources}
          selected={selected?.id || ""}
          onSelect={selectSource}
          onAdd={() => {
            setUploadError("");
            setModal("upload");
          }}
        />
        <section className="chat-panel" aria-label="Audit Memory chat">
          <Header onSettings={() => setModal("settings")} />
          <ChatWindow
            messages={messages}
            loading={loading}
            activeMessage={activeId}
            onSend={beginQuestion}
            onReference={showReference}
            onReview={(m) => {
              setReviewMessage(m);
              setConfirmationError("");
              setModal("confirm");
            }}
            onSelectAnswer={(m) => setActiveId(m.id)}
          />
        </section>
        <MemoryPanel
          references={active?.references || []}
          analysis={active?.analysis}
          memories={active?.memories}
          readiness={readiness}
          allowHistory={memory && !!active?.memoryEnabled}
          onReference={showReference}
          onCase={(id) => {
            setCaseId(id);
            setModal("case");
          }}
        />
      </main>
      <dialog
        ref={dialog}
        className={`app-dialog ${modal === "settings" ? "settings-dialog" : ""}`}
        aria-labelledby="dialog-title"
        onCancel={(e) => {
          if (busy) e.preventDefault();
          else setModal(null);
        }}
        onClick={(e) => {
          if (e.target === e.currentTarget) closeModal();
        }}
      >
        <div className="dialog-inner">
          <header className="dialog-header">
            <h2 id="dialog-title">{modalTitle}</h2>
            <button
              className="icon-button"
              onClick={closeModal}
              aria-label="Close dialog"
              disabled={busy}
            >
              <Icon name="close" size={18} />
            </button>
          </header>
          {modal === "settings" && (
            <div className="settings-content">
              <div className="setting-row">
                <label htmlFor="memory-switch">Agent Memory</label>
                <button
                  id="memory-switch"
                  className={`toggle ${memory ? "on" : ""}`}
                  role="switch"
                  aria-checked={memory}
                  aria-label="Agent Memory"
                  onClick={() => setMemory((v) => !v)}
                  disabled={loading}
                >
                  <span />
                  {memory ? "ON" : "OFF"}
                </button>
              </div>
              <p>
                When enabled, Audit Memory can use all indexed source history
                and previous verified cases when answering.
              </p>
              {loading && (
                <p className="settings-hint">
                  You can change this once the current answer is complete.
                </p>
              )}
            </div>
          )}
          {modal === "source" && selected && (
            <>
              <div className="source-detail-meta">
                <DocumentIcon filename={selected.title} />
                {selected.category}
                <span>·</span>
                {selected.origin === "seed"
                  ? "Seeded record"
                  : selected.status === "indexed"
                    ? "Indexed source"
                    : "Local file · not indexed"}
              </div>
              {selected.origin === "seed" && (
                <p className="source-provenance">
                  Markdown view of {String(selected.details.source_file)} ·{" "}
                  {selected.id}
                </p>
              )}
              <pre className="source-content">
                {selected.content ||
                  "Text extraction is pending. Connect source indexing to read this document."}
              </pre>
            </>
          )}
          {modal === "reference" && reference && (
            <>
              <p className="source-detail-meta">
                {reference.category}
                {reference.location && ` · ${reference.location}`}
              </p>
              <blockquote className="reference-full">
                {reference.snippet}
              </blockquote>
              <p className="source-provenance">
                Source ID: {reference.sourceId}
              </p>
              {sources.some((s) => s.id === reference.sourceId) && (
                <button
                  className="secondary-button"
                  onClick={() =>
                    selectSource(
                      sources.find((s) => s.id === reference.sourceId)!,
                    )
                  }
                >
                  Open source file
                </button>
              )}
            </>
          )}
          {modal === "case" && caseRecord && (
            <>
              <p className="dialog-description">{caseRecord.summary}</p>
              <div className="case-comparison">
                {Object.entries(caseRecord.comparison).map(([key, value]) => (
                  <div key={key}>
                    <strong>{key.replaceAll("_", " ")}</strong>
                    <p>{value.reason}</p>
                  </div>
                ))}
              </div>
              <p className="source-provenance">
                Evidence: {caseRecord.memory_ids.join(", ")}
              </p>
            </>
          )}
          {modal === "context" && (
            <form
              className="dialog-form"
              onSubmit={(e) => {
                e.preventDefault();
                if (control.trim() && department.trim())
                  void analyze(pendingQuestion);
              }}
            >
              <p className="dialog-description">
                Specify the control and department for this finding. These
                provide context for the analysis.
              </p>
              <label>
                Control ID
                <input
                  autoFocus
                  required
                  value={control}
                  onChange={(e) => setControl(e.target.value)}
                  placeholder="e.g. CC6.2"
                />
              </label>
              <label>
                Department
                <input
                  required
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="e.g. Support Engineering"
                />
              </label>
              <label>
                Question
                <textarea
                  required
                  rows={3}
                  value={pendingQuestion}
                  onChange={(e) => setPendingQuestion(e.target.value)}
                />
              </label>
              <button
                className="primary-button"
                disabled={
                  !control.trim() ||
                  !department.trim() ||
                  !pendingQuestion.trim()
                }
              >
                Analyze finding
              </button>
            </form>
          )}
          {modal === "confirm" && reviewMessage && (
            <ConfirmationForm
              key={reviewMessage.id}
              message={reviewMessage}
              onConfirm={(r) => void confirm(r)}
              busy={confirmationBusy}
              error={confirmationError}
            />
          )}
          {modal === "upload" && (
            <div className="dialog-form">
              <p className="dialog-description">
                Add documents to your workspace. Connected source indexing
                extracts text and makes the source available for retrieval.
              </p>

              <button
                className="upload-zone"
                onClick={() => fileInput.current?.click()}
                disabled={uploading}
              >
                <Icon name="plus" size={22} />
                <strong>
                  {uploading ? "Adding sources…" : "Choose source files"}
                </strong>
                <span>Any file type · up to 10 MB</span>
              </button>
              <input
                ref={fileInput}
                type="file"
                hidden
                multiple
                accept="*/*"
                onChange={(e) => void addFiles(e.target.files)}
              />
              {uploading && (
                <div className="upload-progress-bar">
                  <div className="upload-progress-bar-inner"></div>
                </div>
              )}
              {!uploading && !!uploadIds.length && (
                <p
                  className="inline-notice"
                  style={{ color: "#4caf50", fontWeight: "bold" }}
                >
                  {uploadIds.length > 1
                    ? "These files have been uploaded successfully."
                    : "This file has been uploaded successfully."}
                </p>
              )}
              {!!uploadIds.length && (
                <ul className="upload-list">
                  {sources
                    .filter((s) => uploadIds.includes(s.id))
                    .map((s) => (
                      <li key={s.id}>
                        <DocumentIcon filename={s.title} />
                        <span>{s.title}</span>

                        {s.status === "failed" &&
                          localFiles.current.has(s.id) && (
                            <button
                              className="text-button"
                              disabled={uploading}
                              onClick={async () => {
                                setUploading(true);
                                await indexSource(
                                  s,
                                  localFiles.current.get(s.id)!,
                                );
                                setUploading(false);
                              }}
                            >
                              Retry
                            </button>
                          )}
                      </li>
                    ))}
                </ul>
              )}
              {uploadError && (
                <p className="form-error" role="alert">
                  {uploadError}
                </p>
              )}
            </div>
          )}
        </div>
      </dialog>
    </>
  );
}
