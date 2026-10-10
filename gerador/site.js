// Curtidas: o número = curtidas que o post já tinha no Substack (data-base) + curtidas dadas aqui no site.
// As do site ficam num contador gratuito (abacus.jasoncameron.dev); cada navegador curte uma vez (guardado no próprio navegador).
var Curtidas = (function () {
  var API = "https://abacus.jasoncameron.dev", NS = "marcoscacau-site";
  var site = {}, carregado = {};
  function ja(slug) { try { return localStorage.getItem("curtiu:" + slug) === "1"; } catch (e) { return false; } }
  function marcar(slug) { try { localStorage.setItem("curtiu:" + slug, "1"); } catch (e) {} }
  function botoes(slug) { return Array.prototype.slice.call(document.querySelectorAll('.curtir[data-slug="' + slug + '"]')); }
  function pintar(slug) {
    botoes(slug).forEach(function (b) {
      var n = (+b.dataset.base || 0) + (site[slug] || 0), feito = ja(slug);
      b.querySelector(".n").textContent = n;
      b.setAttribute("aria-pressed", feito ? "true" : "false");
      b.querySelector(".rotulo").textContent = feito ? "Curtido" : "Curtir";
      b.setAttribute("aria-label", (feito ? "Você curtiu este texto. " : "Curtir este texto. ") + n + " curtida" + (n === 1 ? "" : "s"));
    });
  }
  function carregar(slug) {
    pintar(slug);
    if (carregado[slug]) return;
    carregado[slug] = true;
    fetch(API + "/get/" + NS + "/" + slug).then(function (r) { return r.ok ? r.json() : { value: 0 }; })
      .then(function (d) { site[slug] = Math.max(site[slug] || 0, d.value || 0); pintar(slug); })
      .catch(function () { pintar(slug); });
  }
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest(".curtir");
    if (!b) return;
    var slug = b.dataset.slug;
    if (ja(slug)) return;
    marcar(slug);
    site[slug] = (site[slug] || 0) + 1;
    pintar(slug);
    botoes(slug).forEach(function (x) { x.classList.remove("pulsa"); void x.offsetWidth; x.classList.add("pulsa"); });
    fetch(API + "/hit/" + NS + "/" + slug).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d && typeof d.value === "number") { site[slug] = d.value; pintar(slug); } })
      .catch(function () {});
  });
  return { carregar: carregar };
})();

// Frase-manifesto: a palavra em negrito troca a cada 2,6 s (parada para quem prefere menos movimento).
(function () {
  var b = document.querySelector(".manifesto .giro");
  if (!b || (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
  var palavras = b.dataset.palavras.split("|"), i = 0;
  setInterval(function () {
    b.classList.add("troca");
    setTimeout(function () { i = (i + 1) % palavras.length; b.textContent = palavras[i]; b.classList.remove("troca"); }, 350);
  }, 2600);
})();

// Navegação por endereço (#texto, #tema-fisica, #sobre) e carrossel de destaques.
(function () {
  var base = document.title;
  var vistas = Array.prototype.slice.call(document.querySelectorAll(".vista"));
  var links = Array.prototype.slice.call(document.querySelectorAll(".menu a"));
  function mostrar() {
    var id = (location.hash || "").slice(1);
    var alvo = document.getElementById("v-" + id);
    if (!alvo || !alvo.classList.contains("vista")) { alvo = document.getElementById("v-inicio"); id = "inicio"; }
    vistas.forEach(function (v) { v.hidden = v !== alvo; });
    links.forEach(function (a) { a.classList.toggle("atual", a.getAttribute("href") === "#" + id); });
    var h = alvo.querySelector(".titulo-post, .etiqueta.grande span");
    document.title = id === "inicio" || !h ? base : h.textContent + " · Cacau";
    var vistos = {};
    Array.prototype.forEach.call(alvo.querySelectorAll(".curtir"), function (c) {
      if (!vistos[c.dataset.slug]) { vistos[c.dataset.slug] = true; Curtidas.carregar(c.dataset.slug); }
    });
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", mostrar);
  mostrar();

  // notas: carrossel de fotos e legenda longa dobrada
  Array.prototype.forEach.call(document.querySelectorAll(".fotos"), function (f) {
    var trilho = f.querySelector(".fotos-trilho"), cont = f.querySelector(".fotos-cont");
    var ant = f.querySelector(".fotos-seta.ant"), prox = f.querySelector(".fotos-seta.prox");
    var total = +f.dataset.total;
    function atualiza() {
      var i = Math.round(trilho.scrollLeft / (trilho.clientWidth || 1));
      cont.textContent = (i + 1) + "/" + total;
      ant.disabled = i <= 0; prox.disabled = i >= total - 1;
    }
    trilho.addEventListener("scroll", atualiza, { passive: true });
    ant.addEventListener("click", function () { trilho.scrollBy({ left: -trilho.clientWidth, behavior: "smooth" }); });
    prox.addEventListener("click", function () { trilho.scrollBy({ left: trilho.clientWidth, behavior: "smooth" }); });
    atualiza();
  });
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest && ev.target.closest(".continuar");
    if (!b) return;
    var t = b.previousElementSibling, aberta = t.classList.toggle("aberta");
    b.textContent = aberta ? "Mostrar menos" : "Continuar lendo";
    b.setAttribute("aria-expanded", aberta ? "true" : "false");
  });

  var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
  var pontos = Array.prototype.slice.call(document.querySelectorAll(".ponto"));
  if (!slides.length) return;
  var atual = 0, timer = null;
  var calmo = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function ir(i) {
    atual = (i + slides.length) % slides.length;
    slides.forEach(function (s, k) {
      var on = k === atual;
      s.classList.toggle("ativo", on);
      if (on) { s.removeAttribute("aria-hidden"); s.removeAttribute("tabindex"); }
      else { s.setAttribute("aria-hidden", "true"); s.setAttribute("tabindex", "-1"); }
    });
    pontos.forEach(function (p, k) { p.classList.toggle("ativo", k === atual); });
  }
  // com "reduzir animações" ligado, continua passando, mais devagar e sem fade (o CSS tira a transição)
  function auto() { clearInterval(timer); timer = setInterval(function () { ir(atual + 1); }, calmo ? 8000 : 6000); }
  pontos.forEach(function (p) { p.addEventListener("click", function () { ir(+p.dataset.i); auto(); }); });
  var ant = document.querySelector(".seta-c.ant"), prox = document.querySelector(".seta-c.prox");
  if (ant) ant.addEventListener("click", function () { ir(atual - 1); auto(); });
  if (prox) prox.addEventListener("click", function () { ir(atual + 1); auto(); });
  var c = document.querySelector(".carrossel");
  c.addEventListener("mouseenter", function () { clearInterval(timer); });
  c.addEventListener("mouseleave", auto);
  var x0 = null;                                     // deslizar com o dedo no celular
  c.addEventListener("touchstart", function (ev) { x0 = ev.touches[0].clientX; }, { passive: true });
  c.addEventListener("touchend", function (ev) {
    if (x0 === null) return;
    var dx = ev.changedTouches[0].clientX - x0; x0 = null;
    if (Math.abs(dx) > 40) { ev.preventDefault(); ir(atual + (dx < 0 ? 1 : -1)); auto(); }
  });
  auto();
})();
