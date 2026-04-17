"use client";

import { Activity, Pill, ShieldAlert, Info } from "lucide-react";
import { motion } from "framer-motion";
import { Diagnosis } from "@/context/ChatStateContext";

// Reusable card for clinical sections
const DataSection = ({ title, icon: Icon, items, themeClass, iconColorClass, delay }: { title: string, icon: React.ElementType, items: string[], themeClass: string, iconColorClass: string, delay: number }) => {
    if (!items || items.length === 0) return null;
    return (
        <motion.div 
            initial={{ opacity: 0, y: 15 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ delay, duration: 0.4, ease: "easeOut" }}
            className={`p-5 rounded-2xl border bg-white/5 backdrop-blur-md ${themeClass}`}
        >
            <div className="flex items-center gap-2.5 mb-3">
                <div className={`p-2 rounded-lg bg-surfaceDark/50 border border-white/5 shadow-inner flex items-center justify-center ${iconColorClass}`}>
                    <Icon className="w-4 h-4" />
                </div>
                <h4 className="text-[13px] font-bold uppercase tracking-widest text-white/80">{title}</h4>
            </div>
            <ul className="space-y-3">
                {items.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                        <div className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${iconColorClass.replace('text-', 'bg-')}`} />
                        <span className="text-[14px] leading-relaxed text-white/70 font-medium">{item}</span>
                    </li>
                ))}
            </ul>
        </motion.div>
    );
};

export function TriageCard({ diagnosis }: { diagnosis: Diagnosis | null | undefined }) {
    if (!diagnosis || Object.keys(diagnosis).length === 0) return null;

    const conditionName = diagnosis.disease || diagnosis.status || diagnosis.episode_context?.title || "Symptom Assessment";

    // Ensure arrays exist
    const actions      = diagnosis.actions || diagnosis.home_care || [];
    const alerts       = diagnosis.alerts || diagnosis.warnings || [];
    const medicinesRaw = diagnosis.medicines || [];
    const medicines    = medicinesRaw.map(m => typeof m === 'string' ? m : `${m.name} (${m.purpose})`);

    // Styling logic for header background
    const isWarning  = (alerts.length > 0) || (actions.length > 0);



    return (
        <motion.div 
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-3xl flex flex-col gap-5 overflow-hidden"
        >
            {/* ── Header Card ── */}
            <div className="relative overflow-hidden bg-gradient-to-br from-surface to-[#0d1627] rounded-3xl border border-white/10 shadow-2xl p-6 md:p-8">
                {/* Subtle background glow based on alerts */}
                <div className={`absolute top-0 right-0 w-64 h-64 blur-[100px] rounded-full opacity-20 pointer-events-none ${isWarning ? 'bg-amber-500' : 'bg-emerald-500'}`} />

                <div className="relative z-10 flex flex-col md:flex-row md:items-start justify-between gap-6">
                    <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[10px] font-bold tracking-[0.2em] uppercase text-primary">Health Assessment</span>
                        </div>
                        <h3 className="text-3xl md:text-4xl font-extrabold text-white font-heading tracking-tight leading-tight">
                            {conditionName}
                        </h3>
                    </div>

                    {/* Meta Pillars removed as per user request */}
                </div>
            </div>

            {/* ── Clinical Sections Grid ── */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <DataSection 
                    delay={0.1}
                    title="Immediate Clinical Steps" 
                    icon={Activity} 
                    items={actions} 
                    themeClass="hover:border-teal-500/30 transition-colors"
                    iconColorClass="text-teal-400"
                />

                <DataSection 
                    delay={0.2}
                    title="Safe Relief Guidance" 
                    icon={Pill} 
                    items={medicines} 
                    themeClass="hover:border-blue-500/30 transition-colors"
                    iconColorClass="text-blue-400"
                />
                
                {/* Red Flags spans full width at the bottom if it maps nicely */}
                {alerts.length > 0 && (
                    <div className="md:col-span-2">
                        <DataSection 
                            delay={0.3}
                            title="Watch Out For (Red Flags)" 
                            icon={ShieldAlert} 
                            items={alerts} 
                            themeClass="bg-rose-950/10 border-rose-500/20 hover:border-rose-500/40 transition-colors"
                            iconColorClass="text-rose-400"
                        />
                    </div>
                )}
            </div>
            
            {/* Subtle Disclaimer Footer */}
            <p className="text-center text-[11px] text-white/30 tracking-wide mt-2 mx-auto flex items-center justify-center gap-1.5 max-w-lg">
                <Info className="w-3.5 h-3.5" /> AI triage is for informational purposes. If symptoms worsen rapidly, consult a doctor immediately.
            </p>
        </motion.div>
    );
}
