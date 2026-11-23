const $ = s => document.querySelector(s);
let job = null, duration = 0, segments = [];
let analysisData = null;
let suggestionMessage = null;
const player = $('#player');
let yt = null;

const I18N = {
  nl: {
    brand_tag: "Clipper",
    nav_clipper: "Clipper (URL)",
    nav_editor: "Tijdlijn Editor",
    hero_title: "Video Clipper & Transcribe",
    hero_desc: "Plak een YouTube- of video-link, markeer de beste momenten en genereer automatisch korte clips met optionele ondertitels en 9:16 formaat.",
    url_placeholder: "https://www.youtube.com/watch?v=... of andere videolink",
    btn_load: "Video laden",
    hint_platforms: "Ondersteunt: YouTube, Vimeo, directe MP4/WebM en andere webvideo's",
    timeline_label: "Tijdlijn preview",
    timeline_hint: "Klik op de balk om te spoelen",
    timeline_title: "Klik om naar die plek te springen",
    label_start: "Starttijd",
    btn_start_now: "Start = nu",
    label_end: "Eindtijd",
    btn_end_now: "Einde = nu",
    btn_add: "Stuk toevoegen",
    segments_header: "Geselecteerde stukken",
    segments_empty: "Nog geen stukken gekozen. Speel de video af, stel start en einde in en klik op 'Stuk toevoegen'.",
    options_title: "Opties & Effecten",
    subs_title: "Ondertitels maken",
    subs_desc: "Automatische spraakherkenning via Whisper AI",
    subs_lang_label: "Taal van de video:",
    opt_lang_auto: "Automatisch herkennen",
    opt_lang_nl: "Nederlands",
    opt_lang_en: "Engels",
    opt_lang_fr: "Frans",
    opt_lang_de: "Duits",
    vert_title: "Verticaal 9:16 formaat",
    vert_desc: "Ideaal voor TikTok, Shorts & Reels",
    vert_blur: "Geblurde achtergrond (i.p.v. zwarte balken)",
    vert_logo: "Logo onder de ondertitels:",
    caption_title: "Caption bovenin (automatisch of comments)",
    caption_desc: "Gebruikt de automatische caption van de clip, of anders de best gewaardeerde comment met een timestamp. Voor een blur-balk boven de video: kies ook 9:16 en geblurde achtergrond.",
    caption_position: "Positie caption:",
    caption_above: "Boven de video (bovenste balk)",
    caption_top: "Bovenin de video",
    caption_center: "Midden in beeld",
    caption_bottom: "Onderaan de video",
    err_caption_analysis: "Analyseer eerst de YouTube-comments om captions te genereren.",
    msg_done_caption_missing: "{count} clip(s) gemaakt; voor {missing} clip(s) was geen passende comment met timestamp gevonden, dus die hebben geen caption.",
    btn_render: "Clips maken & exporteren",
    results_title: "Gegenereerde Clips",
    btn_preview: "Bekijk",
    btn_delete: "Verwijder",
    segment_suggestion: "voorstel",
    email_recipient: "E-mailadres ontvanger",
    email_placeholder: "naam@voorbeeld.nl",
    btn_email: "Mail video",
    to: "tot",
    analysis_title: "Commenttijdstempels & kijkersmomenten",
    analysis_desc: "Vergelijk tijdstempels uit maximaal 1.000 YouTube-comments met de beschikbare kijkersheatmap.",
    analysis_button: "Analyseer comments",
    analysis_loading: "YouTube-comments en kijkersheatmap ophalen...",
    analysis_mentions_label: "Tijdstempelvermeldingen",
    analysis_comments_label: "Geanalyseerde comments",
    analysis_peak_comments_label: "Interval met meeste timestamps",
    analysis_peak_viewers_label: "Hoogste heatmapscore (relatief)",
    analysis_legend_mentions: "Tijdstempels in comments",
    analysis_legend_viewers: "Kijkersheatmap (relatief)",
    analysis_no_timestamps: "Er zijn geen tijdstempels in de opgehaalde comments gevonden.",
    analysis_no_heatmap: "YouTube heeft voor deze video geen kijkersheatmap beschikbaar.",
    analysis_peaks: "Meeste timestamps: {comments} ({count} vermeldingen). Hoogste heatmapscore: {viewers} ({score}, relatief).",
    analysis_peak_comments_value: "{interval} ({count})",
    analysis_peak_viewers_value: "{interval} ({score})",
    analysis_table_title: "Exacte cijfers per interval",
    analysis_table_description: "Elke rij beslaat {seconds} seconden. De heatmapscore is relatief, geen exact aantal kijkers.",
    analysis_table_interval: "Video-interval",
    analysis_table_mentions: "Timestamps genoemd",
    analysis_table_score: "Heatmapscore (relatief)",
    analysis_suggestions_title: "Automatische clipvoorstellen",
    analysis_suggestions_desc: "De rangschikking combineert commentvermeldingen en kijkersinteresse; als beide beschikbaar zijn tellen ze even zwaar. Bekijk de voorstellen en verwijder ongewenste stukken voordat je exporteert.",
    analysis_suggestion_count: "Aantal clips",
    analysis_suggestion_duration: "Lengte per clip",
    analysis_generate_suggestions: "Genereer clipvoorstellen",
    analysis_suggestions_added_singular: "1 clipvoorstel toegevoegd aan 'Geselecteerde stukken'. Bekijk het, verwijder het als nodig en kies daarna ondertitels, formaat en blur.",
    analysis_suggestions_added_plural: "{count} clipvoorstellen toegevoegd aan 'Geselecteerde stukken'. Bekijk ze, verwijder ongewenste stukken en kies daarna ondertitels, formaat en blur.",
    analysis_suggestions_none: "Geen nieuwe voorstellen gevonden. Mogelijk ontbreken pieken of overlappen ze met al gekozen stukken.",
    analysis_chart_label: "Grafiek van genoemde tijdstempels en relatieve kijkersinteresse per videomoment.",
    msg_searching: "Video wordt opgezocht...",
    msg_loaded: "Video geladen ({duration}). Selecteer nu de stukken.",
    msg_processing_subs: "Clips worden verwerkt en ondertiteld via Whisper. Een ogenblik...",
    msg_processing: "Clips worden verwerkt en gerenderd. Een ogenblik...",
    msg_done: "{count} clip(s) succesvol gegenereerd!",
    err_times: "Vul een start en een einde in, bijvoorbeeld 1:23 of 83.",
    err_end_before_start: "Het einde moet na de start liggen.",
    err_end_exceeds: "De video is maar {duration} lang.",
    err_yt_playback: "YouTube laat deze video hier niet afspelen. Je kunt de tijden zelf typen bij Start en Einde.",
    err_yt_load: "De YouTube-speler kon niet laden. Je kunt de tijden zelf typen bij Start en Einde.",
    err_generic: "Er ging iets mis.",
    err_logo_upload: "Logo uploaden mislukt.",
    auto_title: "✨ Automatisch TikToks maken",
    auto_desc: "Analyseert de hele video lokaal en gratis: hooks in het transcript, energie in het geluid, spreektempo en (bij YouTube) comments en heatmap. Clips beginnen en eindigen op hele zinnen, met een hook-caption en posttekst met hashtags.",
    auto_export: "Meteen exporteren",
    subs_model_label: "Nauwkeurigheid:",
    opt_model_tiny: "Snelst (tiny)",
    opt_model_base: "Snel (base)",
    opt_model_small: "Gebalanceerd (small)",
    opt_model_medium: "Nauwkeurigst, traag (medium)",
    auto_blur: "Geblurde achtergrond",
    auto_caption: "Caption bovenin",
    auto_hint: "Tip: zet 'Ondertitels maken' aan voor slimmere keuzes op basis van wat er gezegd wordt (gebruikt Whisper). Zonder ondertitels kiest de app op luidheid en comments.",
    auto_button: "Maak TikToks",
    auto_working: "Video wordt geanalyseerd op de beste momenten. Bij lange video's kan dit enkele minuten duren...",
    auto_done: "{count} voorstel(len) toegevoegd. Pas de captions aan als je wilt en exporteer.",
    auto_done_exporting: "{count} voorstel(len) gevonden, de TikToks worden nu gemaakt...",
    segment_auto: "auto",
    caption_placeholder: "Caption bovenin beeld",
    btn_copy_post: "Kopieer posttekst",
    msg_copied: "Posttekst gekopieerd.",
    msg_email_sending: "Video wordt verstuurd...",
    msg_email_sent_attachment: "Video als bijlage verstuurd naar {recipient}.",
    msg_email_sent_drive: "Privé-Drive-link verstuurd naar {recipient}."
  },
  en: {
    brand_tag: "Clipper",
    nav_clipper: "Clipper (URL)",
    nav_editor: "Timeline Editor",
    hero_title: "Video Clipper & Transcribe",
    hero_desc: "Paste a YouTube or video link, mark the best moments and automatically generate short clips with optional subtitles and 9:16 format.",
    url_placeholder: "https://www.youtube.com/watch?v=... or other video link",
    btn_load: "Load Video",
    hint_platforms: "Supports: YouTube, Vimeo, direct MP4/WebM and other web videos",
    timeline_label: "Timeline Preview",
    timeline_hint: "Click on the bar to seek",
    timeline_title: "Click to jump to this position",
    label_start: "Start Time",
    btn_start_now: "Start = now",
    label_end: "End Time",
    btn_end_now: "End = now",
    btn_add: "Add Clip",
    segments_header: "Selected Clips",
    segments_empty: "No clips selected yet. Play video, set start and end times, and click 'Add Clip'.",
    options_title: "Options & Effects",
    subs_title: "Generate Subtitles",
    subs_desc: "Automatic speech recognition via Whisper AI",
    subs_lang_label: "Video language:",
    opt_lang_auto: "Auto-detect",
    opt_lang_nl: "Dutch",
    opt_lang_en: "English",
    opt_lang_fr: "French",
    opt_lang_de: "German",
    vert_title: "Vertical 9:16 Format",
    vert_desc: "Ideal for TikTok, Shorts & Reels",
    vert_blur: "Blurred background (instead of black bars)",
    vert_logo: "Logo below subtitles:",
    caption_title: "Top caption (automatic or comments)",
    caption_desc: "Uses the clip's automatic caption, or otherwise the highest-rated comment with a timestamp. For a blurred area above the video, also choose 9:16 and blurred background.",
    caption_position: "Caption position:",
    caption_above: "Above the video (top margin)",
    caption_top: "Top of the video",
    caption_center: "Center of the frame",
    caption_bottom: "Bottom of the video",
    err_caption_analysis: "Analyze the YouTube comments first to generate captions.",
    msg_done_caption_missing: "{count} clip(s) created; no matching timestamp comment was found for {missing}, so those clips have no caption.",
    btn_render: "Generate & Export Clips",
    results_title: "Generated Clips",
    btn_preview: "Preview",
    btn_delete: "Delete",
    segment_suggestion: "suggestion",
    email_recipient: "Recipient email address",
    email_placeholder: "name@example.com",
    btn_email: "Email video",
    to: "to",
    analysis_title: "Comment timestamps & viewer activity",
    analysis_desc: "Compare timestamps from up to 1,000 YouTube comments with the available viewer heatmap.",
    analysis_button: "Analyze comments",
    analysis_loading: "Fetching YouTube comments and viewer heatmap...",
    analysis_mentions_label: "Timestamp mentions",
    analysis_comments_label: "Comments analyzed",
    analysis_peak_comments_label: "Interval with most timestamps",
    analysis_peak_viewers_label: "Highest heatmap score (relative)",
    analysis_legend_mentions: "Timestamps in comments",
    analysis_legend_viewers: "Viewer heatmap (relative)",
    analysis_no_timestamps: "No timestamps were found in the retrieved comments.",
    analysis_no_heatmap: "YouTube does not provide a viewer heatmap for this video.",
    analysis_peaks: "Most timestamps: {comments} ({count} mentions). Highest heatmap score: {viewers} ({score}, relative).",
    analysis_peak_comments_value: "{interval} ({count})",
    analysis_peak_viewers_value: "{interval} ({score})",
    analysis_table_title: "Exact figures per interval",
    analysis_table_description: "Each row covers {seconds} seconds. The heatmap score is relative, not an exact viewer count.",
    analysis_table_interval: "Video interval",
    analysis_table_mentions: "Timestamps mentioned",
    analysis_table_score: "Heatmap score (relative)",
    analysis_suggestions_title: "Automatic clip suggestions",
    analysis_suggestions_desc: "Suggestions rank moments using comment mentions and viewer interest; when both are available, they count equally. Preview suggestions and remove unwanted clips before exporting.",
    analysis_suggestion_count: "Number of clips",
    analysis_suggestion_duration: "Length per clip",
    analysis_generate_suggestions: "Generate clip suggestions",
    analysis_suggestions_added_singular: "Added 1 suggestion to 'Selected Clips'. Preview it, remove it if needed, then choose subtitles, format and blur.",
    analysis_suggestions_added_plural: "Added {count} suggestions to 'Selected Clips'. Preview them, remove unwanted clips, then choose subtitles, format and blur.",
    analysis_suggestions_none: "No new suggestions found. There may be no peaks, or they may overlap with clips already selected.",
    analysis_chart_label: "Chart of mentioned timestamps and relative viewer interest across the video.",
    msg_searching: "Searching for video...",
    msg_loaded: "Video loaded ({duration}). Select your clips now.",
    msg_processing_subs: "Processing clips and generating subtitles with Whisper. Please wait...",
    msg_processing: "Processing and rendering clips. Please wait...",
    msg_done: "{count} clip(s) successfully generated!",
    err_times: "Please enter start and end times, e.g. 1:23 or 83.",
    err_end_before_start: "End time must be after start time.",
    err_end_exceeds: "The video is only {duration} long.",
    err_yt_playback: "YouTube does not allow playback here. You can manually enter Start and End times.",
    err_yt_load: "The YouTube player could not load. You can manually enter Start and End times.",
    err_generic: "Something went wrong.",
    err_logo_upload: "Failed to upload logo.",
    auto_title: "✨ Make TikToks automatically",
    auto_desc: "Analyses the whole video locally and for free: hooks in the transcript, audio energy, speaking pace and (for YouTube) comments and heatmap. Clips start and end on full sentences, with a hook caption and post text with hashtags.",
    auto_export: "Export right away",
    subs_model_label: "Accuracy:",
    opt_model_tiny: "Fastest (tiny)",
    opt_model_base: "Fast (base)",
    opt_model_small: "Balanced (small)",
    opt_model_medium: "Most accurate, slow (medium)",
    auto_blur: "Blurred background",
    auto_caption: "Caption on top",
    auto_hint: "Tip: turn on 'Create subtitles' for smarter picks based on what is said (uses Whisper). Without subtitles the app picks on loudness and comments.",
    auto_button: "Make TikToks",
    auto_working: "Analysing the video for the best moments. Long videos can take a few minutes...",
    auto_done: "Added {count} suggestion(s). Edit the captions if you like, then export.",
    auto_done_exporting: "Found {count} suggestion(s), creating the TikToks now...",
    segment_auto: "auto",
    caption_placeholder: "Caption at the top",
    btn_copy_post: "Copy post text",
    msg_copied: "Post text copied.",
    msg_email_sending: "Sending video...",
    msg_email_sent_attachment: "Video attachment sent to {recipient}.",
    msg_email_sent_drive: "Private Drive link sent to {recipient}."
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

  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (I18N[currentLang][key]) el.placeholder = I18N[currentLang][key];
  });

  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.dataset.i18nTitle;
    if (I18N[currentLang][key]) el.title = I18N[currentLang][key];
  });

  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
    const key = el.dataset.i18nAriaLabel;
    if (I18N[currentLang][key]) el.setAttribute('aria-label', I18N[currentLang][key]);
  });

  renderSegments();
  if (analysisData) renderAnalysis(analysisData);
  if (suggestionMessage) {
    $('#analysis-suggestion-status').textContent = t(
      suggestionMessage.key, suggestionMessage.params
    );
  }
}

