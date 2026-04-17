/**
 * native-bridge.d.ts
 *
 * Shared TypeScript ambient declarations for the MIT App Inventor WebViewer bridge.
 * This prevents type conflicts when multiple files reference window.AppInventor.
 */

interface AppInventorBridge {
    /** Send a string to MIT App Inventor native side (used for TTS, events, etc.) */
    setWebViewString: (text: string) => void;
    /** Read the last string set by MIT App Inventor native side */
    getWebViewString: () => string;
}

declare global {
    interface Window {
        /**
         * Present only when the web app is running inside MIT App Inventor WebViewer.
         * undefined in normal browser environments.
         */
        AppInventor?: AppInventorBridge;

        /**
         * Global function registered by HospitalMap to receive native GPS coordinates
         * sent from MIT App Inventor's LocationSensor via RunJavaScript.
         */
        receiveNativeLocation?: (lat: number | string, lng: number | string) => void;
    }
}

export { };
