"""Site do Cacau: base Gates Notes (carrossel no topo, frase-manifesto, grade de cartões, rodapé grande)
com toques do Super Literário (página inicial por categoria, etiquetas de seção).
Cada texto aparece uma vez só na página inicial (no tema principal); a página do texto não tem coluna lateral.
Tudo vem da pasta conteudo/ (ver conteudo.py). Biblioteca e Notas só aparecem quando têm o mínimo.

uso: python gerador/site.py [pasta de saída]     (padrão: _site)
O GitHub roda isto sozinho a cada alteração (.github/workflows/site.yml).
"""
import os, re, sys, html, json, hashlib, datetime, unicodedata, urllib.parse
import conteudo, indexnow

S = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(conteudo.RAIZ, "_site"))
os.makedirs(SITE, exist_ok=True)
img = conteudo.Imagens(SITE)
CFG = conteudo.config()
FOTO = img(CFG.get("foto"))


def icones(foto):
    """Ícone da aba do navegador (e do atalho no celular): a foto do perfil, recortada em círculo."""
    from PIL import Image, ImageDraw
    if not foto:
        return ""
    im = Image.open(os.path.join(SITE, "img", foto)).convert("RGBA")
    lado = min(im.size)
    im = im.crop(((im.width - lado) // 2, (im.height - lado) // 2, (im.width + lado) // 2, (im.height + lado) // 2))
    for nome, tam, redondo in (("favicon.png", 64, True), ("apple-touch-icon.png", 180, False)):
        c = im.resize((tam, tam), Image.LANCZOS)
        if redondo:
            mascara = Image.new("L", (tam * 4, tam * 4), 0)
            ImageDraw.Draw(mascara).ellipse((0, 0, tam * 4 - 1, tam * 4 - 1), fill=255)
            c.putalpha(mascara.resize((tam, tam), Image.LANCZOS))
        c.save(os.path.join(SITE, nome))
    return '<link rel="icon" type="image/png" href="favicon.png">\n<link rel="apple-touch-icon" href="apple-touch-icon.png">'


ICONES = icones(FOTO)
BIO = str(CFG.get("bio") or "")
HOJE = datetime.date.today().isoformat()

SUBSTACK = CFG.get("substack") or "https://marcoscacau.substack.com"
INSTAGRAM = CFG.get("instagram") or "https://www.instagram.com/marcos_cacau/"
X_URL = CFG.get("x") or "https://x.com/leitordamanha"
arroba = lambda u: "@" + u.rstrip("/").split("/")[-1].lstrip("@")
IC = {
    "instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17.3" cy="6.7" r="1.2" fill="currentColor"/></svg>',
    "x": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4l16 16M20 4L4 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    "substack": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h14v2.4H5zM5 8.6h14V11H5zM5 13.2h14V21l-7-3.9L5 21z" fill="currentColor"/></svg>',
}
REDES = [("instagram", "Instagram", arroba(INSTAGRAM), INSTAGRAM), ("x", "X", arroba(X_URL), X_URL),
         ("substack", "Substack", SUBSTACK.split("//")[-1].split(".")[0], SUBSTACK)]
ENDERECO = str(CFG.get("endereco") or "https://marcoscacau.github.io").rstrip("/")


def rota(i):
    """Endereço de cada página do site."""
    if i == "inicio":
        return "/"
    if i.startswith("tema-"):
        return f"/tema/{i[5:]}/"
    if i in ("notas", "biblioteca", "sobre", "links", "painel"):
        return f"/{i}/"
    if i.startswith("livro-"):
        return f"/biblioteca/{i[6:]}/"
    if i.startswith("nota-"):
        return f"/notas/#{i}"
    return f"/textos/{i}/"


# ---------- compartilhar ----------
ICS = {
    "whatsapp": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M8.8 8.2c.2-.4.4-.4.7-.4h.5c.2 0 .4 0 .5.4l.7 1.7c.1.2 0 .4-.1.6l-.5.6c-.1.1-.2.3 0 .5.4.7 1 1.4 1.7 1.9.5.3.9.5 1.1.6.2.1.4 0 .5-.1l.6-.7c.2-.2.4-.2.6-.1l1.6.8c.2.1.4.2.4.4 0 .5-.2 1.2-.7 1.5-.5.4-1.4.6-2.5.2a10 10 0 0 1-5.5-5.1c-.5-1.1-.2-2 .2-2.6z" fill="currentColor"/></svg>',
    "x": IC["x"],
    "facebook": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.5 8H16V5h-2a4 4 0 0 0-4 4v2H8v3h2v7h3v-7h2.3l.7-3h-3V9.2c0-.7.4-1.2 1.5-1.2z" fill="currentColor"/></svg>',
    "telegram": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 4 3 11l6 2 2 6 3-4 5 4z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="m9 13 8-6" stroke="currentColor" stroke-width="1.7"/></svg>',
    "link": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "partilha": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V3m0 0L7.5 7.5M12 3l4.5 4.5M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "lupa": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m15.5 15.5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
}
BUSCA = '''<dialog class="busca" aria-label="Buscar no site">
  <form class="busca-cab" method="dialog" role="search">
    <input class="busca-campo" type="search" placeholder="Buscar textos, livros e notas…" aria-label="O que você procura?" autocomplete="off" enterkeyhint="search">
    <button class="busca-fechar" value="fechar" aria-label="Fechar a busca">Esc</button>
  </form>
  <p class="busca-info" role="status" aria-live="polite"></p>
  <ol class="busca-lista"></ol>
</dialog>'''


def compartilhar(i, titulo, rotulo="Compartilhar", pequeno=False):
    """Botão de compartilhar: no celular abre a janela do aparelho; no computador mostra as redes e "copiar link"."""
    url = ENDERECO + rota(i)
    q = lambda s: urllib.parse.quote(s, safe="")
    texto = f"{titulo} — Cacau"
    redes = [("whatsapp", "WhatsApp", f"https://wa.me/?text={q(texto + ' ' + url)}"),
             ("x", "X", f"https://x.com/intent/post?text={q(texto)}&url={q(url)}"),
             ("facebook", "Facebook", f"https://www.facebook.com/sharer/sharer.php?u={q(url)}"),
             ("telegram", "Telegram", f"https://t.me/share/url?url={q(url)}&text={q(texto)}")]
    itens = "".join(f'<a class="cp-rede" href="{e(u)}" target="_blank" rel="noopener" aria-label="Compartilhar no {n}">{ICS[k]}</a>' for k, n, u in redes)
    if pequeno:
        return (f'<button class="cp-mini" type="button" data-url="{e(url)}" data-titulo="{e(texto)}" aria-label="Compartilhar">'
                f'{ICS["partilha"]}</button>')
    return f'''<div class="cp" data-url="{e(url)}" data-titulo="{e(texto)}">
  <button class="cp-botao" type="button">{ICS["partilha"]}<span>{e(rotulo)}</span></button>
  <div class="cp-redes">{itens}<button class="cp-rede cp-copiar" type="button" aria-label="Copiar o link">{ICS["link"]}</button></div>
  <span class="cp-aviso" role="status" aria-live="polite"></span>
</div>'''

# Os temas de cada texto ficam no próprio texto (campo "temas"; o primeiro é o principal).
ORDEM_TEMAS = ["Física", "Teologia", "Literatura", "Filosofia", "Sociedade"]
COMECE = [str(s).strip() for s in conteudo.lista(CFG.get("comece"))]
GIRO = [str(s) for s in conteudo.lista(CFG.get("frase_palavras"))] or ["física", "teologia", "literatura", "filosofia", "sociedade"]
N_DESTAQUES = int(CFG.get("destaques") or 5)                       # quantos textos passam no carrossel do topo

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
def data_ext(d):
    a, m, dd = d.split("-")
    return f"{int(dd)} de {MESES[int(m) - 1]} de {a}"
e = lambda s: html.escape(s, quote=True)
slugt = lambda t: "tema-" + re.sub(r"[^a-z]", "", t.lower().replace("í", "i").replace("ç", "c").replace("ã", "a"))
minutos = lambda w: max(1, round(w / 200))


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def corta(s, n):
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"

posts = conteudo.textos(img)
for p in posts:
    p["temas"] = p["temas"] or ["Textos"]
porslug = {p["slug"]: p for p in posts}
recentes = sorted(posts, key=lambda p: p["data"], reverse=True)

LIVROS = conteudo.livros(img)
NOTAS = conteudo.notas(img)
TEM_LIVROS = len(LIVROS) >= conteudo.MIN_LIVROS
TEM_NOTAS = len(NOTAS) >= conteudo.MIN_NOTAS


def linha(p, n=120):
    s = p["sub"] or p["resumo"]
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def kicker(p, data=True):
    return f'<span class="kicker">{e(p["temas"][0])}{" · " + data_ext(p["data"]) if data else ""}</span>'


def tags(p):
    return '<div class="tags">' + "".join(
        f'<a class="tag" href="#{slugt(t)}">{e(t)}</a>' if t in ORDEM_TEMAS else f'<span class="tag">{e(t)}</span>' for t in p["temas"]) + "</div>"


chave_curtida = lambda slug: slug[:64]                  # o Abacus recusa chave com mais de 64 caracteres


def curtir(p, classe=""):
    # sem número à vista (escolha do autor); o contador Abacus continua registrando (ver site.js)
    return (f'<button class="curtir {classe}" type="button" data-slug="{chave_curtida(p["slug"])}" aria-pressed="false" aria-label="Curtir este texto">'
            f'<span class="coracao" aria-hidden="true">♥</span><span class="rotulo">Curtir</span></button>')


def cartao(p, cls):
    """Cartão da grade: imagem inteira com um cartão branco por cima (largo) ou uma faixa no rodapé (estreito)."""
    tam = "(max-width: 640px) 75vw, (max-width: 960px) 50vw, " + ("370px" if cls == "b-1" else "1130px" if cls == "b-largo" else "760px")
    img = f'<img src="img/{p["capa"]}" alt="" loading="lazy" data-tam="{tam}">' if p["capa"] else ""   # alt vazio: o título já está no cartão
    if cls == "b-1":
        sob = f'<span class="b-barra">{kicker(p, False)}<span>{e(p["titulo"])}</span></span>'
    else:
        sob = f'<span class="b-card">{kicker(p, False)}<span class="b-tit">{e(p["titulo"])}</span><span class="b-dek">{e(linha(p, 110))}</span></span>'
    return f'<a class="bento {cls}" href="#{p["slug"]}">{img}{sob}</a>'


def grade(lista):
    """Monta linhas que fecham as 3 colunas: [2+1], [1+2], [1+1+1]…, sem buraco no fim."""
    n, linhas, alterna = len(lista), [], 0
    while n > 0:
        if n == 1:
            linhas.append(["b-largo"]); n -= 1
        elif n in (2, 4) or (n > 4 and n % 3 != 0 and alterna < 2):
            linhas.append(["b-2", "b-1"] if alterna % 2 == 0 else ["b-1", "b-2"]); n -= 2; alterna += 1
        else:
            linhas.append(["b-1", "b-1", "b-1"]); n -= 3
    formatos = [c for l in linhas for c in l]
    return "".join(cartao(p, c) for p, c in zip(lista, formatos))


def assinar(titulo="Receba os próximos textos por e-mail"):
    redes = "".join(f'<a class="rede" href="{u}" target="_blank" rel="noopener">{IC[k]}<span>{e(h)}</span></a>' for k, n, h, u in REDES if k != "substack")
    return f'''<section class="assinar">
  <div class="assinar-txt">
    <h2>{e(titulo)}</h2>
    <p>Física, ficção e teologia, direto na sua caixa de entrada. Grátis, pelo Substack.</p>
  </div>
  <div class="assinar-acoes">
    <a class="botao-principal" href="{SUBSTACK}/subscribe" target="_blank" rel="noopener">Assinar grátis</a>
    <div class="redes">{redes}</div>
  </div>
</section>'''


# ---------- início ----------
topo_post = next((p for p in recentes if p["capa"]), recentes[0])
destaques = [p for p in recentes if p["capa"]][:N_DESTAQUES]


def slide(p, i):
    oculto = "" if i == 0 else ' aria-hidden="true" tabindex="-1"'
    return f'''<a class="destaque slide{" ativo" if i == 0 else ""}" href="#{p["slug"]}"{oculto}>
  <img src="img/{p["capa"]}" alt=""{' data-adiar="1"' if i else ' fetchpriority="high"'} data-tam="(max-width: 640px) 75vw, (max-width: 1160px) 100vw, 1130px">
  <span class="destaque-card">{kicker(p)}<span class="destaque-tit">{e(p["titulo"])}</span>
    <span class="destaque-dek">{e(linha(p, 150))}</span><span class="ler">Ler o texto →</span></span>
</a>'''


destaque = f'''<section class="carrossel" aria-roledescription="carrossel" aria-label="Textos em destaque">
  {"".join(slide(p, i) for i, p in enumerate(destaques))}
  <div class="controles">
    <button class="seta-c ant" type="button" aria-label="Destaque anterior">‹</button>
    {"".join(f'<button class="ponto{" ativo" if i == 0 else ""}" type="button" data-i="{i}" aria-label="Destaque {i + 1}"></button>' for i in range(len(destaques)))}
    <button class="seta-c prox" type="button" aria-label="Próximo destaque">›</button>
  </div>
</section>''' if len(destaques) > 1 else slide(topo_post, 0)
manifesto = (f'<p class="manifesto">Escrevo sobre <b class="giro" data-palavras="{e("|".join(GIRO))}">{GIRO[0]}</b> '
             f'para quem sente que o mundo visível nunca é o mundo inteiro.</p>')
perfil_card = f'''<aside class="perfil-card" aria-label="Sobre o autor">
  <div class="perfil-topo"><img src="mini/{FOTO}" alt="Foto de Marcos Vinicius, o Cacau" data-tam="60px">
    <div><b>Marcos Vinicius</b><span>Cacau · no Substack</span></div></div>
  <p>{e(BIO)}</p>
  <div class="perfil-acoes"><a class="botao-principal" href="{SUBSTACK}/subscribe" target="_blank" rel="noopener">Assinar grátis</a>
    <a class="perfil-sobre" href="#sobre">Sobre mim →</a></div>
  <div class="perfil-cp">{compartilhar("inicio", "Física, ficção e teologia", "Compartilhar o site")}</div>
</aside>'''
comece = "".join(f'<li><span class="num">{i}</span><a href="#{s}">{e(porslug[s]["titulo"])}</a></li>'
                 for i, s in enumerate(COMECE, 1) if s in porslug)


def secoes_por_tema():
    """Cada texto entra uma vez, no tema principal. Tema com 1 texto pega emprestado um texto que tem esse tema
    como secundário (de um tema que fica com 2 ou mais); se ainda ficar com 1, recebe o texto do destaque."""
    resto = [p for p in recentes if p is not topo_post and p["temas"][0] in ORDEM_TEMAS]
    sec = {t: [p for p in resto if p["temas"][0] == t] for t in ORDEM_TEMAS}
    for t in ORDEM_TEMAS:
        if len(sec[t]) == 1:
            for doador in ORDEM_TEMAS:
                cand = next((p for p in sec[doador] if t in p["temas"][1:]), None) if len(sec[doador]) > 2 else None
                if cand:
                    sec[doador].remove(cand); sec[t].append(cand); break
        if len(sec[t]) == 1 and topo_post["temas"][0] == t:
            sec[t].append(topo_post)
    return [(t, sorted(sec[t], key=lambda p: p["data"], reverse=True)) for t in ORDEM_TEMAS if sec[t]]


_capas_usadas = set()
def mosaico_tema(t):
    """Cartão do tema; cada tema usa uma imagem diferente (de preferência de um texto do tema principal)."""
    lista = sorted([p for p in recentes if t in p["temas"] and p["capa"]], key=lambda p: p["temas"][0] != t)
    escolha = next((p for p in lista if p["capa"] not in _capas_usadas), lista[0] if lista else None)
    if escolha:
        _capas_usadas.add(escolha["capa"])
    img = f'<img src="mini/{escolha["capa"]}" alt="" loading="lazy" data-tam="(max-width: 640px) 27vw, (max-width: 960px) 33vw, 220px">' if escolha else ""
    n = sum(t in p["temas"] for p in posts)
    return f'<a class="tema-tile" href="#{slugt(t)}">{img}<span><b>{e(t)}</b><small>{n} texto{"s" if n != 1 else ""}</small></span></a>'


def capa_livro(l):
    img = f'<img src="mini/{l["capa"]}" alt="Capa de {e(l["titulo"])}" loading="lazy">' if l["capa"] else f'<span class="sem-capa">{e(l["titulo"])}</span>'
    return f'<a class="livro" href="#{l["slug"]}"><span class="livro-capa">{img}</span><span class="livro-tit">{e(l["titulo"])}</span><span class="livro-autor">{e(l["autor"])}</span></a>'


def estrelas(n):
    return f'<span class="estrelas" aria-label="Nota {n} de 5">' + "".join(f'<span class="{"on" if i < n else ""}">★</span>' for i in range(5)) + "</span>"


def cartao_nota(n):
    imgs = n.get("imagens") or ([n["imagem"]] if n["imagem"] else [])
    trecho = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", n["html"])).strip()
    trecho = html.unescape(trecho[:70].rsplit(" ", 1)[0] + "…" if len(trecho) > 70 else trecho)
    tam = 'data-tam="(max-width: 640px) 75vw, 380px"'
    img = ""
    if len(imgs) > 1:                                                     # carrossel: desliza como no Instagram
        img = (f'<div class="fotos" data-total="{len(imgs)}"><div class="fotos-trilho">'
               + "".join(f'<img src="img/{i}" alt="Foto {k} de {len(imgs)}{": " + e(trecho) if trecho else ""}" loading="lazy" {tam}>'
                         for k, i in enumerate(imgs, 1))
               + f'</div><span class="fotos-cont">1/{len(imgs)}</span>'
               '<button class="fotos-seta ant" type="button" aria-label="Foto anterior">‹</button>'
               '<button class="fotos-seta prox" type="button" aria-label="Próxima foto">›</button></div>')
    elif imgs:
        img = f'<img src="img/{imgs[0]}" alt="{"Foto: " + e(trecho) if trecho else "Foto"}" loading="lazy" {tam}>'
    if img and n.get("video") and n.get("url"):
        img = (f'<a class="nota-video" href="{e(n["url"])}" target="_blank" rel="noopener" aria-label="Ver o vídeo no Instagram">{img}'
               '<span class="play" aria-hidden="true">▶</span></a>')
    tema = f' · {e(n["tema"])}' if n["tema"] else ""
    data = data_ext(n["data"]) if re.match(r"\d{4}-\d{2}-\d{2}$", n["data"]) else ""
    classe = "nota curta" if n["curta"] and not imgs else "nota"
    texto = f'<div class="nota-txt">{n["html"]}</div>'
    if n.get("longa"):
        texto = (f'<div class="nota-txt dobrada">{n["html"]}</div>'
                 '<button class="continuar" type="button" aria-expanded="false">Continuar lendo</button>')
    ig = (f'<a class="nota-ig" href="{e(n["url"])}" target="_blank" rel="noopener" aria-label="Ver no Instagram">{IC["instagram"]}</a>'
          if n.get("instagram") and n.get("url") else "")
    return f'''<article class="{classe}" id="{n["slug"]}">{img}{texto}
  <footer><span class="kicker">{data}{tema}</span><span class="nota-acoes">{ig}{compartilhar(n["slug"], trecho, pequeno=True)}{curtir(n, "pequeno")}</span></footer></article>'''


fileiras = "".join(f'''<section class="fileira">
  <h2 class="etiqueta"><span>{e(t)}</span><a class="ver" href="#{slugt(t)}">ver todos →</a></h2>
  <div class="grade-bento">{grade(lista)}</div>
</section>''' for t, lista in secoes_por_tema())
sem_tema = [p for p in recentes if p["temas"][0] == "Textos" and p is not topo_post]
if sem_tema:                                           # texto novo que ainda não ganhou tema no editor
    fileiras += f'''<section class="fileira">
  <h2 class="etiqueta"><span>Mais textos</span></h2>
  <div class="grade-bento">{grade(sem_tema)}</div>
</section>'''
def vitrine(n=5):
    """Na página inicial, um pouco de cada coleção (alternando), para mostrar a variedade da estante."""
    grupos = {}
    for l in LIVROS:
        grupos.setdefault(l["colecao"], []).append(l)
    filas = [sorted(g, key=lambda x: (x["ordem"], x["titulo"])) if c else g for c, g in grupos.items()]
    filas.sort(key=lambda g: g[0]["colecao"] != "")              # as leituras do Cacau primeiro
    out = []
    while len(out) < n and any(filas):
        for g in filas:
            if g and len(out) < n:
                out.append(g.pop(0))
    return out


bloco_livros = f'''<section class="fileira">
  <h2 class="etiqueta"><span>Biblioteca</span><a class="ver" href="#biblioteca">ver os {len(LIVROS)} livros →</a></h2>
  <div class="estante">{"".join(capa_livro(l) for l in vitrine())}</div>
</section>''' if TEM_LIVROS else ""
bloco_notas = f'''<section class="fileira">
  <h2 class="etiqueta"><span>Notas curtas</span><a class="ver" href="#notas">ver todas →</a></h2>
  <div class="mural">{"".join(cartao_nota(n) for n in NOTAS[:3])}</div>
</section>''' if TEM_NOTAS else ""

inicio = f'''<section class="vista" id="inicio">
  {destaque}
  <div class="intro">{manifesto}{perfil_card}</div>
  {bloco_livros}
  <section class="explore" aria-label="Explore por tema"><h2 class="etiqueta"><span>Explore por tema</span></h2>
    <div class="temas-tiles">{"".join(mosaico_tema(t) for t in ORDEM_TEMAS)}</div></section>
  {fileiras}
  {bloco_notas}
  <section class="comece">
    <h2 class="etiqueta"><span>Comece por aqui</span></h2>
    <ol>{comece}</ol>
  </section>
  {assinar()}
</section>'''

# ---------- biblioteca e notas ----------
paginas_extras = ""
def prateleiras():
    """A Biblioteca por coleção: primeiro os livros avulsos (as leituras do Cacau), depois cada coleção em ordem."""
    avulsos = [l for l in LIVROS if not l["colecao"]]
    cols = {}
    for l in LIVROS:
        if l["colecao"]:
            cols.setdefault(l["colecao"], []).append(l)
    grupos = ([("Leituras do Cacau", avulsos)] if avulsos else []) + [
        (c, sorted(ls, key=lambda x: (x["ordem"], x["titulo"]))) for c, ls in sorted(cols.items(), key=lambda kv: (len(kv[1]), kv[0]))]
    sid = lambda c: "estante-" + re.sub(r"[^a-z0-9]+", "-", html.unescape(c).lower().translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))).strip("-")
    atalhos = "".join(f'<a href="#{sid(c)}">{e(c)} <small>{len(ls)}</small></a>' for c, ls in grupos)
    blocos = "".join(f'''<section class="prateleira" id="{sid(c)}">
    <h2 class="etiqueta"><span>{e(c)}</span><small class="ver">{len(ls)} livro{"s" if len(ls) != 1 else ""}</small></h2>
    <div class="estante grande">{"".join(capa_livro(l) for l in ls)}</div>
  </section>''' for c, ls in grupos)
    return (f'<nav class="atalhos-estante" aria-label="Coleções">{atalhos}</nav>' if len(grupos) > 1 else "") + blocos


