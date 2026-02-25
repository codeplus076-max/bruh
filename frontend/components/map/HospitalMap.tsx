"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Translations } from "@/lib/translations";
import { MapPin, AlertCircle, Crosshair, Globe, Navigation } from "lucide-react";
import { motion } from "framer-motion";

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

const MapComponent = dynamic(() => import("./Map"), { ssr: false });

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

export function HospitalMap({ t }: { t: Translations }) {
    const [hospitals, setHospitals] = useState<Hospital[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [userLoc, setUserLoc] = useState<{ lat: number; lng: number } | null>(null);

    const findHospitals = () => {
        setLoading(true);
        setError(null);
        if (!navigator.geolocation) {
            setError(t.hospitalNoAccess);
            setLoading(false);
            return;
        }
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                setUserLoc({ lat: latitude, lng: longitude });
                try {
                    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                    const res = await fetch(`${apiUrl}/hospitals/nearby?lat=${latitude}&lng=${longitude}`);
                    if (!res.ok) throw new Error("api_error");
                    const data = await res.json();
                    setHospitals(data.hospitals);
                } catch {
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
                }
                setLoading(false);
            },
            () => {
                setError(t.hospitalNoAccess);
                setLoading(false);
            }
        );
    };

    return (
        <div className="glass-panel flex flex-col p-1">
            <div className="p-5 border-b border-borderDark flex flex-col gap-4">
                <h3 className="text-sm uppercase tracking-widest text-textMuted font-bold flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-primary" />
                    {t.hospitalTitle}
                </h3>

                <button
                    onClick={findHospitals}
                    disabled={loading}
                    className="relative w-full overflow-hidden group bg-surfaceHighlight hover:bg-surface border border-borderDark rounded-xl px-4 py-3 text-sm text-textMain hover:text-white transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                    <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-primary/5 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
                    <Crosshair className={`w-4 h-4 ${loading ? 'animate-spin text-primary' : 'text-primary'}`} />
                    <span className="font-medium tracking-wide">{loading ? t.hospitalLocating : t.hospitalFind}</span>
                </button>

                {error && <p className="text-danger text-xs px-2 flex items-center gap-1"><AlertCircle className="w-3 h-3" /> {error}</p>}
            </div>

            <div className="relative border-b border-borderDark bg-background/50">
                <div className="absolute inset-x-0 top-0 h-4 bg-gradient-to-b from-surface/20 to-transparent z-10 pointer-events-none" />
                <MapComponent userLoc={userLoc} hospitals={hospitals} />
            </div>

            {/* Hospital cards */}
            <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar">
                {hospitals.map((h, i) => (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
                        key={i}
                        className="bg-white/5 border border-borderDark rounded-xl overflow-hidden hover:border-primary/30 hover:shadow-glass transition-all"
                    >
                        {/* Card body */}
                        <div className="p-4 flex gap-3">
                            {/* Left: info */}
                            <div className="flex-1 min-w-0">
                                {/* Name + emergency badge */}
                                <div className="flex items-start gap-2 flex-wrap">
                                    <h4 className="font-bold text-white text-[15px] leading-snug">
                                        {h.name}
                                    </h4>
                                    {h.emergency && (
                                        <span className="shrink-0 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-danger/20 text-danger border border-danger/20">
                                            {t.hospitalEmergency}
                                        </span>
                                    )}
                                </div>

                                {/* Rating row */}
                                {h.rating != null && (
                                    <div className="flex items-center gap-1.5 mt-1.5">
                                        <span className="text-sm font-bold text-amber-400">{h.rating.toFixed(1)}</span>
                                        <StarRating rating={h.rating} />
                                        {h.user_ratings_total != null && (
                                            <span className="text-xs text-textMuted">({h.user_ratings_total.toLocaleString()})</span>
                                        )}
                                    </div>
                                )}

                                {/* Specialty · wheelchair · address */}
                                <p className="text-xs text-textMuted mt-1.5 leading-relaxed">
                                    {h.specialty && <span>{h.specialty}</span>}
                                    {h.wheelchair_accessible && <span> · ♿</span>}
                                    {h.address && h.address !== "Unknown Address" && (
                                        <span className={h.specialty ? " · " : ""}>{h.address}</span>
                                    )}
                                </p>

                                {/* Open/Closed + hours + phone */}
                                <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-1.5">
                                    {h.open_now != null && (
                                        <span className={`text-xs font-semibold ${h.open_now ? "text-emerald-400" : "text-danger"}`}>
                                            {h.open_now ? "Open" : "Closed"}
                                        </span>
                                    )}
                                    {h.opening_hours && h.opening_hours !== "Unknown Hours" && (
                                        <span className="text-xs text-textMuted">{h.opening_hours}</span>
                                    )}
                                    {h.phone && h.phone !== "Unknown Phone" && (
                                        <>
                                            <span className="text-xs text-textMuted/40">·</span>
                                            <a
                                                href={`tel:${h.phone}`}
                                                className="text-xs text-textMuted hover:text-secondary transition-colors"
                                            >
                                                {h.phone}
                                            </a>
                                        </>
                                    )}
                                </div>

                                {/* Distance badge */}
                                {h.distance_km > 0 && (
                                    <p className="text-xs font-mono text-secondary/70 mt-1.5">
                                        📍 {h.distance_km} km away
                                    </p>
                                )}
                            </div>

                            {/* Right: Website + Directions icon buttons */}
                            <div className="flex flex-col gap-2 items-center shrink-0 pt-0.5">
                                {h.website && (
                                    <a
                                        href={h.website}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex flex-col items-center gap-1 group"
                                        title="Visit website"
                                    >
                                        <span className="w-10 h-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                                            <Globe className="w-4 h-4 text-primary" />
                                        </span>
                                        <span className="text-[10px] text-textMuted group-hover:text-primary transition-colors">Website</span>
                                    </a>
                                )}
                                <a
                                    href={`https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex flex-col items-center gap-1 group"
                                    title="Get directions"
                                >
                                    <span className="w-10 h-10 rounded-full bg-secondary/10 border border-secondary/20 flex items-center justify-center group-hover:bg-secondary/20 transition-colors">
                                        <Navigation className="w-4 h-4 text-secondary" />
                                    </span>
                                    <span className="text-[10px] text-textMuted group-hover:text-secondary transition-colors">Directions</span>
                                </a>
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
                        <p className="text-xs uppercase tracking-widest">Connect GPS to populate list</p>
                    </div>
                )}
            </div>
        </div>
    );
}
