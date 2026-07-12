(() => {
  const data = window.SENTENCE_DATA;
  const notes = window.CHAPTER_NOTES || [];
  const $ = id => document.getElementById(id);
  const escapeHtml = value => String(value).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const chapterKeys = [...new Set(data.rows.map(row => `${row.book}:${row.chapter}`))];
  const state = { chapterIndex: 0, query: '' };
  const keyParts = key => { const [book, chapter] = key.split(':'); return {book, chapter:Number(chapter)}; };
  const current = () => keyParts(chapterKeys[state.chapterIndex]);
  const chapterLabel = index => index < 0 || index >= chapterKeys.length ? '' : (() => { const c=keyParts(chapterKeys[index]); return `Book ${c.book} · Chapter ${c.chapter}`; })();
  const toast = message => { $('toast').textContent=message; $('toast').classList.add('show'); clearTimeout(toast.timer); toast.timer=setTimeout(()=>$('toast').classList.remove('show'),1500); };

  $('totalCount').textContent = data.meta.rowCount.toLocaleString();
  $('bookCount').textContent = data.meta.bookCount;
  $('chapterCount').textContent = data.meta.chapterCount;
  data.meta.books.forEach(book => $('bookFilter').insertAdjacentHTML('beforeend', `<option value="${escapeHtml(book)}">Book ${escapeHtml(book)}</option>`));

  function updateChapterOptions() {
    const {book,chapter} = current();
    const chapters = chapterKeys.map(keyParts).filter(item => item.book===book);
    $('bookFilter').value = book;
    $('chapterFilter').innerHTML = chapters.map(item => `<option value="${item.chapter}"${item.chapter===chapter?' selected':''}>Chapter ${item.chapter}</option>`).join('');
  }

  function renderNote() {
    const {book,chapter}=current();
    const note=notes.find(item=>String(item.book)===book && Number(item.chapter)===chapter);
    const panel=$('chapterNote');
    if(!note){panel.hidden=true; panel.innerHTML=''; return;}
    const list = (title,items) => !items?.length ? '' : `<div><h4>${title}</h4><ul>${items.map(item=>`<li><span>${escapeHtml(item.label||item)}</span>${item.explanation_zh?` — ${escapeHtml(item.explanation_zh)}`:''}</li>`).join('')}</ul></div>`;
    const topics=note.topics_zh || (note.topic_zh ? [note.topic_zh] : []);
    panel.innerHTML=`<div class="chapter-note-head"><div><span class="chapter-note-kicker">CHAPTER GUIDE · CORPUS-INFERRED</span><h3>${topics.map(escapeHtml).join('／')}</h3></div><span class="chapter-note-status">reference only</span></div><div class="chapter-note-grid">${list('CORE PATTERNS',note.patterns||note.patterns_zh)}${list('GRAMMAR',note.grammar||note.grammar_zh)}${list('FUNCTIONS & PRAGMATICS',note.functions||note.functions_zh)}</div>`;
    panel.hidden=false;
  }

  function render() {
    updateChapterOptions(); renderNote();
    const {book,chapter}=current();
    const query=state.query.trim().toLocaleLowerCase();
    const all=data.rows.filter(row=>row.book===book && row.chapter===chapter);
    const rows=all.filter(row=>!query || `${row.id} ${row.thai} ${row.english}`.toLocaleLowerCase().includes(query));
    $('visibleCount').textContent=rows.length.toLocaleString();
    $('chapterPosition').textContent=`Chapter ${state.chapterIndex+1} of ${chapterKeys.length}`;
    $('resultLabel').textContent=`${chapterLabel(state.chapterIndex)} · ${rows.length} of ${all.length} sentences`;
    $('emptyState').hidden=rows.length>0;
    $('sentenceGrid').innerHTML=rows.map(row=>`<article class="sentence-card"><div class="card-meta"><span class="chip">BOOK ${escapeHtml(row.book)} · CH ${row.chapter}</span><span class="chip level">${escapeHtml(row.level)}</span><span class="row-id">#${String(row.id).padStart(4,'0')} · L${row.sourceLine}</span></div><p class="thai" lang="th">${escapeHtml(row.thai)}</p><p class="english">${escapeHtml(row.english)}</p><div class="actions"><button class="icon-button speak" data-id="${row.id}" title="Speak Thai" aria-label="Speak Thai">▶</button><button class="icon-button copy" data-id="${row.id}" title="Copy sentence" aria-label="Copy sentence">⧉</button></div></article>`).join('');
    $('prevChapter').disabled=state.chapterIndex===0; $('nextChapter').disabled=state.chapterIndex===chapterKeys.length-1;
    $('prevChapterLabel').textContent=chapterLabel(state.chapterIndex-1); $('nextChapterLabel').textContent=chapterLabel(state.chapterIndex+1);
    const url=new URL(location.href); url.searchParams.set('book',book); url.searchParams.set('chapter',chapter); history.replaceState(null,'',url);
  }

  function go(index){state.chapterIndex=Math.max(0,Math.min(chapterKeys.length-1,index));state.query='';$('searchInput').value='';render();document.querySelector('.explorer').scrollIntoView({behavior:'smooth'});}
  $('bookFilter').addEventListener('change',e=>go(chapterKeys.findIndex(key=>key.startsWith(`${e.target.value}:`))));
  $('chapterFilter').addEventListener('change',e=>{const book=current().book;go(chapterKeys.indexOf(`${book}:${e.target.value}`));});
  $('searchInput').addEventListener('input',e=>{state.query=e.target.value;render();});
  $('resetButton').addEventListener('click',()=>go(0)); $('prevChapter').addEventListener('click',()=>go(state.chapterIndex-1)); $('nextChapter').addEventListener('click',()=>go(state.chapterIndex+1));
  $('sentenceGrid').addEventListener('click',async event=>{const button=event.target.closest('button[data-id]');if(!button)return;const row=data.rows[Number(button.dataset.id)-1];if(button.classList.contains('copy')){await navigator.clipboard.writeText(`${row.thai}\n${row.english}`);return toast('Sentence copied');}if(!('speechSynthesis'in window))return toast('Speech is unavailable in this browser');speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(row.thai);utterance.lang='th-TH';utterance.rate=.82;speechSynthesis.speak(utterance);});
  const params=new URLSearchParams(location.search);const requested=`${params.get('book')}:${params.get('chapter')}`;if(chapterKeys.includes(requested))state.chapterIndex=chapterKeys.indexOf(requested);render();
})();
