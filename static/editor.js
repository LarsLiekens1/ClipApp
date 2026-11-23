const $ = s => document.querySelector(s);
const clamp = (v, a, b) => Math.min(Math.max(v, a), b);

const I18N = {
  nl: {
    tag_editor: "Studio Editor",
    nav_clipper: "Clipper (URL)",
    nav_editor: "Tijdlijn Editor",
    editor_title: "Tijdlijn Editor",
    editor_lead: "Knip en combineer video's of audiofragmenten op een interactieve tijdlijn en exporteer direct in elk gewenst formaat.",
    note_empty: "Voeg rechts mediabestanden toe om te beginnen",
    note_audio: "Audiospoor actief",
    btn_play: "Afspelen",
    btn_pause: "Pauze",
    media_title: "Mediabestanden",
    btn_pick: "Bestanden kiezen",
    drop_hint: "of sleep bestanden hierheen",
    no_sources: "Nog geen bestanden geüpload.",
    btn_add_to_timeline: "+ Toevoegen",
    b_split: "Knippen (S)",
    b_split_title: "Knippen op de afspeelkop (S)",
    b_del: "Wissen",
    b_del_title: "Verwijderen (Delete)",
    b_dup: "Dupliceren (D)",
    b_dup_title: "Dupliceren (D)",
    b_left: "◀ Links",
    b_left_title: "Naar links",
    b_right: "Rechts ▶",
    b_right_title: "Naar rechts",
    b_undo: "Ongedaan",
    b_undo_title: "Ongedaan maken (Ctrl+Z)",
    b_redo: "Opnieuw",
    b_redo_title: "Opnieuw (Ctrl+Y)",
    label_zoom: "Zoom",
    hint_shortcuts: "Sneltoetsen: Spatie = afspelen/pauze | S = knippen op de rode lijn | Delete = wissen | D = dupliceren | Ctrl+Z / Ctrl+Y = ongedaan / opnieuw. Sleep een blok om te verplaatsen en de randen om te trimmen.",
    c_start_label: "Begin in bron",
    c_end_label: "Einde in bron",
    c_len_label: "Lengte",
    export_title: "Video exporteren",
    format_label: "Formaat:",
    opt_auto: "Zoals het eerste videostuk",
    opt_vertical: "Verticaal 9:16 (Shorts/Reels 1080x1920)",
    opt_landscape: "Liggend 16:9 (YouTube 1920x1080)",
    opt_square: "Vierkant (Post 1080x1080)",
    blur_label: "Geblurde achtergrond",
    audio_only_label: "Alleen audio (MP3)",
    watermark_label: "Watermark:",
    watermark_pick: "Afbeelding kiezen",
    watermark_none: "Geen afbeelding gekozen",
    watermark_uploading: "Uploaden...",
    watermark_ready: "Geselecteerd: {name}",
    watermark_drag_hint: "Sleep het watermerk in de preview naar de gewenste plek.",
    btn_export: "Exporteren & Samenvoegen",
    err_split_pos: "Zet de rode lijn in het midden van een stuk om te knippen.",
    msg_copied: "Stuk gekopieerd. Plak met Ctrl+V.",
    err_trim_range: "Kies een begin en einde tussen 0 en {max}, met minstens 0,1 seconde ertussen.",
    err_format_playback: "De browser kan dit formaat niet direct afspelen in het voorbeeld. Exporteren werkt via ffmpeg wel.",
    err_empty_timeline: "De tijdlijn is leeg.",
    msg_exporting: "Exporteren en encoderen via ffmpeg... Een ogenblik geduld.",
    msg_export_success: "Export succesvol voltooid!",
    err_waveform_load: "De audiogolfvorm kon niet worden geladen.",
    download_btn: "Download {name}",
    email_recipient: "E-mailadres ontvanger",
    email_placeholder: "naam@voorbeeld.nl",
    btn_email: "Mail video",
    msg_email_sending: "Video wordt verstuurd...",
    msg_email_sent_attachment: "Video als bijlage verstuurd naar {recipient}.",
    msg_email_sent_drive: "Privé-Drive-link verstuurd naar {recipient}.",
    err_generic: "Er ging iets mis."
  },
  en: {
    tag_editor: "Studio Editor",
    nav_clipper: "Clipper (URL)",
    nav_editor: "Timeline Editor",
    editor_title: "Timeline Editor",
    editor_lead: "Cut and combine video or audio clips on an interactive timeline and export directly to any desired format.",
    note_empty: "Add media files on the right to get started",
    note_audio: "Audio track active",
    btn_play: "Play",
    btn_pause: "Pause",
    media_title: "Media Files",
    btn_pick: "Choose Files",
    drop_hint: "or drag files here",
    no_sources: "No files uploaded yet.",
    btn_add_to_timeline: "+ Add",
    b_split: "Split (S)",
    b_split_title: "Split at playhead (S)",
    b_del: "Delete",
    b_del_title: "Delete (Delete)",
    b_dup: "Duplicate (D)",
    b_dup_title: "Duplicate (D)",
    b_left: "◀ Left",
    b_left_title: "Move left",
    b_right: "Right ▶",
    b_right_title: "Move right",
    b_undo: "Undo",
    b_undo_title: "Undo (Ctrl+Z)",
    b_redo: "Redo",
    b_redo_title: "Redo (Ctrl+Y)",
    label_zoom: "Zoom",
    hint_shortcuts: "Shortcuts: Space = play/pause | S = split at red line | Delete = remove | D = duplicate | Ctrl+Z / Ctrl+Y = undo / redo. Drag clip to move and edges to trim.",
    c_start_label: "Start in source",
    c_end_label: "End in source",
    c_len_label: "Duration",
    export_title: "Export Video",
    format_label: "Format:",
    opt_auto: "Same as first video clip",
    opt_vertical: "Vertical 9:16 (Shorts/Reels 1080x1920)",
    opt_landscape: "Landscape 16:9 (YouTube 1920x1080)",
    opt_square: "Square (Post 1080x1080)",
    blur_label: "Blurred background",
    audio_only_label: "Audio only (MP3)",
    watermark_label: "Watermark:",
    watermark_pick: "Choose image",
    watermark_none: "No image selected",
    watermark_uploading: "Uploading...",
    watermark_ready: "Selected: {name}",
    watermark_drag_hint: "Drag the watermark in the preview to choose its position.",
    btn_export: "Export & Merge",
    err_split_pos: "Place the red line inside a clip to split.",
    msg_copied: "Clip copied. Paste with Ctrl+V.",
    err_trim_range: "Choose a start and end between 0 and {max}, with at least 0.1s between them.",
    err_format_playback: "The browser cannot preview this format directly. Exporting with ffmpeg will work.",
    err_empty_timeline: "The timeline is empty.",
    msg_exporting: "Exporting and encoding via ffmpeg... Please wait.",
    msg_export_success: "Export completed successfully!",
    err_waveform_load: "The audio waveform could not be loaded.",
    download_btn: "Download {name}",
    email_recipient: "Recipient email address",
    email_placeholder: "name@example.com",
    btn_email: "Email video",
    msg_email_sending: "Sending video...",
    msg_email_sent_attachment: "Video attachment sent to {recipient}.",
    msg_email_sent_drive: "Private Drive link sent to {recipient}.",
    err_generic: "Something went wrong."
  }
};

