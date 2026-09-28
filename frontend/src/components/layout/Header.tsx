import { Icon } from '../Icon';
export function Header({onSettings}:{onSettings:()=>void}) {
  return <header className="chat-header"><div><h1>Audit Memory</h1><p>Your AI agent for compliance, audit, and risk memory</p></div><button className="icon-button" onClick={onSettings} aria-label="Settings" title="Settings"><Icon name="settings" size={19}/></button></header>;
}