if TEM_LIVROS:
    paginas_extras += f'''<section class="vista" id="biblioteca">
  <header class="cab-tema"><h1 class="etiqueta grande"><span>Biblioteca</span></h1>
    <p class="contagem">{len(LIVROS)} livros, com sinopse, por coleção</p></header>
  {prateleiras()}
  {assinar()}
</section>'''
    for l in LIVROS:
        meta = " · ".join(x for x in (l["autor"], l["ano"]) if x)
        paginas_extras += f'''<section class="vista" id="{l["slug"]}">
  <article class="folha livro-pag">
    <a class="voltar" href="#biblioteca">← Biblioteca</a>
    <div class="livro-cab">
      <div class="livro-capa grande">{f'<img src="img/{l["capa"]}" alt="Capa de {e(l["titulo"])}" fetchpriority="high" data-tam="(max-width: 640px) 60vw, 220px">' if l["capa"] else f'<span class="sem-capa">{e(l["titulo"])}</span>'}</div>
      <div class="livro-info">
        <span class="kicker">{e(l["colecao"]) + (f" · volume {int(l['ordem'])}" if 1 <= l["ordem"] < 999 and l["colecao"] != l["autor"] and "Cury" not in l["colecao"] else "") if l["colecao"] else "Biblioteca"}{" · " + e(l["tema"]) if l["tema"] else ""}</span>
        <h1 class="titulo-post">{e(l["titulo"])}</h1>
        <p class="livro-meta">{e(meta)}</p>
        {estrelas(l["nota"]) if l["nota"] else ""}
        {f'<p class="livro-frase">{e(l["frase"])}</p>' if l["frase"] else ""}
        <div class="acoes-mini">{curtir(l, "pequeno")}{compartilhar(l["slug"], l["titulo"], pequeno=True)}</div>
      </div>
    </div>
    <div class="corpo">{l["html"]}</div>
    <div class="curtir-fim"><p>Este resumo te ajudou?</p>{curtir(l)}{compartilhar(l["slug"], l["titulo"])}</div>
  </article>
  {assinar()}
</section>'''
if TEM_NOTAS:
    paginas_extras += f'''<section class="vista" id="notas">
  <header class="cab-tema"><h1 class="etiqueta grande"><span>Notas curtas</span></h1>
    <p class="contagem">Pensamentos rápidos, entre um texto e outro · também no Instagram, <a href="{INSTAGRAM}" target="_blank" rel="noopener">@marcos_cacau</a></p></header>
  <div class="mural todas">{"".join(cartao_nota(n) for n in NOTAS)}</div>
  {assinar()}
</section>'''

