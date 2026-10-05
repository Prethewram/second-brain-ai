import { useEffect, useRef, useState } from "react";
import { Mic, Square } from "lucide-react";

type Recognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult:
    | ((event: {
        results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }>;
      }) => void)
    | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
type VoiceWindow = Window & {
  SpeechRecognition?: new () => Recognition;
  webkitSpeechRecognition?: new () => Recognition;
};

export default function VoiceInput({
  draft,
  onText,
  disabled,
}: {
  draft: string;
  onText: (text: string) => void;
  disabled: boolean;
}) {
  const recognition = useRef<Recognition | null>(null);
  const [listening, setListening] = useState(false);
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("en-IN");
  const Constructor =
    (window as VoiceWindow).SpeechRecognition ||
    (window as VoiceWindow).webkitSpeechRecognition;
  function cancel() {
    const current = recognition.current;
    recognition.current = null;
    if (current) {
      current.onresult = null;
      current.onerror = null;
      current.onend = null;
      current.abort();
    }
  }
  useEffect(() => () => cancel(), []);
  useEffect(() => {
    if (disabled) {
      cancel();
      setListening(false);
      setStatus("");
    }
  }, [disabled]);
  useEffect(() => {
    const hidden = () => {
      if (document.hidden) {
        cancel();
        setListening(false);
        setStatus("Microphone stopped. Review your text before sending.");
      }
    };
    document.addEventListener("visibilitychange", hidden);
    return () => document.removeEventListener("visibilitychange", hidden);
  }, []);
  function start() {
    if (!Constructor || disabled) return;
    const current = new Constructor();
    recognition.current = current;
    const prefix = draft.trim();
    let heard = false;
    let failed = false;
    current.lang = language;
    current.continuous = true;
    current.interimResults = true;
    current.onresult = (event) => {
      if (recognition.current !== current) return;
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ")
        .trim();
      heard = Boolean(transcript);
      onText([prefix, transcript].filter(Boolean).join(" ").slice(0, 12000));
    };
    current.onerror = (event) => {
      failed = true;
      const errors: Record<string, string> = {
        "not-allowed":
          "Microphone permission denied. Allow microphone access in your browser and try again.",
        "service-not-allowed":
          "Speech recognition is unavailable in this browser. Try another browser or type your command.",
        "audio-capture":
          "No microphone is available. Connect a microphone and try again.",
        "no-speech": "No speech detected. Try again when you are ready.",
        network:
          "Speech recognition could not connect. Check your connection and try again.",
        "language-not-supported":
          "This speech language is unavailable. Choose another language.",
      };
      setStatus(
        errors[event.error] ||
          "Voice input stopped. Your text is kept; you can type or try again.",
      );
    };
    current.onend = () => {
      if (recognition.current !== current) return;
      recognition.current = null;
      setListening(false);
      if (!failed)
        setStatus(
          heard
            ? "Voice captured. Review your command, then send."
            : "No speech captured. Try again or type your command.",
        );
    };
    try {
      current.start();
      setListening(true);
      setStatus("Listening… Speak your command. Tap stop when finished.");
    } catch {
      cancel();
      setListening(false);
      setStatus("Could not start voice input. Try again or type your command.");
    }
  }
  return (
    <div className="voice-input">
      <div className="voice-controls">
        <button
          type="button"
          className={`voice-button ${listening ? "listening" : ""}`}
          aria-label={listening ? "Stop voice input" : "Start voice input"}
          aria-pressed={listening}
          disabled={disabled || !Constructor}
          onClick={() => (listening ? recognition.current?.stop() : start())}
        >
          {listening ? <Square size={15} /> : <Mic size={17} />}
          {listening ? "Stop" : "Voice"}
        </button>
        {Constructor && (
          <select
            aria-label="Voice language"
            value={language}
            disabled={disabled || listening}
            onChange={(event) => setLanguage(event.target.value)}
          >
            <option value="en-IN">English (India)</option>
            <option value="en-US">English (US)</option>
            <option value="hi-IN">Hindi</option>
            <option value="ta-IN">Tamil</option>
          </select>
        )}
      </div>
      <p role="status" className="voice-status">
        {Constructor
          ? status || "Speak to draft a command. Review it before sending."
          : "Voice input is unavailable in this browser. You can still type your command."}
      </p>
      {Constructor && (
        <small className="voice-privacy">
          Your browser handles speech recognition and may use an online service.
        </small>
      )}
    </div>
  );
}
