"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Square } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

export function VoiceControls({ onTranscription }: { onTranscription: (text: string) => void }) {
  const { lang, t } = useLanguage();
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

      if (lang === "hi") recognition.lang = "hi-IN";
      else if (lang === "mr") recognition.lang = "mr-IN";
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
          <span className="text-white font-medium text-sm tracking-wide">{t.voiceInputTitle}</span>
          <span className={`text-xs ${errorMsg ? 'text-danger' : isRecording ? 'text-danger animate-pulse' : 'text-textMuted'}`}>
            {errorMsg ? errorMsg : isRecording ? t.voiceInputListening : t.voiceInputTap}
          </span>
        </div>
      </div>
    </div>
  );
}
