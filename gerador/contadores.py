"""Foto dos contadores (visitas e curtidas) para o /painel/.

O contador gratuito (Abacus) aceita só 30 leituras a cada 10 segundos, e o painel tem umas 400.
Lidas todas de uma vez no navegador, a maioria era recusada e virava zero, e o total "descia".
Aqui elas são lidas com calma, no ritmo que o contador aceita, e vão para /contadores.json.
Um número nunca desce: vale o maior entre a leitura de agora e a foto anterior (que também
protege do contador apagar uma página que passou meses sem visita).

Uso: python gerador/contadores.py _site          (lê tudo; uns 3 minutos)
     python gerador/contadores.py _site --rapido (só repete a foto anterior)
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://abacus.jasoncameron.dev/get/marcoscacau-site/"
FOTO = "https://marcoscacau.github.io/contadores.json"
UA = {"User-Agent": "Mozilla/5.0 (compatible; site-marcoscacau/1.0)"}


def anterior():
    try:
        with urllib.request.urlopen(urllib.request.Request(FOTO, headers=UA), timeout=20) as r:
            return json.loads(r.read()).get("valores", {})
    except Exception:
        return {}


def ler(chave):
    """Valor do contador; 0 se a chave não existe; espera e tenta de novo se o contador pedir calma."""
    for _ in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + chave, headers=UA), timeout=20) as r:
                return json.loads(r.read()).get("value", 0)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 0
            if e.code == 429:
                fim = int(e.headers.get("ratelimit-reset") or 0)
                time.sleep(min(15, max(2, fim - time.time() + 1)) if fim > 1e9 else 11)
                continue
            return None
        except Exception:
            time.sleep(3)
    return None


def main():
    saida = sys.argv[1]
    painel = open(os.path.join(saida, "painel", "index.html"), encoding="utf-8").read()
    linhas = json.loads(re.search(r'id="painel-dados">([\s\S]*?)</script>', painel).group(1).replace("<\\/", "</"))
    chaves = sorted({l[k] for l in linhas for k in ("v", "c") if l.get(k)})
    valores = anterior()
    lidas = falhas = 0
    if "--rapido" not in sys.argv:
        for k in chaves:
            v = ler(k)
            if v is None:
                falhas += 1
                continue
            lidas += 1
            valores[k] = max(v, valores.get(k, 0))
    json.dump({"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "valores": valores},
              open(os.path.join(saida, "contadores.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"contadores: {len(chaves)} chaves, {lidas} lidas agora, {falhas} sem resposta, {len(valores)} na foto")


if __name__ == "__main__":
    main()
