"use client";

import { useEffect, useState } from "react";
import { db } from "@/lib/firebase";
import { collection, query, orderBy, limit, onSnapshot, doc, deleteDoc } from "firebase/firestore";
import { useAuth } from "@/context/AuthContext";
import { useChat } from "@/context/ChatStateContext";
import { useLanguage } from "@/context/LanguageContext";
import { History, ChevronRight, Clock, MessageCircle, Trash2 } from "lucide-react";
import { motion } from "framer-motion";

interface ChatSession {
    id: string;
    title?: string;
    risk_level?: string;
    language?: string;
    messages?: { role: "user" | "assistant"; content: string; diagnosis?: object }[];
    updatedAt?: number;
}

interface ChatHistoryProps {
    refreshKey?: number;
    onSessionSelect?: () => void; // Called after user picks a session (e.g. close the panel)
}

export function ChatHistory({ refreshKey = 0, onSessionSelect }: ChatHistoryProps) {
    const { user } = useAuth();
    const { loadSession } = useChat();
    const { t } = useLanguage();
    const [history, setHistory] = useState<ChatSession[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) return;

        console.log(`[ChatHistory] Setting up real-time listener for: ${user.uid}`);
        const q = query(
            collection(db, "users", user.uid, "sessions"),
            orderBy("updatedAt", "desc"),
            limit(20)
        );

        // real-time listener
        const unsubscribe = onSnapshot(q, (snapshot) => {
            console.log(`[ChatHistory] Snapshot update: ${snapshot.size} sessions found`);
            const docs = snapshot.docs.map(d => ({ id: d.id, ...d.data() } as ChatSession));
            setHistory(docs);
            setLoading(false);
        }, (error) => {
            console.error("[ChatHistory] Snapshot error:", error);
            setLoading(false);
        });

        return () => unsubscribe();
    }, [user, refreshKey]); // FIX: refreshKey triggers a fresh fetch when panel opens

    if (!user) return null;

    const formatTime = (ts?: number) => {
        if (!ts) return "";
        return new Date(ts * 1000).toLocaleDateString("en-IN", {
            day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
        });
    };

    const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        if (confirm("Delete this session permanently?")) {
            try {
                await deleteDoc(doc(db, "users", user!.uid, "sessions", sessionId));
            } catch (err) {
                console.error("Delete failed:", err);
                alert("Failed to delete session.");
            }
        }
    };

    return (
        <div className="flex flex-col h-full bg-surface/30 backdrop-blur-xl border border-borderDark rounded-2xl overflow-hidden shadow-glass">
            <div className="p-4 border-b border-borderDark flex items-center gap-3 bg-primary/5">
                <History className="w-5 h-5 text-primary" />
                <h3 className="font-heading font-bold text-sm tracking-tight">{t.chatHistory || "Chat History"}</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
                {loading ? (
                    <div className="p-4 space-y-3">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-16 bg-primary/5 rounded-xl animate-pulse" />
                        ))}
                    </div>
                ) : history.length === 0 ? (
                    <div className="p-8 text-center text-textMuted text-xs italic flex flex-col items-center gap-3">
                        <MessageCircle className="w-6 h-6 opacity-40" />
                        No previous sessions found.
                    </div>
                ) : (
                    history.map((session) => (
                        <motion.div
                            key={session.id}
                            className="relative group"
                        >
                            <motion.button
                                whileHover={{ scale: 1.01 }}
                                whileTap={{ scale: 0.99 }}
                                onClick={() => {
                                    loadSession(session.messages || [], session.id);
                                    onSessionSelect?.(); // Close panel
                                }}
                                className="w-full text-left p-4 rounded-xl border border-borderDark hover:border-primary/40 hover:bg-primary/5 transition-all group relative overflow-hidden"
                            >
                                <div className="flex flex-col gap-1.5 pr-8">
                                    <div className="flex items-center justify-between">
                                        <span className="text-[10px] font-mono text-primary uppercase tracking-wider">
                                            {session.risk_level || "Session"}
                                        </span>
                                        <span className="text-[9px] text-textMuted flex items-center gap-1">
                                            <Clock className="w-2.5 h-2.5" />
                                            {formatTime(session.updatedAt)}
                                        </span>
                                    </div>
                                    <span className="text-sm font-bold text-textMain line-clamp-1">
                                        {session.title || "Health Consultation"}
                                    </span>
                                    <span className="text-[11px] text-textMuted line-clamp-1">
                                        {session.messages?.find(m => m.role === "user")?.content || "..."}
                                    </span>
                                </div>
                                <ChevronRight className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/0 group-hover:text-primary transition-all mr-6" />
                            </motion.button>
                            
                            <button
                                onClick={(e) => handleDelete(e, session.id)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-red-500/10 text-red-400 opacity-0 group-hover:opacity-100 hover:bg-red-500 hover:text-white transition-all z-10"
                                title="Delete Session"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                            </button>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    );
}
