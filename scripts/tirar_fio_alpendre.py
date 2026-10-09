"""Tira o fio elétrico que atravessa o vale na foto do alpendre (a que cresce
em «Ao ar livre»; a versão escolhida pelo Eduardo, alpendre-referencia.jpg).

1. Na abertura da porta, coluna a coluna, procura a crista escura do fio: o
   pixel muito mais escuro do que a média de 5 px acima e abaixo.
2. Ajusta-lhe uma curva (o fio pende: parábola) e marca uma faixa de ±4 px.
3. Tapa a faixa com a mata de logo acima (mesma coluna, 14 px mais alto),
   com as bordas esbatidas, para manter a textura das árvores.
O original fica igual; grava scripts/alpendre-sem-fio.jpg, que é a que o
imagens.py usa.

Correr: py scripts/tirar_fio_alpendre.py"""
import os
import numpy as np
import cv2

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = RAIZ + '/scripts/alpendre-referencia.jpg'
OUT = RAIZ + '/scripts/alpendre-sem-fio.jpg'
X0, X1 = 1414, 1716          # a abertura da porta (entre as ombreiras de pedra)
Y0, Y1 = 400, 510            # a faixa onde o fio passa

im = cv2.imread(SRC).astype(np.float32)
L = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
# crista escura: o pixel contra a média de 5 px acima e abaixo
acima = np.roll(L, 5, axis=0); abaixo = np.roll(L, -5, axis=0)
crista = (acima + abaixo) / 2 - L
# o fio vai mais ou menos de (1415, 474) a (1715, 436): procura-se a crista
# só a ±10 px dessa reta, para não apanhar as sombras das árvores
guia = lambda x: 474 + (x - 1415) * (436 - 474) / 300
xs, ys = [], []
for x in range(X0 + 2, X1 - 2):
    g = int(round(guia(x)))
    col = crista[g - 10:g + 11, x]
    y = int(np.argmax(col)); v = col[y]
    if v > 12:
        xs.append(x); ys.append(g - 10 + y)
xs, ys = np.array(xs), np.array(ys)
curva = np.polyfit(xs, ys, 2)
# afasta os pontos soltos (folhas escuras) e volta a ajustar
bom = np.abs(ys - np.polyval(curva, xs)) < 3
curva = np.polyfit(xs[bom], ys[bom], 2)

H, W = L.shape
yy, xx = np.mgrid[0:H, 0:W]
dist = np.abs(yy - np.polyval(curva, xx))
dentro = (xx >= X0) & (xx <= X1)
# máscara com a borda esbatida: 1 até 4 px do fio, 0 aos 7 px
m = np.clip((7 - dist) / 3, 0, 1) * dentro
m = m[..., None]
fonte = np.roll(im, 14, axis=0)            # a mata 14 px acima (já longe do fio)
out = im * (1 - m) + fonte * m
cv2.imwrite(OUT, np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 96])
print('pontos do fio', int(bom.sum()), 'de', len(xs), '· curva', np.round(curva, 6))