let currentLang = localStorage.getItem('clipapp_lang') || 'nl';

function t(key, params = {}) {
  let str = (I18N[currentLang] && I18N[currentLang][key]) || (I18N['nl'] && I18N['nl'][key]) || key;
  for (const [k, v] of Object.entries(params)) {
    str = str.replace(`{${k}}`, v);
  }
  return str;
}

function setLanguage(lang) {
  currentLang = (lang === 'en') ? 'en' : 'nl';
  localStorage.setItem('clipapp_lang', currentLang);
  document.documentElement.lang = currentLang;

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === currentLang);
  });

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (I18N[currentLang][key]) el.textContent = I18N[currentLang][key];
  });

  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.dataset.i18nTitle;
    if (I18N[currentLang][key]) el.title = I18N[currentLang][key];
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (I18N[currentLang][key]) el.placeholder = I18N[currentLang][key];
  });

  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
    const key = el.dataset.i18nAriaLabel;
    if (I18N[currentLang][key]) el.setAttribute('aria-label', I18N[currentLang][key]);
  });

  syncPlayBtn();
  renderBin();
}

document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
});

let job = null;
let watermarkUploaded = false;
let watermarkUploading = false;
let watermarkObjectUrl = null;
let watermarkX = 0.5;
let watermarkY = 0.75;
let watermarkDrag = null;
const watermarkPreviewImage = new Image();
const sources = {};
const waveformImages = {};
let clips = [];
let sel = -1;
let pps = 40;
let tpos = 0;
let playing = false;
let cur = -1;
let pending = null;
let history = [], future = [];
let clipboard = null;
let nextId = 1;
const video = $('#video');

