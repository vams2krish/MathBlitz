const DAILY_GOAL = 12;
const guestOnly = document.querySelector('meta[name="mathblitz-mode"]').content === "guest";
const state = {
  token: sessionStorage.getItem("mathblitz_token"),
  user: JSON.parse(sessionStorage.getItem("mathblitz_user") || "null"),
  catalog: null,
  preferences: null,
  dashboard: null,
  activityId: "shopping-value",
  difficulty: "Medium",
  task: null,
  timer: null,
  guest: false,
  taskRequest: 0,
};

const byId = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll("\"", "&quot;")
  .replaceAll("'", "&#039;");

const icons = {
  equation: '<svg viewBox="0 0 24 24"><path d="M5 8h14M5 16h14M9 5v6M15 13v6"/></svg>',
  pattern: '<svg viewBox="0 0 24 24"><path d="M4 17 9 7l4 8 3-6 4 8"/><path d="M3 20h18"/></svg>',
  prime: '<svg viewBox="0 0 24 24"><path d="M12 3 4 8v8l8 5 8-5V8z"/><path d="M8 12h8M12 8v8"/></svg>',
  geometry: '<svg viewBox="0 0 24 24"><path d="M4 19 12 4l8 15z"/><circle cx="12" cy="14" r="2"/></svg>',
  bolt: '<svg viewBox="0 0 24 24"><path d="m13 2-9 12h8l-1 8 9-12h-8z"/></svg>',
  multiply: '<svg viewBox="0 0 24 24"><path d="m6 6 12 12M18 6 6 18"/></svg>',
  divide: '<svg viewBox="0 0 24 24"><path d="M5 12h14"/><circle cx="12" cy="6" r="1"/><circle cx="12" cy="18" r="1"/></svg>',
  percent: '<svg viewBox="0 0 24 24"><path d="m6 18 12-12"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/></svg>',
  wallet: '<svg viewBox="0 0 24 24"><path d="M4 8h16v11H4zM4 8V6h12"/><path d="M15 13h3"/></svg>',
  split: '<svg viewBox="0 0 24 24"><circle cx="8" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 19c.5-4 9.5-4 10 0M14 16c3-1 6 .5 6.5 3"/></svg>',
  compare: '<svg viewBox="0 0 24 24"><path d="M5 8h14M5 16h14M9 4 5 8l4 4M15 12l4 4-4 4"/></svg>',
  growth: '<svg viewBox="0 0 24 24"><path d="M4 19h16M6 16l5-5 4 3 5-8"/><path d="M16 6h4v4"/></svg>',
  spark: '<svg viewBox="0 0 24 24"><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="m18 15 .8 2.2L21 18l-2.2.8L18 21l-.8-2.2L15 18l2.2-.8z"/></svg>',
  steps: '<svg viewBox="0 0 24 24"><path d="M5 19h4v-4h4v-4h4V7h2"/><path d="M5 19V5"/></svg>',
  target: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/></svg>',
  fire: '<svg viewBox="0 0 24 24"><path d="M12 3c3 4 6 7 6 11a6 6 0 0 1-12 0c0-4 3-7 6-11Z"/><path d="M12 13c1 1.5 2 2.6 2 4a2 2 0 1 1-4 0c0-1.4 1-2.5 2-4Z"/></svg>',
  orbit: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="2.5"/><path d="M4 12c0-3 3.6-5.5 8-5.5s8 2.5 8 5.5-3.6 5.5-8 5.5-8-2.5-8-5.5Z"/><path d="M7 5c2.2-2 7.8 1 10 5s1.4 9.1-1.8 9.7-7.8-3.1-10-7.1S3.8 7 7 5Z"/></svg>',
  cart: '<svg viewBox="0 0 24 24"><path d="M5 6h16l-2 8H7L5 3H2"/><circle cx="8" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/></svg>',
  receipt: '<svg viewBox="0 0 24 24"><path d="M6 3h12v18l-2-1.2-2 1.2-2-1.2-2 1.2-2-1.2L6 21z"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>',
  piggy: '<svg viewBox="0 0 24 24"><path d="M5 12a7 7 0 0 1 7-6h4a4 4 0 0 1 4 4v3h-2l-1 4H8l-1-3H5z"/><path d="M4 10H2m8-4V4h4v2"/><circle cx="16" cy="10" r=".7"/></svg>',
  credit: '<svg viewBox="0 0 24 24"><path d="M3 6h18v12H3z"/><path d="M3 10h18M7 15h4"/></svg>',
  home: '<svg viewBox="0 0 24 24"><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></svg>',
  meeting: '<svg viewBox="0 0 24 24"><path d="M4 19V7h16v12z"/><path d="M8 11h8M8 15h5"/><path d="M7 4h10"/></svg>',
  car: '<svg viewBox="0 0 24 24"><path d="M5 15h14l-1.5-5h-11z"/><path d="M3 15v4h3m12 0h3v-4"/><circle cx="7" cy="19" r="2"/><circle cx="17" cy="19" r="2"/></svg>',
  tools: '<svg viewBox="0 0 24 24"><path d="m14 7 3-3 3 3-3 3z"/><path d="m14 10-9 9"/><path d="M7 5l12 12"/><path d="m5 7 2-2 3 3-2 2z"/></svg>',
  health: '<svg viewBox="0 0 24 24"><path d="M12 21s-8-4.7-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6.3-8 11-8 11Z"/><path d="M8 12h3l1-2 2 4 1-2h2"/></svg>',
  recipe: '<svg viewBox="0 0 24 24"><path d="M7 3h10v18H7z"/><path d="M10 7h4M10 11h4M10 15h2"/><path d="M5 6h2M17 6h2"/></svg>',
  utilities: '<svg viewBox="0 0 24 24"><path d="M13 2 5 13h6l-1 9 9-13h-6z"/></svg>',
  estimate: '<svg viewBox="0 0 24 24"><path d="M4 17c4-8 12-8 16 0"/><path d="M12 17l4-6"/><path d="M4 20h16"/></svg>',
};

