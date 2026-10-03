export type User = { id: number; name: string; email: string };
export type Note = {
  id: number;
  title: string;
  content: string;
  category: string;
  source: string;
  is_archived: boolean;
};
export type Task = {
  id: number;
  title: string;
  description: string | null;
  priority: string;
  deadline: string | null;
  completed: boolean;
  created_at: string;
};
export type Memory = {
  id: number;
  content: string;
  category: string;
  importance: number;
  created_at: string;
};
export const profileFields = [
  "name",
  "occupation",
  "company",
  "timezone",
  "language",
  "bio",
  "goals",
  "interests",
  "skills",
] as const;
export type ProfileField = (typeof profileFields)[number];
export type Profile = { id: number; user_id: number } & Record<
  ProfileField,
  string | null
>;
export type Collections = {
  notes: Note[];
  tasks: Task[];
  memories: Memory[];
  profile: Profile | null;
};
export const emptyCollections: Collections = {
  notes: [],
  tasks: [],
  memories: [],
  profile: null,
};
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function request<T>(
  path: string,
  token?: string,
  method = "GET",
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      signal,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new ApiError(
      "Cannot reach your server. Check your connection and try again.",
      0,
    );
  }
  if (response.status === 204) return undefined as T;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      payload?.detail ?? payload?.error?.message ?? payload?.message;
    const message = Array.isArray(detail)
      ? detail
          .map((item: { msg?: string }) => item.msg ?? "Invalid input")
          .join(". ")
      : typeof detail === "string"
        ? detail
        : "The request failed. Please try again.";
    throw new ApiError(
      response.status === 502
        ? "Your server is unavailable. Check that the backend is running."
        : message,
      response.status,
    );
  }
  return payload as T;
}

export async function loadCollections(
  token: string,
  signal?: AbortSignal,
): Promise<Collections> {
  const [notes, tasks, memories, profile] = await Promise.all([
    request<Note[]>("/notes", token, "GET", undefined, signal),
    request<Task[]>("/tasks", token, "GET", undefined, signal),
    request<Memory[]>("/memory", token, "GET", undefined, signal),
    request<Profile>("/profile", token, "GET", undefined, signal).catch(
      (error) => {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      },
    ),
  ]);
  return { notes, tasks, memories, profile };
}
