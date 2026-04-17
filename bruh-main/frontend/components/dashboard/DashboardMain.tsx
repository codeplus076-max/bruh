"use client";

import { useState, useEffect } from "react";
import { Send, Plus, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { useDashboardStore } from "@/context/dashboardStore";
import { saveEpisodeMeta, saveMessageTick, fetchEpisodeMessages } from "@/lib/firestoreOperations";

import { EpisodeContextCard } from "./EpisodeContextCard";
import { MultiViewTabs } from "./MultiViewTabs";
import { ChatHistory } from "./ChatHistory"; // We will rewrite this

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

import { ParsedSnapshot } from "@/lib/dashboardUtils";

interface Message {
    role: string;
    content: string;
    parsed_snapshot?: ParsedSnapshot;
}

export function DashboardMain() {
    const { user } = useAuth();
    const { lang } = useLanguage();
    const { currentEpisodeId, currentSnapshot, onNewResponse, setCurrentEpisode } = useDashboardStore();
    
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [localMessages, setLocalMessages] = useState<Message[]>([]);

    // Handle initial episode load or fresh state
    useEffect(() => {
        if (currentEpisodeId && user) {
            fetchEpisodeMessages(currentEpisodeId).then(messages => {
                setLocalMessages(messages as unknown as Message[]);
            });
        } else {
            setLocalMessages([]);
        }
    }, [currentEpisodeId, user]);

    const handleSend = async () => {
        if (!input.trim() || !user) return;
        const currentInput = input;
        setInput("");
        setIsLoading(true);

        const newMessages = [...localMessages, { role: "user", content: currentInput }];
        setLocalMessages(newMessages);

        try {
            const formData = new FormData();
            formData.append("message", currentInput);
            formData.append("language", lang === "en" ? "English" : "Hindi");
            // If continuing episode, we pass context so backend can relate.
            formData.append("context", JSON.stringify(newMessages.slice(-5))); 

            const response = await fetch(`${API_URL}/chat`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) throw new Error("Backend connection failed");
            
            const data = await response.json();
            
            // Native diff triggering in Zustand
            onNewResponse(data.diagnosis);

            // Fetch the freshly updated snapshot state from Zustand (it was synchronous)
            const freshSnapshot = useDashboardStore.getState().currentSnapshot;

            if (freshSnapshot) {
                // Background Sync to Firestore 
                const boundEpisodeId = await saveEpisodeMeta(user.uid, currentEpisodeId, freshSnapshot);
                
                if (!currentEpisodeId) {
                    setCurrentEpisode(boundEpisodeId);
                }

                await saveMessageTick(boundEpisodeId, "user", currentInput, undefined);
                await saveMessageTick(boundEpisodeId, "assistant", data.content, freshSnapshot);
                
                setLocalMessages(prev => [...prev, { role: "assistant", content: data.content }]);
            }

        } catch (err) {
            console.error("AI Evaluation Error", err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen w-full bg-[#0a0c10] text-gray-200 overflow-hidden font-sans">
            {/* Left Sidebar (Episode Tracker) */}
            <div className="w-80 border-r border-gray-800 bg-[#11151a] flex flex-col">
                <div className="p-4 border-b border-gray-800">
                    <button 
                        onClick={() => setCurrentEpisode(null)}
                        className="w-full py-2.5 flex items-center justify-center gap-2 bg-teal-500/10 hover:bg-teal-500/20 text-teal-400 rounded-lg transition-colors border border-teal-500/20"
                    >
                        <Plus className="w-4 h-4" /> New Health Episode
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto">
                    {/* We mount the refactored ChatHistory component which now queries `episodes` */}
                    <ChatHistory />
                </div>
            </div>

            {/* Main Operational Container */}
            <div className="flex-1 flex flex-col h-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-teal-900/10 via-[#0a0c10] to-[#0a0c10]">
                
                {currentSnapshot && <EpisodeContextCard />}

                <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
                    {!currentSnapshot && localMessages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
                            <div className="w-16 h-16 bg-teal-500/10 rounded-full flex items-center justify-center">
                                <Plus className="w-8 h-8 text-teal-500" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-200">New Health Episode</h2>
                            <p className="text-gray-400 leading-relaxed text-sm">
                                Enter your symptoms below to initialize a progression-aware timeline. All evaluations are continuously tracked and dynamically analyzed.
                            </p>
                        </div>
                    ) : (
                        <MultiViewTabs />
                    )}

                    {/* Mini Stream rendering text logic at bottom to show actual raw chat history softly */}
                    {localMessages.length > 0 && (
                        <div className="mt-8 pt-8 border-t border-gray-800/50 max-w-4xl mx-auto space-y-4">
                            <h3 className="text-xs uppercase tracking-widest text-gray-500 mb-4 px-2">Clinical Data Stream</h3>
                            {localMessages.map((m, i) => (
                                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`text-sm tracking-wide leading-relaxed p-3 rounded-lg max-w-[80%] ${m.role === 'user' ? 'bg-teal-500/10 text-teal-50 border border-teal-500/20' : 'bg-transparent border-l-2 border-gray-700 pl-4 text-gray-400'}`}>
                                        {m.content.replace(/#.*📋.*/gi, '')} {/* Strip headers */}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Secure Input Controller at Bottom */}
                <div className="p-4 border-t border-gray-800 bg-[#11151a]">
                    <div className="max-w-4xl mx-auto relative rounded-xl border border-gray-700 bg-gray-900 focus-within:border-teal-500/50 transition-colors shadow-lg">
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSend()}
                            placeholder="Describe progressive symptoms..."
                            disabled={isLoading}
                            className="w-full bg-transparent p-4 pr-14 text-sm text-gray-200 placeholder-gray-500 outline-none"
                        />
                        <button
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-teal-500/20 hover:bg-teal-500/30 text-teal-400 rounded-lg disabled:opacity-50 transition-colors"
                        >
                            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}