function fmt(t) {
  const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
  const sec = s.toFixed(1).padStart(4, '0');
  return h ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
}
function parse(str) {
  str = str.trim();
  if (!str) return NaN;
  const parts = str.replace(',', '.').split(':').map(Number);
  if (parts.some(isNaN) || parts.length > 3) return NaN;
  return parts.reduce((total, p) => total * 60 + p, 0);
}
function setStatus(msg, isError = false) {
  const el = $('#status');
  el.textContent = msg;
  el.classList.toggle('error', isError);
}
const dur = c => c.end - c.start;
const total = () => clips.reduce((a, c) => a + dur(c), 0);
function startOf(i) { let t = 0; for (let k = 0; k < i; k++) t += dur(clips[k]); return t; }
function locate(t) {
  let acc = 0;
  for (let i = 0; i < clips.length; i++) {
    const d = dur(clips[i]);
    if (t < acc + d) return { i, off: t - acc };
    acc += d;
  }
  return clips.length ? { i: clips.length - 1, off: dur(clips[clips.length - 1]) } : { i: -1, off: 0 };
}

// ---------- history ----------
const snap = () => JSON.stringify({ clips, sel });
function commit() {
  stop();
  history.push(snap());
  if (history.length > 100) history.shift();
  future = [];
}
function restore(str) { const o = JSON.parse(str); clips = o.clips; sel = o.sel; render(); }
function undo() { if (!history.length) return; stop(); future.push(snap()); restore(history.pop()); }
function redo() { if (!future.length) return; stop(); history.push(snap()); restore(future.pop()); }

// ---------- bewerken ----------
function addSource(id) {
  const s = sources[id];
  if (!s) return;
  commit();
  clips.push({ id: nextId++, src: id, start: 0, end: s.duration });
  sel = clips.length - 1;
  render();
}
function split() {
  if (!clips.length) return;
  const { i, off } = locate(tpos);
  const c = clips[i];
  if (off < 0.1 || dur(c) - off < 0.1) return setStatus(t('err_split_pos'), true);
  setStatus('');
  commit();
  const cut = c.start + off;
  clips.splice(i, 1, { ...c, id: nextId++, end: cut }, { ...c, id: nextId++, start: cut });
  sel = i + 1;
  render();
}
function removeClip() {
  if (sel < 0) return;
  commit();
  clips.splice(sel, 1);
  sel = Math.min(sel, clips.length - 1);
  render();
}
function duplicateClip() {
  if (sel < 0) return;
  commit();
  clips.splice(sel + 1, 0, { ...clips[sel], id: nextId++ });
  sel++;
  render();
}
function copyClip() { if (sel >= 0) { clipboard = { ...clips[sel] }; setStatus(t('msg_copied')); } }
function pasteClip() {
  if (!clipboard) return;
  commit();
  const at = sel >= 0 ? sel + 1 : clips.length;
  clips.splice(at, 0, { ...clipboard, id: nextId++ });
  sel = at;
  render();
}
function moveClip(dir) {
  const j = sel + dir;
  if (sel < 0 || j < 0 || j >= clips.length) return;
  commit();
  [clips[sel], clips[j]] = [clips[j], clips[sel]];
  sel = j;
  render();
}
function setBounds() {
  const c = clips[sel];
  if (!c) return;
  const a = parse($('#c-start').value), b = parse($('#c-end').value);
  const max = sources[c.src].duration;
  if (isNaN(a) || isNaN(b) || a < 0 || b > max + 0.01 || b - a < 0.1) {
    setStatus(t('err_trim_range', { max: fmt(max) }), true);
    return renderPanel();
  }
  setStatus('');
  commit();
  c.start = a; c.end = Math.min(b, max);
  render();
}

