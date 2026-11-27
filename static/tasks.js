// Gedeeld door de clipper en de editor: lange taken op de achtergrond met voortgang en annuleren.
(function () {
  const TEXT = {
    nl: { cancel: 'Annuleren', cancelled: 'Geannuleerd.', busy: 'Bezig...', error: 'Er ging iets mis.' },
    en: { cancel: 'Cancel', cancelled: 'Cancelled.', busy: 'Working...', error: 'Something went wrong.' },
  };
  const tr = key => (TEXT[document.documentElement.lang] || TEXT.nl)[key];

  const style = document.createElement('style');
  style.textContent = `
    .task-box { display: grid; grid-template-columns: 1fr auto; gap: 10px 14px; align-items: center;
      margin: 0 0 16px; padding: 14px 16px; border-radius: var(--radius-lg, 12px);
      border: 1px solid var(--border, rgba(127,127,127,.3)); background: var(--surface, #fff); }
    .task-box[hidden] { display: none; }
    .task-text { min-width: 0; font-size: 0.88rem; line-height: 1.4; font-weight: 600; }
    .task-text small { display: block; font-weight: 400; color: var(--text-2, inherit);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .task-cancel { height: 32px; font-size: 0.82rem; }
    .task-track { grid-column: 1 / -1; position: relative; height: 6px; border-radius: 999px; overflow: hidden;
      background: var(--surface-2, rgba(127,127,127,.2)); }
    .task-fill { position: absolute; inset: 0 auto 0 0; width: 0; border-radius: inherit;
      background: var(--primary, #18181b); transition: width .3s ease; }
    .task-box.indeterminate .task-fill { width: 30% !important; transition: none;
      animation: task-slide 1.2s ease-in-out infinite; }
    @keyframes task-slide { 0% { left: -30%; } 100% { left: 100%; } }
    .task-meta { display: flex; justify-content: space-between; gap: 12px; grid-column: 1 / -1;
      font-size: 0.76rem; color: var(--muted, inherit); font-variant-numeric: tabular-nums; }
    .task-pct { color: var(--text, inherit); font-weight: 600; }
    @media (prefers-reduced-motion: reduce) {
      .task-box.indeterminate .task-fill { animation: none; left: 0; width: 100% !important; opacity: .35; }
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
