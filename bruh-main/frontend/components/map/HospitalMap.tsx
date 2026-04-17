"use client";

/**
 * HospitalMap.tsx
 *
 * NATIVE GPS INTEGRATION (MIT App Inventor / WebViewer)
 * -------------------------------------------------------
 * When this web app is embedded inside an MIT App Inventor WebViewer,
 * the native Android/iOS app calls:
 *
 *   window.receiveNativeLocation(latitude, longitude)
 *
 * This component registers that global function on mount and
 * automatically uses it when the app detects it is running inside
 * MIT App Inventor (via: typeof window.AppInventor !== "undefined").
 *
 * PRIORITY ORDER:
 *   1. Native GPS  → MIT App Inventor calls window.receiveNativeLocation()
 *   2. Browser GPS → navigator.geolocation.getCurrentPosition()
 *   3. Offline     → Demo fallback hospital card
 *
 * CLEANUP:
 *   The global window.receiveNativeLocation is deleted on component unmount
 *   to prevent stale closures and memory leaks.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { Translations } from "@/lib/translations";
import { MapPin, AlertCircle, Crosshair, Globe, Navigation, Smartphone } from "lucide-react";
import { motion } from "framer-motion";

// --------------------
// Types
// --------------------
type Hospital = {
    name: string;
    address: string;
    distance_km: number;
    lat: number;
    lng: number;
    emergency: boolean;
    maps_url: string;
    phone?: string;
    opening_hours?: string;
    rating?: number;
    user_ratings_total?: number;
    website?: string;
    wheelchair_accessible?: boolean;
    open_now?: boolean;
    specialty?: string;
};


// Window types for native bridges are centralized in types/native-bridge.d.ts


// --------------------
// Dynamic Map (no SSR)
// --------------------
const MapComponent = dynamic(() => import("./Map"), { ssr: false });

// --------------------
// Star Rating sub-component
// --------------------
function StarRating({ rating }: { rating: number }) {
    const full = Math.floor(rating);
    const half = rating - full >= 0.5;
    return (
        <span className="flex items-center gap-0.5">
            {Array.from({ length: 5 }).map((_, i) => {
                const filled = i < full;
                const isHalf = !filled && half && i === full;
                return (
                    <svg key={i} className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
                        {filled ? (
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="#f59e0b" />
                        ) : isHalf ? (
                            <>
                                <defs>
                                    <linearGradient id={`half-${i}`}>
                                        <stop offset="50%" stopColor="#f59e0b" />
                                        <stop offset="50%" stopColor="#374151" />
                                    </linearGradient>
                                </defs>
                                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill={`url(#half-${i})`} />
                            </>
                        ) : (
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="#374151" />
                        )}
                    </svg>
                );
            })}
        </span>
    );
}

// --------------------
// Main Component
// --------------------
export function HospitalMap({ t }: { t: Translations }) {
    const [hospitals, setHospitals] = useState<Hospital[]>([]);
    const [loading, setLoading] = useState(false);
    const [locationStatus, setLocationStatus] = useState<"idle" | "waiting_native" | "fetching_browser" | "fetching_hospitals">("idle");
    const [error, setError] = useState<string | null>(null);
    const [userLoc, setUserLoc] = useState<{ lat: number; lng: number } | null>(null);
    const [isNativeApp, setIsNativeApp] = useState(false);

    // Ref to hold a resolve function for the pending native location promise
    const nativeLocationResolveRef = useRef<((loc: { lat: number; lng: number }) => void) | null>(null);
    // Ref to prevent duplicate location triggers
    const locationReceivedRef = useRef(false);

    // ---------------------------------------------------------------
    // Detect MIT App Inventor environment (safe: after component mounts)
    // ---------------------------------------------------------------
    useEffect(() => {
        if (typeof window !== "undefined") {
            setIsNativeApp(typeof window.AppInventor !== "undefined");
        }
    }, []);

    // ---------------------------------------------------------------
    // Register global window.receiveNativeLocation on mount
    // Cleanup on unmount to avoid stale closures
    // ---------------------------------------------------------------
    useEffect(() => {
        if (typeof window === "undefined") return;

        window.receiveNativeLocation = (lat: number | string, lng: number | string) => {
            // Guard against duplicate calls (e.g. GPS polling from native side)
            if (locationReceivedRef.current) return;
            locationReceivedRef.current = true;

            const parsedLat = Number(lat);
            const parsedLng = Number(lng);

            if (isNaN(parsedLat) || isNaN(parsedLng)) {
                console.error("[GPS Bridge] Received invalid coordinates:", lat, lng);
                return;
            }

            const loc = { lat: parsedLat, lng: parsedLng };
            setUserLoc(loc);

            // If there's a pending promise waiting for native location, resolve it
            if (nativeLocationResolveRef.current) {
                nativeLocationResolveRef.current(loc);
                nativeLocationResolveRef.current = null;
            }
        };

        // Cleanup: remove global function to prevent memory leaks / stale ref
        return () => {
            if (typeof window !== "undefined") {
                delete window.receiveNativeLocation;
            }
        };
    }, []); // Run only once on mount

    // ---------------------------------------------------------------
    // Fetch hospitals from backend given a lat/lng
    // ---------------------------------------------------------------
    const fetchHospitals = useCallback(async (latitude: number, longitude: number) => {
        setLocationStatus("fetching_hospitals");
        setLoading(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://bruh-1-u248.onrender.com";
            const res = await fetch(`${apiUrl}/hospitals/nearby?lat=${latitude}&lng=${longitude}`);
            if (!res.ok) throw new Error("api_error");
            const data = await res.json();
            setHospitals(data.hospitals);
        } catch {
            // Offline fallback card
            setHospitals([{
                name: "Central Medical Center (Demo)",
                address: "Network disconnected. Offline fallback.",
                distance_km: 0,
                lat: latitude + 0.01,
                lng: longitude + 0.01,
                emergency: true,
                maps_url: `https://www.google.com/maps/search/hospital/@${latitude},${longitude},14z`,
                phone: "+1-800-RURAL-MED",
                opening_hours: "24/7"
            }]);
        } finally {
            setLoading(false);
            setLocationStatus("idle");
        }
    }, []);

    // ---------------------------------------------------------------
    // Main "Find Hospitals" handler — uses native GPS or browser GPS
    // ---------------------------------------------------------------
    const findHospitals = useCallback(async () => {
        setError(null);
        setHospitals([]);
        locationReceivedRef.current = false; // Reset duplicate guard for new search

        // ------------------------------------
        // PATH 1: MIT App Inventor native GPS
        // ------------------------------------
        if (isNativeApp) {
            setLocationStatus("waiting_native");
            setLoading(true);

            try {
                // Create a promise that resolves when the native app calls
                // window.receiveNativeLocation(), or times out after 10 seconds
                const nativeLocation = await new Promise<{ lat: number; lng: number }>((resolve, reject) => {
                    nativeLocationResolveRef.current = resolve;

                    // 10-second timeout in case GPS is unavailable
                    setTimeout(() => {
                        nativeLocationResolveRef.current = null;
                        reject(new Error("Native GPS timed out after 10 seconds."));
                    }, 10_000);
                });

                setUserLoc(nativeLocation);
                await fetchHospitals(nativeLocation.lat, nativeLocation.lng);

            } catch (err) {
                const message = err instanceof Error ? err.message : "Native GPS failed.";
                console.error("[GPS Bridge] Error:", message);
                setError(t.hospitalNoAccess + " (Native GPS unavailable — try browser mode)");
                setLoading(false);
                setLocationStatus("idle");
            }
            return;
        }

        // ------------------------------------
        // PATH 2: Standard Browser GPS fallback
        // ------------------------------------
        if (!navigator.geolocation) {
            setError(t.hospitalNoAccess);
            return;
        }

        setLocationStatus("fetching_browser");
        setLoading(true);

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                setUserLoc({ lat: latitude, lng: longitude });
                await fetchHospitals(latitude, longitude);
            },
            (geoError) => {
                console.error("[Browser GPS] Error:", geoError.message);
                setError(t.hospitalNoAccess);
                setLoading(false);
                setLocationStatus("idle");
            },
            {
                enableHighAccuracy: false, // Much faster, sufficient for hospital radius search
                timeout: 10_000,
                maximumAge: 60_000 // Cache GPS lock for 1 minute
            }
        );
    }, [isNativeApp, fetchHospitals, t.hospitalNoAccess]);

    // ---------------------------------------------------------------
    // Dynamic button label based on current loading state
    // ---------------------------------------------------------------
    const getButtonLabel = () => {
        if (locationStatus === "waiting_native") return "Waiting for GPS…";
        if (locationStatus === "fetching_browser") return "Fetching location…";
        if (locationStatus === "fetching_hospitals") return "Loading hospitals…";
        return t.hospitalFind;
    };

    // ---------------------------------------------------------------
    // Render
    // ---------------------------------------------------------------
    // ---------------------------------------------------------------
    // Render
    // ---------------------------------------------------------------
    return (
        <div className="glass-panel flex flex-col p-1 overflow-hidden">
            <div className="p-6 border-b border-borderDark flex flex-col gap-5 bg-surfaceHighlight/30">
                <div className="flex items-center justify-between gap-4">
                    <h3 className="text-[11px] uppercase tracking-[0.25em] text-primary font-black flex items-center gap-2.5">
                        <MapPin className="w-4 h-4" />
                        Nearby Facilities & Hospitals
                    </h3>
                    
                    {/* Native GPS indicator badge */}
                    {isNativeApp && (
                        <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[10px] font-bold text-emerald-400">
                            <Smartphone className="w-3 h-3" />
                            Live GPS
                        </span>
                    )}
                </div>

                <div className="relative group">
                    <button
                        onClick={findHospitals}
                        disabled={loading}
                        className="w-full bg-surfaceHighlight hover:bg-surface border border-borderDark rounded-2xl px-6 py-4 text-sm text-textMain transition-all shadow-lg flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed group-hover:border-primary/40 group-hover:shadow-neon"
                    >
                        <Crosshair className={`w-4 h-4 ${loading ? 'animate-spin text-primary' : 'text-primary'}`} />
                        <span className="font-bold tracking-wider">{getButtonLabel()}</span>
                    </button>
                    {loading && <div className="absolute inset-0 rounded-2xl border-2 border-primary/20 animate-pulse pointer-events-none" />}
                </div>

                {error && (
                    <p className="text-danger text-xs px-2 py-2 bg-danger/5 border border-danger/10 rounded-lg flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        {error}
                    </p>
                )}
            </div>

            <div className="relative border-b border-borderDark bg-[#0a0a0f] h-[340px]">
                <div className="absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-black/40 to-transparent z-10 pointer-events-none" />
                <MapComponent userLoc={userLoc} hospitals={hospitals} />
                <div className="absolute inset-x-0 bottom-0 h-4 bg-gradient-to-t from-black/20 to-transparent z-10 pointer-events-none" />
            </div>

            {/* Hospital cards — Modern List style */}
            <div className="p-4 space-y-4 max-h-[480px] overflow-y-auto custom-scrollbar bg-background/30">
                {hospitals.map((h, i) => (
                    <motion.div
                        initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                        key={i}
                        className="relative group bg-surfaceHighlight/40 border border-borderDark rounded-[24px] overflow-hidden hover:border-primary/40 hover:bg-surfaceHighlight transition-all shadow-md active:scale-[0.98]"
                    >
                        <div className="p-5 pr-16 flex flex-col gap-1.5">
                            {/* Emergency Badge */}
                            {h.emergency && (
                                <span className="w-fit mb-1.5 px-2 py-0.5 rounded-full text-[9px] uppercase font-black bg-danger/20 text-danger border border-danger/30 tracking-widest">
                                    Emergency Unit
                                </span>
                            )}

                            <h4 className="font-bold text-textMain text-base leading-tight group-hover:text-primary transition-colors">
                                {h.name}
                            </h4>

                            {/* Ratings & Metadata */}
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 mt-0.5">
                                {h.rating != null && (
                                    <div className="flex items-center gap-1.5">
                                        <StarRating rating={h.rating} />
                                        <span className="text-[11px] font-mono text-amber-500 font-bold">{h.rating.toFixed(1)}</span>
                                    </div>
                                )}
                                
                                {h.distance_km > 0 && (
                                    <span className="text-[10px] font-bold text-secondary flex items-center gap-1">
                                        <span className="w-1 h-1 rounded-full bg-secondary/30" />
                                        {h.distance_km} KM
                                    </span>
                                )}

                                {h.open_now != null && (
                                    <span className={`text-[10px] font-bold tracking-tight uppercase ${h.open_now ? "text-emerald-400" : "text-danger"}`}>
                                        {h.open_now ? "• Open Now" : "• Closed"}
                                    </span>
                                )}
                            </div>

                            <p className="text-xs text-textMuted mt-1 line-clamp-2 leading-relaxed opacity-80">
                                {h.address !== "Unknown Address" ? h.address : "Location details available via GPS"}
                            </p>

                            {/* Action Row */}
                            <div className="flex items-center gap-4 mt-3 pt-3 border-t border-white/5">
                                {h.phone && h.phone !== "Unknown Phone" && (
                                    <a href={`tel:${h.phone}`} className="text-[11px] font-bold text-primary hover:text-primary-light flex items-center gap-1.5">
                                        <Smartphone className="w-3.5 h-3.5" />
                                        Call Facility
                                    </a>
                                )}
                                {h.website && (
                                    <a href={h.website} target="_blank" rel="noopener noreferrer" className="text-[11px] font-bold text-textMuted hover:text-textMain flex items-center gap-1.5">
                                        <Globe className="w-3.5 h-3.5" />
                                        Website
                                    </a>
                                )}
                            </div>
                        </div>

                        {/* Large Circular Directions Button (Floating style on right) */}
                        <a
                            href={`https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}&travelmode=driving`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-primary flex items-center justify-center shadow-neon hover:scale-110 active:scale-95 transition-all group-hover:bg-primary-light"
                            title="Start Navigation"
                        >
                            <Navigation className="w-5 h-5 text-background fill-current" />
                        </a>
                    </motion.div>
                ))}

                {hospitals.length === 0 && !loading && userLoc && (
                    <div className="py-12 px-6 text-center border border-dashed border-borderDark rounded-3xl bg-surfaceHighlight/10">
                        <MapPin className="w-8 h-8 mx-auto mb-4 text-textMuted/20" />
                        <p className="text-sm text-textMuted/60 font-mono tracking-tight">{t.hospitalNone}</p>
                    </div>
                )}
                
                {hospitals.length === 0 && !loading && !userLoc && (
                    <div className="py-16 px-6 text-center">
                        <div className="relative w-12 h-12 mx-auto mb-6">
                            <MapPin className="w-12 h-12 text-primary/20 animate-pulse" />
                            <div className="absolute inset-0 w-12 h-12 rounded-full border border-primary/20 animate-ping" />
                        </div>
                        <p className="text-xs uppercase tracking-[0.2em] font-black text-textMuted/40">
                            {isNativeApp ? "Awaiting GPS Signal..." : "Connect GPS to find help"}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
