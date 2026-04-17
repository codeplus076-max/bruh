/**
 * voiceHandler.ts
 *
 * Cross-Platform AI Voice Output Utility
 * ----------------------------------------
 * This module provides a unified `handleAIVoice(text, lang)` function
 * that dispatches speech output to the correct engine based on the
 * runtime environment:
 *
 *  1. MIT App Inventor (WebViewer): Calls window.AppInventor.setWebViewString(text)
 *     The native Android/iOS side receives this string and passes it
 *     to the Android TextToSpeech engine. No audio API needed in JS.
 *
 *  2. Normal Browser: Uses the Web Speech API (SpeechSynthesisUtterance)
 *     as the direct fallback for reading AI responses aloud.
 *
 * PRIORITY:
 *   Native App (MIT App Inventor) → Browser Speech API → Silent (graceful fail)
 *
 * USAGE:
 *   import { handleAIVoice, cancelAIVoice } from "@/lib/voiceHandler";
 *   handleAIVoice("AI response text here", "en");
 *
 * CLEANUP (on unmount):
 *   cancelAIVoice();
 */

// -------------------------------------------------------------------
// Helpers (Window types centralized in types/native-bridge.d.ts)
// -------------------------------------------------------------------

/** Map our internal lang code → BCP-47 locale tag for Web Speech API */
function toLangTag(lang: string): string {
    if (lang === "hi") return "hi-IN";
    if (lang === "mr") return "mr-IN";
    return "en-US";
}

/** True if we are in a browser context (not SSR) */
function isBrowser(): boolean {
    return typeof window !== "undefined";
}

/** True if running inside MIT App Inventor WebViewer */
function isNativeApp(): boolean {
    return isBrowser() && typeof window.AppInventor !== "undefined";
}

/** True if Web Speech API is available in the current browser */
function hasSpeechSynthesis(): boolean {
    return isBrowser() && "speechSynthesis" in window;
}


// -------------------------------------------------------------------
// cancelAIVoice — stop any in-progress speech
// -------------------------------------------------------------------
export function cancelAIVoice(): void {
    if (!isBrowser()) return;

    // Cancel Web Speech API
    if (hasSpeechSynthesis()) {
        try {
            window.speechSynthesis.cancel();
        } catch {
            // Ignore — cancel can throw in some browsers when nothing is playing
        }
    }

}

// -------------------------------------------------------------------
// handleAIVoice — main entry point
// -------------------------------------------------------------------
/**
 * Speak the given AI response text using the best available voice method.
 *
 * @param text  The text to be spoken (AI response)
 * @param lang  The language code: "en" | "hi" | "mr"
 * @param onEnd Optional callback invoked when speech finishes (browser only)
 * @param onError Optional callback invoked if speech fails
 */
export function handleAIVoice(
    text: string,
    lang: string = "en",
    onEnd?: () => void,
    onError?: (err?: string) => void
): void {
    // --- Safety: never run during SSR ---
    if (!isBrowser()) return;

    // --- Safety: reject empty text ---
    if (!text || !text.trim()) {
        console.warn("[Voice] handleAIVoice called with empty text. Skipping.");
        return;
    }

    // --- Always cancel any ongoing speech first (prevents overlaps) ---
    cancelAIVoice();

    // ================================================================
    // PATH 1: MIT App Inventor — delegate to native Android TTS
    // ================================================================
    if (isNativeApp()) {
        try {
            const bridge = window.AppInventor as { setWebViewString: (t: string) => void };
            bridge.setWebViewString(text);
            console.info("[Voice] ✅ Sent to MIT App Inventor native TTS.");
            // Native completion is not observable from JS; call onEnd immediately
            onEnd?.();
        } catch (err) {
            console.error("[Voice] Failed to send text to AppInventor:", err);
            onError?.("Native TTS failed.");
            // Attempt browser fallback if native fails
            speakWithBrowser(text, lang, onEnd, onError);
        }
        return;
    }

    // ================================================================
    // PATH 2: Web Speech API (browser fallback)
    // ================================================================
    speakWithBrowser(text, lang, onEnd, onError);
}

// -------------------------------------------------------------------
// speakWithBrowser — internal Web Speech API implementation
// -------------------------------------------------------------------
function speakWithBrowser(
    text: string,
    lang: string,
    onEnd?: () => void,
    onError?: (err?: string) => void
): void {
    if (!hasSpeechSynthesis()) {
        console.warn("[Voice] Web Speech API not supported in this browser.");
        onError?.("Speech synthesis unavailable.");
        return;
    }

    try {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = toLangTag(lang);
        utterance.rate = 0.95;   // Slightly slower — clearer for medical content
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        utterance.onend = () => {
            onEnd?.();
        };

        utterance.onerror = (event) => {
            // "interrupted" fires when cancel() is called; not a real error
            if (event.error === "interrupted") {
                return; // cancel() was called — not a real error, ignore silently
            }
            console.error("[Voice] SpeechSynthesisUtterance error:", event.error);
            onError?.(event.error);
        };

        window.speechSynthesis.speak(utterance);
        console.info("[Voice] ✅ Speaking via Web Speech API in:", utterance.lang);

    } catch (err) {
        console.error("[Voice] Unexpected error launching speech:", err);
        onError?.("Unexpected speech error.");
    }
}
