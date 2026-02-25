"use client";

import { useEffect, useRef } from "react";
import type { Map as LeafletMap } from "leaflet";
import "leaflet/dist/leaflet.css";

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

export interface MapProps {
    userLoc: { lat: number; lng: number } | null;
    hospitals: Hospital[];
}

export default function OSMMap({ userLoc, hospitals }: MapProps) {
    const mapRef = useRef<HTMLDivElement>(null);
    const leafletMapRef = useRef<LeafletMap | null>(null);

    useEffect(() => {
        // Dynamically import leaflet to avoid SSR issues
        import("leaflet").then((L) => {
            if (!mapRef.current) return;

            // Destroy existing map instance before re-init
            if (leafletMapRef.current) {
                leafletMapRef.current.remove();
                leafletMapRef.current = null;
            }

            const center: [number, number] = userLoc
                ? [userLoc.lat, userLoc.lng]
                : [20.5937, 78.9629]; // Default: center of India

            const map = L.map(mapRef.current).setView(center, userLoc ? 13 : 5);
            leafletMapRef.current = map;

            L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            }).addTo(map);

            // Fix default icon URLs
            const defaultIcon = L.icon({
                iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
                iconRetinaUrl:
                    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
                shadowUrl:
                    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
            });

            const redIcon = L.icon({
                iconUrl:
                    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
                shadowUrl:
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
            });

            const greenIcon = L.icon({
                iconUrl:
                    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
                shadowUrl:
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
            });

            // User location marker
            if (userLoc) {
                L.marker([userLoc.lat, userLoc.lng], { icon: greenIcon })
                    .addTo(map)
                    .bindPopup("<strong>📍 You are here</strong>");
            }

            // Hospital markers
            hospitals.forEach((h) => {
                const markerIcon = h.emergency ? redIcon : defaultIcon;
                const phoneStr = h.phone && h.phone !== "Unknown Phone" ? `<br/>📞 ${h.phone}` : "";
                const hoursStr = h.opening_hours && h.opening_hours !== "Unknown Hours" ? `<br/>🕒 ${h.opening_hours}` : "";
                const navUrl = `https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lng}`;

                L.marker([h.lat, h.lng], { icon: markerIcon })
                    .addTo(map)
                    .bindPopup(
                        `<div style="font-family: inherit; padding-top: 4px;">
                            <strong>${h.name}${h.emergency ? " 🚨" : ""}</strong><br/>
                            🗺️ ${h.address}<br/>
                            📏 Distance: ${h.distance_km} km${phoneStr}${hoursStr}<br/>
                            <div style="margin-top: 8px; display: flex; gap: 8px; align-items: center;">
                                <a href="${navUrl}" target="_blank" style="background: #2563eb; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 500;">🧭 Navigate</a>
                                <a href="${h.maps_url}" target="_blank" style="color: #2563eb; padding: 4px 0; text-decoration: underline; font-size: 12px;">OSM</a>
                            </div>
                         </div>`
                    );
            });
        });

        // Cleanup on unmount
        return () => {
            if (leafletMapRef.current) {
                leafletMapRef.current.remove();
                leafletMapRef.current = null;
            }
        };
    }, [userLoc, hospitals]);

    return (
        <div
            ref={mapRef}
            className="h-[400px] w-full rounded overflow-hidden border"
        />
    );
}
