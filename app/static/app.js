/* ============================================================
   PyForge frontend — a small hand-rolled SPA.
   Two views: dashboard (learning path) and project workspace.
   ============================================================ */
const $main = document.getElementById('main');
let curriculum = null;      // /api/curriculum payload
const editors = {};         // exercise_id -> CodeMirror instance

/* Graceful degradation if CDN scripts are unavailable (e.g. offline):
   - md(): fall back from marked to simple paragraph/bold rendering
   - makeEditor(): fall back from CodeMirror to a styled <textarea> */
function md(t) {
  if (window.marked) return marked.parse(t);
  // offline fallback: code fences, inline code, bold, paragraphs
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const blocks = [];
  t = t.replace(/```(?:\w+)?\n([\s\S]*?)```/g, (_, code) => {
    blocks.push('<pre><code>' + esc(code) + '</code></pre>');
    return '\u0000' + (blocks.length - 1) + '\u0000';
  });
  t = esc(t)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  t = '<p>' + t.replace(/\n\n/g, '</p><p>') + '</p>';
  return t.replace(/\u0000(\d+)\u0000/g, (_, i) => blocks[+i]);
}

/* Live linting: as the learner types (600ms debounce), send the code to the
   backend, which runs a syntax check + pyflakes, and render the problems as
   gutter markers with hover tooltips. */
function lintViaBackend(code, updateLinting, options, cm) {
  const toMarkers = (problems) => (problems || []).map(p => ({
    from: CodeMirror.Pos(p.line - 1, Math.max(0, (p.col || 1) - 1)),
    to: CodeMirror.Pos(p.line - 1, p.col || 1),
    message: p.message,
    severity: p.severity || 'warning',
  }));

  if (isHosted()) {                       // hosted: lint in the browser too
    lintInBrowser(code)
      .then(problems => updateLinting(cm, toMarkers(problems)))
      .catch(() => updateLinting(cm, []));
    return;
  }
  fetch('/api/lint', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  })
    .then(r => r.json())
    .then(d => updateLinting(cm, toMarkers(d.problems)))
    .catch(() => updateLinting(cm, []));   // backend unreachable: no markers
}

function makeEditor(textarea) {
  if (window.CodeMirror) {
    // If the lint addon failed to load, the 'lint' option is simply inert and
    // the extra gutter stays empty — everything else keeps working.
    return CodeMirror.fromTextArea(textarea, {
      mode: 'python', theme: 'material-darker', lineNumbers: true,
      indentUnit: 4, viewportMargin: Infinity,
      gutters: ['CodeMirror-lint-markers', 'CodeMirror-linenumbers'],
      lint: { async: true, getAnnotations: lintViaBackend, delay: 600 },
    });
  }
  // minimal CodeMirror-compatible shim around the raw textarea
  textarea.style.cssText = 'width:100%;min-height:160px;background:#0a0e16;color:#e7edf7;' +
    'border:1px solid var(--border);border-radius:10px;padding:12px;font-family:ui-monospace,Consolas,monospace;font-size:13.5px;';
  return {
    getValue: () => textarea.value,
    setValue: (v) => { textarea.value = v; },
    refresh: () => {},
  };
}

const api = {
  get: (u) => fetch(u, { credentials: 'same-origin' }).then(r => r.json()),
  post: (u, body) => fetch(u, { method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body) }).then(r => r.json()),
};

/* ============================================================
   Runtime layer.

   local mode  : the server runs exercises in a sandbox (localhost only).
   hosted mode : exercises run in THIS browser via Pyodide, so a public
                 deployment never executes visitor code on the server.
   ============================================================ */
const STATE = {
  mode: 'local', authEnabled: false, user: null,
  pyodideUrl: null, pyodide: null, pyodideStatus: 'idle', pyflakes: null,
};
const isHosted = () => STATE.mode === 'hosted';

/* Anonymous progress lives in the browser. Wrapped because storage can be
   unavailable (private mode, embedded frames) — then we degrade to memory. */
