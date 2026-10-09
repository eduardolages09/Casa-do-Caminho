"""Tira o fio elétrico que atravessa o céu na foto da fachada (fachada-01).

1. Encontra o fio no céu limpo (coluna a coluna, o pixel mais escuro) e
   ajusta-lhe uma curva (o fio pende: parábola).
2. Ajusta ao céu azul uma superfície em degradé (por canal), com os pixéis
   de céu longe do fio.
3. Repõe o céu: interpola entre o céu logo acima e logo abaixo; onde por
   baixo há pedra ou metal (chaminé, gradeamento), usa só o céu de cima.
   Pedra e metal nunca são tocados (o fio é muito mais escuro: soma RGB
   < 200, o céu ~350, o gradeamento ~330 e azulado).
4. Junta um grão igual ao do céu, para não ficar uma risca lisa.
O original do dossiê fica igual; grava scripts/fachada-01-sem-fio.jpg, que é
a que o imagens.py usa.

Correr: py scripts/tirar_fio.py"""
import os
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = RAIZ + '/dossie/marketing/fotos/exterior/fachada-01.jpg'
OUT = RAIZ + '/scripts/fachada-01-sem-fio.jpg'
FIM = 1335          # até ao poste do gradeamento (dali para a frente o fio prende-se à casa)
CEU = 330           # abaixo disto (soma RGB) ainda é fio ou a sua orla

im = np.asarray(Image.open(SRC).convert('RGB')).astype(float)
soma = im.sum(axis=2)
rng = np.random.default_rng(7)

def minimo(x, y0, y1):
    col = soma[max(y0, 0):y1, x]
    y = int(np.argmin(col)) + max(y0, 0)
    return y, soma[y, x]

xs, ys = [], []
for x in range(320, 1060):
    y, v = minimo(x, 0, 300)
    if v < 200:
        xs.append(x); ys.append(y)
curva = np.polyfit(xs, ys, 2)
# acrescenta o troço junto à chaminé e ao gradeamento, já guiado pela curva
for x in range(1060, FIM):
    yc = int(round(np.polyval(curva, x)))
    y, v = minimo(x, yc - 12, yc + 12)
    if v < 200:
        xs.append(x); ys.append(y)
curva = np.polyfit(xs, ys, 2)

# o céu é um azul liso em degradé: ajusta-se-lhe uma superfície (quadrática
# em x e y, por canal) com os pixéis de céu longe do fio
H, W = 340, 1700
yy, xx = np.mgrid[0:H, 0:W]
dist = np.abs(yy - np.polyval(curva, xx))
reg = im[:H, :W]
azul = reg[..., 2] - reg[..., 0]
e_ceu = (azul > 80) & (reg.sum(axis=2) > 300) & (dist > 20)
def termos(x, y):
    x, y = x / W, y / H
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=-1)
A = termos(xx[e_ceu].astype(float), yy[e_ceu].astype(float))
ceu = np.empty_like(reg)
T = termos(xx.astype(float), yy.astype(float))
for c in range(3):
    coef, *_ = np.linalg.lstsq(A, reg[..., c][e_ceu], rcond=None)
    ceu[..., c] = T @ coef
grao = float((reg[e_ceu] - ceu[e_ceu]).std())

# faixa do fio (±16 px, leva a orla de cor do JPEG): troca-se o fio e a orla
# azulada; pedra (mais vermelha que azul) e metal cinzento ficam
faixa = (dist <= 16) & (xx < FIM)
soma_r = reg.sum(axis=2)
troca = faixa & ((soma_r < 260) | ((azul > 40) & (soma_r < 420)))
reg[troca] = ceu[troca] + rng.normal(0, grao, (int(troca.sum()), 3))
im[:H, :W] = reg
tapados = int(troca.sum())

Image.fromarray(im.clip(0, 255).astype(np.uint8)).save(OUT, quality=95, subsampling=0)
print('pontos do fio', len(xs), '· pixéis repostos', tapados, '· grão', round(grao, 2))