function iconFor(key) {
  return icons[key] || icons.bolt;
}

function difficultyIconFor(name) {
  return {
    "Very Easy": icons.spark,
    Easy: icons.steps,
    Medium: icons.target,
    Hard: icons.fire,
    "Extreme Hard": icons.orbit,
  }[name] || icons.target;
}

function slugName(value) {
  return String(value).toLowerCase().replaceAll(" ", "-");
}

async function api(path, options = {}) {
  if (state.guest) return MathBlitzGuest.request(path, options);
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`/api/v1${path}`, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (response.status === 401 && state.token) {
    signOut();
    throw new Error("Your session has ended. Please sign in again.");
  }
  if (!response.ok) throw new Error(payload.detail || "Something went wrong.");
  return payload;
}

function setMessage(element, message, positive = false) {
  element.textContent = message;
  element.style.color = positive ? "var(--success)" : "var(--danger)";
}

function showAuthTab(isRegister) {
  byId("login-tab").classList.toggle("active", !isRegister);
  byId("register-tab").classList.toggle("active", isRegister);
  byId("login-tab").setAttribute("aria-selected", String(!isRegister));
  byId("register-tab").setAttribute("aria-selected", String(isRegister));
  byId("login-form").classList.toggle("hidden", isRegister);
  byId("register-form").classList.toggle("hidden", !isRegister);
  setMessage(byId("auth-message"), "");
}

async function authenticate(event, endpoint) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const response = await api(`/auth/${endpoint}`, {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    state.token = response.access_token;
    state.user = response.user;
    sessionStorage.setItem("mathblitz_token", state.token);
    sessionStorage.setItem("mathblitz_user", JSON.stringify(state.user));
    form.reset();
    await startApplication();
  } catch (error) {
    setMessage(byId("auth-message"), error.message);
  }
}

