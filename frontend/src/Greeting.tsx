import { useEffect, useRef, useState } from "react";
import { Volume2 } from "lucide-react";

export function greetingAt(date: Date) {
  const hour = date.getHours();
  const period = hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening";
  const day = `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
  return { period, token: `${day}:${period}`, text: `Good ${period}` };
}

export default function Greeting({
  userId,
  name,
  active,
  supported,
  speak,
}: {
  userId: number;
  name: string;
  active: boolean;
  supported: boolean;
  speak: (text: string, started: () => void) => void;
}) {
  const [now, setNow] = useState(() => new Date());
  const attempted = useRef("");
  const greeting = greetingAt(now);
  const text = `${greeting.text}, ${name.trim() || "friend"}.`;
  const key = `second-brain-greeting:${userId}`;
  const record = () => {
    try {
      sessionStorage.setItem(key, greeting.token);
    } catch {
      /* Greeting remains usable without storage. */
    }
  };
  useEffect(() => {
    const update = () => setNow(new Date());
    update();
    const timer = window.setInterval(update, 30000);
    const visible = () => {
      if (!document.hidden) update();
    };
    document.addEventListener("visibilitychange", visible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [active]);
  useEffect(() => {
    if (
      !active ||
      !supported ||
      document.hidden ||
      attempted.current === greeting.token
    )
      return;
    let previous = "";
    try {
      previous = sessionStorage.getItem(key) || "";
    } catch {
      /* Storage is optional. */
    }
    attempted.current = greeting.token;
    if (previous !== greeting.token) speak(text, record);
  }, [active, supported, greeting.token, key, text, speak]);
  return (
    <div className="personal-greeting">
      <div>
        <span className="eyebrow">WELCOME TO YOUR THINKING SPACE</span>
        <h2>
          {greeting.text}, <span>{name.trim() || "friend"}.</span>
        </h2>
      </div>
      {supported && (
        <button
          type="button"
          className="text-button"
          aria-label="Hear greeting"
          onClick={() => speak(text, record)}
        >
          <Volume2 size={16} /> Hear greeting
        </button>
      )}
    </div>
  );
}
