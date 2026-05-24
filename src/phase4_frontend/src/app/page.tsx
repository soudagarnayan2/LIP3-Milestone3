"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  id: string;
  role: "user" | "bot";
  content: string;
  citation?: string | null;
  timestamp: Date;
  suggestions?: { name: string; type: string; change: string; risk: string }[];
}

const RECENT_FUNDS = [
  { name: "SBI Gold Fund", change: "+1.4%", negative: false, points: "20,40,30,50,45,60" },
  { name: "SBI Contra Fund", change: "+0.8%", negative: false, points: "10,25,20,35,30,40" },
  { name: "Axis Bluechip Fund", change: "-0.2%", negative: true, points: "50,45,55,40,35,30" },
];

function renderContentWithLinks(text: string) {
  if (!text) return null;

  // Split by markdown links [text](url) and raw URLs
  const urlRegex = /(\[[^\]]+\]\(https?:\/\/[^\s)]+\)|https?:\/\/[^\s)]+)/g;
  const parts = text.split(urlRegex);

  return parts.map((part, index) => {
    const markdownMatch = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
    if (markdownMatch) {
      const [_, linkText, url] = markdownMatch;
      return (
        <a
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#00d09c] hover:underline font-medium break-all"
        >
          {linkText}
        </a>
      );
    }

    const rawUrlMatch = part.match(/^(https?:\/\/[^\s)]+)$/);
    if (rawUrlMatch) {
      const url = rawUrlMatch[1];
      return (
        <a
          key={index}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#00d09c] hover:underline font-medium break-all"
        >
          {url}
        </a>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const query = text || input.trim();
    if (!query || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, language: "en" }),
      });

      const data = await res.json();
      
      if (res.status === 400) {
        setMessages((prev) => [...prev, {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: `⚠️ ${data.detail}`,
          timestamp: new Date(),
        }]);
      } else {
        // Mocking suggestions for the design demonstration if they aren't in the API yet
        const suggestions = query.toLowerCase().includes("portfolio") ? [
          { name: "Quantum Growth Fund", type: "Mid-cap", change: "+24.8%", risk: "High Risk" },
          { name: "Eco-Pulse Equity", type: "Sectoral", change: "+18.2%", risk: "ESG" }
        ] : undefined;

        setMessages((prev) => [...prev, {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: data.answer,
          citation: data.citation_url,
          timestamp: new Date(),
          suggestions
        }]);
      }
    } catch {
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "bot",
        content: "I'm having trouble connecting to the server. Please try again later.",
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 border-r border-[#1e1e1e] flex flex-col p-6 gap-8 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 text-[#00d09c]">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M3 17l6-6 4 4 8-8M21 7v6m0-6h-6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 className="text-xl font-bold tracking-tight">Groww Assistant</h1>
        </div>

        <div className="flex flex-col gap-4">
          <h2 className="text-[10px] font-bold text-[#9ba3af] uppercase tracking-widest px-1">Recently Viewed Funds</h2>
          {RECENT_FUNDS.map((fund) => (
            <div key={fund.name} className="sidebar-card group">
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm font-medium">{fund.name}</span>
                <span className={`text-xs font-bold ${fund.negative ? "text-[#ff5252]" : "text-[#00d09c]"}`}>
                  {fund.change}
                </span>
              </div>
              <svg className="w-full h-8" viewBox="0 0 100 40">
                <polyline
                  points={fund.points}
                  className={fund.negative ? "sparkline-negative" : "sparkline"}
                  transform="translate(0, 10)"
                />
              </svg>
            </div>
          ))}
        </div>

        <div className="mt-auto">
          <div className="bg-[#0a211b] border border-[#00d09c]/10 rounded-2xl p-5 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-[#00d09c]">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3zm0 2.18l6 2.25v4.66c0 3.82-2.55 7.39-6 8.39-3.45-1-6-4.57-6-8.39V6.43l6-2.25z"/>
              </svg>
              <span className="text-xs font-bold">Verified Secure</span>
            </div>
            <p className="text-[10px] text-[#9ba3af] leading-relaxed">
              Your investment data is secured with AES-256 encryption.
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-20 border-b border-[#1e1e1e] flex items-center justify-between px-8 bg-[#0a0a0a]/80 backdrop-blur-md z-10">
          <div className="flex items-center gap-6">
            <div className="bg-[#121212] rounded-full px-4 py-2 border border-[#1e1e1e] flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#9ba3af] font-bold">NIFTY 50</span>
                <span className="text-xs font-bold">22,097.45</span>
                <span className="text-[10px] text-[#00d09c] font-bold">+0.45% ▲</span>
              </div>
              <div className="w-[1px] h-3 bg-[#1e1e1e]" />
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#9ba3af] font-bold">SENSEX</span>
                <span className="text-xs font-bold">72,708.16</span>
                <span className="text-[10px] text-[#00d09c] font-bold">+0.38%</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="p-2 text-[#9ba3af] hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
            <div className="w-8 h-8 rounded-full bg-[#1e1e1e] border border-[#2a2a2a] overflow-hidden">
              <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="Profile" />
            </div>
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8 scroll-smooth">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center gap-4 text-center">
              <div className="w-16 h-16 bg-[#00d09c]/10 rounded-3xl flex items-center justify-center text-[#00d09c]">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold mb-2">How can I help you today?</h3>
                <p className="text-sm text-[#9ba3af]">Ask about fund NAVs, risks, or portfolio suggestions.</p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start animate-in"}`}>
              {msg.role === "bot" && (
                <div className="w-8 h-8 rounded-full bg-[#00d09c]/10 border border-[#00d09c]/20 flex items-center justify-center text-[#00d09c] flex-shrink-0">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
              
              <div className={`max-w-[70%] ${msg.role === "user" ? "bg-[#1e1e1e] px-5 py-3 rounded-[20px] rounded-tr-none" : "flex flex-col gap-4"}`}>
                {msg.role === "user" ? (
                  <p className="text-sm leading-relaxed">{renderContentWithLinks(msg.content)}</p>
                ) : (
                  <div className="message-bot-card">
                    <p className="text-sm leading-relaxed mb-6 text-[#e0e0e0]">{renderContentWithLinks(msg.content)}</p>
                    
                    {msg.suggestions && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        {msg.suggestions.map((fund) => (
                          <div key={fund.name} className="fund-product-card flex flex-col gap-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="text-sm font-bold">{fund.name}</h4>
                                <p className="text-[10px] text-[#9ba3af]">{fund.type} &bull; {fund.risk}</p>
                              </div>
                              <span className="text-xs font-bold text-[#00d09c]">{fund.change}</span>
                            </div>
                            <button className={fund.type === "Mid-cap" ? "btn-green-solid text-[11px]" : "btn-outline text-[11px]"}>
                              {fund.type === "Mid-cap" ? "INVEST NOW" : "VIEW DETAILS"}
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="flex flex-wrap gap-2">
                      <a 
                        href="https://www.sbimf.com/en-us/research" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="tag-chip hover:bg-[#00d09c]/10 hover:border-[#00d09c]/30 transition-colors"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                        SBI Mutual Fund Research
                      </a>
                      <a 
                        href="https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY%2050" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="tag-chip hover:bg-[#00d09c]/10 hover:border-[#00d09c]/30 transition-colors"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                        NSE Sectoral Trends
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex gap-4 animate-in">
              <div className="w-8 h-8 rounded-full bg-[#00d09c]/10 border border-[#00d09c]/20 flex items-center justify-center text-[#00d09c] flex-shrink-0">
                <svg className="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div className="message-bot-card py-4 px-6">
                <div className="flex gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00d09c] animate-bounce" style={{ animationDelay: '0s' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00d09c] animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-[#00d09c] animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-8 pt-0">
          <div className="input-field-container">
            <button className="p-2 text-[#9ba3af] hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Type your investment query..."
              className="flex-1 bg-transparent border-none outline-none text-sm py-3 placeholder:text-[#4a4a4a]"
              disabled={isLoading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || !input.trim()}
              className="send-btn-circle disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </div>
          <p className="text-center text-[9px] text-[#4a4a4a] font-bold uppercase tracking-[0.2em] mt-4">
            End-to-end encrypted assistant channel
          </p>
        </div>
      </main>
    </div>
  );
}
