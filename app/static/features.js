/* ============================================================
   PyForge learning features: onboarding, stack unlock, mentor,
   spaced review, portfolio, analytics, community solutions,
   local deep-links.
   ============================================================ */

const ReviewState = {
  KEY: 'pyforge_review_v1',
  _read() {
    try { return JSON.parse(localStorage.getItem(this.KEY)) || {}; }
    catch (e) { return {}; }
  },
  _write(s) {
    try { localStorage.setItem(this.KEY, JSON.stringify(s)); } catch (e) {}
  },
  get() {
    const s = this._read();
    s.exercise_passed_at = s.exercise_passed_at || {};
    s.exercise_fails = s.exercise_fails || {};
    s.interview_reviewed_at = s.interview_reviewed_at || {};
    return s;
  },
  bumpFail(id) {
    const s = this.get();
    s.exercise_fails[id] = (s.exercise_fails[id] || 0) + 1;
    this._write(s);
    return s.exercise_fails[id];
  },
  markPassed(id) {
    const s = this.get();
    s.exercise_passed_at[id] = new Date().toISOString();
    this._write(s);
  },
  markInterview(pid, idx) {
    const s = this.get();
    s.interview_reviewed_at[`${pid}:${idx}`] = new Date().toISOString();
    this._write(s);
  },
  fails(id) { return this.get().exercise_fails[id] || 0; },
};

const Onboarding = {
  KEY: 'pyforge_onboarding_v1',
  done() {
    try { return localStorage.getItem(this.KEY) === '1'; } catch (e) { return false; }
  },
  complete() {
    try { localStorage.setItem(this.KEY, '1'); } catch (e) {}
    track('onboarding_complete');
  },
};

const ResumeState = {
  KEY: 'pyforge_resume_v1',
  save(partial) {
    const prev = this.get() || {};
    const next = Object.assign({}, prev, partial || {}, { at: new Date().toISOString() });
    try { localStorage.setItem(this.KEY, JSON.stringify(next)); } catch (e) {}
  },
  get() {
    try { return JSON.parse(localStorage.getItem(this.KEY)) || null; }
    catch (e) { return null; }
  },
  clear() {
    try { localStorage.removeItem(this.KEY); } catch (e) {}
  },
};

function track(event, extra) {
  const body = Object.assign({ event }, extra || {});
  try {
    fetch('/api/analytics/event', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).catch(() => {});
  } catch (e) {}
}

function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const ta = document.createElement('textarea');
  ta.value = text; document.body.appendChild(ta); ta.select();
  document.execCommand('copy'); document.body.removeChild(ta);
  return Promise.resolve();
}

function stackChip(tier) {
  const labels = {
    light: 'base stack',
    db: 'needs databases',
    spark: 'needs Spark',
    full: 'full stack',
  };
  return `<span class="chip stack-${tier || 'light'}">${labels[tier] || tier}</span>`;
}

/* ---------- dashboard enhancements ---------- */
function resolveResume(cur) {
  const saved = ResumeState.get();
  if (!saved || !saved.project_id || !cur) return null;
  const proj = (cur.projects || []).find(p => p.id === saved.project_id);
  if (!proj) return null;
  let exerciseTitle = null;
  if (saved.exercise_id) {
    const ex = (proj.exercises || []).find(e => e.id === saved.exercise_id);
    exerciseTitle = (ex && ex.title) || saved.exercise_id;
  }
  return {
    project_id: proj.id,
    exercise_id: saved.exercise_id || null,
    project_title: proj.title,
    exercise_title: exerciseTitle,
  };
}