document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
});

const videoCtl = {
  time: () => player.currentTime,
  seek: t => { player.currentTime = t; },
  play: () => player.play(),
  pause: () => player.pause(),
};
const ytCtl = {
  time: () => (yt && yt.getCurrentTime ? yt.getCurrentTime() : 0),
  seek: t => yt && yt.seekTo && yt.seekTo(t, true),
  play: () => yt && yt.playVideo && yt.playVideo(),
  pause: () => yt && yt.pauseVideo && yt.pauseVideo(),
};
let ctl = videoCtl;
let previewPoll = null;

function stopPreviewTracking() {
  if (previewPoll !== null) clearInterval(previewPoll);
  previewPoll = null;
}

function previewSegment(segment) {
  stopPreviewTracking();
  const previewController = ctl;
  let seekObserved = false;
  let pollsBeforeSeek = 0;
  previewController.seek(segment.start);
  previewController.play();
  previewPoll = setInterval(() => {
    const currentTime = previewController.time();
    if (!seekObserved) {
      seekObserved = Math.abs(currentTime - segment.start) <= 1;
      if (!seekObserved) {
        pollsBeforeSeek += 1;
        if (pollsBeforeSeek >= 50) stopPreviewTracking();
        return;
      }
    }
    if (currentTime < segment.end) return;
    previewController.pause();
    stopPreviewTracking();
  }, 100);
}

