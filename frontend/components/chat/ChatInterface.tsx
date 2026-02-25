"use client";

import { useState, useRef, useEffect } from "react";
import { Translations } from "@/lib/translations";
import { Send, ActivitySquare, Volume2, VolumeX } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

type Message = { role: "assistant" | "user"; text: string };
type Step = "symptoms" | "age" | "duration" | "result";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ChatInterface({ t }: { t: Translations }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [step, setStep] = useState<Step>("symptoms");
    const [collected, setCollected] = useState({ symptoms: "", age: 0, duration: 0 });
    const [isMuted, setIsMuted] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    const speak = (content: string) => {
        if (isMuted || typeof window === "undefined" || !window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(content);

        // Try to match voice lang to selected lang roughly
        if (content.includes("क्या") || content.includes("नमस्ते")) utterance.lang = "hi-IN";
        else if (content.includes("नमस्कार")) utterance.lang = "mr-IN";
        else utterance.lang = "en-US";

        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    };

    useEffect(() => {
        setMessages([{ role: "assistant", text: t.chatGreeting }]);
        setStep("symptoms");
        setCollected({ symptoms: "", age: 0, duration: 0 });
        setInput("");
        // Initially speak the greeting on lang change if not muted
        speak(t.chatGreeting);
    }, [t]);

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

    useEffect(() => {
        // Cleanup speech on unmount
        return () => window.speechSynthesis?.cancel();
    }, []);

    const addMsg = (role: "assistant" | "user", text: string) => {
        setMessages((prev) => [...prev, { role, text }]);
        if (role === "assistant") {
            // Remove common emojis manually to avoid TS 'es6' regex flag errors
            const textToSpeak = text
                .replace(/👋/g, "")
                .replace(/🙏/g, "")
                .replace(/📋/g, "")
                .replace(/🔍/g, "")
                .replace(/😊/g, "")
                .replace(/🤒/g, "")
                .replace(/📊/g, "")
                .replace(/🔴/g, "")
                .replace(/🟡/g, "")
                .replace(/🟢/g, "")
                .replace(/💊/g, "")
                .replace(/⚠️/g, "")
                .replace(/🌿/g, "");
            speak(textToSpeak);
        } else {
            window.speechSynthesis?.cancel();
        }
    };

    const delay = (fn: () => void, ms: number) => setTimeout(fn, ms);

    const handleSend = async () => {
        const text = input.trim();
        if (!text || loading) return;
        setInput("");
        addMsg("user", text);

        if (step === "symptoms") {
            setCollected((c) => ({ ...c, symptoms: text }));
            setStep("age");
            delay(() => addMsg("assistant", t.chatAskAge), 600);

        } else if (step === "age") {
            const age = parseInt(text);
            if (isNaN(age) || age < 1 || age > 120) {
                delay(() => addMsg("assistant", t.chatInvalidAge), 400);
                return;
            }
            setCollected((c) => ({ ...c, age }));
            setStep("duration");
            delay(() => addMsg("assistant", t.chatAskDuration), 600);

        } else if (step === "duration") {
            const duration = parseFloat(text);
            if (isNaN(duration) || duration < 0) {
                delay(() => addMsg("assistant", t.chatInvalidDuration), 400);
                return;
            }
            const finalData = { ...collected, duration };
            setStep("result");
            setLoading(true);
            delay(() => addMsg("assistant", t.chatAnalysing), 500);

            try {
                const severity = duration > 5 ? 3 : duration > 2 ? 2 : 1;
                const res = await fetch(`${API_URL}/predict`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ Age: finalData.age, Gender: 1, Severity: severity, Duration_Min_Days: finalData.duration }),
                });
                if (!res.ok) throw new Error();
                const data = await res.json();
                const msg = t.chatResultLabel(finalData.symptoms, data.disease, data.risk_level, data.triage_guidance, data.risk_level === "High");
                delay(() => addMsg("assistant", msg), 1500);
            } catch {
                delay(() => addMsg("assistant", t.chatError), 1500);
            } finally {
                setLoading(false);
            }

        } else {
            setStep("symptoms");
            setCollected({ symptoms: "", age: 0, duration: 0 });
            delay(() => addMsg("assistant", t.chatRestart), 500);
        }
    };

    const placeholder =
        step === "symptoms" ? t.chatPlaceholderSymptoms
            : step === "age" ? t.chatPlaceholderAge
                : step === "duration" ? t.chatPlaceholderDuration
                    : t.chatPlaceholderRestart;

    return (
        <div className="flex flex-col h-[560px] glass-panel overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -z-10 mix-blend-screen transform translate-x-1/2 -translate-y-1/2" />

            <div className="bg-surfaceHighlight/50 backdrop-blur-md px-6 py-4 border-b border-borderDark flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg border border-primary/20 shadow-neon">
                        <ActivitySquare className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-white font-heading font-medium tracking-wide">{t.chatTitle}</h2>
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
                                {m.text.includes("🔴") || m.text.includes("🟡") || m.text.includes("🟢") ? (
                                    // Style the markdown-ish result specifically
                                    <div className="space-y-3">
                                        {m.text.split('\n\n').map((block, idx) => (
                                            <p key={idx} className={block.includes("⚠️") ? "text-warning font-medium p-3 bg-warning/10 rounded-lg border border-warning/20" : ""}>
                                                {block}
                                            </p>
                                        ))}
                                    </div>
                                ) : (
                                    m.text
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
                        placeholder={placeholder}
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
