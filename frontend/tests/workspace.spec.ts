import { test, expect, type Page } from "@playwright/test";

test("personal greeting changes with time and speaks once per period", async ({
  page,
}) => {
  await page.clock.install({ time: new Date(2026, 9, 5, 9, 0) });
  await page.addInitScript(() => {
    const spoken: string[] = [];
    Object.defineProperty(window, "greetingsTest", { value: spoken });
    Object.defineProperty(window, "SpeechSynthesisUtterance", {
      value: class {
        text: string;
        constructor(text: string) {
          this.text = text;
        }
      },
    });
    Object.defineProperty(window, "speechSynthesis", {
      value: {
        getVoices: () => [],
        addEventListener() {},
        removeEventListener() {},
        cancel() {},
        speak(utterance: { text: string; onstart?: () => void }) {
          spoken.push(utterance.text);
          utterance.onstart?.();
        },
      },
    });
  });
  await mockApi(page);
  await signIn(page);
  await expect(
    page.getByRole("heading", { name: "Good morning, Alex Morgan." }),
  ).toBeVisible();
  const spoken = () =>
    page.evaluate(
      () => (window as unknown as { greetingsTest: string[] }).greetingsTest,
    );
  expect(await spoken()).toEqual(["Good morning, Alex Morgan."]);
  await page.getByRole("button", { name: /^Notes/ }).click();
  await page.getByRole("button", { name: "Thinking space" }).click();
  expect(await spoken()).toHaveLength(1);
  await page.clock.setSystemTime(new Date(2026, 9, 5, 13, 0));
  await page.clock.runFor(30000);
  await expect(
    page.getByRole("heading", { name: "Good afternoon, Alex Morgan." }),
  ).toBeVisible();
  expect(await spoken()).toHaveLength(2);
  await page.getByRole("button", { name: /^Notes/ }).click();
  await page.clock.setSystemTime(new Date(2026, 9, 5, 18, 0));
  await page.getByRole("button", { name: "Thinking space" }).click();
  await expect(
    page.getByRole("heading", { name: "Good evening, Alex Morgan." }),
  ).toBeVisible();
  expect(await spoken()).toHaveLength(3);
  await page.getByRole("button", { name: "Hear greeting" }).click();
  expect(await spoken()).toHaveLength(4);
});

test("voice replies support manual playback, automatic reading and cleanup", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const state = { spoken: [] as string[], cancelled: 0 };
    const now = new Date();
    const period =
      now.getHours() < 12
        ? "morning"
        : now.getHours() < 17
          ? "afternoon"
          : "evening";
    sessionStorage.setItem(
      "second-brain-greeting:1",
      `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}:${period}`,
    );
    Object.defineProperty(window, "voiceTest", { value: state });
    Object.defineProperty(window, "SpeechSynthesisUtterance", {
      value: class {
        text: string;
        constructor(text: string) {
          this.text = text;
        }
      },
    });
    Object.defineProperty(window, "speechSynthesis", {
      value: {
        getVoices: () => [
          { voiceURI: "test-voice", name: "Test English", lang: "en-IN" },
        ],
        addEventListener() {},
        removeEventListener() {},
        speak(utterance: { text: string }) {
          state.spoken.push(utterance.text);
        },
        cancel() {
          state.cancelled++;
        },
      },
    });
  });
  await mockApi(page);
  await page.route("**/api/chat", (route) =>
    route.fulfill({
      json: { conversation_id: 1, response: "**Hello** from your notes." },
    }),
  );
  await signIn(page);
  await page.getByLabel("Message", { exact: true }).fill("Hello");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByRole("button", { name: "Listen to reply" }),
  ).toBeVisible();
  const snapshot = () =>
    page.evaluate(
      () =>
        (
          window as unknown as {
            voiceTest: { spoken: string[]; cancelled: number };
          }
        ).voiceTest,
    );
  expect((await snapshot()).spoken).toEqual([]);
  await page.getByRole("button", { name: "Listen to reply" }).click();
  expect((await snapshot()).spoken).toEqual(["Hello from your notes."]);
  await page.getByRole("button", { name: "Stop reading reply" }).click();
  expect((await snapshot()).cancelled).toBe(1);
  await page.getByLabel("Read replies aloud").check();
  await page.getByLabel("Reply voice").selectOption("test-voice");
  await page.getByLabel("Message", { exact: true }).fill("Again");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByRole("button", { name: "Stop reading reply" }),
  ).toBeVisible();
  expect((await snapshot()).spoken).toHaveLength(2);
  await page.getByRole("button", { name: /^Notes/ }).click();
  expect((await snapshot()).cancelled).toBe(2);
  await page.getByRole("button", { name: "Thinking space" }).click();
  expect((await snapshot()).spoken).toHaveLength(2);
});

