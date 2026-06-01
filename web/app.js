/* app.js - Loads pre-extracted dataset.json from /data/dataset.json and implements Study and Quiz modes */
const DATA_URL = 'data/dataset.json';
let dataset = null;
let currentPageIndex = 0;
let filteredPages = [];
let quizItems = []; // each item: {image, pageIndex, slideName, features}
let quizState = {index:0,score:0,answers:[]};

async function loadDataset(){
  const res = await fetch(DATA_URL);
  dataset = await res.json();
  filteredPages = dataset.pages || [];
  buildPageSelect();
  renderStudyPage(0);
  buildQuizItems();
  updateStats();
}

function buildPageSelect(){
  const sel = document.getElementById('page-select');
  sel.innerHTML = '';
  filteredPages.forEach((p,i)=>{
    const o = document.createElement('option'); o.value=i; o.textContent = `Page ${p.pageNumber} - ${p.slideName||'(no title)'}`; sel.appendChild(o);
  });
  sel.addEventListener('change',e=>{ renderStudyPage(parseInt(e.target.value,10)); });
}

function renderStudyPage(i){
  currentPageIndex = i;
  const page = filteredPages[i];
  document.getElementById('current-page-indicator').textContent = `Page ${page.pageNumber} (${i+1}/${filteredPages.length})`;
  document.getElementById('page-select').value = i;
  const container = document.getElementById('slide-container');
  container.innerHTML = '';
  const title = document.createElement('div'); title.className='slide-title'; title.textContent = page.slideName || `Page ${page.pageNumber}`;
  container.appendChild(title);
  // images
  const imgs = document.createElement('div'); imgs.className='slide-images';
  page.images.forEach(img=>{
    const imgEl = document.createElement('img'); imgEl.src = img.file; imgEl.alt = img.file;
    imgs.appendChild(imgEl);
  });
  container.appendChild(imgs);
  // features
  const feat = document.createElement('div'); feat.className='features';
  feat.innerHTML = `<strong>Features</strong><ul>${(page.features||[]).map(f=>`<li>${escapeHtml(f)}</li>`).join('')}</ul>`;
  container.appendChild(feat);
  const txt = document.createElement('div'); txt.className='page-text'; txt.innerText = page.extracted_text || '';
  container.appendChild(txt);
}

function escapeHtml(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function prevPage(){ if(currentPageIndex>0) renderStudyPage(currentPageIndex-1); }
function nextPage(){ if(currentPageIndex<filteredPages.length-1) renderStudyPage(currentPageIndex+1); }

function doSearch(q){ q=q.trim().toLowerCase(); if(!q) { filteredPages = dataset.pages; buildPageSelect(); renderStudyPage(0); return; }
  filteredPages = dataset.pages.filter(p=>{
    const hay = ([p.slideName||'',...p.features||[],p.extracted_text||'']).join('\n').toLowerCase();
    return hay.indexOf(q)!==-1;
  });
  buildPageSelect(); renderStudyPage(0);
}

function buildQuizItems(){
  quizItems = [];
  dataset.pages.forEach((p,pi)=>{
    p.images.forEach(img=>{
      quizItems.push({image:img.file,pageIndex:pi,slideName:p.slideName,features:p.features});
    });
  });
  // shuffle
  quizItems = shuffle(quizItems);
}

function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a}

function startQuiz(){
  quizState={index:0,score:0,answers:[]};
  document.getElementById('quiz-view').classList.remove('hidden');
  document.getElementById('study-view').classList.add('hidden');
  document.getElementById('results-view').classList.add('hidden');
  document.getElementById('q-total').textContent = quizItems.length*2;
  showQuizQuestion();
}

function showQuizQuestion(){
  const qidx = quizState.index;
  const total = quizItems.length*2;
  document.getElementById('q-index').textContent = Math.min(qidx+1,total);
  const progress = ((qidx)/total)*100; document.getElementById('progress').style.width = `${progress}%`;
  const container = document.getElementById('quiz-content'); container.innerHTML='';
  const item = quizItems[Math.floor(qidx/2)];
  const isFirst = (qidx%2===0);
  const img = document.createElement('img'); img.src = item.image; img.style.maxWidth='600px'; img.style.width='100%'; container.appendChild(img);
  if(isFirst){
    const q = document.createElement('h3'); q.textContent = 'What is the name of this slide?'; container.appendChild(q);
    // build options: 1 correct slideName, 3 incorrect slideNames
    const correct = item.slideName || '(no title)';
    const pool = dataset.pages.map(p=>p.slideName||`Page ${p.pageNumber}`).filter(n=>n!==correct);
    const opts = [correct];
    while(opts.length<4 && pool.length){ opts.push(pool.splice(Math.floor(Math.random()*pool.length),1)[0]); }
    while(opts.length<4) opts.push('Unknown');
    renderOptions(container,opts,correct,qidx);
  } else {
    const q = document.createElement('h3'); q.textContent = 'Which of the following is a characteristic feature of this slide?'; container.appendChild(q);
    const correct = (item.features&&item.features[0])||'(no feature)';
    const pool = ([]).concat(...dataset.pages.map(p=>p.features||[])).filter(f=>f!==correct);
    const opts=[correct];
    while(opts.length<4 && pool.length){ opts.push(pool.splice(Math.floor(Math.random()*pool.length),1)[0]); }
    while(opts.length<4) opts.push('N/A');
    renderOptions(container,opts,correct,qidx);
  }
}