// ---------- renderen ----------
function render(reseek = true) {
  renderBin(); renderTimeline(); renderPanel(); updateButtons();
  if (tpos > total()) tpos = total();
  $('#empty-note').hidden = clips.length > 0;
  if (reseek) seek(tpos); else drawPlayhead();
}

function renderBin() {
  const ul = $('#sources');
  ul.innerHTML = '';
  const list = Object.values(sources);
  $('#no-sources').hidden = list.length > 0;
  list.forEach(s => {
    const li = document.createElement('li');
    const info = document.createElement('div');
    info.className = 'src-info';
    const name = document.createElement('strong');
    name.textContent = s.name;
    const meta = document.createElement('span');
    meta.textContent = `${s.kind === 'video' ? '🎬 Video' : '🎵 Audio'} • ${fmt(s.duration)}`;
    info.append(name, meta);
    const add = document.createElement('button');
    add.innerHTML = t('btn_add_to_timeline');
    add.onclick = () => addSource(s.id);
    li.append(info, add);
    ul.appendChild(li);
  });
}

function drawWaveform(canvas, source, clip) {
  let image = waveformImages[source.waveform_url];
  if (!image) {
    image = new Image();
    waveformImages[source.waveform_url] = image;
    image.onload = () => renderTimeline();
    image.onerror = () => setStatus(t('err_waveform_load'), true);
    image.src = source.waveform_url;
    return;
  }
  if (!image.complete || !image.naturalWidth) return;
  const start = clip.start / source.duration * image.naturalWidth;
  const end = clip.end / source.duration * image.naturalWidth;
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(image, start, 0, Math.max(1, end - start), image.naturalHeight,
                    0, 0, canvas.width, canvas.height);
}

function renderTimeline() {
  const track = $('#track');
  const width = Math.max(total() * pps + 240, $('#tl-scroll').clientWidth);
  $('#tl-inner').style.width = width + 'px';
  track.innerHTML = '';
  clips.forEach((c, i) => {
    const s = sources[c.src];
    const b = document.createElement('div');
    b.className = `clip ${s.kind}` + (i === sel ? ' sel' : '');
    b.style.left = startOf(i) * pps + 'px';
    b.style.width = Math.max(dur(c) * pps, 8) + 'px';
    const label = document.createElement('div');
    label.className = 'label';
    label.textContent = s.name;
    const small = document.createElement('small');
    small.textContent = fmt(dur(c));
    label.appendChild(small);
    if (s.waveform_url && dur(c) * pps >= 36) {
      const waveform = document.createElement('canvas');
      waveform.className = 'waveform';
      waveform.width = 300;
      waveform.height = 40;
      b.appendChild(waveform);
      drawWaveform(waveform, s, c);
    }
    const hl = document.createElement('div'); hl.className = 'handle l'; hl.dataset.side = 'l';
    const hr = document.createElement('div'); hr.className = 'handle r'; hr.dataset.side = 'r';
    b.append(hl, label, hr);
    b.addEventListener('pointerdown', e => onBlockDown(e, i));
    track.appendChild(b);
  });
  drawRuler(width);
  drawPlayhead();
}

function drawRuler(width) {
  const r = $('#ruler');
  r.innerHTML = '';
  const steps = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 1800, 3600];
  const step = steps.find(s => s * pps >= 70) || 3600;
  for (let t = 0; t * pps < width; t += step) {
    const tick = document.createElement('span');
    tick.style.left = t * pps + 'px';
    tick.textContent = `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`;
    r.appendChild(tick);
  }
}

function drawPlayhead() {
  $('#playhead').style.left = tpos * pps + 'px';
  $('#clock').textContent = `${fmt(tpos)} / ${fmt(total())}`;
}

function renderPanel() {
  const c = clips[sel];
  $('#clip-panel').hidden = !c;
  if (!c) return;
  $('#c-name').textContent = sources[c.src].name;
  $('#c-start').value = fmt(c.start);
  $('#c-end').value = fmt(c.end);
  $('#c-len').textContent = fmt(dur(c));
}

