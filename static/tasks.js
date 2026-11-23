// Gedeeld door de clipper en de editor: lange taken op de achtergrond met voortgang en annuleren.
(function () {
  const TEXT = {
    nl: { cancel: 'Annuleren', cancelled: 'Geannuleerd.', busy: 'Bezig...', error: 'Er ging iets mis.' },
    en: { cancel: 'Cancel', cancelled: 'Cancelled.', busy: 'Working...', error: 'Something went wrong.' },
  };
  const tr = key => (TEXT[document.documentElement.lang] || TEXT.nl)[key];

  const style = document.createElement('style');
  style.textContent = `
    .task-box { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 10px 0 18px;
      padding: 12px 14px; border-radius: 12px; border: 1px solid var(--border, rgba(127,127,127,.3)); }
    .task-box[hidden] { display: none; }
    .task-text { flex: 1 1 260px; font-size: 0.88rem; line-height: 1.4; }
    .task-text small { display: block; opacity: 0.75; }
    .task-box progress { flex: 1 1 200px; height: 10px; }
  `;
  document.head.appendChild(style);

  let box = null;
  let currentTask = null;

  function ensureBox() {
    if (box) return box;
    box = document.createElement('div');
    box.className = 'task-box';
    box.hidden = true;
    box.setAttribute('role', 'status');
    box.innerHTML = '<div class="task-text"></div><progress max="1"></progress>'
      + '<button type="button" class="task-cancel"></button>';
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
    const bar = b.querySelector('progress');
    if (typeof state.progress === 'number') bar.value = state.progress;
    else bar.removeAttribute('value');            // onbepaald: bewegende balk
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
        await sleep(700);
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
