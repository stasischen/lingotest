(() => {
  const data = window.SENTENCE_DATA;
  const $ = id => document.getElementById(id);
  const state = { page: 1, size: 48, query: '', book: '', chapter: '', level: '', speaker: '' };
  const collator = new Intl.Collator(undefined, { numeric: true });
  let filtered = data.rows;

  const escapeHtml = value => String(value).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const unique = values => [...new Set(values)];
  const populate = (select, values, label) => values.forEach(value => select.insertAdjacentHTML('beforeend', `<option value="${escapeHtml(value)}">${label ? label(value) : escapeHtml(value)}</option>`));
  const toast = message => { $('toast').textContent = message; $('toast').classList.add('show'); clearTimeout(toast.timer); toast.timer = setTimeout(() => $('toast').classList.remove('show'), 1500); };

  $('totalCount').textContent = data.meta.rowCount.toLocaleString();
  $('bookCount').textContent = data.meta.bookCount;
  $('chapterCount').textContent = data.meta.chapterCount;
  populate($('bookFilter'), data.meta.books, value => `Book ${value}`);
  populate($('levelFilter'), unique(data.rows.map(row => row.level)));

  function updateChapters() {
    const selected = state.chapter;
    const chapters = unique(data.rows.filter(row => !state.book || row.book === state.book).map(row => row.chapter)).sort((a,b) => a-b);
    $('chapterFilter').innerHTML = '<option value="">All chapters</option>';
    populate($('chapterFilter'), chapters, value => `Chapter ${value}`);
    if (chapters.map(String).includes(selected)) $('chapterFilter').value = selected; else state.chapter = '';
  }

  function applyFilters() {
    const query = state.query.trim().toLocaleLowerCase();
    filtered = data.rows.filter(row =>
      (!state.book || row.book === state.book) &&
      (!state.chapter || String(row.chapter) === state.chapter) &&
      (!state.level || row.level === state.level) &&
      (!state.speaker || row.speaker === state.speaker) &&
      (!query || `${row.id} ${row.thai} ${row.english}`.toLocaleLowerCase().includes(query))
    );
    const pages = Math.max(1, Math.ceil(filtered.length / state.size));
    state.page = Math.min(state.page, pages);
    render();
  }

  function render() {
    const pages = Math.max(1, Math.ceil(filtered.length / state.size));
    const start = (state.page - 1) * state.size;
    const rows = filtered.slice(start, start + state.size);
    $('visibleCount').textContent = filtered.length.toLocaleString();
    $('resultLabel').textContent = `${filtered.length.toLocaleString()} matches · showing ${filtered.length ? start + 1 : 0}–${Math.min(start + state.size, filtered.length)}`;
    $('pageLabel').textContent = `Page ${state.page} of ${pages}`;
    $('prevPage').disabled = state.page <= 1;
    $('nextPage').disabled = state.page >= pages;
    $('emptyState').hidden = rows.length > 0;
    $('sentenceGrid').innerHTML = rows.map(row => `<article class="sentence-card">
      <div class="card-meta"><span class="chip">BOOK ${escapeHtml(row.book)} · CH ${row.chapter}</span><span class="chip level">${escapeHtml(row.level)}</span><span class="row-id">#${String(row.id).padStart(4,'0')} · L${row.sourceLine}</span></div>
      <p class="thai" lang="th">${escapeHtml(row.thai)}</p><p class="english">${escapeHtml(row.english)}</p>
      <div class="actions"><button class="icon-button speak" data-id="${row.id}" title="Speak Thai" aria-label="Speak Thai">▶</button><button class="icon-button copy" data-id="${row.id}" title="Copy sentence" aria-label="Copy sentence">⧉</button></div>
    </article>`).join('');
    window.scrollTo({ top: Math.min(window.scrollY, document.querySelector('.explorer').offsetTop - 18), behavior: 'smooth' });
  }

  const bind = (id, key, event = 'change') => $(id).addEventListener(event, e => { state[key] = e.target.value; state.page = 1; if (key === 'book') updateChapters(); applyFilters(); });
  bind('searchInput','query','input'); bind('bookFilter','book'); bind('chapterFilter','chapter'); bind('levelFilter','level'); bind('speakerFilter','speaker');
  $('pageSize').addEventListener('change', e => { state.size = Number(e.target.value); state.page = 1; applyFilters(); });
  $('prevPage').addEventListener('click', () => { state.page--; render(); }); $('nextPage').addEventListener('click', () => { state.page++; render(); });
  $('resetButton').addEventListener('click', () => { Object.assign(state,{page:1,query:'',book:'',chapter:'',level:'',speaker:''}); ['searchInput','bookFilter','chapterFilter','levelFilter','speakerFilter'].forEach(id => $(id).value=''); updateChapters(); applyFilters(); });
  $('sentenceGrid').addEventListener('click', async event => {
    const button = event.target.closest('button[data-id]'); if (!button) return;
    const row = data.rows[Number(button.dataset.id) - 1];
    if (button.classList.contains('copy')) { await navigator.clipboard.writeText(`${row.thai}\n${row.english}`); toast('Sentence copied'); return; }
    if (!('speechSynthesis' in window)) return toast('Speech is unavailable in this browser');
    speechSynthesis.cancel(); const utterance = new SpeechSynthesisUtterance(row.thai); utterance.lang='th-TH'; utterance.rate=.82; speechSynthesis.speak(utterance);
  });
  updateChapters(); applyFilters();
})();
