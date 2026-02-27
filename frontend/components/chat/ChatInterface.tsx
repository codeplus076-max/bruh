"use client";

declare global {
    interface Window {
        SpeechRecognition: any; // We'll use more specific casts where used if needed, but defining the class type is better
        webkitSpeechRecognition: any;
    }

    // Define minimum needed for SpeechRecognition
    interface SpeechRecognition extends EventTarget {
        continuous: boolean;
        interimResults: boolean;
        lang: string;
        onresult: (event: SpeechRecognitionEvent) => void;
        onerror: (event: SpeechRecognitionErrorEvent) => void;
        onend: () => void;
        start(): void;
        stop(): void;
        abort(): void;
    }

    interface SpeechRecognitionEvent extends Event {
        results: SpeechRecognitionResultList;
        resultIndex: number;
    }

    interface SpeechRecognitionErrorEvent extends Event {
        error: string;
        message: string;
    }
}

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, ActivitySquare, Volume2, VolumeX, FileText, Mic, MicOff, Phone, Play, Pause, Plus } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";


import { useLanguage } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";
import { useChat } from "@/context/ChatStateContext";
import { LiveCallOverlay } from "./LiveCallOverlay";

interface Diagnosis {
    disease?: string;
    confidence?: string;
    risk_level?: string;
    is_high_risk?: boolean;
    urgency?: string;
    first_aid?: string[];
    home_remedies?: string[];
    medicines?: Array<{ name: string; purpose: string; guidance: string; warning?: string }>;
    routine?: string[];
    when_to_seek_care?: string[];
    warnings?: string[];
    explanation?: string[];
    sessionId?: string;
}