# ---------- temas ----------
paginas_tema = ""
for t in ORDEM_TEMAS:
    lista = [p for p in recentes if t in p["temas"]]
    paginas_tema += f'''<section class="vista" id="{slugt(t)}">
  <header class="cab-tema"><h1 class="etiqueta grande"><span>{e(t)}</span></h1>
    <p class="contagem">{len(lista)} texto{"s" if len(lista) != 1 else ""}</p></header>
  <div class="grade-bento">{grade(lista)}</div>
  {assinar()}
</section>'''

# ---------- textos ----------
def alt_corpo(h, titulo):
    """Imagem dentro do texto sem descrição: usa a legenda da figura ou, sem legenda, o título do texto."""
    def com_alt(tag, texto):
        if re.search(r'\salt="[^"]+"', tag):
            return tag
        return "<img" + f' alt="{e(texto)}"' + re.sub(r'\salt=(""|\'\')', "", tag[4:])

    def figura(m):
        leg = conteudo.texto_puro(re.search(r"<figcaption\b.*?</figcaption>", m.group(0), re.S).group(0))[:140]
        return re.sub(r"<img\b[^>]*>", lambda x: com_alt(x.group(0), leg), m.group(0)) if leg else m.group(0)
    h = re.sub(r"<figure\b(?:(?!</figure>).)*?<figcaption\b.*?</figure>", figura, h, flags=re.S)
    return re.sub(r"<img\b[^>]*>", lambda x: com_alt(x.group(0), "Imagem do texto " + titulo), h)


