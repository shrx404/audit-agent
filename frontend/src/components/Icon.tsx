import type { CSSProperties, ReactNode } from "react";
const paths: Record<string, ReactNode> = {
  settings: <><path d="m9 3-1 3-3 1-2 3 2 2-1 3 2 3 3-1 2 2 3-1 1-3 3-1 2-3-2-2 1-3-2-3-3 1-2-2z"/><circle cx="11.5" cy="11" r="3"/></>,
  'chevron-right': <path d="m9 5 7 7-7 7"/>,
  send: <path d="M12 20V4m-6 6 6-6 6 6"/>,
  database: (
    <>
      <ellipse cx="12" cy="5" rx="7.5" ry="3" />
      <path d="M4.5 5v14c0 4 15 4 15 0V5M4.5 10c0 4 15 4 15 0M4.5 15c0 4 15 4 15 0" />
    </>
  ),
  file: (
    <>
      <path d="M6 3h8l5 5v13H6zM14 3v6h5M9 13h7M9 17h5" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="7" />
      <path d="m16 16 5 5" />
    </>
  ),
  plus: <path d="M12 4v16M4 12h16" />,
  chevron: <path d="m7 10 5 5 5-5" />,
  arrow: <path d="M4 12h16m-7-7 7 7-7 7" />,
  close: <path d="m6 6 12 12M6 18 18 6" />,
  sliders: (
    <>
      <path d="M3 7h5m4 0h9M3 17h11m4 0h3" />
      <circle cx="10" cy="7" r="2" />
      <circle cx="16" cy="17" r="2" />
    </>
  ),
  more: (
    <>
      <circle cx="12" cy="5" r="1" />
      <circle cx="12" cy="12" r="1" />
      <circle cx="12" cy="19" r="1" />
    </>
  ),
  link: (
    <>
      <path
        d="m10 14 4-4M8 16l-1 1a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m0 2 1-1a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0"
        transform="translate(2 0)"
      />
    </>
  ),
  clip: <path d="m9 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l9-9m-5 13 8-8" />,
  check: (
    <>
      <rect x="4" y="3" width="16" height="18" rx="3" />
      <path d="m8 12 3 3 5-6" />
    </>
  ),
  table: (
    <>
      <path d="M6 3h9l4 4v14H6zM6 10h13M6 15h13M11 10v11" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M2 21v-3a7 7 0 0 1 14 0v3zM16 5a3 3 0 0 1 0 6m2 3a5 5 0 0 1 4 5v2" />
    </>
  ),
  folder: <path d="M3 6h7l2 3h9v11H3zM3 6V3h7l2 3h7v3" />,
  history: (
    <>
      <path d="M3 11a9 9 0 1 1 2 7M3 4v7h7M12 7v6l4 2" />
    </>
  ),
  expand: <path d="M9 3H3v6m12-6h6v6M3 15v6h6m12-6v6h-6M8 8h8v8H8z" />,
  warning: (
    <>
      <path
        d="M10 4a2.3 2.3 0 0 1 4 0l8 14a2.3 2.3 0 0 1-2 3H4a2.3 2.3 0 0 1-2-3z"
        fill="currentColor"
        stroke="none"
      />
      <path d="M12 8v5m0 3v.5" stroke="#261220" strokeWidth="2.5" />
    </>
  ),
};
export function Icon({
  name,
  size = 22,
  style,
}: {
  name: string;
  size?: number;
  style?: CSSProperties;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={style}
    >
      {paths[name] || paths.file}
    </svg>
  );
}
export function DocumentIcon({ filename }: { filename: string }) {
  const ext = filename.split('.').pop()?.toLowerCase();
  const label = ext === 'pdf' ? 'PDF' : ext === 'doc' || ext === 'docx' ? 'W' : ext === 'md' ? 'M↓' : 'T';
  return <span className={`document-icon doc-${ext || 'txt'}`} aria-hidden="true"><Icon name="file" size={18}/><span>{label}</span></span>;
}
export function Sparkle({ small = false }: { small?: boolean }) {
  return (
    <span className={`sparkle ${small ? "small" : ""}`} aria-hidden="true">
      <span>✦</span>
      <i>✦</i>
      <b>✦</b>
      <em>✧</em>
    </span>
  );
}
export function FileIcon({
  tone = "blue",
  icon = "file",
}: {
  tone?: string;
  icon?: string;
}) {
  return (
    <span className={`file-icon ${tone}`}>
      <Icon name={icon} size={25} />
    </span>
  );
}
