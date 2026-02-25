"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Translations } from "@/lib/translations";
import { Send, ActivitySquare, Volume2, VolumeX } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Message = { role: "assistant" | "user"; content: string; diagnosis?: any };

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ChatInterface({ t, lang, input, setInput }: { t: Translations, lang: string, input: string, setInput: (v: string) => void }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (typeof window !== "undefined" && window.speechSynthesis) {
            const loadVoices = () => setVoices(window.speechSynthesis.getVoices());
            loadVoices();
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }
    }, []);

    const speak = useCallback((content: string) => {
        if (isMuted || typeof window === "undefined" || !window.speechSynthesis) return;
        window.speechSynthesis.cancel();

        // Strip emojis to prevent reading them aloud
        const cleanContent = content.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, '');

        const utterance = new SpeechSynthesisUtterance(cleanContent);

        // Explicitly set language based on frontend state
        const preferredLang = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-US";
        utterance.lang = preferredLang;

        // Find and bind real voice payload
        if (voices.length > 0) {
            const targetLangCode = lang === "hi" ? "hi" : lang === "mr" ? "mr" : "en";
            const matchedVoice = voices.find(v => v.lang.toLowerCase().includes(targetLangCode));
            if (matchedVoice) {
                utterance.voice = matchedVoice;
            }
        }

        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }, [isMuted, lang, voices]);

    // Initialize chat session on mount
    useEffect(() => {
        setMessages([{ role: "assistant", content: t.chatGreeting }]);
        speak(t.chatGreeting);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Only run once on mount

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

    useEffect(() => {
        // Cleanup speech on unmount
        return () => window.speechSynthesis?.cancel();
    }, []);

    const handleSend = async () => {
        const text = input.trim();
        if (!text || loading) return;

        setInput("");
        window.speechSynthesis?.cancel();

        // Add user message to UI immediately
        const userMsg: Message = { role: "user", content: text };
        const newMessagesContext = [...messages, userMsg];
        setMessages(newMessagesContext);
        setLoading(true);

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    // Cleanse diagnosis obj from payload sent to backend to match strict pydantic type
                    messages: newMessagesContext.map(m => ({ role: m.role, content: m.content })),
                    language: lang
                }),
            });

            if (!res.ok) throw new Error("API Error");

            const data = await res.json();

            const aiMsg: Message = { role: "assistant", content: data.content, diagnosis: data.diagnosis };
            setMessages(prev => [...prev, aiMsg]);

            speak(data.content);
        } catch {
            const errorMsg: Message = { role: "assistant", content: t.chatError };
            setMessages(prev => [...prev, errorMsg]);
            speak(t.chatError);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[560px] glass-panel overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -z-10 mix-blend-screen transform translate-x-1/2 -translate-y-1/2" />

            <div className="bg-surfaceHighlight/50 backdrop-blur-md px-6 py-4 border-b border-borderDark flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg border border-primary/20 shadow-neon">
                        <ActivitySquare className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-slate-800 font-heading font-medium tracking-wide">{t.chatTitle}</h2>
                        <p className="text-primaryVibrant/70 text-xs tracking-wider uppercase mt-0.5">{t.chatSubtitle}</p>
                    </div>
                </div>
                <button
                    onClick={() => setIsMuted(!isMuted)}
                    className={`p-2 rounded-full border transition-colors ${isMuted ? 'bg-surface border-borderDark text-textMuted' : 'bg-primary/10 border-primary/30 text-primary shadow-neon'}`}
                    title={isMuted ? "Unmute AI Voice" : "Mute AI Voice"}
                >
                    {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar z-10">
                <AnimatePresence initial={false}>
                    {messages.map((m, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            transition={{ type: "spring", stiffness: 200, damping: 20 }}
                            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div className={`max-w-[85%] px-5 py-3.5 text-sm whitespace-pre-wrap leading-relaxed shadow-lg ${m.role === "user"
                                ? "bg-primary/10 text-primary border border-primary/30 rounded-2xl rounded-tr-sm"
                                : "bg-surface text-textMain border border-borderDark rounded-2xl rounded-tl-sm ring-1 ring-white/5"
                                }`}>
                                {m.content}

                                {m.diagnosis && (
                                    <div className={`mt-3 p-4 rounded-xl border ${m.diagnosis.is_high_risk ? 'bg-warning/10 border-warning/30' : 'bg-primary/5 border-primary/20'}`}>
                                        <div className="space-y-2">
                                            <p><span className="font-semibold text-slate-800">📊 Condition:</span> {m.diagnosis.disease}</p>
                                            <p><span className="font-semibold text-slate-800">⚠️ Risk Level:</span> <span className={m.diagnosis.is_high_risk ? 'text-danger font-bold' : 'text-primary'}>{m.diagnosis.risk_level}</span></p>
                                            <p className="pt-2 border-t border-borderDark text-textMuted"><span className="text-slate-800">💊 Advice:</span> {m.diagnosis.triage_guidance}</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}
                    {loading && (
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                            className="flex justify-start"
                        >
                            <div className="bg-surface border border-borderDark rounded-2xl rounded-tl-sm px-5 py-4 shadow-glass">
                                <span className="flex gap-1.5 items-center">
                                    {[0, 150, 300].map((d) => (
                                        <span key={d} className="w-2 h-2 bg-primary/60 rounded-full animate-pulse" style={{ animationDelay: `${d}ms` }} />
                                    ))}
                                </span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <div ref={bottomRef} className="h-1" />
            </div>

            <div className="p-4 bg-surfaceHighlight/40 backdrop-blur-lg border-t border-borderDark z-10">
                <div className="flex items-center gap-3 relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type to chat..."
                        className="flex-1 bg-surface border border-borderDark rounded-full px-5 py-3.5 text-sm text-textMain outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-textMuted/60"
                        onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        disabled={loading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className="p-3.5 bg-primary/10 text-primary hover:bg-primary/20 hover:text-primaryVibrant disabled:opacity-50 disabled:hover:bg-primary/10 border border-primary/20 rounded-full transition-colors flex items-center justify-center shadow-neon"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
