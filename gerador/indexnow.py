"""Avisa os buscadores (Bing, DuckDuckGo, Yandex, Seznam, Naver…) que o site mudou, pelo IndexNow. Não precisa de conta:
a "chave" abaixo é pública por natureza — o site publica o arquivo /<chave>.txt e o buscador confere que é o mesmo.
(O Google não usa o IndexNow; ele lê o sitemap.xml sozinho.)

uso: python gerador/indexnow.py      (o GitHub roda depois de publicar, só quando algo mudou)
"""
import json, re, sys, time, urllib.request

CHAVE = "ac56586bb5f82e678b3696def12ad881"


def main():
    import conteudo
    site = str(conteudo.config().get("endereco") or "https://marcoscacau.github.io").rstrip("/")
    for t in range(6):                                     # o Pages leva alguns segundos para mostrar a versão nova
        try:
            ok = urllib.request.urlopen(f"{site}/{CHAVE}.txt", timeout=30).read().decode().strip() == CHAVE
        except Exception:
            ok = False
        if ok:
            break
        time.sleep(15)
    else:
        sys.exit("o arquivo da chave ainda não está no ar; o aviso fica para a próxima publicação")
    mapa = urllib.request.urlopen(f"{site}/sitemap.xml", timeout=30).read().decode()
    urls = re.findall(r"<loc>([^<]+)</loc>", mapa)
    dados = json.dumps({"host": site.split("//")[1], "key": CHAVE, "keyLocation": f"{site}/{CHAVE}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=dados, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        print("IndexNow:", r.status, "·", len(urls), "endereços avisados")
    except urllib.error.HTTPError as e:
        print("IndexNow respondeu", e.code, e.read()[:200])


if __name__ == "__main__":
    main()
