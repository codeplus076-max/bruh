import { create } from 'zustand';
import { ParsedSnapshot, DiffResult, sanitizeSnapshot, computeDiff } from '@/lib/dashboardUtils';

export interface DashboardState {
    currentEpisodeId: string | null;
    previousSnapshot: ParsedSnapshot | null;
    currentSnapshot: ParsedSnapshot | null;
    diffResult: DiffResult;
    
    // Actions
    setCurrentEpisode: (id: string | null) => void;
    onNewResponse: (rawJson: Partial<ParsedSnapshot> | null) => void;
    loadEpisodeState: (snapshot: ParsedSnapshot) => void;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
    currentEpisodeId: null,
    previousSnapshot: null,
    currentSnapshot: null,
    diffResult: {
        risk_changed: false,
        trend_changed: false,
        status_changed: false,
        actions_changed: false
    },

    setCurrentEpisode: (id: string | null) => set({ currentEpisodeId: id }),

    onNewResponse: (rawJson) => {
        const parsed = sanitizeSnapshot(rawJson);
        const prev = get().currentSnapshot;
        set({
            previousSnapshot: prev,
            currentSnapshot: parsed,
            diffResult: computeDiff(prev, parsed)
        });
    },

    loadEpisodeState: (snapshot) => {
        // Hydrate from Firestore history without triggering an aggressive diff 
        // since we are just resuming the page
        const parsed = sanitizeSnapshot(snapshot);
        set({
            previousSnapshot: parsed, // Assume last state is baseline
            currentSnapshot: parsed,
            diffResult: {
                risk_changed: false,
                trend_changed: false,
                status_changed: false,
                actions_changed: false
            }
        });
    }
}));
