import { useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  Check,
  LoaderCircle,
  Sparkles,
} from "lucide-react";
import { request, type User } from "./api";

export default function Auth({
  onLogin,
}: {
  onLogin: (token: string, user: User) => void;
}) {
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const fields = new FormData(event.currentTarget);
    const email = String(fields.get("email"));
    const password = String(fields.get("password"));
    try {
      if (register) {
        await request("/auth/register", undefined, "POST", {
          name: fields.get("name"),
          email,
          password,
        });
        setRegister(false);
      }
      const login = await request<{ access_token: string }>(
        "/auth/login",
        undefined,
        "POST",
        { email, password },
      );
      const user = await request<User>("/users/me", login.access_token);
      onLogin(login.access_token, user);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Please try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="auth-layout">
      <section className="auth-story">
        <a className="brand" href="/" aria-label="Second Brain home">
          <span className="brand-mark">
            <BrainCircuit size={25} />
          </span>
          <span>
            second brain<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="story-content">
          <span className="eyebrow">
            <span className="tiny-dot" /> A LITTLE SPACE FOR BIG IDEAS
          </span>
          <h1>
            Less on your mind.
            <br />
            <em>More in your life.</em>
          </h1>
          <p>
            A home for the thoughts you want to keep.
            <br />
            Capture ideas, find connections, and make room
            <br className="desktop-break" /> for what comes next.
          </p>
          <div className="orbit-art" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="art-center">
              <BrainCircuit size={55} />
            </div>
            <div className="floating-card idea">
              <Sparkles size={18} />
              <span>That next big idea</span>
            </div>
            <div className="floating-card memory">
              <span className="art-dot" />
              Worth remembering
            </div>
            <div className="floating-card task">
              <Check size={17} />
              One step forward
            </div>
            <span className="art-star">✳</span>
          </div>
        </div>
        <div className="story-footer">
          <span>YOUR THOUGHTS, CONNECTED.</span>
          <span>
            Made for a clearer mind <ArrowUpRight size={14} />
          </span>
        </div>
      </section>
      <section className="auth-form-side">
        <div className="auth-form-wrap">
          <span className="pill">
            <Sparkles size={13} /> Your personal thinking space
          </span>
          <h2>{register ? "Make room for you." : "Welcome back."}</h2>
          <p className="muted">
            {register
              ? "Start collecting what matters to you."
              : "Your ideas are right where you left them."}
          </p>
          <div className="auth-tabs">
            <button
              className={!register ? "selected" : ""}
              onClick={() => {
                setRegister(false);
                setError("");
              }}
              disabled={busy}
            >
              Sign in
            </button>
            <button
              className={register ? "selected" : ""}
              onClick={() => {
                setRegister(true);
                setError("");
              }}
              disabled={busy}
            >
              Create account
            </button>
          </div>
          <form onSubmit={submit}>
            {register && (
              <label>
                Your name
                <input
                  name="name"
                  autoComplete="name"
                  placeholder="What should we call you?"
                  required
                  maxLength={100}
                />
              </label>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete={register ? "new-password" : "current-password"}
                placeholder={
                  register ? "Choose a password" : "Enter your password"
                }
                required
                maxLength={72}
              />
            </label>
            {register && (
              <small className="muted">
                Use a unique password, up to 72 UTF-8 bytes.
              </small>
            )}
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <button className="primary auth-submit" disabled={busy}>
              {busy ? (
                <LoaderCircle className="spin" size={18} />
              ) : (
                <>
                  {register ? "Create your space" : "Enter your space"}
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
          <div className="auth-footnote">
            <span className="tiny-dot" />A calmer place to think, remember, and
            do.
          </div>
        </div>
      </section>
    </main>
  );
}