artigos = ""
for k, p in enumerate(recentes):
    ant = recentes[k + 1] if k + 1 < len(recentes) else None
    prox = recentes[k - 1] if k > 0 else None
    rel = [x for x in recentes if x is not p and set(x["temas"]) & set(p["temas"])]
    rel = (rel + [x for x in recentes if x is not p and x not in rel])[:3]
    nav = '<nav class="navpost">'
    nav += f'<a href="#{ant["slug"]}"><span>← Anterior</span>{e(ant["titulo"])}</a>' if ant else "<span></span>"
    nav += f'<a class="dir" href="#{prox["slug"]}"><span>Próximo →</span>{e(prox["titulo"])}</a>' if prox else "<span></span>"
    nav += "</nav>"
    artigos += f'''<section class="vista" id="{p["slug"]}">
  <article class="folha post">
    <a class="voltar" href="#inicio">← Todos os textos</a>
    {tags(p)}
    <h1 class="titulo-post">{e(p["titulo"])}</h1>
    {f'<p class="linha-fina">{e(p["sub"])}</p>' if p["sub"] else ""}
    <div class="linha-byline"><p class="byline">por <strong>Cacau</strong> · {data_ext(p["data"])} · {minutos(p["palavras"])} min de leitura</p><div class="acoes-mini">{curtir(p, "pequeno")}{compartilhar(p["slug"], p["titulo"], pequeno=True)}</div></div>
    {f'<figure class="capa"><img src="img/{p["capa"]}" alt="{e(p["titulo"])}" fetchpriority="high" data-tam="(max-width: 640px) 75vw, (max-width: 900px) 100vw, 864px"></figure>' if p["capa"] else ""}
    <div class="corpo">
{alt_corpo(p["html"], p["titulo"])}
    </div>
    <div class="curtir-fim"><p>Gostou deste texto?</p>{curtir(p)}{compartilhar(p["slug"], p["titulo"])}</div>
    {f'<p class="origem">Publicado originalmente no <a href="{e(p["url"])}" target="_blank" rel="noopener">Substack</a> em {data_ext(p["data"])}.</p>' if p["url"] else ""}
    {nav}
  </article>
  {assinar("Gostou? Receba o próximo texto por e-mail")}
  <h2 class="etiqueta"><span>Leia também</span></h2>
  <div class="grade-bento tres">{"".join(cartao(x, "b-1") for x in rel)}</div>
</section>'''

