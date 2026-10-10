# Site do Cacau — marcoscacau.github.io

Textos de física, ficção e teologia de Marcos Vinicius (Cacau). Também em [marcoscacau.substack.com](https://marcoscacau.substack.com).

## Como editar (sem precisar de ninguém)

1. Entre em **[app.pagescms.org](https://app.pagescms.org)** com a sua conta do GitHub e abra `marcoscacau.github.io`.
2. No menu da esquerda aparecem **Textos**, **Notas curtas**, **Biblioteca** e **Configurações do site**.
3. Para **criar**, clique em *Add an entry* (Novo), preencha e clique em *Save*.
   Para **editar**, abra o item, mude e salve.
   Para **esconder** sem apagar, desligue **Mostrar no site** e salve.
   Para **apagar**, abra o item e use o menu ⋯ → *Delete*.
4. Em uns **2 minutos** o site se atualiza sozinho. Se ainda aparecer a versão antiga, recarregue com Ctrl+F5.

As imagens vão para `conteudo/imagens` (arraste no campo de foto ou dentro do texto).

## O que acontece sozinho

- **A cada alteração**, o GitHub refaz e publica o site (aba *Actions* → *Site*).
- **Todo dia às 6h**, ele busca os textos novos do **Substack** e os posts novos do **Instagram** e os põe no site.
  O texto novo do Substack chega **sem tema**: aparece em "Mais textos" até você escolher os temas no editor.
  O Instagram às vezes bloqueia esse acesso; aí o post entra no dia seguinte, ou você cria a nota no editor.
- Um post apagado **não volta** na busca do dia seguinte (a lista do que já foi importado fica em `gerador/dados/vistos.json`).

## Onde fica cada coisa

| Pasta | O que tem |
|---|---|
| `conteudo/textos` | um arquivo por texto (os do Substack) |
| `conteudo/notas` | um arquivo por nota curta / post do Instagram |
| `conteudo/livros` | um arquivo por resumo de livro (a Biblioteca aparece com 3 ou mais) |
| `conteudo/imagens` | todas as imagens |
| `conteudo/config.yml` | mini apresentação, foto, redes, frase do topo, "Comece por aqui" |
| `gerador/` | os programas que montam o site (não precisa mexer) |
| `.pages.yml` | os campos do editor |
| `.github/workflows/site.yml` | a automação |

As **Notas curtas** aparecem no site com 6 ou mais; a **Biblioteca** com 3 ou mais.
