import { motion } from "framer-motion";
import { ActivitySquare, TrendingUp, TrendingDown, ArrowRight, Clock } from "lucide-react";
import { useDashboardStore } from "@/context/dashboardStore";

export function EpisodeContextCard() {
    const { currentSnapshot, diffResult } = useDashboardStore();

    if (!currentSnapshot) return null;

    const ctx = currentSnapshot.episode_context;

    const renderTrendIcon = () => {
        if (ctx.trend.toLowerCase().includes("worsen")) return <TrendingDown className="text-red-500 w-5 h-5" />;
        if (ctx.trend.toLowerCase().includes("improv")) return <TrendingUp className="text-teal-400 w-5 h-5" />;
        return <ArrowRight className="text-gray-400 w-5 h-5" />;
    };

    return (
        <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="sticky top-0 z-20 bg-[#1c2128]/95 backdrop-blur-md border-b border-gray-800 p-4 shadow-md flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
        >
            <div className="flex items-center gap-3">
                <div className="bg-teal-500/20 p-2 rounded-lg">
                    <ActivitySquare className="text-teal-400 w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-lg font-bold text-gray-100">{ctx.title}</h2>
                    <span className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                        <Clock className="w-3 h-3" /> Last Active: {ctx.last_updated}
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-4">
                {/* Status Badge */}
                <div className="px-3 py-1 rounded-full bg-gray-800 border border-gray-700 text-sm font-medium flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${ctx.status.toLowerCase().includes("recover") ? 'bg-green-500' : 'bg-teal-400 animate-pulse'}`}></div>
                    {ctx.status}
                </div>

                {/* Trend Indicator reacting to Diff */}
                <motion.div 
                    animate={diffResult.trend_changed ? { scale: [1, 1.2, 1] } : {}}
                    transition={{ duration: 0.5 }}
                    className="flex items-center gap-2 bg-gray-800/50 px-3 py-1 rounded-full border border-gray-700/50"
                >
                    <span className="text-xs text-gray-400 uppercase tracking-wider">Trend</span>
                    {renderTrendIcon()}
                    <span className="text-sm font-medium text-gray-300 capitalize">{ctx.trend}</span>
                </motion.div>
            </div>
        </motion.div>
    );
}
