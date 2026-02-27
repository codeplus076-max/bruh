"use client";

import { useEffect, useState } from "react";
import { Plus, MessageSquare, Clock, ChevronLeft, ChevronRight, LogOut } from "lucide-react";
import { useChat } from "@/context/ChatStateContext";
import { useAuth } from "@/context/AuthContext";
import { useLanguage } from "@/context/LanguageContext";
import { motion, AnimatePresence } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function Sidebar() {
    const { messages, sessionId, loadSession, resetChat } = useChat();
    const { user } = useAuth();
    const { t } = useLanguage();
    const [history, setHistory] = useState<any[]>([]);
    const [isOpen, setIsOpen] = useState(true);
    const [loading, setLoading] = useState(false);

    const fetchHistory = async () => {
        if (!user) return;
        setLoading(true);
        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_URL}/sessions/history`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setHistory(data);
            }
        } catch (err) {
            console.error("Failed to fetch history", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) fetchHistory();
    }, [user, messages.length]); // Refresh when new messages added

    const openSession = async (id: string) => {
        if (!user) return;
        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_URL}/sessions/${id}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                loadSession(data.messages, data.sessionId);
            }
        } catch (err) {
            console.error("Failed to load session", err);
        }
    };

    const handleNewChat = () => {
        resetChat(t.chatGreeting);
    };

    return (
        <motion.div
            initial={false}
            animate={{ width: isOpen ? 280 : 80 }}
            className="h-full bg-surface border-r border-borderDark flex flex-col relative transition-all duration-300 z-30 shadow-2xl"
        >
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="absolute -right-3 top-10 bg-primary text-white p-1 rounded-full shadow-lg z-40 hover:scale-110 transition-transform"
            >
                {isOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
            </button>

            {/* New Chat Button */}
            <div className="p-4">
                <button
                    onClick={handleNewChat}
                    className={`w-full flex items-center gap-3 px-4 py-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 rounded-xl transition-all font-bold shadow-neon group ${!isOpen && "justify-center"}`}
                >
                    <Plus className="group-hover:rotate-90 transition-transform" size={20} />
                    {isOpen && <span>New Chat</span>}
                </button>
            </div>

            {/* History List */}
            <div className="flex-1 overflow-y-auto px-3 space-y-2 py-2 custom-scrollbar">
                {isOpen && <p className="px-2 text-[10px] text-textMuted uppercase tracking-widest font-black opacity-50 mb-4">Previous Chats</p>}

                {loading ? (
                    <div className="flex justify-center p-4">
                        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    history.map((chat) => (
                        <button
                            key={chat.sessionId}
                            onClick={() => openSession(chat.sessionId)}
                            className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all hover:bg-surfaceHighlight group ${sessionId === chat.sessionId ? "bg-surfaceHighlight border border-primary/30" : "border border-transparent"}`}
                        >
                            <MessageSquare size={18} className={sessionId === chat.sessionId ? "text-primary" : "text-textMuted"} />
                            {isOpen && (
                                <div className="flex-1 overflow-hidden">
                                    <p className={`text-xs truncate font-medium ${sessionId === chat.sessionId ? "text-textMain" : "text-textMuted"}`}>
                                        {chat.title}
                                    </p>
                                    <p className="text-[10px] text-textMuted/60 flex items-center gap-1 mt-0.5">
                                        <Clock size={10} />
                                        {new Date(chat.createdAt * 1000).toLocaleDateString()}
                                    </p>
                                </div>
                            )}
                        </button>
                    ))
                )}
            </div>

            {/* User Info / Logout Placeholder */}
            {user && isOpen && (
                <div className="p-4 border-t border-borderDark bg-surfaceHighlight/30">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-xs">
                            {user.displayName?.[0] || "U"}
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <p className="text-xs font-bold text-textMain truncate">{user.displayName || "User"}</p>
                            <p className="text-[10px] text-textMuted truncate">{user.email}</p>
                        </div>
                    </div>
                </div>
            )}
        </motion.div>
    );
}
