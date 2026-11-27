// Gedeeld door de clipper en de editor: lange taken op de achtergrond met voortgang en annuleren.
(function () {
  const TEXT = {
    nl: { cancel: 'Annuleren', cancelled: 'Geannuleerd.', busy: 'Bezig...', error: 'Er ging iets mis.' },
    en: { cancel: 'Cancel', cancelled: 'Cancelled.', busy: 'Working...', error: 'Something went wrong.' },
  };
  const tr = key => (TEXT[document.documentElement.lang] || TEXT.nl)[key];

  const style = document.createElement('style');
  style.textContent = `
    .task-box { position: relative; display: grid; grid-template-columns: 1fr auto; gap: 10px 14px;
      align-items: center; margin: 10px 0 18px; padding: 14px 16px; overflow: hidden;
      border-radius: var(--radius-md, 12px); border: 1px solid var(--border, rgba(127,127,127,.3));
      background: var(--bg-card, rgba(17,24,39,.75)); box-shadow: 0 0 0 1px var(--accent-glow, transparent);
      animation: task-in .25s ease-out; }
    .task-box[hidden] { display: none; }
    @keyframes task-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
    .task-text { min-width: 0; font-size: 0.9rem; line-height: 1.4; font-weight: 600; }
    .task-text small { display: block; font-weight: 400; color: var(--text-secondary, inherit); opacity: .9;
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .task-meta { display: flex; justify-content: space-between; gap: 12px; grid-column: 1 / -1;
      font: 500 0.78rem var(--font-mono, ui-monospace, monospace); color: var(--text-secondary, inherit); }
    .task-pct { color: var(--text-primary, inherit); font-weight: 700; font-variant-numeric: tabular-nums; }
    .task-track { grid-column: 1 / -1; position: relative; height: 10px; border-radius: 999px; overflow: hidden;
      background: var(--bg-elevated, rgba(127,127,127,.2)); }
    .task-fill { position: absolute; inset: 0 auto 0 0; width: 0; border-radius: inherit;
      background: linear-gradient(90deg, #22d3ee, #6366f1 45%, #a855f7 70%, #ec4899);
      background-size: 200% 100%; box-shadow: 0 0 12px rgba(139, 92, 246, .55);
      transition: width .35s ease; animation: task-shine 2.4s linear infinite; }
    .task-fill::after { content: ''; position: absolute; inset: 0;
      background: repeating-linear-gradient(-45deg, rgba(255,255,255,.16) 0 8px, transparent 8px 16px);
      background-size: 22px 22px; animation: task-stripes .8s linear infinite; }
    .task-box.indeterminate .task-fill { width: 35% !important; transition: none;
      animation: task-slide 1.3s ease-in-out infinite, task-shine 2.4s linear infinite; }
    @keyframes task-shine { to { background-position: -200% 0; } }
    @keyframes task-stripes { to { background-position: 22px 0; } }
    @keyframes task-slide { 0% { left: -35%; } 100% { left: 100%; } }
    @media (prefers-reduced-motion: reduce) {
      .task-fill, .task-fill::after, .task-box { animation: none !important; }
      .task-box.indeterminate .task-fill { left: 0; width: 100% !important; opacity: .5; }
    }
  `;
  document.head.appendChild(style);

  let box = null;
  let currentTask = null;

  function ensureBox() {
    if (box) return box;
    box = document.createElement('div');
    box.className = 'task-box indeterminate';
    box.hidden = true;
    box.setAttribute('role', 'status');
    box.innerHTML = '<div class="task-text"></div>'
      + '<button type="button" class="task-cancel"></button>'
      + '<div class="task-track" role="progressbar" aria-valuemin="0" aria-valuemax="100">'
      + '<div class="task-fill"></div></div>'
      + '<div class="task-meta"><span class="task-detail"></span><span class="task-pct"></span></div>';
    const status = document.getElementById('status');
    status.insertAdjacentElement('afterend', box);
    box.querySelector('.task-cancel').addEventListener('click', async () => {
      if (!currentTask) return;
      box.querySelector('.task-cancel').disabled = true;
      await fetch(`/api/tasks/${currentTask}/cancel`, { method: 'POST' }).catch(() => {});
    });
    return box;
  }

  function show(state) {
    const b = ensureBox();
    b.hidden = false;
    const text = b.querySelector('.task-text');
    text.textContent = state.title || tr('busy');
    if (state.step) {
      const small = document.createElement('small');
      small.textContent = state.step.replace(/^Stap\s+/, '');
      text.appendChild(small);
    }
    const known = typeof state.progress === 'number';
    const pct = known ? Math.round(state.progress * 100) : null;
    b.classList.toggle('indeterminate', !known);   // onbekend: heen-en-weer bewegende balk
    b.querySelector('.task-fill').style.width = known ? `${pct}%` : '';
    const track = b.querySelector('.task-track');
    if (known) track.setAttribute('aria-valuenow', pct);
    else track.removeAttribute('aria-valuenow');
    b.querySelector('.task-pct').textContent = known ? `${pct}%` : '';
    b.querySelector('.task-detail').textContent = state.detail || '';
    b.querySelector('.task-cancel').textContent = tr('cancel');
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  window.runTask = async function runTask(path, body) {
    const r = await fetch(path, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, background: true }),
    });
    const start = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(start.error || tr('error'));
    if (!start.task) return start;                 // server deed het meteen
    currentTask = start.task;
    show({});
    ensureBox().querySelector('.task-cancel').disabled = false;
    try {
      let failures = 0;
      for (;;) {
        await sleep(500);
        let state;
        try {
          const s = await fetch(`/api/tasks/${start.task}`);
          state = await s.json();
          if (!s.ok) throw new Error(state.error || tr('error'));
          failures = 0;
        } catch (err) {
          if (++failures > 5) throw err;
          continue;
        }
        show(state);
        if (state.status === 'done') return state.result;
        if (state.status === 'error') throw new Error(state.error || tr('error'));
        if (state.status === 'cancelled') throw new Error(tr('cancelled'));
      }
    } finally {
      currentTask = null;
      if (box) box.hidden = true;
    }
  };
})();
