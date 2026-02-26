"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    updateProfile
} from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useLanguage } from "@/context/LanguageContext";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { motion } from "framer-motion";
import { LogIn, UserPlus, HeartPulse, Mail, Lock, User } from "lucide-react";
import Image from "next/image";

export default function LoginPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [username, setUsername] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const router = useRouter();
    const { t, lang, setLang } = useLanguage();

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            if (isLogin) {
                await signInWithEmailAndPassword(auth, email, password);
            } else {
                const userCredential = await createUserWithEmailAndPassword(auth, email, password);
                await updateProfile(userCredential.user, { displayName: username });
            }
            router.push("/chat");
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
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
                        <div className="relative w-24 h-24 rounded-full bg-primary/10 overflow-hidden border border-primary/20 p-2">
                            <Image src="/logo.png" alt="Upchaar Logo" fill className="object-contain p-2" />
                        </div>
                    </div>
                    <div>
                        <h1 className="text-3xl font-heading font-bold text-textMain">{t.appTitle}</h1>
                        <p className="text-textMuted text-sm font-light uppercase tracking-widest mt-1">Health Rural Assistant</p>
                    </div>
                </div>

                <form onSubmit={handleAuth} className="space-y-4">
                    {!isLogin && (
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                            <input
                                type="text"
                                placeholder="Username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-surface border border-borderDark rounded-xl px-10 py-3 text-sm focus:border-primary/50 transition-all outline-none"
                                required
                            />
                        </div>
                    )}
                    <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                        <input
                            type="email"
                            placeholder="Email address"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-surface border border-borderDark rounded-xl px-10 py-3 text-sm focus:border-primary/50 transition-all outline-none"
                            required
                        />
                    </div>
                    <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-surface border border-borderDark rounded-xl px-10 py-3 text-sm focus:border-primary/50 transition-all outline-none"
                            required
                        />
                    </div>

                    {error && <p className="text-danger text-xs text-center font-medium bg-danger/10 p-2 rounded-lg border border-danger/20">{error}</p>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 rounded-xl font-semibold transition-all shadow-neon flex items-center justify-center gap-2 group disabled:opacity-50"
                    >
                        {loading ? "Processing..." : isLogin ? <><LogIn className="w-4 h-4" /> Sign In</> : <><UserPlus className="w-4 h-4" /> Create Account</>}
                    </button>
                </form>

                <div className="text-center">
                    <button
                        onClick={() => setIsLogin(!isLogin)}
                        className="text-textMuted text-xs hover:text-primary transition-colors font-mono uppercase tracking-widest"
                    >
                        {isLogin ? "Need an account? Sign Up" : "Already have an account? Login"}
                    </button>
                </div>

                <p className="text-[10px] text-textMuted/60 leading-tight text-center italic">
                    {t.disclaimer.split('.')[0]}.
                </p>
            </motion.div>
        </main>
    );
}
