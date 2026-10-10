"""Site do Cacau: base Gates Notes (carrossel no topo, frase-manifesto, grade de cartões, rodapé grande)
com toques do Super Literário (página inicial por categoria, etiquetas de seção).
Cada texto aparece uma vez só na página inicial (no tema principal); a página do texto não tem coluna lateral.
Tudo vem da pasta conteudo/ (ver conteudo.py). Biblioteca e Notas só aparecem quando têm o mínimo.

uso: python gerador/site.py [pasta de saída]     (padrão: _site)
O GitHub roda isto sozinho a cada alteração (.github/workflows/site.yml).
"""
import os, re, sys, html, datetime
import conteudo

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


def curtir(p, classe=""):
    # curtidas que o post já tinha no Substack (data-base) + curtidas no site (contador Abacus, ver site2.js)
    b = p.get("curtidas", 0)
    return (f'<button class="curtir {classe}" type="button" data-slug="{p["slug"]}" data-base="{b}" aria-pressed="false">'
            f'<span class="coracao" aria-hidden="true">♥</span><span class="rotulo">Curtir</span><span class="n">{b}</span></button>')


def cartao(p, cls):
    """Cartão da grade: imagem inteira com um cartão branco por cima (largo) ou uma faixa no rodapé (estreito)."""
    img = f'<img src="img/{p["capa"]}" alt="" loading="lazy">' if p["capa"] else ""
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
  <img src="img/{p["capa"]}" alt=""{' loading="lazy"' if i else ""}>
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
  <div class="perfil-topo"><img src="mini/{FOTO}" alt="Foto de Marcos Vinicius, o Cacau">
    <div><b>Marcos Vinicius</b><span>Cacau · no Substack</span></div></div>
  <p>{e(BIO)}</p>
  <div class="perfil-acoes"><a class="botao-principal" href="{SUBSTACK}/subscribe" target="_blank" rel="noopener">Assinar grátis</a>
    <a class="perfil-sobre" href="#sobre">Sobre mim →</a></div>
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
    img = f'<img src="mini/{escolha["capa"]}" alt="" loading="lazy">' if escolha else ""
    n = sum(t in p["temas"] for p in posts)
    return f'<a class="tema-tile" href="#{slugt(t)}">{img}<span><b>{e(t)}</b><small>{n} texto{"s" if n != 1 else ""}</small></span></a>'


def capa_livro(l):
    img = f'<img src="mini/{l["capa"]}" alt="Capa de {e(l["titulo"])}" loading="lazy">' if l["capa"] else f'<span class="sem-capa">{e(l["titulo"])}</span>'
    return f'<a class="livro" href="#{l["slug"]}"><span class="livro-capa">{img}</span><span class="livro-tit">{e(l["titulo"])}</span><span class="livro-autor">{e(l["autor"])}</span></a>'


def estrelas(n):
    return f'<span class="estrelas" aria-label="Nota {n} de 5">' + "".join(f'<span class="{"on" if i < n else ""}">★</span>' for i in range(5)) + "</span>"


def cartao_nota(n):
    imgs = n.get("imagens") or ([n["imagem"]] if n["imagem"] else [])
    img = ""
    if len(imgs) > 1:                                                     # carrossel: desliza como no Instagram
        img = (f'<div class="fotos" data-total="{len(imgs)}"><div class="fotos-trilho">'
               + "".join(f'<img src="img/{i}" alt="Foto {k} de {len(imgs)}" loading="lazy">' for k, i in enumerate(imgs, 1))
               + f'</div><span class="fotos-cont">1/{len(imgs)}</span>'
               '<button class="fotos-seta ant" type="button" aria-label="Foto anterior">‹</button>'
               '<button class="fotos-seta prox" type="button" aria-label="Próxima foto">›</button></div>')
    elif imgs:
        img = f'<img src="img/{imgs[0]}" alt="" loading="lazy">'
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
    return f'''<article class="{classe}">{img}{texto}
  <footer><span class="kicker">{data}{tema}</span><span class="nota-acoes">{ig}{curtir(n, "pequeno")}</span></footer></article>'''


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
bloco_livros = f'''<section class="fileira">
  <h2 class="etiqueta"><span>Biblioteca</span><a class="ver" href="#biblioteca">ver a biblioteca →</a></h2>
  <div class="estante">{"".join(capa_livro(l) for l in LIVROS[:5])}</div>
</section>''' if TEM_LIVROS else ""
bloco_notas = f'''<section class="fileira">
  <h2 class="etiqueta"><span>Notas curtas</span><a class="ver" href="#notas">ver todas →</a></h2>
  <div class="mural">{"".join(cartao_nota(n) for n in NOTAS[:3])}</div>
</section>''' if TEM_NOTAS else ""

inicio = f'''<section class="vista" id="inicio">
  {destaque}
  <div class="intro">{manifesto}{perfil_card}</div>
  <section class="explore" aria-label="Explore por tema"><h2 class="etiqueta"><span>Explore por tema</span></h2>
    <div class="temas-tiles">{"".join(mosaico_tema(t) for t in ORDEM_TEMAS)}</div></section>
  {fileiras}
  {bloco_livros}
  {bloco_notas}
  <section class="comece">
    <h2 class="etiqueta"><span>Comece por aqui</span></h2>
    <ol>{comece}</ol>
  </section>
  {assinar()}
</section>'''