boas = porslug.get("sejam-bem-vindos")
redes_sobre = "".join(f'<a class="rede" href="{u}" target="_blank" rel="noopener">{IC[k]}<span>{e(n)} · {e(h)}</span></a>' for k, n, h, u in REDES)
sobre = f'''<section class="vista" id="sobre">
  <article class="folha post">
    <div class="sobre-cab"><img src="img/{FOTO}" alt="Foto de Marcos Vinicius, o Cacau" data-tam="130px"><div>
      <span class="kicker">Sobre</span><h1 class="titulo-post">Marcos Vinicius, o Cacau</h1><p class="linha-fina">{e(BIO)}</p>
      <div class="redes">{redes_sobre}</div></div></div>
    <div class="corpo">{boas["html"] if boas else ""}</div>
  </article>
  {assinar()}
</section>'''

# ---------- páginas: cada endereço vira um arquivo (bom para o Google e para a prévia no WhatsApp/Instagram) ----------
GOAT = str(CFG.get("goatcounter") or "").strip()
CUSDIS = str(CFG.get("cusdis_app_id") or "").strip()
GOOGLE = str(CFG.get("google_verificacao") or "").strip()


def comentarios(p):
    if not CUSDIS:
        return ""
    return f'''<section class="comentarios" aria-label="Comentários">
  <h2 class="etiqueta"><span>Comentários</span></h2>
  <div id="cusdis_thread" data-host="https://cusdis.com" data-app-id="{e(CUSDIS)}" data-page-id="{e(p["slug"])}"
       data-page-url="{ENDERECO}{rota(p["slug"])}" data-page-title="{e(p["titulo"])}" data-theme="auto"></div>
  <p class="comentarios-nota">Qualquer pessoa pode comentar, sem criar conta. Os comentários aparecem depois de aprovados.</p>
</section>
<script async defer src="https://cusdis.com/js/cusdis.es.js"></script>'''