test("voice drafts commands without sending and stops on navigation", async ({
  page,
}) => {
  await page.addInitScript(() => {
    class FakeRecognition {
      onresult: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;
      onerror: ((event: unknown) => void) | null = null;
      start() {
        (window as unknown as Record<string, unknown>).testRecognition = this;
      }
      stop() {
        this.onend?.();
      }
      abort() {
        (window as unknown as Record<string, unknown>).voiceAborted = true;
      }
    }
    Object.defineProperty(window, "SpeechRecognition", {
      value: FakeRecognition,
    });
  });
  const api = await mockApi(page);
  await signIn(page);
  await page.getByLabel("Message", { exact: true }).fill("Please");
  await page.getByRole("button", { name: "Start voice input" }).click();
  await expect(
    page.getByRole("button", { name: "Stop voice input" }),
  ).toBeVisible();
  await page.evaluate(() => {
    const recognition = (
      window as unknown as {
        testRecognition: { onresult: (event: unknown) => void };
      }
    ).testRecognition;
    recognition.onresult({
      results: [{ isFinal: false, 0: { transcript: "list my" } }],
    });
    recognition.onresult({
      results: [{ isFinal: true, 0: { transcript: "list my notes" } }],
    });
  });
  await expect(page.getByLabel("Message", { exact: true })).toHaveValue(
    "Please list my notes",
  );
  expect(api.chatBodies).toEqual([]);
  await page.getByRole("button", { name: "Stop voice input" }).click();
  await expect(
    page.getByText("Voice captured. Review your command, then send."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByRole("button", { name: "Send message" }),
  ).toBeDisabled();
  expect(api.chatBodies).toEqual([
    { message: "Please list my notes", conversation_id: null },
  ]);
  await page.getByRole("button", { name: "Start voice input" }).click();
  await page.getByRole("button", { name: /^Notes/ }).click();
  expect(
    await page.evaluate(
      () => (window as unknown as Record<string, unknown>).voiceAborted,
    ),
  ).toBe(true);
});

test("voice permission failures preserve typed text", async ({ page }) => {
  await page.addInitScript(() => {
    class DeniedRecognition {
      onerror: ((event: { error: string }) => void) | null = null;
      onend: (() => void) | null = null;
      start() {
        setTimeout(() => {
          this.onerror?.({ error: "not-allowed" });
          this.onend?.();
        }, 10);
      }
      abort() {}
    }
    Object.defineProperty(window, "SpeechRecognition", {
      value: DeniedRecognition,
    });
  });
  await mockApi(page);
  await signIn(page);
  await page.getByLabel("Message", { exact: true }).fill("Keep this draft");
  await page.getByRole("button", { name: "Start voice input" }).click();
  await expect(page.getByText(/Microphone permission denied/)).toBeVisible();
  await expect(page.getByLabel("Message", { exact: true })).toHaveValue(
    "Keep this draft",
  );
  await expect(
    page.getByRole("button", { name: "Start voice input" }),
  ).toBeEnabled();
});

test("formatted replies render safely and fit desktop and mobile", async ({
  page,
}) => {
  await mockApi(page);
  await page.route("**/api/chat", (route) =>
    route.fulfill({
      json: {
        conversation_id: 1,
        response:
          "## Your active notes\n\nHere are your **2 saved notes**:\n\n- **Database backup** — Take a snapshot every 5 days.\n- **Server renewal** — Renew the server on 11 October.\n\n| Note | Next step |\n| --- | --- |\n| Backup | Schedule a snapshot |\n\n`Review your library`\n\n<script>window.unsafeReply = true</script>\n\n[Unsafe link](javascript:alert(1))",
      },
    }),
  );
  await signIn(page);
  await page.getByLabel("Message", { exact: true }).fill("List my notes");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByRole("heading", { name: "Your active notes" }),
  ).toBeVisible();
  await expect(page.locator(".reply-markdown strong").first()).toHaveText(
    "2 saved notes",
  );
  await expect(page.locator(".reply-markdown li")).toHaveCount(2);
  await expect(page.locator(".reply-markdown table")).toBeVisible();
  expect(await page.locator(".reply-markdown script").count()).toBe(0);
  expect(
    await page.getByRole("link", { name: "Unsafe link" }).getAttribute("href"),
  ).not.toContain("javascript:");
  await page.screenshot({
    path: "test-results/chat-redesign-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Copy reply" })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/chat-redesign-mobile.png",
    fullPage: true,
  });
});

