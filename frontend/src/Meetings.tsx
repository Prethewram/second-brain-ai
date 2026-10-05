import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  CalendarDays,
  Check,
  CheckCheck,
  FileText,
  LoaderCircle,
  Pencil,
  Plus,
  Search,
  Trash2,
  UsersRound,
  X,
} from "lucide-react";
import type { Collections, Note, Task } from "./api";
import Editor, { type EditorState } from "./Editor";

type Meeting = {
  id: number;
  title: string;
  meeting_date: string | null;
  attendees: string;
  agenda: string;
  minutes: string;
  decisions: string;
  created_at: string;
};
type Detail = Meeting & { notes: Note[]; tasks: Task[] };
type Call = <T>(path: string, method?: string, body?: unknown) => Promise<T>;

export default function Meetings({
  call,
  onUpdated,
  refreshKey,
}: {
  call: Call;
  onUpdated: () => Promise<void>;
  refreshKey: Collections;
}) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [form, setForm] = useState<Meeting | "new" | null>(null);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [busy, setBusy] = useState(false);
  const confirm = useRef<HTMLDialogElement>(null);
  const version = useRef(0);
  const load = useCallback(async () => {
    const current = ++version.current;
    setLoading(true);
    setError("");
    try {
      const list = await call<Meeting[]>("/meetings");
      const next = selected
        ? await call<Detail>(`/meetings/${selected}`)
        : null;
      if (version.current === current) {
        setMeetings(list);
        setDetail(next);
      }
    } catch (error) {
      if (version.current === current)
        setError(
          error instanceof Error ? error.message : "Could not load meetings.",
        );
    } finally {
      if (version.current === current) setLoading(false);
    }
  }, [call, selected]);
  useEffect(() => {
    void load();
    return () => {
      version.current++;
    };
  }, [load, refreshKey]);
  useEffect(() => {
    if (deleting) confirm.current?.showModal();
  }, [deleting]);
  async function save(method: string, path: string, body?: unknown) {
    await call(path, method, body);
    await load();
    await onUpdated();
  }
  async function complete(task: Task) {
    setBusy(true);
    try {
      await save("PATCH", `/tasks/${task.id}/complete`);
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Could not complete task.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    if (!detail) return;
    setBusy(true);
    try {
      await call(`/meetings/${detail.id}`, "DELETE");
      setDeleting(false);
      setSelected(null);
      setDetail(null);
      await onUpdated();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Could not delete meeting.",
      );
    } finally {
      setBusy(false);
    }
  }
  const visible = meetings.filter((meeting) =>
    `${meeting.title} ${meeting.attendees} ${meeting.minutes}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <section className="meeting-space">
      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button onClick={() => void load()}>Try again</button>
        </div>
      )}
      {selected ? (
        <>
          <div className="meeting-toolbar">
            <button
              className="text-button"
              onClick={() => {
                setSelected(null);
                setDetail(null);
              }}
            >
              <ArrowLeft size={15} />
              All meetings
            </button>
            {detail && (
              <div className="card-actions">
                <button className="secondary" onClick={() => setForm(detail)}>
                  <Pencil size={15} />
                  Edit MOM
                </button>
                <button
                  className="icon-button"
                  aria-label="Delete meeting"
                  onClick={() => setDeleting(true)}
                >
                  <Trash2 size={17} />
                </button>
              </div>
            )}
          </div>
          {loading ? (
            <div className="empty-state" role="status">
              <LoaderCircle className="spin" />
              Opening meeting…
            </div>
          ) : (
            detail && (
              <>
                <div className="meeting-summary">
                  <span className="category">MINUTES OF MEETING</span>
                  <h2>{detail.title}</h2>
                  <div className="meeting-meta">
                    <span>
                      <CalendarDays size={15} />
                      {detail.meeting_date || "No date set"}
                    </span>
                    <span>
                      <UsersRound size={15} />
                      {detail.attendees || "No attendees added"}
                    </span>
                  </div>
                </div>
                <div className="meeting-structure">
                  <div className="meeting-document">
                    {[
                      ["Agenda", detail.agenda],
                      ["Meeting minutes", detail.minutes],
                      ["Decisions", detail.decisions],
                    ].map(([title, content]) => (
                      <section key={title}>
                        <h3>{title}</h3>
                        <p className={content ? "" : "muted"}>
                          {content || "Nothing added yet."}
                        </p>
                      </section>
                    ))}
                  </div>
                  <aside className="meeting-actions">
                    <div className="section-title">
                      <h3>
                        Action tasks{" "}
                        <span className="nav-count">
                          {
                            detail.tasks.filter((task) => !task.completed)
                              .length
                          }{" "}
                          open
                        </span>
                      </h3>
                      <button
                        className="text-button"
                        onClick={() =>
                          setEditor({ kind: "tasks", meetingId: detail.id })
                        }
                      >
                        <Plus size={15} />
                        Add task
                      </button>
                    </div>
                    {detail.tasks.length ? (
                      detail.tasks.map((task) => (
                        <div
                          className={`linked-task ${task.completed ? "completed" : ""}`}
                          key={task.id}
                        >
                          <button
                            className="task-check"
                            disabled={task.completed || busy}
                            aria-label={
                              task.completed
                                ? `${task.title} completed`
                                : `Complete ${task.title}`
                            }
                            onClick={() => void complete(task)}
                          >
                            {task.completed && <Check size={14} />}
                          </button>
                          <div>
                            <h4>{task.title}</h4>
                            {task.description && <p>{task.description}</p>}
                            <span className={`priority ${task.priority}`}>
                              {task.priority}
                            </span>
                            {task.deadline && (
                              <span className="deadline">
                                Due: {task.deadline}
                              </span>
                            )}
                          </div>
                          <button
                            className="icon-button"
                            aria-label={`Edit ${task.title}`}
                            onClick={() =>
                              setEditor({ kind: "tasks", item: task })
                            }
                          >
                            <Pencil size={14} />
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="muted">
                        Turn a decision into a next step. Tasks added here also
                        appear in your task library.
                      </p>
                    )}
                    <div className="section-title linked-notes-title">
                      <h3>Linked notes</h3>
                      <button
                        className="text-button"
                        onClick={() =>
                          setEditor({ kind: "notes", meetingId: detail.id })
                        }
                      >
                        <Plus size={15} />
                        Add note
                      </button>
                    </div>
                    {detail.notes.length ? (
                      detail.notes.map((note) => (
                        <article className="linked-note" key={note.id}>
                          <div>
                            <h4>{note.title}</h4>
                            <button
                              className="icon-button"
                              aria-label={`Edit ${note.title}`}
                              onClick={() =>
                                setEditor({ kind: "notes", item: note })
                              }
                            >
                              <Pencil size={14} />
                            </button>
                          </div>
                          <p>{note.content}</p>
                          {note.is_archived && (
                            <span className="category">Archived</span>
                          )}
                        </article>
                      ))
                    ) : (
                      <p className="muted">
                        Keep research, context, and follow-up details with this
                        meeting.
                      </p>
                    )}
                  </aside>
                </div>
              </>
            )
          )}
        </>
      ) : (
        <>
          <div className="library-toolbar">
            <div>
              <span className="pill">
                <FileText size={14} />
                Minutes → decisions → action
              </span>
            </div>
            <div className="toolbar-right">
              <label className="search-field">
                <Search size={16} />
                <input
                  aria-label="Search meetings"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search meetings…"
                />
              </label>
              <button className="primary" onClick={() => setForm("new")}>
                <Plus size={16} />
                Add MOM
              </button>
            </div>
          </div>
          {loading ? (
            <div className="empty-state" role="status">
              <LoaderCircle className="spin" />
              Gathering your meetings…
            </div>
          ) : visible.length ? (
            <div className="note-grid">
              {visible.map((meeting) => (
                <button
                  className="meeting-card"
                  key={meeting.id}
                  onClick={() => {
                    setDetail(null);
                    setSelected(meeting.id);
                  }}
                >
                  <span className="category">
                    <CalendarDays size={14} />
                    {meeting.meeting_date || "Meeting"}
                  </span>
                  <h2>{meeting.title}</h2>
                  <p>{meeting.minutes}</p>
                  <span className="meeting-card-footer">
                    <UsersRound size={14} />
                    {meeting.attendees || "Open meeting details"}
                    <span>↗</span>
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">
                <UsersRound size={30} />
              </span>
              <h2>
                {query
                  ? "No matching meetings"
                  : "Give your meetings a next step"}
              </h2>
              <p>
                {query
                  ? "Try another search."
                  : "Capture the minutes, record decisions, and keep notes and tasks connected."}
              </p>
              {!query && (
                <button className="primary" onClick={() => setForm("new")}>
                  <Plus size={16} />
                  Add your first MOM
                </button>
              )}
            </div>
          )}
        </>
      )}
      {form && (
        <MeetingForm
          meeting={form === "new" ? undefined : form}
          onClose={() => setForm(null)}
          onSave={async (body) => {
            await save(
              form === "new" ? "POST" : "PUT",
              form === "new" ? "/meetings" : `/meetings/${form.id}`,
              body,
            );
          }}
        />
      )}
      {editor && (
        <Editor editor={editor} onClose={() => setEditor(null)} onSave={save} />
      )}
      {deleting && (
        <dialog
          ref={confirm}
          className="editor"
          aria-labelledby="meeting-delete-title"
          onCancel={(event) => {
            event.preventDefault();
            if (!busy) setDeleting(false);
          }}
        >
          <h2 id="meeting-delete-title">Delete this meeting?</h2>
          <p className="muted">
            The MOM will be removed. Its notes and tasks will remain in your
            library without a meeting link.
          </p>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="dialog-actions">
            <button
              className="secondary"
              onClick={() => setDeleting(false)}
              disabled={busy}
            >
              Keep meeting
            </button>
            <button
              className="danger"
              onClick={() => void remove()}
              disabled={busy}
            >
              {busy ? "Deleting…" : "Delete meeting"}
            </button>
          </div>
        </dialog>
      )}
    </section>
  );
}

function MeetingForm({
  meeting,
  onClose,
  onSave,
}: {
  meeting?: Meeting;
  onClose: () => void;
  onSave: (body: unknown) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const el = dialog.current!;
    el.showModal();
    return () => el.close();
  }, []);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const fields = new FormData(event.currentTarget);
    const body = {
      title: fields.get("title"),
      meeting_date: fields.get("meeting_date") || null,
      attendees: fields.get("attendees"),
      agenda: fields.get("agenda"),
      minutes: fields.get("minutes"),
      decisions: fields.get("decisions"),
    };
    try {
      await onSave(body);
      onClose();
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Could not save meeting.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="editor meeting-editor"
      aria-labelledby="meeting-editor-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="dialog-heading">
        <div>
          <span className="eyebrow">MINUTES OF MEETING</span>
          <h2 id="meeting-editor-title">{meeting ? "Edit MOM" : "Add MOM"}</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Close meeting editor"
          onClick={onClose}
          disabled={busy}
        >
          <X size={19} />
        </button>
      </div>
      <form onSubmit={submit}>
        <label>
          Meeting title
          <input
            name="title"
            required
            maxLength={255}
            defaultValue={meeting?.title}
            placeholder="e.g. Product planning — week 1"
            autoFocus
          />
        </label>
        <div className="form-row">
          <label>
            Meeting date
            <input
              name="meeting_date"
              type="date"
              defaultValue={meeting?.meeting_date ?? ""}
            />
          </label>
          <label>
            Attendees
            <input
              name="attendees"
              maxLength={10000}
              defaultValue={meeting?.attendees}
              placeholder="Names, separated by commas"
            />
          </label>
        </div>
        {[
          ["agenda", "Agenda", 50000],
          ["minutes", "Meeting minutes", 100000],
          ["decisions", "Decisions", 50000],
        ].map(([key, label, limit]) => (
          <label key={String(key)} className="meeting-text-label">
            {label}
            <textarea
              aria-label={String(label)}
              name={String(key)}
              required={key === "minutes"}
              rows={key === "minutes" ? 6 : 3}
              maxLength={Number(limit)}
              defaultValue={
                meeting?.[key as "agenda" | "minutes" | "decisions"] ?? ""
              }
              placeholder={
                key === "minutes"
                  ? "Paste your MOM or write the key discussion points…"
                  : "Optional"
              }
            />
          </label>
        ))}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="dialog-actions">
          <button
            type="button"
            className="secondary"
            onClick={onClose}
            disabled={busy}
          >
            Cancel
          </button>
          <button className="primary" disabled={busy}>
            {busy ? <LoaderCircle className="spin" size={16} /> : "Save MOM"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