# comentários no fim de cada texto (antes do convite para assinar)
for p in recentes:
    marca = f'<section class="vista" id="{p["slug"]}">'
    i = artigos.find(marca)
    j = artigos.find("</article>", i) + len("</article>")
    artigos = artigos[:j] + comentarios(p) + artigos[j:]

# página "links" (para a bio do Instagram)
ultimo = recentes[0] if recentes else None
links_pag = f'''<section class="vista" id="links">
  <div class="links">
    {f'<img class="links-foto" src="mini/{FOTO}" alt="Foto de Marcos Vinicius, o Cacau" data-tam="104px">' if FOTO else ""}
    <h1>Marcos Vinicius · Cacau</h1>
    <p>{e(BIO)}</p>
    <nav class="links-lista">
      {f'<a class="links-destaque" href="#{ultimo["slug"]}"><small>Texto mais recente</small>{e(ultimo["titulo"])}</a>' if ultimo else ""}
      <a href="{SUBSTACK}/subscribe" target="_blank" rel="noopener">Receber os textos por e-mail (grátis)</a>
      <a href="#inicio">Todos os textos no site</a>
      {'<a href="#notas">Notas curtas</a>' if TEM_NOTAS else ""}
      {'<a href="#biblioteca">Biblioteca</a>' if TEM_LIVROS else ""}
      {"".join(f'<a href="{u}" target="_blank" rel="noopener">{IC[k]} {e(n)} · {e(h)}</a>' for k, n, h, u in REDES)}
    </nav>
  </div>
</section>'''

# painel (só para o autor; fora do menu, do mapa do site e do Google): visitas e curtidas de cada página
chave_visita = lambda i: "v-" + i[:60]                    # contador de visitas no Abacus, o mesmo serviço das curtidas
painel_dados = [dict(t="Página inicial", k="Página", u="/", v=chave_visita("inicio"))]
painel_dados += [dict(t=p["titulo"], k="Texto", u=rota(p["slug"]), v=chave_visita(p["slug"]), c=chave_curtida(p["slug"])) for p in recentes]
painel_dados += [dict(t=l["titulo"], k="Livro", u=rota(l["slug"]), v=chave_visita(l["slug"]), c=chave_curtida(l["slug"])) for l in LIVROS]
painel_dados += [dict(t=corta(conteudo.texto_puro(n["html"]), 60) or "(nota só com foto)", k="Nota", u=rota(n["slug"]), c=chave_curtida(n["slug"])) for n in NOTAS]
painel_dados += [dict(t=t, k="Tema", u=rota(slugt(t)), v=chave_visita(slugt(t))) for t in ORDEM_TEMAS]
painel_dados += [dict(t=t, k="Página", u=rota(i), v=chave_visita(i)) for i, t in
                 (("biblioteca", "Biblioteca"), ("notas", "Notas curtas"), ("sobre", "Sobre"), ("links", "Links (bio do Instagram)")) if i != "notas" or TEM_NOTAS]
painel = f'''<section class="vista" id="painel">
  <header class="cab-tema"><h1 class="etiqueta grande"><span>Painel</span></h1>
    <p class="contagem">Visitas e curtidas de cada página. Esta página não aparece no menu nem no Google; guarde o endereço.</p></header>
  <div class="painel-resumo"><div><b class="painel-total" data-o="visitas">…</b><small>visitas no total</small></div>
    <div><b class="painel-total" data-o="curtidas">…</b><small>curtidas no total</small></div></div>
  <p class="painel-status" aria-live="polite"></p>
  <label class="painel-eu"><input type="checkbox" class="painel-nao-contar"> Não contar as minhas visitas neste aparelho</label>
  <div class="painel-filtros" role="group" aria-label="Mostrar">{"".join(f'<button type="button" data-k="{k}" aria-pressed="{str(k == "Tudo").lower()}">{k}</button>' for k in ("Tudo", "Texto", "Livro", "Nota", "Tema", "Página"))}</div>
  <table class="painel-tabela"><thead><tr><th>Página</th><th>Tipo</th><th class="n">Visitas</th><th class="n">Curtidas</th></tr></thead><tbody></tbody></table>
  <p class="painel-nota">As visitas começaram a ser contadas em 10 de outubro de 2026. Robôs e as suas visitas marcadas acima ficam de fora. Não guarda nada de quem visita: só soma um número por página.</p>
  <script type="application/json" id="painel-dados">{json.dumps(painel_dados, ensure_ascii=False).replace("</", "<\\/")}</script>
</section>'''

