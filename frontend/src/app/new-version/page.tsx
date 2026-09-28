"use client";

import React, { useState, useEffect, useRef } from "react";

// Types matching the backend
type Flag = {
  id: string;
  control_id: string;
  kind: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  state: "open" | "resolved" | "false_alarm";
  explanation: string;
  sources: string[];
};

type ReadinessReport = {
  score: number;
  total_controls: number;
  flags: Flag[];
};

type MemoryHit = {
  id: string;
  text: string;
  type: string;
  date: string | null;
  relevance: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "error";
  text: string;
  sources?: string[];
  memories?: MemoryHit[];
};

export default function NewVersionPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [useMemory, setUseMemory] = useState(true);
  const [loading, setLoading] = useState(false);
  const [readiness, setReadiness] = useState<ReadinessReport | null>(null);
  const [health, setHealth] = useState<{ ok: boolean; hindsight: boolean; llm: boolean } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchHealth = async () => {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        setHealth(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

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

  useEffect(() => {
    const init = async () => {
      await fetchHealth();
      await fetchReadiness();
    };
    init();
  }, []);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg.text, use_memory: useMemory }),
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.error || "An error occurred");
      }
      
      const astMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: data.answer,
        sources: data.sources,
        memories: data.memories,
      };
      setMessages((prev) => [...prev, astMsg]);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch response.";
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "error", text: errorMessage },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoReset = async () => {
    if (!confirm("Are you sure you want to reset the demo feedback?")) return;
    try {
      await fetch("/api/demo/reset", { method: "POST" });
      fetchReadiness();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-indigo-500/30">
      {/* Top Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between px-8 py-4 bg-slate-900/80 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-4">
          <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
            AuditAgent v2
          </h1>
        </div>
        
        <div className="flex items-center gap-6">
          {health && (
            <div className="flex gap-3 text-xs font-medium">
              <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${health.hindsight ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${health.hindsight ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]' : 'bg-rose-400'}`}></div>
                Hindsight
              </span>
              <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full ${health.llm ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${health.llm ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]' : 'bg-rose-400'}`}></div>
                LLM
              </span>
            </div>
          )}
          <button 
            onClick={handleDemoReset}
            className="text-xs font-semibold px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors border border-white/5"
          >
            Reset Demo
          </button>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8 h-[calc(100vh-73px)]">
        
        {/* Left Panel: Chat Interface */}
        <section className="lg:col-span-8 flex flex-col bg-slate-900/40 border border-white/5 rounded-3xl overflow-hidden shadow-2xl relative">
          
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-4">
                <div className="w-20 h-20 mb-6 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center border border-indigo-500/30">
                   <svg className="w-10 h-10 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold mb-2">How can I help with the audit?</h2>
                <p className="text-slate-400 max-w-md">Ask questions about your controls, findings, or review past memories to ensure compliance.</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-2xl p-5 ${
                    msg.role === "user" 
                      ? "bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-lg shadow-indigo-900/20 rounded-tr-sm" 
                      : msg.role === "error"
                      ? "bg-rose-950/50 border border-rose-900/50 text-rose-200 rounded-tl-sm"
                      : "bg-slate-800/80 border border-white/5 text-slate-200 rounded-tl-sm shadow-xl"
                  }`}>
                    {msg.role === "assistant" && (
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center">
                          <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </div>
                        <span className="text-xs font-semibold text-indigo-300 tracking-wider uppercase">AuditAgent</span>
                      </div>
                    )}
                    
                    <div className="whitespace-pre-wrap leading-relaxed text-sm">{msg.text}</div>
                    
                    {/* Sources & Memories Display */}
                    {(msg.sources?.length || msg.memories?.length) ? (
                      <div className="mt-5 pt-4 border-t border-white/10 space-y-4">
                        {msg.sources && msg.sources.length > 0 && (
                          <div>
                            <h4 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Sources Cited</h4>
                            <div className="flex flex-wrap gap-2">
                              {msg.sources.map((s, i) => (
                                <span key={i} className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-xs font-medium text-slate-300 flex items-center gap-1.5">
                                  <svg className="w-3 h-3 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                  </svg>
                                  {s}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {msg.memories && msg.memories.length > 0 && (
                          <div>
                            <h4 className="text-xs font-semibold text-indigo-400/80 mb-2 uppercase tracking-wider">Recalled Context</h4>
                            <div className="space-y-2">
                              {msg.memories.map((m, i) => (
                                <div key={i} className="p-3 rounded-lg bg-indigo-500/5 border border-indigo-500/10 text-xs text-slate-300">
                                  <div className="flex items-center justify-between mb-1.5">
                                    <span className="font-semibold text-indigo-300">{m.type}</span>
                                    {m.date && <span className="text-slate-500 text-[10px]">{m.date}</span>}
                                  </div>
                                  <p className="line-clamp-2 text-slate-400">{m.text}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-800/80 border border-white/5 rounded-2xl rounded-tl-sm p-5 shadow-xl flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                  </div>
                  <span className="text-sm font-medium text-slate-400">Analyzing...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-slate-900/80 border-t border-white/5 backdrop-blur-lg">
            <form onSubmit={handleAsk} className="relative flex items-center">
              <button 
                type="button"
                onClick={() => setUseMemory(!useMemory)}
                className={`absolute left-3 p-2 rounded-xl transition-all ${
                  useMemory 
                    ? 'bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30' 
                    : 'bg-slate-800 text-slate-500 hover:bg-slate-700 hover:text-slate-400'
                }`}
                title={useMemory ? "Memory Enabled" : "Memory Disabled"}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </button>
              
              <input 
                type="text" 
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about compliance, controls, or past audits..."
                className="w-full bg-slate-950/50 border border-white/10 rounded-2xl py-4 pl-14 pr-16 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all shadow-inner"
                disabled={loading}
              />
              
              <button 
                type="submit" 
                disabled={loading || !question.trim()}
                className="absolute right-3 p-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-900/50"
              >
                <svg className="w-4 h-4 translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </form>
            <div className="mt-3 flex justify-center">
              <span className="text-[10px] text-slate-500 font-medium tracking-wide uppercase">AI can make mistakes. Verify critical findings.</span>
            </div>
          </div>
        </section>

        {/* Right Panel: Readiness Report */}
        <section className="lg:col-span-4 flex flex-col gap-6">
          {/* Score Card */}
          <div className="bg-slate-900/40 border border-white/5 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg className="w-32 h-32 text-indigo-500 rotate-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            
            <h3 className="text-sm font-semibold text-slate-400 mb-6 flex items-center gap-2">
              <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
              READINESS SCORE
            </h3>
            
            <div className="flex items-end gap-3 mb-2">
              <span className="text-6xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white to-slate-400">
                {readiness ? readiness.score : "--"}
              </span>
              <span className="text-xl font-bold text-slate-500 mb-1.5">/ 100</span>
            </div>
            
            {readiness && (
              <div className="w-full bg-slate-800 rounded-full h-2 mt-6 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${readiness.score}%` }}
                ></div>
              </div>
            )}
            
            <div className="mt-4 text-xs font-medium text-slate-500">
              {readiness ? `${readiness.total_controls} Total Controls Validated` : "Loading report..."}
            </div>
          </div>

          {/* Flags List */}
          <div className="flex-1 bg-slate-900/40 border border-white/5 rounded-3xl shadow-2xl overflow-hidden flex flex-col">
            <div className="p-5 border-b border-white/5 flex justify-between items-center bg-slate-900/80">
              <h3 className="text-sm font-semibold text-slate-200">Open Findings</h3>
              {readiness && (
                <span className="bg-rose-500/10 text-rose-400 text-xs font-bold px-2.5 py-1 rounded-full border border-rose-500/20">
                  {readiness.flags.filter(f => f.state === 'open').length}
                </span>
              )}
            </div>
            
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {!readiness ? (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                  Loading findings...
                </div>
              ) : readiness.flags.filter(f => f.state === 'open').length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 p-6 text-center">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center mb-3">
                    <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-sm font-medium text-emerald-400/80">All clear!</p>
                  <p className="text-xs mt-1">No open findings detected.</p>
                </div>
              ) : (
                readiness.flags.filter(f => f.state === 'open').map(flag => (
                  <div key={flag.id} className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-pointer group">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <span className="text-xs font-bold text-indigo-400 font-mono bg-indigo-500/10 px-2 py-0.5 rounded">{flag.control_id}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider
                        ${flag.severity === 'critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 
                          flag.severity === 'high' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' : 
                          'bg-amber-500/20 text-amber-400 border border-amber-500/30'}`}>
                        {flag.severity}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-slate-200 mb-2 leading-snug">{flag.description}</p>
                    <p className="text-xs text-slate-400 line-clamp-2">{flag.explanation}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
