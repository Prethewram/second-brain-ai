import { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  BrainCircuit,
  CheckCheck,
  Copy,
  Check,
  Lightbulb,
  LoaderCircle,
  Plus,
  Sparkles,
  Volume2,
  Square,
} from "lucide-react";
import { ApiError } from "./api";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import VoiceInput from "./VoiceInput";
import useVoiceReply from "./useVoiceReply";
import Greeting from "./Greeting";

function Reply({
  text,
  speaking,
  onPlay,
  onStop,
  supported,
}: {
  text: string;
  speaking: boolean;
  onPlay: (text: string) => void;
  onStop: () => void;
  supported: boolean;
}) {
  const content = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timer);
  }, [copied]);
  return (
    <>
      <div className="reply-markdown" ref={content}>
        <Markdown remarkPlugins={[remarkGfm]} skipHtml>
          {text}
        </Markdown>
      </div>
      <div className="reply-actions">
        {supported && (
          <button
            type="button"
            className="copy-reply"
            aria-label={speaking ? "Stop reading reply" : "Listen to reply"}
            onClick={() =>
              speaking ? onStop() : onPlay(content.current?.innerText || text)
            }
          >
            {speaking ? <Square size={14} /> : <Volume2 size={15} />}
            {speaking ? "Stop" : "Listen"}
          </button>
        )}
        <button
          className="copy-reply"
          aria-label="Copy reply"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(text);
              setCopied(true);
              setCopyError(false);
            } catch {
              setCopyError(true);
            }
          }}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? "Copied" : "Copy reply"}
        </button>
        <span role="status">
          {copyError
            ? "Could not copy. Select the text to copy it."
            : copied
              ? "Reply copied"
              : ""}
        </span>
      </div>
    </>
  );
}

type Message = { role: "user" | "assistant"; text: string };
export default function Chat({
  call,
  onUpdated,
  onError,
  userName,
  active,
  userId,
}: {
  call: <T>(path: string, method?: string, body?: unknown) => Promise<T>;
  onUpdated: () => Promise<void>;
  onError: (error: unknown) => void;
  userName: string;
  active: boolean;
  userId: number;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversation, setConversation] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [voiceVersion, setVoiceVersion] = useState(0);
  const bottom = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const voice = useVoiceReply(active);
  const transcript = useRef<HTMLDivElement>(null);
  const processed = useRef(-1);
  useEffect(() => {
    const index = messages.length - 1;
    if (index <= processed.current) return;
    processed.current = index;
    if (messages[index]?.role === "assistant" && voice.automatic && active) {
      const cards =
        transcript.current?.querySelectorAll<HTMLElement>(".reply-markdown");
      const text = cards?.[cards.length - 1]?.innerText;
      if (text) voice.play(index, text);
    }
  }, [messages, active, voice]);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, busy]);
  async function send(event: React.FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    voice.stop();
    setVoiceVersion((version) => version + 1);
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
      if (error instanceof Error && error.name === "AbortError") return;
      if (error instanceof ApiError && error.status === 401) {
        onError(error);
        return;
      }
      if (
        error instanceof ApiError &&
        error.data?.message_saved &&
        Number.isInteger(error.data.conversation_id)
      ) {
        setConversation(error.data.conversation_id!);
        setError(
          `${error.message} Your message was saved. ${error.data.actions_may_be_saved ? "Some extracted actions may already be saved; review your library before repeating them." : "No extracted actions were saved."}`,
        );
        await onUpdated();
      } else {
        const cause =
          error instanceof Error
            ? error.message
            : "Your reply could not be completed.";
        setError(
          `${cause} Your message or extracted actions may already be saved. Review your library before sending again.`,
        );
      }
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
            voice.stop();
            processed.current = -1;
            setConversation(null);
            setError("");
            setDraft("");
            setVoiceVersion((version) => version + 1);
          }}
          disabled={busy}
        >
          <Plus size={15} />
          New conversation
        </button>
      </div>
      <Greeting
        userId={userId}
        name={userName}
        active={active && !busy}
        supported={voice.supported}
        speak={(text, started) => voice.play(-1, text, started)}
      />
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
                    setVoiceVersion((version) => version + 1);
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
          <div className="messages" ref={transcript}>
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
                  {message.role === "assistant" ? (
                    <Reply
                      text={message.text}
                      supported={voice.supported}
                      speaking={voice.speaking === index}
                      onStop={voice.stop}
                      onPlay={(text) => {
                        setVoiceVersion((version) => version + 1);
                        voice.play(index, text);
                      }}
                    />
                  ) : (
                    <p>{message.text}</p>
                  )}
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
        <div className="voice-output-controls">
          {voice.supported ? (
            <>
              <label>
                <input
                  type="checkbox"
                  checked={voice.automatic}
                  onChange={(event) => {
                    voice.setAutomatic(event.target.checked);
                    if (!event.target.checked) voice.stop();
                  }}
                />{" "}
                Read replies aloud
              </label>
              <select
                aria-label="Reply voice"
                value={voice.voiceURI}
                onChange={(event) => {
                  voice.stop();
                  voice.setVoiceURI(event.target.value);
                }}
              >
                <option value="">Default voice</option>
                {voice.voices.map((v) => (
                  <option key={v.voiceURI} value={v.voiceURI}>
                    {v.name} ({v.lang})
                  </option>
                ))}
              </select>
            </>
          ) : (
            <span>Voice replies are unavailable in this browser.</span>
          )}
        </div>
        <p className="voice-status" role="status">
          {voice.status}
        </p>
        <VoiceInput
          key={voiceVersion}
          draft={draft}
          onText={setDraft}
          disabled={busy || !active}
          onStart={voice.stop}
        />
        <textarea
          ref={input}
          aria-label="Message"
          placeholder="Ask about your notes, plan your day, or save a thought…"
          value={draft}
          onChange={(event) => {
            setVoiceVersion((version) => version + 1);
            setDraft(event.target.value);
          }}
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
            <Sparkles size={13} /> Enter to send · Shift + Enter for a new line
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