tudo = inicio + paginas_tema + paginas_extras + artigos + sobre + links_pag + painel
MARCA = '<section class="vista" id="'
vistas = {}
for parte in tudo.split(MARCA)[1:]:
    i = parte[:parte.index('"')]
    vistas[i] = MARCA + parte
ids = set(vistas)


# No celular, as imagens de tela cheia dizem "75vw": num aparelho 3x isso escolhe a versão de 960 px em vez da de 1400
# (a diferença não se vê numa foto, e o arquivo cai pela metade). No computador vale o tamanho real.
TAMANHOS = {"img": "(max-width: 640px) 75vw, (max-width: 760px) 100vw, 704px", "mini": "(max-width: 640px) 30vw, 210px"}


def afinar(h):
    """Cada imagem ganha largura e altura (a página não "pula" ao carregar) e as versões WebP, para o navegador
    baixar só o tamanho que cabe na tela. O tamanho na tela vem de data-tam (ou do padrão da pasta)."""
    def troca(m):
        tag = m.group(0)
        s = re.search(r'\ssrc="/(img|mini)/([^"]+)"', tag)
        med = img.medidas.get(s.group(2)) if s else None
        if not med:
            return tag
        t = re.search(r'\sdata-tam="([^"]*)"', tag)
        tam = t.group(1) if t else TAMANHOS[s.group(1)]
        tag = tag.replace(t.group(0), "") if t else tag
        l, a = med[s.group(1)]
        extra = f' srcset="{", ".join(f"/w/{arq} {w}w" for w, arq in med["w"])}" sizes="{tam}"'
        if "width=" not in tag:
            extra += f' width="{l}" height="{a}"'
        tag = tag[:-1].rstrip("/ ") + extra + ">"
        if 'data-adiar="1"' in tag:            # slide escondido do carrossel: o site.js carrega pouco antes de aparecer
            tag = re.sub(r'\s(src|srcset)="', r' data-\1="', tag.replace(' data-adiar="1"', ""))
        return tag
    return re.sub(r"<img\b[^>]*>", troca, h)


def caminhos(h):
    h = re.sub(r'href="#([^"]+)"', lambda m: f'href="{rota(m.group(1))}"' if m.group(1) in ids else m.group(0), h)
    return afinar(re.sub(r'(src|srcset)="(img|mini)/', r'\1="/\2/', h))


# título, resumo e imagem de cada página (o que aparece no Google e na prévia dos links)
info = {"inicio": ("Cacau — Física, Ficção e Teologia", BIO, None), "sobre": ("Sobre · Cacau", BIO, FOTO),
        "notas": ("Notas curtas · Cacau", "Pensamentos rápidos, entre um texto e outro.", NOTAS[0]["imagem"] if NOTAS else None),
        "biblioteca": ("Biblioteca · Cacau", "Resumos de livros.", LIVROS[0]["capa"] if LIVROS else None),
        "links": ("Cacau · links", BIO, FOTO), "painel": ("Painel · Cacau", "Visitas e curtidas.", None)}
for t in ORDEM_TEMAS:
    info[slugt(t)] = (f"{t} · Cacau", f"Textos de {t.lower()} de Marcos Vinicius (Cacau).", None)
for p in posts:
    info[p["slug"]] = (f'{p["titulo"]} · Cacau', p["sub"] or linha(p, 160), p["capa"])
for l in LIVROS:
    info[l["slug"]] = (f'{l["titulo"]} — resumo · Cacau', l["resumo"][:160], l["capa"])

menu = "".join(f'<a href="#{slugt(t)}">{e(t)}</a>' for t in ORDEM_TEMAS)
menu += ('<a href="#biblioteca">Biblioteca</a>' if TEM_LIVROS else "") + ('<a href="#notas">Notas</a>' if TEM_NOTAS else "")
CSS = open(os.path.join(S, "site.css"), encoding="utf-8").read()
JS = open(os.path.join(S, "site.js"), encoding="utf-8").read()
VER = hashlib.sha1((CSS + JS).encode()).hexdigest()[:8]                  # muda o nome quando o visual muda (sem cache velho)
open(os.path.join(SITE, "site.css"), "w", encoding="utf-8", newline="\n").write(CSS)
open(os.path.join(SITE, "site.js"), "w", encoding="utf-8", newline="\n").write(JS)
capa_padrao = next((p["capa"] for p in recentes if p["capa"]), FOTO)
cabecalho = f'''<header class="topo">
  <div class="topo-dentro">
    <a class="logo" href="#inicio"><span class="logo-nome">CACAU</span><span class="logo-sub">física · ficção · teologia</span></a>
    <nav class="menu" aria-label="Seções"><a href="#inicio">Início</a>{menu}<a href="#sobre">Sobre</a></nav>
    <button class="topo-busca" type="button" aria-label="Buscar no site" title="Buscar (/)" hidden>{ICS["lupa"]}</button>
    <a class="topo-assinar" href="{SUBSTACK}/subscribe" target="_blank" rel="noopener">Assinar</a>
  </div>
</header>'''
rodape = f'''<footer class="rodape"><div class="rodape-dentro">
  <nav class="rodape-menu" aria-label="Seções"><a href="#inicio">Início</a>{menu}<a href="#sobre">Sobre</a></nav>
  <div class="rodape-redes">{"".join(f'<a href="{u}" target="_blank" rel="noopener" aria-label="{e(n)}">{IC[k]}</a>' for k, n, h, u in REDES)}</div>
  <div class="rodape-fim">
    <span class="logo-nome">CACAU</span>
    <p>© {HOJE[:4]} Marcos Vinicius (Cacau) · textos também em <a href="{SUBSTACK}" target="_blank" rel="noopener">marcoscacau.substack.com</a></p>
  </div>
</div></footer>'''