function updateButtons() {
  const has = sel >= 0;
  $('#b-split').disabled = !clips.length;
  $('#b-del').disabled = !has;
  $('#b-dup').disabled = !has;
  $('#b-left').disabled = !has || sel === 0;
  $('#b-right').disabled = !has || sel === clips.length - 1;
  $('#b-undo').disabled = !history.length;
  $('#b-redo').disabled = !future.length;
  $('#play').disabled = !clips.length;
  $('#export-btn').disabled = !clips.length;
}

function xOnTimeline(e) { return e.clientX - $('#tl-inner').getBoundingClientRect().left; }

function selectOnly(i) {
  sel = i;
  $('#track').querySelectorAll('.clip').forEach((b, k) => b.classList.toggle('sel', k === i));
  renderPanel(); updateButtons();
}

function onBlockDown(e, i) {
  if (e.button !== 0) return;
  e.preventDefault();
  if (e.target.dataset.side) return startTrim(e, i, e.target.dataset.side);
  startDrag(e, i);
}

function startTrim(e, i, side) {
  selectOnly(i);
  commit();
  const x0 = e.clientX, c0 = { ...clips[i] }, max = sources[c0.src].duration;
  const move = ev => {
    const dt = (ev.clientX - x0) / pps;
    if (side === 'l') clips[i].start = clamp(c0.start + dt, 0, c0.end - 0.1);
    else clips[i].end = clamp(c0.end + dt, c0.start + 0.1, max);
    render(false);
  };
  const up = () => {
    document.removeEventListener('pointermove', move);
    document.removeEventListener('pointerup', up);
    seek(tpos);
  };
  document.addEventListener('pointermove', move);
  document.addEventListener('pointerup', up);
}

function startDrag(e, i) {
  const x0 = e.clientX, el = e.currentTarget;
  let dragging = false, target = i;
  selectOnly(i);
  const move = ev => {
    const dx = ev.clientX - x0;
    if (!dragging && Math.abs(dx) < 5) return;
    if (!dragging) { dragging = true; el.classList.add('dragging'); }
    el.style.transform = `translateX(${dx}px)`;
    const centre = startOf(i) * pps + dur(clips[i]) * pps / 2 + dx;
    let acc = 0, idx = 0;
    clips.forEach((o, k) => {
      if (k === i) return;
      if (centre > acc + dur(o) * pps / 2) idx++;
      acc += dur(o) * pps;
    });
    target = idx;
    let mx = 0, n = 0;
    clips.forEach((o, k) => { if (k !== i && n < target) { mx += dur(o) * pps; n++; } });
    const m = $('#marker');
    m.hidden = false;
    m.style.left = mx - 1 + 'px';
  };
  const up = ev => {
    document.removeEventListener('pointermove', move);
    document.removeEventListener('pointerup', up);
    $('#marker').hidden = true;
    if (!dragging) {
      const b = el.getBoundingClientRect();
      const t = startOf(i) + clamp((ev.clientX - b.left) / pps, 0, dur(clips[i]));
      stop(); seek(t);
      return;
    }
    if (target !== i) {
      commit();
      const [c] = clips.splice(i, 1);
      clips.splice(target, 0, c);
      sel = target;
    }
    render();
  };
  document.addEventListener('pointermove', move);
  document.addEventListener('pointerup', up);
}

$('#tl-inner').addEventListener('pointerdown', e => {
  if (e.target.id === 'ruler' || e.target.id === 'track' || e.target.id === 'tl-inner') {
    stop();
    seek(xOnTimeline(e) / pps);
  }
});

video.addEventListener('loadedmetadata', () => {
  if (!pending) return;
  video.currentTime = pending.t;
  if (pending.play) video.play().catch(() => {});
  pending = null;
});
video.addEventListener('error', () => {
  if (video.getAttribute('src')) setStatus('De browser kan dit formaat niet direct afspelen in het voorbeeld. Exporteren werkt via ffmpeg wel.', true);
});