function startYouTube(id) {
  return new Promise(resolve => {
    $('#yt-wrap').innerHTML = '<div id="yt"></div>';
    const make = () => {
      yt = new YT.Player('yt', {
        videoId: id,
        playerVars: { rel: 0, playsinline: 1 },
        events: {
          onReady: () => resolve(true),
          onError: () => setStatus(t('err_yt_playback'), true),
        },
      });
    };
    if (window.YT && YT.Player) make();
    else {
      window.onYouTubeIframeAPIReady = make;
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(s);
    }
    setTimeout(() => {
      if (!(yt && yt.getCurrentTime)) {
        setStatus(t('err_yt_load'), true);
        resolve(false);
      }
    }, 8000);
  });
}

function fmt(t) {
  const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
  const sec = s.toFixed(1).padStart(4, '0');
  return h ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`;
}

function fmtChartTime(seconds) {
  const total = Math.floor(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const remainder = total % 60;
  return hours
    ? `${hours}:${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
    : `${minutes}:${String(remainder).padStart(2, '0')}`;
}

function fmtHeatmapScore(score) {
  return Number(score.toPrecision(6)).toLocaleString(currentLang, {
    maximumSignificantDigits: 6,
  });
}

function captionForRange(data, start, end) {
  const comments = data && Array.isArray(data.caption_comments) ? data.caption_comments : [];
  const matches = comments.filter(comment =>
    Array.isArray(comment.timestamps)
      && comment.timestamps.some(timestamp => timestamp >= start && timestamp < end)
  ).sort((a, b) => (b.like_count || 0) - (a.like_count || 0));
  for (const comment of matches) {
    const text = String(comment.text || '')
      .replace(/(^|[^\d:])(?:\d{1,3}:)?\d{1,3}:[0-5]\d(?![\d:])/g, '$1')
      .replace(/\s+/g, ' ')
      .replace(/^[\s:;,.\-–—]+|[\s:;,.\-–—]+$/g, '')
      .trim();
    if (text) return text.length > 220 ? `${text.slice(0, 217).trimEnd()}...` : text;
  }
  return '';
}

function generateClipSuggestions(data, requestedCount, requestedDuration, existingSegments) {
  const totalDuration = Number(data.duration);
  const clipDuration = Math.min(totalDuration, requestedDuration);
  const bins = Array.isArray(data.bins) ? data.bins : [];
  if (!Number.isFinite(totalDuration) || totalDuration < 0.5
      || !Number.isFinite(clipDuration) || clipDuration < 0.5
      || !Number.isInteger(requestedCount) || requestedCount < 1) return [];

  const maxMentions = Math.max(0, ...bins.map(bin => bin.comment_mentions || 0));
  const viewerScores = bins
    .map(bin => bin.viewer_score)
    .filter(Number.isFinite)
    .map(score => Math.max(0, score));
  const maxViewers = Math.max(0, ...viewerScores);
  const hasMentions = maxMentions > 0;
  const hasViewers = maxViewers > 0;
  if (!hasMentions && !hasViewers) return [];

  const bothSignalsAvailable = hasMentions && hasViewers;
  const commentWeight = bothSignalsAvailable ? 0.5 : (hasMentions ? 1 : 0);
  const viewerWeight = bothSignalsAvailable ? 0.5 : (hasViewers ? 1 : 0);
  const rankedBins = bins.map(bin => {
    const viewerScore = Number.isFinite(bin.viewer_score) ? Math.max(0, bin.viewer_score) : 0;
    return {
      bin,
      viewerScore,
      rank: (hasMentions ? bin.comment_mentions / maxMentions * commentWeight : 0)
        + (hasViewers ? viewerScore / maxViewers * viewerWeight : 0),
    };
  }).filter(item => item.rank > 0).sort((a, b) =>
    b.rank - a.rank
    || b.bin.comment_mentions - a.bin.comment_mentions
    || b.viewerScore - a.viewerScore
    || a.bin.start - b.bin.start
  );

  const suggestions = [];
  const occupied = existingSegments.slice();
  for (const candidate of rankedBins) {
    const center = (candidate.bin.start + candidate.bin.end) / 2;
    const start = Math.max(0, Math.min(center - clipDuration / 2, totalDuration - clipDuration));
    const end = start + clipDuration;
    if (occupied.some(segment => start < segment.end && end > segment.start)) continue;
    const suggestion = {
      start,
      end,
      caption: captionForRange(data, candidate.bin.start, candidate.bin.end),
    };
    suggestions.push(suggestion);
    occupied.push(suggestion);
    if (suggestions.length >= requestedCount) break;
  }
  return suggestions.sort((a, b) => a.start - b.start);
}

function setSuggestionStatus(key, params = {}) {
  suggestionMessage = { key, params };
  $('#analysis-suggestion-status').textContent = t(key, params);
}

function renderAnalysis(data) {
  analysisData = data;
  const results = $('#comment-analysis-results');
  const chart = $('#comment-analysis-chart');
  const status = $('#comment-analysis-status');
  const rows = $('#analysis-data-rows');
  $('#analysis-mentions-value').textContent = data.timestamp_mentions.toLocaleString(currentLang);
  $('#analysis-comments-value').textContent = data.comment_count.toLocaleString(currentLang);
  chart.replaceChildren();
  rows.replaceChildren();

  const bins = data.bins || [];
  const hasMentions = bins.some(bin => bin.comment_mentions > 0);
  const viewerBins = bins.filter(bin => Number.isFinite(bin.viewer_score));
  const maxMentions = Math.max(1, ...bins.map(bin => bin.comment_mentions));
  const maxViewers = viewerBins.length
    ? Math.max(...viewerBins.map(bin => bin.viewer_score))
    : 0;
  results.hidden = bins.length === 0;
  const messages = [
    hasMentions ? '' : t('analysis_no_timestamps'),
    viewerBins.length ? '' : t('analysis_no_heatmap'),
  ].filter(Boolean);
  const commentPeak = bins.reduce(
    (best, bin) => bin.comment_mentions > (best ? best.comment_mentions : 0) ? bin : best,
    null
  );
  const viewerPeak = viewerBins.reduce(
    (best, bin) => bin.viewer_score > (best ? best.viewer_score : -Infinity) ? bin : best,
    null
  );
  const commentPeakValue = commentPeak
    ? t('analysis_peak_comments_value', {
      interval: `${fmtChartTime(commentPeak.start)}–${fmtChartTime(commentPeak.end)}`,
      count: commentPeak.comment_mentions.toLocaleString(currentLang),
    })
    : '—';
  const viewerPeakValue = viewerPeak
    ? t('analysis_peak_viewers_value', {
      interval: `${fmtChartTime(viewerPeak.start)}–${fmtChartTime(viewerPeak.end)}`,
      score: fmtHeatmapScore(viewerPeak.viewer_score),
    })
    : '—';
  $('#analysis-peak-comments-value').textContent = commentPeakValue;
  $('#analysis-peak-viewers-value').textContent = viewerPeakValue;
  $('#analysis-table-description').textContent = t('analysis_table_description', {
    seconds: data.bin_seconds,
  });
  if (commentPeak && viewerPeak) {
    messages.push(t('analysis_peaks', {
      comments: `${fmtChartTime(commentPeak.start)}–${fmtChartTime(commentPeak.end)}`,
      viewers: `${fmtChartTime(viewerPeak.start)}–${fmtChartTime(viewerPeak.end)}`,
      count: commentPeak.comment_mentions.toLocaleString(currentLang),
      score: fmtHeatmapScore(viewerPeak.viewer_score),
    }));
  }
  status.textContent = messages.join(' ');
  if (!bins.length) return;

  bins.forEach(bin => {
    const row = document.createElement('tr');
    const values = [
      `${fmtChartTime(bin.start)}–${fmtChartTime(bin.end)}`,
      bin.comment_mentions.toLocaleString(currentLang),
      Number.isFinite(bin.viewer_score) ? fmtHeatmapScore(bin.viewer_score) : '—',
    ];
    values.forEach((value, index) => {
      const cell = document.createElement('td');
      if (index > 0) cell.className = 'numeric';
      cell.textContent = value;
      row.appendChild(cell);
    });
    rows.appendChild(row);
  });

  const ns = 'http://www.w3.org/2000/svg';
  const add = (name, attrs, text) => {
    const node = document.createElementNS(ns, name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    chart.appendChild(node);
    return node;
  };
  const left = 64, right = 892, top = 24, bottom = 258;
  const width = right - left, height = bottom - top;
  const x = seconds => left + (seconds / data.duration) * width;
  const yViewers = value => bottom - (value / maxViewers) * height;
  chart.setAttribute('aria-label', t('analysis_chart_label'));

  for (let tick = 0; tick <= 4; tick++) {
    const fraction = tick / 4;
    const rowY = bottom - fraction * height;
    const count = Math.round(maxMentions * fraction);
    add('line', { x1: left, y1: rowY, x2: right, y2: rowY, stroke: 'rgba(255,255,255,0.12)' });
    add('text', { x: left - 10, y: rowY + 4, 'text-anchor': 'end' }, String(count));
    add('text', { x: right + 10, y: rowY + 4 }, `${Math.round(fraction * 100)}%`);
  }

  bins.forEach(bin => {
    const barHeight = (bin.comment_mentions / maxMentions) * height;
    if (barHeight <= 0) return;
    const bar = add('rect', {
      x: x(bin.start) + 1,
      y: bottom - barHeight,
      width: Math.max(1, x(bin.end) - x(bin.start) - 2),
      height: barHeight,
      fill: '#818cf8',
      rx: 2,
    });
    const title = document.createElementNS(ns, 'title');
    title.textContent = `${fmtChartTime(bin.start)}–${fmtChartTime(bin.end)}: ${bin.comment_mentions}`;
    bar.appendChild(title);
  });

  if (maxViewers > 0) {
    const points = viewerBins.map(bin => `${x((bin.start + bin.end) / 2)},${yViewers(bin.viewer_score)}`);
    if (points.length) {
      add('path', {
        d: `M ${points.join(' L ')}`,
        fill: 'none',
        stroke: '#34d399',
        'stroke-width': 3,
        'stroke-linejoin': 'round',
        'stroke-linecap': 'round',
      });
    }
  }

  for (let tick = 0; tick <= 4; tick++) {
    const tickTime = data.duration * tick / 4;
    add('text', { x: x(tickTime), y: bottom + 24, 'text-anchor': 'middle' }, fmtChartTime(tickTime));
  }
  add('text', { x: left, y: 310 }, currentLang === 'nl' ? 'Aantal vermeldingen' : 'Timestamp mentions');
  add('text', { x: right, y: 310, 'text-anchor': 'end' }, currentLang === 'nl' ? 'Relatieve kijkersinteresse' : 'Relative viewer interest');
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

async function api(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || t('err_generic'));
  return data;
}

function drawTimeline() {
  const tl = $('#timeline');
  tl.querySelectorAll('.seg, .draft').forEach(e => e.remove());
  const pct = t => (t / duration * 100) + '%';
  segments.forEach(s => {
    const el = document.createElement('div');
    el.className = 'seg';
    el.style.left = pct(s.start);
    el.style.width = pct(s.end - s.start);
    tl.appendChild(el);
  });
  const a = parse($('#start').value), b = parse($('#end').value);
  if (a >= 0 && b > a) {
    const el = document.createElement('div');
    el.className = 'draft';
    el.style.left = pct(a);
    el.style.width = pct(Math.min(b, duration) - a);
    tl.appendChild(el);
  }
}

function renderSegments() {
  const ul = $('#segments');
  ul.innerHTML = '';
  segments.forEach((s, i) => {
    const li = document.createElement('li');
    const label = document.createElement('span');
    const suggestionLabel = s.auto ? ` · ${t('segment_auto')}${s.score ? ` ${s.score}/100` : ''}`
      : (s.suggested ? ` · ${t('segment_suggestion')}` : '');
    label.textContent = `${fmt(s.start)} ${t('to')} ${fmt(s.end)} (${Math.round(s.end - s.start)} s)${suggestionLabel}`;
    const main = document.createElement('span');
    main.className = 'segment-main';
    main.appendChild(label);
    if (s.auto) {
      const cap = document.createElement('input');
      cap.className = 'segment-caption';
      cap.value = s.caption || '';
      cap.placeholder = t('caption_placeholder');
      cap.oninput = () => { s.caption = cap.value; };
      main.appendChild(cap);
      if (s.reason) {
        const why = document.createElement('span');
        why.className = 'segment-reason';
        why.textContent = s.reason;
        main.appendChild(why);
      }
    }
    const actions = document.createElement('span');
    actions.className = 'actions';
    const go = document.createElement('button');
    go.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> ${t('btn_preview')}`;
    go.onclick = () => previewSegment(s);
    const del = document.createElement('button');
    del.className = 'btn-del';
    del.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg> ${t('btn_delete')}`;
    del.onclick = () => {
      segments.splice(i, 1);
      suggestionMessage = null;
      $('#analysis-suggestion-status').textContent = '';
      renderSegments();
    };
    actions.append(go, del);
    li.append(main, actions);
    ul.appendChild(li);
  });
  $('#empty').hidden = segments.length > 0;
  $('#render-btn').disabled = segments.length === 0;
  drawTimeline();
}

$('#timeline').addEventListener('click', e => {
  const box = e.currentTarget.getBoundingClientRect();
  ctl.seek(((e.clientX - box.left) / box.width) * duration);
});

setInterval(() => {
  if (!duration) return;
  try { $('#playhead').style.left = (ctl.time() / duration * 100) + '%'; } catch (e) {}
}, 250);

['start', 'end'].forEach(id => $('#' + id).addEventListener('input', drawTimeline));
$('#start-now').onclick = () => { $('#start').value = fmt(ctl.time()); drawTimeline(); };
$('#end-now').onclick = () => { $('#end').value = fmt(ctl.time()); drawTimeline(); };

// Opties toggles & afhankelijke controls
const subsCheck = $('#subs');
const langSelect = $('#lang');
const subLangRow = $('#sub-lang-row');
const groupSubs = $('#group-subs');

function updateSubsState() {
  langSelect.disabled = !subsCheck.checked;
  subLangRow.classList.toggle('disabled', !subsCheck.checked);
  $('#whisper-model').disabled = !subsCheck.checked;
  $('#sub-model-row').classList.toggle('disabled', !subsCheck.checked);
  groupSubs.classList.toggle('active', subsCheck.checked);
}
subsCheck.addEventListener('change', updateSubsState);

const vertCheck = $('#vertical');
const blurCheck = $('#blur');
const logoInput = $('#logo');
const vertControls = $('#vertical-sub-controls');
const groupVert = $('#group-vertical');

function updateVerticalState() {
  blurCheck.disabled = !vertCheck.checked;
  logoInput.disabled = !vertCheck.checked;
  if (!vertCheck.checked) {
    blurCheck.checked = false;
    logoInput.value = '';
  }
  vertControls.classList.toggle('disabled', !vertCheck.checked);
  groupVert.classList.toggle('active', vertCheck.checked);
}
vertCheck.addEventListener('change', updateVerticalState);

const captionToggle = $('#caption-toggle');
const captionPosition = $('#caption-position');
const captionPositionRow = $('#caption-position-row');
const groupCaption = $('#group-caption');

function updateCaptionState() {
  captionPosition.disabled = !captionToggle.checked;
  captionPositionRow.classList.toggle('disabled', !captionToggle.checked);
  groupCaption.classList.toggle('active', captionToggle.checked);
}
captionToggle.addEventListener('change', updateCaptionState);

// Het TikTok-paneel heeft eigen knoppen die gekoppeld zijn aan de opties onderaan.
const autoLinks = [...document.querySelectorAll('#auto-panel [data-link]')]
  .map(el => ({ el, target: $(el.dataset.link) }));

function syncAutoOptions() {
  for (const { el, target } of autoLinks) {
    if (el.type === 'checkbox') el.checked = target.checked;
    else el.value = target.value;
    el.disabled = target.disabled;
    const box = el.closest('.auto-option');
    if (box && el.type === 'checkbox') box.classList.toggle('disabled', target.disabled);
  }
}

for (const { el, target } of autoLinks) {
  el.addEventListener('change', () => {
    if (el.type === 'checkbox') target.checked = el.checked;
    else target.value = el.value;
    target.dispatchEvent(new Event('change'));
    syncAutoOptions();
  });
  target.addEventListener('change', syncAutoOptions);
}

$('#add').onclick = () => {
  const start = parse($('#start').value), end = parse($('#end').value);
  if (isNaN(start) || isNaN(end)) return setStatus(t('err_times'), true);
  if (end <= start) return setStatus(t('err_end_before_start'), true);
  if (end > duration + 0.5) return setStatus(t('err_end_exceeds', { duration: fmt(duration) }), true);
  segments.push({ start, end: Math.min(end, duration) });
  segments.sort((a, b) => a.start - b.start);
  $('#start').value = '';
  $('#end').value = '';
  setStatus('');
  renderSegments();
};

// --- video laden ---
$('#load-form').addEventListener('submit', async e => {
  e.preventDefault();
  $('#load-btn').disabled = true;
  setStatus(t('msg_searching'));
  try {
    const data = await api('/api/load', { url: $('#url').value });
    job = data.job; duration = data.duration; segments = [];
    stopPreviewTracking();
    analysisData = null;
    suggestionMessage = null;
    updateCaptionState();
    syncAutoOptions();
    $('#comment-analysis-results').hidden = true;
    $('#comment-analysis-status').textContent = '';
    $('#analysis-suggestion-status').textContent = '';
    $('#auto-status').textContent = '';
    $('#comment-analysis-panel').hidden = data.mode !== 'youtube';
    groupCaption.hidden = false;
    player.pause();
    $('#editor').hidden = false;
    $('#results').hidden = true;
    let ok = true;
    if (data.mode === 'youtube') {
      player.hidden = true; $('#yt-wrap').hidden = false;
      ctl = ytCtl;
      ok = await startYouTube(data.id);
    } else {
      $('#yt-wrap').hidden = true; player.hidden = false;
      ctl = videoCtl;
      player.src = data.video;
    }
    renderSegments();
    if (ok) setStatus(t('msg_loaded', { duration: fmt(duration) }));
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    $('#load-btn').disabled = false;
  }
});

$('#analyze-comments-btn').onclick = async () => {
  const btn = $('#analyze-comments-btn');
  btn.disabled = true;
  analysisData = null;
  suggestionMessage = null;
  $('#comment-analysis-status').textContent = t('analysis_loading');
  $('#analysis-suggestion-status').textContent = '';
  $('#comment-analysis-results').hidden = true;
  try {
    const data = await api('/api/analyze-comments', { url: $('#url').value });
    renderAnalysis(data);
  } catch (err) {
    $('#comment-analysis-status').textContent = err.message;
  } finally {
    btn.disabled = false;
  }
};

$('#generate-suggestions-btn').onclick = () => {
  if (!analysisData) return;
  const manualSegments = segments.filter(segment => !segment.suggested);
  const suggestions = generateClipSuggestions(
    analysisData,
    Number($('#analysis-clip-count').value),
    Number($('#analysis-clip-duration').value),
    manualSegments
  );
  if (!suggestions.length) {
    setSuggestionStatus('analysis_suggestions_none');
    return;
  }
  segments = [
    ...manualSegments,
    ...suggestions.map(segment => ({ ...segment, suggested: true })),
  ].sort((a, b) => a.start - b.start);
  renderSegments();
  const key = suggestions.length === 1
    ? 'analysis_suggestions_added_singular'
    : 'analysis_suggestions_added_plural';
  setSuggestionStatus(key, { count: suggestions.length });
  $('#segments').scrollIntoView({ behavior: 'smooth', block: 'center' });
};

// --- automatisch TikToks maken ---
$('#auto-btn').onclick = async () => {
  const btn = $('#auto-btn');
  const [minLen, maxLen] = $('#auto-length').value.split('-').map(Number);
  btn.disabled = true;
  $('#auto-status').textContent = t('auto_working');
  try {
    const data = await api('/api/auto-clips', {
      job,
      count: Number($('#auto-count').value),
      min_len: minLen,
      max_len: maxLen,
      language: $('#lang').value,
      whisper_model: $('#whisper-model').value,
      speech: subsCheck.checked,
      bins: analysisData && Array.isArray(analysisData.bins) ? analysisData.bins : null,
      comments: analysisData && Array.isArray(analysisData.caption_comments)
        ? analysisData.caption_comments : null,
    });
    const manualSegments = segments.filter(segment => !segment.suggested && !segment.auto);
    const aiSegments = data.clips
      .filter(c => !manualSegments.some(m => c.start < m.end && c.end > m.start))
      .map(c => ({
        start: c.start,
        end: c.end,
        caption: c.caption,
        reason: c.reason,
        score: c.score,
        postText: [c.description, (c.hashtags || []).join(' ')].filter(Boolean).join('\n\n'),
        auto: true,
      }));
    segments = [...manualSegments, ...aiSegments].sort((a, b) => a.start - b.start);
    renderSegments();
    if ($('#auto-export').checked && aiSegments.length) {
      $('#auto-status').textContent = t('auto_done_exporting', { count: aiSegments.length });
      $('#render-btn').click();
    } else {
      $('#auto-status').textContent = t('auto_done', { count: aiSegments.length });
      $('#segments').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  } catch (err) {
    $('#auto-status').textContent = err.message;
  } finally {
    btn.disabled = false;
  }
};

// --- clips maken ---
$('#render-btn').onclick = async () => {
  const captionsEnabled = captionToggle.checked;
  if (captionsEnabled && !analysisData && segments.some(segment => !segment.caption && !segment.auto)) {
    setStatus(t('err_caption_analysis'), true);
    return;
  }
  const renderSegments = segments.map(segment => ({
    start: segment.start,
    end: segment.end,
    caption: captionsEnabled
      ? ((segment.caption || '').trim()
        || (analysisData ? captionForRange(analysisData, segment.start, segment.end) : ''))
      : '',
    post_text: segment.postText || '',
  }));
  const missingCaptions = captionsEnabled
    ? renderSegments.filter(segment => !segment.caption).length
    : 0;
  const btn = $('#render-btn');
  btn.disabled = true;
  setStatus($('#subs').checked
    ? t('msg_processing_subs')
    : t('msg_processing'));
  try {
    let hasLogo = false;
    const logoFile = $('#logo').files[0];
    if ($('#vertical').checked && logoFile) {
      const fd = new FormData();
      fd.append('job', job);
      fd.append('file', logoFile);
      const r = await fetch('/api/logo', { method: 'POST', body: fd });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error || t('err_logo_upload'));
      hasLogo = true;
    }
    const data = await api('/api/render', {
      job, segments: renderSegments,
      subtitles: $('#subs').checked,
      language: $('#lang').value,
      whisper_model: $('#whisper-model').value,
      vertical: $('#vertical').checked,
      blur: $('#blur').checked,
      logo: hasLogo,
      caption_position: captionPosition.value,
    });
    const box = $('#clips');
    box.innerHTML = '';
    data.clips.forEach(c => {
      const fig = document.createElement('figure');
      const v = document.createElement('video');
      v.controls = true;
      v.src = c.url;
      const cap = document.createElement('figcaption');
      const mp4 = document.createElement('a');
      mp4.href = c.url; mp4.download = c.name;
      mp4.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg> MP4';
      cap.appendChild(mp4);
      if (c.srt) {
        const srt = document.createElement('a');
        srt.href = c.srt; srt.download = c.name.replace('.mp4', '.srt');
        srt.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-9 9H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v4zm7 0h-3.5V9H18v1.5h-2v.75h2v1.5h-2v.25h2V13z"/></svg> SRT';
        cap.appendChild(srt);
      }
      const emailForm = document.createElement('form');
      emailForm.className = 'clip-email';
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
            name: c.name,
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
      if (c.txt) {
        const txt = document.createElement('a');
        txt.href = c.txt; txt.download = c.name.replace('.mp4', '.txt');
        txt.textContent = 'TXT';
        cap.appendChild(txt);
      }
      const extras = [];
      if (c.post_text) {
        const post = document.createElement('p');
        post.className = 'post-text';
        post.textContent = c.post_text;
        const copy = document.createElement('button');
        copy.type = 'button';
        copy.textContent = t('btn_copy_post');
        copy.onclick = async () => {
          try {
            await navigator.clipboard.writeText(c.post_text);
            setStatus(t('msg_copied'));
          } catch (err) {
            setStatus(err.message, true);
          }
        };
        extras.push(post, copy);
      }
      fig.append(v, cap, ...extras, emailForm);
      box.appendChild(fig);
    });
    $('#results').hidden = false;
    setStatus(missingCaptions
      ? t('msg_done_caption_missing', { count: data.clips.length, missing: missingCaptions })
      : t('msg_done', { count: data.clips.length }));
    $('#results').scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    btn.disabled = segments.length === 0;
  }
};

// --- instellingen onthouden (alleen in deze browser) ---
const SETTINGS_KEY = 'clipapp_settings';
// volgorde telt: 9:16 voor blur, want blur kan alleen aan als 9:16 aanstaat
const REMEMBERED = ['#subs', '#lang', '#whisper-model', '#vertical', '#blur', '#caption-toggle', '#caption-position',
  '#auto-count', '#auto-length', '#auto-export', '#analysis-clip-count', '#analysis-clip-duration'];

function saveSettings() {
  const values = {};
  for (const sel of REMEMBERED) {
    const el = $(sel);
    if (el) values[sel] = el.type === 'checkbox' ? el.checked : el.value;
  }
  try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(values)); } catch (e) {}
}

function restoreSettings() {
  let values = {};
  try { values = JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}') || {}; } catch (e) {}
  for (const sel of REMEMBERED) {
    const el = $(sel);
    if (!el || !(sel in values)) continue;
    if (el.type === 'checkbox') el.checked = Boolean(values[sel]);
    else if ([...el.options].some(o => o.value === values[sel])) el.value = values[sel];
    if (sel === '#subs') updateSubsState();
    if (sel === '#vertical') updateVerticalState();
  }
  updateVerticalState();               // blur uit als 9:16 uit staat
  updateCaptionState();
}

restoreSettings();
for (const sel of REMEMBERED) {
  const el = $(sel);
  if (el) el.addEventListener('change', saveSettings);
}

// Initialiseer taal bij laden van de pagina
setLanguage(currentLang);
syncAutoOptions();
