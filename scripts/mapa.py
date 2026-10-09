"""Desenha o mapa de "Como chegar" (SVG) e mete-o no index.html.

Lê os dados de mapa-dados/ (descarregados por mapa_dados.py) e escreve o SVG
entre os marcadores <!-- mapa:inicio --> e <!-- mapa:fim --> do index.html.
O SVG vai inline para as etiquetas usarem as letras do site; as cores e os
tamanhos estão no styles.css (.mapa__*).

    py mapa.py
"""
import json, math, os, re
import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(AQUI, 'mapa-dados')
HTML = os.path.join(AQUI, '..', 'site', 'index.html')

CASA = (40.8162458, -8.4220418)
# o recorte: centrado um pouco a norte da casa, para caber Ossela
CENTRO = (40.8214, -8.4220)
LARGURA_KM = 3.9
VW, VH = 1200, 900
KM_LON = 111.32 * math.cos(math.radians(CENTRO[0]))
KM_LAT = 110.57
DLON = LARGURA_KM / KM_LON / 2
DLAT = LARGURA_KM * VH / VW / KM_LAT / 2
W, E = CENTRO[1] - DLON, CENTRO[1] + DLON
S, N = CENTRO[0] - DLAT, CENTRO[0] + DLAT
UNID_M = LARGURA_KM * 1000 / VW  # metros por unidade do SVG


def xy(lat, lon):
    return (lon - W) / (E - W) * VW, (N - lat) / (N - S) * VH


def dentro(pts, m=60):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return max(xs) > -m and min(xs) < VW + m and max(ys) > -m and min(ys) < VH + m


def simplifica(pts, eps=0.7, fechado=False):
    if len(pts) < 3:
        return pts
    a = np.array(pts, np.float32).reshape(-1, 1, 2)
    return [tuple(p) for p in cv2.approxPolyDP(a, eps, fechado).reshape(-1, 2)]


def corta(pts, m=40):
    """Tira os troços longe do quadro (mantém um ponto de cada lado)."""
    fora = [not (-m < x < VW + m and -m < y < VH + m) for x, y in pts]
    pedacos, atual = [], []
    for i, p in enumerate(pts):
        perto = not fora[i] or (i > 0 and not fora[i - 1]) or (i + 1 < len(pts) and not fora[i + 1])
        if perto:
            atual.append(p)
        elif atual:
            pedacos.append(atual); atual = []
    if atual:
        pedacos.append(atual)
    return [p for p in pedacos if len(p) > 1]