function dashboardHeroCtaHtml(cur) {
  const resume = resolveResume(cur);
  const fh = cur && cur.first_hour;
  const stats = (cur && cur.stats) || {};
  const primary = resume
    ? `<button type="button" class="cta-primary" onclick="resumeLearning()">Resume ${escapeHtml(resume.project_title)}${resume.exercise_title ? ' · ' + escapeHtml(resume.exercise_title) : ''} ▸</button>`
    : (fh && !Onboarding.done()
      ? `<button type="button" class="cta-primary" onclick="startFirstHour()">Start first hour ▸</button>`
      : `<button type="button" class="cta-primary" onclick="startFirstHour()">Start first hour ▸</button>`);
  const secondary = resume && fh
    ? `<button type="button" class="cta-secondary" onclick="startFirstHour()">First hour</button>`
    : `<button type="button" class="cta-secondary" onclick="showReviewDesk()">Review desk</button>`;

  return `
    <div class="cta-row">
      ${primary}
      ${secondary}
      <button type="button" class="cta-secondary" onclick="showPortfolioDesk()">Portfolio</button>
      <details class="more-tools">
        <summary>More</summary>
        <div class="more-panel">
          <button type="button" onclick="showReviewDesk()">Review desk</button>
          <button type="button" onclick="startFirstHour()">Restart first hour</button>
          <button type="button" onclick="showFrictionDesk()">Friction report</button>
        </div>
      </details>
    </div>
    <p class="tool-meta" style="margin-top:12px">${stats.pct || 0}% path · ${stats.exercises_done || 0}/${stats.exercises_total || 0} exercises</p>`;
}

function dismissOnboarding() {
  Onboarding.complete();
  const el = document.getElementById('onboard-card');
  if (el) el.remove();
}

