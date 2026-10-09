# Casa do Caminho

Site da Casa do Caminho (Mosteiro, Ossela, Oliveira de Azeméis), versão base
de demonstração. Versão 2: combina o melhor de três sites — da Casa da Gueira
a letra fina, o texto que se acende, a foto que cresce e o fundo que muda de
tom; das Casas dos Avós o acordeão das divisões e o fecho em arco; da Quinta da
Malhada o visor. A versão 1 (cópia da Malhada) está em `arquivo/site-v1-malhada/`.

- `site/` — o site (HTML, CSS e JS, sem build). É a pasta que a Netlify publica.
- `netlify.toml` — configuração da Netlify.
- `scripts/imagens.py` — prepara as imagens a partir das fotos do dossiê
  (`py scripts/imagens.py`): tratamento leve (ruído, contraste local,
  sombras, cor) e nitidez à medida de cada tamanho. Precisa do OpenCV
  (`py -m pip install opencv-python-headless`).
- `scripts/tirar_fio.py` e `scripts/tirar_deposito.py` — apagam o fio elétrico
  da fachada e o depósito solar das fotos da pérgola; correm antes do
  `imagens.py` (gravam as fotos retocadas em `scripts/`).
- `scripts/tirar_fio_alpendre.py` — apaga o fio elétrico do vale na foto do
  alpendre (a que cresce em «Ao ar livre»); grava `scripts/alpendre-sem-fio.jpg`.
- `scripts/alisar_ceu.py` — tira os blocos de compressão do céu da foto do fim;
  corre depois do `cor_referencia.py` e grava `scripts/hero-ceu.jpg`.
- `scripts/mapa_dados.py` e `scripts/mapa.py` — o mapa de «Como chegar».
  O primeiro descarrega (uma vez) as estradas, rios e matas do OpenStreetMap
  e o relevo (tiles terrarium) para `scripts/mapa-dados/`. O segundo desenha o
  SVG e escreve-o no `index.html` entre `<!-- mapa:inicio -->` e
  `<!-- mapa:fim -->`; as cores e as letras estão no `styles.css` (`.mapa__*`).
  A atribuição «© OpenStreetMap» tem de ficar no mapa (licença ODbL).
- `scripts/cor_referencia.py` — dá à foto do hero (a casa debaixo da pérgola,
  sem o depósito) a cor da versão escolhida pelo Eduardo
  (`scripts/hero-referencia.jpg`); corre depois do `tirar_deposito.py` e antes
  do `imagens.py`. As outras versões escolhidas (`scripts/*-referencia.jpg`)
  usam-se tal como estão.
- `fotos-livres/` e `fotos-terceiros/` — fotos da região, com os créditos; as
  de `fotos-terceiros/` não têm licença livre e só servem para a demonstração.
- `dossie/` — o dossiê da casa; `dossie/site-pronto.md` diz o que o site pode afirmar.