for (const actionsSaved of [false, true]) {
  test(`busy AI keeps the conversation and explains saved actions (${actionsSaved})`, async ({
    page,
  }) => {
    const api = await mockApi(page);
    let calls = 0;
    await page.route("**/api/chat", (route) => {
      calls++;
      if (calls === 1)
        return route.fulfill({
          status: 503,
          json: {
            success: false,
            message:
              "The AI model is busy right now. Please try again shortly.",
            data: {
              conversation_id: 7,
              message_saved: true,
              actions_may_be_saved: actionsSaved,
            },
          },
        });
      return route.fallback();
    });
    await signIn(page);
    await page
      .getByLabel("Message", { exact: true })
      .fill("Remember my preference.");
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(page.getByRole("alert")).toContainText("AI model is busy");
    await expect(page.getByRole("alert")).toContainText(
      actionsSaved
        ? "Some extracted actions may already be saved"
        : "No extracted actions were saved",
    );
    await expect(
      page.getByRole("button", { name: "New conversation" }),
    ).toBeEnabled();
    expect(calls).toBe(1);
    await page.getByLabel("Message", { exact: true }).fill("Hello again");
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(
      page.getByText("A little more room for your thoughts.", { exact: false }),
    ).toBeVisible();
    expect(api.chatBodies).toEqual([
      { message: "Hello again", conversation_id: 7 },
    ]);
    expect(calls).toBe(2);
  });
}

async function mockApi(page: Page) {
  const user = { id: 1, name: "Alex Morgan", email: "alex@example.com" };
  let notes = [
    {
      id: 1,
      title: "A quieter morning",
      content: "Leave room to think before the day begins.",
      category: "personal",
      is_archived: false,
      source: "chat",
    },
  ];
  let tasks = [
    {
      id: 1,
      title: "Plan a little reading time",
      description: "Twenty minutes is enough.",
      priority: "medium",
      deadline: "Friday",
      completed: false,
      created_at: "2026-10-03T10:00:00Z",
    },
  ];
  let profile: unknown = null;
  let expired = false;
  const chatBodies: unknown[] = [];
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace("/api", "");
    const method = request.method();
    const body = method === "GET" ? null : request.postDataJSON();
    const respond = (json: unknown, status = 200) =>
      route.fulfill({ status, json });
    if (path === "/auth/login")
      return respond({ access_token: "test-token", token_type: "bearer" });
    if (path === "/auth/register") return respond(user);
    if (expired)
      return respond({ detail: "Invalid authentication credentials" }, 401);
    expect(request.headers()["authorization"]).toBe("Bearer test-token");
    if (path === "/users/me") return respond(user);
    if (path === "/notes" && method === "GET") return respond(notes);
    if (path === "/notes" && method === "POST") {
      const note = { ...body, id: 2, source: "manual", is_archived: false };
      notes.push(note);
      return respond(note, 201);
    }
    if (path.startsWith("/notes/") && method === "PATCH") {
      notes = notes.map((note) =>
        note.id === Number(path.split("/")[2]) ? { ...note, ...body } : note,
      );
      return respond(
        notes.find((note) => note.id === Number(path.split("/")[2])),
      );
    }
    if (path.startsWith("/notes/") && method === "DELETE") {
      notes = notes.filter((note) => note.id !== Number(path.split("/")[2]));
      return route.fulfill({ status: 204 });
    }
    if (path === "/tasks") return respond(tasks);
    if (path === "/tasks/1/complete") {
      tasks = tasks.map((task) => ({ ...task, completed: true }));
      return respond(tasks[0]);
    }
    if (path === "/memory")
      return respond([
        {
          id: 1,
          content: "I prefer morning meetings.",
          category: "preferences",
          importance: 2,
          created_at: "2026-10-03T10:00:00Z",
        },
      ]);
    if (path === "/profile" && method === "GET")
      return respond(
        profile ?? { detail: "Profile not found" },
        profile ? 200 : 404,
      );
    if (path === "/profile" && method === "PATCH") {
      profile = { id: 1, user_id: 1, ...body };
      return respond(profile);
    }
    if (path === "/chat") {
      chatBodies.push(body);
      return respond({
        conversation_id: 7,
        response:
          "A little more room for your thoughts. I have saved that preference.",
      });
    }
    return respond(
      { detail: `Unexpected test request ${method} ${path}` },
      500,
    );
  });
  return {
    expire: () => {
      expired = true;
    },
    chatBodies,
  };
}

