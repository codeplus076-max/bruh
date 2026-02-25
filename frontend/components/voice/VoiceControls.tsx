"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Square, Loader2, Volume2 } from "lucide-react";

export function VoiceControls({ onTranscription, currentLang = "en" }: { onTranscription: (text: string) => void, currentLang?: string }) {
  const [isRecording, setIsRecording] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      // Stop recording
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
    } else {
      // Start recording
      setErrorMsg("");

      // @ts-ignore
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setErrorMsg("Voice not supported in this browser");
        return;
      }

      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;

      recognition.continuous = false;
      recognition.interimResults = false;

      if (currentLang === "hi") recognition.lang = "hi-IN";
      else if (currentLang === "mr") recognition.lang = "mr-IN";
      else recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        onTranscription(transcript);
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error", event.error);
        if (event.error !== "no-speech") {
          setErrorMsg("Microphone error");
        }
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      try {
        recognition.start();
      } catch (e) {
        console.error("Failed to start speech recognition", e);
        setIsRecording(false);
      }
    }
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleRecording}
          className={`relative flex items-center justify-center w-12 h-12 rounded-full border transition-all ${isRecording
            ? "bg-danger/20 border-danger text-danger shadow-[0_0_20px_rgba(255,51,102,0.4)] animate-pulse"
            : "bg-surfaceHighlight border-borderDark text-primary hover:bg-primary/10 hover:border-primary/50"
            }`}
        >
          {isRecording ? (
            <Square className="w-4 h-4 fill-current" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>

        <div className="flex flex-col">
          <span className="text-white font-medium text-sm tracking-wide">Voice Input</span>
          <span className={`text-xs ${errorMsg ? 'text-danger' : isRecording ? 'text-danger animate-pulse' : 'text-textMuted'}`}>
            {errorMsg ? errorMsg : isRecording ? "Listening now..." : "Tap to speak your symptoms"}
          </span>
        </div>
      </div>
    </div>
  );
}
