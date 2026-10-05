import { useCallback, useEffect, useRef, useState } from "react";
import {
  Archive,
  ArrowRight,
  ArrowUpRight,
  BrainCircuit,
  Check,
  CheckCheck,
  ChevronRight,
  Circle,
  FileText,
  Layers,
  LoaderCircle,
  LogOut,
  MessageSquare,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  UserRound,
  X,
} from "lucide-react";
import Auth from "./Auth";
import Meetings from "./Meetings";
import Chat from "./Chat";
import Editor, { type EditorState } from "./Editor";
import {
  ApiError,
  emptyCollections,
  loadCollections,
  profileFields,
  request,
  type Collections,
  type Profile,
  type User,
} from "./api";

type View = "chat" | "notes" | "tasks" | "memories" | "profile" | "meetings";
const navigation = [
  { id: "chat", label: "Thinking space", icon: MessageSquare },
  { id: "notes", label: "Notes", icon: FileText },
  { id: "tasks", label: "Tasks", icon: CheckCheck },
  { id: "meetings", label: "Meetings / MOM", icon: FileText },
  { id: "memories", label: "Memories", icon: BrainCircuit },
  { id: "profile", label: "My profile", icon: UserRound },
] as const;
const headings: Record<View, { title: string; description: string }> = {
  meetings: {
    title: "Meetings with a next step",
    description: "Keep minutes, decisions, notes, and tasks together.",
  },
  chat: {
    title: "Your thinking space",
    description: "Let it out. We’ll help you connect the dots.",
  },
  notes: {
    title: "A library of ideas",
    description: "Give your thoughts a place to grow.",
  },
  tasks: {
    title: "One step at a time",
    description: "Turn the things on your mind into things you do.",
  },
  memories: {
    title: "Worth remembering",
    description: "The little details that make your world yours.",
  },
  profile: {
    title: "A little about you",
    description: "Help your second brain understand your world.",
  },
};