# ---------- biblioteca e notas ----------
paginas_extras = ""
if TEM_LIVROS:
    paginas_extras += f'''<section class="vista" id="biblioteca">
  <header class="cab-tema"><h1 class="etiqueta grande"><span>Biblioteca</span></h1>
    <p class="contagem">{len(LIVROS)} livro{"s" if len(LIVROS) != 1 else ""} resumido{"s" if len(LIVROS) != 1 else ""}, do mais recente ao mais antigo</p></header>
  <div class="estante grande">{"".join(capa_livro(l) for l in LIVROS)}</div>
  {assinar()}
</section>'''
    for l in LIVROS:
        meta = " · ".join(x for x in (l["autor"], l["ano"]) if x)
        paginas_extras += f'''<section class="vista" id="{l["slug"]}">
  <article class="folha livro-pag">
    <a class="voltar" href="#biblioteca">← Biblioteca</a>
    <div class="livro-cab">
      <div class="livro-capa grande">{f'<img src="img/{l["capa"]}" alt="Capa de {e(l["titulo"])}">' if l["capa"] else f'<span class="sem-capa">{e(l["titulo"])}</span>'}</div>
      <div class="livro-info">
        <span class="kicker">Resumo de livro{" · " + e(l["tema"]) if l["tema"] else ""}</span>
        <h1 class="titulo-post">{e(l["titulo"])}</h1>
        <p class="livro-meta">{e(meta)}</p>
        {estrelas(l["nota"]) if l["nota"] else ""}
        {f'<p class="livro-frase">{e(l["frase"])}</p>' if l["frase"] else ""}
        {curtir(l, "pequeno")}
      </div>
    </div>
    <div class="corpo">{l["html"]}</div>
    <div class="curtir-fim"><p>Este resumo te ajudou?</p>{curtir(l)}</div>
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
    <div class="linha-byline"><p class="byline">por <strong>Cacau</strong> · {data_ext(p["data"])} · {minutos(p["palavras"])} min de leitura</p>{curtir(p, "pequeno")}</div>
    {f'<figure class="capa"><img src="img/{p["capa"]}" alt=""></figure>' if p["capa"] else ""}
    <div class="corpo">
{p["html"]}
    </div>
    <div class="curtir-fim"><p>Gostou deste texto?</p>{curtir(p)}</div>
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
    <div class="sobre-cab"><img src="img/{FOTO}" alt="Foto de Marcos Vinicius, o Cacau"><div>
      <span class="kicker">Sobre</span><h1 class="titulo-post">Marcos Vinicius, o Cacau</h1><p class="linha-fina">{e(BIO)}</p>
      <div class="redes">{redes_sobre}</div></div></div>
    <div class="corpo">{boas["html"] if boas else ""}</div>
  </article>
  {assinar()}
</section>'''

menu = "".join(f'<a href="#{slugt(t)}">{e(t)}</a>' for t in ORDEM_TEMAS)
menu += ('<a href="#biblioteca">Biblioteca</a>' if TEM_LIVROS else "") + ('<a href="#notas">Notas</a>' if TEM_NOTAS else "")
CSS = open(os.path.join(S, "site.css"), encoding="utf-8").read()
JS = open(os.path.join(S, "site.js"), encoding="utf-8").read()
doc = f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Cacau — Física, Ficção e Teologia</title>
<meta name="description" content="{e(BIO)}">
{ICONES}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Oswald:wght@600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,700;1,8..60,400&family=Roboto:wght@300;400;500;700&display=swap">
<style>
{CSS}
</style>
</head>
<body>
<header class="topo">
  <div class="topo-dentro">
    <a class="logo" href="#inicio"><span class="logo-nome">CACAU</span><span class="logo-sub">física · ficção · teologia</span></a>
    <nav class="menu" aria-label="Seções"><a href="#inicio">Início</a>{menu}<a href="#sobre">Sobre</a></nav>
    <a class="topo-assinar" href="{SUBSTACK}/subscribe" target="_blank" rel="noopener">Assinar</a>
  </div>
</header>
<main class="pagina">
{inicio}
{paginas_tema}
{paginas_extras}
{artigos}
{sobre}
</main>
<footer class="rodape"><div class="rodape-dentro">
  <nav class="rodape-menu" aria-label="Seções"><a href="#inicio">Início</a>{menu}<a href="#sobre">Sobre</a></nav>
  <div class="rodape-redes">{"".join(f'<a href="{u}" target="_blank" rel="noopener" aria-label="{e(n)}">{IC[k]}</a>' for k, n, h, u in REDES)}</div>
  <div class="rodape-fim">
    <span class="logo-nome">CACAU</span>
    <p>© {HOJE[:4]} Marcos Vinicius (Cacau) · textos também em <a href="{SUBSTACK}" target="_blank" rel="noopener">marcoscacau.substack.com</a></p>
  </div>
</div></footer>
<script>
{JS}
</script>
</body>
</html>
'''
# as vistas têm id "v-<endereço>", para o navegador não pular até a âncora ao abrir #endereço
doc = doc.replace('class="vista" id="', 'class="vista" id="v-')
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8", newline="\n").write(doc)
open(os.path.join(SITE, ".nojekyll"), "w").close()
print("ok:", len(doc) // 1024, "KB ·", len(posts), "textos ·", len(NOTAS), "notas ·", len(LIVROS), "livros")
