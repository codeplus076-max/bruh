import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Stethoscope, FileText } from "lucide-react";
import { RiskCard, ActionCard, AlertsCard, DoctorProgressionCard } from "./DeltaCards";
import { useDashboardStore } from "@/context/dashboardStore";

type ViewMode = "PATIENT" | "DOCTOR" | "SUMMARY";

export function MultiViewTabs() {
    const [view, setView] = useState<ViewMode>("PATIENT");
    const { currentSnapshot } = useDashboardStore();

    if (!currentSnapshot) return null;

    return (
        <div className="w-full max-w-4xl mx-auto flex flex-col gap-6">
            {/* View Controller */}
            <div className="flex items-center justify-center gap-2 p-1 bg-gray-900 rounded-lg w-fit mx-auto border border-gray-800">
                <button 
                    onClick={() => setView("PATIENT")}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${view === "PATIENT" ? "bg-gray-800 text-teal-400" : "text-gray-400 hover:text-gray-200"}`}
                >
                    <User className="w-4 h-4" /> Patient View
                </button>
                <button 
                    onClick={() => setView("DOCTOR")}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${view === "DOCTOR" ? "bg-gray-800 text-indigo-400" : "text-gray-400 hover:text-gray-200"}`}
                >
                    <Stethoscope className="w-4 h-4" /> Doctor View
                </button>
                <button 
                    onClick={() => setView("SUMMARY")}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${view === "SUMMARY" ? "bg-gray-800 text-yellow-400" : "text-gray-400 hover:text-gray-200"}`}
                >
                    <FileText className="w-4 h-4" /> Summary
                </button>
            </div>

            {/* Content Area rendering stateless children matching the view natively */}
            <AnimatePresence mode="wait">
                <motion.div 
                    key={view} 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    className="flex flex-col gap-4"
                >
                    {view === "PATIENT" && (
                        <>
                            <RiskCard />
                            <ActionCard />
                            <AlertsCard />
                        </>
                    )}

                    {view === "DOCTOR" && (
                        <>
                            <RiskCard />
                            <DoctorProgressionCard />
                            <AlertsCard />
                        </>
                    )}

                    {view === "SUMMARY" && (
                        <div className="p-6 rounded-xl border border-gray-800 bg-[#15191e]">
                            <h3 className="text-lg font-bold text-gray-200 mb-2">{currentSnapshot.episode_context.title}</h3>
                            <p className="text-gray-400 text-sm leading-relaxed mb-4">
                                {currentSnapshot.status}
                            </p>
                            <div className="flex gap-4">
                                <span className="text-xs bg-gray-800 px-3 py-1 rounded text-gray-300">Trend: {currentSnapshot.progression.trend}</span>
                                <span className="text-xs bg-gray-800 px-3 py-1 rounded text-gray-300">Risk: {currentSnapshot.risk.level}</span>
                            </div>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