const LocalProgress = {
  KEY: 'pyforge_progress_v1',
  _memory: null,
  _store() {
    try { window.localStorage.setItem('__t', '1'); window.localStorage.removeItem('__t'); return window.localStorage; }
    catch (e) { return null; }
  },
  read() {
    const s = this._store();
    if (!s) return this._memory || (this._memory = { exercises: {}, milestones: {} });
    try { return JSON.parse(s.getItem(this.KEY)) || { exercises: {}, milestones: {} }; }
    catch (e) { return { exercises: {}, milestones: {} }; }
  },
  write(p) {
    const s = this._store();
    if (!s) { this._memory = p; return; }
    try { s.setItem(this.KEY, JSON.stringify(p)); } catch (e) { this._memory = p; }
  },
  setExercise(id, passed) {
    const p = this.read();
    if (passed) p.exercises[id] = true; else delete p.exercises[id];
    this.write(p);
  },
  setMilestone(pid, idx, done) {
    const p = this.read();
    const set = new Set(p.milestones[pid] || []);
    done ? set.add(idx) : set.delete(idx);
    p.milestones[pid] = [...set].sort((a, b) => a - b);
    this.write(p);
    return p.milestones[pid];
  },
  isEmpty() {
    const p = this.read();
    return !Object.keys(p.exercises).length && !Object.keys(p.milestones).length;
  },
  clear() { const s = this._store(); if (s) { try { s.removeItem(this.KEY); } catch (e) {} } this._memory = null; },
};

/* Overlay anonymous progress onto a server payload that has none. */
function applyLocalProgress(curr) {
  if (!isHosted() || STATE.user) return curr;
  const local = LocalProgress.read();
  curr.progress = local;
  for (const p of curr.projects) {
    p.exercises_done = (p.exercise_ids || []).filter(id => local.exercises[id]).length;
    p.milestones_done = (local.milestones[p.id] || []).length;
  }
  return curr;
}

/* ---------------- Pyodide boot ---------------- */
function banner(html, warn) {
  const el = document.getElementById('runtime-banner');
  el.className = warn ? 'warn' : '';
  el.innerHTML = html || '';
}

async function ensurePyodide(onProgress) {
  if (STATE.pyodide) return STATE.pyodide;
  if (STATE.pyodideStatus === 'loading') {
    while (STATE.pyodideStatus === 'loading') await new Promise(r => setTimeout(r, 200));
    return STATE.pyodide;
  }
  STATE.pyodideStatus = 'loading';
  const url = STATE.pyodideUrl;
  onProgress && onProgress('Starting the Python runtime (one-off ~10 MB download)…');
  try {
    if (!window.loadPyodide) {
      await new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = url + 'pyodide.js';
        s.onload = resolve;
        s.onerror = () => reject(new Error('could not load pyodide.js from ' + url));
        document.head.appendChild(s);
      });
    }
    STATE.pyodide = await loadPyodide({ indexURL: url });
    STATE.pyodideStatus = 'ready';
    banner('');
    return STATE.pyodide;
  } catch (e) {
    STATE.pyodideStatus = 'failed';
    banner('⚠ Could not start the in-browser Python runtime from <code>' + url +
           '</code>. Exercises can\'t run until it loads — check the network tab, or ' +
           'set <code>PYODIDE_INDEX_URL</code> to a reachable full Pyodide distribution.', true);
    throw e;
  }
}

/* Run learner code + the exercise's checks, exactly like the server sandbox:
   a fresh globals dict per run, stdout captured, asserts decide pass/fail. */
async function runInBrowser(code, checkCode, onProgress) {
  const py = await ensurePyodide(onProgress);
  const script =
    '_USER_SOURCE = ' + JSON.stringify(code) + '\n' +
    code + '\n\n# ---- exercise checks ----\n' + checkCode;

  let out = '';
  py.setStdout({ batched: (s) => { out += s + '\n'; } });
  py.setStderr({ batched: (s) => { out += s + '\n'; } });

  try {
    onProgress && onProgress('Loading Python packages…');
    await py.loadPackagesFromImports(script);
  } catch (e) {
    return { passed: false, output: out, error: 'Could not load a required package: ' + e.message };
  }
  onProgress && onProgress('');

  const globals = py.globals.get('dict')();
  try {
    await py.runPythonAsync(script, { globals });
    return { passed: true, output: out, error: '' };
  } catch (e) {
    const lines = String(e.message || e).trim().split('\n');
    return { passed: false, output: out, error: lines.slice(-14).join('\n') };
  } finally {
    globals.destroy();
  }
}

/* Linting in the browser: syntax errors always, pyflakes warnings when the
   package is available (installed once, in the background). */
