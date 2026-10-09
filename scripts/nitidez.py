"""Nitidez de cada foto: variância do laplaciano numa versão a 1600 px de
largura (mesma escala para todas), mais o ruído estimado no céu/zonas lisas."""
import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps
SRC = 'C:/Users/Eduardo/Desktop/SItes/Clientes/casa-do-caminho-ossela/dossie/marketing/fotos/'
K = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=float)
def lap(a):
    return (a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:] - 4 * a[1:-1, 1:-1])
res = []
for d in ('exterior', 'interior'):
    for f in sorted(os.listdir(SRC + d)):
        im = ImageOps.exif_transpose(Image.open(SRC + d + '/' + f)).convert('L')
        W, H = im.size
        if W < 1500:
            res.append((0, d + '/' + f, W, H, 0)); continue
        im = im.resize((1600, round(H * 1600 / W)), Image.LANCZOS)
        a = np.asarray(im, dtype=float)
        L = lap(a)
        # nitidez: percentil 99 do |laplaciano| (arestas fortes), robusto ao ruído
        sharp = np.percentile(np.abs(L), 99)
        res.append((sharp, d + '/' + f, W, H, L.var()))
for s, f, W, H, v in sorted(res, reverse=True):
    print(f'{s:6.1f} {v:8.1f} {W}x{H} {f}')
