"""Roda no GitHub Actions: lista no Google Books os livros em português de cada autor e baixa as capas."""
import json, os, time, urllib.request, urllib.parse
SAIDA = "saida_livros"
os.makedirs(os.path.join(SAIDA, "capas"), exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
AUTORES = ["Augusto Cury", "Dan Brown", "J.R.R. Tolkien"]


def get(u, binario=False):
    for t in range(5):
        try:
            d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
            return d if binario else json.loads(d)
        except Exception as ex:
            err = ex
            time.sleep(5 * (t + 1))
    raise err


tudo = {}
for autor in AUTORES:
    vistos, itens = set(), []
    for inicio in range(0, 400, 40):
        q = urllib.parse.quote(f'inauthor:"{autor}"')
        d = get(f"https://www.googleapis.com/books/v1/volumes?q={q}&langRestrict=pt&printType=books&maxResults=40&startIndex={inicio}")
        lote = d.get("items", [])
        for it in lote:
            if it["id"] in vistos:
                continue
            vistos.add(it["id"])
            vi = it["volumeInfo"]
            itens.append(dict(id=it["id"], titulo=vi.get("title", ""), subtitulo=vi.get("subtitle", ""), autores=vi.get("authors", []),
                              editora=vi.get("publisher", ""), data=vi.get("publishedDate", ""), descricao=vi.get("description", ""),
                              paginas=vi.get("pageCount"), lingua=vi.get("language"), categorias=vi.get("categories", []),
                              isbn=next((x["identifier"] for x in vi.get("industryIdentifiers", []) if x["type"] == "ISBN_13"), ""),
                              tem_capa=bool(vi.get("imageLinks"))))
        print(autor, inicio, len(lote))
        if len(lote) < 40:
            break
        time.sleep(1.5)
    tudo[autor] = itens
    print(autor, "total", len(itens))
json.dump(tudo, open(os.path.join(SAIDA, "google.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# capas (maior tamanho disponível), só das que têm imagem
for autor, itens in tudo.items():
    for it in itens:
        if not it["tem_capa"]:
            continue
        f = os.path.join(SAIDA, "capas", it["id"] + ".jpg")
        for u in (f"https://books.google.com/books/publisher/content/images/frontcover/{it['id']}?fife=w800-h1200",
                  f"https://books.google.com/books/content?id={it['id']}&printsec=frontcover&img=1&zoom=1"):
            try:
                data = get(u, binario=True)
                if len(data) > 3000:
                    open(f, "wb").write(data)
                    break
            except Exception:
                pass
        time.sleep(0.3)
print("capas:", len(os.listdir(os.path.join(SAIDA, "capas"))))
