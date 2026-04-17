"use client";

import type { ISpeechRecognition, ISpeechRecognitionEvent, ISpeechRecognitionErrorEvent, ISpeechRecognitionResult, SpeechRecognitionResultAlternative } from "@/types/speech";



import { useState, useRef, useEffect, useCallback } from "react";
import { Send, ActivitySquare, Volume2, VolumeX, FileText, Mic, MicOff, Phone, Play, Pause, Plus, History, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";


import { useLanguage } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";
import { useChat, Diagnosis, Message } from "@/context/ChatStateContext";
import { LiveCallOverlay } from "./LiveCallOverlay";
import { SummaryCard } from "./SummaryCard";
import { GenerateSummaryResponse } from "@/types/summary";
import { handleAIVoice, cancelAIVoice } from "@/lib/voiceHandler";
import { TriageCard } from "./TriageCard";
import { ChatHistory } from "./ChatHistory";
import { db } from "@/lib/firebase";
import { doc, setDoc } from "firebase/firestore";

const audioCache = new Map<string, string>();
const MAX_AUDIO_CACHE = 20; // Revoke oldest ObjectURLs to prevent memory leaks

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://bruh-1-u248.onrender.com";

export function ChatInterface({ input, setInput }: { input: string, setInput: (v: string) => void }) {
    const { lang, t } = useLanguage();
    const { user, userProfile } = useAuth();
    const { messages, sessionId, setMessages, resetChat, loadSession } = useChat();
    const [loading, setLoading] = useState(false);
    const [loadingStatus, setLoadingStatus] = useState("Analyzing symptoms...");
    const [autoSpeak, setAutoSpeak] = useState(false);
    const [showCall, setShowCall] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
    const [isListening, setIsListening] = useState(false);
    const [playingMessageId, setPlayingMessageId] = useState<number | null>(null);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const [isGeneratingReport, setIsGeneratingReport] = useState(false);
    const [reportSummary, setReportSummary] = useState<GenerateSummaryResponse | null>(null);

    const bottomRef = useRef<HTMLDivElement>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const recognitionRef = useRef<ISpeechRecognition | null>(null);

    const playAudio = useCallback(async (text: string, index: number) => {
        if (playingMessageId === index) {
            audioRef.current?.pause();
            setPlayingMessageId(null);
            return;
        }

        setVoiceError(null);
        setPlayingMessageId(index);

        // Unified cross-platform fallback:
        // MIT App Inventor → Web Speech API → silent
        const fallbackToSpeechSynthesis = () => {
            console.warn("[Voice] Falling back to cross-platform voice handler.");
            handleAIVoice(
                text,
                lang,
                () => setPlayingMessageId(null),
                () => finalFallback()
            );
        };

        const finalFallback = () => {
            console.error("[Voice] All voice methods failed.");
            setVoiceError("Voice unavailable. Showing text guidance.");
            setPlayingMessageId(null);
            // Auto-clear error after 5s
            setTimeout(() => setVoiceError(null), 5000);
        };

        const cacheKey = `${lang}_${text.substring(0, 100)}`;
        if (audioCache.has(cacheKey)) {
            const url = audioCache.get(cacheKey)!;
            if (audioRef.current) {
                audioRef.current.src = url;
                const playPromise = audioRef.current.play();
                if (playPromise !== undefined) {
                    playPromise.catch(() => fallbackToSpeechSynthesis());
                }
                audioRef.current.onended = () => setPlayingMessageId(null);
            }
            return;
        }

        try {
            const response = await fetch(`${API_URL}/voice/tts`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, language: lang })
            });

            if (response.ok) {
                const blob = await response.blob();
                if (blob.size < 100) {
                    const errorText = await blob.text();
                    console.error("[Voice] Small blob text content:", errorText.substring(0, 100));
                    throw new Error("Audio blob too small/invalid");
                }

                const url = URL.createObjectURL(blob);
                // Evict oldest entry to prevent ObjectURL memory leak
                if (audioCache.size >= MAX_AUDIO_CACHE) {
                    const oldestKey = audioCache.keys().next().value;
                    if (oldestKey) {
                        URL.revokeObjectURL(audioCache.get(oldestKey)!);
                        audioCache.delete(oldestKey);
                    }
                }
                audioCache.set(cacheKey, url);

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
        // Use functional updater — avoids including `messages` in the dep array
        // which would re-wire STT recognition on every single message
        let newMessagesContext: Message[] = [];
        setMessages(prev => {
            newMessagesContext = [...prev, userMsg];
            return newMessagesContext;
        });
        setReportSummary(null); // Clear previous report when continuing chat
        setLoadingStatus("Analyzing symptoms...");
        setLoading(true);

        const statusTimer = setTimeout(() => {
            setLoadingStatus("Generating medical guidance...");
        }, 3000);

        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    // Cleanse diagnosis obj from payload sent to backend to match strict pydantic type
                    messages: newMessagesContext.map(m => ({ role: m.role, content: m.content })),
                    language: lang,
                    age: userProfile?.age || 30,
                    gender: userProfile?.gender === "Male" ? 1 : 0,
                    name: userProfile?.fullName || "Patient"
                }),
            });

            if (!res.ok) throw new Error("API Error");

            const data = await res.json();

            const aiMsg: Message = { 
                role: "assistant", 
                content: data.content, 
                diagnosis: data.diagnosis ? { ...data.diagnosis, sessionId: currentSessionId } : undefined 
            };
            const finalMessages = [...newMessagesContext, aiMsg];

            setMessages(finalMessages);

            // ── Direct Firestore save (more reliable than backend fire-and-forget) ──
            if (user) {
                try {
                    // Auto-generate title from the first user message
                    const firstUserMsg = finalMessages.find((m: Message) => m.role === "user");
                    const dateStr = new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short" });
                    const symptomSnippet = firstUserMsg
                        ? firstUserMsg.content.split(" ").slice(0, 3).join(" ")
                        : "Health Consultation";
                    const title = `${symptomSnippet} - ${dateStr}`;

                    // Only write createdAt on first save (new session); omit it on subsequent
                    // merges so the original creation timestamp is preserved.
                    const isNewSession = !sessionId;
                    // --- Sanitization Helper ---
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    const sanitizePayload = (data: unknown): any => {
                        if (Array.isArray(data)) return data.map(v => sanitizePayload(v));
                        if (data !== null && typeof data === 'object') {
                            const obj: Record<string, unknown> = {};
                            for (const [k, v] of Object.entries(data as Record<string, unknown>)) {
                                if (v !== undefined) obj[k] = sanitizePayload(v);
                            }
                            return obj;
                        }
                        return data;
                    };

                    const savePayload = sanitizePayload({
                        sessionId: currentSessionId,
                        userId: user.uid,
                        title,
                        messages: finalMessages,
                        language: lang,
                        risk_level: data.diagnosis?.urgency || data.diagnosis?.risk?.level || data.diagnosis?.risk_level || "Normal",
                        predictions: { 
                            disease: data.diagnosis?.disease || data.diagnosis?.risk?.cause || data.predictions?.disease || "Unknown Condition" 
                        },
                        diagnosis: data.diagnosis || null,
                        updatedAt: Math.floor(Date.now() / 1000),
                        createdAt: isNewSession ? Math.floor(Date.now() / 1000) : undefined
                    });

                    await setDoc(
                        doc(db, "users", user.uid, "sessions", currentSessionId),
                        savePayload,
                        { merge: true }
                    );
                } catch (saveErr) {
                    console.error("[Session] Firestore direct save failed:", saveErr);
                }

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
            clearTimeout(statusTimer);
            setLoading(false);
        }
    // NOTE: `messages` intentionally omitted from deps — we use the functional
    // setMessages(prev => ...) updater pattern instead, which avoids a new
    // handleSend reference on every message (which would re-wire the STT recognition).
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [input, setInput, loading, sessionId, setMessages, lang, userProfile, user, loadSession, autoSpeak, playAudio, t]);

    const handleGenerateReport = async (diagnosisData: Diagnosis) => {
        if (!diagnosisData) return;
        setIsGeneratingReport(true);
        try {
            const res = await fetch(`${API_URL}/generate-summary`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    messages: messages.map(m => ({ role: m.role, content: m.content })),
                    diagnosis: diagnosisData,
                    patient_profile: {
                        name: user?.displayName || "Unknown",
                        age: userProfile?.age?.toString() || "Unknown",
                        gender: userProfile?.gender || "Unknown"
                    },
                    language: lang
                }),
            });

            if (!res.ok) throw new Error("Failed to generate report");

            const data: GenerateSummaryResponse = await res.json();
            setReportSummary(data);
        } catch (err) {
            console.error("Report generation error:", err);
            // We could show a toast here if we had a toast system
        } finally {
            setIsGeneratingReport(false);
        }
    };

    useEffect(() => {
        if (typeof window !== "undefined") {
            const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognitionClass) {
                recognitionRef.current = new SpeechRecognitionClass();
                if (recognitionRef.current) {
                    recognitionRef.current.continuous = false;
                    recognitionRef.current.interimResults = true;

                    recognitionRef.current.onresult = (e: ISpeechRecognitionEvent) => {
                        const transcript = Array.from<ISpeechRecognitionResult>(e.results as unknown as Iterable<ISpeechRecognitionResult> | ArrayLike<ISpeechRecognitionResult>)
                            .map((result: ISpeechRecognitionResult) => result[0])
                            .map((alt: SpeechRecognitionResultAlternative) => alt.transcript)
                            .join("");

                        setInput(transcript);

                        if (e.results[0].isFinal) {
                            setIsListening(false);
                            handleSend(transcript);
                        }
                    };
                    recognitionRef.current.onend = () => setIsListening(false);
                    recognitionRef.current.onerror = (err: ISpeechRecognitionErrorEvent) => {
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
        const storageKey = user ? `upchaar_messages_${user.uid}` : "upchaar_messages";
        const savedMessages = localStorage.getItem(storageKey);
        const greetingText = userProfile?.fullName ? t.chatGreeting.replace("Hi there!", `Hi ${userProfile.fullName.split(' ')[0]}!`) : t.chatGreeting;
        
        if (savedMessages) {
            try {
                setMessages(JSON.parse(savedMessages));
            } catch (e) {
                console.error("Failed to parse saved messages", e);
                setMessages([{ role: "assistant", content: greetingText }]);
            }
        } else {
            setMessages([{ role: "assistant", content: greetingText }]);
            // Auto-speak greeting if enabled
            setTimeout(() => {
                if (autoSpeak) playAudio(greetingText, 0);
            }, 1000);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, userProfile?.fullName]); // Run on mount and user login

    // Persist messages to localStorage on change
    useEffect(() => {
        if (messages.length > 0) {
            const storageKey = user ? `upchaar_messages_${user.uid}` : "upchaar_messages";
            localStorage.setItem(storageKey, JSON.stringify(messages));
        }
    }, [messages, user]);

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

    useEffect(() => {
        // Cleanup all speech on unmount — covers both native TTS bridge and Web Speech API
        const currentAudio = audioRef.current;
        return () => {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.src = "";
            }
            // Cancel any in-progress cross-platform voice (MIT App or browser)
            cancelAIVoice();
        };
    }, []);


    return (
        <div className="flex flex-col h-[80vh] min-h-[500px] md:h-[650px] w-full glass-panel overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -z-10 mix-blend-screen transform translate-x-1/2 -translate-y-1/2" />

            {/* Inworld Voice Controls Header */}
            <div className="bg-surfaceHighlight/50 backdrop-blur-md px-4 sm:px-6 py-3 border-b border-borderDark flex flex-col sm:flex-row items-center justify-between z-20 gap-3 sm:gap-0">
                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 sm:gap-3 w-full sm:w-auto">
                    {/* History Button */}
                    <button
                        onClick={() => {
                            setHistoryRefreshKey(k => k + 1); // Force re-fetch latest sessions
                            setShowHistory(true);
                        }}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] uppercase font-bold tracking-wider bg-surface border border-borderDark text-textMuted hover:text-primary hover:border-primary/50 transition-all shadow-sm group"
                        title="View past sessions"
                    >
                        <History className="w-3.5 h-3.5" />
                        History
                    </button>

                    <div className="w-px h-4 bg-borderDark mx-0.5" />

                    {/* New Chat Button — saves current session BEFORE resetting */}
                    <button
                        onClick={async () => {
                            // BUG FIX: Save the current session to backend BEFORE clearing state
                            if (user && messages.length > 1 && sessionId) {
                                try {
                                    const firstUserMsg = messages.find((m: Message) => m.role === "user");
                                    const dateStr = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
                                    const symptomSnippet = firstUserMsg 
                                        ? firstUserMsg.content.split(" ").slice(0, 3).join(" ") 
                                        : "Health Consultation";
                                    const title = `${symptomSnippet} - ${dateStr}`;

                                    const savePath = `users/${user.uid}/sessions/${sessionId}`;
                                    console.log(`[Firestore] New Chat Save Attempt to: ${savePath}`);
                                    const risk_level = messages.findLast((m: Message) => m.diagnosis)?.diagnosis?.risk?.level || 
                                                     messages.findLast((m: Message) => m.diagnosis)?.diagnosis?.risk_level || "Normal";
                                    
                                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                    const sanitizePayload = (data: unknown): any => {
                                        if (Array.isArray(data)) return data.map(v => sanitizePayload(v));
                                        if (data !== null && typeof data === 'object') {
                                            const obj: Record<string, unknown> = {};
                                            for (const [k, v] of Object.entries(data as Record<string, unknown>)) {
                                                if (v !== undefined) obj[k] = sanitizePayload(v);
                                            }
                                            return obj;
                                        }
                                        return data;
                                    };

                                    const savePayload = sanitizePayload({
                                        sessionId,
                                        userId: user.uid,
                                        title,
                                        messages,
                                        language: lang,
                                        risk_level,
                                        updatedAt: Math.floor(Date.now() / 1000),
                                    });

                                    await setDoc(
                                        doc(db, "users", user.uid, "sessions", sessionId),
                                        savePayload,
                                        { merge: true }
                                    );
                                    console.log(`[Firestore] New Chat Save successful to: ${savePath}`);
                                } catch (e) {
                                    console.error("[NewChat] Failed to save session to Firestore:", e);
                                }
                            }
                            const greetingText = userProfile?.fullName ? t.chatGreeting.replace("Hi there!", `Hi ${userProfile.fullName.split(' ')[0]}!`) : t.chatGreeting;
                            resetChat(greetingText);
                            setReportSummary(null);
                        }}
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

                <div className="hidden md:flex items-center gap-2 text-[9px] text-textMuted uppercase tracking-[0.2em] font-black opacity-60 w-full sm:w-auto justify-center sm:justify-end">
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

            <div className="bg-surface/30 backdrop-blur-sm px-4 sm:px-6 py-3 sm:py-4 border-b border-borderDark flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg border border-primary/20 shadow-neon shrink-0">
                        <ActivitySquare className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-textMain font-heading font-medium tracking-wide text-base sm:text-lg">{t.chatTitle}</h2>
                        <p className="text-primaryVibrant/70 text-[10px] sm:text-xs tracking-wider uppercase mt-0.5 line-clamp-1">{t.chatSubtitle}</p>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 sm:space-y-5 custom-scrollbar z-10">
                <AnimatePresence initial={false}>
                    {messages.map((m: Message, i: number) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            transition={{ type: "spring", stiffness: 200, damping: 20 }}
                            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div className={`max-w-[95%] sm:max-w-[85%] md:max-w-[80%] px-4 py-3 sm:px-5 sm:py-3.5 text-sm whitespace-pre-wrap leading-relaxed shadow-lg relative group ${m.role === "user"
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
                                    <div className="mt-4 flex flex-col gap-3">
                                        <TriageCard diagnosis={m.diagnosis} />
                                        
                                        <div className="mt-4 pt-4 border-t border-borderDark space-y-3">
                                            <button
                                                onClick={() => handleGenerateReport(m.diagnosis!)}
                                                disabled={isGeneratingReport}
                                                className="w-full py-3 bg-gradient-to-r from-primary to-primary-light hover:from-primary-light hover:to-primary text-white text-sm rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-neon disabled:opacity-50"
                                            >
                                                {isGeneratingReport ? (
                                                    <span className="flex items-center gap-2">
                                                        <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                                        Generating Summary...
                                                    </span>
                                                ) : (
                                                    <>
                                                        <FileText className="w-4 h-4" /> Generate Patient Report
                                                    </>
                                                )}
                                            </button>
                                            
                                            <p className="text-[10px] text-textMuted text-center italic">
                                                Clicking will render a medical summary below
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}

                    {/* Rendering the summary card directly in the chat window if it exists */}
                    {reportSummary && (
                        <motion.div
                            key="report-summary-card"
                            initial={{ opacity: 0, y: 10, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ type: "spring", stiffness: 200, damping: 20 }}
                            className="w-full pb-4"
                        >
                            <SummaryCard summary={reportSummary.structured_data} rawText={reportSummary.summary_text} />
                        </motion.div>
                    )}

                    {loading && (
                        <motion.div
                            key="loading-indicator"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex justify-start"
                        >
                            <div className="bg-surface border border-borderDark rounded-2xl rounded-tl-sm px-5 py-4 shadow-glass max-w-[85%]">
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center gap-1.5">
                                        {[0, 150, 300].map((d) => (
                                            <span key={d} className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-pulse" style={{ animationDelay: `${d}ms` }} />
                                        ))}
                                    </div>
                                    <span className="text-sm text-textMuted animate-pulse">{loadingStatus}</span>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <div ref={bottomRef} className="h-1" />
            </div>

            <div className="p-3 sm:p-4 bg-surfaceHighlight/40 backdrop-blur-lg border-t border-borderDark z-10">
                <div className="flex items-center gap-2 sm:gap-3 relative max-w-4xl mx-auto">
                    <div className="flex-1 relative group">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={t.chatPlaceholderSymptoms || "Type to chat..."}
                            className="w-full bg-surface border border-borderDark rounded-full py-3.5 sm:py-4 pl-4 sm:pl-6 pr-24 sm:pr-28 text-sm text-textMain outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-textMuted/60 shadow-inner"
                            onKeyDown={(e) => e.key === "Enter" && handleSend()}
                            disabled={loading}
                        />
                        <div className="absolute right-1.5 sm:right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 sm:gap-1.5">
                            <button
                                onClick={toggleSTT}
                                className={`p-2 sm:p-2.5 rounded-full transition-all min-w-[40px] min-h-[40px] sm:min-w-[44px] sm:min-h-[44px] flex items-center justify-center ${isListening ? "bg-danger text-white animate-pulse" : "bg-primary/5 text-primary hover:bg-primary/10"
                                    }`}
                                title="Voice Input"
                            >
                                {isListening ? <MicOff className="w-4 h-4 sm:w-5 sm:h-5" /> : <Mic className="w-4 h-4 sm:w-5 sm:h-5 shadow-sm" />}
                            </button>
                            <button
                                onClick={() => handleSend()}
                                disabled={loading || !input.trim()}
                                className="p-2 sm:p-2.5 bg-primary text-white rounded-full hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-primary/20 min-w-[40px] min-h-[40px] sm:min-w-[44px] sm:min-h-[44px] flex items-center justify-center"
                            >
                                <Send className="w-4 h-4 sm:w-5 sm:h-5" />
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

            {/* ── History Slide-in Panel ── */}
            <AnimatePresence>
                {showHistory && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            key="backdrop"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowHistory(false)}
                            className="absolute inset-0 bg-black/60 backdrop-blur-sm z-30"
                        />
                        {/* Panel */}
                        <motion.div
                            key="panel"
                            initial={{ x: "-100%", opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: "-100%", opacity: 0 }}
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            className="absolute left-0 top-0 h-full w-[320px] max-w-[90%] z-40 bg-[#0f151e] border-r border-borderDark shadow-2xl flex flex-col"
                        >
                            {/* Panel Header */}
                            <div className="flex items-center justify-between px-4 py-3.5 border-b border-borderDark bg-primary/5">
                                <div className="flex items-center gap-2.5">
                                    <History className="w-4 h-4 text-primary" />
                                    <span className="text-sm font-bold text-textMain tracking-wide uppercase">Past Sessions</span>
                                </div>
                                <button
                                    onClick={() => setShowHistory(false)}
                                    className="p-1.5 rounded-lg hover:bg-white/10 text-textMuted hover:text-white transition-colors"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Scrollable List */}
                            <div className="flex-1 overflow-y-auto custom-scrollbar">
                                <ChatHistory 
                                    refreshKey={historyRefreshKey} 
                                    onSessionSelect={() => setShowHistory(false)}
                                />
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}
