"""Traz os textos novos do Substack para conteudo/textos (o GitHub roda isto uma vez por dia).

Só entra texto público que nunca foi importado (lista em gerador/dados/vistos.json). Por isso, um texto
que você apagou do site não volta. O texto novo chega sem tema: escolha os temas no editor.
"""
import os, re, json, html, time, hashlib, io, urllib.request, urllib.parse
from html.parser import HTMLParser
import yaml
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTOS = os.path.join(RAIZ, "conteudo", "textos")
IMAGENS = os.path.join(RAIZ, "conteudo", "imagens")
VISTOS = os.path.join(RAIZ, "gerador", "dados", "vistos.json")
BASE = "https://marcoscacau.substack.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def get(u, tent=8):
    """O Substack às vezes responde 500; tenta de novo com espera crescente."""
    for i in range(tent):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*"}), timeout=60).read()
        except Exception as e:
            err = e
            time.sleep(2 * (i + 1))
    raise err


def original(u):
    u = u.replace("&amp;", "&")
    m = re.search(r"/(https?%3A%2F%2F.+)$", u)
    return urllib.parse.unquote(m.group(1)) if m else u


def baixa_imagem(u):
    """Guarda em conteudo/imagens/<hash>.jpg (até 1600 px) e devolve o caminho usado no conteúdo."""
    o = original(u)
    nome = hashlib.sha1(o.encode()).hexdigest()[:12] + ".jpg"
    f = os.path.join(IMAGENS, nome)
    if not os.path.exists(f):
        try:
            data = get(o)
        except Exception:
            data = get(u.replace("&amp;", "&"))
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((1600, 3200))
        im.save(f, "JPEG", quality=85, optimize=True, progressive=True)
    return "/conteudo/imagens/" + nome


# ---------- HTML do Substack -> HTML limpo ----------
VOID = {"br", "hr", "img", "source", "input", "meta", "link", "polyline", "line", "path"}
PULAR_TAG = {"svg", "button", "form", "input", "source", "script", "style", "noscript"}
PULAR_CLASSE = ("image-link-expand", "subscription-widget", "button-wrapper", "subscribe-widget", "share-dialog", "footnote-anchor-")
INLINE = {"strong": ("<strong>", "</strong>"), "b": ("<strong>", "</strong>"), "em": ("<em>", "</em>"), "i": ("<em>", "</em>")}
BLOCO = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "ul", "ol", "li", "hr", "figure", "div", "pre"}


class No:
    def __init__(self, tag, attrs=None, pai=None):
        self.tag, self.attrs, self.pai, self.filhos = tag, dict(attrs or {}), pai, []


