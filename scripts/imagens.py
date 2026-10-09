"""Copia as fotos escolhidas do dossiê para o site, com nome próprio e três
tamanhos (original até 2400 px, 1400 px e 800 px). Os originais do dossiê
nunca são tocados.

Cada foto passa por um tratamento leve (função trata), sem mudar o que se vê:
  1. tira o ruído e os blocos do JPEG (céu, sombras), sem tirar o grão da
     pedra;
  2. contraste local (CLAHE na luminância, misturado com o original), que
     devolve o relevo ao granito e à madeira;
  3. levanta as sombras nas fotos em contraluz (o alpendre);
  4. um pouco mais de cor onde há pouca (vibração).
Depois de cada redução (2400, 1400, 800) a foto é afiada à medida desse
tamanho (afia): é o que mais conta para parecer nítida no ecrã.

Para acrescentar uma foto: uma linha em MAP ('pasta/ficheiro do dossiê':
('nome', recorte ou None, receita)), correr `py scripts/imagens.py` e pôr o
nome no catálogo de site/main.js.

recorte = (esquerda, cima, direita, baixo) em frações da foto. O terraço sobre
o vale (terraco-02) tem uma névoa da lente na margem direita: corta-se aí.
Antes de gerar, a pasta site/assets/img é esvaziada: só lá fica o que está aqui."""
import os, json
import numpy as np
import cv2
from PIL import Image, ImageOps

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = RAIZ + '/dossie/marketing/fotos/'
DST = RAIZ + '/site/assets/img/'
os.makedirs(DST, exist_ok=True)
for f in os.listdir(DST):
    os.remove(DST + f)

# fotos já retocadas, em scripts/ (o original do dossiê fica igual):
SEM_FIO = '../../../scripts/fachada-01-sem-fio.jpg'                 # scripts/tirar_fio.py
HERO = '../../../scripts/hero-ceu.jpg'      # scripts/cor_referencia.py e depois scripts/alisar_ceu.py
# as versões escolhidas pelo Eduardo, mais nítidas e com mais cor (a da
# pérgola sem o depósito: scripts/tirar_deposito.py)
ALPENDRE = '../../../scripts/alpendre-sem-fio.jpg'    # alpendre-referencia.jpg sem o fio (scripts/tirar_fio_alpendre.py)
PERGOLA = '../../../scripts/pergola-referencia-sem-deposito.jpg'
# a oferta à chegada, na versão do Eduardo, com mais qualidade
CHEGADA = '../../../scripts/chegada-referencia.jpg'
# o quarto claro (a abertura do Interior), na versão do Eduardo, com mais qualidade
QUARTO = '../../../scripts/quarto-referencia.jpg'
# a mesa posta no alpendre (as Comodidades), na versão do Eduardo: 896 px
MESA = '../../../scripts/mesa-referencia.jpg'
# fotos da região com licença livre (créditos em fotos-livres/CREDITOS.md)
LIVRES = '../../../fotos-livres/'
# fotos de terceiros, só para a demonstração (fotos-terceiros/CREDITOS.md)
TERCEIROS = '../../../fotos-terceiros/'

FORA = {}                                   # receita por omissão das de fora
PRONTA = {'ruido': 0, 'clahe': 0, 'vibra': 0}   # já tratada: só a nitidez
DENTRO = {'clahe': 1.2, 'mistura': 0.4, 'vibra': 0.06}
PEQUENA = {'ruido': 3, 'clahe': 1.2, 'mistura': 0.4, 'vibra': 0.06}

