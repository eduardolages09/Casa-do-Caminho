"""Alisa o céu da foto do fim (a casa ao sol, debaixo da pérgola): o original
tem blocos de compressão no azul, que em ecrã inteiro se veem.

1. Marca o céu: azul (B bem acima de R) e claro, ligado à margem de cima.
   As traves, o telhado e a serra nunca entram (não são azuis).
2. Desfoca só o céu, com uma média que ignora o que não é céu (assim a
   madeira não escorre para o azul); as nuvens ficam, mais suaves.
3. Junta um grão leve igual ao da foto, para o céu não ficar de plástico.
Corre depois do cor_referencia.py: lê scripts/hero-cor.jpg e grava
scripts/hero-ceu.jpg, que é a que o imagens.py usa.

Correr: py scripts/alisar_ceu.py"""
import os
import numpy as np
import cv2

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = RAIZ + '/scripts/hero-cor.jpg'
OUT = RAIZ + '/scripts/hero-ceu.jpg'
SIGMA = 6                       # os blocos têm ~12 px nesta foto

im = cv2.imread(SRC).astype(np.float32)
H, W = im.shape[:2]
b, g, r = im[..., 0], im[..., 1], im[..., 2]
# céu: azul, ou nuvem (muito clara e quase sem cor)
azul = (b - r > 8) & (im.sum(axis=2) > 330)
nuvem = (im.sum(axis=2) > 630) & (im.max(axis=2) - im.min(axis=2) < 40)
e = (azul | nuvem)
e[int(H * 0.5):] = False
# só o que está ligado à margem de cima (o céu, não um reflexo)
n, lab = cv2.connectedComponents(e.astype(np.uint8), connectivity=4)
topo = set(np.unique(lab[0, :])) - {0}
ceu = np.isin(lab, list(topo)).astype(np.uint8)
ceu = cv2.morphologyEx(ceu, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
# afasta 2 px das traves e do telhado: as orlas ficam como estão
ceu = cv2.erode(ceu, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(np.float32)

# desfoque só dentro do céu (média que ignora o resto: a madeira não escorre
# para o azul); igual em todo o céu, para as nuvens ficarem todas iguais
m3 = ceu[..., None]
soma = cv2.GaussianBlur(im * m3, (0, 0), SIGMA)
peso = cv2.GaussianBlur(ceu, (0, 0), SIGMA)[..., None]
liso = soma / np.maximum(peso, 1e-3)
rng = np.random.default_rng(3)
liso += rng.normal(0, 1.6, liso.shape)
# a passagem para o original faz-se em ~3 px
mistura = cv2.GaussianBlur(ceu, (0, 0), 1.5)[..., None]
out = im * (1 - mistura) + liso * mistura
cv2.imwrite(OUT, np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 96])
print('céu', round(float(ceu.mean()) * 100, 1), '% da foto')
