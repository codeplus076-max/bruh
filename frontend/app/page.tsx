"use client";

import { useState } from "react";
import { motion, Variants } from "framer-motion";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { VoiceControls } from "@/components/voice/VoiceControls";
import { HospitalMap } from "@/components/map/HospitalMap";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Language, translations } from "@/lib/translations";
import { BriefcaseMedical, Moon, User, Activity } from "lucide-react";

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.15, delayChildren: 0.1 }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: {
        opacity: 1,
        y: 0,
        transition: { type: "spring" as const, stiffness: 80, damping: 15 }
    }
};

export default function Home() {
    const [lang, setLang] = useState<Language>("en");
    const [chatInput, setChatInput] = useState("");
    const [isAnalyzed, setIsAnalyzed] = useState(false);
    const t = translations[lang];

    return (
        <main className="min-h-screen bg-slate-100 text-slate-900 pb-12 font-sans selection:bg-primary/30 flex justify-center w-full">
            <div className="w-full max-w-md bg-slate-50 min-h-screen shadow-2xl relative overflow-hidden flex flex-col pt-6 pb-20 sm:rounded-[40px] sm:my-8 sm:min-h-[850px] border-4 border-slate-200">

                <motion.div
                    className="relative z-10 w-full flex flex-col space-y-8"
                    variants={containerVariants}
                    initial="hidden"
                    animate="show"
                >
                    {/* Header */}
                    <div className="px-6 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-11 h-11 rounded-full bg-primary flex items-center justify-center text-white shadow-md">
                                <BriefcaseMedical className="w-5 h-5" />
                            </div>
                            <div className="flex flex-col">
                                <h1 className="text-xl font-bold text-slate-800 leading-none mb-1 tracking-tight">TriageAI</h1>
                                <p className="text-xs text-slate-500 font-medium tracking-wide">Rural Health Assistant</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button className="w-8 h-8 rounded-full bg-white shadow-sm border border-slate-100 flex items-center justify-center text-slate-500">
                                <Moon className="w-4 h-4" />
                            </button>
                            <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center overflow-hidden border border-orange-200">
                                <User className="w-5 h-5 text-orange-400 mt-1" />
                            </div>
                        </div>
                    </div>

                    {/* Language Switcher */}
                    <div className="px-6 flex justify-center">
                        <LanguageSwitcher current={lang} onChange={setLang} />
                    </div>

                    {/* Main Content Area */}
                    <div className="flex-1 px-4 space-y-6 flex flex-col">

                        {/* Voice Node */}
                        <div className="w-full relative z-10 flex flex-col items-center">
                            <VoiceControls
                                t={t}
                                currentLang={lang}
                                onTranscription={(text) => {
                                    setChatInput((prev) => prev ? prev + " " + text : text);
                                    setIsAnalyzed(false);
                                }}
                            />
                        </div>

                        {/* Live Transcript Card */}
                        {chatInput && !isAnalyzed && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                className="w-full bg-white rounded-3xl p-6 shadow-card border border-slate-100 mx-auto max-w-[95%]"
                            >
                                <div className="flex items-center justify-between mb-4">
                                    <span className="text-xs font-bold text-slate-400 tracking-wider uppercase">Live Transcript</span>
                                    <span className="w-2 h-2 rounded-full bg-danger animate-pulse"></span>
                                </div>
                                <p className="text-lg text-slate-800 leading-relaxed font-medium mb-6">
                                    "{chatInput}"
                                </p>
                                <button
                                    onClick={() => setIsAnalyzed(true)}
                                    className="w-full py-4 bg-primary hover:bg-primaryVibrant text-white rounded-2xl font-bold text-[15px] shadow-md transition-colors flex items-center justify-center gap-2"
                                >
                                    <Activity className="w-5 h-5" />
                                    Analyze Symptoms
                                </button>
                            </motion.div>
                        )}

                        {/* Interactive Chat and Map Section (Revealed automatically or manually) */}
                        <div className={`w-full transition-opacity duration-500 ${isAnalyzed ? 'opacity-100' : 'opacity-40 pointer-events-none hidden'}`}>
                            <div className="space-y-6 px-2">
                                <div className="glass-panel overflow-hidden border-0">
                                    <ChatInterface t={t} lang={lang} input={chatInput} setInput={setChatInput} />
                                </div>

                                <div className="glass-panel p-4 pb-0 bg-white">
                                    <p className="font-bold text-slate-700 mb-3 px-2 flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-primary" />
                                        {t.locationServices}
                                    </p>
                                    <HospitalMap t={t} />
                                </div>
                            </div>
                        </div>

                    </div>
                </motion.div>
            </div>
        </main>
    );
}
