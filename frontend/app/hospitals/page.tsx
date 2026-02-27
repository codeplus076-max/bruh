"use client";

import { Suspense, useEffect } from "react";
import dynamic from "next/dynamic";
import { motion, Variants } from "framer-motion";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ArrowLeft, Map as MapIcon, LogOut, Navigation2 } from "lucide-react";
import Image from "next/image";

const HospitalMap = dynamic(() => import("@/components/map/HospitalMap").then(mod => mod.HospitalMap), {
    loading: () => <div className="p-8 text-center text-primary animate-pulse flex flex-col items-center justify-center gap-4 h-[600px] bg-surface rounded-2xl">
        <MapIcon className="w-10 h-10 text-primary/20" />
        Initializing GIS Topology...
    </div>,
    ssr: false
});

const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.1, delayChildren: 0.1 }
    }
};

const itemVariants: Variants = {
    hidden: { opacity: 0, scale: 0.98 },
    show: {
        opacity: 1,
        scale: 1,
        transition: { type: "spring" as const, stiffness: 80, damping: 15 }
    }
};

export default function HospitalsPage() {
    const { t } = useLanguage();
    const { user, signOut } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!user) {
            router.push("/");
        }
    }, [user, router]);

    if (!user) return null;

    return (
        <main className="relative min-h-screen text-textMain selection:bg-primary/30 selection:text-primaryVibrant overflow-hidden pb-12">
            <div className="absolute inset-x-0 top-0 h-[600px] bg-hero-glow pointer-events-none opacity-20 mix-blend-screen" />

            <motion.div
                className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-8"
                variants={containerVariants}
                initial="hidden"
                animate="show"
            >
                {/* Navbar */}
                <motion.nav variants={itemVariants} className="flex items-center justify-between bg-surface/40 backdrop-blur-xl border border-borderDark rounded-2xl px-6 py-3 shadow-glass">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => router.push("/chat")}
                            className="p-3 hover:bg-primary/10 text-textMuted hover:text-primary rounded-xl transition-all mr-2 flex items-center justify-center min-w-[44px] min-h-[44px]"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="relative w-10 h-10 rounded-full overflow-hidden bg-primary/10 border border-primary/20">
                            <Image src="/logo.png" alt="Upchaar Logo" fill className="object-cover" />
                        </div>
                        <div className="flex flex-col">
                            <span className="font-heading font-bold text-base tracking-tight text-textMain leading-none">UPCHAAR</span>
                            <span className="text-[10px] text-primary font-mono uppercase tracking-widest opacity-80 mt-1">ai rural triage</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden sm:flex items-center gap-3 mr-4">
                            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                            <span className="text-[10px] font-mono tracking-[0.2em] uppercase text-primary">Live GIS Node</span>
                        </div>
                        <LanguageSwitcher />
                        <ThemeToggle />
                        <div className="w-px h-6 bg-borderDark hidden sm:block" />
                        <a
                            href="/logout"
                            className="p-3 hover:bg-danger/10 text-textMuted hover:text-danger rounded-xl transition-all flex items-center justify-center min-w-[44px] min-h-[44px]"
                            title="Sign Out"
                        >
                            <LogOut className="w-5 h-5" />
                        </a>
                    </div>
                </motion.nav>

                <div className="grid grid-cols-1 gap-8">
                    <motion.header variants={itemVariants} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h1 className="text-3xl font-heading font-bold text-textMain flex items-center gap-3">
                                <Navigation2 className="w-8 h-8 text-primary" />
                                {t.hospitalTitle}
                            </h1>
                            <p className="text-textMuted mt-1 font-light tracking-wide">{t.hospitalSubtitle || "Geolocation-aware health facility finder"}</p>
                        </div>
                    </motion.header>

                    <motion.div variants={itemVariants} className="relative z-20 shadow-2xl rounded-2xl overflow-hidden border border-borderDark">
                        <Suspense fallback={<div className="h-[600px] bg-surface flex items-center justify-center animate-pulse">GIS Stream Synchronizing...</div>}>
                            <HospitalMap t={t} />
                        </Suspense>
                    </motion.div>
                </div>
            </motion.div>
        </main>
    );
}
