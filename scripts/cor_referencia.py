"""Dá à foto do hero a cor da versão que o Eduardo escolheu.

A versão escolhida (scripts/hero-referencia.jpg) tem a cor mais quente e
mais viva, mas está cortada em cima e em baixo (3168×1344) e ainda tem o
depósito solar. Aqui passa-se essa cor para a foto inteira já sem o depósito
(scripts/terraco-03-sem-deposito.jpg, de tirar_deposito.py), que tem o
enquadramento 16:9 do ecrã e mais píxeis.

As outras duas versões escolhidas (o alpendre, alpendre-referencia.jpg, e a
pérgola ao sol, pergola-referencia.jpg) são mais nítidas do que os originais
e a proporção foi mudada de forma desigual: usam-se elas próprias (a da
pérgola sem o depósito, de tirar_deposito.py).

Como:
  1. alinha-se a referência com a foto (pontos SIFT e uma homografia: a
     referência tem a perspetiva e a proporção um pouco mudadas);
  2. uma correção de cor global (polinómio de grau 2 em RGB), ajustada nas
     zonas comuns, com as duas desfocadas para o alinhamento não pesar;
  3. o que sobra (as sombras levantadas, que mudam de sítio para sítio) vai
     num ganho por canal, muito desfocado, que se esbate para fora da zona
     comum.
O depósito (que só a referência tem) fica fora das contas.

Correr depois de tirar_deposito.py e antes de imagens.py:
py scripts/cor_referencia.py  →  grava scripts/hero-cor.jpg"""
import os
import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))

# nome: (foto inteira, referência, zona a ignorar (x0, y0, x1, y1) na foto)
FOTOS = {
    'hero': (AQUI + '/terraco-03-sem-deposito.jpg', AQUI + '/hero-referencia.jpg', (1100, 280, 1480, 420)),
}


def cinz(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255


def alinha(foto, ref):
    """M (3×3) leva da foto à referência (warpPerspective com WARP_INVERSE_MAP):
    pontos SIFT nas duas e uma homografia (RANSAC)"""
    sift = cv2.SIFT_create(5000)
    k1, d1 = sift.detectAndCompute(cv2.cvtColor(foto, cv2.COLOR_BGR2GRAY), None)
    k2, d2 = sift.detectAndCompute(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), None)
    pares = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.7 * b.distance]
    p1 = np.float32([k1[a.queryIdx].pt for a in pares])
    p2 = np.float32([k2[a.trainIdx].pt for a in pares])
    M, _ = cv2.findHomography(p1, p2, cv2.RANSAC, 4)
    return M


def termos(x):
    r, g, b = x[:, 0], x[:, 1], x[:, 2]
    return np.stack([np.ones_like(r), r, g, b, r * r, g * g, b * b, r * g, r * b, g * b], 1)


for nome, (cf, cr, fora) in FOTOS.items():
    foto, ref = cv2.imread(cf), cv2.imread(cr)
    H, W = foto.shape[:2]
    M = alinha(foto, ref)
    refa = cv2.warpPerspective(ref, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
    dentro = cv2.warpPerspective(np.ones(ref.shape[:2], np.uint8), M, (W, H), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP) > 0
    # o alinhamento, medido: correlação das duas, desfocadas, na zona comum
    g1, g2 = cv2.GaussianBlur(cinz(foto), (0, 0), 3)[dentro], cv2.GaussianBlur(cinz(refa), (0, 0), 3)[dentro]
    corr = float(np.corrcoef(g1, g2)[0, 1])
    ok = cv2.erode(dentro.astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
    if fora:
        x0, y0, x1, y1 = fora
        ok[y0:y1, x0:x1] = False

    # 2. a cor global
    fa = cv2.GaussianBlur(foto, (0, 0), 6).astype(np.float32) / 255
    ra = cv2.GaussianBlur(refa, (0, 0), 6).astype(np.float32) / 255
    idx = np.flatnonzero(ok)[::37]
    X, Y = fa.reshape(-1, 3)[idx], ra.reshape(-1, 3)[idx]
    coef, *_ = np.linalg.lstsq(termos(X), Y, rcond=None)
    px = foto.astype(np.float32).reshape(-1, 3) / 255
    out = np.clip(termos(px) @ coef, 0, 1).reshape(H, W, 3)

    # 3. o que sobra, local (só se o alinhamento for bom; senão faria halos): ganho por canal, muito desfocado, normalizado
    #    pelo peso da zona comum (assim esbate-se para fora dela)
    s = max(W, H) / 40
    peso = ok.astype(np.float32)
    ob = cv2.GaussianBlur(out * peso[..., None], (0, 0), s)
    rb = cv2.GaussianBlur(ra * peso[..., None], (0, 0), s)
    pb = cv2.GaussianBlur(peso, (0, 0), s)[..., None]
    ganho = np.where(pb > 1e-3, (rb + 1e-3) / (ob + 1e-3), 1)
    confia = np.clip(pb * 1.6, 0, 1)                 # 1 dentro, 0 longe da zona comum
    ganho = 1 + (np.clip(ganho, 0.7, 1.45) - 1) * confia
    if corr > 0.9:
        out = np.clip(out * ganho, 0, 1)

    erro = np.abs(cv2.GaussianBlur(out, (0, 0), 6)[ok] - ra[ok]).mean() * 255
    cv2.imwrite(f'{AQUI}/{nome}-cor.jpg', (out * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(nome, 'correlação', round(corr, 2), 'erro médio', round(erro, 1), 'níveis')
