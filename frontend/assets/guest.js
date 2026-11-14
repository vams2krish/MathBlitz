/* Local practice has its own data boundary; nothing is posted to the account API. */
globalThis.MathBlitzGuest = (() => {
  const KEY = "mathblitz_guest_v1";
  const defaults = { default_activity_id: "shopping-value", default_difficulty: "Very Easy", sound_enabled: false };
  let catalogPromise;
  let task;
  let lastPick = new Map();
  let data;

  function load() {
    if (data) return data;
    try { data = JSON.parse(localStorage.getItem(KEY)); } catch { /* Storage can be unavailable. */ }
    return data ||= { attempts: [], preferences: { ...defaults } };
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(data)); } catch { /* Keep this session usable. */ }
  }

  function bank() {
    return catalogPromise ||= fetch("/assets/guest-catalog.json")
      .then((response) => {
        if (!response.ok) throw new Error("The guest puzzle library could not be loaded.");
        return response.json();
      })
      .catch((error) => { catalogPromise = null; throw error; });
  }

  function dashboard() {
    const attempts = load().attempts;
    const correct = attempts.filter((entry) => entry.result_status === "correct");
    const today = new Date().toDateString();
    const firstMiss = attempts.findIndex((entry) => entry.result_status !== "correct");
    return {
      total_attempts: attempts.length,
      correct_attempts: correct.length,
      score: attempts.reduce((total, entry) => total + entry.points, 0),
      accuracy: attempts.length ? Math.round(1000 * correct.length / attempts.length) / 10 : 0,
      average_seconds: attempts.length ? Math.round(attempts.reduce((total, entry) => total + entry.duration_ms, 0) / attempts.length / 100) / 10 : 0,
      streak: firstMiss === -1 ? attempts.length : firstMiss,
      solved_today: correct.filter((entry) => new Date(entry.submitted_at).toDateString() === today).length,
      recent_attempts: attempts.slice(0, 20),
    };
  }

  async function request(path, options = {}) {
    if (path === "/activities") {
      const { activities, difficulties } = await bank();
      return { activities, difficulties };
    }
    if (path === "/leaderboard") return [];
    if (path === "/me/dashboard") return dashboard();
    if (path === "/me/preferences") {
      if (options.method === "PATCH") {
        load().preferences = JSON.parse(options.body);
        save();
      }
      return { ...load().preferences };
    }
    if (path === "/tasks") {
      const { activity_id, difficulty } = JSON.parse(options.body);
      const catalog = await bank();
      const activity = catalog.activities.find((entry) => entry.id === activity_id);
      const level = catalog.difficulties.find((entry) => entry.name === difficulty);
      const pool = catalog.puzzles[activity_id]?.[difficulty];
      if (!activity || !level || !pool?.length) throw new Error("Choose a valid scenario and level.");
      const key = `${activity_id}:${difficulty}`;
      const previous = lastPick.get(key);
      let pick = Math.floor(Math.random() * (pool.length - (previous === undefined ? 0 : 1)));
      if (previous !== undefined && pick >= previous) pick++;
      lastPick.set(key, pick);
      const [prompt, hint, answer_mode, answer] = pool[pick];
      const created = Date.now();
      const expires = created + level.time_limit_seconds * 1000;
      const publicTask = {
        id: `${created}-${Math.random().toString(36).slice(2)}`, activity_id, activity_name: activity.name,
        difficulty, prompt, hint, answer_mode,
        time_limit_seconds: level.time_limit_seconds, expires_at: new Date(expires).toISOString(),
      };
      task = { ...publicTask, answer, created, expires, level };
      return publicTask;
    }
    if (task && path === `/tasks/${task.id}/submissions`) {
      if (task.completed) throw new Error("This scenario has already been submitted.");
      const answer = JSON.parse(options.body).answer;
      if (answer === "" || answer === null || !Number.isFinite(Number(answer))) throw new Error("Enter a valid answer.");
      const now = Date.now();
      const elapsed = now - task.created;
      const tolerance = ["decimal", "currency"].includes(task.answer_mode) ? 0.01 : 0;
      const correct = Math.abs(Number(answer) - task.answer) <= tolerance + (tolerance ? 1e-9 : 0);
      const result_status = now >= task.expires ? "timeout" : correct ? "correct" : "incorrect";
      const points = result_status === "correct" ? task.level.points_multiplier * 10 + Math.floor((task.expires - now) / 5000) : 0;
      const result = { activity_id: task.activity_id, difficulty: task.difficulty, result_status, points,
        duration_ms: elapsed, submitted_at: new Date(now).toISOString() };
      task.completed = true;
      load().attempts.unshift(result);
      data.attempts.length = Math.min(data.attempts.length, 1000);
      save();
      return { ...result, correct_answer: task.answer };
    }
    throw new Error("This action is not available in guest mode.");
  }

  return { request, clearTask: () => { task = null; } };
})();
