import { useCallback, useEffect, useRef, useState } from "react";

export default function useVoiceReply(active: boolean) {
  const supported =
    "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
  const [speaking, setSpeaking] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voiceURI, setVoiceURI] = useState("");
  const [automatic, setAutomatic] = useState(false);
  const utterance = useRef<SpeechSynthesisUtterance | null>(null);
  const stop = useCallback(() => {
    const current = utterance.current;
    utterance.current = null;
    if (current) {
      current.onend = null;
      current.onstart = null;
      current.onerror = null;
      window.speechSynthesis.cancel();
    }
    setSpeaking(null);
    setStatus("");
  }, []);
  useEffect(() => {
    if (!supported) return;
    const update = () => setVoices(window.speechSynthesis.getVoices());
    update();
    window.speechSynthesis.addEventListener("voiceschanged", update);
    const hidden = () => {
      if (document.hidden) stop();
    };
    document.addEventListener("visibilitychange", hidden);
    return () => {
      window.speechSynthesis.removeEventListener("voiceschanged", update);
      document.removeEventListener("visibilitychange", hidden);
      stop();
    };
  }, [supported, stop]);
  useEffect(() => {
    if (!active) stop();
  }, [active, stop]);
  function play(index: number, text: string, started?: () => void) {
    if (!supported || !active || !text.trim()) return;
    stop();
    const next = new SpeechSynthesisUtterance(text);
    const voice = voices.find((v) => v.voiceURI === voiceURI);
    if (voice) {
      next.voice = voice;
      next.lang = voice.lang;
    } else next.lang = navigator.language || "en-IN";
    utterance.current = next;
    next.onstart = () => {
      if (utterance.current === next) started?.();
    };
    next.onend = () => {
      if (utterance.current !== next) return;
      utterance.current = null;
      setSpeaking(null);
      setStatus("Reply finished.");
    };
    next.onerror = () => {
      if (utterance.current !== next) return;
      utterance.current = null;
      setSpeaking(null);
      setStatus(
        "Could not play this reply. Try Listen again or choose another voice.",
      );
    };
    try {
      setSpeaking(index);
      setStatus("Reading reply aloud…");
      window.speechSynthesis.speak(next);
    } catch {
      stop();
      setStatus("Voice playback is unavailable. You can still read the reply.");
    }
  }
  return {
    supported,
    speaking,
    status,
    voices,
    voiceURI,
    setVoiceURI,
    automatic,
    setAutomatic,
    play,
    stop,
  };
}
