"use client";

import { useState, Suspense, useEffect } from "react";
import dynamic from "next/dynamic";
import { motion, Variants } from "framer-motion";
import { useRouter } from "next/navigation";
import { VoiceControls } from "@/components/voice/VoiceControls";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useLanguage } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";
import { Activity, ShieldAlert, Cpu, MapPin, LogOut } from "lucide-react";
import Image from "next/image";

import { ChatHistory } from "@/components/chat/ChatHistory";

// Lazy load heavy components
const ChatInterface = dynamic(() => import("@/components/chat/ChatInterface").then(mod => mod.ChatInterface), {
    loading: () => <div className="p-8 text-center text-primary animate-pulse">Initializing Neural Interface...</div>,
    ssr: false
});

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

export default function ChatPage() {
    const { lang, t } = useLanguage();
    const { user, signOut } = useAuth();
    const router = useRouter();
    const [chatInput, setChatInput] = useState("");

    // Redirect to login if not authenticated
    useEffect(() => {
        if (!user) {
            router.push("/");
        }
    }, [user, router]);

    if (!user) return null;

    return (
        <main className="relative min-h-screen text-textMain selection:bg-primary/30 selection:text-primaryVibrant overflow-hidden pb-12">
            <div className="absolute inset-x-0 top-0 h-[600px] bg-hero-glow pointer-events-none opacity-40 mix-blend-screen" />

            <motion.div
                className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 lg:pt-12 space-y-8"
                variants={containerVariants}
                initial="hidden"
                animate="show"
            >
                {/* Navbar */}
                <motion.nav variants={itemVariants} className="flex items-center justify-between bg-surface/40 backdrop-blur-xl border border-borderDark rounded-2xl px-6 py-3 shadow-glass">
                    <div className="flex items-center gap-4">
                        <div className="relative w-10 h-10 rounded-full overflow-hidden bg-primary/10 border border-primary/20">
                            <Image src="/logo.png" alt="Upchaar Logo" fill className="object-cover" />
                        </div>
                        <div className="flex flex-col">
                            <span className="font-heading font-bold text-base tracking-tight text-textMain leading-none">UPCHAAR</span>
                            <span className="text-[10px] text-primary font-mono uppercase tracking-widest opacity-80 mt-1">ai rural triage</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <ThemeToggle />
                        <LanguageSwitcher />
                        <div className="w-px h-6 bg-borderDark hidden sm:block" />
                        <button
                            onClick={() => signOut()}
                            className="p-2 hover:bg-danger/10 text-textMuted hover:text-danger rounded-xl transition-all"
                            title="Sign Out"
                        >
                            <LogOut className="w-5 h-5" />
                        </button>
                    </div>
                </motion.nav>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                    {/* Sidebar Area (Left/History) */}
                    <div className="hidden lg:block lg:col-span-3 space-y-6 sticky top-12 h-[calc(100vh-100px)]">
                        <motion.div variants={itemVariants} className="h-full">
                            <ChatHistory />
                        </motion.div>
                    </div>

                    {/* Main Chat Area */}
                    <div className="lg:col-span-9 space-y-6">
                        <motion.header variants={itemVariants} className="space-y-4">
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface border border-primary/20 text-primary text-[10px] font-mono tracking-widest uppercase">
                                <Cpu className="w-3 h-3" />
                                <span>Upchaar v2.0 Online</span>
                            </div>
                            <h1 className="text-3xl md:text-4xl font-heading font-bold text-textMain leading-tight">
                                {t.diagnosticChat}
                            </h1>
                        </motion.header>

                        <motion.section variants={itemVariants} className="relative overflow-hidden rounded-xl bg-danger/5 border border-danger/20 p-4">
                            <div className="flex items-start gap-4">
                                <ShieldAlert className="w-4 h-4 text-danger mt-1 shrink-0" />
                                <p className="text-[12px] text-textMuted leading-relaxed">
                                    {t.disclaimer}
                                </p>
                            </div>
                        </motion.section>

                        <motion.div variants={itemVariants} className="relative z-20 shadow-2xl rounded-2xl overflow-hidden border border-borderDark bg-surface">
                            <Suspense fallback={<div className="h-[500px] bg-surface rounded-2xl animate-pulse flex items-center justify-center text-primary/40">Initializing Neural Engine...</div>}>
                                <ChatInterface input={chatInput} setInput={setChatInput} />
                            </Suspense>
                        </motion.div>

                        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4">
                            <div className="flex-1 glass-panel p-4">
                                <VoiceControls
                                    onTranscription={(text) => setChatInput((prev) => prev ? prev + " " + text : text)}
                                />
                            </div>
                            <button
                                onClick={() => router.push("/hospitals")}
                                className="sm:w-64 flex items-center justify-center gap-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-2xl py-6 font-heading font-bold shadow-neon transition-all group"
                            >
                                <MapPin className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                {t.hospitalFind}
                            </button>
                        </motion.div>
                    </div>
                </div>
            </motion.div>
        </main>
    );
}