export default function App() {
  const [token, setToken] = useState(
    () => sessionStorage.getItem("second-brain-token") ?? "",
  );
  const [user, setUser] = useState<User | null>(null);
  const [booting, setBooting] = useState(Boolean(token));
  const [view, setView] = useState<View>("chat");
  const [data, setData] = useState<Collections>(emptyCollections);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("active");
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [working, setWorking] = useState(false);
  const [deletion, setDeletion] = useState<{
    path: string;
    title: string;
  } | null>(null);
  const deleteDialog = useRef<HTMLDialogElement>(null);
  const generation = useRef(0);
  const activeToken = useRef(token);
  activeToken.current = token;
  const logout = useCallback(() => {
    generation.current++;
    activeToken.current = "";
    sessionStorage.removeItem("second-brain-token");
    setToken("");
    setUser(null);
    setData(emptyCollections);
    setLoaded(false);
    setLoading(false);
    setError("");
    setEditor(null);
    setDeletion(null);
    setView("chat");
    setSearch("");
    setNotice("");
  }, []);
  const handleError = useCallback(
    (error: unknown) => {
      if (error instanceof Error && error.name === "AbortError") return;
      if (error instanceof ApiError && error.status === 401) {
        logout();
        setError("Your session expired. Please sign in again.");
      } else
        setError(
          error instanceof Error
            ? error.message
            : "Something went wrong. Please try again.",
        );
    },
    [logout],
  );
  const call = useCallback(
    async <T,>(path: string, method = "GET", body?: unknown): Promise<T> => {
      try {
        const result = await request<T>(path, token, method, body);
        if (activeToken.current !== token)
          throw new DOMException("Session changed", "AbortError");
        return result;
      } catch (error) {
        if (activeToken.current !== token)
          throw new DOMException("Session changed", "AbortError");
        if (error instanceof ApiError && error.status === 401)
          handleError(error);
        throw error;
      }
    },
    [token, handleError],
  );
  const refresh = useCallback(async () => {
    if (!token || activeToken.current !== token) return;
    const current = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const next = await loadCollections(token);
      if (generation.current === current && activeToken.current === token) {
        setData(next);
        setLoaded(true);
      }
    } catch (error) {
      if (generation.current === current) handleError(error);
    } finally {
      if (generation.current === current) setLoading(false);
    }
  }, [token, handleError]);
  useEffect(() => {
    if (!token || user) {
      setBooting(false);
      return;
    }
    const controller = new AbortController();
    setBooting(true);
    request<User>("/users/me", token, "GET", undefined, controller.signal)
      .then(setUser)
      .catch((error) => {
        if (error.name !== "AbortError") {
          logout();
          setError(
            error instanceof ApiError && error.status === 401
              ? "Your session expired. Please sign in again."
              : error.message,
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setBooting(false);
      });
    return () => controller.abort();
  }, [token, user, logout]);
  useEffect(() => {
    if (user && token) void refresh();
  }, [user, token, refresh]);
  useEffect(() => {
    if (deletion) deleteDialog.current?.showModal();
  }, [deletion]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(""), 4000);
    return () => clearTimeout(timer);
  }, [notice]);
  function navigate(next: View) {
    setView(next);
    setSearch("");
    setFilter("active");
    setNotice("");
  }
  async function save(method: string, path: string, payload?: unknown) {
    await call(path, method, payload);
    setNotice("Saved to your space.");
    await refresh();
  }
  async function action(path: string, method = "PATCH", payload?: unknown) {
    setWorking(true);
    try {
      await save(method, path, payload);
      setDeletion(null);
    } catch (error) {
      handleError(error);
    } finally {
      setWorking(false);
    }
  }
  if (booting)
    return (
      <div className="boot-screen" role="status">
        <BrainCircuit size={40} />
        <p>Opening your space…</p>
        <LoaderCircle className="spin" size={20} />
      </div>
    );
  if (!user)
    return (
      <>
        {error && (
          <div className="session-banner" role="alert">
            {error}
            <button aria-label="Dismiss message" onClick={() => setError("")}>
              <X size={16} />
            </button>
          </div>
        )}
        <Auth
          onLogin={(nextToken, nextUser) => {
            sessionStorage.setItem("second-brain-token", nextToken);
            setError("");
            setToken(nextToken);
            setUser(nextUser);
          }}
        />
      </>
    );
  const activeTasks = data.tasks.filter((task) => !task.completed);
  const activeNotes = data.notes.filter((note) => !note.is_archived);
  const query = search.toLowerCase().trim();
  const counts: Partial<Record<View, number>> = {
    notes: activeNotes.length,
    tasks: activeTasks.length,
    memories: data.memories.length,
  };
  const match = (...values: (string | null)[]) =>
    values.join(" ").toLowerCase().includes(query);
  const notes = data.notes.filter(
    (note) =>
      (filter === "all" ||
        (filter === "archived" ? note.is_archived : !note.is_archived)) &&
      match(note.title, note.content, note.category),
  );
  const tasks = data.tasks.filter(
    (task) =>
      (filter === "all" ||
        (filter === "completed" ? task.completed : !task.completed)) &&
      match(task.title, task.description, task.priority),
  );
  const memories = data.memories.filter((memory) =>
    match(memory.content, memory.category),
  );
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <a
          href="/"
          className="brand"
          onClick={(event) => {
            event.preventDefault();
            navigate("chat");
          }}
        >
          <span className="brand-mark">
            <BrainCircuit size={24} />
          </span>
          <span>
            second brain<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="workspace-label">
          <span className="workspace-avatar">
            {user.name[0]?.toUpperCase()}
          </span>
          <div>
            <strong>Personal workspace</strong>
            <span>A little more headspace</span>
          </div>
        </div>
        <span className="nav-caption">YOUR SPACE</span>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "nav-item active" : "nav-item"}
              onClick={() => navigate(item.id)}
              aria-current={view === item.id ? "page" : undefined}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
              {counts[item.id] !== undefined && (
                <span className="nav-count">
                  {loaded ? counts[item.id] : "–"}
                </span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="note-star">✳</span>
            <h3>
              Your mind is for
              <br />
              having ideas.
            </h3>
            <p>Let this space hold onto them.</p>
          </div>
          <div className="user-menu">
            <span className="user-avatar">{user.name[0]?.toUpperCase()}</span>
            <div>
              <strong>{user.name}</strong>
              <span>{user.email}</span>
            </div>
            <button
              aria-label="Sign out"
              title="Sign out"
              className="icon-button"
              onClick={logout}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            My workspace <ChevronRight size={13} />
            <span>{navigation.find((item) => item.id === view)?.label}</span>
          </div>
          <span className="topbar-badge">
            <span className="tiny-dot" /> A place to think clearly
          </span>
        </header>
        <div className="page-heading">
          <div>
            <span className="eyebrow">YOUR SECOND BRAIN</span>
            <h1>
              {headings[view].title}
              <span className="heading-dot">.</span>
            </h1>
            <p>{headings[view].description}</p>
          </div>
          <button
            className="secondary refresh-button"
            aria-label="Refresh library"
            onClick={() => void refresh()}
            disabled={loading}
          >
            <RefreshCw className={loading ? "spin" : ""} size={16} />
            <span>Refresh</span>
          </button>
        </div>
        {error && (
          <div className="error-banner" role="alert">
            <span>{error}</span>
            <button onClick={() => void refresh()} disabled={loading}>
              Try again
            </button>
            <button
              aria-label="Dismiss error"
              className="icon-button"
              onClick={() => setError("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
        {notice && (
          <div className="toast" role="status">
            <Check size={16} />
            {notice}
          </div>
        )}
        <div className={view === "chat" ? "chat-layout" : "hidden"}>
          <Chat
            key={user.id}
            call={call}
            onUpdated={refresh}
            onError={handleError}
            userName={user.name}
            userId={user.id}
            active={view === "chat"}
          />
          <aside className="context-rail">
            <div className="rail-heading">
              <Layers size={17} />
              <span>YOUR WORLD, AT A GLANCE</span>
            </div>
            <div className="library-stats">
              <button onClick={() => navigate("notes")}>
                <span className="stat-icon sand">
                  <FileText size={18} />
                </span>
                <strong>{loaded ? activeNotes.length : "–"}</strong>
                <span>Ideas captured</span>
                <ArrowUpRight size={16} />
              </button>
              <button onClick={() => navigate("tasks")}>
                <span className="stat-icon mint">
                  <CheckCheck size={18} />
                </span>
                <strong>{loaded ? activeTasks.length : "–"}</strong>
                <span>Next steps</span>
                <ArrowUpRight size={16} />
              </button>
              <button onClick={() => navigate("memories")}>
                <span className="stat-icon lavender">
                  <BrainCircuit size={18} />
                </span>
                <strong>{loaded ? data.memories.length : "–"}</strong>
                <span>Things remembered</span>
                <ArrowUpRight size={16} />
              </button>
            </div>
            <div className="rail-section">
              <div className="section-title">
                <h3>A little focus</h3>
                <button
                  className="text-button"
                  onClick={() => navigate("tasks")}
                >
                  View all <ArrowRight size={13} />
                </button>
              </div>
              {!loaded ? (
                <p className="muted">
                  {loading
                    ? "Loading your next steps…"
                    : "Refresh to load your library."}
                </p>
              ) : activeTasks.length ? (
                activeTasks.slice(0, 3).map((task) => (
                  <div className="focus-task" key={task.id}>
                    <Circle size={15} />
                    <span>{task.title}</span>
                  </div>
                ))
              ) : (
                <div className="rail-empty">
                  <CheckCheck size={24} />
                  <p>
                    A clear slate.
                    <br />
                    Add a task when inspiration strikes.
                  </p>
                </div>
              )}
            </div>
            <div className="connection-card">
              <Sparkles size={20} />
              <h3>
                Small thoughts.
                <br />
                Bigger connections.
              </h3>
              <p>
                Tell your thinking space something worth remembering. Your
                library grows with you.
              </p>
              <span>
                MAKE ROOM FOR POSSIBILITY <ArrowUpRight size={14} />
              </span>
            </div>
          </aside>
        </div>
        {view !== "chat" && view !== "profile" && view !== "meetings" && (
          <section className="library">
            <div className="library-toolbar">
              <div
                className="filter-tabs"
                role="group"
                aria-label="Filter items"
              >
                {(view === "notes"
                  ? ["active", "archived", "all"]
                  : view === "tasks"
                    ? ["active", "completed", "all"]
                    : ["all"]
                ).map((tab) => (
                  <button
                    key={tab}
                    className={
                      view === "memories" || filter === tab ? "selected" : ""
                    }
                    onClick={() => setFilter(tab)}
                  >
                    {tab === "active"
                      ? view === "notes"
                        ? "My notes"
                        : "To do"
                      : tab === "all"
                        ? "All"
                        : tab[0].toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>
              <div className="toolbar-right">
                <label className="search-field">
                  <Search size={16} />
                  <input
                    aria-label={`Search ${view}`}
                    placeholder={`Search ${view}…`}
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </label>
                {view !== "memories" && (
                  <button
                    className="primary"
                    onClick={() =>
                      setEditor(
                        view === "notes"
                          ? { kind: "notes" }
                          : { kind: "tasks" },
                      )
                    }
                  >
                    <Plus size={16} />
                    New {view === "notes" ? "note" : "task"}
                  </button>
                )}
              </div>
            </div>
            {loading && !loaded ? (
              <div className="empty-state" role="status">
                <LoaderCircle className="spin" />
                <h2>Gathering your thoughts…</h2>
              </div>
            ) : !loaded ? (
              <Empty
                title="Your library is taking a moment"
                text="Refresh to try loading your saved items again."
              />
            ) : (
              <>
                {view === "notes" &&
                  (notes.length ? (
                    <div className="note-grid">
                      {notes.map((note, index) => (
                        <article
                          className={`note-card tone-${index % 3}`}
                          key={note.id}
                        >
                          <div className="card-meta">
                            <span className="category">{note.category}</span>
                            <FileText size={17} />
                          </div>
                          <h2>{note.title}</h2>
                          <p className="note-content">{note.content}</p>
                          <div className="card-footer">
                            <span>
                              {note.is_archived
                                ? "Archived"
                                : note.source === "chat"
                                  ? "From your thinking space"
                                  : "In your library"}
                            </span>
                            <div className="card-actions">
                              <button
                                className="icon-button"
                                aria-label={`Edit ${note.title}`}
                                onClick={() =>
                                  setEditor({ kind: "notes", item: note })
                                }
                              >
                                <Pencil size={15} />
                              </button>
                              <button
                                className="icon-button"
                                aria-label={
                                  note.is_archived
                                    ? `Restore ${note.title}`
                                    : `Archive ${note.title}`
                                }
                                disabled={working}
                                onClick={() =>
                                  void action(`/notes/${note.id}`, "PATCH", {
                                    is_archived: !note.is_archived,
                                  })
                                }
                              >
                                <Archive size={15} />
                              </button>
                              <button
                                className="icon-button"
                                aria-label={`Delete ${note.title}`}
                                onClick={() =>
                                  setDeletion({
                                    path: `/notes/${note.id}`,
                                    title: note.title,
                                  })
                                }
                              >
                                <Trash2 size={15} />
                              </button>
                            </div>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <Empty
                      icon="notes"
                      title={
                        query
                          ? "No matching notes"
                          : "Every idea starts somewhere"
                      }
                      text={
                        query
                          ? "Try another search or filter."
                          : "Capture a thought, a plan, or a spark of inspiration."
                      }
                      action={
                        !query ? () => setEditor({ kind: "notes" }) : undefined
                      }
                      actionLabel="Write your first note"
                    />
                  ))}
                {view === "tasks" &&
                  (tasks.length ? (
                    <div className="task-list">
                      {tasks.map((task) => (
                        <article
                          className={`task-row ${task.completed ? "completed" : ""}`}
                          key={task.id}
                        >
                          <button
                            className="task-check"
                            aria-label={
                              task.completed
                                ? `${task.title} completed`
                                : `Complete ${task.title}`
                            }
                            disabled={working || task.completed}
                            onClick={() =>
                              void action(`/tasks/${task.id}/complete`)
                            }
                          >
                            {task.completed && <Check size={15} />}
                          </button>
                          <div className="task-text">
                            <h2>{task.title}</h2>
                            {task.description && <p>{task.description}</p>}
                            {task.deadline && (
                              <span className="deadline">
                                Due: {task.deadline}
                              </span>
                            )}
                          </div>
                          <span className={`priority ${task.priority}`}>
                            {task.priority}
                          </span>
                          <button
                            className="icon-button"
                            aria-label={`Edit ${task.title}`}
                            onClick={() =>
                              setEditor({ kind: "tasks", item: task })
                            }
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            className="icon-button"
                            aria-label={`Delete ${task.title}`}
                            onClick={() =>
                              setDeletion({
                                path: `/tasks/${task.id}`,
                                title: task.title,
                              })
                            }
                          >
                            <Trash2 size={16} />
                          </button>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <Empty
                      icon="tasks"
                      title={
                        query
                          ? "No matching tasks"
                          : filter === "completed"
                            ? "Progress lives here"
                            : "Make space for your next step"
                      }
                      text={
                        query
                          ? "Try another search or filter."
                          : filter === "completed"
                            ? "Completed tasks will appear here."
                            : "A small action is a good place to start."
                      }
                      action={
                        !query && filter !== "completed"
                          ? () => setEditor({ kind: "tasks" })
                          : undefined
                      }
                      actionLabel="Add a task"
                    />
                  ))}
                {view === "memories" && (
                  <>
                    <div className="memory-tip">
                      <Sparkles size={17} />
                      <span>
                        Memories grow through conversation. Tell your thinking
                        space what to remember.
                      </span>
                      <button
                        className="text-button"
                        onClick={() => navigate("chat")}
                      >
                        Start a thought <ArrowRight size={14} />
                      </button>
                    </div>
                    {memories.length ? (
                      <div className="note-grid">
                        {memories.map((memory) => (
                          <article className="memory-card" key={memory.id}>
                            <div className="card-meta">
                              <span className="category">
                                {memory.category}
                              </span>
                              <BrainCircuit size={18} />
                            </div>
                            <p>{memory.content}</p>
                            <div className="card-footer">
                              <span>Importance · {memory.importance}</span>
                              <div className="card-actions">
                                <button
                                  className="icon-button"
                                  aria-label={`Edit memory ${memory.id}`}
                                  onClick={() =>
                                    setEditor({
                                      kind: "memories",
                                      item: memory,
                                    })
                                  }
                                >
                                  <Pencil size={15} />
                                </button>
                                <button
                                  className="icon-button"
                                  aria-label={`Delete memory ${memory.id}`}
                                  onClick={() =>
                                    setDeletion({
                                      path: `/memory/${memory.id}`,
                                      title: "this memory",
                                    })
                                  }
                                >
                                  <Trash2 size={15} />
                                </button>
                              </div>
                            </div>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <Empty
                        icon="memories"
                        title={
                          query
                            ? "No matching memories"
                            : "Your story, one detail at a time"
                        }
                        text={
                          query
                            ? "Try another search."
                            : "Share a preference, a goal, or something you want to keep."
                        }
                        action={!query ? () => navigate("chat") : undefined}
                        actionLabel="Open your thinking space"
                      />
                    )}
                  </>
                )}
              </>
            )}
          </section>
        )}
        {view === "meetings" && (
          <Meetings call={call} onUpdated={refresh} refreshKey={data} />
        )}
        {view === "profile" && (
          <ProfileForm
            key={data.profile ? JSON.stringify(data.profile) : "new"}
            profile={data.profile}
            disabled={loading || !loaded}
            onSave={(payload) => save("PATCH", "/profile", payload)}
            onDelete={() =>
              setDeletion({ path: "/profile", title: "your profile" })
            }
          />
        )}
        <footer className="workspace-footer">
          <span>
            <BrainCircuit size={13} /> Second Brain
          </span>
          <span>A little less to hold. A little more to discover.</span>
        </footer>
      </main>
      {editor && (
        <Editor editor={editor} onClose={() => setEditor(null)} onSave={save} />
      )}
      {deletion && (
        <dialog
          ref={deleteDialog}
          className="editor confirm-dialog"
          onCancel={(event) => {
            event.preventDefault();
            if (!working) setDeletion(null);
          }}
          aria-labelledby="delete-title"
        >
          <span className="delete-icon">
            <Trash2 size={23} />
          </span>
          <h2 id="delete-title">Delete {deletion.title}?</h2>
          <p className="muted">
            This removes it from your library. This action cannot be undone.
          </p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="dialog-actions">
            <button
              className="secondary"
              disabled={working}
              onClick={() => setDeletion(null)}
            >
              Keep it
            </button>
            <button
              className="danger"
              disabled={working}
              onClick={() => void action(deletion.path, "DELETE")}
            >
              {working ? <LoaderCircle className="spin" size={16} /> : "Delete"}
            </button>
          </div>
        </dialog>
      )}
    </div>
  );
}

function Empty({
  title,
  text,
  icon = "notes",
  action,
  actionLabel,
}: {
  title: string;
  text: string;
  icon?: string;
  action?: () => void;
  actionLabel?: string;
}) {
  const Icon =
    icon === "tasks"
      ? CheckCheck
      : icon === "memories"
        ? BrainCircuit
        : FileText;
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon size={31} />
      </span>
      <h2>{title}</h2>
      <p>{text}</p>
      {action && (
        <button className="primary" onClick={action}>
          <Plus size={16} />
          {actionLabel}
        </button>
      )}
    </div>
  );
}

function ProfileForm({
  profile,
  disabled,
  onSave,
  onDelete,
}: {
  profile: Profile | null;
  disabled: boolean;
  onSave: (payload: unknown) => Promise<void>;
  onDelete: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    const changed = Object.fromEntries(
      profileFields
        .filter(
          (field) =>
            String(form.get(field) ?? "").trim() !== (profile?.[field] ?? ""),
        )
        .map((field) => [field, String(form.get(field) ?? "").trim() || null]),
    );
    try {
      await onSave(changed);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Please try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="profile-section">
      <div className="profile-intro">
        <span className="welcome-mark">
          <UserRound size={28} />
        </span>
        <h2>
          More context.
          <br />
          More thoughtful connections.
        </h2>
        <p>
          You decide what to share. These details help your AI replies feel a
          little more like you.
        </p>
      </div>
      <form className="profile-form" onSubmit={submit}>
        <fieldset disabled={disabled || busy}>
          <div className="profile-fields">
            {profileFields.map((field) => (
              <label
                key={field}
                className={
                  ["bio", "goals", "interests", "skills"].includes(field)
                    ? "wide"
                    : ""
                }
              >
                {field[0].toUpperCase() + field.slice(1)}
                {["bio", "goals", "interests", "skills"].includes(field) ? (
                  <textarea
                    name={field}
                    defaultValue={profile?.[field] ?? ""}
                    maxLength={1000}
                    rows={3}
                    placeholder={`Your ${field}…`}
                  />
                ) : (
                  <input
                    name={field}
                    defaultValue={profile?.[field] ?? ""}
                    maxLength={
                      ["timezone", "language"].includes(field) ? 100 : 255
                    }
                    placeholder={
                      field === "timezone" ? "e.g. Asia/Kolkata" : ""
                    }
                  />
                )}
              </label>
            ))}
          </div>
        </fieldset>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="dialog-actions">
          {profile && (
            <button
              type="button"
              className="text-button delete-text"
              onClick={onDelete}
              disabled={busy || disabled}
            >
              Delete profile
            </button>
          )}
          <button className="primary" disabled={busy || disabled}>
            {busy ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              "Save profile"
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