MAP = {
    # ---- fora
    # a foto do fim (Reservar): a casa ao sol, debaixo da pérgola (sem o
    # depósito solar e com a cor que o Eduardo escolheu: scripts/cor_referencia.py)
    HERO: ('hero-pergola', None, PRONTA),
    # a foto que abre o Exterior, até às bordas do ecrã: o alpendre, com a
    # mesa, a churrasqueira e o vale
    ALPENDRE: ('alpendre-aberto', None, PRONTA),
    # hero, em ecrã inteiro: a pérgola ao sol, à porta dos quartos
    PERGOLA: ('pergola-sol', None, PRONTA),
    # a esquina de granito com o telhado de telha, ao sol. Cortada à
    # esquerda: o depósito solar no telhado de trás.
    'exterior/fachada-02.jpg': ('hero-casa', (0.32, 0, 1, 1), FORA),
    'exterior/detalhe-01.jpg': ('granito-potes', None, FORA),
    'exterior/alpendre-01.jpg': ('alpendre', None, {'sombras': 0.3}),

    # o muro de granito e as escadas que sobem para a casa. Cortada à
    # esquerda: o fio elétrico no céu.
    'exterior/fachada-04.jpg': ('muros-escadas', (0.235, 0, 1, 1), FORA),
    # a praia fluvial do Pedregulhal, em Ossela (Câmara de Oliveira de
    # Azeméis; pequena: 1020 px)
    TERCEIROS + 'praia-pedregulhal-cmoaz.jpg': ('praia-ossela', None, {'ruido': 3}),
    # arredores: cortadas em baixo (a marca de água do autor; o crédito está
    # no site, por baixo de cada foto)
    LIVRES + 'moinhos-ul.jpg': ('moinhos-ul', (0, 0, 1, 0.955), FORA),
    LIVRES + 'vale-caima-freita.jpg': ('serra-freita', (0, 0.3, 1, 0.94), FORA),
    # as escadas e o jardim, com o fio elétrico apagado (scripts/tirar_fio.py)
    SEM_FIO: ('escadas-granito', None, FORA),
    # a mesa posta no alpendre
    MESA: ('mesa-posta', None, PRONTA),
    # a oferta à chegada: espumante, dois copos e queijo num tabuleiro de
    # verga, junto à janela de granito
    CHEGADA: ('chegada', None, PRONTA),
    # ---- dentro (só as fotos nítidas: ver a medição em scripts/nitidez.txt)
    # a porta-janela entre a pedra, com a portada de madeira
    'interior/quarto-03.jpg': ('janela-granito', (0, 0, 0.597, 1), DENTRO),
    'interior/quarto-03.jpg#2': ('quarto-portadas', None, DENTRO),
    QUARTO: ('quarto-luz', None, PRONTA),
    'interior/quarto-01.jpg': ('quarto-flores', None, DENTRO),
    'interior/quarto-06.jpg': ('quarto-roupeiro', None, DENTRO),
    'interior/quarto-14.jpg': ('quarto-terraco', None, DENTRO),
    'interior/quarto-11.jpg': ('quarto-pedra', None, DENTRO),
    'interior/quarto-12.jpg': ('quarto-janelas', None, DENTRO),
    'interior/quarto-09.jpg': ('quarto-claro', None, DENTRO),
    'interior/refeicoes-01.jpg': ('sala-jantar', None, DENTRO),
    'interior/sala-02.jpg': ('sala-estar', None, DENTRO),
    'interior/sala-01.jpg': ('sala-sofa', None, DENTRO),
    'interior/refeicoes-02.jpg': ('sala-cozinha', None, DENTRO),
    'interior/cozinha-01.jpg': ('cozinha', None, DENTRO),
    'interior/casa-de-banho-04.jpg': ('wc-pedra', None, DENTRO),
    'interior/casa-de-banho-03.jpg': ('wc-duche', None, DENTRO),
    'interior/casa-de-banho-01.jpg': ('wc-madeira', None, DENTRO),
    'interior/casa-de-banho-02.jpg': ('wc-espelho', None, DENTRO),
}


# fotos mostradas em ecrã inteiro: ficam no tamanho do original (sem o
# limite de 2400) e ganham uma cópia ampliada (Lanczos + nitidez) para ecrãs
# grandes. Ampliar não inventa pormenor; só evita que o browser estique.
GRANDES = {}
INTEIRAS = {'hero-pergola', 'alpendre-aberto', 'pergola-sol', 'quarto-luz'}     # sem o limite de 2400
# as fotos em ecrã inteiro (o hero, a foto do fim, a que cresce e a abertura
# do Interior) ganham também 2200 px e AVIF
AVIF = {'hero-pergola', 'pergola-sol', 'alpendre-aberto', 'quarto-luz'}
# No telemóvel ao alto, o hero e a foto que cresce mostram só uma fatia do
# meio da foto, mas o browser pedia a foto inteira (3168 px, ~600 KB). Estas
# ganham um recorte vertical, -vertical.jpg/.avif, que o site serve a ecrãs
# estreitos (<source media> no index.html). Para o que se vê ficar igual, o
# recorte começa em pos × (largura − recorte), com pos = o object-position
# horizontal do styles.css nesse ecrã (hero 57 %, cresce 60 %): se um mudar,
# muda o outro. nome: (largura/altura do recorte, pos)
VERTICAIS = {'pergola-sol': (3 / 4, 0.57), 'alpendre-aberto': (1.0, 0.60)}
# folhagem e água miúdas pesam muito em JPEG: os moinhos de Ul a 82/80
# davam 460 KB a 1400 px. Qualidade própria para todos os tamanhos.
QUALIDADE = {'moinhos-ul': 72}


