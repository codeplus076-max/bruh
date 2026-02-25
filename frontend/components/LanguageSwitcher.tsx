"use client";

import { Language } from "@/lib/translations";

const labels: Record<Language, string> = { en: "EN", hi: "HI", mr: "MR" };

export function LanguageSwitcher({
    current,
    onChange,
}: {
    current: Language;
    onChange: (l: Language) => void;
}) {
    return (
        <div className="flex items-center gap-2 p-1 bg-white rounded-full border border-slate-100 shadow-sm overflow-x-auto no-scrollbar w-full max-w-sm">
            {(["en", "hi", "mr"] as Language[]).map((lang) => (
                <button
                    key={lang}
                    onClick={() => onChange(lang)}
                    className={`relative px-4 py-2 rounded-full text-sm font-medium transition-all flex-1 ${current === lang
                        ? "bg-primary text-white shadow-md"
                        : "text-slate-500 hover:text-slate-800"
                        }`}
                >
                    {labels[lang]}
                </button>
            ))}
        </div>
    );
}
