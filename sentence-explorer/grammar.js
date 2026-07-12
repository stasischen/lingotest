(() => {
  const notes = window.CHAPTER_NOTES || [];
  const corpus = window.SENTENCE_DATA || {rows:[]};
  const $ = id => document.getElementById(id);
  const escapeHtml = value => String(value).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const thaiRuns = value => escapeHtml(value).replace(/[\u0E00-\u0E7F]+(?:\s+[\u0E00-\u0E7F]+)*/g, text => `<button class="thai-keyword" type="button" data-speak="${text}" lang="th" title="播放泰文：${text}" aria-label="播放泰文 ${text}">${text}<span aria-hidden="true">◖</span></button>`);
  const normalize = value => String(value).toLocaleLowerCase().replace(/[／/|+＋、，,;；:：()（）[\]{}]/g,' ').replace(/\s+/g,' ').trim();
  const rowsByLine = new Map(corpus.rows.map(row => [Number(row.sourceLine), row]));
  const observations = [];

  notes.forEach(note => {
    [['pattern', note.patterns || []], ['grammar', note.grammar || []]].forEach(([kind, items]) => {
      items.forEach((item, index) => observations.push({
        id: `${note.book}:${note.chapter}:${kind}:${index + 1}`,
        kind,
        book: String(note.book),
        chapter: Number(note.chapter),
        label: item.label,
        explanation: item.explanation_zh,
        lines: item.example_lines || [],
      }));
    });
  });

  const books = [...new Set(notes.map(note => String(note.book)))];
  books.forEach(book => $('bookFilter').insertAdjacentHTML('beforeend', `<option value="${escapeHtml(book)}">Book ${escapeHtml(book)}</option>`));
  $('patternCount').textContent = observations.filter(item => item.kind === 'pattern').length.toLocaleString();
  $('grammarCount').textContent = observations.filter(item => item.kind === 'grammar').length.toLocaleString();
  $('exampleCount').textContent = observations.reduce((sum,item) => sum + item.lines.length, 0).toLocaleString();

  const state = {query:'', type:'all', book:'all', view:'observations', page:1, pageSize:40};
  const evidence = item => item.lines.map(line => rowsByLine.get(Number(line))).filter(Boolean);
  const searchable = item => `${item.label} ${item.explanation} ${evidence(item).map(row => `${row.thai} ${row.english}`).join(' ')}`.toLocaleLowerCase();

  function groupedItems(items) {
    const groups = new Map();
    items.forEach(item => {
      const key = `${item.kind}:${normalize(item.label)}`;
      if (!groups.has(key)) groups.set(key, {...item, observations:[], lines:[]});
      const group = groups.get(key);
      group.observations.push(item);
      group.lines.push(...item.lines);
    });
    return [...groups.values()].map(group => ({...group, lines:[...new Set(group.lines)]}));
  }

  function card(item) {
    const examples = evidence(item);
    const source = item.observations || [item];
    const sourceLinks = source.slice(0,12).map(obs => `<a href="sentences.html?book=${encodeURIComponent(obs.book)}&chapter=${obs.chapter}">B${escapeHtml(obs.book)} · C${obs.chapter}</a>`).join('');
    return `<article class="grammar-card"><div class="grammar-card-head"><h3>${thaiRuns(item.label)}</h3><span class="kind-badge ${item.kind}">${item.kind==='pattern'?'sentence pattern':'grammar'}</span></div><p class="grammar-explanation">${thaiRuns(item.explanation)}</p><div class="source-meta"><span>Book ${escapeHtml(item.book)}</span><span>Chapter ${item.chapter}</span><span>${item.lines.length} evidence line${item.lines.length===1?'':'s'}</span>${item.observations?`<span>${item.observations.length} grouped observation${item.observations.length===1?'':'s'}</span>`:''}</div><div class="example-list">${examples.length?examples.map(row=>`<div class="example"><div class="example-thai-row"><p class="thai" lang="th">${escapeHtml(row.thai)}</p><button class="example-speak" type="button" data-speak="${escapeHtml(row.thai)}" title="播放完整例句" aria-label="播放泰文例句">▶ <span>播放</span></button></div><p class="english">${escapeHtml(row.english)}</p><small>Source line ${row.sourceLine} · ${escapeHtml(row.level)} · row #${row.id}</small></div>`).join(''):'<p class="missing-example">No matching sentence row found for this evidence locator.</p>'}</div>${item.observations?`<p class="group-summary">Grouped by normalized label only. Review each original chapter observation before canonical merging.</p><div class="observation-links">${sourceLinks}</div>`:''}</article>`;
  }

  function render() {
    const q = state.query.trim().toLocaleLowerCase();
    let items = observations.filter(item => (state.type==='all'||item.kind===state.type) && (state.book==='all'||item.book===state.book) && (!q||searchable(item).includes(q)));
    if (state.view === 'grouped') items = groupedItems(items);
    const pages = Math.max(1,Math.ceil(items.length/state.pageSize));
    state.page = Math.min(state.page,pages);
    const start = (state.page-1)*state.pageSize;
    const visible = items.slice(start,start+state.pageSize);
    $('visibleCount').textContent = items.length.toLocaleString();
    $('resultLabel').textContent = `${items.length.toLocaleString()} ${state.view==='grouped'?'grouped labels':'observations'} · showing ${items.length?start+1:0}–${Math.min(start+state.pageSize,items.length)}`;
    $('grammarGrid').innerHTML = visible.map(card).join('');
    $('emptyState').hidden = items.length>0;
    $('pagePosition').textContent = `Page ${state.page} of ${pages}`;
    $('prevPage').disabled = state.page===1; $('nextPage').disabled = state.page===pages;
    const url = new URL(location.href); [['type',state.type],['book',state.book],['view',state.view],['q',state.query]].forEach(([key,value]) => value&&value!=='all'&&value!=='observations'?url.searchParams.set(key,value):url.searchParams.delete(key)); history.replaceState(null,'',url);
  }

  function resetPage(){state.page=1;render();}
  $('searchInput').addEventListener('input',e=>{state.query=e.target.value;resetPage();});
  $('typeFilter').addEventListener('change',e=>{state.type=e.target.value;resetPage();});
  $('bookFilter').addEventListener('change',e=>{state.book=e.target.value;resetPage();});
  $('viewFilter').addEventListener('change',e=>{state.view=e.target.value;resetPage();});
  $('pageSize').addEventListener('change',e=>{state.pageSize=Number(e.target.value);resetPage();});
  $('prevPage').addEventListener('click',()=>{state.page--;render();scrollTo({top:document.querySelector('.grammar-explorer').offsetTop-20,behavior:'smooth'});});
  $('nextPage').addEventListener('click',()=>{state.page++;render();scrollTo({top:document.querySelector('.grammar-explorer').offsetTop-20,behavior:'smooth'});});
  $('resetButton').addEventListener('click',()=>{Object.assign(state,{query:'',type:'all',book:'all',view:'observations',page:1,pageSize:40});['searchInput','typeFilter','bookFilter','viewFilter','pageSize'].forEach(id=>$(id).value=id==='pageSize'?'40':id==='viewFilter'?'observations':id==='searchInput'?'':'all');render();});
  $('grammarGrid').addEventListener('click', event => {
    const button = event.target.closest('[data-speak]');
    if (!button) return;
    const status = $('speechStatus');
    if (!('speechSynthesis' in window)) { status.textContent = '此瀏覽器不支援語音播放。'; return; }
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(button.dataset.speak);
    utterance.lang = 'th-TH'; utterance.rate = .82;
    utterance.onstart = () => { status.textContent = `正在播放：${button.dataset.speak}`; button.classList.add('speaking'); };
    utterance.onend = utterance.onerror = () => { status.textContent = ''; button.classList.remove('speaking'); };
    speechSynthesis.speak(utterance);
  });
  const params = new URLSearchParams(location.search); if(['pattern','grammar'].includes(params.get('type')))state.type=params.get('type');if(books.includes(params.get('book')))state.book=params.get('book');if(params.get('view')==='grouped')state.view='grouped';state.query=params.get('q')||'';$('typeFilter').value=state.type;$('bookFilter').value=state.book;$('viewFilter').value=state.view;$('searchInput').value=state.query;render();
})();
