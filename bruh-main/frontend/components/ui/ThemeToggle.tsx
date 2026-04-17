"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { motion } from "framer-motion";

export function ThemeToggle() {
    const { theme, setTheme } = useTheme();
    // Avoid hydration mismatch by only rendering after mount
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        return <div className="w-10 h-10" aria-hidden="true" />; // placeholder to prevent layout shift
    }

    const isDark = theme === "dark";

    return (
        <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className="relative inline-flex items-center justify-center w-10 h-10 rounded-full bg-surface border border-borderDark hover:bg-surfaceHighlight transition-colors group cursor-pointer shadow-glass"
            aria-label="Toggle theme"
        >
            <div className="relative w-5 h-5 flex items-center justify-center">
                <motion.div
                    initial={false}
                    animate={{
                        scale: isDark ? 1 : 0,
                        rotate: isDark ? 0 : 90,
                        opacity: isDark ? 1 : 0
                    }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                    className="absolute text-primary"
                >
                    <Moon size={20} strokeWidth={2} />
                </motion.div>

                <motion.div
                    initial={false}
                    animate={{
                        scale: isDark ? 0 : 1,
                        rotate: isDark ? -90 : 0,
                        opacity: isDark ? 0 : 1
                    }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                    className="absolute text-warning"
                >
                    <Sun size={20} strokeWidth={2} />
                </motion.div>
            </div>

            {/* Glow effect on hover */}
            <div className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 bg-primary/10 transition-opacity blur-md" />
        </button>
    );
}
