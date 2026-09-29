// Shared behaviour for index.html (EN) and he.html (HE). Page text lives in window.SITE.
const S = window.SITE;

// ——— SET THESE ———
// WHATSAPP: number in international format without + or spaces.
// GROW_LINK: the Grow payment page. Empty = no pay button yet, orders go to WhatsApp only.
const WHATSAPP = '972509948169';
const GROW_LINK = '';
const PRICE = 100;

const wa = (text) => `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(text)}`;
document.querySelectorAll('[data-wa]').forEach((a) => { a.href = wa(S.waHello); a.target = '_blank'; a.rel = 'noopener'; });

// Rotating struck-out small-talk line in the hero
const rotEl = document.getElementById('rot');
let ri = 0;
setInterval(() => {
  rotEl.classList.add('out');
  setTimeout(() => { ri = (ri + 1) % S.rot.length; rotEl.textContent = S.rot[ri]; rotEl.classList.remove('out'); }, 350);
}, 2400);

// WhatsApp phone: boring messages pop in on a loop
const waBody = document.getElementById('wa'), waStatus = document.getElementById('waStatus');
const clock = () => new Date().toTimeString().slice(0, 5);
let wi = 0;
function waStep() {
  if (wi >= S.chat.length) { setTimeout(() => { waBody.innerHTML = ''; wi = 0; waStep(); }, 2600); return; }
  const m = S.chat[wi++];
  const typing = document.createElement('div');
  typing.className = 'wa-typing'; typing.innerHTML = '<i></i><i></i><i></i>';
  if (!m.me) { waBody.appendChild(typing); waStatus.style.visibility = 'visible'; }
  setTimeout(() => {
    typing.remove(); waStatus.style.visibility = 'hidden';
    const b = document.createElement('div');
    b.className = 'wa-msg' + (m.me ? ' me' : '');
    b.textContent = m.t;
    const t = document.createElement('time'); t.textContent = clock(); b.appendChild(t);
    waBody.appendChild(b);
    while (waBody.children.length > 9) waBody.firstChild.remove();
    setTimeout(waStep, 700);
  }, m.me ? 500 : 900);
}
waStep();

// Free-taste cards: hover flips on desktop (CSS), tap flips on touch
document.querySelectorAll('.fc').forEach((c) => c.addEventListener('click', () => c.classList.toggle('flip')));

// Drag-to-spin 3D objects (box, rules card). They idle-rotate until grabbed.
function spinnable(stage, obj, tiltX, start) {
  let ry = start, rx = tiltX, vy = 0.3, drag = false, lx = 0, ly = 0;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  stage.addEventListener('pointerdown', (e) => { e.preventDefault(); drag = true; lx = e.clientX; ly = e.clientY; vy = 0; stage.setPointerCapture(e.pointerId); });
  stage.addEventListener('pointermove', (e) => {
    if (!drag) return;
    vy = (e.clientX - lx) * 0.5; ry += vy; rx -= (e.clientY - ly) * 0.5;
    lx = e.clientX; ly = e.clientY;
  });
  const up = () => { drag = false; if (Math.abs(vy) < 0.2) vy = 0.3; };
  stage.addEventListener('pointerup', up); stage.addEventListener('pointercancel', up);
  (function tick() {
    if (!drag && !reduce) { ry += vy; vy += (0.3 - vy) * 0.03; }
    obj.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg)`;
    requestAnimationFrame(tick);
  })();
}
spinnable(document.getElementById('boxStage'), document.getElementById('box3d'), -10, -30);
spinnable(document.getElementById('rulesStage'), document.getElementById('rules3d'), 6, 150);

// Order: details first (name, email, phone), then WhatsApp me, then pay.
const modal = document.getElementById('order'), form = document.getElementById('orderForm'),
  qtyEl = document.getElementById('qty'), totalEl = document.getElementById('total'), err = document.getElementById('err'),
  done = document.getElementById('done'), payBtn = document.getElementById('payBtn');
let qty = 1;
const openOrder = () => { modal.classList.add('open'); form.hidden = false; done.hidden = true; setTimeout(() => form.name.focus(), 50); };
const closeOrder = () => modal.classList.remove('open');
document.querySelectorAll('.buy').forEach((b) => b.addEventListener('click', (e) => { e.preventDefault(); openOrder(); }));
modal.addEventListener('click', (e) => { if (e.target === modal || e.target.closest('.x')) closeOrder(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeOrder(); });
function refresh() {
  qtyEl.textContent = qty;
  totalEl.textContent = '₪' + qty * PRICE + (form.ship.value === 'pickup' ? '' : S.plusShipping);
}
document.getElementById('qminus').onclick = () => { qty = Math.max(1, qty - 1); refresh(); };
document.getElementById('qplus').onclick = () => { qty = Math.min(20, qty + 1); refresh(); };
form.addEventListener('change', refresh);
refresh();
form.addEventListener('submit', (e) => {
  e.preventDefault();
  const v = (n) => form[n].value.trim();
  const bad = ['name', 'phone'].filter((n) => !v(n));
  if (v('email') && !/^\S+@\S+\.\S+$/.test(v('email'))) bad.push('email');
  form.querySelectorAll('input').forEach((i) => i.classList.toggle('bad', bad.includes(i.name)));
  if (bad.length) { err.textContent = S.fillIn; return; }
  err.textContent = '';
  const msg = S.orderText({ qty, total: qty * PRICE, name: v('name'), email: v('email'), phone: v('phone'), pickup: form.ship.value === 'pickup' });
  window.open(wa(msg), '_blank', 'noopener');
  form.hidden = true; done.hidden = false;
  if (GROW_LINK) { payBtn.href = GROW_LINK; payBtn.hidden = false; } else payBtn.hidden = true;
});

// Scroll reveal
const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach((el) => io.observe(el));