type Message = { role: "assistant" | "user"; content: string; diagnosis?: Diagnosis };

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ChatInterface({ input, setInput }: { input: string, setInput: (v: string) => void }) {
    const { lang, t } = useLanguage();
    const { user, userProfile } = useAuth();
    const { messages, sessionId, setMessages, resetChat, loadSession } = useChat();
    const [loading, setLoading] = useState(false);
    const [autoSpeak, setAutoSpeak] = useState(false);
    const [showCall, setShowCall] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [playingMessageId, setPlayingMessageId] = useState<number | null>(null);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const recognitionRef = useRef<SpeechRecognition | null>(null);

    const playAudio = useCallback(async (text: string, index: number) => {
        if (playingMessageId === index) {
            audioRef.current?.pause();
            setPlayingMessageId(null);
            return;
        }

        setVoiceError(null);
        console.log(`[Voice] Starting playback for message ${index}. Text length: ${text.length}`);
        setPlayingMessageId(index);

        // Native Browser Fallback Function
        const fallbackToSpeechSynthesis = () => {
            console.warn("[Voice] Falling back to Browser Speech Synthesis.");
            if (!("speechSynthesis" in window)) {
                console.error("[Voice] Browser Speech Synthesis not supported.");
                setPlayingMessageId(null);
                return;
            }
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-US";
            utterance.onend = () => setPlayingMessageId(null);
            utterance.onerror = (e) => {
                console.error("[Voice] Browser Synthesis Error:", e);
                finalFallback();
            };
            window.speechSynthesis.speak(utterance);
        };

        const finalFallback = () => {
            console.error("[Voice] All voice methods failed.");
            setVoiceError("Voice unavailable. Showing text guidance.");
            setPlayingMessageId(null);
            // Auto-clear error after 5s
            setTimeout(() => setVoiceError(null), 5000);
        };

        try {
            const response = await fetch(`${API_URL}/voice/tts`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, language: lang })
            });

            console.log(`[Voice] API Status: ${response.status} | Content-Type: ${response.headers.get("Content-Type")}`);
            if (response.ok) {
                const blob = await response.blob();
                console.log(`[Voice] Blob Size: ${(blob.size / 1024).toFixed(2)} KB | Type: ${blob.type}`);
                if (blob.size < 100) {
                    const errorText = await blob.text();
                    console.error("[Voice] Small blob text content:", errorText.substring(0, 100));
                    throw new Error("Audio blob too small/invalid");
                }

                const url = URL.createObjectURL(blob);
                if (audioRef.current) {
                    audioRef.current.src = url;

                    // Resume audio context if needed (browser restriction)
                    const playPromise = audioRef.current.play();

                    if (playPromise !== undefined) {
                        playPromise.catch(error => {
                            console.error("[Voice] Playback blocked by browser:", error);
                            // If blocked, fallback to speech synth which behaves differently with gestures
                            fallbackToSpeechSynthesis();
                        });
                    }

                    audioRef.current.onended = () => {
                        setPlayingMessageId(null);
                        URL.revokeObjectURL(url);
                    };
                }
            } else {
                throw new Error(`TTS API failed with status ${response.status}`);
            }
        } catch (error) {
            console.error("[Voice] Inworld TTS Failed:", error);
            fallbackToSpeechSynthesis();
        }
    }, [lang, playingMessageId]);

    const handleSend = useCallback(async (transcript?: string) => {
        const text = typeof transcript === "string" ? transcript : input.trim();
        if (!text || loading) return;

        if (typeof transcript !== "string") setInput("");

        // Stop any current audio
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }

        let currentSessionId = sessionId;
        if (!currentSessionId) {
            currentSessionId = crypto.randomUUID();
        }

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
                    language: lang,
                    age: userProfile?.age || 30,
                    gender: userProfile?.gender === "Male" ? 1 : 0
                }),
            });

            if (!res.ok) throw new Error("API Error");

            const data = await res.json();

            const aiMsg: Message = { role: "assistant", content: data.content, diagnosis: data.diagnosis };
            const finalMessages = [...newMessagesContext, aiMsg];

            setMessages(finalMessages);

            // Auto-save session to backend
            if (user) {
                const token = await user.getIdToken();
                await fetch(`${API_URL}/sessions/save`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        sessionId: currentSessionId,
                        messages: finalMessages,
                        language: lang,
                        risk_level: data.diagnosis?.risk_level || "Normal"
                    }),
                });

                // Update local context with the session ID if it was new
                if (!sessionId) {
                    loadSession(finalMessages, currentSessionId);
                }
            }

            if (autoSpeak) {
                playAudio(aiMsg.content, newMessagesContext.length);
            }
        } catch (err) {
            console.error("Chat error:", err);
            const errorMsg: Message = { role: "assistant", content: t.chatError };
            setMessages((prev: Message[]) => [...prev, errorMsg]);
            if (autoSpeak) playAudio(t.chatError, newMessagesContext.length);
        } finally {
            setLoading(false);
        }
    }, [input, loading, sessionId, messages, setMessages, lang, userProfile, user, loadSession, autoSpeak, playAudio, t]);

    useEffect(() => {
        if (typeof window !== "undefined") {
            const SpeechRecognitionClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (SpeechRecognitionClass) {
                recognitionRef.current = new SpeechRecognitionClass();
                if (recognitionRef.current) {
                    recognitionRef.current.continuous = false;
                    recognitionRef.current.interimResults = true;

                    recognitionRef.current.onresult = (e: SpeechRecognitionEvent) => {
                        const transcript = Array.from(e.results)
                            .map((result) => result[0])
                            .map((result) => result.transcript)
                            .join("");

                        setInput(transcript);

                        if (e.results[0].isFinal) {
                            setIsListening(false);
                            handleSend(transcript);
                        }
                    };
                    recognitionRef.current.onend = () => setIsListening(false);
                    recognitionRef.current.onerror = (err: SpeechRecognitionErrorEvent) => {
                        console.error("STT Error:", err);
                        setIsListening(false);
                    };
                }
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [handleSend]);

    const toggleSTT = () => {
        if (isListening) {
            recognitionRef.current?.stop();
        } else if (recognitionRef.current) {
            recognitionRef.current.lang = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-US";
            recognitionRef.current.start();
            setIsListening(true);
        }
    };

    // Initialize chat session from localStorage or use default greeting
    useEffect(() => {
        const savedMessages = localStorage.getItem("upchaar_messages");
        if (savedMessages) {
            try {
                setMessages(JSON.parse(savedMessages));
            } catch (e) {
                console.error("Failed to parse saved messages", e);
                setMessages([{ role: "assistant", content: t.chatGreeting }]);
            }
        } else {
            setMessages([{ role: "assistant", content: t.chatGreeting }]);
            // Auto-speak greeting if enabled
            setTimeout(() => {
                if (autoSpeak) playAudio(t.chatGreeting, 0);
            }, 1000);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Run on mount

    // Persist messages to localStorage on change
    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem("upchaar_messages", JSON.stringify(messages));
        }
    }, [messages]);

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

    useEffect(() => {
        // Cleanup speech on unmount
        const currentAudio = audioRef.current;
        return () => {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.src = "";
            }
        };
    }, []);


    return (
        <div className="flex flex-col h-[600px] glass-panel overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -z-10 mix-blend-screen transform translate-x-1/2 -translate-y-1/2" />

            {/* Inworld Voice Controls Header */}
            <div className="bg-surfaceHighlight/50 backdrop-blur-md px-6 py-3 border-b border-borderDark flex items-center justify-between z-20">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => resetChat(t.chatGreeting)}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] uppercase font-bold tracking-wider bg-surface border border-borderDark text-textMuted hover:text-primary hover:border-primary/50 transition-all shadow-sm group"
                        title="Start a fresh conversation"
                    >
                        <Plus className="w-3.5 h-3.5 group-hover:rotate-90 transition-transform" />
                        New Chat
                    </button>

                    <div className="w-px h-4 bg-borderDark mx-1" />

                    <button
                        onClick={() => setAutoSpeak(!autoSpeak)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] uppercase font-bold tracking-wider transition-all shadow-sm ${autoSpeak ? "bg-primary text-white shadow-neon" : "bg-surface border border-borderDark text-textMuted"
                            }`}
                        title="Auto-speak AI responses"
                    >
                        {autoSpeak ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                        {autoSpeak ? "Auto-Voice On" : "Auto-Voice Off"}
                    </button>

                    <button
                        onClick={() => setShowCall(true)}
                        className="relative flex items-center gap-2 px-4 py-2 rounded-full text-[10px] uppercase font-bold tracking-widest bg-gradient-to-r from-emerald-500 to-green-600 text-white shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:scale-105 active:scale-95 transition-all group overflow-hidden"
                    >
                        <motion.div
                            className="absolute inset-0 bg-white/20"
                            animate={{ x: ["-100%", "100%"] }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        />
                        <div className="relative flex items-center gap-2">
                            <span className="flex h-2 w-2 relative">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                            </span>
                            <Phone className="w-3.5 h-3.5 group-hover:rotate-12 transition-transform" />
                            Talk Live
                        </div>
                    </button>
                </div>

                <div className="flex items-center gap-2 text-[9px] text-textMuted uppercase tracking-[0.2em] font-black opacity-60">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                    Inworld AI Powered
                </div>

                <AnimatePresence>
                    {voiceError && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="absolute top-16 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-danger/90 text-white text-xs font-bold rounded-full shadow-lg backdrop-blur-md flex items-center gap-2"
                        >
                            <VolumeX className="w-3.5 h-3.5" />
                            {voiceError}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <div className="bg-surface/30 backdrop-blur-sm px-6 py-4 border-b border-borderDark flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg border border-primary/20 shadow-neon">
                        <ActivitySquare className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-textMain font-heading font-medium tracking-wide">{t.chatTitle}</h2>
                        <p className="text-primaryVibrant/70 text-xs tracking-wider uppercase mt-0.5">{t.chatSubtitle}</p>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar z-10">
                <AnimatePresence initial={false}>
                    {messages.map((m: Message, i: number) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            transition={{ type: "spring", stiffness: 200, damping: 20 }}
                            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div className={`max-w-[85%] px-5 py-3.5 text-sm whitespace-pre-wrap leading-relaxed shadow-lg relative group ${m.role === "user"
                                ? "bg-primary/10 text-primary border border-primary/30 rounded-2xl rounded-tr-sm"
                                : "bg-surface text-textMain border border-borderDark rounded-2xl rounded-tl-sm ring-1 ring-white/5"
                                }`}>
                                {m.role === "assistant" && (
                                    <button
                                        onClick={() => playAudio(m.content, i)}
                                        className="absolute -right-12 top-0 p-2 rounded-full bg-surface border border-borderDark text-textMuted opacity-0 group-hover:opacity-100 transition-all hover:text-primary hover:border-primary/50"
                                        title="Play Speech"
                                    >
                                        {playingMessageId === i ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                                    </button>
                                )}
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
                                                        {m.diagnosis.medicines.map((med: { name: string; purpose: string; guidance: string; warning?: string }, idx: number) => (
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
                <div className="flex items-center gap-3 relative max-w-4xl mx-auto">
                    <div className="flex-1 relative group">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={t.chatPlaceholderSymptoms || "Type to chat..."}
                            className="w-full bg-surface border border-borderDark rounded-full py-4 pl-6 pr-28 text-sm text-textMain outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-textMuted/60 shadow-inner"
                            onKeyDown={(e) => e.key === "Enter" && handleSend()}
                            disabled={loading}
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
                            <button
                                onClick={toggleSTT}
                                className={`p-2.5 rounded-full transition-all ${isListening ? "bg-danger text-white animate-pulse" : "bg-primary/5 text-primary hover:bg-primary/10"
                                    }`}
                                title="Voice Input"
                            >
                                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 shadow-sm" />}
                            </button>
                            <button
                                onClick={() => handleSend()}
                                disabled={loading || !input.trim()}
                                className="p-2.5 bg-primary text-white rounded-full hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-primary/20"
                            >
                                <Send className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <audio ref={audioRef} className="hidden" />

            <LiveCallOverlay
                isOpen={showCall}
                onClose={() => setShowCall(false)}
                language={lang}
                onTranscription={(text) => {
                    setInput(text);
                    handleSend(text);
                }}
                lastAiResponse={messages.length > 0 && messages[messages.length - 1].role === "assistant" ? messages[messages.length - 1].content : undefined}
            />
        </div>
    );
}
