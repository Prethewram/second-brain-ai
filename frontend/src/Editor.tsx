import { useEffect, useRef, useState } from "react";
import { LoaderCircle, X } from "lucide-react";
import type { Memory, Note, Task } from "./api";

export type EditorState =
  | { kind: "notes"; item?: Note; meetingId?: number }
  | { kind: "tasks"; item?: Task; meetingId?: number }
  | { kind: "memories"; item: Memory };
export default function Editor({
  editor,
  onClose,
  onSave,
}: {
  editor: EditorState;
  onClose: () => void;
  onSave: (method: string, path: string, payload: unknown) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const el = dialog.current!;
    el.showModal();
    return () => el.close();
  }, []);
  const item = editor.item;
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const kind = editor.kind;
    const payload =
      kind === "notes"
        ? {
            title: form.get("title"),
            content: form.get("content"),
            category: form.get("category"),
          }
        : kind === "tasks"
          ? {
              title: form.get("title"),
              description: form.get("description") || null,
              priority: form.get("priority"),
              deadline: form.get("deadline") || null,
            }
          : {
              content: form.get("content"),
              category: form.get("category"),
              importance: Number(form.get("importance")),
            };
    const path =
      !item && "meetingId" in editor && editor.meetingId
        ? `/meetings/${editor.meetingId}/${kind}`
        : `/${kind === "memories" ? "memory" : kind}${item ? `/${item.id}` : ""}`;
    try {
      await onSave(
        kind === "memories" ? "PUT" : item ? "PATCH" : "POST",
        path,
        payload,
      );
      onClose();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Please try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="editor"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
      aria-labelledby="editor-title"
    >
      <div className="dialog-heading">
        <div>
          <span className="eyebrow">A PLACE FOR WHAT MATTERS</span>
          <h2 id="editor-title">
            {item ? "Edit" : "New"}{" "}
            {editor.kind === "memories"
              ? "memory"
              : editor.kind === "notes"
                ? "note"
                : "task"}
          </h2>
        </div>
        <button
          aria-label="Close editor"
          className="icon-button"
          onClick={onClose}
          disabled={busy}
        >
          <X size={20} />
        </button>
      </div>
      <form onSubmit={submit}>
        {editor.kind !== "memories" && (
          <label>
            Title
            <input
              name="title"
              defaultValue={item && "title" in item ? item.title : ""}
              required
              maxLength={255}
              autoFocus
            />
          </label>
        )}
        {editor.kind === "tasks" ? (
          <>
            <label>
              Description
              <textarea
                name="description"
                defaultValue={
                  item && "description" in item ? (item.description ?? "") : ""
                }
                rows={4}
              />
            </label>
            <div className="form-row">
              <label>
                Priority
                <select
                  name="priority"
                  defaultValue={
                    item && "priority" in item ? item.priority : "medium"
                  }
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </label>
              <label>
                Deadline
                <input
                  name="deadline"
                  placeholder="e.g. Friday, or 2026-10-15"
                  maxLength={100}
                  defaultValue={
                    item && "deadline" in item ? (item.deadline ?? "") : ""
                  }
                />
              </label>
            </div>
          </>
        ) : (
          <>
            <label>
              {editor.kind === "notes" ? "Your note" : "What to remember"}
              <textarea
                name="content"
                rows={6}
                required
                defaultValue={item && "content" in item ? item.content : ""}
              />
            </label>
            <div className="form-row">
              <label>
                Category
                <input
                  name="category"
                  defaultValue={
                    item && "category" in item ? item.category : "general"
                  }
                  required
                  maxLength={100}
                />
              </label>
              {editor.kind === "memories" && (
                <label>
                  Importance
                  <input
                    name="importance"
                    type="number"
                    step="1"
                    required
                    defaultValue={editor.item.importance}
                  />
                </label>
              )}
            </div>
          </>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="dialog-actions">
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={onClose}
          >
            Cancel
          </button>
          <button className="primary" disabled={busy}>
            {busy ? (
              <LoaderCircle size={16} className="spin" />
            ) : (
              "Save changes"
            )}
          </button>
        </div>
      </form>
    </dialog>
  );
}
