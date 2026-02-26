"use client";

import { useState, Suspense } from "react";
import dynamic from "next/dynamic";
import { motion, Variants } from "framer-motion";
import { VoiceControls } from "@/components/voice/VoiceControls";

// Lazy load heavy components
const ChatInterface = dynamic(() => import("@/components/chat/ChatInterface").then(mod => mod.ChatInterface), {
    loading: () => <div className="p-8 text-center text-primary animate-pulse">Initializing Neural Interface...</div>,
    ssr: false
});

const HospitalMap = dynamic(() => import("@/components/map/HospitalMap").then(mod => mod.HospitalMap), {
    loading: () => <div className="p-8 text-center text-primary animate-pulse">Loading GIS Topology...</div>,
    ssr: false
});
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { Language, translations } from "@/lib/translations";
import { Activity, ShieldAlert, Cpu } from "lucide-react";

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
    const t = translations[lang];

    return (
        <main className="relative min-h-screen text-textMain selection:bg-primary/30 selection:text-primaryVibrant overflow-hidden pb-12">

            {/* Background Atmosphere */}
            <div className="absolute inset-x-0 top-0 h-[600px] bg-hero-glow pointer-events-none opacity-40 mix-blend-screen" />

            <motion.div
                className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 lg:pt-16 space-y-12"
                variants={containerVariants}
                initial="hidden"
                animate="show"
            >
                {/* Header Section */}
                <motion.header
                    variants={itemVariants}
                    className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 pb-6 border-b border-borderDark"
                >
                    <div className="space-y-4 max-w-2xl">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface border border-primary/20 text-primary text-xs font-mono tracking-widest uppercase">
                            <Cpu className="w-3.5 h-3.5" />
                            <span>Bio-Triage Online</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-heading font-bold text-textMain tracking-tight leading-tight dark:mix-blend-plus-lighter">
                            {t.appTitle}
                        </h1>
                        <p className="text-lg text-textMuted font-light max-w-xl leading-relaxed">
                            {t.appSubtitle}
                        </p>
                    </div>

                    <div className="flex flex-col items-start lg:items-end gap-3 shrink-0 pt-4 lg:pt-0">
                        <div className="flex items-center gap-3">
                            <ThemeToggle />
                            <LanguageSwitcher current={lang} onChange={setLang} />
                        </div>
                    </div>
                </motion.header>

                {/* Disclaimer Bar */}
                <motion.section variants={itemVariants} className="relative overflow-hidden rounded-xl bg-danger/10 border border-danger/20 p-4 shadow-glass">
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-danger shadow-[0_0_15px_rgba(255,51,102,0.8)]" />
                    <div className="flex items-start gap-4">
                        <ShieldAlert className="w-5 h-5 text-danger shrink-0 mt-0.5" />
                        <p className="text-sm text-textMain/90 leading-relaxed font-light">
                            {t.disclaimer}
                        </p>
                    </div>
                </motion.section>

                {/* Main Grid Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-start">

                    {/* Chat Side */}
                    <motion.div variants={itemVariants} className="lg:col-span-7 flex flex-col gap-6">
                        <div className="flex items-center gap-3 mb-2">
                            <Activity className="w-5 h-5 text-secondary" />
                            <h2 className="text-xl font-heading text-textMain">{t.diagnosticChat}</h2>
                        </div>

                        <div className="relative z-20 shadow-glass rounded-2xl">
                            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/20 to-secondary/20 rounded-[18px] blur opacity-30" />
                            <Suspense fallback={<div className="h-[400px] bg-surface rounded-2xl animate-pulse" />}>
                                <ChatInterface t={t} lang={lang} input={chatInput} setInput={setChatInput} />
                            </Suspense>
                        </div>

                        {/* Voice Control Node */}
                        <div className="glass-panel p-4">
                            <VoiceControls
                                t={t}
                                currentLang={lang}
                                onTranscription={(text) => setChatInput((prev) => prev ? prev + " " + text : text)}
                            />
                        </div>
                    </motion.div>

                    {/* Map Side */}
                    <motion.div variants={itemVariants} className="lg:col-span-5 flex flex-col gap-6 sticky top-8">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-2 h-2 rounded-full bg-primary shadow-neon" />
                            <h2 className="text-xl font-heading text-textMain">{t.locationServices}</h2>
                        </div>

                        <div className="relative shadow-glass rounded-2xl">
                            <Suspense fallback={<div className="h-[400px] bg-surface rounded-2xl animate-pulse" />}>
                                <HospitalMap t={t} />
                            </Suspense>
                        </div>
                    </motion.div>

                </div>
            </motion.div>
        </main>
    );
}
