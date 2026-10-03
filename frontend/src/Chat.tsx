import { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  BrainCircuit,
  CheckCheck,
  Lightbulb,
  LoaderCircle,
  Plus,
  Sparkles,
} from "lucide-react";
import { ApiError } from "./api";

type Message = { role: "user" | "assistant"; text: string };
export default function Chat({
  call,
  onUpdated,
  onError,
  userName,
}: {
  call: <T>(path: string, method?: string, body?: unknown) => Promise<T>;
  onUpdated: () => Promise<void>;
  onError: (error: unknown) => void;
  userName: string;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversation, setConversation] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, busy]);
  async function send(event: React.FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    setError("");
    setBusy(true);
    setMessages((previous) => [...previous, { role: "user", text }]);
    try {
      const reply = await call<{ conversation_id: number; response: string }>(
        "/chat",
        "POST",
        { message: text, conversation_id: conversation },
      );
      setConversation(reply.conversation_id);
      setMessages((previous) => [
        ...previous,
        { role: "assistant", text: reply.response },
      ]);
      await onUpdated();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) onError(error);
      setError(
        "Your reply could not be completed. Your message or extracted actions may already be saved. Check your connection before sending again.",
      );
    } finally {
      setBusy(false);
      input.current?.focus();
    }
  }
  const prompts = [
    {
      icon: BrainCircuit,
      title: "Remember something",
      text: "Remember that I prefer morning meetings.",
    },
    {
      icon: Lightbulb,
      title: "Save a fresh idea",
      text: "Create a note called Weekend ideas with a plan to explore a new walking route.",
    },
    {
      icon: CheckCheck,
      title: "Make a little progress",
      text: "Create a task to plan my week with medium priority.",
    },
  ];
  return (
    <section className="chat-panel">
      <div className="panel-top">
        <span>
          <span className="tiny-dot" /> Your personal AI space
        </span>
        <button
          className="text-button"
          onClick={() => {
            setMessages([]);
            setConversation(null);
            setError("");
            setDraft("");
          }}
          disabled={busy}
        >
          <Plus size={15} />
          New conversation
        </button>
      </div>
      <div className="chat-scroll">
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="welcome-mark">
              <Sparkles size={31} />
            </div>
            <span className="eyebrow">CLEAR YOUR MIND</span>
            <h2>
              What’s on your mind,
              <br />
              <em>{userName.split(" ")[0]}?</em>
            </h2>
            <p>
              Big ideas. Small reminders. Half-formed thoughts.
              <br />
              There’s room for all of them here.
            </p>
            <div className="prompt-grid">
              {prompts.map((prompt) => (
                <button
                  key={prompt.title}
                  className="prompt-card"
                  onClick={() => {
                    setDraft(prompt.text);
                    input.current?.focus();
                  }}
                >
                  <prompt.icon size={20} />
                  <span>{prompt.title}</span>
                  <span className="prompt-arrow">↗</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message, index) => (
              <div className={`message ${message.role}`} key={index}>
                {message.role === "assistant" && (
                  <span className="message-avatar">
                    <Sparkles size={16} />
                  </span>
                )}
                <div>
                  <span className="message-name">
                    {message.role === "user" ? "You" : "Second Brain"}
                  </span>
                  <p>{message.text}</p>
                </div>
              </div>
            ))}
            {busy && (
              <div className="thinking" role="status">
                <LoaderCircle size={15} className="spin" />
                Connecting the dots…
              </div>
            )}
          </div>
        )}
        <div ref={bottom} />
      </div>
      {error && (
        <p className="form-error chat-error" role="alert">
          {error}
        </p>
      )}
      <form className="composer" onSubmit={send}>
        <textarea
          ref={input}
          aria-label="Message"
          placeholder="Leave a thought here…"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          maxLength={12000}
          rows={2}
          disabled={busy}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              void send(event);
            }
          }}
        />
        <div className="composer-bottom">
          <span>
            <Sparkles size={13} /> A thought today. A connection tomorrow.
          </span>
          <button
            className="send-button"
            aria-label="Send message"
            disabled={busy || !draft.trim()}
          >
            {busy ? (
              <LoaderCircle className="spin" size={18} />
            ) : (
              <ArrowUp size={20} />
            )}
          </button>
        </div>
      </form>
      <small className="chat-disclaimer">
        AI can make mistakes. Review important information in your library.
      </small>
    </section>
  );
}
