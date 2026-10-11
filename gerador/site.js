// Curtidas: o botão não mostra número (escolha do autor); as curtidas continuam contadas por trás,
// num contador gratuito (abacus.jasoncameron.dev). Cada navegador curte uma vez (guardado no próprio navegador).
var Curtidas = (function () {
  var API = "https://abacus.jasoncameron.dev", NS = "marcoscacau-site";
  var site = {}, carregado = {};
  function ja(slug) { try { return localStorage.getItem("curtiu:" + slug) === "1"; } catch (e) { return false; } }
  function marcar(slug) { try { localStorage.setItem("curtiu:" + slug, "1"); } catch (e) {} }
  function botoes(slug) { return Array.prototype.slice.call(document.querySelectorAll('.curtir[data-slug="' + slug + '"]')); }
  function pintar(slug) {
    botoes(slug).forEach(function (b) {
      var feito = ja(slug);
      b.setAttribute("aria-pressed", feito ? "true" : "false");
      b.querySelector(".rotulo").textContent = feito ? "Curtido" : "Curtir";
      b.setAttribute("aria-label", feito ? "Você curtiu este texto" : "Curtir este texto");
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

// Compartilhar: no celular usa a janela de compartilhar do aparelho; no computador abre as redes e o "copiar link".
(function () {
  var nativo = !!navigator.share && window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
  function antigo(url) {
    var t = document.createElement("textarea"), deu = false;
    t.value = url; t.setAttribute("readonly", ""); t.style.position = "fixed"; t.style.opacity = "0";
    document.body.appendChild(t); t.select();
    try { deu = document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(t);
    return deu;
  }
  function copiar(url, pronto) {
    if (navigator.clipboard && window.isSecureContext)
      navigator.clipboard.writeText(url).then(function () { pronto(true); }, function () { pronto(antigo(url)); });
    else pronto(antigo(url));
  }
  function partilhar(url, titulo, senao) {
    if (nativo) { navigator.share({ title: titulo, url: url }).catch(function () {}); return; }
    senao();
  }
  document.addEventListener("click", function (ev) {
    var alvo = ev.target.closest ? ev.target : null;
    if (!alvo) return;
    var b = alvo.closest(".cp-botao"), c = alvo.closest(".cp-copiar"), m = alvo.closest(".cp-mini");
    if (b) {
      var cp = b.closest(".cp");
      partilhar(cp.dataset.url, cp.dataset.titulo, function () { cp.classList.toggle("aberto"); });
    } else if (c) {
      var cp2 = c.closest(".cp"), aviso = cp2.querySelector(".cp-aviso");
      copiar(cp2.dataset.url, function (ok) { aviso.textContent = ok ? "Link copiado!" : "Não deu para copiar"; setTimeout(function () { aviso.textContent = ""; }, 2200); });
    } else if (m) {
      partilhar(m.dataset.url, m.dataset.titulo, function () {
        copiar(m.dataset.url, function (ok) {
          m.classList.add("ok"); m.setAttribute("aria-label", ok ? "Link copiado" : "Não deu para copiar"); m.title = ok ? "Link copiado!" : "Não deu para copiar";
          setTimeout(function () { m.classList.remove("ok"); m.setAttribute("aria-label", "Compartilhar"); m.title = ""; }, 2200);
        });
      });
    } else if (!alvo.closest(".cp")) {
      Array.prototype.forEach.call(document.querySelectorAll(".cp.aberto"), function (x) { x.classList.remove("aberto"); });
    }
  });
})();

// Visitas: soma 1 no contador da página (o mesmo serviço das curtidas). Não guarda nada de quem visita.
// Fica de fora: robôs, a versão de teste no computador e quem marcou "não contar" no /painel/.
var Visitas = (function () {
  var API = "https://abacus.jasoncameron.dev", NS = "marcoscacau-site";
  function contar() {
    var chave = document.body.dataset.conta;
    if (!chave || navigator.webdriver || /bot|crawl|spider|headless|preview/i.test(navigator.userAgent)) return;
    if (location.protocol !== "https:") return;        // a cópia de teste (http://localhost) não conta
    try { if (localStorage.getItem("nao-contar") === "1") return; } catch (e) {}
    fetch(API + "/hit/" + NS + "/" + chave, { keepalive: true }).catch(function () {});
  }
  function ler(chave) {
    return fetch(API + "/get/" + NS + "/" + chave).then(function (r) { return r.ok ? r.json() : { value: 0 }; })
      .then(function (d) { return d.value || 0; }, function () { return null; });
  }
  return { contar: contar, ler: ler };
})();
Visitas.contar();

// Busca: o índice (/busca.json) só é baixado quando alguém abre a busca. Ignora acentos e maiúsculas.
(function () {
  var botao = document.querySelector(".topo-busca"), caixa = document.querySelector("dialog.busca");
  if (!botao || !caixa || !caixa.showModal) return;
  botao.hidden = false;
  var campo = caixa.querySelector(".busca-campo"), lista = caixa.querySelector(".busca-lista"), info = caixa.querySelector(".busca-info");
  var indice = null, pedido = null;
  function limpa(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function carregar() {
    pedido = pedido || fetch("/busca.json").then(function (r) { return r.json(); }).then(function (d) {
      d.forEach(function (x) { x.tl = limpa(x.t); x.xl = limpa(x.x); }); indice = d; return d;
    });
    return pedido;
  }
  function trecho(x, termos) {
    // o trecho em volta da palavra, tirado do texto original (com acentos); sem acento o tamanho é o mesmo
    var i = x.xl.indexOf(termos[0]);
    if (i < 0 || x.k === "Nota" || x.xl.length !== x.x.length || x.tl.indexOf(termos[0]) >= 0) return x.l || x.x.slice(0, 140) + "…";
    var a = Math.max(0, x.x.lastIndexOf(" ", Math.max(0, i - 60)) + 1);
    return (a > 0 ? "…" : "") + x.x.slice(a, a + 150).trim() + "…";
  }
  function buscar() {
    var q = limpa(campo.value).trim(), termos = q.split(/\s+/).filter(function (t) { return t.length > 1; });
    lista.innerHTML = "";
    if (!termos.length) { info.textContent = indice ? indice.length + " textos, livros e notas para buscar" : ""; return; }
    var achados = [];
    indice.forEach(function (x) {
      var pontos = 0;
      for (var k = 0; k < termos.length; k++) {
        var t = termos[k], p = 0;
        if (x.tl.indexOf(t) >= 0) p += x.k === "Nota" ? 1 : 10;   // o "título" da nota é o próprio começo dela
        if (x.b.indexOf(t) >= 0) p += 5;
        if (x.xl.indexOf(t) >= 0) p += 1 + Math.min(4, x.xl.split(t).length - 2);
        if (!p) return;                                  // todas as palavras precisam aparecer
        pontos += p;
      }
      achados.push({ x: x, p: pontos + (x.k === "Texto" ? 3 : 0) });
    });
    achados.sort(function (a, b) { return b.p - a.p; });
    info.textContent = achados.length ? achados.length + (achados.length === 1 ? " resultado" : " resultados") : "Nada encontrado para “" + campo.value.trim() + "”.";
    lista.innerHTML = achados.slice(0, 30).map(function (a) {
      var x = a.x;
      return '<li><a href="' + esc(x.u) + '"><span class="kicker">' + esc(x.k) + "</span><b>" + esc(x.t) + "</b>" +
        (x.l || x.x ? "<small>" + esc(trecho(x, termos) || "") + "</small>" : "") + "</a></li>";
    }).join("");
  }
  function abrir(q) {
    caixa.showModal();
    if (q) campo.value = q;
    campo.focus();
    carregar().then(buscar, function () { info.textContent = "Não deu para carregar a busca. Tente de novo."; pedido = null; });
  }
  botao.addEventListener("click", function () { abrir(); });
  campo.addEventListener("input", function () { if (indice) buscar(); });
  caixa.addEventListener("click", function (ev) { if (ev.target === caixa) caixa.close(); });   // clique fora fecha
  caixa.querySelector(".busca-cab").addEventListener("submit", function (ev) {
    var primeiro = lista.querySelector("a");
    if (ev.submitter && ev.submitter.value === "fechar") return;
    ev.preventDefault();
    if (primeiro) location.href = primeiro.href;
  });
  document.addEventListener("keydown", function (ev) {
    var t = ev.target.tagName;
    if (ev.key === "/" && !caixa.open && t !== "INPUT" && t !== "TEXTAREA" && !ev.target.isContentEditable) { ev.preventDefault(); abrir(); }
  });
  var pedida = new URLSearchParams(location.search).get("busca");          // /?busca=termo (o Google usa)
  if (pedida) abrir(pedida);
})();

// Painel (/painel/): visitas e curtidas de cada página, lidas do contador.
(function () {
  var dados = document.getElementById("painel-dados");
  if (!dados) return;
  var linhas = JSON.parse(dados.textContent), corpo = document.querySelector(".painel-tabela tbody");
  var marca = document.querySelector(".painel-nao-contar");
  try { marca.checked = localStorage.getItem("nao-contar") === "1"; } catch (e) {}
  marca.addEventListener("change", function () { try { localStorage.setItem("nao-contar", marca.checked ? "1" : "0"); } catch (e) {} });
  var filtro = "Tudo";
  function n(v) { return v === null ? "—" : v === undefined ? "" : v.toLocaleString("pt-BR"); }
  function desenhar() {
    var mostrar = linhas.filter(function (l) { return filtro === "Tudo" || l.k === filtro; });
    mostrar.sort(function (a, b) { return ((b.vis || 0) - (a.vis || 0)) || ((b.cur || 0) - (a.cur || 0)); });
    corpo.innerHTML = mostrar.map(function (l) {
      var t = l.t.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
      return '<tr><td><a href="' + l.u + '">' + t + "</a></td><td>" + l.k + '</td><td class="n">' + (l.v ? n(l.vis) : "") +
        '</td><td class="n">' + (l.c ? n(l.cur) : "") + "</td></tr>";
    }).join("");
    var soma = function (campo) { return linhas.reduce(function (s, l) { return s + (l[campo] || 0); }, 0); };
    document.querySelector('.painel-total[data-o="visitas"]').textContent = soma("vis").toLocaleString("pt-BR");
    document.querySelector('.painel-total[data-o="curtidas"]').textContent = soma("cur").toLocaleString("pt-BR");
  }
  Array.prototype.forEach.call(document.querySelectorAll(".painel-filtros button"), function (b) {
    b.addEventListener("click", function () {
      filtro = b.dataset.k;
      Array.prototype.forEach.call(b.parentNode.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      desenhar();
    });
  });
  // O contador gratuito aceita só 30 leituras a cada 10 s, e aqui são umas 400. Por isso:
  // 1) mostra na hora a foto que o site tira com calma ao ser montado (/contadores.json, várias vezes por dia);
  // 2) confere ao vivo, uma leitura por vez; quando o contador pede calma, espera e tenta de novo.
  // Um número nunca desce: vale o maior entre a foto, a leitura ao vivo e o último visto neste aparelho.
  var status = document.querySelector(".painel-status"), guardados = {};
  try { guardados = JSON.parse(localStorage.getItem("painel-valores") || "{}"); } catch (e) {}
  function guardar() { try { localStorage.setItem("painel-valores", JSON.stringify(guardados)); } catch (e) {} }
  function aplicar(chave, v) {
    if (typeof v !== "number") return;
    guardados[chave] = Math.max(guardados[chave] || 0, v);
    linhas.forEach(function (l) {
      if (l.v === chave) l.vis = guardados[chave];
      if (l.c === chave) l.cur = guardados[chave];
    });
  }
  var chaves = [];
  linhas.forEach(function (l) { if (l.v) chaves.push(l.v); if (l.c) chaves.push(l.c); });
  Object.keys(guardados).forEach(function (k) { aplicar(k, guardados[k]); });
  function lerAoVivo(chave) {
    return fetch("https://abacus.jasoncameron.dev/get/marcoscacau-site/" + chave).then(function (r) {
      if (r.status === 404) return 0;
      if (r.status === 429) return "calma";
      return r.ok ? r.json().then(function (d) { return d.value || 0; }) : null;
    }, function () { return null; });
  }
  var i = 0;
  function proximo() {
    if (i >= chaves.length) {
      guardar(); desenhar();
      status.textContent = "Números conferidos agora há pouco.";
      return;
    }
    lerAoVivo(chaves[i]).then(function (v) {
      if (v === "calma") {
        status.textContent = "Conferindo ao vivo: " + i + " de " + chaves.length + " (o contador pediu uma pausa)…";
        setTimeout(proximo, 11000);
        return;
      }
      aplicar(chaves[i], v);
      i++;
      if (i % 15 === 0) { guardar(); desenhar(); status.textContent = "Conferindo ao vivo: " + i + " de " + chaves.length + "…"; }
      setTimeout(proximo, 150);
    });
  }
  fetch("/contadores.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (foto) {
    if (foto && foto.valores) Object.keys(foto.valores).forEach(function (k) { aplicar(k, foto.valores[k]); });
  }, function () {}).then(function () {
    desenhar();
    status.textContent = "Conferindo ao vivo…";
    proximo();
  });
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

// Cada endereço é uma página própria (/textos/vida/, /tema/fisica/…). Aqui: item do menu atual,
// estado dos botões de curtir, carrosséis e "continuar lendo".
(function () {
  var aqui = location.pathname.replace(/index\.html$/, "");
  Array.prototype.forEach.call(document.querySelectorAll(".menu a"), function (a) {
    var alvo = a.getAttribute("href");
    a.classList.toggle("atual", alvo === aqui || (alvo !== "/" && aqui.indexOf(alvo) === 0));
  });
  var vistos = {};
  Array.prototype.forEach.call(document.querySelectorAll(".curtir"), function (c) {
    if (!vistos[c.dataset.slug]) { vistos[c.dataset.slug] = true; Curtidas.carregar(c.dataset.slug); }
  });

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
  // as capas dos slides escondidos só são baixadas pouco antes de aparecer (o próximo fica sempre pronto)
  function revela(k) {
    var im = slides[(k + slides.length) % slides.length].querySelector("img[data-src]");
    if (!im) return;
    if (im.dataset.srcset) im.srcset = im.dataset.srcset;
    im.src = im.dataset.src;
    im.removeAttribute("data-src"); im.removeAttribute("data-srcset");
  }
  if (document.readyState === "complete") revela(1);
  else window.addEventListener("load", function () { revela(1); });
  function ir(i) {
    atual = (i + slides.length) % slides.length;
    revela(atual); revela(atual + 1);
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
