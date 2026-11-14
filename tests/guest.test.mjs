import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const script = readFileSync(new URL('../frontend/assets/guest.js', import.meta.url), 'utf8');
const catalog = JSON.parse(readFileSync(new URL('../frontend/assets/guest-catalog.json', import.meta.url), 'utf8'));
const storage = new Map();
const key = 'mathblitz_guest_v1';

function guest(initialTime = Date.now()) {
  let clock = initialTime;
  const context = {
    fetch: async (path) => {
      assert.equal(path, '/assets/guest-catalog.json');
      return { ok: true, json: async () => catalog };
    },
    localStorage: { getItem: (name) => storage.get(name) ?? null, setItem: (name, value) => storage.set(name, value) },
    Date: class extends Date {
      constructor(...args) { super(...(args.length ? args : [clock])); }
      static now() { return clock; }
    },
  };
  runInNewContext(script, context);
  return { ...context.MathBlitzGuest, advance: (ms) => { clock += ms; } };
}

const params = { activity_id: 'shopping-value', difficulty: 'Very Easy' };
const issue = (app) => app.request('/tasks', { method: 'POST', body: JSON.stringify(params) });
const submit = (app, id, answer) => app.request(`/tasks/${id}/submissions`, { method: 'POST', body: JSON.stringify({ answer }) });
const answerTo = (task) => catalog.puzzles[task.activity_id][task.difficulty].find(([prompt]) => prompt === task.prompt)[3];

test('local practice grades answers once and preserves progress across sessions', async () => {
  storage.delete(key);
  const app = guest();
  const first = await issue(app);
  assert.equal('answer' in first, false);
  await assert.rejects(submit(app, first.id, ''), /valid answer/);
  app.advance(1000);
  const result = await submit(app, first.id, answerTo(first));
  assert.equal(result.result_status, 'correct');
  assert.equal(result.points, 27);
  await assert.rejects(submit(app, first.id, answerTo(first)), /already/);
  const second = await issue(app);
  assert.notEqual(second.prompt, first.prompt);
  app.advance(90_000);
  assert.equal((await submit(app, second.id, answerTo(second))).result_status, 'timeout');

  const afterRestart = await guest().request('/me/dashboard');
  assert.equal(afterRestart.total_attempts, 2);
  assert.equal(afterRestart.correct_attempts, 1);
  assert.equal(afterRestart.score, 27);
  assert.equal(afterRestart.accuracy, 50);
});

test('guest preferences persist separately from accounts and invalid actions fail', async () => {
  storage.delete(key);
  const app = guest();
  const preferences = { default_activity_id: 'recipe-scaling', default_difficulty: 'Easy', sound_enabled: true };
  await app.request('/me/preferences', { method: 'PATCH', body: JSON.stringify(preferences) });
  assert.deepEqual(JSON.parse(JSON.stringify(await guest().request('/me/preferences'))), preferences);
  const dismissed = await issue(app);
  app.clearTask();
  await assert.rejects(submit(app, dismissed.id, 1), /not available/);
  await assert.rejects(app.request('/auth/register'), /not available/);
});
