export interface SpeechRecognitionResultAlternative {
    transcript: string;
    confidence: number;
}

export interface ISpeechRecognitionResult {
    [index: number]: SpeechRecognitionResultAlternative;
    length: number;
    isFinal: boolean;
}

export interface ISpeechRecognitionResultList {
    [index: number]: ISpeechRecognitionResult;
    length: number;
}

export interface ISpeechRecognitionEvent extends Event {
    results: ISpeechRecognitionResultList;
    resultIndex: number;
}

export interface ISpeechRecognitionErrorEvent extends Event {
    error: string;
    message: string;
}

export interface ISpeechRecognition extends EventTarget {
    lang: string;
    continuous: boolean;
    interimResults: boolean;
    maxAlternatives: number;
    start(): void;
    stop(): void;
    abort(): void;
    onresult: ((event: ISpeechRecognitionEvent) => void) | null;
    onerror: ((event: ISpeechRecognitionErrorEvent) => void) | null;
    onend: (() => void) | null;
    onspeechstart: (() => void) | null;
    onspeechend: (() => void) | null;
}

declare global {
    interface Window {
        SpeechRecognition?: { new(): ISpeechRecognition };
        webkitSpeechRecognition?: { new(): ISpeechRecognition };
    }
}