async function openExerciseInProject(pid, eid) {
  await showProject(pid);
  switchTab('exercises');
  if (!eid) return;
  const ex = document.getElementById('ex-' + eid);
  if (ex) {
    document.querySelectorAll('.ex').forEach(n => n.classList.remove('open'));
    ex.classList.add('open');
    const ed = editors && editors[eid];
    if (ed) setTimeout(() => ed.refresh(), 0);
    ex.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

async function resumeLearning() {
  const resume = resolveResume(curriculum);
  if (!resume) {
    await startFirstHour();
    return;
  }
  track('resume_open', { project_id: resume.project_id, exercise_id: resume.exercise_id });
  await openExerciseInProject(resume.project_id, resume.exercise_id);
}

async function startFirstHour() {
  const fh = (curriculum && curriculum.first_hour) || await api.get('/api/onboarding');
  Onboarding.complete();
  track('onboarding_start', { project_id: fh.project_id, exercise_id: fh.exercise_id });
  ResumeState.save({ project_id: fh.project_id, exercise_id: fh.exercise_id });
  await openExerciseInProject(fh.project_id, fh.exercise_id);
}

/** @deprecated dashboard now builds CTA via dashboardHeroCtaHtml */
function enhanceDashboardHtml(html) {
  return html;
}

/* ---------- portfolio ---------- */
async function showPortfolioDesk() {
  track('portfolio_export');
  const data = (isHosted() && !STATE.user)
    ? await api.post('/api/portfolio', { progress: LocalProgress.read() })
    : await api.get('/api/portfolio');
  $main.innerHTML = `
    <button class="back" onclick="showDashboard()">← Back to the path</button>
    <div class="hero">
      <h2>Your portfolio artifact</h2>
      <p>Download a README you can drop into GitHub, or print an honor-system certificate.
         ${data.honor_system ? '<b>Hosted passes are browser-verified — not proctored.</b>' : ''}</p>
    </div>
    <div class="dash-toolbar">
      <a class="tool-btn primary" href="/api/portfolio.md">Download README.md</a>
      <a class="tool-btn" href="/api/certificate" target="_blank" rel="noopener">Open certificate</a>
      <button class="tool-btn" onclick="copyText(document.getElementById('pf-md').textContent).then(()=>alert('Copied'))">Copy markdown</button>
    </div>
    <div class="panel"><pre id="pf-md" class="portfolio-pre">${escapeHtml(data.markdown)}</pre></div>`;
  window.scrollTo(0, 0);
}

function escapeHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ---------- spaced review ---------- */
async function showReviewDesk() {
  track('review_open');
  const out = await api.post('/api/review', { review_state: ReviewState.get() });
  const items = out.items || [];
  let body;
  if (!items.length) {
    body = `<div class="panel">You're caught up — no drills due. Pass more exercises or check back in a week.</div>`;
  } else {
    body = items.map((it, i) => {
      if (it.kind === 'interview') {
        return `<div class="ivq" id="rvitem-${i}">
          <div class="ivq-head">
            <span class="chip">${it.project_title}</span>
            <span class="chip ${(it.difficulty||'').toLowerCase()}">${it.difficulty}</span>
            <span class="chip">interview</span>
          </div>
          <div class="tag" style="margin-bottom:8px">${it.reason}</div>
          <div class="ivq-body">${md(it.question)}</div>
          <button class="reveal" onclick="revealReviewAnswer(${i})">Show answer ▾</button>
          <div class="ivq-answer" id="rva-${i}">
            <div class="ans-label">Answer</div>${md(it.answer || '')}
            <div class="ans-label">Why</div>${md(it.explanation || '')}
            <button class="run" style="margin-top:12px" onclick="completeReviewInterview('${it.project_id}', ${it.index})">Mark reviewed ✓</button>
          </div>
        </div>`;
      }
      return `<div class="pcard" style="cursor:pointer" onclick="openReviewExercise('${it.project_id}','${it.exercise_id}')">
        <div class="num" style="--pct:0"><span>↻</span></div>
        <div>
          <h3>${it.title}</h3>
          <div class="tag">${it.project_title} · ${it.reason}</div>
        </div>
        <div class="pmeta"><b>${it.kind === 'weak_exercise' ? 'Retry' : 'Review'}</b></div>
      </div>`;
    }).join('');
  }
  $main.innerHTML = `
    <button class="back" onclick="showDashboard()">← Back to the path</button>
    <div class="hero">
      <h2>Review desk</h2>
      <p>Spaced interview drills and exercises you struggled with or haven't revisited in ~2 weeks.</p>
    </div>
    <div class="path">${body}</div>`;
  window.scrollTo(0, 0);
}

function revealReviewAnswer(i) {
  document.getElementById('rva-' + i).style.display = 'block';
}

function completeReviewInterview(pid, idx) {
  ReviewState.markInterview(pid, idx);
  track('review_complete', { project_id: pid, meta: { index: idx } });
  showReviewDesk();
}

async function openReviewExercise(pid, eid) {
  await openExerciseInProject(pid, eid);
}

/* ---------- friction analytics ---------- */
async function showFrictionDesk() {
  const out = await api.get('/api/analytics/friction?limit=10');
  const items = out.items || [];
  const rows = items.length ? items.map((it, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><code>${it.exercise_id}</code></td>
      <td>${it.opens}</td>
      <td>${it.fails}</td>
      <td>${it.passes}</td>
      <td>${Math.round((it.fail_rate || 0) * 100)}%</td>
      <td>${it.drop_score}</td>
    </tr>`).join('') : `<tr><td colspan="7">No analytics yet — run a few exercises first.</td></tr>`;
  $main.innerHTML = `
    <button class="back" onclick="showDashboard()">← Back to the path</button>
    <div class="hero">
      <h2>Friction report</h2>
      <p>Lightweight drop-off signals from this machine's learning events. Fix the top offenders before adding more content.</p>
    </div>
    <div class="panel" style="overflow-x:auto">
      <table class="friction-table">
        <thead><tr><th>#</th><th>Exercise</th><th>Opens</th><th>Fails</th><th>Passes</th><th>Fail rate</th><th>Drop score</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  window.scrollTo(0, 0);
}

/* ---------- mentor + community solutions ---------- */
function mentorPanelHtml(ex) {
  const d = ex.mentor_debrief;
  if (!d) return '';
  const fails = ReviewState.fails(ex.id);
  const need = d.fails_before_unlock || 3;
  if (fails < need) {
    return `<div class="mentor locked" id="mentor-${ex.id}">
      Mentor walkthrough unlocks after ${need} failed checks
      (${fails}/${need} so far).</div>`;
  }
  return `<div class="mentor open" id="mentor-${ex.id}">
    <div class="mentor-title">${d.title}</div>
    <p>${d.intro}</p>
    <ol>${(d.steps || []).map(s => `<li>${s}</li>`).join('')}</ol>
    <div class="obj-title">What the checker looks for</div>
    <ul>${(d.checker_looks_for || []).map(s => `<li>${s}</li>`).join('')}</ul>
    <div class="hint">Next nudge: ${d.next_hint || ''}</div>
  </div>`;
}

function solutionsSlotHtml(ex) {
  if (!ex.has_community_solutions) return '';
  return `<div class="solutions-slot" id="sols-${ex.id}"></div>`;
}

async function loadCommunitySolutions(exId) {
  const passed = !!(current && current.exercises_passed && current.exercises_passed[exId]);
  if (!passed) return;
  const q = (isHosted() && !STATE.user) ? '?passed=1' : '';
  try {
    const out = await api.get('/api/solutions/' + exId + q);
    const el = document.getElementById('sols-' + exId);
    if (!el) return;
    if (!(out.solutions || []).length) {
      el.innerHTML = '';
      return;
    }
    el.innerHTML = `
      <div class="solutions">
        <div class="obj-title">Community solutions (unlocked)</div>
        <p class="tag">Alternate approaches + tradeoffs — you already passed, so this is for depth.</p>
        ${(out.solutions || []).map((s, i) => `
          <div class="sol-card">
            <h4>${s.title}</h4>
            <pre><code>${escapeHtml(s.code)}</code></pre>
            <div class="hint">${s.tradeoffs || ''}</div>
          </div>`).join('')}
      </div>`;
  } catch (e) { /* still locked server-side */ }
}

function refreshMentor(exId) {
  const ex = current && current.project.exercises.find(e => e.id === exId);
  if (!ex) return;
  const slot = document.getElementById('mentor-' + exId);
  if (!slot) return;
  const wrap = document.createElement('div');
  wrap.innerHTML = mentorPanelHtml(ex);
  slot.replaceWith(wrap.firstElementChild);
  const fails = ReviewState.fails(exId);
  if (fails >= (ex.mentor_debrief && ex.mentor_debrief.fails_before_unlock || 3)) {
    track('mentor_unlock', { exercise_id: exId, project_id: current.project.id });
  }
}

/* ---------- local deep link (hosted runtime:local) ---------- */
function localLaunchHtml(ex) {
  const L = ex.local_launch || {};
  const cmd = L.compose || 'docker compose up -d --build';
  const deep = `http://localhost:8000${L.url_path || '/'}`;
  const block = [
    '# 1) Clone + start base stack',
    'git clone https://github.com/TapiwaChikwenya/pyforge.git',
    'cd pyforge',
    cmd,
    '',
    '# 2) Open this exercise locally',
    deep,
  ].join('\n');
  return `
    <div class="local-only">
      <b>This exercise needs the local Docker stack</b> (real JVM Spark — browsers can't run it).
      <p style="margin-top:8px">${L.note || ''}</p>
      <pre class="launch-block" id="launch-${ex.id}">${escapeHtml(block)}</pre>
      <div class="ex-actions" style="margin-top:10px">
        <button class="run" onclick="copyText(document.getElementById('launch-${ex.id}').textContent).then(()=>alert('Launch commands copied'))">Copy launch commands</button>
        <button class="reset" onclick="copyText('${deep}').then(()=>alert('Local deep link copied'))">Copy local URL</button>
      </div>
    </div>`;
}

/* ---------- deep-link boot (?project=&exercise=) ---------- */
async function consumeDeepLink() {
  const params = new URLSearchParams(location.search);
  const pid = params.get('project');
  const eid = params.get('exercise');
  if (!pid) return false;
  history.replaceState({}, '', '/');
  ResumeState.save({ project_id: pid, exercise_id: eid || null });
  await openExerciseInProject(pid, eid);
  return true;
}

/* hooks used from app.js */
window.PyForgeFeatures = {
  ReviewState, ResumeState, track, mentorPanelHtml, solutionsSlotHtml, loadCommunitySolutions,
  refreshMentor, localLaunchHtml, enhanceDashboardHtml, dashboardHeroCtaHtml, stackChip,
  showPortfolioDesk, showReviewDesk, showFrictionDesk, startFirstHour, resumeLearning,
  consumeDeepLink, openExerciseInProject,
};
window.startFirstHour = startFirstHour;
window.resumeLearning = resumeLearning;
window.showReviewDesk = showReviewDesk;
window.showPortfolioDesk = showPortfolioDesk;
window.showFrictionDesk = showFrictionDesk;
