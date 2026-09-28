import { useEffect, useRef, useState } from "react";
import { Icon } from "../Icon";
import { relatedCases, sourcedClaim } from "../../lib/evidence";
import type { Message, Reference } from "../../types/audit";
import React from 'react';

function formatTextWithCitations(text: string, references?: Reference[], onReference?: (r: Reference) => void) {
  if (!text) return text;
  
  // Match [UUID] or just UUID
  const uuidRegex = /\[?([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]?/g;
  const parts = text.split(uuidRegex);
  
  if (parts.length <= 1) return text; // No matches
  
  const result: React.ReactNode[] = [];
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 0) {
      result.push(parts[i]);
    } else {
      const uuid = parts[i];
      const refIndex = references ? references.findIndex(r => r.id === uuid || r.sourceId === uuid) : -1;
      const displayNum = refIndex !== -1 ? refIndex + 1 : '*';
      const refObj = refIndex !== -1 && references ? references[refIndex] : undefined;
      
      result.push(
        <button 
          key={uuid + i}
          onClick={refObj && onReference ? () => onReference(refObj) : undefined}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            color: '#818cf8',
            borderRadius: '12px',
            padding: '0 6px',
            fontSize: '0.7rem',
            margin: '0 3px',
            verticalAlign: 'middle',
            fontWeight: 600,
            cursor: refObj ? 'pointer' : 'default',
            border: 'none',
            outline: 'none',
            lineHeight: '1.2'
          }}
          title={refObj ? refObj.title : `Source ID: ${uuid}`}
        >
          {displayNum}
        </button>
      );
    }
  }
  
  return <>{result}</>;
}

