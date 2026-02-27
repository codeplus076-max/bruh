"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

type Message = { role: "assistant" | "user"; content: string; diagnosis?: any };

interface ChatContextType {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    resetChat: (greeting: string) => void;
    loadSession: (msgs: Message[]) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
    const [messages, setMessages] = useState<Message[]>([]);

    const resetChat = (greeting: string) => {
        setMessages([{ role: "assistant", content: greeting }]);
        localStorage.removeItem("upchaar_messages");
    };

    const loadSession = (msgs: Message[]) => {
        setMessages(msgs);
        localStorage.setItem("upchaar_messages", JSON.stringify(msgs));
    };

    return (
        <ChatContext.Provider value={{ messages, setMessages, resetChat, loadSession }}>
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
