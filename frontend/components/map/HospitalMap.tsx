"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Translations } from "@/lib/translations";
import { MapPin, AlertCircle, Crosshair, Phone, Clock, Star } from "lucide-react";
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
    open_now?: boolean;
    rating?: number;
    rating_count?: number;
};

const MapComponent = dynamic(() => import("./Map"), { ssr: false });

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
                        phone: undefined,
                        opening_hours: undefined,
                    }]);
                }
                setLoading(false);
            },
            () => {
                setError(t.hospitalNoAccess);
                setLoading(false);
            },
            // High accuracy GPS — get exact position
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    };

    const renderStars = (rating: number) => {
        const full = Math.floor(rating);
        const half = rating % 1 >= 0.5;
        return (
            <span className="flex items-center gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                        key={i}
                        className={`w-3 h-3 ${i < full ? "text-yellow-400 fill-yellow-400" : half && i === full ? "text-yellow-400 fill-yellow-400/50" : "text-textMuted/30"}`}
                    />
                ))}
            </span>
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

            <div className="p-4 space-y-3 max-h-[380px] overflow-y-auto custom-scrollbar">
                {hospitals.map((h, i) => (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
                        key={i}
                        className={`p-4 rounded-xl border relative overflow-hidden transition-all hover:shadow-glass ${h.emergency
                            ? "bg-danger/5 border-danger/20 hover:border-danger/40"
                            : "bg-surfaceHighlight/50 border-borderDark hover:border-primary/30"
                            }`}
                    >
                        {h.emergency && <div className="absolute top-0 right-0 w-16 h-16 bg-danger/10 blur-2xl rounded-full" />}

                        <div className="relative z-10">
                            {/* Name + Emergency badge */}
                            <div className="flex items-start justify-between gap-2 mb-1">
                                <h4 className="font-bold text-white tracking-wide text-[15px] leading-snug">
                                    {h.name}
                                </h4>
                                {h.emergency && (
                                    <span className="shrink-0 px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-danger/20 text-danger border border-danger/20">
                                        {t.hospitalEmergency}
                                    </span>
                                )}
                            </div>

                            {/* Address */}
                            <p className="text-sm text-textMuted mb-2">{h.address}</p>

                            {/* Rating + Open/Closed */}
                            <div className="flex items-center gap-3 mb-3">
                                {h.rating !== undefined && h.rating !== null && (
                                    <div className="flex items-center gap-1.5">
                                        {renderStars(h.rating)}
                                        <span className="text-xs text-yellow-400 font-semibold">{h.rating.toFixed(1)}</span>
                                        {h.rating_count && (
                                            <span className="text-xs text-textMuted/60">({h.rating_count.toLocaleString()})</span>
                                        )}
                                    </div>
                                )}
                                {h.open_now !== undefined && h.open_now !== null && (
                                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${h.open_now ? "text-emerald-400 bg-emerald-400/10" : "text-red-400 bg-red-400/10"}`}>
                                        {h.open_now ? "Open Now" : "Closed"}
                                    </span>
                                )}
                            </div>

                            {/* Phone + Hours */}
                            {(h.phone || h.opening_hours) && (
                                <div className="flex flex-col gap-1 mb-3 pt-2 border-t border-borderDark/30">
                                    {h.phone && (
                                        <div className="flex items-center gap-1.5 text-xs text-textMuted/80">
                                            <Phone className="w-3 h-3 text-secondary" />
                                            <a href={`tel:${h.phone}`} className="hover:text-secondary hover:underline">{h.phone}</a>
                                        </div>
                                    )}
                                    {h.opening_hours && (
                                        <div className="flex items-center gap-1.5 text-xs text-textMuted/80">
                                            <Clock className="w-3 h-3 text-primaryVibrant" />
                                            <span>{h.opening_hours}</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Distance + Buttons */}
                            <div className="flex items-center justify-between mt-auto pt-3 border-t border-borderDark/50 gap-2">
                                {h.distance_km > 0
                                    ? <span className="text-xs font-mono text-secondary">{h.distance_km} {t.hospitalDistanceUnit}</span>
                                    : <span className="text-xs font-mono text-primary/60">GPS Origin</span>
                                }
                                <div className="flex gap-2">
                                    <a
                                        href={userLoc
                                            ? `https://www.google.com/maps/dir/?api=1&origin=${userLoc.lat},${userLoc.lng}&destination=${h.lat},${h.lng}&travelmode=driving`
                                            : `https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}`
                                        }
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs font-medium px-2.5 py-1 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 transition-colors"
                                    >
                                        🧭 Navigate
                                    </a>
                                    <a
                                        href={h.maps_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs font-medium px-2.5 py-1 rounded-lg bg-surface text-textMuted hover:text-white border border-borderDark hover:border-primary/30 transition-colors"
                                    >
                                        📍 View
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
                        <p className="text-xs uppercase tracking-widest">Connect GPS to populate list</p>
                    </div>
                )}
            </div>
        </div>
    );
}