async function lintInBrowser(code) {
  if (!STATE.pyodide) return [];              // don't boot the runtime just to lint
  const py = STATE.pyodide;
  if (STATE.pyflakes === null) {
    STATE.pyflakes = false;
    py.runPythonAsync(`
import micropip
await micropip.install("pyflakes")
`).then(() => { STATE.pyflakes = true; }).catch(() => { STATE.pyflakes = false; });
  }
  const src = JSON.stringify(code);
  try {
    const json = await py.runPythonAsync(`
import json
_problems = []
_src = ${src}
try:
    compile(_src, "<exercise>", "exec")
except SyntaxError as e:
    _problems.append({"line": e.lineno or 1, "col": e.offset or 1,
                      "message": "SyntaxError: " + str(e.msg), "severity": "error"})
if not _problems:
    try:
        import io, re
        from pyflakes.api import check
        from pyflakes.reporter import Reporter
        _o, _e = io.StringIO(), io.StringIO()
        check(_src, "<exercise>", Reporter(_o, _e))
        for _line in _o.getvalue().splitlines():
            _m = re.match(r"^<exercise>:(\\d+):(\\d+):?\\s*(.*)$", _line)
            if _m:
                _problems.append({"line": int(_m.group(1)), "col": int(_m.group(2)),
                                  "message": _m.group(3), "severity": "warning"})
    except Exception:
        pass
json.dumps(_problems)
`);
    return JSON.parse(json);
  } catch (e) {
    return [];
  }
}

/* ---------------- dashboard ---------------- */
async function showDashboard() {
  const payload = await api.get('/api/curriculum');
  // Read the mode BEFORE overlaying local progress — applyLocalProgress needs
  // to know we're hosted, and STATE starts out assuming local mode.
  STATE.mode = payload.mode || 'local';
  STATE.authEnabled = !!payload.auth_enabled;
  STATE.user = payload.user || null;
  STATE.pyodideUrl = payload.pyodide_index_url || STATE.pyodideUrl;
  curriculum = applyLocalProgress(payload);
  renderAuth();
  renderFooter();
  await maybeMergeLocalProgress();
  updateHeader();
  const byId = Object.fromEntries(curriculum.projects.map(p => [p.id, p]));
  const nProjects = curriculum.projects.length;
  const nInterview = curriculum.projects.reduce((a, p) => a + (p.interview_total || 0), 0);
  const F = window.PyForgeFeatures;
  let html = `
    <div class="hero">
      <h2>Your path to professional data engineering</h2>
      <p>${nProjects} real projects across ${curriculum.stages.length} stages — Python, algorithms,
         SQL &amp; NoSQL databases, ETL engineering, Spark, Airflow, and AI. Each project has build
         milestones, in-app coding exercises with instant checks, an <b>Under&nbsp;the&nbsp;Hood</b>
         deep-dive into the machinery, and <b>${nInterview} interview questions</b> with worked
         answers at LeetCode standard.</p>
    </div>`;
  for (const st of curriculum.stages) {
    html += `<div class="stage-label">${st.title}</div><div class="path">`;
    for (const pid of st.project_ids) {
      const p = byId[pid];
      if (!p) continue;
      const total = p.exercises_total + p.milestones_total;
      const done = p.exercises_done + p.milestones_done;
      const pct = total ? Math.round(done / total * 100) : 0;
      const tierChip = F ? F.stackChip(p.stack_tier) : '';
      html += `
        <div class="pcard ${pct === 100 ? 'done' : ''}" onclick="showProject('${p.id}')">
          <div class="num" style="--pct:${pct}"><span>${pct === 100 ? '✓' : p.num}</span></div>
          <div>
            <h3>${p.title}</h3>
            <div class="tag">${p.tagline}</div>
            <div class="chips">
              <span class="chip level">${p.level}</span>
              ${tierChip}
              ${p.tech.slice(0, 4).map(t => `<span class="chip">${t}</span>`).join('')}
            </div>
          </div>
          <div class="pmeta">
            <div><b>${p.exercises_done}/${p.exercises_total}</b> exercises</div>
            <div><b>${p.milestones_done}/${p.milestones_total}</b> milestones</div>
            <div><b>${p.interview_total}</b> interview Q&amp;A · ~${p.est_hours}h</div>
          </div>
        </div>`;
    }
    html += `</div>`;
  }
  if (F && F.enhanceDashboardHtml) html = F.enhanceDashboardHtml(html);
  $main.innerHTML = html;
  // Always explain the hosted setup \u2014 including when sign-in is unavailable,
  // so nobody is left wondering where the login button went.
  if (isHosted() && !STATE.user) {
    banner(STATE.authEnabled
      ? 'Your Python runs in this browser \u2014 no code is sent to a server. ' +
        'Progress is saved on this device; <a href="/auth/login?next=/">sign in with GitHub</a> ' +
        'to keep it across devices.'
      : 'Your Python runs in this browser \u2014 no code is sent to a server. ' +
        'Progress is saved on this device. GitHub sign-in is not configured on ' +
        'this deployment, so there is nothing to log in to.');
  }
  window.scrollTo(0, 0);
}