class Arvore(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.raiz = self.atual = No("raiz")

    def handle_starttag(self, tag, attrs):
        n = No(tag, attrs, self.atual)
        self.atual.filhos.append(n)
        if tag not in VOID:
            self.atual = n

    def handle_startendtag(self, tag, attrs):
        self.atual.filhos.append(No(tag, attrs, self.atual))

    def handle_endtag(self, tag):
        n = self.atual
        while n is not self.raiz and n.tag != tag:
            n = n.pai
        if n is not self.raiz:
            self.atual = n.pai

    def handle_data(self, d):
        self.atual.filhos.append(d)


def pular(n):
    return n.tag in PULAR_TAG or any(k in n.attrs.get("class", "") for k in PULAR_CLASSE)


def achar(n, tag):
    for f in n.filhos:
        if isinstance(f, No):
            if f.tag == tag:
                return f
            r = achar(f, tag)
            if r:
                return r
    return None


def texto(n):
    if isinstance(n, str):
        return n
    return "" if pular(n) else "".join(texto(f) for f in n.filhos)


def inl(n):
    if isinstance(n, str):
        return html.escape(n, quote=False)
    if pular(n):
        return ""
    if n.tag == "br":
        return "<br>"
    dentro = "".join(inl(f) for f in n.filhos)
    if n.tag in INLINE:
        a, b = INLINE[n.tag]
        return a + dentro + b if dentro.strip() else dentro
    if n.tag == "a":
        href = n.attrs.get("href", "")
        return f'<a href="{html.escape(href)}" target="_blank" rel="noopener">{dentro}</a>' if href else dentro
    return dentro


def blocos(n, H):
    for f in n.filhos:
        if isinstance(f, str):
            if f.strip():
                H.append("<p>" + html.escape(f.strip(), quote=False) + "</p>")
            continue
        if pular(f):
            continue
        t = f.tag
        if t == "figure" or (t == "div" and "captioned-image-container" in f.attrs.get("class", "")):
            fig = f if t == "figure" else (achar(f, "figure") or f)
            im = achar(fig, "img")
            if im is not None:
                src = im.attrs.get("src", "")
                try:
                    src = json.loads(im.attrs.get("data-attrs", "{}")).get("src") or src
                except Exception:
                    pass
                cap = achar(fig, "figcaption")
                cap = texto(cap).strip() if cap else ""
                H.append(f'<figure><img src="{baixa_imagem(src)}" alt="{html.escape(cap)}" loading="lazy">'
                         + (f"<figcaption>{html.escape(cap)}</figcaption>" if cap else "") + "</figure>")
            continue
        if t in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            h = inl(f).strip()
            if not re.sub(r"<br>|\s", "", h):
                continue
            k = min(int(t[1]) + 1, 4) if t != "p" else 0           # h1 do post vira h2 (o h1 é o título)
            H.append(f"<p>{h}</p>" if t == "p" else f"<h{k}>{h}</h{k}>")
        elif t == "hr":
            H.append("<hr>")
        elif t == "blockquote":
            h2 = []
            blocos(f, h2)
            H.append("<blockquote>" + ("".join(h2) or "<p>" + inl(f).strip() + "</p>") + "</blockquote>")
        elif t in ("ul", "ol"):
            itens = []
            for li in [x for x in f.filhos if isinstance(x, No) and x.tag == "li"]:
                hh = []
                blocos(li, hh)
                itens.append("<li>" + ("".join(hh) if hh else inl(li).strip()) + "</li>")
            H.append(f"<{t}>" + "".join(itens) + f"</{t}>")
        elif t == "pre":
            H.append("<pre>" + html.escape(texto(f)) + "</pre>")
        elif any(isinstance(x, No) and x.tag in BLOCO for x in f.filhos):
            blocos(f, H)
        else:
            h = inl(f).strip()
            if re.sub(r"<br>|\s", "", h):
                H.append(f"<p>{h}</p>")


def pelo_feed():
    """Plano B: o feed RSS traz os textos públicos recentes com o texto inteiro (a API às vezes recusa servidores)."""
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    raiz = ET.fromstring(get(f"{BASE}/feed", tent=3))
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
    out = []
    for it in raiz.iter("item"):
        link = (it.findtext("link") or "").strip()
        m = re.search(r"/p/([^/?#]+)", link)
        if not m:
            continue
        enc = it.find("enclosure")
        out.append(({"slug": m.group(1), "audience": "everyone", "reaction_count": 0,
                     "post_date": parsedate_to_datetime(it.findtext("pubDate")).strftime("%Y-%m-%d")},
                    {"title": it.findtext("title") or m.group(1), "subtitle": it.findtext("description") or "",
                     "body_html": it.findtext("content:encoded", namespaces=ns) or "", "canonical_url": link,
                     "cover_image": enc.get("url") if enc is not None else ""}))
    return out


def pela_api(ja):
    arch, off = [], 0
    while True:
        a = json.loads(get(f"{BASE}/api/v1/archive?sort=new&offset={off}&limit=12", tent=3))
        arch += a
        off += len(a)
        if len(a) < 12:
            break
    for a in arch:
        if a.get("audience") == "everyone" and a["slug"] not in ja:
            yield a, json.loads(get(f"{BASE}/api/v1/posts/{a['slug']}"))


def importar():
    os.makedirs(TEXTOS, exist_ok=True)
    os.makedirs(IMAGENS, exist_ok=True)
    vistos = json.load(open(VISTOS, encoding="utf-8")) if os.path.exists(VISTOS) else {}
    ja = set(vistos.get("substack", []))
    try:
        fonte = list(pela_api(ja))
    except Exception as ex:
        print("API do Substack recusou (", ex, "); usando o feed RSS")
        fonte = [(a, p) for a, p in pelo_feed() if a["slug"] not in ja]
    novos = []
    for a, p in fonte:
        if a["slug"] in ja or os.path.exists(os.path.join(TEXTOS, a["slug"] + ".md")):
            continue
        arv = Arvore()
        arv.feed(p.get("body_html") or "")
        H = []
        blocos(arv.raiz, H)
        capa = baixa_imagem(p["cover_image"]) if p.get("cover_image") else ""
        if capa and H and capa in H[0] and H[0].startswith("<figure>"):
            H.pop(0)                                         # a capa já abre o texto: fica só como capa
        sub = (p.get("subtitle") or "").strip()
        if sub.lower() == p["title"].strip().lower():
            sub = ""
        meta = {"titulo": p["title"].strip(), "subtitulo": sub, "data": a["post_date"][:10], "temas": [], "capa": capa,
                "publicar": True, "substack": p.get("canonical_url") or f"{BASE}/p/{a['slug']}",
                "curtidas_substack": a.get("reaction_count") or 0}
        cab = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, width=10000).strip()
        with open(os.path.join(TEXTOS, a["slug"] + ".md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(f"---\n{cab}\n---\n" + "\n".join(H) + "\n")
        ja.add(a["slug"])
        novos.append(a["slug"])
        time.sleep(0.5)
    vistos["substack"] = sorted(ja)
    json.dump(vistos, open(VISTOS, "w", encoding="utf-8"), indent=1)
    print("Substack: textos novos:", novos or "nenhum")


if __name__ == "__main__":
    importar()
