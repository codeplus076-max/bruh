"use client";

import { useEffect, useState } from "react";
import { db } from "@/lib/firebase";
import { collection, query, orderBy, getDocs, limit } from "firebase/firestore";
import { useAuth } from "@/context/AuthContext";
import { useChat } from "@/context/ChatStateContext";
import { useLanguage } from "@/context/LanguageContext";
import { History, ChevronRight, Clock } from "lucide-react";
import { motion } from "framer-motion";

interface ChatSession {
    id: string;
    risk_level?: string;
    predictions?: {
        disease?: string;
    };
    symptoms?: string;
    messages?: { role: "user" | "assistant"; content: string }[];
}

export function ChatHistory() {
    const { user } = useAuth();
    const { loadSession } = useChat();
    const { t } = useLanguage();
    const [history, setHistory] = useState<ChatSession[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) return;

        const fetchHistory = async () => {
            try {
                const q = query(
                    collection(db, "users", user.uid, "sessions"),
                    orderBy("createdAt", "desc"),
                    limit(10)
                );
                const querySnapshot = await getDocs(q);
                const docs = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as ChatSession));
                setHistory(docs);
            } catch (e) {
                console.error("Error fetching history:", e);
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, [user]);

    if (!user) return null;

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
                    <div className="p-8 text-center text-textMuted text-xs italic">
                        No previous sessions found.
                    </div>
                ) : (
                    history.map((session) => (
                        <motion.button
                            key={session.id}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => loadSession(session.messages || [], session.id)}
                            className="w-full text-left p-4 rounded-xl border border-borderDark hover:border-primary/40 hover:bg-primary/5 transition-all group relative overflow-hidden"
                        >
                            <div className="flex flex-col gap-1">
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-mono text-primary uppercase tracking-wider">
                                        {session.risk_level || "Unknown Risk"}
                                    </span>
                                    <Clock className="w-3 h-3 text-textMuted" />
                                </div>
                                <span className="text-sm font-bold text-textMain line-clamp-1">{session.predictions?.disease || "Session"}</span>
                                <span className="text-[11px] text-textMuted line-clamp-1">{session.symptoms}</span>
                            </div>
                            <ChevronRight className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-primary/0 group-hover:text-primary transition-all" />
                        </motion.button>
                    ))
                )}
            </div>
        </div>
    );
}