function updateHeader() {
  if (!curriculum) return;
  const prog = curriculum.progress || { exercises: {}, milestones: {} };
  let done = 0, total = 0;
  for (const p of curriculum.projects) {
    total += p.exercises_total + p.milestones_total;
    done += (prog.milestones[p.id] || []).length;
  }
  done += Object.keys(prog.exercises || {}).length;
  const pct = total ? Math.round(done / total * 100) : 0;
  document.getElementById('hdr-bar').style.width = pct + '%';
  document.getElementById('hdr-count').textContent = `${pct}% of the path`;
}

/* Header progress after a change, without a full dashboard reload. */
async function refreshHeaderProgress() {
  if (isHosted() && !STATE.user) {
    curriculum.progress = LocalProgress.read();
  } else {
    try { curriculum.progress = await api.get('/api/progress'); } catch (e) { return; }
  }
  updateHeader();
}

function renderAuth() {
  const el = document.getElementById('hdr-auth');
  // Local mode is single-user by design — there is nothing to sign in to.
  // Say so plainly, since it's the obvious question when the button is absent.
  if (!isHosted()) {
    el.innerHTML = '<span class="mode-chip" title="Running on your machine: ' +
      'exercises execute locally and progress is yours alone. Sign-in exists ' +
      'only in hosted mode.">local mode</span>';
    return;
  }
  if (!STATE.authEnabled) { el.innerHTML = ''; return; }
  if (STATE.user) {
    const u = STATE.user;
    el.innerHTML =
      `${u.avatar_url ? `<img class="avatar" src="${u.avatar_url}" alt="">` : ''}` +
      `<button class="signout" onclick="location.href='/auth/logout'" title="Signed in as ${u.login}">Sign out</button>`;
  } else {
    el.innerHTML = `<a class="signin" href="/auth/login?next=/" title="Save progress across devices">
      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>
      Sign in</a>`;
  }
}

function renderFooter() {
  const el = document.getElementById('footer');
  if (!el) return;
  if (!isHosted()) {
    el.textContent = 'PyForge · your progress is saved automatically · full stack docs in RUNBOOK.md';
  } else if (STATE.user) {
    el.textContent = 'PyForge · Python runs in your browser · progress saved to your account';
  } else {
    el.textContent = 'PyForge · Python runs in your browser · progress saved on this device';
  }
}

/* First sign-in: fold whatever the visitor did anonymously into their account. */
async function maybeMergeLocalProgress() {
  if (!isHosted() || !STATE.user || LocalProgress.isEmpty()) return;
  try {
    const out = await api.post('/api/progress/merge', { progress: LocalProgress.read() });
    if (out && out.progress) {
      curriculum.progress = out.progress;
      LocalProgress.clear();
      curriculum = await api.get('/api/curriculum');   // refresh the per-project counts
    }
  } catch (e) { /* keep local copy if the merge fails */ }
}

/* ---------------- project view ---------------- */
let current = null;   // { project, exercises_passed, milestones_done }

