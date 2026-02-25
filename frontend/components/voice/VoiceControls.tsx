"use client";

import { useState } from "react";
import { Mic, Square, Loader2, Volume2 } from "lucide-react";

export function VoiceControls({ onTranscription }: { onTranscription: (text: string) => void }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      setIsProcessing(true);
      // Mock processing delay
      setTimeout(() => {
        setIsProcessing(false);
        onTranscription("Patient reports mild fever and persistent cough for 3 days.");
      }, 1500);
    } else {
      setIsRecording(true);
    }
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleRecording}
          disabled={isProcessing}
          className={`relative flex items-center justify-center w-12 h-12 rounded-full border transition-all ${isRecording
              ? "bg-danger/20 border-danger text-danger shadow-[0_0_20px_rgba(255,51,102,0.4)] animate-pulse"
              : "bg-surfaceHighlight border-borderDark text-primary hover:bg-primary/10 hover:border-primary/50"
            } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
          ) : isRecording ? (
            <Square className="w-4 h-4 fill-current" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>

        <div className="flex flex-col">
          <span className="text-white font-medium text-sm tracking-wide">Voice Input</span>
          <span className={`text-xs ${isRecording ? 'text-danger animate-pulse' : isProcessing ? 'text-primary' : 'text-textMuted'}`}>
            {isRecording ? "Listening..." : isProcessing ? "Processing audio..." : "Tap to speak symptoms"}
          </span>
        </div>
      </div>

      <button className="p-3 rounded-full bg-surfaceHighlight border border-borderDark text-textMuted hover:text-white transition-colors" title="Read responses aloud">
        <Volume2 className="w-4 h-4" />
      </button>
    </div>
  );
}
