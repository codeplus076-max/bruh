"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect } from "react";

type Message = { role: "assistant" | "user"; content: string; diagnosis?: any };

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