function load(i, off, play) {
  const c = clips[i];
  if (!c) return;
  const s = sources[c.src];
  cur = i;
  $('#audio-note').hidden = s.kind !== 'audio';
  const t = c.start + off;
  if (video.dataset.src !== s.url) {
    video.dataset.src = s.url;
    pending = { t, play };
    video.src = s.url;
  } else {
    video.currentTime = t;
    if (play) video.play().catch(() => {}); else video.pause();
  }
}
function seek(t) {
  tpos = clamp(t, 0, total());
  const { i, off } = locate(tpos);
  if (i >= 0) load(i, off, playing);
  drawPlayhead();
}
function stop() {
  if (!playing) return;
  playing = false;
  video.pause();
  syncPlayBtn();
}
function togglePlay() {
  if (!clips.length) return;
  if (playing) { stop(); return; }
  playing = true;
  if (tpos >= total() - 0.05) tpos = 0;
  seek(tpos);
  syncPlayBtn();
}
function syncPlayBtn() {
  $('#play').innerHTML = playing
    ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg> ${t('btn_pause')}`
    : `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ${t('btn_play')}`;
}

function tick() {
  if (playing && clips[cur] && !pending) {
    const c = clips[cur], t = video.currentTime;
    if (t >= c.end - 0.02 || video.ended) {
      const n = clips[cur + 1];
      if (!n) { playing = false; video.pause(); tpos = total(); syncPlayBtn(); }
      else if (n.src === c.src && Math.abs(n.start - c.end) < 0.05) cur++;
      else load(cur + 1, 0, true);
    } else {
      tpos = startOf(cur) + Math.max(0, t - c.start);
    }
    drawPlayhead();
    const sc = $('#tl-scroll'), x = tpos * pps;
    if (x > sc.scrollLeft + sc.clientWidth - 40 || x < sc.scrollLeft) sc.scrollLeft = Math.max(0, x - 80);
  }
  drawWatermarkPreview();
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);

// ---------- uploaden ----------
function upload(file) {
  return new Promise(resolve => {
    const row = document.createElement('div');
    row.className = 'up';
    const name = document.createElement('span');
    name.textContent = file.name;
    const bar = document.createElement('progress');
    bar.max = 1; bar.value = 0;
    row.append(name, bar);
    $('#uploads').appendChild(row);
    const fail = msg => { row.classList.add('fail'); bar.remove(); name.textContent = `${file.name}: ${msg}`; resolve(); };

    const fd = new FormData();
    fd.append('file', file);
    if (job) fd.append('job', job);
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/editor/upload');
    xhr.upload.onprogress = e => { if (e.lengthComputable) bar.value = e.loaded / e.total; };
    xhr.onerror = () => fail('uploaden mislukt');
    xhr.onload = () => {
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch (e) {}
      if (xhr.status !== 200) return fail(data.error || 'uploaden mislukt');
      job = data.job;
      syncWatermarkControls();
      sources[data.source.id] = data.source;
      row.remove();
      addSource(data.source.id);
      resolve();
    };
    xhr.send(fd);
  });
}
async function uploadAll(files) { for (const f of files) await upload(f); }

$('#pick').onclick = () => $('#file').click();
$('#file').onchange = e => { const files = [...e.target.files]; e.target.value = ''; uploadAll(files); };
document.addEventListener('dragover', e => e.preventDefault());
document.addEventListener('drop', e => {
  e.preventDefault();
  if (e.dataTransfer && e.dataTransfer.files.length) uploadAll([...e.dataTransfer.files]);
});

$('#play').onclick = togglePlay;
$('#b-split').onclick = split;
$('#b-del').onclick = removeClip;
$('#b-dup').onclick = duplicateClip;
$('#b-left').onclick = () => moveClip(-1);
$('#b-right').onclick = () => moveClip(1);
$('#b-undo').onclick = undo;
$('#b-redo').onclick = redo;
$('#c-start').onchange = setBounds;
$('#c-end').onchange = setBounds;
$('#zoom').oninput = e => { pps = Number(e.target.value); render(false); };
$('#audio-only').onchange = e => {
  $('#format').disabled = e.target.checked;
  $('#blur').disabled = e.target.checked;
  syncWatermarkControls();
};
$('#format').onchange = syncWatermarkControls;
function syncWatermarkControls() {
  const visible = $('#format').value === 'vertical' && !$('#audio-only').checked;
  $('#watermark-controls').hidden = !visible;
  $('#watermark-preview-panel').hidden = !visible || !watermarkUploaded;
  $('#watermark-pick').disabled = !job || watermarkUploading;
}
function watermarkPreviewSize() {
  const scale = Math.min(420 / watermarkPreviewImage.naturalWidth, 420 / watermarkPreviewImage.naturalHeight) / 4;
  return {
    width: watermarkPreviewImage.naturalWidth * scale,
    height: watermarkPreviewImage.naturalHeight * scale,
  };
}
function watermarkPreviewPoint(event) {
  const rect = $('#watermark-preview').getBoundingClientRect();
  return {
    x: (event.clientX - rect.left) * $('#watermark-preview').width / rect.width,
    y: (event.clientY - rect.top) * $('#watermark-preview').height / rect.height,
  };
}
function moveWatermarkPreview(point, offset) {
  const size = watermarkPreviewSize();
  const canvas = $('#watermark-preview');
  watermarkX = clamp((point.x - offset.x) / Math.max(1, canvas.width - size.width), 0, 1);
  watermarkY = clamp((point.y - offset.y) / Math.max(1, canvas.height - size.height), 0, 1);
  drawWatermarkPreview();
}
function drawWatermarkPreview() {
  const canvas = $('#watermark-preview');
  if ($('#watermark-preview-panel').hidden) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#080b12';
  ctx.fillRect(0, 0, w, h);
  if (video.videoWidth && video.videoHeight && video.readyState >= 2) {
    const cover = Math.max(w / video.videoWidth, h / video.videoHeight) * 1.08;
    const bgW = video.videoWidth * cover, bgH = video.videoHeight * cover;
    ctx.save();
    ctx.filter = 'blur(8px)';
    ctx.drawImage(video, (w - bgW) / 2, (h - bgH) / 2, bgW, bgH);
    ctx.restore();
    ctx.fillStyle = 'rgba(0, 0, 0, 0.12)';
    ctx.fillRect(0, 0, w, h);
    const fit = Math.min(w / video.videoWidth, h / video.videoHeight);
    const fgW = video.videoWidth * fit, fgH = video.videoHeight * fit;
    ctx.drawImage(video, (w - fgW) / 2, (h - fgH) / 2, fgW, fgH);
  }
  if (watermarkPreviewImage.complete && watermarkPreviewImage.naturalWidth) {
    const size = watermarkPreviewSize();
    const x = watermarkX * (w - size.width), y = watermarkY * (h - size.height);
    ctx.drawImage(watermarkPreviewImage, x, y, size.width, size.height);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.setLineDash([4, 3]);
    ctx.strokeRect(x, y, size.width, size.height);
    ctx.setLineDash([]);
  }
}
$('#watermark-preview').onpointerdown = event => {
  if (!watermarkUploaded || !watermarkPreviewImage.complete || !watermarkPreviewImage.naturalWidth) return;
  const point = watermarkPreviewPoint(event);
  const size = watermarkPreviewSize();
  const canvas = $('#watermark-preview');
  const left = watermarkX * (canvas.width - size.width);
  const top = watermarkY * (canvas.height - size.height);
  const inside = point.x >= left && point.x <= left + size.width &&
                 point.y >= top && point.y <= top + size.height;
  watermarkDrag = {
    offset: inside ? { x: point.x - left, y: point.y - top } : { x: size.width / 2, y: size.height / 2 },
    pointerId: event.pointerId,
  };
  canvas.setPointerCapture(event.pointerId);
  if (!inside) moveWatermarkPreview(point, watermarkDrag.offset);
};
$('#watermark-preview').onpointermove = event => {
  if (watermarkDrag && watermarkDrag.pointerId === event.pointerId) {
    moveWatermarkPreview(watermarkPreviewPoint(event), watermarkDrag.offset);
  }
};
$('#watermark-preview').onpointerup = event => {
  if (watermarkDrag && watermarkDrag.pointerId === event.pointerId) watermarkDrag = null;
};
$('#watermark-preview').onpointercancel = () => { watermarkDrag = null; };
$('#watermark-pick').onclick = () => $('#watermark-file').click();
$('#watermark-file').onchange = async e => {
  const file = e.target.files[0];
  e.target.value = '';
  if (!file || !job) return;
  watermarkUploading = true;
  $('#watermark-name').textContent = t('watermark_uploading');
  syncWatermarkControls();
  try {
    const form = new FormData();
    form.append('job', job);
    form.append('file', file);
    const response = await fetch('/api/editor/watermark', { method: 'POST', body: form });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || t('err_generic'));
    watermarkUploaded = true;
    if (watermarkObjectUrl) URL.revokeObjectURL(watermarkObjectUrl);
    watermarkObjectUrl = URL.createObjectURL(file);
    watermarkPreviewImage.src = watermarkObjectUrl;
    $('#watermark-name').textContent = t('watermark_ready', { name: file.name });
  } catch (err) {
    $('#watermark-name').textContent = err.message;
  } finally {
    watermarkUploading = false;
    syncWatermarkControls();
  }
};
document.addEventListener('click', e => { if (e.target.tagName === 'BUTTON') e.target.blur(); });

document.addEventListener('keydown', e => {
  if (/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) return;
  const mod = e.ctrlKey || e.metaKey, k = e.key.toLowerCase();
  if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
  else if (mod && k === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); }
  else if (mod && k === 'y') { e.preventDefault(); redo(); }
  else if (mod && k === 'c') copyClip();
  else if (mod && k === 'v') pasteClip();
  else if (!mod && k === 's') split();
  else if (!mod && k === 'd') duplicateClip();
  else if (e.key === 'Delete' || e.key === 'Backspace') removeClip();
  else if (e.key === 'ArrowLeft') { stop(); seek(tpos - (e.shiftKey ? 5 : 1)); }
  else if (e.key === 'ArrowRight') { stop(); seek(tpos + (e.shiftKey ? 5 : 1)); }
});

async function api(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || t('err_generic'));
  return data;
}

$('#export-btn').onclick = async () => {
  if (!clips.length) return setStatus(t('err_empty_timeline'), true);
  stop();
  const btn = $('#export-btn');
  btn.disabled = true;
  $('#result').hidden = true;
  setStatus(t('msg_exporting'));
  try {
    const data = await runTask('/api/editor/export', {
      job,
      clips: clips.map(c => ({ src: c.src, start: c.start, end: c.end })),
      format: $('#format').value,
      blur: $('#blur').checked,
      audio_only: $('#audio-only').checked,
      watermark: watermarkUploaded && $('#format').value === 'vertical' && !$('#audio-only').checked,
      watermark_x: watermarkX,
      watermark_y: watermarkY,
    });
    const box = $('#result');
    box.innerHTML = '';
    const media = document.createElement(data.kind === 'audio' ? 'audio' : 'video');
    media.controls = true;
    media.src = data.url;
    const a = document.createElement('a');
    a.href = data.url; a.download = data.name;
    a.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg> ${t('download_btn', { name: data.name })}`;
    box.append(media, a);
    if (data.kind === 'video') {
      const emailForm = document.createElement('form');
      emailForm.className = 'email-form';
      const recipient = document.createElement('input');
      recipient.type = 'email';
      recipient.required = true;
      recipient.autocomplete = 'email';
      recipient.dataset.i18nPlaceholder = 'email_placeholder';
      recipient.dataset.i18nAriaLabel = 'email_recipient';
      recipient.placeholder = t('email_placeholder');
      recipient.setAttribute('aria-label', t('email_recipient'));
      const send = document.createElement('button');
      send.type = 'submit';
      send.dataset.i18n = 'btn_email';
      send.textContent = t('btn_email');
      emailForm.append(recipient, send);
      emailForm.onsubmit = async event => {
        event.preventDefault();
        send.disabled = true;
        setStatus(t('msg_email_sending'));
        try {
          const result = await api('/api/send-video', {
            job,
            name: data.name,
            recipient: recipient.value.trim(),
          });
          const key = result.delivery === 'drive'
            ? 'msg_email_sent_drive'
            : 'msg_email_sent_attachment';
          setStatus(t(key, { recipient: recipient.value.trim() }));
        } catch (err) {
          setStatus(err.message, true);
        } finally {
          send.disabled = false;
        }
      };
      box.append(emailForm);
    }
    box.hidden = false;
    setStatus(t('msg_export_success'));
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    updateButtons();
  }
};

render();
setLanguage(currentLang);
syncWatermarkControls();
