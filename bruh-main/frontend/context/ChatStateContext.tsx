"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect } from "react";

export interface LikelyCondition {
    name: string;
    raw_name?: string;
    confidence_band: "High" | "Moderate" | "Low";
    score: number;
    boosted_by_rules?: boolean;
}

export interface Diagnosis {
    // New Dashboard/Triage Schema
    episode_context?: { title: string; status: string; trend: string; last_updated: string; };
    status?: string;
    progression?: { trend: string; day: string; };
    risk?: { level: string; reason: string; };
    actions?: string[];
    alerts?: string[];
    // Hybrid/Legacy fields
    likely_conditions?: LikelyCondition[];
    home_care?: string[];
    diet_advice?: string[];
    when_to_seek_help?: string[];
    safety_disclaimer?: string;
    blacklist_applied?: boolean;
    rules_applied?: string[];
    disease?: string;
    confidence?: string;
    risk_level?: string;
    is_high_risk?: boolean;
    urgency?: string;
    reasoning_summary?: string;
    summary?: string;
    first_aid?: string[];
    home_remedies?: string[];
    medicines?: Array<{ name: string; purpose: string; guidance: string; warning?: string }> | string[];
    routine?: string[];
    when_to_seek_care?: string[];
    warnings?: string[];
    explanation?: string[];
    sessionId?: string;
}

export type Message = { role: "assistant" | "user"; content: string; diagnosis?: Diagnosis };

interface ChatContextType {
    messages: Message[];
    sessionId: string | null;
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    resetChat: (greeting: string) => void;
    loadSession: (msgs: Message[], id: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [sessionId, setSessionId] = useState<string | null>(null);

    useEffect(() => {
        const savedId = localStorage.getItem("upchaar_session_id");
        if (savedId) setSessionId(savedId);
    }, []);

    const resetChat = (greeting: string) => {
        setMessages([{ role: "assistant", content: greeting }]);
        setSessionId(null);
        localStorage.removeItem("upchaar_messages");
        localStorage.removeItem("upchaar_session_id");
    };

    const loadSession = (msgs: Message[], id: string) => {
        setMessages(msgs);
        setSessionId(id);
        localStorage.setItem("upchaar_messages", JSON.stringify(msgs));
        localStorage.setItem("upchaar_session_id", id);
    };

    return (
        <ChatContext.Provider value={{ messages, sessionId, setMessages, resetChat, loadSession }}>
            {children}
        </ChatContext.Provider>
    );
}

export function useChat() {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
}
