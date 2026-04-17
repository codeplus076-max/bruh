export interface ParsedSnapshot {
    episode_context: {
        title: string;
        status: string;
        trend: string;
        last_updated: string;
    };
    status: string;
    progression: {
        trend: string;
        day: string;
    };
    risk: {
        level: string;
        reason: string;
    };
    actions: string[];
    medicines: string[];
    alerts: string[];
}

export interface DiffResult {
    risk_changed: boolean;
    trend_changed: boolean;
    status_changed: boolean;
    actions_changed: boolean;
}

/**
 * Ensures a robust fallback if the formatting engine failed to provide an exact rigid schema.
 */
export function sanitizeSnapshot(rawJson: Partial<ParsedSnapshot> | null | undefined): ParsedSnapshot {
    return {
        episode_context: {
            title: rawJson?.episode_context?.title || "New Health Episode",
            status: rawJson?.episode_context?.status || "Active",
            trend: rawJson?.episode_context?.trend || "Stable",
            last_updated: rawJson?.episode_context?.last_updated || new Date().toISOString()
        },
        status: rawJson?.status || "Analyzing context...",
        progression: {
            trend: rawJson?.progression?.trend || "Stable",
            day: rawJson?.progression?.day || "Day 1"
        },
        risk: {
            level: rawJson?.risk?.level || "Evaluating",
            reason: rawJson?.risk?.reason || ""
        },
        actions: Array.isArray(rawJson?.actions) ? rawJson.actions : [],
        medicines: Array.isArray(rawJson?.medicines) ? rawJson.medicines : [],
        alerts: Array.isArray(rawJson?.alerts) ? rawJson.alerts : []
    };
}

/**
 * Computes deep differential changes to dispatch animation triggers across Dashboard cards.
 */
export function computeDiff(prev: ParsedSnapshot | null, curr: ParsedSnapshot): DiffResult {
    if (!prev) {
        return {
            risk_changed: true,
            trend_changed: true,
            status_changed: true,
            actions_changed: true
        };
    }

    return {
        risk_changed: prev.risk.level !== curr.risk.level,
        trend_changed: prev.progression.trend !== curr.progression.trend,
        status_changed: prev.status !== curr.status,
        actions_changed: JSON.stringify(prev.actions) !== JSON.stringify(curr.actions)
    };
}