def num(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def d_pts(pts, fechar=False):
    s = 'M' + ' '.join(f'{num(x)} {num(y)}' for x, y in pts)
    return s + ('Z' if fechar else '')


# ---------------------------------------------------------------- dados
osm = json.load(open(os.path.join(DADOS, 'osm.json'), encoding='utf-8'))['elements']

CLASSE = {
    'primary': 'grande', 'primary_link': 'grande', 'secondary': 'grande', 'secondary_link': 'grande', 'trunk': 'grande',
    'tertiary': 'media', 'tertiary_link': 'media',
    'residential': 'pequena', 'unclassified': 'pequena', 'living_street': 'pequena',
    'service': 'servico', 'track': 'caminho',
}
camadas = {k: [] for k in ('mata', 'agua', 'rio', 'ribeiro', 'caminho', 'servico', 'pequena', 'media', 'grande', 'edificio')}
# o Caima e os troços de rio sem nome (o outro rio no quadro é o Moscoso)
caima_e_afins = []
igrejas = []

for e in osm:
    t = e.get('tags', {})
    g = e.get('geometry')
    if e['type'] == 'relation' and t.get('natural') == 'water':
        for m in e.get('members', []):
            if m.get('role') == 'outer' and m.get('geometry'):
                pts = [xy(q['lat'], q['lon']) for q in m['geometry']]
                if dentro(pts):
                    camadas['agua'].append(simplifica(pts, 0.6, True))
        continue
    if t.get('amenity') == 'place_of_worship' and 'igreja' in t.get('name', '').lower():
        if g:
            la = sum(q['lat'] for q in g) / len(g); lo = sum(q['lon'] for q in g) / len(g)
        elif 'lat' in e:
            la, lo = e['lat'], e['lon']
        else:
            continue
        igrejas.append((t['name'], xy(la, lo)))
    if not g or e['type'] != 'way':
        continue
    pts = [xy(q['lat'], q['lon']) for q in g if q]
    if not dentro(pts):
        continue
    if t.get('landuse') == 'forest' or t.get('natural') in ('wood', 'scrub'):
        camadas['mata'].append(simplifica(pts, 1.2, True))
    elif t.get('natural') == 'water':
        camadas['agua'].append(simplifica(pts, 0.6, True))
    elif t.get('waterway') == 'river':
        for p in corta(pts):
            camadas['rio'].append(simplifica(p, 0.6))
        if 'Moscoso' not in t.get('name', ''):
            caima_e_afins.append(pts)
    elif t.get('waterway') in ('stream', 'canal'):
        for p in corta(pts):
            camadas['ribeiro'].append(simplifica(p, 0.8))
    elif t.get('highway') in CLASSE:
        for p in corta(pts):
            camadas[CLASSE[t['highway']]].append(simplifica(p, 0.6))
    elif 'building' in t:
        camadas['edificio'].append(simplifica(pts, 0.4, True))


# ---------------------------------------------------------------- relevo
def relevo():
    z = 14
    tiles = {}
    for nome in os.listdir(DADOS):
        m = re.match(r'dem-(\d+)-(\d+)-(\d+)\.png', nome)
        if m and int(m.group(1)) == z:
            tiles[(int(m.group(2)), int(m.group(3)))] = os.path.join(DADOS, nome)
    xs = sorted({k[0] for k in tiles}); ys = sorted({k[1] for k in tiles})
    mosaico = np.zeros((len(ys) * 256, len(xs) * 256), np.float32)
    for (tx, ty), f in tiles.items():
        im = cv2.imread(f, cv2.IMREAD_COLOR)[:, :, ::-1].astype(np.float32)
        alt = im[:, :, 0] * 256 + im[:, :, 1] + im[:, :, 2] / 256 - 32768
        mosaico[(ty - ys[0]) * 256:(ty - ys[0] + 1) * 256, (tx - xs[0]) * 256:(tx - xs[0] + 1) * 256] = alt
    n = 2 ** z

    def px(lat, lon):
        x = ((lon + 180) / 360 * n - xs[0]) * 256
        y = ((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n - ys[0]) * 256
        return x, y
    # reamostra para a grelha do SVG (com folga), em meia unidade
    F = 2
    gx = np.linspace(-20, VW + 20, (VW + 40) * F // 4)
    gy = np.linspace(-20, VH + 20, (VH + 40) * F // 4)
    lon = W + gx / VW * (E - W)
    lat = N - gy / VH * (N - S)
    mx = np.array([px(CENTRO[0], lo)[0] for lo in lon], np.float32)
    my = np.array([px(la, CENTRO[1])[1] for la in lat], np.float32)
    MX, MY = np.meshgrid(mx, my)
    dem = cv2.remap(mosaico, MX, MY, cv2.INTER_CUBIC)
    dem = cv2.GaussianBlur(dem, (0, 0), 2.2)
    # mais fino antes de cortar por cotas, para as linhas não sairem em escada
    dem = cv2.resize(dem, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    esc = (VW + 40) / dem.shape[1]
    curvas = []
    lo, hi = float(dem.min()), float(dem.max())
    print(f'relevo: {lo:.0f} a {hi:.0f} m')
    for cota in range(int(lo // 20 + 1) * 20, int(hi) + 1, 20):
        mask = (dem >= cota).astype(np.uint8)
        cs, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        for c in cs:
            if len(c) < 40:
                continue
            pts = [(p[0] * esc - 20, p[1] * esc - 20) for p in c.reshape(-1, 2)]
            pts = simplifica(pts, 0.9, True)
            if len(pts) > 3:
                curvas.append((cota, pts))
    return curvas


curvas = relevo()


# ---------------------------------------------------------------- etiquetas
def lugar(nome):
    for e in osm:
        if e.get('tags', {}).get('place') and e['tags'].get('name') == nome:
            return xy(e['lat'], e['lon'])
    raise KeyError(nome)


casa = xy(*CASA)


def reamostra(pts, passo=4):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        for k in range(1, int(d // passo) + 1):
            out.append((x0 + (x1 - x0) * k * passo / d, y0 + (y1 - y0) * k * passo / d))
    return out


def troco_para_nome(rios, comp=200, x0=190, x1=1010, y0=60, y1=VH - 60):
    """O troço de rio mais direito e mais deitado, dentro da parte do quadro
    que também se vê no telemóvel (onde o mapa perde os lados)."""
    melhor, nota = None, -1
    n = comp // 4
    for pts in rios:
        r = reamostra(pts)
        for i in range(0, len(r) - n, 3):
            w = r[i:i + n + 1]
            if not all(x0 < x < x1 and y0 < y < y1 for x, y in w):
                continue
            if math.hypot(cx - w[n // 2][0], cy - w[n // 2][1]) < 200:
                continue  # longe da etiqueta da casa
            corda = math.hypot(w[-1][0] - w[0][0], w[-1][1] - w[0][1])
            ang = abs(math.degrees(math.atan2(w[-1][1] - w[0][1], w[-1][0] - w[0][0])))
            ang = min(ang, 180 - ang)
            # direito pesa mais do que deitado: um nome em curva lê-se mal
            s = (corda / comp) ** 6 - ang / 150
            if s > nota:
                melhor, nota = w, s
    if not melhor:
        return []
    if melhor[0][0] > melhor[-1][0]:
        melhor = melhor[::-1]
    # uma curva suave (2.º grau) por cima do troço: as letras não tremem
    a = np.array(melhor)
    t = np.linspace(0, 1, len(a))
    fx, fy = np.polyfit(t, a[:, 0], 2), np.polyfit(t, a[:, 1], 2)
    tt = np.linspace(0, 1, 24)
    return list(zip(np.polyval(fx, tt), np.polyval(fy, tt)))


cx, cy = casa
troco = troco_para_nome(caima_e_afins)


# ---------------------------------------------------------------- SVG
def grupo(cl, polis, fechar=False):
    if not polis:
        return ''
    return f'<path class="{cl}" d="' + ''.join(d_pts(p, fechar) for p in polis if len(p) > 1) + '"/>'


partes = [
    f'<svg class="mapa__svg" viewBox="0 0 {VW} {VH}" preserveAspectRatio="xMidYMid slice" role="img" aria-labelledby="mapaTitulo" focusable="false">',
    '<title id="mapaTitulo">Mapa da zona: a Casa do Caminho em Mosteiro, Ossela, numa curva do rio Caima</title>',
    f'<rect class="mapa__terra" width="{VW}" height="{VH}"/>',
    grupo('mapa__mata', camadas['mata'], True),
    grupo('mapa__curva', [p for c, p in curvas if c % 100], True),
    grupo('mapa__curva mapa__curva--mestra', [p for c, p in curvas if not c % 100], True),
    grupo('mapa__agua', camadas['agua'], True),
    grupo('mapa__ribeiro', camadas['ribeiro']),
    grupo('mapa__rio', camadas['rio']),
    grupo('mapa__caminho', camadas['caminho']),
]
for cl in ('servico', 'pequena', 'media', 'grande'):
    partes.append(grupo(f'mapa__borda mapa__borda--{cl}', camadas[cl]))
for cl in ('servico', 'pequena', 'media', 'grande'):
    partes.append(grupo(f'mapa__estrada mapa__estrada--{cl}', camadas[cl]))
partes.append(grupo('mapa__edificio', camadas['edificio'], True))

# igreja de Ossela: uma cruz pequena
for nome, (x, y) in igrejas:
    if 'Ossela' in nome and 0 < x < VW and 0 < y < VH:
        partes.append(f'<path class="mapa__cruz" d="M{num(x)} {num(y - 9)}v18M{num(x - 6)} {num(y - 3)}h12"/>')

# o rio, escrito ao longo da água
if troco:
    partes.append(f'<path id="mapaCaima" d="{d_pts(troco)}" fill="none"/>')
    partes.append('<text class="mapa__rio-nome" dy="-9"><textPath href="#mapaCaima" startOffset="50%" text-anchor="middle">rio Caima</textPath></text>')

def rotulo(nome, x, y, cl='mapa__lugar', ancora='middle', extra=''):
    return f'<text class="{cl}" x="{num(x)}" y="{num(y)}" text-anchor="{ancora}"{extra}>{nome}</text>'

for nome, dx, dy, anc, cl in (
    ('Ossela', 0, -16, 'middle', 'mapa__lugar mapa__lugar--vila'),
    ('Selores', 0, -14, 'middle', 'mapa__lugar'),
    ('Alvelhe', 14, 6, 'start', 'mapa__lugar'),
    ('Ponte Nova', 0, -14, 'middle', 'mapa__lugar mapa__lugar--largo'),
    ('Carvalhosa', 14, 6, 'start', 'mapa__lugar'),
):
    x, y = lugar(nome)
    if 30 < x < VW - 30 and 30 < y < VH - 30:
        partes.append(rotulo(nome, x + dx, y + dy, cl, anc))

# a casa
partes.append(f'<g class="mapa__alvo" transform="translate({num(cx)} {num(cy)})">'
              '<circle class="mapa__onda" r="11"/><circle class="mapa__ponto" r="11"/></g>')
partes.append(f'<text class="mapa__casa-nome" x="{num(cx + 24)}" y="{num(cy + 2)}">Casa do Caminho'
              f'<tspan class="mapa__lugar" x="{num(cx + 25)}" dy="1.75em">Mosteiro</tspan></text>')

# norte e escala (500 m), no canto de baixo à direita; a segunda versão fica
# mais para dentro, porque no telemóvel o quadro perde os lados (só se vê
# de x=150 a x=1050)
esc = 500 / UNID_M
for direita, cl in ((VW - 44, 'mapa__legenda mapa__legenda--larga'), (1010, 'mapa__legenda mapa__legenda--estreita')):
    x = direita - esc
    partes.append(f'<g class="{cl}" transform="translate({num(x)} {VH - 44})">'
                  f'<path class="mapa__escala" d="M0 0v-7M0 0h{num(esc)}v-7"/>'
                  f'<text x="{num(esc / 2)}" y="-14" text-anchor="middle">500 m</text>'
                  f'<path class="mapa__norte" d="M-34 -2L-27 -26L-20 -2L-27 -8Z"/></g>')
partes.append('</svg>')
svg = ''.join(p for p in partes if p)

h = open(HTML, encoding='utf-8').read()
a, b = '<!-- mapa:inicio -->', '<!-- mapa:fim -->'
i, j = h.index(a) + len(a), h.index(b)
h = h[:i] + '\n        ' + svg + '\n        ' + h[j:]
open(HTML, 'w', encoding='utf-8').write(h)
print('svg', len(svg) // 1024, 'KB;', {k: len(v) for k, v in camadas.items()}, 'curvas', len(curvas), 'caima', len(troco))
