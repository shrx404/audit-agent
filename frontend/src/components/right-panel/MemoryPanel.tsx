import { DocumentIcon, Icon } from "../Icon";
import type { Analysis, Reference, MemoryHit } from "../../types/audit";
import { relatedCases } from "../../lib/evidence";
import { useState } from "react";

function MemoryCard({ m }: { m: MemoryHit }) {
  const [expanded, setExpanded] = useState(false);
  const parts = m.text.split(" | ");
  const mainText = parts[0];
  let when = m.date;
  let involving = "";

  for (const p of parts.slice(1)) {
    if (p.startsWith("When: ")) when = p.substring(6);
    else if (p.startsWith("Involving: ")) involving = p.substring(11);
  }

  return (
    <button
      onClick={() => setExpanded(!expanded)}
      style={{
        display: "block",
        width: "100%",
        textAlign: "left",
        padding: "0.85rem",
        backgroundColor: "rgba(255,255,255,0.04)",
        borderRadius: "8px",
        border: "1px solid rgba(255,255,255,0.08)",
        cursor: "pointer",
        transition: "all 0.2s",
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.08)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.04)")
      }
    >
      {involving && (
        <div
          style={{
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "#e2e8f0",
            marginBottom: "0.35rem",
          }}
        >
          {involving}
        </div>
      )}

      <div
        style={{
          fontSize: "0.75rem",
          lineHeight: "1.5",
          color: "#94a3b8",
          display: "-webkit-box",
          WebkitLineClamp: expanded ? "unset" : 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          whiteSpace: "pre-wrap",
        }}
      >
        {mainText}
      </div>

      {when && (
        <div
          style={{
            marginTop: "0.5rem",
            display: "inline-block",
            padding: "0.15rem 0.4rem",
            backgroundColor: "rgba(99, 102, 241, 0.1)",
            color: "#818cf8",
            borderRadius: "4px",
            fontSize: "0.65rem",
            fontWeight: 500,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          {when}
        </div>
      )}
    </button>
  );
}

export function MemoryPanel({
  references,
  analysis,
  memories,
  allowHistory,
  onReference,
  onCase,
}: {
  references: Reference[];
  analysis?: Analysis;
  memories?: MemoryHit[];
  allowHistory: boolean;
  onReference: (r: Reference) => void;
  onCase: (id: string) => void;
}) {
  const [showContext, setShowContext] = useState(false);
  const [showSources, setShowSources] = useState(true);
  const [showCases, setShowCases] = useState(true);
  const visible = references.filter((r) => allowHistory || !r.historical);
  const cases = analysis && allowHistory ? relatedCases(analysis) : [];
  const uniqueMemories: MemoryHit[] = [];
  const sortedMem = (memories || [])
    .slice()
    .sort((a, b) => b.text.length - a.text.length);
  for (const m of sortedMem) {
    if (
      !uniqueMemories.some((u) => {
        const minLen = Math.min(u.text.length, m.text.length, 30);
        return u.text.substring(0, minLen) === m.text.substring(0, minLen);
      })
    ) {
      uniqueMemories.push(m);
    }
  }
  return (
    <aside className="references-panel" aria-label="Sources cited">
      <div className="references-scroll">
        <section
          className="past-cases"
          style={{ borderTop: "none", marginTop: "33px", paddingTop: "0" }}
        >
          <h3
            onClick={() => setShowSources(!showSources)}
            style={{
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            Sources cited
            {!!visible.length && (
              <span style={{ fontSize: "10px", color: "#696969" }}>
                {visible.length}
              </span>
            )}
            <div
              style={{
                transform: showSources ? "rotate(90deg)" : "rotate(0deg)",
                transition: "transform 0.2s",
                display: "flex",
              }}
            >
              <Icon name="chevron-right" size={12} />
            </div>
          </h3>

          {showSources &&
            (visible.length ? (
              <div className="reference-list">
                {visible.map((r, i) => (
                  <button
                    className="reference-item"
                    key={r.id}
                    onClick={() => onReference(r)}
                  >
                    <span className="reference-heading">
                      <DocumentIcon filename={r.title} />
                      <strong>{r.title}</strong>
                      <span className="reference-number">{i + 1}</span>
                    </span>
                    <span className="reference-meta">
                      {r.category}
                      {r.location && ` · ${r.location}`}
                    </span>
                    <span className="reference-snippet">
                      {r.snippet.length > 185
                        ? `${r.snippet.slice(0, 182)}…`
                        : r.snippet}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="references-empty">
                <Icon name="file" size={21} />
                <p>
                  Sources cited in your answer
                  <br />
                  will appear here.
                </p>
              </div>
            ))}
        </section>

        <section className="past-cases">
          <h3
            onClick={() => setShowCases(!showCases)}
            style={{
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            Past similar cases
            {!!cases.length && (
              <span style={{ fontSize: "10px", color: "#696969" }}>
                {cases.length}
              </span>
            )}
            <div
              style={{
                transform: showCases ? "rotate(90deg)" : "rotate(0deg)",
                transition: "transform 0.2s",
                display: "flex",
              }}
            >
              <Icon name="chevron-right" size={12} />
            </div>
          </h3>
          {showCases &&
            (cases.length ? (
              cases.map((c) => (
                <button
                  key={c.finding_id}
                  className="past-case"
                  onClick={() => onCase(c.finding_id)}
                >
                  <Icon name="history" size={14} />
                  <span>
                    <strong>{c.finding_id}</strong>
                    <span>{c.summary}</span>
                  </span>
                  <Icon name="chevron-right" size={12} />
                </button>
              ))
            ) : (
              <p className="cases-empty">No related cases to show.</p>
            ))}
        </section>

        <section className="past-cases">
          <h3
            onClick={() => setShowContext(!showContext)}
            style={{
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            Recalled Context
            <div
              style={{
                transform: showContext ? "rotate(90deg)" : "rotate(0deg)",
                transition: "transform 0.2s",
                display: "flex",
              }}
            >
              <Icon name="chevron-right" size={12} />
            </div>
          </h3>
          {showContext &&
            (uniqueMemories.length ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.75rem",
                  marginTop: "0.5rem",
                }}
              >
                {uniqueMemories.map((m, i) => (
                  <MemoryCard key={i} m={m} />
                ))}
              </div>
            ) : (
              <p className="cases-empty">No recalled context.</p>
            ))}
        </section>
      </div>
    </aside>
  );
}