def pagina(i, corpo):
    titulo, desc, imagem = info.get(i, ("Cacau", BIO, None))
    url = ENDERECO + rota(i)
    imagem = imagem or capa_padrao
    tipo = "article" if i in porslug or i.startswith("livro-") else "website"
    sem_moldura = i == "links"
    extra = ""
    if i in porslug:
        p = porslug[i]
        extra = (f'<meta property="article:published_time" content="{p["data"]}">\n'
                 f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article","headline":{json.dumps(p["titulo"], ensure_ascii=False)},'
                 f'"datePublished":"{p["data"]}","author":{{"@type":"Person","name":"Marcos Vinicius (Cacau)"}},'
                 f'"image":"{ENDERECO}/img/{imagem}","mainEntityOfPage":"{url}"}}</script>')
    elif i == "inicio":                                   # o Google pode mostrar uma caixa de busca do site
        extra = (f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"Cacau","url":"{ENDERECO}/",'
                 f'"potentialAction":{{"@type":"SearchAction","target":"{ENDERECO}/?busca={{q}}","query-input":"required name=q"}}}}</script>')
    elif i == "painel":
        extra = '<meta name="robots" content="noindex, nofollow">'
    conta = "" if i in ("painel", "erro") else f' data-conta="{chave_visita(i)}"'
    classes = ' class="so-conteudo"' if sem_moldura else ""
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="Cacau">
<meta property="og:type" content="{tipo}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="pt_BR">
{f'<meta property="og:image" content="{ENDERECO}/img/{imagem}">' if imagem else ""}
<meta name="twitter:card" content="summary_large_image">
{extra}
{f'<meta name="google-site-verification" content="{e(GOOGLE)}">' if GOOGLE else ""}
{ICONES.replace('href="', 'href="/')}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Oswald:wght@600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,700;1,8..60,400&family=Roboto:wght@300;400;500;700&display=swap">
<link rel="stylesheet" href="/site.css?v={VER}">
{f'<script data-goatcounter="https://{e(GOAT)}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' if GOAT else ""}
</head>
<body{classes}{conta}>
{"" if sem_moldura else caminhos(cabecalho)}
<main class="pagina">
{caminhos(corpo)}
</main>
{"" if sem_moldura else caminhos(rodape) + BUSCA}
<script src="/site.js?v={VER}"></script>
</body>
</html>
'''


for i, corpo in vistas.items():
    pasta = os.path.join(SITE, *[x for x in rota(i).split("/") if x])
    os.makedirs(pasta, exist_ok=True)
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8", newline="\n").write(pagina(i, corpo))

# endereços antigos (#vida) continuam funcionando: a página inicial redireciona
antigos = json.dumps({i: rota(i) for i in ids}, ensure_ascii=False)
inicio_f = os.path.join(SITE, "index.html")
h = open(inicio_f, encoding="utf-8").read()
h = h.replace("<head>\n", f'<head>\n<script>(function(){{var r={antigos},k=location.hash.slice(1);if(r[k]&&r[k]!=="/")location.replace(r[k]);}})();</script>\n', 1)
open(inicio_f, "w", encoding="utf-8", newline="\n").write(h)
nao_achou = f'''<section class="vista" id="erro"><article class="folha post"><h1 class="titulo-post">Página não encontrada</h1>
<p class="linha-fina">O endereço pode ter mudado ou o texto saiu do site.</p><p><a class="botao-principal" href="#inicio">Ir para o início</a></p></article></section>'''
open(os.path.join(SITE, "404.html"), "w", encoding="utf-8", newline="\n").write(pagina("erro", nao_achou.replace('href="#inicio"', 'href="/"')))

# índice da busca (baixado só quando alguém abre a busca): título, tipo, endereço, uma linha, palavras-chave sem acento
# e o texto (o navegador tira os acentos na hora; o texto original fica para mostrar o trecho)
puro = lambda h: unicodedata.normalize("NFC", conteudo.texto_puro(h))
indice = [dict(t=p["titulo"], k="Texto", u=rota(p["slug"]), l=linha(p, 140), b=sem_acento(" ".join([p["titulo"], p["sub"], " ".join(p["temas"])])),
               x=puro(p["html"])) for p in recentes]
indice += [dict(t=l["titulo"], k="Livro", u=rota(l["slug"]), l=" · ".join(x for x in (l["autor"], l["colecao"]) if x),
                b=sem_acento(" ".join([l["titulo"], l["autor"], l["colecao"]])), x=puro(l["html"] + " " + e(l["frase"]))) for l in LIVROS]
for n in NOTAS:
    txt = puro(n["html"])
    if txt:
        indice.append(dict(t=corta(txt, 80), k="Nota", u=rota(n["slug"]), l=data_ext(n["data"]) if re.match(r"\d{4}-\d{2}-\d{2}$", n["data"]) else "",
                           b=sem_acento(n["tema"] or ""), x=txt))
open(os.path.join(SITE, "busca.json"), "w", encoding="utf-8").write(json.dumps(indice, ensure_ascii=False, separators=(",", ":")))

# mapa do site e robots, para o Google
datas = {p["slug"]: p["data"] for p in posts}
datas.update({l["slug"]: l["data"] for l in LIVROS if l["data"]})
urls = "".join(f'<url><loc>{ENDERECO}{rota(i)}</loc>{f"<lastmod>{datas[i]}</lastmod>" if datas.get(i) else ""}</url>'
               for i in sorted(ids, key=lambda x: (x != "inicio", rota(x))) if i not in ("links", "painel"))
open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(
    f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
open(os.path.join(SITE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nDisallow: /painel/\nSitemap: {ENDERECO}/sitemap.xml\n")
open(os.path.join(SITE, indexnow.CHAVE + ".txt"), "w").write(indexnow.CHAVE)   # prova para o Bing de que o site é seu
open(os.path.join(SITE, ".nojekyll"), "w").close()
print("ok:", len(vistas), "páginas ·", len(posts), "textos ·", len(NOTAS), "notas ·", len(LIVROS), "livros")
