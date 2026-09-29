import { useState } from "react";
import { DocumentIcon, Icon } from "../Icon";
import type { SourceCategory, SourceRecord } from "../../types/audit";
const defaultFolders: SourceCategory[] = [
  "Policies",
  "Findings",
  "Remediations",
  "Access Reviews",
  "Past Cases",
];
export function SourceDataCorpus({
  sources,
  selected,
  onSelect,
  onAdd,
  onDropFiles,
}: {
  sources: SourceRecord[];
  selected: string;
  onSelect: (s: SourceRecord) => void;
  onAdd: () => void;
  onDropFiles?: (files: FileList | File[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All");
  const [closed, setClosed] = useState<string[]>([]);
  const matches = sources.filter(
    (s) =>
      (filter === "All" || s.category === filter) &&
      `${s.title} ${s.content} ${s.description}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const activeFolders = Array.from(
    new Set([...defaultFolders, ...sources.map((s) => s.category)]),
  );

  return (
    <aside
      className="sources-panel"
      aria-label="Source explorer"
      onDragOver={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onDrop={(e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const items = e.dataTransfer.items;
        if (items) {
          const files: File[] = [];
          for (let i = 0; i < items.length; i++) {
            if (items[i].kind === 'file') {
              const file = items[i].getAsFile();
              if (file) files.push(file);
            }
          }
          if (files.length > 0) {
            onDropFiles?.(files);
          }
        } else if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          onDropFiles?.(e.dataTransfer.files);
        }
      }}
    >
      <div className="explorer-controls">
        <button className="add-sources" onClick={onAdd}>
          <Icon name="plus" size={17} />
          Add sources
        </button>
        <label className="source-search">
          <Icon name="search" size={15} />
          <input
            aria-label="Search files, folders, or content"
            placeholder="Search files, folders, or content..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button onClick={() => setQuery("")} aria-label="Clear search">
              <Icon name="close" size={13} />
            </button>
          )}
        </label>
        <div className="source-filters" aria-label="Filter sources">
          {["All", "Policies", "Findings", "Remediations"].map((f) => (
            <button
              key={f}
              className={filter === f ? "active" : ""}
              aria-pressed={filter === f}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>
      <div className="file-tree">
        {activeFolders
          .filter((f) => filter === "All" || filter === f)
          .map((folder) => {
            const files = matches.filter((s) => s.category === folder);
            if (files.length === 0) return null;
            const expanded = !!query || !closed.includes(folder);
            return (
              <div className="tree-folder" key={folder}>
                <button
                  className="folder-row"
                  aria-expanded={expanded}
                  onClick={() =>
                    setClosed((c) =>
                      c.includes(folder)
                        ? c.filter((f) => f !== folder)
                        : [...c, folder],
                    )
                  }
                >
                  <Icon
                    name={expanded ? "chevron" : "chevron-right"}
                    size={13}
                  />
                  <Icon name="folder" size={16} />
                  <span>{folder}</span>
                  <span className="folder-count">{files.length}</span>
                </button>
                {expanded && (
                  <div className="folder-files">
                    {files.map((s) => (
                      <button
                        className={`file-row ${selected === s.id ? "selected" : ""}`}
                        key={s.id}
                        onClick={() => onSelect(s)}
                        title={s.title}
                        aria-current={selected === s.id ? "true" : undefined}
                      >
                        <DocumentIcon filename={s.title} />
                        <span>{s.title}</span>
                        {s.status && s.status !== "indexed" && (
                          <span
                            className="file-pending"
                            aria-label={s.status}
                            title={
                              s.status === "failed" ? "Not indexed" : s.status
                            }
                          />
                        )}
                      </button>
                    ))}
                    {!files.length && (
                      <p className="folder-empty">
                        {query ? "No matching files" : "No files"}
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
      </div>
      <div className="explorer-footer">
        <span>{sources.length} files</span>
      </div>
    </aside>
  );
}
export function formatDate(date: string) {
  return date
    ? new Date(`${date}T00:00:00`).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "Date not recorded";
}
