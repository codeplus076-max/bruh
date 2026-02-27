"use client";

declare global {
    interface Window {
        SpeechRecognition: any;
        webkitSpeechRecognition: any;
    }
}

import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, PhoneOff, Volume2, ActivitySquare } from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";

interface LiveCallOverlayProps {
    isOpen: boolean;
    onClose: () => void;
    language: string;
    onTranscription: (text: string) => void;
    lastAiResponse?: string;
}

export function LiveCallOverlay({ isOpen, onClose, language, onTranscription, lastAiResponse }: LiveCallOverlayProps) {
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    const playResponse = useCallback(async (text: string) => {
        setIsSpeaking(true);
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        console.log(`LiveCall: Stream fetch from ${API_URL}/voice/stream`);

        const fallbackToSpeechSynth = () => {
            console.warn("LiveCall: Falling back to Browser Speech Synthesis.");
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = language === "hi" ? "hi-IN" : language === "mr" ? "mr-IN" : "en-US";
            utterance.onend = () => {
                setIsSpeaking(false);
                startListening();
            };
            utterance.onerror = () => {
                setIsSpeaking(false);
                startListening();
            };
            window.speechSynthesis.speak(utterance);
        };

        try {
            const response = await fetch(`${API_URL}/voice/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, language })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                if (audioRef.current) {
                    audioRef.current.src = url;
                    audioRef.current.play().catch(e => {
                        console.error("LiveCall: Audio play blocked:", e);
                        fallbackToSpeechSynth();
                    });
                    audioRef.current.onended = () => {
                        setIsSpeaking(false);
                        URL.revokeObjectURL(url);
                        startListening();
                    };
                }
            } else {
                console.error("LiveCall: Stream request failed", response.status);
                fallbackToSpeechSynth();
            }
        } catch (error) {
            console.error("LiveCall: TTS fetch error:", error);
            fallbackToSpeechSynth();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [language]); // onTranscription is stable

    const startListening = useCallback(() => {
        if (recognitionRef.current && !isSpeaking) {
            try {
                recognitionRef.current.lang = language === "hi" ? "hi-IN" : language === "mr" ? "mr-IN" : "en-US";
                recognitionRef.current.start();
                setIsListening(true);
            } catch (e) {
                console.warn("Speech recognition already started or failed:", e);
            }
        }
    }, [isSpeaking, language]);

    useEffect(() => {
        if (typeof window !== "undefined") {
            const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognitionClass) {
                recognitionRef.current = new SpeechRecognitionClass();
                if (recognitionRef.current) {
                    recognitionRef.current.continuous = false;
                    recognitionRef.current.interimResults = false;

                    recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
                        const transcript = event.results[0][0].transcript;
                        onTranscription(transcript);
                        setIsListening(false);
                    };

                    recognitionRef.current.onerror = () => setIsListening(false);
                    recognitionRef.current.onend = () => setIsListening(false);
                }
            }
        }
    }, [onTranscription]);

    useEffect(() => {
        if (isOpen && lastAiResponse) {
            playResponse(lastAiResponse);
        }
    }, [isOpen, lastAiResponse, playResponse]);

    const toggleMic = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
        } else {
            startListening();
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] bg-background/95 backdrop-blur-xl flex flex-col items-center justify-between p-8"
            >
                <div className="flex flex-col items-center mt-12 space-y-4">
                    <div className="relative">
                        <motion.div
                            animate={isListening || isSpeaking ? { scale: [1, 1.2, 1] } : {}}
                            transition={{ repeat: Infinity, duration: 2 }}
                            className="w-32 h-32 rounded-full bg-primary/20 flex items-center justify-center border-4 border-primary/30"
                        >
                            <div className="w-24 h-24 rounded-full bg-primary flex items-center justify-center">
                                {isSpeaking ? <Volume2 className="w-10 h-10 text-white" /> : <Mic className="w-10 h-10 text-white" />}
                            </div>
                        </motion.div>
                        {(isListening || isSpeaking) && (
                            <motion.div
                                animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                                transition={{ repeat: Infinity, duration: 1.5 }}
                                className="absolute inset-0 rounded-full border-2 border-primary"
                            />
                        )}
                    </div>
                    <h2 className="text-2xl font-bold text-textMain">
                        {isSpeaking ? "Upchaar is Speaking..." : isListening ? "Listening..." : "Upchaar AI Agent"}
                    </h2>
                    <p className="text-textMuted text-center max-w-sm">
                        Real-time multilingual medical triage call. Please speak clearly.
                    </p>
                </div>

                <div className="flex items-center gap-8 mb-12">
                    <button
                        onClick={toggleMic}
                        className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${isListening ? "bg-red-500 text-white" : "bg-surface border border-borderDark text-textMain"
                            }`}
                    >
                        {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                    </button>

                    <button
                        onClick={onClose}
                        className="w-20 h-20 rounded-full bg-red-600 flex items-center justify-center text-white shadow-lg hover:bg-red-700 transition-all"
                    >
                        <PhoneOff className="w-8 h-8" />
                    </button>

                    <div className="w-16 h-16 rounded-full bg-surface border border-borderDark flex items-center justify-center text-textMuted">
                        <ActivitySquare className="w-6 h-6" />
                    </div>
                </div>

                <audio ref={audioRef} className="hidden" />
            </motion.div>
        </AnimatePresence>
    );
}

