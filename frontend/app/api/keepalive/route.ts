import { NextResponse } from "next/server";

export async function GET() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "https://bruh-1-u248.onrender.com";

    try {
        const res = await fetch(`${backendUrl}/health`, {
            cache: "no-store",
            signal: AbortSignal.timeout(10000),
        });
        const data = await res.json();
        return NextResponse.json({ pinged: true, backend: data }, { status: 200 });
    } catch (err) {
        console.error("[Keepalive] Failed to ping backend:", err);
        return NextResponse.json({ pinged: false, error: String(err) }, { status: 500 });
    }
}