async function showProject(pid) {
  current = await api.get('/api/project/' + pid);
  // Anonymous hosted visitors keep progress in the browser, not on the server.
  if (isHosted() && !STATE.user) {
    const local = LocalProgress.read();
    for (const e of current.project.exercises) {
      current.exercises_passed[e.id] = !!local.exercises[e.id];
    }
    current.milestones_done = local.milestones[pid] || [];
  }
  const p = current.project;
  if (window.PyForgeFeatures) {
    window.PyForgeFeatures.track('project_open', { project_id: p.id });
  }
  const tier = p.stack_tier || 'light';
  const stackNote = tier === 'light'
    ? `Base stack only — <code>${p.environment.command}</code>`
    : `This project needs a higher stack tier (${tier}). Start it when you reach the Environment tab: <code>${p.environment.command}</code>`;
  $main.innerHTML = `
    <button class="back" onclick="showDashboard()">← Back to the path</button>
    <div class="proj-head">
      <h2>${p.num}. ${p.title}</h2>
      <div class="tag">${p.tagline}</div>
      <div class="chips" style="margin-top:10px">
        <span class="chip level">${p.level}</span>
        ${window.PyForgeFeatures ? window.PyForgeFeatures.stackChip(tier) : ''}
        ${p.tech.map(t => `<span class="chip">${t}</span>`).join('')}
        <span class="chip">~${p.est_hours}h</span>
      </div>
      <div class="stack-banner">${stackNote}</div>
    </div>
    <div class="tabs">
      <div class="tab active" data-tab="brief" onclick="switchTab('brief')">Brief</div>
      <div class="tab" data-tab="milestones" onclick="switchTab('milestones')">Milestones</div>
      <div class="tab" data-tab="exercises" onclick="switchTab('exercises')">Exercises</div>
      <div class="tab" data-tab="hood" onclick="switchTab('hood')">Under the Hood</div>
      <div class="tab" data-tab="interview" onclick="switchTab('interview')">Interview Q&amp;A${p.interview.length ? ` (${p.interview.length})` : ''}</div>
      <div class="tab" data-tab="env" onclick="switchTab('env')">Environment</div>
    </div>
    <div id="tab-content"></div>`;
  switchTab('brief');
  window.scrollTo(0, 0);
}

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t =>
    t.classList.toggle('active', t.dataset.tab === name));
  const p = current.project;
  const el = document.getElementById('tab-content');

  if (name === 'brief') {
    el.innerHTML = `<div class="panel">${md(p.brief)}</div>`;

  } else if (name === 'milestones') {
    el.innerHTML = `<div class="panel">` + p.milestones.map((m, i) => `
      <div class="milestone ${current.milestones_done.includes(i) ? 'done' : ''}" onclick="toggleMilestone(${i}, this)">
        <div class="box">${current.milestones_done.includes(i) ? '✓' : ''}</div>
        <div class="txt">${m}</div>
      </div>`).join('') + `</div>`;

  } else if (name === 'hood') {
    el.innerHTML = `<div class="panel">${md(p.under_the_hood)}</div>`;

  } else if (name === 'interview') {
    if (!p.interview.length) {
      el.innerHTML = `<div class="panel">No interview questions for this project yet.</div>`;
    } else {
      el.innerHTML = `
        <div class="iv-intro">Try each question on paper (or in the Exercises editor) <b>before</b>
          revealing the answer — retrieval practice is what makes it stick in a real interview.</div>` +
        p.interview.map((q, i) => `
        <div class="ivq" id="ivq-${i}">
          <div class="ivq-head">
            <span class="ivq-num">Q${i + 1}</span>
            <span class="chip ${(q.difficulty || '').toLowerCase()}">${q.difficulty || 'Medium'}</span>
            ${(q.topics || []).map(t => `<span class="chip">${t}</span>`).join('')}
          </div>
          <div class="ivq-body">${md(q.question)}</div>
          <button class="reveal" onclick="revealAnswer(${i})" id="rv-${i}">Show answer &amp; explanation ▾</button>
          <div class="ivq-answer" id="iva-${i}">
            <div class="ans-label">Answer</div>
            ${md(q.answer)}
            <div class="ans-label">Why this is the answer</div>
            ${md(q.explanation)}
          </div>
        </div>`).join('');
    }

  } else if (name === 'env') {
    const e = p.environment;
    const tier = p.stack_tier || 'light';
    el.innerHTML = `<div class="panel">
      <h4 style="margin-top:0">Progressive stack unlock</h4>
      <p>Only start what this project needs — don't bring up Spark/Airflow early.</p>
      <p>${window.PyForgeFeatures ? window.PyForgeFeatures.stackChip(tier) : tier}</p>
      <h4>What must be running</h4>
      <p>${e.services.map(s => `• ${s}`).join('<br>')}</p>
      <h4>One command for this tier</h4>
      <code class="cmd">${e.command}</code>
      <button class="reset" style="margin-left:8px" onclick="copyText('${e.command.replace(/'/g, "\\'")}').then(()=>alert('Copied'))">Copy</button>
      <div class="env-note">${e.note}</div>
      <p style="margin-top:14px;color:var(--muted)">See <b>RUNBOOK.md</b> for ports, credentials, and troubleshooting.</p>
    </div>`;

  } else if (name === 'exercises') {
    const F = window.PyForgeFeatures;
    el.innerHTML = p.exercises.map((ex, i) => `
      <div class="ex ${current.exercises_passed[ex.id] ? 'passed' : ''} ${i === 0 ? 'open' : ''}" id="ex-${ex.id}">
        <div class="ex-head" onclick="toggleEx('${ex.id}')">
          <div class="status"></div>
          <h4>${ex.title}</h4>
          <span class="hint">${ex.heavy ? '⚡ boots local Spark (~1 min)' : ''}
            ${current.exercises_passed[ex.id] ? ' passed ✓' : ''}</span>
        </div>
        <div class="ex-body">

          ${ex.refresher ? `
          <div class="refresher ${i === 0 ? 'open' : ''}" id="ref-${ex.id}">
            <div class="refresher-head" onclick="document.getElementById('ref-${ex.id}').classList.toggle('open')">
              📚 Concept refresher — read me first
              <span class="caret">▸</span>
            </div>
            <div class="refresher-body">${md(ex.refresher)}</div>
          </div>` : ''}

          ${ex.objectives.length ? `
          <div class="objectives">
            <div class="obj-title">After this exercise you can</div>
            ${ex.objectives.map(o => `<div class="obj">${o}</div>`).join('')}
          </div>` : ''}

          <div class="instructions">${md(ex.instructions)}</div>

          ${localOnly(ex) && F ? F.localLaunchHtml(ex) : ''}

          ${F ? F.mentorPanelHtml(ex) : ''}

          ${localOnly(ex) ? '' : `<textarea id="code-${ex.id}"></textarea>`}

          <div class="ex-actions">
            ${localOnly(ex) ? '' :
              `<button class="run" onclick="runExercise('${ex.id}', ${!!ex.heavy})">Run &amp; Check ▸</button>`}
            ${ex.hints.length ? `<button class="hint-btn" id="hintbtn-${ex.id}" onclick="showHint('${ex.id}')">💡 Hint (0/${ex.hints.length})</button>` : ''}
            ${localOnly(ex) ? '' : `<button class="reset" onclick="resetExercise('${ex.id}')">Reset</button>`}
            <div class="spinner" id="spin-${ex.id}"></div>
            <span class="heavy-note" id="note-${ex.id}"></span>
            ${(!localOnly(ex) && ex.packages && ex.packages.length && isHosted())
              ? `<span class="pkg-note">first run downloads ${ex.packages.join(' + ')}</span>` : ''}
            ${(ex.heavy && !isHosted()) ? '<span class="heavy-note">real Spark session — be patient on first run</span>' : ''}
          </div>
          <div id="hints-${ex.id}"></div>
          <div class="result" id="res-${ex.id}"></div>
          ${F ? F.solutionsSlotHtml(ex) : ''}

          ${ex.resources.length ? `
          <div class="resources">
            <div class="res-title">Learn more</div>
            ${ex.resources.map(r => `<a href="${r.url}" target="_blank" rel="noopener">${r.title}</a>`).join('')}
          </div>` : ''}
        </div>
      </div>`).join('');
    for (const ex of p.exercises) {
      if (localOnly(ex)) continue;
      const ta = document.getElementById('code-' + ex.id);
      ta.value = ex.starter_code;
      editors[ex.id] = makeEditor(ta);
      hintsShown[ex.id] = 0;
      if (F) {
        F.track('exercise_open', { exercise_id: ex.id, project_id: p.id });
        if (current.exercises_passed[ex.id]) F.loadCommunitySolutions(ex.id);
      }
    }
    if (isHosted() && p.exercises.some(e => !localOnly(e))) {
      ensurePyodide(msg => banner(msg)).then(() => banner('')).catch(() => {});
    }
  }
}