function signOut() {
  resetTask();
  MathBlitzAudio.setMusic(false);
  MathBlitzGuest.clearTask();
  clearInterval(state.timer);
  state.token = null;
  state.user = null;
  state.guest = false;
  state.preferences = null;
  sessionStorage.removeItem("mathblitz_token");
  sessionStorage.removeItem("mathblitz_user");
  byId("app-view").classList.add("hidden");
  byId("auth-view").classList.remove("hidden");
}

function activityById(id) {
  return state.catalog.activities.find((activity) => activity.id === id);
}

function activityButton(activity, large = false) {
  const tag = large ? "div" : "span";
  const copyClass = large ? "explore-copy" : "activity-copy";
  const variants = state.guest ? '<span class="variant-count">160 guest challenges</span>' : activity.variant_estimate
    ? `<span class="variant-count">${Math.round(activity.variant_estimate / 1000)}k+ variations</span>`
    : "";
  return `
    <button class="${large ? "explore-card" : "activity-card"} accent-${activity.accent}${state.activityId === activity.id ? " selected" : ""}" type="button" data-activity="${activity.id}">
      <span class="activity-icon accent-${activity.accent}">${iconFor(activity.icon)}</span>
      <${tag} class="${copyClass}">
        <strong>${escapeHtml(activity.name)}</strong>
        ${large
          ? `<p>${escapeHtml(activity.description)}</p><span class="activity-chip">${escapeHtml(activity.skill)}</span>${variants}`
          : `<small>${escapeHtml(activity.skill)}</small>`}
      </${tag}>
      <span class="activity-arrow" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span>
    </button>`;
}

function renderActivityCollections() {
  const featuredIds = ["shopping-value", "budget-planner", "office-meetings", "health-science"];
  const selected = activityById(state.activityId);
  const featured = featuredIds.map(activityById).filter(Boolean);
  if (selected && !featured.some((activity) => activity.id === selected.id)) {
    featured[featured.length - 1] = selected;
  }
  byId("activity-cards").innerHTML = featured.map((activity) => activityButton(activity)).join("");
  byId("explore-grid").innerHTML = state.catalog.activities
    .map((activity) => activityButton(activity, true))
    .join("");
}

function renderCatalog() {
  const options = state.catalog.activities
    .map((activity) => `<option value="${activity.id}">${escapeHtml(activity.name)}</option>`)
    .join("");
  byId("settings-activity").innerHTML = options;
  byId("difficulty-buttons").innerHTML = state.catalog.difficulties
    .map((level) => `
      <button class="difficulty-button level-${slugName(level.name)}" type="button" data-level="${level.name}">
        <span class="difficulty-icon">${difficultyIconFor(level.name)}</span>
        <b>${level.name}</b><small>${level.time_limit_seconds}s / ${level.points_multiplier}x</small>
      </button>`)
    .join("");
  byId("settings-difficulty").innerHTML = state.catalog.difficulties
    .map((level) => `<option value="${level.name}">${level.name}</option>`)
    .join("");
  renderActivityCollections();
}

function syncSelections() {
  for (const button of byId("difficulty-buttons").querySelectorAll("button")) {
    button.classList.toggle("selected", button.dataset.level === state.difficulty);
  }
  renderActivityCollections();
}

async function loadPreferences() {
  state.preferences = await api("/me/preferences");
  state.activityId = state.preferences.default_activity_id;
  state.difficulty = state.preferences.default_difficulty;
  byId("settings-activity").value = state.activityId;
  byId("settings-difficulty").value = state.difficulty;
  byId("settings-sound").checked = state.preferences.sound_enabled;
  syncSelections();
}

function formatActivity(activityId) {
  return activityById(activityId)?.name || activityId;
}

