"""Lê a pasta conteudo/ (o que você edita no Pages CMS ou no GitHub) e prepara as imagens do site.

Cada post é um arquivo .md: o cabeçalho (entre ---) tem os campos e o resto é o texto.
  conteudo/textos/  textos longos (os do Substack); o texto fica em HTML
  conteudo/notas/   notas curtas e posts do Instagram; o texto fica em Markdown
  conteudo/livros/  resumos de livros; Markdown
  conteudo/imagens/ todas as imagens
  conteudo/config.yml  bio, foto, redes, frase do topo, "Comece por aqui"
Apagar o arquivo tira o post do site; `publicar: false` esconde sem apagar.
"""
import os, re, html, datetime
import yaml
from markdown_it import MarkdownIt
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(RAIZ, "conteudo")
IMAGENS = os.path.join(C, "imagens")
MIN_LIVROS, MIN_NOTAS = 3, 6
md = MarkdownIt("commonmark", {"breaks": True, "html": True})


def texto_puro(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()


def ler(caminho):
    txt = open(caminho, encoding="utf-8").read().replace("\r\n", "\n")
    meta, corpo = {}, txt
    m = re.match(r"---\n(.*?)\n---\n?", txt, re.S)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        corpo = txt[m.end():]
    return meta, corpo.strip()


def data_str(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v or "")[:10]


def lista(v):
    if v is None or v == "":
        return []
    return v if isinstance(v, list) else [v]


def publicado(m):
    v = m.get("publicar", True)
    return v is True or str(v).lower() in ("true", "sim", "yes", "1")


def itens(pasta):
    d = os.path.join(C, pasta)
    out = []
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".md") and not f.startswith("_"):
            m, corpo = ler(os.path.join(d, f))
            if publicado(m):
                out.append((f[:-3], m, corpo))
    return out


def config():
    f = os.path.join(C, "config.yml")
    return yaml.safe_load(open(f, encoding="utf-8")) if os.path.exists(f) else {}


# ---------- imagens ----------
class Imagens:
    """Toda imagem usada vira img/<nome>.jpg (1400 px) e mini/<nome>.jpg (640 px) no site, para a prévia dos links,
    e w/<nome>-<largura>.webp em 4 larguras: o navegador baixa só a que cabe na tela (bem mais leve)."""
    LARGURAS = (360, 640, 960, 1400)

    def __init__(self, site):
        self.site = site
        self.medidas = {}                      # nome -> {"img": (l, a), "mini": (l, a), "w": [(largura, arquivo), ...]}
        for p in ("img", "mini", "w"):
            os.makedirs(os.path.join(site, p), exist_ok=True)

    def _salva(self, origem, f, larg, formato):
        if not os.path.exists(f) or os.path.getmtime(f) < os.path.getmtime(origem):
            im = Image.open(origem).convert("RGB")
            im.thumbnail((larg, larg * 2))
            if formato == "JPEG":
                im.save(f, "JPEG", quality=82, optimize=True, progressive=True)
            else:
                im.save(f, "WEBP", quality=74, method=5)
        with Image.open(f) as im:
            return im.size

    def __call__(self, ref):
        if not ref:
            return None
        nome = os.path.basename(str(ref).split("?")[0])
        origem = os.path.join(IMAGENS, nome)
        if not os.path.exists(origem):
            print("  aviso: imagem não encontrada:", ref)
            return None
        base = os.path.splitext(nome)[0]
        saida = base + ".jpg"
        if saida in self.medidas:
            return saida
        m = {}
        for pasta, larg in (("img", 1400), ("mini", 640)):
            m[pasta] = self._salva(origem, os.path.join(self.site, pasta, saida), larg, "JPEG")
        m["w"], vistas = [], set()
        for larg in self.LARGURAS:
            arq = f"{base}-{larg}.webp"
            l, _ = self._salva(origem, os.path.join(self.site, "w", arq), larg, "WEBP")
            if l not in vistas:                # imagem pequena: as larguras maiores dariam o mesmo arquivo
                vistas.add(l)
                m["w"].append((l, arq))
        self.medidas[saida] = m
        return saida

    def no_html(self, h):
        """Imagens dentro do texto: /conteudo/imagens/x.png -> img/x.jpg."""
        def troca(m):
            n = self(m.group(2))
            return f'{m.group(1)}"img/{n}"' if n else m.group(0)
        h = re.sub(r'(<img[^>]*?\ssrc=)"(/?conteudo/imagens/[^"]+)"', troca, h)
        return re.sub(r'<img(?![^>]*loading=)', '<img loading="lazy"', h)


def sem_secao_vazia(h):
    partes = [x for x in re.split(r"\n(?=<h\d)", h) if x.strip()]
    vazia = lambda x: re.fullmatch(r"\s*<h\d[^>]*>.*?</h\d>\s*", x, re.S)
    return "\n".join(x for x in partes if not vazia(x))


def md_html(corpo):
    h = md.render(corpo or "")
    h = re.sub(r"<h1>", "<h2>", re.sub(r"</h1>", "</h2>", h))
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', h)
    return sem_secao_vazia(h)


# ---------- coleções ----------
def textos(img):
    res = []
    for nome, m, corpo in itens("textos"):
        h = img.no_html(corpo)
        temas = [t for t in lista(m.get("temas")) if t]
        res.append(dict(slug=nome, titulo=str(m.get("titulo") or nome), sub=str(m.get("subtitulo") or ""),
                        data=data_str(m.get("data")), temas=temas,
                        url=m["substack"] if str(m.get("substack") or "").startswith("http") else "",
                        curtidas=int(m.get("curtidas_substack") or 0), capa=img(m.get("capa")), html=h,
                        palavras=len(texto_puro(h).split()), resumo=texto_puro(re.sub(r"<(figure|h[1-6])[\s\S]*?</\1>", " ", h))))
    return res


def notas(img):
    res = []
    for nome, m, corpo in itens("notas"):
        h = md_html(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", corpo))         # fotos ficam no campo "fotos"
        fotos = [x for x in (img(f) for f in lista(m.get("fotos"))) if x]
        tam = len(texto_puro(h))
        link = m.get("link") or ""
        res.append(dict(slug="nota-" + nome, data=data_str(m.get("data")) or nome[:10], tema=m.get("tema") or "",
                        html=h, imagens=fotos, imagem=fotos[0] if fotos else None, curta=tam <= 160, longa=tam > 420,
                        url=link, instagram="instagram.com" in link, video=bool(m.get("video"))))
    return sorted(res, key=lambda x: x["data"], reverse=True)


def livros(img):
    res = []
    for nome, m, corpo in itens("livros"):
        try:
            nota = max(0, min(5, int(float(m.get("nota") or 0))))
        except (TypeError, ValueError):
            nota = 0
        h = img.no_html(md_html(corpo))
        frase = str(m.get("frase") or "")
        try:
            ordem = float(m["ordem"]) if m.get("ordem") not in (None, "") else 999
        except (TypeError, ValueError):
            ordem = 999
        res.append(dict(slug="livro-" + nome, titulo=str(m.get("livro") or nome), autor=str(m.get("autor") or ""),
                        colecao=str(m.get("colecao") or "").strip(), ordem=ordem,
                        ano=str(m.get("ano") or ""), tema=m.get("tema") or "", nota=nota, frase=frase,
                        data=data_str(m.get("data")), capa=img(m.get("capa")), html=h, resumo=frase or texto_puro(h)[:200]))
    return sorted(res, key=lambda x: x["data"], reverse=True)
