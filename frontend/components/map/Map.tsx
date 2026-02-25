"use client";

import { useState, useCallback } from "react";
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from "@react-google-maps/api";

const MAPS_API_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY || "";

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

const mapContainerStyle = { width: "100%", height: "400px" };
const defaultCenter = { lat: 20.5937, lng: 78.9629 }; // Center of India

const darkMapStyles = [
    { elementType: "geometry", stylers: [{ color: "#1a1a2e" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#1a1a2e" }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#8892b0" }] },
    { featureType: "road", elementType: "geometry", stylers: [{ color: "#0f3460" }] },
    { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#16213e" }] },
    { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#64ffda" }] },
    { featureType: "water", elementType: "geometry", stylers: [{ color: "#0d1b2a" }] },
    { featureType: "poi", elementType: "geometry", stylers: [{ color: "#162032" }] },
    { featureType: "transit", elementType: "geometry", stylers: [{ color: "#162032" }] },
    { featureType: "administrative", elementType: "geometry", stylers: [{ color: "#1f4068" }] },
];

export default function GoogleMapComponent({ userLoc, hospitals }: MapProps) {
    const { isLoaded, loadError } = useJsApiLoader({
        googleMapsApiKey: MAPS_API_KEY,
    });

    const [selectedHospital, setSelectedHospital] = useState<Hospital | null>(null);

    const center = userLoc ? { lat: userLoc.lat, lng: userLoc.lng } : defaultCenter;
    const zoom = userLoc ? 13 : 5;

    const onMapClick = useCallback(() => {
        setSelectedHospital(null);
    }, []);

    if (loadError) {
        return (
            <div className="h-[400px] w-full flex items-center justify-center bg-surface text-textMuted rounded border border-borderDark text-sm">
                ⚠️ Failed to load Google Maps. Check your API key.
            </div>
        );
    }

    if (!isLoaded) {
        return (
            <div className="h-[400px] w-full flex items-center justify-center bg-surface text-textMuted rounded border border-borderDark text-sm animate-pulse">
                Loading Google Maps...
            </div>
        );
    }

    return (
        <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={center}
            zoom={zoom}
            onClick={onMapClick}
            options={{
                styles: darkMapStyles,
                disableDefaultUI: false,
                zoomControl: true,
                streetViewControl: false,
                mapTypeControl: false,
                fullscreenControl: true,
            }}
        >
            {/* User location marker */}
            {userLoc && (
                <Marker
                    position={{ lat: userLoc.lat, lng: userLoc.lng }}
                    icon={{
                        url: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
                        scaledSize: new window.google.maps.Size(40, 40),
                    }}
                    title="You are here"
                />
            )}

            {/* Hospital markers */}
            {hospitals.map((h, i) => (
                <Marker
                    key={i}
                    position={{ lat: h.lat, lng: h.lng }}
                    icon={{
                        url: h.emergency
                            ? "https://maps.google.com/mapfiles/ms/icons/red-dot.png"
                            : "https://maps.google.com/mapfiles/ms/icons/hospitals.png",
                        scaledSize: new window.google.maps.Size(36, 36),
                    }}
                    onClick={() => setSelectedHospital(h)}
                    title={h.name}
                />
            ))}

            {/* Info window for selected hospital */}
            {selectedHospital && (
                <InfoWindow
                    position={{ lat: selectedHospital.lat, lng: selectedHospital.lng }}
                    onCloseClick={() => setSelectedHospital(null)}
                >
                    <div style={{ fontFamily: "sans-serif", maxWidth: "220px", padding: "4px 0" }}>
                        <strong style={{ fontSize: "14px" }}>
                            {selectedHospital.name}{selectedHospital.emergency ? " 🚨" : ""}
                        </strong>
                        <p style={{ fontSize: "12px", color: "#555", margin: "4px 0" }}>
                            🗺️ {selectedHospital.address}
                        </p>
                        <p style={{ fontSize: "12px", color: "#555", margin: "2px 0" }}>
                            📏 {selectedHospital.distance_km} km away
                        </p>
                        {selectedHospital.phone && selectedHospital.phone !== "Unknown Phone" && (
                            <p style={{ fontSize: "12px", margin: "2px 0" }}>
                                📞 <a href={`tel:${selectedHospital.phone}`} style={{ color: "#2563eb" }}>
                                    {selectedHospital.phone}
                                </a>
                            </p>
                        )}
                        {selectedHospital.opening_hours && selectedHospital.opening_hours !== "Unknown Hours" && (
                            <p style={{ fontSize: "12px", color: "#555", margin: "2px 0" }}>
                                🕒 {selectedHospital.opening_hours}
                            </p>
                        )}
                        <div style={{ marginTop: "10px", display: "flex", gap: "8px" }}>
                            <a
                                href={`https://www.google.com/maps/dir/?api=1&destination=${selectedHospital.lat},${selectedHospital.lng}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                    background: "#2563eb",
                                    color: "white",
                                    padding: "5px 10px",
                                    borderRadius: "6px",
                                    textDecoration: "none",
                                    fontSize: "12px",
                                    fontWeight: "600"
                                }}
                            >
                                🧭 Navigate
                            </a>
                            <a
                                href={selectedHospital.maps_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ color: "#2563eb", fontSize: "12px", alignSelf: "center" }}
                            >
                                View on Maps
                            </a>
                        </div>
                    </div>
                </InfoWindow>
            )}
        </GoogleMap>
    );
}
