"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Translations } from "@/lib/translations";
import { MapPin, AlertCircle, Crosshair, Phone, Clock } from "lucide-react";
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
                        maps_url: `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=14/${latitude}/${longitude}`,
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

            <div className="p-4 space-y-3 max-h-[320px] overflow-y-auto custom-scrollbar">
                {hospitals.map((h, i) => (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                        key={i}
                        className={`p-4 rounded-xl border relative overflow-hidden transition-all hover:shadow-glass ${h.emergency
                            ? "bg-danger/5 border-danger/20 hover:border-danger/40"
                            : "bg-surfaceHighlight/50 border-borderDark hover:border-primary/30"
                            }`}
                    >
                        {h.emergency && <div className="absolute top-0 right-0 w-16 h-16 bg-danger/10 blur-2xl rounded-full" />}

                        <div className="relative z-10">
                            <h4 className="font-bold text-white tracking-wide text-[15px] flex items-center gap-2">
                                {h.name} {h.emergency && <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-danger/20 text-danger border border-danger/20">{t.hospitalEmergency}</span>}
                            </h4>
                            <p className="text-sm text-textMuted mt-1 mb-2">{h.address}</p>

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

                            <div className="flex items-center justify-between mt-auto pt-3 border-t border-borderDark/50">
                                {h.distance_km > 0
                                    ? <span className="text-xs font-mono text-secondary">{h.distance_km} {t.hospitalDistanceUnit}</span>
                                    : <span className="text-xs font-mono text-primary/60">GPS Origin</span>
                                }

                                <a href={h.maps_url} target="_blank" rel="noopener noreferrer" className="text-primary text-xs font-medium hover:text-primaryVibrant hover:underline flex items-center gap-1 transition-colors">
                                    {t.hospitalOpenMaps}
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