def trata(bgr, ruido=4, clahe=1.4, mistura=0.55, sombras=0.0, vibra=0.10):
    if ruido:
        bgr = cv2.fastNlMeansDenoisingColored(bgr, None, ruido, ruido, 7, 21)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0]
    if clahe:
        c = cv2.createCLAHE(clipLimit=clahe, tileGridSize=(8, 8)).apply(L.astype(np.uint8)).astype(np.float32)
        L = L * (1 - mistura) + c * mistura
    if sombras:
        x = L / 255.0
        L = 255.0 * (x + sombras * 2.2 * x * (1 - x) ** 2)
    lab[..., 0] = np.clip(L, 0, 255)
    out = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    if vibra:
        hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
        s = hsv[..., 1] / 255.0
        hsv[..., 1] = np.clip(255 * (s + vibra * 1.6 * s * (1 - s)), 0, 255)
        out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return out


def afia(bgr, raio, quanto, limiar=2):
    """máscara de nitidez; o limiar deixa o céu liso"""
    d = bgr.astype(np.int16) - cv2.GaussianBlur(bgr, (0, 0), raio).astype(np.int16)
    d[np.abs(d) < limiar] = 0
    return np.clip(bgr + quanto * d, 0, 255).astype(np.uint8)


def reduz(bgr, largura):
    h, w = bgr.shape[:2]
    if w <= largura:
        return bgr
    return cv2.resize(bgr, (largura, round(h * largura / w)), interpolation=cv2.INTER_AREA)


def grava(bgr, caminho, q):
    Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).save(caminho, quality=q, optimize=True, progressive=True)


abre = lambda p: ImageOps.exif_transpose(Image.open(SRC + p.split('#')[0])).convert('RGB')
out = {}
for src, (nome, rec, receita) in MAP.items():
    im = abre(src)
    if rec:
        W, H = im.size
        im = im.crop((round(W * rec[0]), round(H * rec[1]), round(W * rec[2]), round(H * rec[3])))
    bgr = trata(cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR), **receita)
    # o maior lado até 2400
    h, w = bgr.shape[:2]
    if max(h, w) > 2400 and nome not in INTEIRAS:
        bgr = cv2.resize(bgr, (round(w * 2400 / max(h, w)), round(h * 2400 / max(h, w))), interpolation=cv2.INTER_AREA)
    pequena = bgr.shape[1] < 1000
    grande = afia(bgr, 0.8, 0.30)
    q = QUALIDADE.get(nome)
    grava(grande, f'{DST}{nome}.jpg', q or (84 if pequena else 82))
    tam = {'full': (grande.shape[1], grande.shape[0])}
    if nome in VERTICAIS:
        prop, pos = VERTICAIS[nome]
        H, W = grande.shape[:2]
        cw = round(H * prop)
        x = round(pos * (W - cw))
        v = np.ascontiguousarray(grande[:, x:x + cw])
        grava(v, f'{DST}{nome}-vertical.jpg', 82)
        Image.fromarray(cv2.cvtColor(v, cv2.COLOR_BGR2RGB)).save(f'{DST}{nome}-vertical.avif', quality=62)
        tam['vertical'] = (cw, H)
    # as fotos pequenas (768 px) também ganham -800 e -1400, iguais ao
    # original, para o site poder pedir sempre os mesmos nomes
    for s, (raio, quanto) in ((1400, (0.7, 0.45)), (800, (0.6, 0.5))) + (((2200, (0.75, 0.4)),) if nome in AVIF else ()):
        c = grande if bgr.shape[1] <= s else afia(reduz(bgr, s), raio, quanto)
        grava(c, f'{DST}{nome}-{s}.jpg', q or (88 if pequena else 80))
        tam[s] = (c.shape[1], c.shape[0])
    if nome in GRANDES:
        L = GRANDES[nome]
        c = cv2.resize(bgr, (L, round(bgr.shape[0] * L / bgr.shape[1])), interpolation=cv2.INTER_LANCZOS4)
        c = afia(c, 1.1, 0.45)
        grava(c, f'{DST}{nome}-{L}.jpg', 80)
        tam[L] = (c.shape[1], c.shape[0])
    out[nome] = {'src': src, 'receita': receita, **{str(k): v for k, v in tam.items()}}
    if nome in AVIF:
        for s in (800, 1400, 2200, None):
            c = grande if not s else afia(reduz(bgr, s), 0.7, 0.45)
            Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)).save(f'{DST}{nome}{"-" + str(s) if s else ""}.avif', quality=62)

json.dump(out, open(RAIZ + '/scripts/imagens.json', 'w', encoding='utf-8'), indent=1)
tot = sum(os.path.getsize(DST + f) for f in os.listdir(DST))
print(len(out), 'fotos,', len(os.listdir(DST)), 'ficheiros,', round(tot / 1e6, 1), 'MB')
for k, v in out.items():
    print(k, v['full'], v['1400'])
