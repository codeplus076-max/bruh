"use client";

import { Language } from "@/lib/translations";
import { Globe } from "lucide-react";

const labels: Record<Language, string> = { en: "EN", hi: "HI", mr: "MR" };

export function LanguageSwitcher({
    current,
    onChange,
}: {
    current: Language;
    onChange: (l: Language) => void;
}) {
    return (
        <div className="inline-flex items-center gap-1 p-1 bg-surface/80 backdrop-blur-md rounded-full border border-borderDark shadow-glass">
            <div className="pl-3 pr-2 py-1 text-primary/70 flex items-center">
                <Globe className="w-4 h-4" />
            </div>
            <div className="w-px h-5 bg-borderDark/80 mx-1" />
            {(["en", "hi", "mr"] as Language[]).map((lang) => (
                <button
                    key={lang}
                    onClick={() => onChange(lang)}
                    className={`relative px-4 py-1.5 rounded-full text-xs font-mono font-bold tracking-widest transition-all ${current === lang
                            ? "text-background bg-primary shadow-neon"
                            : "text-textMuted hover:text-white"
                        }`}
                >
                    {labels[lang]}
                </button>
            ))}
        </div>
    );
}