export function ChatWindow({
  messages,
  loading,
  activeMessage,
  onSend,
  onReference,
  onReview,
  onSelectAnswer,
}: {
  messages: Message[];
  loading: boolean;
  activeMessage: string;
  onSend: (q: string) => void;
  onReference: (r: Reference) => void;
  onReview: (m: Message) => void;
  onSelectAnswer: (m: Message) => void;
}) {
  const [input, setInput] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [messages.length, loading]);
  useEffect(() => {
    if (textarea.current) {
      textarea.current.style.height = "auto";
      textarea.current.style.height = `${Math.min(textarea.current.scrollHeight, 160)}px`;
    }
  }, [input]);
  function send() {
    if (input.trim() && !loading) {
      onSend(input.trim());
      setInput("");
    }
  }
  return (
    <>
      <div
        className={`conversation ${!messages.length ? "is-empty" : ""}`}
        aria-label="Conversation"
        aria-live="polite"
      >
        {!messages.length && (
          <div className="chat-welcome">
            <div className="welcome-mark">
              <Icon name="file" size={23} />
            </div>
            <h2>What would you like to review?</h2>
            <p>
              Ask about a finding, review the evidence,
              <br />
              or trace a previous remediation.
            </p>
            <div className="starter-prompts">
              <button
                onClick={() =>
                  setInput("What are the next steps for finding F-2024-03?")
                }
              >
                Review finding F-2024-03
                <Icon name="arrow" size={14} />
              </button>
              <button
                onClick={() =>
                  setInput(
                    "Compare this finding with previous access review issues.",
                  )
                }
              >
                Compare with previous findings
                <Icon name="arrow" size={14} />
              </button>
            </div>
          </div>
        )}
        {messages.map((m) => (
          <article
            key={m.id}
            className={`chat-message ${m.role} ${m.error ? "message-error" : ""}`}
          >
            <div className="message-label">
              {m.role === "user" ? "You" : "Audit Memory"}
            </div>
            <div className="message-content">
              <div className="answer-text">
                {formatTextWithCitations(m.text, m.references, (r) => {
                  onSelectAnswer(m);
                  onReference(r);
                })}
              </div>
              {m.analysis && (
                <>
                  <div className="analysis-details">
                    {m.analysis.previous_root_cause &&
                      sourcedClaim(
                        m.analysis.previous_root_cause.source_mem_ids,
                        m.analysis,
                      ) && (
                        <p>
                          <strong>Previous root cause</strong>
                          {m.analysis.previous_root_cause.text}
                        </p>
                      )}
                    {m.analysis.previous_remediation &&
                      sourcedClaim(
                        m.analysis.previous_remediation.source_mem_ids,
                        m.analysis,
                      ) && (
                        <p>
                          <strong>Previous remediation</strong>
                          {m.analysis.previous_remediation.text}
                        </p>
                      )}
                    {relatedCases(m.analysis)
                      .filter((c) => c.is_recurrence_candidate)
                      .slice(0, 1)
                      .map((c) => (
                        <div key={c.finding_id} className="recurrence-note">
                          <strong>Possible recurrence · {c.finding_id}</strong>
                          <ul>
                            {Object.entries(c.comparison)
                              .filter(
                                ([, d]) =>
                                  d.rating === "match" ||
                                  d.rating === "partial",
                              )
                              .map(([key, d]) => (
                                <li key={key}>{d.reason}</li>
                              ))}
                          </ul>
                        </div>
                      ))}
                    {m.analysis.deterministic_checks &&
                      m.analysis.deterministic_checks.length > 0 && (
                        <div className="deterministic-checks">
                          <strong>Automated Checks</strong>
                          <ul>
                            {m.analysis.deterministic_checks.map((check, i) => (
                              <li key={i}>
                                <strong>{check.kind}</strong> ({check.severity}
                                ): {check.explanation}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                  </div>
                  {!!m.references?.length && (
                    <div className="answer-sources">
                      <span>Sources used</span>
                      {m.references.map((r, i) => (
                        <button
                          key={r.id}
                          onClick={() => {
                            onSelectAnswer(m);
                            onReference(r);
                          }}
                          title={r.title}
                        >
                          {i + 1}
                          <span>{r.title}</span>
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="answer-actions">
                    <button
                      className={activeMessage === m.id ? "answer-active" : ""}
                      onClick={() => onSelectAnswer(m)}
                    >
                      <Icon name="file" size={13} />
                      References
                    </button>
                    {!m.confirmation ? (
                      <button onClick={() => onReview(m)}>
                        <Icon name="check" size={13} />
                        Review &amp; confirm
                      </button>
                    ) : (
                      <span className="confirmation-status">
                        <Icon name="check" size={13} />
                        {m.confirmation.retrievable
                          ? "Confirmed and available for recall"
                          : "Confirmed · indexing in progress"}
                      </span>
                    )}
                  </div>
                  {m.confirmation && (
                    <p className="confirmation-note">
                      {m.confirmation.message}
                    </p>
                  )}
                  {m.analysis.warnings.includes("hindsight_degraded") && (
                    <p className="inline-notice">
                      Historical retrieval was unavailable for this answer.
                    </p>
                  )}
                </>
              )}
              {/* Handle new /api/ask response format */}
              {m.sources && m.sources.length > 0 ? (
                <div className="analysis-details" style={{ marginTop: '1rem' }}>
                  {m.sources && m.sources.length > 0 && (
                    <div>
                      <strong>Sources Cited</strong>
                      <ul style={{ listStyleType: 'disc', paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
                        {m.sources.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
          </article>
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div className="message-label">Audit Memory</div>
            <p className="loading-message" role="status">
              <span />
              Reviewing the finding and its evidence…
            </p>
          </div>
        )}
        <div ref={bottom} />
      </div>
      <div className="composer-area">
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <textarea
            ref={textarea}
            rows={1}
            aria-label="Ask Audit Memory"
            placeholder="Ask about your compliance data, past findings, or policies..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                !e.shiftKey &&
                !e.nativeEvent.isComposing
              ) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button
            className="send-button"
            aria-label="Send message"
            disabled={!input.trim() || loading}
          >
            <Icon name="send" size={19} />
          </button>
        </form>
        <p className="composer-note">
          Review source evidence before confirming a finding.
        </p>
      </div>
    </>
  );
}
