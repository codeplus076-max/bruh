import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, ArrowRight, MessageSquare } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { fetchUserEpisodes, fetchEpisodeMessages } from "@/lib/firestoreOperations";
import { useDashboardStore } from "@/context/dashboardStore";

import { ParsedSnapshot } from "@/lib/dashboardUtils";

interface Episode {
    id: string;
    title?: string;
    status?: string;
    trend?: string;
}

interface DashboardMessage {
    id: string;
    role: string;
    content: string;
    parsed_snapshot?: ParsedSnapshot;
}

export function ChatHistory() {
    const { user } = useAuth();
    const { currentEpisodeId, setCurrentEpisode, loadEpisodeState } = useDashboardStore();
    const [episodes, setEpisodes] = useState<Episode[]>([]);

    useEffect(() => {
        if (!user) return;
        fetchUserEpisodes(user.uid).then(setEpisodes);
        // Assuming a live listener or manual polling for production, 
        // for now fetch is completely fine on mount
    }, [user]); // Only refetch the list when the logged-in user changes

    const handleSelect = async (m: Episode) => {
        setCurrentEpisode(m.id);
        
        // Fetch the messages heavily caching the latest snapshot 
        // Then we load that into Zustand without firing aggressive diff animations
        const messages = await fetchEpisodeMessages(m.id) as DashboardMessage[];
        if (messages.length > 0) {
            const lastMsg = [...messages].reverse().find(x => x.role === "assistant" && x.parsed_snapshot);
            if (lastMsg && lastMsg.parsed_snapshot) {
                loadEpisodeState(lastMsg.parsed_snapshot);
            }
        }
    };

    const renderTrendIcon = (trend?: string) => {
        if (!trend) return <ArrowRight className="w-3 h-3 flex-shrink-0" />;
        if (trend.toLowerCase().includes("worsen")) return <TrendingDown className="text-red-500 w-3 h-3 flex-shrink-0" />;
        if (trend.toLowerCase().includes("improv")) return <TrendingUp className="text-teal-400 w-3 h-3 flex-shrink-0" />;
        return <ArrowRight className="text-gray-400 w-3 h-3 flex-shrink-0" />;
    };

    if (episodes.length === 0) {
        return (
            <div className="text-center p-6 text-gray-500 font-medium text-sm flex flex-col items-center gap-3">
                <MessageSquare className="w-6 h-6" />
                <p>No active Health Episodes tracked yet.</p>
            </div>
        );
    }

    return (
        <div className="space-y-1 p-3">
            <h3 className="text-xs uppercase tracking-widest text-gray-500 font-semibold mb-3 ml-2">Health Episodes</h3>
            {episodes.map((ep) => (
                <button
                    key={ep.id}
                    onClick={() => handleSelect(ep)}
                    className={`w-full text-left p-3 rounded-lg flex flex-col gap-2 transition-all group border ${
                        currentEpisodeId === ep.id
                            ? "bg-teal-500/10 border-teal-500/30"
                            : "bg-transparent border-transparent hover:bg-gray-800"
                    }`}
                >
                    <div className="flex items-center justify-between pointer-events-none">
                        <span className={`text-sm font-semibold truncate flex-1 ${currentEpisodeId === ep.id ? "text-teal-400" : "text-gray-300 group-hover:text-gray-200"}`}>
                            {ep.title || "Health Episode"}
                        </span>
                    </div>

                    <div className="flex items-center gap-2 pointer-events-none w-full">
                        <div className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            ep.status === "Recovered" ? "bg-green-500/20 text-green-400" : 
                            ep.status?.includes("Active") ? "bg-teal-500/20 text-teal-400" : "bg-gray-800 text-gray-400"
                        }`}>
                            {ep.status || "Active"}
                        </div>
                        
                        <div className="flex items-center gap-1 text-[10px] text-gray-400 bg-gray-900 rounded px-2 py-0.5">
                            {renderTrendIcon(ep.trend)}
                            {ep.trend || "Stable"}
                        </div>
                    </div>
                </button>
            ))}
        </div>
    );
}
