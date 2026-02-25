"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Square } from "lucide-react";
import { Translations } from "@/lib/translations";

export function VoiceControls({ t, onTranscription, currentLang = "en" }: { t: Translations, onTranscription: (text: string) => void, currentLang?: string }) {
  const [isRecording, setIsRecording] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
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

      // @ts-expect-error - SpeechRecognition is not standard in Window yet
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setErrorMsg(t.voiceInputErrorNotSupported);
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

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        onTranscription(transcript);
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onerror = (event: any) => {
        console.error("Speech recognition error", event.error);
        if (event.error !== "no-speech") {
          setErrorMsg(t.voiceInputErrorMicrophone);
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
    <div className="flex flex-col items-center justify-center p-8">
      <div className="relative mb-6">
        {/* Pulsing rings when recording */}
        {isRecording && (
          <>
            <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" style={{ animationDuration: '2s' }} />
            <div className="absolute -inset-4 rounded-full border border-primary/30 animate-pulse" />
            <div className="absolute -inset-8 rounded-full border border-primary/10 animate-pulse" style={{ animationDelay: '0.5s' }} />
          </>
        )}

        <button
          onClick={toggleRecording}
          className={`relative z-10 flex items-center justify-center w-28 h-28 rounded-full shadow-lg transition-transform duration-300 hover:scale-105 ${isRecording
            ? "bg-danger text-white shadow-[0_0_30px_rgba(239,68,68,0.5)]"
            : "bg-primary text-white shadow-[0_10px_40px_rgba(37,99,235,0.3)]"
            }`}
        >
          {isRecording ? (
            <Square className="w-10 h-10 fill-current" />
          ) : (
            <Mic className="w-10 h-10" />
          )}
        </button>
      </div>

      <div className="flex flex-col items-center text-center space-y-2">
        <h3 className="text-xl font-bold text-slate-800 tracking-tight">
          {errorMsg ? "Error" : isRecording ? "Listening..." : "Tap to Speak"}
        </h3>
        <p className={`text-base px-6 ${errorMsg ? 'text-danger' : isRecording ? 'text-primary animate-pulse' : 'text-slate-500'}`}>
          {errorMsg ? errorMsg : isRecording ? "Speak now..." : "Describe your symptoms clearly"}
        </p>
      </div>
    </div>
  );
}