function renderOptions(container,opts,correct,qidx){
  const shuffled = shuffle(opts.slice());
  shuffled.forEach(opt=>{
    const b = document.createElement('button'); b.className='option'; b.textContent = opt; b.onclick = ()=>onSelectOption(b,opt,correct,qidx);
    container.appendChild(b);
  });
  document.getElementById('next-question').disabled = true;
}

function onSelectOption(btn,opt,correct,qidx){
  // disable all options
  const opts = document.querySelectorAll('.option');
  opts.forEach(o=>o.disabled=true);
  if(opt===correct){ btn.classList.add('correct'); quizState.score+=1; quizState.answers.push({qidx,ok:true,chosen:opt,correct}); }
  else { btn.classList.add('incorrect'); // mark correct
    quizState.answers.push({qidx,ok:false,chosen:opt,correct});
    opts.forEach(o=>{ if(o.textContent===correct) o.classList.add('correct'); });
  }
  document.getElementById('score').textContent = quizState.score;
  document.getElementById('next-question').disabled = false;
}

function nextQuestion(){
  quizState.index+=1;
  const total = quizItems.length*2;
  if(quizState.index>=total){ showResults(); return; }
  showQuizQuestion();
}

function showResults(){
  document.getElementById('quiz-view').classList.add('hidden');
  document.getElementById('results-view').classList.remove('hidden');
  const total = quizItems.length*2;
  const correct = quizState.score;
  const percent = Math.round((correct/total)*100);
  document.getElementById('results-summary').innerHTML = `<p>Total Questions: ${total}</p><p>Correct: ${correct}</p><p>Percentage: ${percent}%</p>`;
  // review incorrect
  const review = document.getElementById('review-list'); review.innerHTML='';
  quizState.answers.filter(a=>!a.ok).forEach(a=>{
    const itemIndex = Math.floor(a.qidx/2);
    const item = quizItems[itemIndex];
    const card = document.createElement('div'); card.className='review-card';
    card.innerHTML = `<img src="${item.image}" style="max-width:240px;display:block"><p>Your answer: ${a.chosen}</p><p>Correct answer: ${a.correct}</p>`;
    review.appendChild(card);
  });
  // store best score
  const best = parseInt(localStorage.getItem('bestScore')||'0',10);
  if(correct>best){ localStorage.setItem('bestScore',correct); }
  updateStats();
}

function updateStats(){
  const totalSlides = dataset.pages.length;
  const totalImages = dataset.pages.reduce((s,p)=>s+(p.images||[]).length,0);
  const stats = document.getElementById('stats-list');
  const best = localStorage.getItem('bestScore')||0;
  stats.innerHTML = `<p>Total Slides: ${totalSlides}</p><p>Total Images: ${totalImages}</p><p>Best Score: ${best}</p>`;
}

// UI wiring
window.addEventListener('load',()=>{
  document.getElementById('btn-study').onclick = ()=>{ document.getElementById('study-view').classList.remove('hidden'); document.getElementById('quiz-view').classList.add('hidden'); document.getElementById('results-view').classList.add('hidden'); document.getElementById('stats-view').classList.add('hidden'); };
  document.getElementById('btn-quiz').onclick = ()=>{ startQuiz(); };
  document.getElementById('btn-stats').onclick = ()=>{ document.getElementById('stats-view').classList.remove('hidden'); document.getElementById('study-view').classList.add('hidden'); document.getElementById('quiz-view').classList.add('hidden'); document.getElementById('results-view').classList.add('hidden'); };
  document.getElementById('prev-page').onclick = prevPage; document.getElementById('next-page').onclick = nextPage;
  document.getElementById('search').addEventListener('input',e=>doSearch(e.target.value));
  document.getElementById('next-question').onclick = nextQuestion;
  document.getElementById('restart-quiz').onclick = ()=>{ buildQuizItems(); startQuiz(); };
  loadDataset().catch(e=>{ console.error(e); alert('Failed to load dataset.json. Please run the build script to generate /data/dataset.json and extracted images.'); });
});
