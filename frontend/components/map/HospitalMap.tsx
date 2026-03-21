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
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
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
    return (
        <div className="glass-panel flex flex-col p-1">
            <div className="p-5 border-b border-borderDark flex flex-col gap-4">
                <h3 className="text-sm uppercase tracking-widest text-textMuted font-bold flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-primary" />
                    {t.hospitalTitle}
                    {/* Native GPS indicator badge */}
                    {isNativeApp && (
                        <span className="ml-auto flex items-center gap-1 px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[10px] font-bold text-emerald-400">
                            <Smartphone className="w-3 h-3" />
                            Native GPS
                        </span>
                    )}
                </h3>

                <button
                    onClick={findHospitals}
                    disabled={loading}
                    className="relative w-full overflow-hidden group bg-surfaceHighlight hover:bg-surface border border-borderDark rounded-xl px-4 py-3 text-sm text-textMain hover:text-primaryVibrant transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                    <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-primary/5 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
                    <Crosshair className={`w-4 h-4 ${loading ? 'animate-spin text-primary' : 'text-primary'}`} />
                    <span className="font-medium tracking-wide">{getButtonLabel()}</span>
                </button>

                {/* Waiting for native GPS sub-message */}
                {locationStatus === "waiting_native" && (
                    <p className="text-xs text-primary/70 px-2 flex items-center gap-1 animate-pulse">
                        <Smartphone className="w-3 h-3" />
                        Waiting for location from native app…
                    </p>
                )}

                {error && (
                    <p className="text-danger text-xs px-2 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {error}
                    </p>
                )}
            </div>

            <div className="relative border-b border-borderDark bg-background/50">
                <div className="absolute inset-x-0 top-0 h-4 bg-gradient-to-b from-surface/20 to-transparent z-10 pointer-events-none" />
                <MapComponent userLoc={userLoc} hospitals={hospitals} />
            </div>

            {/* Hospital cards — Google Maps style */}
            <div className="p-4 space-y-3 max-h-[420px] overflow-y-auto custom-scrollbar">
                {hospitals.map((h, i) => (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
                        key={i}
                        className="bg-surfaceHighlight/50 border border-borderDark rounded-2xl overflow-hidden hover:border-primary/30 hover:bg-surfaceHighlight transition-all shadow-sm"
                    >
                        <div className="p-4">
                            {/* Row 1: Name + emergency badge + action buttons */}
                            <div className="flex items-start justify-between gap-3">
                                {/* Left: all text info */}
                                <div className="flex-1 min-w-0">
                                    {/* Name + badge */}
                                    <div className="flex items-start gap-2 flex-wrap">
                                        <h4 className="font-bold text-textMain text-[15px] leading-snug">
                                            {h.name}
                                        </h4>
                                        {h.emergency && (
                                            <span className="shrink-0 mt-0.5 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-danger/20 text-danger border border-danger/20">
                                                Emergency
                                            </span>
                                        )}
                                    </div>

                                    {/* Star rating row */}
                                    {h.rating != null && (
                                        <div className="flex items-center gap-1.5 mt-1">
                                            <span className="text-sm font-bold text-amber-400">{h.rating.toFixed(1)}</span>
                                            <StarRating rating={h.rating} />
                                            {h.user_ratings_total != null && (
                                                <span className="text-xs text-textMuted">({h.user_ratings_total.toLocaleString()})</span>
                                            )}
                                        </div>
                                    )}

                                    {/* Specialty · wheelchair · address */}
                                    <p className="text-xs text-textMuted mt-1 leading-relaxed">
                                        {[
                                            h.specialty,
                                            h.wheelchair_accessible ? "♿ Accessible" : null,
                                            h.address && h.address !== "Unknown Address" ? h.address : null,
                                        ].filter(Boolean).join(" · ")}
                                    </p>

                                    {/* Open/Closed + hours + phone */}
                                    <div className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5 mt-1">
                                        {h.open_now != null && (
                                            <span className={`text-xs font-semibold ${h.open_now ? "text-emerald-400" : "text-danger"}`}>
                                                {h.open_now ? "Open" : "Closed"}
                                            </span>
                                        )}
                                        {h.opening_hours && h.opening_hours !== "Unknown Hours" && (
                                            <>
                                                <span className="text-textMuted/40 text-xs">·</span>
                                                <span className="text-xs text-textMuted">{h.opening_hours}</span>
                                            </>
                                        )}
                                        {h.phone && h.phone !== "Unknown Phone" && (
                                            <>
                                                <span className="text-textMuted/40 text-xs">·</span>
                                                <a
                                                    href={`tel:${h.phone}`}
                                                    className="text-xs text-textMuted hover:text-secondary transition-colors"
                                                >
                                                    {h.phone}
                                                </a>
                                            </>
                                        )}
                                    </div>

                                    {/* Distance */}
                                    {h.distance_km > 0 && (
                                        <p className="text-xs font-mono text-secondary/60 mt-1">
                                            📍 {h.distance_km} km away
                                        </p>
                                    )}
                                </div>

                                {/* Right: Website + Directions icon buttons (Google Maps style) */}
                                <div className="flex flex-col gap-2 items-center shrink-0">
                                    {h.website && (
                                        <a
                                            href={h.website}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex flex-col items-center gap-1 group"
                                            title="Visit website"
                                        >
                                            <span className="w-11 h-11 rounded-full bg-[#e8f0fe] flex items-center justify-center group-hover:bg-[#d2e3fc] transition-colors">
                                                <Globe className="w-5 h-5 text-[#1a73e8]" />
                                            </span>
                                            <span className="text-[10px] text-textMuted group-hover:text-[#1a73e8] transition-colors font-medium">Website</span>
                                        </a>
                                    )}
                                    {/* Directions — links to Google Maps turn-by-turn */}
                                    <a
                                        href={`https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}&destination_place_id=${encodeURIComponent(h.maps_url.split("place_id:")[1] ?? "")}&travelmode=driving`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex flex-col items-center gap-1 group"
                                        title="Get directions"
                                    >
                                        <span className="w-11 h-11 rounded-full bg-[#e8f0fe] flex items-center justify-center group-hover:bg-[#d2e3fc] transition-colors">
                                            <Navigation className="w-5 h-5 text-[#1a73e8]" />
                                        </span>
                                        <span className="text-[10px] text-textMuted group-hover:text-[#1a73e8] transition-colors font-medium">Directions</span>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                ))}

                {hospitals.length === 0 && !loading && userLoc && (
                    <div className="py-8 px-4 text-center border border-dashed border-borderDark rounded-xl">
                        <p className="text-sm text-textMuted/60 font-mono">{t.hospitalNone}</p>
                    </div>
                )}
                {hospitals.length === 0 && !loading && !userLoc && (
                    <div className="py-12 px-4 text-center text-textMuted/40">
                        <MapPin className="w-8 h-8 mx-auto mb-3 opacity-20" />
                        <p className="text-xs uppercase tracking-widest">
                            {isNativeApp ? "Tap button — native GPS will activate" : "Connect GPS to populate list"}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
