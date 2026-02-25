"use client";

import dynamic from "next/dynamic";
import { type MapProps } from "./Map";

// By doing it this way instead of mapping .then, Next.js perfectly bundles the default export.
const MapDynamic = dynamic(() => import("./Map"), { ssr: false });

export default function OSMapWrapper(props: MapProps) {
    return <MapDynamic {...props} />;
}
