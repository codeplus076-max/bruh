"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Translations } from "@/lib/translations";
import { Send, ActivitySquare, Volume2, VolumeX, FileText } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { db } from "@/lib/firebase";
import { collection, addDoc, serverTimestamp } from "firebase/firestore";

import { useLanguage } from "@/context/LanguageContext";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Message = { role: "assistant" | "user"; content: string; diagnosis?: any };

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ChatInterface({ input, setInput }: { input: string, setInput: (v: string) => void }) {
    const { lang, t } = useLanguage();
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    const speak = useCallback((content: string) => {
        if (isMuted || typeof window === "undefined") return;

        // Stop existing speech
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        const oldAudio = document.getElementById("tts-audio") as HTMLAudioElement;
        if (oldAudio) {
            oldAudio.pause();
            oldAudio.remove();
        }

        // Clean text (remove emojis and markdown asterisks)
        const cleanContent = content
            .replace(/[\u2700-\u27BF\uE000-\uF8FF\u2011-\u26FF]/g, '')
            .replace(/[\uD83C-\uDBFF][\uDC00-\uDFFF]/g, '')
            .replace(/[*#_`~]/g, '')
            .trim();
        if (!cleanContent) return;

        // For English, native browser TTS is 100% reliable
        if (lang === "en") {
            const utterance = new SpeechSynthesisUtterance(cleanContent);
            utterance.lang = "en-US";
            utterance.rate = 1.0;
            if (window.speechSynthesis) window.speechSynthesis.speak(utterance);
            return;
        }

        // For Hindi (hi) and Marathi (mr), Windows often lacks native voice packs.
        // We use Google Translate Web TTS via HTML5 Audio to guarantee pronunciation.
        const tl = lang === "mr" ? "mr" : "hi";
        // Substring to 200 chars to respect the free web API limit
        const safeText = encodeURIComponent(cleanContent.substring(0, 200));
        const audioUrl = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${tl}&client=tw-ob&q=${safeText}`;

        const audio = new Audio(audioUrl);
        audio.id = "tts-audio";

        audio.play().catch(err => {
            console.warn("[TTS] Web audio failed (likely autoplay blocked), falling back to native TTS", err);
            if (window.speechSynthesis) {
                const utterance = new SpeechSynthesisUtterance(cleanContent);
                utterance.lang = "hi-IN"; // Force Hindi voice even for Marathi text to read Devanagari
                utterance.rate = 0.9;

                const voices = window.speechSynthesis.getVoices();
                const voice = voices.find(v => v.lang.includes('hi') || v.lang.includes('mr'));
                if (voice) utterance.voice = voice;

                window.speechSynthesis.speak(utterance);
            }
        });
    }, [isMuted, lang]);

    // Initialize chat session on mount
    useEffect(() => {
        setMessages([{ role: "assistant", content: t.chatGreeting }]);
        // Delay initial greeting slightly to avoid instant autoplay block
        setTimeout(() => speak(t.chatGreeting), 300);
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

            // Sync to Firestore if it's a diagnosis message
            if (data.diagnosis) {
                try {
                    const docRef = await addDoc(collection(db, "sessions"), {
                        symptoms: newMessagesContext.filter(m => m.role === "user").map(m => m.content).join(", "),
                        predictions: data.diagnosis,
                        risk_level: data.diagnosis.risk_level || "Unknown",
                        guidance: {
                            first_aid: data.diagnosis.first_aid || [],
                            home_remedies: data.diagnosis.home_remedies || [],
                            routine: data.diagnosis.routine || [],
                            medicines: data.diagnosis.medicines || [],
                            warnings: data.diagnosis.warnings || [],
                        },
                        timestamp: new Date().toISOString(),
                        createdAt: serverTimestamp(),
                        language: lang,
                        userId: "anonymous" // In a full implementation, use auth.currentUser.uid
                    });
                    aiMsg.diagnosis.sessionId = docRef.id;
                } catch (dbErr) {
                    console.error("Firestore sync failed", dbErr);
                }
            }

            setMessages(prev => [...prev, aiMsg]);
            speak(data.content);
        } catch (err) {
            console.error("Chat error:", err);
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
                        <h2 className="text-textMain font-heading font-medium tracking-wide">{t.chatTitle}</h2>
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
                                        <div className="space-y-3">
                                            <div className="flex justify-between items-start gap-2 border-b border-borderDark pb-2">
                                                <div>
                                                    <p className="font-semibold text-textMain text-base">📊 {m.diagnosis.disease}</p>
                                                    <p className="text-xs text-textMuted mt-0.5">Confidence: {m.diagnosis.confidence}</p>
                                                </div>
                                                <span className={`px-2.5 py-1 rounded-md text-xs font-semibold ${m.diagnosis.is_high_risk ? 'bg-danger/20 text-danger border border-danger/30' : 'bg-primary/20 text-primary border border-primary/30'}`}>
                                                    {m.diagnosis.risk_level} Risk
                                                </span>
                                            </div>

                                            <div className="space-y-1">
                                                <p className="text-sm font-medium text-textMain">🏥 Urgency: <span className="text-textMuted font-normal">{m.diagnosis.urgency}</span></p>
                                            </div>

                                            {m.diagnosis.first_aid && m.diagnosis.first_aid.length > 0 && (
                                                <div className="mt-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                                                    <p className="text-sm font-bold text-emerald-400 mb-1.5 flex items-center gap-1.5">🩹 Immediate First Aid</p>
                                                    <ul className="list-disc list-inside text-xs text-textMain/90 space-y-1">
                                                        {m.diagnosis.first_aid.map((item: string, idx: number) => <li key={idx} className="leading-relaxed">{item}</li>)}
                                                    </ul>
                                                </div>
                                            )}

                                            {m.diagnosis.home_remedies && m.diagnosis.home_remedies.length > 0 && (
                                                <div className="mt-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                                                    <p className="text-sm font-bold text-amber-500 mb-1.5 flex items-center gap-1.5">☕ Supportive Home Care</p>
                                                    <ul className="list-disc list-inside text-xs text-textMain/90 space-y-1">
                                                        {m.diagnosis.home_remedies.map((item: string, idx: number) => <li key={idx} className="leading-relaxed">{item}</li>)}
                                                    </ul>
                                                </div>
                                            )}

                                            {m.diagnosis.medicines && m.diagnosis.medicines.length > 0 && (
                                                <div className="mt-2 p-3 bg-teal-500/10 border border-teal-500/20 rounded-xl">
                                                    <p className="text-sm font-bold text-teal-400 mb-2 flex items-center gap-1.5">💊 Safe OTC Medicines</p>
                                                    <div className="space-y-2.5">
                                                        {m.diagnosis.medicines.map((med: any, idx: number) => (
                                                            <div key={idx} className="bg-surface/50 p-2 rounded-lg border border-borderDark text-xs">
                                                                <p className="font-bold text-teal-300">{med.name} <span className="text-textMuted font-normal">— {med.purpose}</span></p>
                                                                <p className="text-textMain/80 mt-1 leading-relaxed">🔹 {med.guidance}</p>
                                                                {med.warning && <p className="text-danger mt-1 italic">⚠️ {med.warning}</p>}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {m.diagnosis.routine && m.diagnosis.routine.length > 0 && (
                                                <div className="mt-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                                                    <p className="text-sm font-bold text-blue-400 mb-1.5 flex items-center gap-1.5">📅 Daily Routine</p>
                                                    <ul className="list-disc list-inside text-xs text-textMain/90 space-y-1">
                                                        {m.diagnosis.routine.map((item: string, idx: number) => <li key={idx} className="leading-relaxed">{item}</li>)}
                                                    </ul>
                                                </div>
                                            )}

                                            {m.diagnosis.when_to_seek_care && m.diagnosis.when_to_seek_care.length > 0 && (
                                                <div className="mt-2 p-3 bg-pink-500/10 border border-pink-500/20 rounded-xl">
                                                    <p className="text-sm font-bold text-pink-400 mb-1.5 flex items-center gap-1.5">🏥 When to Seek Care</p>
                                                    <ul className="list-disc list-inside text-xs text-textMain/90 space-y-1">
                                                        {m.diagnosis.when_to_seek_care.map((item: string, idx: number) => <li key={idx} className="leading-relaxed">{item}</li>)}
                                                    </ul>
                                                </div>
                                            )}

                                            {m.diagnosis.warnings && m.diagnosis.warnings.length > 0 && (
                                                <div className="mt-2 p-3 bg-danger/20 border border-danger/40 rounded-xl">
                                                    <p className="text-sm font-bold text-danger mb-1.5 flex items-center gap-1.5">🚫 Critical Warnings</p>
                                                    <ul className="list-disc list-inside text-xs text-textMain/90 space-y-1">
                                                        {m.diagnosis.warnings.map((item: string, idx: number) => <li key={idx} className="font-semibold leading-relaxed">{item}</li>)}
                                                    </ul>
                                                </div>
                                            )}

                                            {m.diagnosis.explanation && m.diagnosis.explanation.length > 0 && (
                                                <div className="pt-3 border-t border-borderDark mt-3">
                                                    <p className="text-xs font-semibold text-textMain mb-1.5">Medical Reasoning:</p>
                                                    <ul className="list-disc list-inside text-xs text-textMuted space-y-1 bg-surfaceHighlight/30 p-2.5 rounded-md">
                                                        {m.diagnosis.explanation.map((exp: string, idx: number) => (
                                                            <li key={idx} className={exp.includes("EMERGENCY") ? "text-danger font-medium leading-relaxed" : "leading-relaxed"}>
                                                                {exp}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}

                                            {m.diagnosis.sessionId && (
                                                <div className="mt-4 pt-4 border-t border-borderDark flex flex-col gap-3">
                                                    <Link
                                                        href={`/report?id=${m.diagnosis.sessionId}`}
                                                        className="w-full py-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-neon"
                                                    >
                                                        <FileText className="w-4 h-4" /> View Full Medical Report (PDF)
                                                    </Link>

                                                    <p className="text-[10px] text-textMuted text-center italic">
                                                        Securely saved to Upchaar Cloud Diagnostics
                                                    </p>
                                                </div>
                                            )}
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