async function signIn(page: Page) {
  await page.goto("/");
  await page.getByLabel("Email address").fill("alex@example.com");
  await page.getByLabel("Password", { exact: true }).fill("local-password");
  await page.getByRole("button", { name: "Enter your space" }).click();
  await expect(
    page.getByRole("heading", { name: "Your thinking space." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Refresh library" }),
  ).toBeEnabled();
}

test("signs in, creates, edits, archives, restores and deletes a note", async ({
  page,
}) => {
  await mockApi(page);
  await signIn(page);
  await page.getByRole("button", { name: /^Notes/ }).click();
  await page.getByRole("button", { name: "New note", exact: true }).click();
  await page.getByLabel("Title", { exact: true }).fill("A fresh idea");
  await page
    .getByLabel("Your note")
    .fill("Make a little room for a walking break.");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(
    page.getByRole("heading", { name: "A fresh idea" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Edit A fresh idea" }).click();
  await page.getByLabel("Title", { exact: true }).fill("An even fresher idea");
  await page.getByRole("button", { name: "Save changes" }).click();
  await page
    .getByRole("button", { name: "Archive An even fresher idea" })
    .click();
  await expect(
    page.getByRole("heading", { name: "An even fresher idea", exact: true }),
  ).not.toBeVisible();
  await page.getByRole("button", { name: "Archived", exact: true }).click();
  await page
    .getByRole("button", { name: "Restore An even fresher idea" })
    .click();
  await page.getByRole("button", { name: "My notes", exact: true }).click();
  await page
    .getByRole("button", { name: "Delete An even fresher idea" })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByRole("heading", { name: "An even fresher idea", exact: true }),
  ).not.toBeVisible();
});

test("keeps conversation IDs across navigation and starts a fresh conversation", async ({
  page,
}) => {
  const api = await mockApi(page);
  await signIn(page);
  await page
    .getByLabel("Message", { exact: true })
    .fill("Remember my preference.");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByText("A little more room for your thoughts.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Notes/ }).click();
  await page
    .getByRole("button", { name: "Thinking space", exact: true })
    .click();
  await page.getByLabel("Message", { exact: true }).fill("Thanks.");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByRole("button", { name: "Send message" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "New conversation" }),
  ).toBeEnabled();
  expect(api.chatBodies).toEqual([
    { message: "Remember my preference.", conversation_id: null },
    { message: "Thanks.", conversation_id: 7 },
  ]);
  await page.getByRole("button", { name: "New conversation" }).click();
  await expect(page.getByText("Thanks.", { exact: true })).not.toBeVisible();
});

test("completes tasks, creates a profile and signs out on an expired token", async ({
  page,
}) => {
  const api = await mockApi(page);
  await signIn(page);
  await page.getByRole("button", { name: /^Tasks/ }).click();
  await page
    .getByRole("button", { name: "Complete Plan a little reading time" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Plan a little reading time" }),
  ).not.toBeVisible();
  await page.getByRole("button", { name: "Completed", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Plan a little reading time" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "My profile", exact: true }).click();
  await page.getByLabel("Occupation").fill("Designer");
  await page.getByRole("button", { name: "Save profile" }).click();
  await expect(page.getByLabel("Occupation")).toHaveValue("Designer");
  api.expire();
  await page.getByRole("button", { name: "Refresh library" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("session expired");
  expect(
    await page.evaluate(() => sessionStorage.getItem("second-brain-token")),
  ).toBeNull();
});

test("shows login errors and uses the JSON registration flow", async ({
  page,
}) => {
  await mockApi(page);
  await page.route("**/api/auth/login", (route) =>
    route.fulfill({ status: 401, json: { detail: "Invalid credentials" } }),
  );
  await page.goto("/");
  await page.getByLabel("Email address").fill("alex@example.com");
  await page.getByLabel("Password", { exact: true }).fill("wrong-password");
  await page.getByRole("button", { name: "Enter your space" }).click();
  await expect(page.getByRole("alert")).toHaveText("Invalid credentials");
  await page.unroute("**/api/auth/login");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await page.getByLabel("Your name").fill("Alex Morgan");
  await page.getByRole("button", { name: "Create your space" }).click();
  await expect(
    page.getByRole("heading", { name: "Your thinking space." }),
  ).toBeVisible();
});

test("mobile layout fits the screen and library requests can be retried", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  let fail = true;
  await page.route("**/api/notes", (route) =>
    fail
      ? route.fulfill({ status: 500, json: { detail: "Could not load notes" } })
      : route.fallback(),
  );
  await signIn(page);
  await expect(page.getByRole("alert")).toContainText("Could not load notes");
  fail = false;
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByRole("alert")).not.toBeVisible();
  await page.getByRole("button", { name: /^Notes/ }).click();
  await expect(
    page.getByRole("heading", { name: "A quieter morning" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/mobile-workspace.png",
    fullPage: true,
  });
});

test("desktop workspace renders with no JavaScript errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await mockApi(page);
  await page.goto("/");
  await page.screenshot({ path: "test-results/sign-in.png", fullPage: true });
  await signIn(page);
  await page.screenshot({ path: "test-results/workspace.png", fullPage: true });
  expect(errors).toEqual([]);
});

test("failed saves preserve edits and cancelled deletion keeps the note", async ({
  page,
}) => {
  await mockApi(page);
  await signIn(page);
  await page.getByRole("button", { name: /^Notes/ }).click();
  await page.getByRole("button", { name: "Edit A quieter morning" }).click();
  await page.getByLabel("Title", { exact: true }).fill("A revised morning");
  await page.route("**/api/notes/1", async (route) => {
    if (route.request().method() === "PATCH")
      return route.fulfill({
        status: 400,
        json: {
          success: false,
          message: "Please choose a different title",
          data: null,
        },
      });
    return route.fallback();
  });
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("alert")).toHaveText(
    "Please choose a different title",
  );
  await expect(page.getByLabel("Title", { exact: true })).toHaveValue(
    "A revised morning",
  );
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page.getByRole("button", { name: "Delete A quieter morning" }).click();
  await page.getByRole("button", { name: "Keep it" }).click();
  await expect(
    page.getByRole("heading", { name: "A quieter morning" }),
  ).toBeVisible();
});

test("reload validates the session and sign out clears private library data", async ({
  page,
}) => {
  await mockApi(page);
  await signIn(page);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Your thinking space." }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Notes/ }).click();
  await expect(
    page.getByRole("heading", { name: "A quieter morning" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "A quieter morning" }),
  ).not.toBeVisible();
  expect(
    await page.evaluate(() => sessionStorage.getItem("second-brain-token")),
  ).toBeNull();
});
