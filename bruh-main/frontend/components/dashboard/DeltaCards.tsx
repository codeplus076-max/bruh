import { motion } from "framer-motion";
import { AlertOctagon, HeartPulse, CheckCircle2, AlertTriangle, Pill } from "lucide-react";
import { useDashboardStore } from "@/context/dashboardStore";

export function RiskCard() {
    const { currentSnapshot, diffResult } = useDashboardStore();
    if (!currentSnapshot) return null;

    const { level, reason } = currentSnapshot.risk;
    const isUrgent = level.toUpperCase() === "URGENT";
    const isModerate = level.toUpperCase() === "MODERATE";

    const bgColor = isUrgent ? "bg-red-500/20" : isModerate ? "bg-yellow-500/20" : "bg-teal-500/10";
    const borderColor = isUrgent ? "border-red-500/50" : isModerate ? "border-yellow-500/50" : "border-teal-500/30";
    const textColor = isUrgent ? "text-red-400" : isModerate ? "text-yellow-400" : "text-teal-400";

    return (
        <motion.div 
            animate={diffResult.risk_changed ? { x: [-5, 5, -5, 5, 0], transition: { duration: 0.4 } } : {}}
            className={`p-4 rounded-xl border ${bgColor} ${borderColor}`}
        >
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-widest flex items-center gap-2">
                    <HeartPulse className="w-4 h-4" /> Risk Assessment
                </h3>
                <span className={`text-sm font-bold px-3 py-1 rounded-full ${isUrgent ? 'bg-red-500 text-white' : 'bg-gray-800 text-gray-200'}`}>
                    {level}
                </span>
            </div>
            <p className={`text-sm ${textColor} font-medium leading-relaxed`}>{reason}</p>
        </motion.div>
    );
}

export function AlertsCard() {
    const { currentSnapshot } = useDashboardStore();
    if (!currentSnapshot || !currentSnapshot.alerts || currentSnapshot.alerts.length === 0) return null;

    // Alerts represent red flags, rendered prominently but not aggressively
    return (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/5">
            <h3 className="text-sm font-semibold text-rose-400 uppercase tracking-widest flex items-center gap-2 mb-3">
                <AlertOctagon className="w-4 h-4" /> Watch Out For
            </h3>
            <ul className="space-y-2">
                {currentSnapshot.alerts.map((alert, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
                        <span>{alert}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export function ActionCard() {
    const { currentSnapshot, diffResult } = useDashboardStore();
    if (!currentSnapshot) return null;

    return (
        <motion.div 
            animate={diffResult.actions_changed ? { opacity: [0.5, 1] } : {}}
            className="grid md:grid-cols-2 gap-4"
        >
            {currentSnapshot.actions.length > 0 && (
                <div className="p-5 rounded-xl border border-gray-800 bg-[#15191e]">
                    <h3 className="text-sm font-semibold text-teal-400 uppercase tracking-widest flex items-center gap-2 mb-4">
                        <CheckCircle2 className="w-4 h-4" /> What To Do Now
                    </h3>
                    <ul className="space-y-3">
                        {currentSnapshot.actions.map((act, idx) => (
                            <li key={idx} className="text-sm text-gray-300 border-b border-gray-800/50 pb-2 last:border-0">{act}</li>
                        ))}
                    </ul>
                </div>
            )}

            {currentSnapshot.medicines.length > 0 && (
                <div className="p-5 rounded-xl border border-gray-800 bg-[#15191e]">
                    <h3 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest flex items-center gap-2 mb-4">
                        <Pill className="w-4 h-4" /> Safe Relief Options
                    </h3>
                    <ul className="space-y-3">
                        {currentSnapshot.medicines.map((med, idx) => (
                            <li key={idx} className="text-sm text-gray-300 border-b border-gray-800/50 pb-2 last:border-0">{med}</li>
                        ))}
                    </ul>
                </div>
            )}
        </motion.div>
    );
}

export function DoctorProgressionCard() {
    const { currentSnapshot } = useDashboardStore();
    if (!currentSnapshot) return null;

    return (
        <div className="p-5 rounded-xl border border-gray-800 bg-[#15191e]">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-3">Clinical Evaluation Context</h3>
            <div className="text-sm text-gray-300 leading-relaxed font-mono bg-black/40 p-3 rounded border border-gray-800">
                {currentSnapshot.status}
            </div>
            <div className="mt-4 flex items-center justify-between text-xs text-gray-500 font-mono">
                <span>Severity Index: {currentSnapshot.progression.day}</span>
                <span>Calculated Trend Map: {currentSnapshot.progression.trend}</span>
            </div>
        </div>
    );
}
