"""Tira o depósito solar do telhado nas fotos da pérgola (terraco-01 e
terraco-03, e a versão da pérgola com a cor escolhida pelo Eduardo,
scripts/pergola-referencia.jpg), que aparecem em grande no site.

O depósito está entre duas vigas da pérgola, contra o céu. O contorno foi
marcado à mão (píxeis do original, sobre uma grelha): por baixo da viga de
cima, por cima da viga de baixo e à esquerda das telhas. Dentro dele tudo
passa a céu, menos o que é claramente viga, telha ou árvore. O céu novo é
um degradé medido no céu à volta, com o grão do céu, como no
scripts/tirar_fio.py. Os pés do suporte que ficam à frente da viga de baixo
não se tocam (no site têm 2 a 3 px).
O original do dossiê fica igual; grava scripts/<foto>-sem-deposito.jpg, que
é a que o imagens.py usa.

Correr: py scripts/tirar_deposito.py"""
import os
import numpy as np
import cv2

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = RAIZ + '/dossie/marketing/fotos/exterior/'

FOTOS = {
    'terraco-01': {
        'contorno': [(1656, 213), (1800, 233), (2058, 259), (2058, 285), (2000, 305), (1962, 318),
                     (1915, 330), (1905, 348), (1880, 362), (1800, 359), (1700, 351), (1656, 348)],
        'telhas_x': 1885,                  # à direita disto há telhas dentro do contorno
        'telhas_topo': [(1885, 318), (1960, 300), (2045, 270), (2130, 262)],   # acima disto já não é telha
        'ceu': (1600, 190, 1680, 300),     # o céu que se vê à esquerda do depósito
    },
    'terraco-03': {
        'contorno': [(1176, 350), (1290, 321), (1345, 331), (1396, 352), (1396, 393), (1340, 399),
                     (1270, 401), (1186, 399)],
        'ceu': (1120, 280, 1460, 400),
        'telhas_x': 1380,
    },
    # a versão escolhida pelo Eduardo (fim do site): o depósito por cima da
    # viga de cima, com as telhas à direita
    'pergola-referencia': {
        'src': RAIZ + '/scripts/pergola-referencia.jpg',
        'contorno': [(1978, 142), (1990, 105), (2040, 62), (2120, 30), (2165, 16), (2225, 12), (2262, 35),
                     (2270, 95), (2300, 98), (2340, 132), (2352, 146), (2300, 166), (2272, 181), (2200, 176),
                     (2100, 167), (2000, 156)],
        'ceu': (1850, 0, 2500, 140),
        'telhas_x': 2265,
        'telhas_topo': [(2265, 178), (2350, 150), (2500, 100)],
        'sem_arvore': True,                # não há árvores atrás do depósito
    },
}
rng = np.random.default_rng(7)

for nome, cfg in FOTOS.items():
    bgr = cv2.imread(cfg.get('src', SRC + nome + '.jpg'))
    H, W = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    S, V = hsv[..., 1] / 255, hsv[..., 2]
    B, G, R = [bgr[..., k].astype(np.float32) for k in range(3)]
    yy, xx = np.mgrid[0:H, 0:W]

    zona = np.zeros((H, W), np.uint8)
    cv2.fillPoly(zona, [np.array(cfg['contorno'], np.int32)], 1)
    zona = zona.astype(bool)
    # o que fica: viga e telha (castanho/laranja com cor), árvore (verde)
    madeira_telha = (R - B > 45) & (S > 0.38)
    arvore = (G > R + 10) & (G > B + 5) & (not cfg.get('sem_arvore'))
    # madeira e telha só se guardam junto ao contorno (as vigas) e do lado das
    # telhas; no meio, um reflexo quente do depósito também passa a céu
    borda = zona & ~cv2.erode(zona.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    guarda = madeira_telha & (borda | (xx > cfg['telhas_x']))
    if 'telhas_topo' in cfg:
        px, py_ = zip(*cfg['telhas_topo'])
        guarda &= ~((xx > cfg['telhas_x']) & ~borda & (yy < np.interp(xx, px, py_)))
    # manchas soltas pequenas (reflexos do depósito) não são telha
    n, rot, est, _ = cv2.connectedComponentsWithStats((guarda & zona).astype(np.uint8), 8)
    for k in range(1, n):
        if est[k, cv2.CC_STAT_AREA] < 600:
            guarda[rot == k] = False
    troca = zona & ~guarda & ~arvore
    # tapa os furinhos (o depósito tem reflexos quentes)
    troca = cv2.morphologyEx(troca.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)).astype(bool) & zona & ~arvore

    x0, y0, x1, y1 = cfg['ceu']
    caixa = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    ceu = caixa & ~zona & (B - R > 25) & (B > 150)

    def termos(x, y):
        x = (x - x0) / max(1, x1 - x0); y = (y - y0) / max(1, y1 - y0)
        return np.stack([np.ones_like(x), x, y], axis=-1)   # degradé plano

    A = termos(xx[ceu].astype(float), yy[ceu].astype(float))
    T = termos(xx[troca].astype(float), yy[troca].astype(float))
    novo = np.empty((len(T), 3))
    for k in range(3):
        coef, *_ = np.linalg.lstsq(A, bgr[..., k][ceu].astype(float), rcond=None)
        resto = bgr[..., k][ceu] - A @ coef
        novo[:, k] = T @ coef + rng.normal(0, min(4.0, float(resto.std())), len(T))
    out = bgr.copy()
    out[troca] = np.clip(novo, 0, 255).astype(np.uint8)
    # o céu novo ganha o desfoque da foto (o JPEG original não é nítido ao píxel)
    suave = cv2.GaussianBlur(out, (0, 0), 0.8)
    out[troca] = suave[troca]
    orla = cv2.dilate(troca.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~troca
    out[orla] = ((out[orla].astype(np.float32) + suave[orla]) / 2).astype(np.uint8)
    cv2.imwrite(RAIZ + f'/scripts/{nome}-sem-deposito.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(nome, 'trocados', int(troca.sum()), 'de', int(zona.sum()), '· céu medido em', int(ceu.sum()))
