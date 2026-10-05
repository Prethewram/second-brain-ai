import { test, expect } from "@playwright/test";

test("captures a MOM and creates notes and tasks linked to it", async ({
  page,
}) => {
  test.setTimeout(60000);
  let meetings: any[] = [];
  let notes: any[] = [];
  let tasks: any[] = [];
  await page.route("**/api/**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname.replace("/api", "");
    const method = req.method();
    const body = req.postData() ? req.postDataJSON() : null;
    const reply = (json: unknown, status = 200) =>
      route.fulfill({ json, status });
    if (path === "/auth/login") return reply({ access_token: "test-token" });
    if (path === "/users/me")
      return reply({ id: 1, name: "Alex", email: "alex@example.com" });
    if (path === "/notes") return reply(notes);
    if (path === "/tasks") return reply(tasks);
    if (path === "/memory") return reply([]);
    if (path === "/profile") return reply({ detail: "Not found" }, 404);
    if (path === "/meetings" && method === "GET") return reply(meetings);
    if (path === "/meetings" && method === "POST") {
      meetings.push({ ...body, id: 1, created_at: "2026-10-05T10:00:00Z" });
      return reply(meetings[0], 201);
    }
    if (path === "/meetings/1" && method === "GET")
      return reply({ ...meetings[0], notes, tasks });
    if (path === "/meetings/1" && method === "PUT") {
      meetings[0] = { ...meetings[0], ...body };
      return reply(meetings[0]);
    }
    if (path === "/meetings/1/notes") {
      notes.push({ ...body, id: 1, source: "meeting", is_archived: false });
      return reply(notes[0], 201);
    }
    if (path === "/meetings/1/tasks") {
      tasks.push({
        ...body,
        id: 1,
        completed: false,
        created_at: "2026-10-05T10:00:00Z",
      });
      return reply(tasks[0], 201);
    }
    if (path === "/tasks/1/complete") {
      tasks[0].completed = true;
      return reply(tasks[0]);
    }
    if (path === "/meetings/1" && method === "DELETE") {
      meetings = [];
      return route.fulfill({ status: 204 });
    }
    return reply({ detail: "Unexpected test request" }, 500);
  });
  await page.goto("/");
  await page.getByLabel("Email address").fill("alex@example.com");
  await page.getByLabel("Password", { exact: true }).fill("password");
  await page.getByRole("button", { name: "Enter your space" }).click();
  await page
    .getByRole("button", { name: "Meetings / MOM", exact: true })
    .click();
  await page.getByRole("button", { name: "Add MOM", exact: true }).click();
  await page.getByLabel("Meeting title").fill("Release planning");
  await page.getByLabel("Meeting date").fill("2026-10-05");
  await page.getByLabel("Attendees", { exact: true }).fill("Alex, Sam");
  await page.getByLabel("Agenda", { exact: true }).fill("Agree scope");
  await page
    .getByLabel("Meeting minutes", { exact: true })
    .fill("Discussed release scope and agreed to ship Friday.");
  await page.getByLabel("Decisions", { exact: true }).fill("Ship Friday");
  await page.getByRole("button", { name: "Save MOM", exact: true }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.getByRole("button", { name: /Release planning/ }).click();
  await expect(
    page.getByRole("heading", { name: "Release planning", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Add note", exact: true }).click();
  await page.getByLabel("Title", { exact: true }).fill("Release scope");
  await page.getByLabel("Your note").fill("Include the new dashboard.");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Release scope", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Add task", exact: true }).click();
  await page
    .getByLabel("Title", { exact: true })
    .fill("Prepare release checklist");
  await page.getByLabel("Deadline", { exact: true }).fill("Friday");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page
    .getByRole("button", {
      name: "Complete Prepare release checklist",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Prepare release checklist completed",
      exact: true,
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/meeting-detail.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Edit MOM", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByLabel("Decisions", { exact: true })
    .fill("Ship Monday");
  await page.getByRole("button", { name: "Save MOM", exact: true }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(page.getByText("Ship Monday", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Delete meeting", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete meeting", exact: true })
    .click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Give your meetings a next step" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /^Notes/ }).click();
  await expect(
    page.getByRole("heading", { name: "Release scope", exact: true }),
  ).toBeVisible();
});
