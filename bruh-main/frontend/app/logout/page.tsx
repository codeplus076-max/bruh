"use client";

import { useRouter } from "next/navigation";
import { signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useLanguage } from "@/context/LanguageContext";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { motion } from "framer-motion";
import { LogOut, X } from "lucide-react";
import Image from "next/image";

export default function LogoutPage() {
    const router = useRouter();
    const { lang, setLang } = useLanguage();

    const handleLogout = async () => {
        try {
            await signOut(auth);
            router.push("/");
        } catch (error) {
            console.error("Logout failed", error);
        }
    };

    const handleCancel = () => {
        router.back();
    };

    return (
        <main className="min-h-screen relative flex items-center justify-center p-4 bg-hero-glow overflow-hidden">
            <div className="absolute top-8 right-8 flex items-center gap-3 z-50">
                <ThemeToggle />
                <LanguageSwitcher current={lang} onChange={setLang} />
            </div>

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-md w-full glass-panel p-8 space-y-8 z-10"
            >
                <div className="text-center space-y-4">
                    <div className="flex justify-center">
                        <div className="relative w-28 h-28 rounded-full bg-primary/5 overflow-hidden border border-primary/10 p-4 flex items-center justify-center">
                            <Image src="/logo.png" alt="Upchaar Logo" fill className="object-cover" />
                        </div>
                    </div>
                    <div>
                        <h1 className="text-3xl font-heading font-bold text-textMain">Account</h1>
                    </div>
                </div>

                <div className="text-center flex flex-col gap-2">
                    <p className="text-lg text-textMain font-medium leading-relaxed">Do you want to log out of the app?</p>
                </div>

                <div className="flex flex-col gap-4 pt-4">
                    <button
                        onClick={handleCancel}
                        className="w-full py-4 bg-danger/10 hover:bg-danger/20 text-danger border border-danger/30 rounded-xl font-semibold transition-all shadow-[0_0_15px_rgba(225,29,72,0.3)] flex items-center justify-center gap-2 group text-lg"
                    >
                        <X className="w-5 h-5 group-hover:rotate-90 transition-transform" /> No
                    </button>

                    <button
                        onClick={handleLogout}
                        className="w-full py-4 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 rounded-xl font-semibold transition-all shadow-neon flex items-center justify-center gap-2 group text-lg"
                    >
                        <LogOut className="w-5 h-5 group-hover:-translate-x-1 transition-transform" /> Yes
                    </button>
                </div>
            </motion.div>
        </main>
    );
}