/* An exercise the browser genuinely cannot run (real Spark, i.e. a JVM). */
function localOnly(ex) {
  return isHosted() && ex.runtime === 'local';
}

/* -------- progressive hints -------- */
const hintsShown = {};   // exercise_id -> how many hints revealed

function showHint(id) {
  const ex = current.project.exercises.find(e => e.id === id);
  const n = hintsShown[id] || 0;
  if (n >= ex.hints.length) return;
  const box = document.getElementById('hints-' + id);
  const div = document.createElement('div');
  div.className = 'hint';
  div.innerHTML = '💡 ' + ex.hints[n];
  box.appendChild(div);
  hintsShown[id] = n + 1;
  const btn = document.getElementById('hintbtn-' + id);
  btn.textContent = `💡 Hint (${hintsShown[id]}/${ex.hints.length})`;
  if (hintsShown[id] >= ex.hints.length) btn.disabled = true;
}

function revealAnswer(i) {
  document.getElementById('ivq-' + i).classList.add('open');
  document.getElementById('rv-' + i).style.display = 'none';
}

function toggleEx(id) {
  document.getElementById('ex-' + id).classList.toggle('open');
  const ed = editors[id];
  if (ed) setTimeout(() => ed.refresh(), 0);
}

function resetExercise(id) {
  const ex = current.project.exercises.find(e => e.id === id);
  editors[id].setValue(ex.starter_code);
  const res = document.getElementById('res-' + id);
  res.className = 'result';
}

