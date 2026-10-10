"""Traz os posts novos do Instagram (@marcos_cacau) para conteudo/notas (o GitHub tenta uma vez por dia).

Abre o perfil num navegador sem janela, como um visitante sem login (o Instagram mostra assim os
12 posts mais recentes), e lê cada post pela página pública de incorporação, que traz todas as fotos.
Só entra post que nunca foi importado (gerador/dados/vistos.json): um post apagado do site não volta.
O Instagram às vezes bloqueia esse acesso vindo de servidores; aí nada muda e ele tenta no dia seguinte.

uso: python gerador/instagram.py                 (posts novos do perfil)
     python gerador/instagram.py LINK_DO_POST ... (posts específicos, até os mais antigos)
"""
import os, re, sys, json, html, time, shutil, datetime, tempfile, subprocess, unicodedata, urllib.request
import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTAS = os.path.join(RAIZ, "conteudo", "notas")
IMAGENS = os.path.join(RAIZ, "conteudo", "imagens")
VISTOS = os.path.join(RAIZ, "gerador", "dados", "vistos.json")
PERFIL = "marcos_cacau"
EPOCA_IG = 1314220021721           # o id do post guarda o instante da publicação (ms desde esta data)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
NAVEGADOR = next((c for c in (shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser"),
                              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if c and os.path.exists(c)), None)
PERFIL_NAV = os.path.join(tempfile.gettempdir(), "cacau-instagram-nav")


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "item"


def render(url):
    """Página depois de rodar o JavaScript (o Instagram monta tudo no navegador)."""
    with tempfile.TemporaryFile() as f:
        subprocess.run([NAVEGADOR, "--headless=new", "--disable-gpu", "--no-sandbox", "--user-data-dir=" + PERFIL_NAV,
                        "--virtual-time-budget=15000", "--dump-dom", url], stdout=f, stderr=subprocess.DEVNULL, timeout=180)
        f.seek(0)
        return f.read().decode("utf-8", "ignore")


def busca(o, achou):
    if isinstance(o, dict):
        if isinstance(o.get("edges"), list) and o["edges"] and isinstance(o["edges"][0], dict) and "code" in (o["edges"][0].get("node") or {}):
            achou.extend(e["node"] for e in o["edges"])
        for v in o.values():
            busca(v, achou)
    elif isinstance(o, list):
        for v in o:
            busca(v, achou)


def linha_do_tempo():
    h = render(f"https://www.instagram.com/{PERFIL}/")
    nos = []
    for m in re.finditer(r'<script type="application/json"[^>]*>(.*?)</script>', h, re.S):
        try:
            busca(json.loads(m.group(1)), nos)
        except ValueError:
            pass
    if not nos:
        # plano B: a página de incorporação do perfil (abre sem login até em servidores) traz os 6 mais recentes
        h = render(f"https://www.instagram.com/{PERFIL}/embed/")
        i = h.find('"contextJSON":')
        if i >= 0:
            s, _ = json.JSONDecoder().raw_decode(h, i + len('"contextJSON":'))
            if isinstance(s, str):
                for m in json.loads(s).get("context", {}).get("graphql_media", []):
                    sm = m.get("shortcode_media") or {}
                    if sm.get("shortcode"):
                        nos.append({"code": sm["shortcode"], "pk": sm.get("id") or codigo_para_id(sm["shortcode"]),
                                    "product_type": "clips" if sm.get("is_video") else ""})
    vistos, out = set(), []
    for n in nos:
        if n["code"] not in vistos:
            vistos.add(n["code"]); out.append(n)
    return out


def detalhes(code):
    """Legenda e fotos em tamanho cheio pela página de incorporação do post."""
    h = render(f"https://www.instagram.com/p/{code}/embed/captioned/")
    i = h.find('"contextJSON":')
    sm = {}
    if i >= 0:
        s, _ = json.JSONDecoder().raw_decode(h, i + len('"contextJSON":'))
        if isinstance(s, str):
            sm = (json.loads(s).get("gql_data") or {}).get("shortcode_media") or {}
    if sm:
        filhos = [e["node"] for e in (sm.get("edge_sidecar_to_children") or {}).get("edges", [])] or [sm]
        cap = (sm.get("edge_media_to_caption") or {}).get("edges", [])
        return dict(imagens=[f["display_url"] for f in filhos], video=any(f.get("is_video") for f in filhos),
                    legenda=cap[0]["node"]["text"] if cap else None)
    m = re.search(r'class="EmbeddedMediaImage"[^>]*?src="([^"]+)"', h)          # post de uma foto só
    cap = re.search(r'<div class="Caption">(.*?)(?:<div class="CaptionComments"|</div>)', h, re.S)
    legenda = None
    if cap:
        t = re.sub(r'<a[^>]*class="CaptionUsername"[^>]*>.*?</a>', "", cap.group(1), count=1, flags=re.S)
        t = re.sub(r"<br\s*/?>", "\n", t)
        legenda = html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
    return dict(imagens=[html.unescape(m.group(1))] if m else [], video=False, legenda=legenda)


def baixar(url, destino):
    if os.path.exists(destino):
        return True
    for tentativa in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
            open(destino, "wb").write(data)
            return True
        except Exception as ex:
            print("   tentando de novo:", ex)
            time.sleep(3 * (tentativa + 1))
    return False


def codigo_para_id(code):
    """O código do link (instagram.com/p/CODIGO) é o id do post escrito em base 64."""
    alfa = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    n = 0
    for ch in code[:11]:
        n = n * 64 + alfa.index(ch)
    return str(n)


def titulo_de(legenda):
    primeira = next((l.strip() for l in legenda.splitlines() if l.strip()), "Post")
    palavras = re.sub(r'[\\/:*?"<>|#^\[\]_]', "", primeira).strip(" .—-").split()
    return " ".join(palavras[:7]) + ("…" if len(palavras) > 7 else "")


def importar(nos):
    os.makedirs(NOTAS, exist_ok=True)
    os.makedirs(IMAGENS, exist_ok=True)
    vistos = json.load(open(VISTOS, encoding="utf-8")) if os.path.exists(VISTOS) else {}
    ja = set(vistos.get("instagram", []))
    novos = []
    for n in nos:
        code = n["code"]
        if code in ja:
            continue
        brasilia = datetime.timezone(datetime.timedelta(hours=-3))
        data = datetime.datetime.fromtimestamp(((int(n["pk"]) >> 23) + EPOCA_IG) / 1000, brasilia).strftime("%Y-%m-%d")
        d = detalhes(code)
        legenda = (d["legenda"] or (n.get("caption") or {}).get("text") or "").strip()
        if not d["imagens"] and n.get("display_uri"):
            d["imagens"] = [n["display_uri"]]
        fotos = []
        for k, u in enumerate(d["imagens"], 1):
            f = f"ig-{code}-{k}.jpg"
            if baixar(u, os.path.join(IMAGENS, f)):
                fotos.append("/conteudo/imagens/" + f)
        if not legenda and not fotos:
            print("sem dados para", code, "(o Instagram bloqueou?)"); continue
        titulo = titulo_de(legenda)
        meta = {"titulo": titulo, "data": data, "tema": "", "fotos": fotos,
                "video": bool(d["video"] or n.get("product_type") == "clips"),
                "link": f"https://www.instagram.com/p/{code}/", "publicar": True}
        cab = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, width=10000).strip()
        nome = slug(f"{data} — Instagram — {titulo}")
        with open(os.path.join(NOTAS, nome + ".md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(f"---\n{cab}\n---\n{legenda}\n")
        ja.add(code)
        novos.append(code)
        time.sleep(2)
    vistos["instagram"] = sorted(ja)
    json.dump(vistos, open(VISTOS, "w", encoding="utf-8"), indent=1)
    print("Instagram: posts novos:", novos or "nenhum")


if __name__ == "__main__":
    if not NAVEGADOR:
        raise SystemExit("navegador não encontrado")
    if sys.argv[1:]:
        codes = [re.sub(r".*/(?:p|reel)/([A-Za-z0-9_-]+).*", r"\1", a) for a in sys.argv[1:]]
        nos = [{"code": c, "pk": codigo_para_id(c)} for c in codes]
    else:
        nos = linha_do_tempo()
        print(len(nos), "posts no perfil público")
    importar(nos)
