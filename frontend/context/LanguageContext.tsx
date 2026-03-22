"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { Language, translations, Translations } from "@/lib/translations";
import { useAuth } from "@/context/AuthContext";

interface LanguageContextType {
    lang: Language;
    setLang: (lang: Language) => void;
    t: Translations;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
    const [lang, setLangState] = useState<Language>("en");
    const { userProfile } = useAuth();

    useEffect(() => {
        // Priority 1: Firebase user profile (cross-device sync)
        const profileLang = userProfile?.language as Language;
        if (profileLang && ["en", "hi", "mr"].includes(profileLang)) {
            setLangState(profileLang);
            return;
        }
        // Priority 2: localStorage (single-device persistence)
        const saved = localStorage.getItem("upchaar-lang") as Language;
        if (saved && ["en", "hi", "mr"].includes(saved)) {
            setLangState(saved);
        }
    }, [userProfile]);

    const setLang = (newLang: Language) => {
        setLangState(newLang);
        localStorage.setItem("upchaar-lang", newLang);
    };

    const value = {
        lang,
        setLang,
        t: translations[lang],
    };

    return (
        <LanguageContext.Provider value={value}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage() {
    const context = useContext(LanguageContext);
    if (context === undefined) {
        throw new Error("useLanguage must be used within a LanguageProvider");
    }
    return context;
}