async function runExercise(id, heavy) {
  const btn = document.querySelector(`#ex-${id} button.run`);
  const spin = document.getElementById('spin-' + id);
  const res = document.getElementById('res-' + id);
  const note = document.getElementById('note-' + id);
  const code = editors[id].getValue();
  const say = (msg) => { if (note) note.textContent = msg || ''; };
  const F = window.PyForgeFeatures;

  btn.disabled = true; spin.style.display = 'block'; res.className = 'result';
  if (F) F.track('exercise_run', { exercise_id: id, project_id: current.project.id });

  try {
    const out = isHosted()
      ? await runInBrowser(code, current.project.exercises.find(e => e.id === id).check_code, say)
      : await api.post('/api/run', { project_id: current.project.id, exercise_id: id, code });
    say('');

    if (out.passed) {
      res.className = 'result ok';
      res.textContent = (out.output || 'Passed!').trim();
      current.exercises_passed[id] = true;
      document.getElementById('ex-' + id).classList.add('passed');
      await recordExercise(id, true);
      if (F) {
        F.ReviewState.markPassed(id);
        F.track('exercise_pass', { exercise_id: id, project_id: current.project.id });
        F.loadCommunitySolutions(id);
      }
      confettiPulse();
    } else {
      res.className = 'result err';
      res.textContent = ((out.output ? out.output + '\n' : '') + (out.error || 'Failed')).trim();
      if (F) {
        F.ReviewState.bumpFail(id);
        F.track('exercise_fail', { exercise_id: id, project_id: current.project.id });
        F.refreshMentor(id);
      }
    }
  } catch (e) {
    say('');
    res.className = 'result err';
    res.textContent = 'Could not run this exercise: ' + (e.message || e);
    if (F) {
      F.ReviewState.bumpFail(id);
      F.track('exercise_fail', { exercise_id: id, project_id: current.project.id });
      F.refreshMentor(id);
    }
  }
  btn.disabled = false; spin.style.display = 'none';
}

/* Where a pass gets recorded: the account when signed in, otherwise this
   browser. Local mode records server-side as it always did. */
async function recordExercise(id, passed) {
  if (isHosted() && !STATE.user) { LocalProgress.setExercise(id, passed); return; }
  if (isHosted()) { await api.post('/api/progress/exercise', { exercise_id: id, passed }); return; }
  // local mode already recorded it as part of /api/run
}

async function toggleMilestone(i, node) {
  const nowDone = !node.classList.contains('done');
  node.classList.toggle('done', nowDone);
  node.querySelector('.box').textContent = nowDone ? '✓' : '';

  if (isHosted() && !STATE.user) {
    current.milestones_done = LocalProgress.setMilestone(current.project.id, i, nowDone);
  } else {
    const out = await api.post('/api/milestone', {
      project_id: current.project.id, index: i, done: nowDone });
    current.milestones_done = out.milestones_done || [];
  }
  refreshHeaderProgress();
}

/* Tiny celebration: pulse the header bar */
function confettiPulse() {
  const bar = document.getElementById('hdr-bar');
  bar.style.transition = 'none'; bar.style.filter = 'brightness(1.8)';
  setTimeout(() => { bar.style.transition = ''; bar.style.filter = ''; }, 350);
  refreshHeaderProgress();
}

(async function boot() {
  const F = window.PyForgeFeatures;
  if (F && await F.consumeDeepLink()) return;
  await showDashboard();
})();
