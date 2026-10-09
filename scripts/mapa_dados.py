"""Descarrega os dados do mapa de "Como chegar" para scripts/mapa-dados/.

- OpenStreetMap (Overpass): estradas, rios, água, matas, casas, lugares.
  © contribuidores do OpenStreetMap, licença ODbL: o site tem de o dizer.
- Relevo: as tiles "terrarium" do Mapzen/AWS (elevation-tiles-prod), públicas.

Só é preciso correr uma vez (ou para refrescar os dados); o desenho é feito
por mapa.py, que lê daqui e não vai à rede.

    py mapa_dados.py
"""
import json, math, os, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, 'mapa-dados')
os.makedirs(PASTA, exist_ok=True)

# a casa (a mesma coordenada do link do Google Maps)
CASA = (40.8162458, -8.4220418)
# uma margem larga à volta: o recorte final é escolhido em mapa.py
S, N = CASA[0] - 0.024, CASA[0] + 0.024
W, E = CASA[1] - 0.042, CASA[1] + 0.042
UA = {'User-Agent': 'casa-do-caminho-site/1.0 (mapa estatico; eduardolages05 at gmail)'}

CONSULTA = f"""
[out:json][timeout:120];
(
  way["highway"]({S},{W},{N},{E});
  way["waterway"]({S},{W},{N},{E});
  way["natural"="water"]({S},{W},{N},{E});
  relation["natural"="water"]({S},{W},{N},{E});
  way["landuse"]({S},{W},{N},{E});
  way["natural"~"wood|scrub"]({S},{W},{N},{E});
  way["building"]({S},{W},{N},{E});
  way["railway"]({S},{W},{N},{E});
  node["place"]({S},{W},{N},{E});
  nwr["leisure"]({S},{W},{N},{E});
  nwr["natural"="beach"]({S},{W},{N},{E});
  nwr["amenity"="place_of_worship"]({S},{W},{N},{E});
);
out geom tags;
"""


def overpass():
    corpo = urllib.parse.urlencode({'data': CONSULTA}).encode()
    for url in ('https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter',
                'https://maps.mail.ru/osm/tools/overpass/api/interpreter', 'https://overpass.kumi.systems/api/interpreter'):
        try:
            req = urllib.request.Request(url, data=corpo, headers=UA)
            dados = urllib.request.urlopen(req, timeout=180).read()
            json.loads(dados)
            open(os.path.join(PASTA, 'osm.json'), 'wb').write(dados)
            print('osm', url, len(dados) // 1024, 'KB')
            return
        except Exception as e:
            print('falhou', url, e)
    raise SystemExit('sem dados do OpenStreetMap')


def tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def relevo(z=14):
    x0, y0 = tile(N, W, z)
    x1, y1 = tile(S, E, z)
    for tx in range(int(x0), int(x1) + 1):
        for ty in range(int(y0), int(y1) + 1):
            dest = os.path.join(PASTA, f'dem-{z}-{tx}-{ty}.png')
            if os.path.exists(dest):
                continue
            url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png'
            open(dest, 'wb').write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
            print('dem', z, tx, ty)


if __name__ == '__main__':
    overpass()
    relevo()
