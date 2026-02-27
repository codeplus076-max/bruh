"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect } from "react";

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