function setGoal(solved) {
  const safeSolved = Math.min(DAILY_GOAL, solved);
  const progress = `${Math.round((safeSolved / DAILY_GOAL) * 100)}%`;
  byId("daily-focus-label").textContent = `${solved} / ${DAILY_GOAL} solved`;
  byId("goal-value").textContent = `${solved} / ${DAILY_GOAL} solved`;
  byId("sidebar-goal").textContent = `${solved} / ${DAILY_GOAL}`;
  byId("goal-fill").style.width = progress;
  byId("sidebar-goal-fill").style.width = progress;
}

function renderDashboard() {
  const dashboard = state.dashboard;
  byId("header-score").textContent = dashboard.score.toLocaleString();
  byId("streak-value").textContent = dashboard.streak;
  byId("accuracy-value").textContent = `${dashboard.accuracy}%`;
  byId("mastery-ring").style.setProperty("--mastery-progress", `${dashboard.accuracy}%`);
  setGoal(dashboard.solved_today);
  const wins = dashboard.recent_attempts
    .filter((attempt) => attempt.result_status === "correct")
    .slice(0, 4);
  byId("recent-list").innerHTML = wins.length
    ? wins.map((attempt) => `
      <li><span>${escapeHtml(formatActivity(attempt.activity_id))}</span><span class="outcome correct">+${attempt.points}</span></li>`)
      .join("")
    : '<li class="muted">Solve correctly to record a win.</li>';
  byId("progress-summary").innerHTML = [
    ["Solved today", dashboard.solved_today],
    ["Total score", dashboard.score.toLocaleString()],
    ["Accuracy", `${dashboard.accuracy}%`],
    ["Average time", `${dashboard.average_seconds}s`],
  ].map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`).join("");
  byId("attempt-table").innerHTML = dashboard.recent_attempts.length
    ? dashboard.recent_attempts.map((attempt) => `
      <tr><td>${escapeHtml(formatActivity(attempt.activity_id))}</td><td>${attempt.difficulty}</td><td><span class="outcome ${attempt.result_status}">${attempt.result_status}</span></td><td>${attempt.points}</td></tr>`)
      .join("")
    : '<tr><td colspan="4" class="muted">Complete a challenge to begin your record.</td></tr>';
}

async function refreshDashboard() {
  state.dashboard = await api("/me/dashboard");
  renderDashboard();
}

async function refreshLeaderboard() {
  const entries = await api("/leaderboard");
  byId("leaderboard-table").innerHTML = entries.length
    ? entries.map((entry) => `
      <tr><td>${entry.rank}</td><td>${escapeHtml(entry.username)}</td><td>${entry.score.toLocaleString()}</td><td>${entry.accuracy}%</td></tr>`)
      .join("")
    : '<tr><td colspan="4" class="muted">The board is ready for its first precision run.</td></tr>';
}

function startTimer(task) {
  clearInterval(state.timer);
  function update() {
    const seconds = Math.max(0, Math.ceil((new Date(task.expires_at).getTime() - Date.now()) / 1000));
    const ratio = Math.min(100, Math.round((seconds / task.time_limit_seconds) * 100));
    byId("timer-value").textContent = seconds;
    byId("timer-ring").style.setProperty("--timer-progress", `${ratio}%`);
    if (seconds === 0 && !task.completed) {
      clearInterval(state.timer);
      byId("submit-answer").disabled = true;
      recordTimeout();
    }
  }
  state.timer = setInterval(update, 1000);
  update();
}

function configureAnswerControl(task) {
  const isChoice = task.answer_mode === "choice";
  byId("answer-input-wrap").classList.toggle("hidden", isChoice);
  byId("choice-options").classList.toggle("hidden", !isChoice);
  byId("answer-input").disabled = isChoice;
  byId("answer-input").required = !isChoice;
  byId("answer-input").value = "";
  byId("choice-options").querySelectorAll("button").forEach((button) => {
    button.classList.remove("selected");
    button.disabled = false;
  });
  byId("submit-answer").disabled = isChoice;
}

function resetTask() {
  clearInterval(state.timer);
  state.task = null;
  state.taskRequest++;
  byId("submit-answer").disabled = true;
  byId("answer-input").disabled = true;
  byId("choice-options").querySelectorAll("button").forEach((button) => { button.disabled = true; });
}

async function newTask(playSound = false) {
  if (!state.catalog || !state.user) return;
  if (playSound && state.preferences?.sound_enabled) MathBlitzAudio.unlock();
  resetTask();
  const request = state.taskRequest;
  byId("task-question").textContent = "Loading your next scenario...";
  byId("timer-value").textContent = "--";
  byId("hint-panel").classList.add("hidden");
  byId("hint-toggle").setAttribute("aria-expanded", "false");
  byId("hint-toggle").disabled = true;
  byId("task-result").classList.add("hidden");
  try {
    const task = await api("/tasks", {
      method: "POST",
      body: JSON.stringify({ activity_id: state.activityId, difficulty: state.difficulty }),
    });
    if (request !== state.taskRequest) return;
    state.task = { ...task, completed: false };
    const activity = activityById(task.activity_id);
    byId("task-activity").textContent = task.activity_name;
    byId("task-skill").textContent = activity.skill;
    byId("current-task-icon").className = `activity-icon accent-${activity.accent}`;
    byId("current-task-icon").innerHTML = iconFor(activity.icon);
    byId("task-question").textContent = task.prompt;
    byId("task-hint").textContent = task.hint;
    byId("hint-toggle").disabled = false;
    configureAnswerControl(task);
    startTimer(state.task);
    if (playSound && state.preferences?.sound_enabled) MathBlitzAudio.play("start");
  } catch (error) {
    if (request !== state.taskRequest) return;
    byId("task-question").textContent = "Choose New scenario to try again.";
    showTaskResult(error.message, false);
  }
}

async function selectActivity(activityId, begin = true) {
  state.activityId = activityId;
  syncSelections();
  if (begin) await newTask(true);
}

function showTaskResult(text, success) {
  const result = byId("task-result");
  result.textContent = text;
  result.classList.remove("hidden");
  result.classList.toggle("wrong", !success);
}

function applyResult(result) {
  const correct = result.result_status === "correct";
  const text = correct
    ? `Excellent. You earned ${result.points} focus points.`
    : result.result_status === "timeout"
      ? `Time elapsed. The solution was ${result.correct_answer}.`
      : `Close, but the solution was ${result.correct_answer}. Try the next scenario.`;
  showTaskResult(text, correct);
  if (state.preferences?.sound_enabled) MathBlitzAudio.play(result.result_status);
  clearInterval(state.timer);
  byId("answer-input").disabled = true;
  byId("submit-answer").disabled = true;
  byId("choice-options").querySelectorAll("button").forEach((button) => { button.disabled = true; });
}

async function finishTask(answer, timeout = false) {
  const task = state.task;
  if (!task || task.completed) return;
  task.completed = true;
  byId("submit-answer").disabled = true;
  try {
    const result = await api(`/tasks/${task.id}/submissions`, {
      method: "POST",
      body: JSON.stringify({ answer }),
    });
    if (task !== state.task) return;
    applyResult(result);
    Promise.allSettled([refreshDashboard(), refreshLeaderboard()]);
  } catch (error) {
    if (task !== state.task) return;
    task.completed = timeout;
    byId("submit-answer").disabled = timeout;
    showTaskResult(error.message, false);
  }
}

function recordTimeout() {
  return finishTask(0, true);
}

function submitAnswer(event) {
  event.preventDefault();
  if (state.preferences?.sound_enabled) MathBlitzAudio.unlock();
  return finishTask(byId("answer-input").value);
}

function selectView(viewName, move = true) {
  document.querySelectorAll(".nav-item").forEach((item) => {
    const active = item.dataset.view === viewName;
    item.classList.toggle("active", active);
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
  if (move) window.scrollTo(0, 0);
  document.querySelectorAll(".page").forEach((page) => {
    page.classList.toggle("active", page.id === `${viewName}-view`);
  });
  if (viewName === "leaderboard") refreshLeaderboard().catch(() => {});
}

async function savePreferences(event) {
  event.preventDefault();
  try {
    state.preferences = await api("/me/preferences", {
      method: "PATCH",
      body: JSON.stringify({
        default_activity_id: byId("settings-activity").value,
        default_difficulty: byId("settings-difficulty").value,
        sound_enabled: byId("settings-sound").checked,
      }),
    });
    setMessage(byId("settings-message"), "Preferences saved for your next session.", true);
  } catch (error) {
    setMessage(byId("settings-message"), error.message);
  }
}

async function startApplication() {
  byId("auth-view").classList.add("hidden");
  byId("app-view").classList.remove("hidden");
  byId("username-label").textContent = state.user.username;
  byId("workspace-mode").textContent = state.guest ? "Guest practice · Progress on this device" : "Practical scenario practice";
  byId("logout-button").textContent = state.guest ? "Exit guest practice" : "Sign out";
  byId("settings-music").checked = false;
  document.querySelector('[data-view="leaderboard"]').classList.toggle("hidden", state.guest);
  selectView("train");
  try {
    state.catalog = await api("/activities");
    renderCatalog();
    await Promise.all([loadPreferences(), refreshDashboard(), refreshLeaderboard()]);
    await newTask();
  } catch (error) {
    signOut();
    setMessage(byId("auth-message"), error.message);
  }
}

function bindEvents() {
  byId("guest-button").addEventListener("click", () => {
    state.guest = true;
    state.user = { username: "Guest" };
    startApplication();
  });
  byId("login-tab").addEventListener("click", () => showAuthTab(false));
  byId("register-tab").addEventListener("click", () => showAuthTab(true));
  byId("login-form").addEventListener("submit", (event) => authenticate(event, "login"));
  byId("register-form").addEventListener("submit", (event) => authenticate(event, "register"));
  byId("logout-button").addEventListener("click", signOut);
  byId("difficulty-buttons").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-level]");
    if (!button) return;
    state.difficulty = button.dataset.level;
    syncSelections();
    newTask(true);
  });
  byId("activity-cards").addEventListener("click", (event) => {
    const card = event.target.closest("button[data-activity]");
    if (card) selectActivity(card.dataset.activity);
  });
  byId("explore-grid").addEventListener("click", (event) => {
    const card = event.target.closest("button[data-activity]");
    if (!card) return;
    selectView("train");
    selectActivity(card.dataset.activity);
  });
  byId("explore-link").addEventListener("click", () => selectView("explore"));
  byId("choice-options").addEventListener("click", (event) => {
    const option = event.target.closest("button[data-answer]");
    if (!option || !state.task || state.task.completed) return;
    byId("answer-input").value = option.dataset.answer;
    byId("choice-options").querySelectorAll("button").forEach((button) => {
      button.classList.toggle("selected", button === option);
    });
    byId("submit-answer").disabled = false;
  });
  byId("hint-toggle").addEventListener("click", () => {
    const panel = byId("hint-panel");
    const expanded = panel.classList.toggle("hidden") === false;
    byId("hint-toggle").setAttribute("aria-expanded", String(expanded));
  });
  byId("new-task").addEventListener("click", () => newTask(true));
  byId("settings-sound").addEventListener("change", (event) => {
    if (event.target.checked) MathBlitzAudio.unlock().then((ready) => { if (ready) MathBlitzAudio.play("start"); });
  });
  byId("settings-music").addEventListener("change", async (event) => {
    const enabled = await MathBlitzAudio.setMusic(event.target.checked);
    event.target.checked = enabled;
  });
  byId("answer-form").addEventListener("submit", submitAnswer);
  byId("settings-form").addEventListener("submit", savePreferences);
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.addEventListener("click", () => selectView(item.dataset.view));
  });
}

async function bootstrap() {
  bindEvents();
  byId("account-controls").classList.toggle("hidden", guestOnly);
  if (!guestOnly && state.token && state.user) await startApplication();
}

bootstrap();
