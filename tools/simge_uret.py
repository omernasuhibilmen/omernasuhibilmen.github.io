# -*- coding: utf-8 -*-
"""favicon.svg ile aynı geometriyi (ÖNB monogramı) PNG/ICO üretir (yalnız stdlib).

    python3 tools/simge_uret.py
"""
import os
import struct
import zlib

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZEMIN = (0x8a, 0x5a, 0x1c)
KAGIT = (0xfb, 0xf9, 0xf5)
KAT = 4          # kenar yumuşatma için üst örnekleme


def _seg(x, y, ax, ay, bx, by):
    """Noktanın [a,b] doğru parçasına uzaklığı."""
    dx, dy = bx - ax, by - ay
    uz = dx * dx + dy * dy
    t = 0.0 if uz == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / uz))
    return ((x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2) ** 0.5


def _cember(x, y, cx, cy, r):
    return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 - r


KALINLIK = 2.0          # çizgi yarıçapı (stroke-width 4)


def _kapsam(x, y):
    """favicon.svg ile aynı geometri: (zemin, harf) örtüşmesi."""
    # köşeleri yuvarlatılmış kare (r = 14)
    kx = 14 if x < 14 else 50 if x > 50 else None
    ky = 14 if y < 14 else 50 if y > 50 else None
    if kx is not None and ky is not None:
        ic = ((x - kx) ** 2 + (y - ky) ** 2) <= 14 * 14
    else:
        ic = 0 <= x <= 64 and 0 <= y <= 64
    if not ic:
        return 0, False

    harf = False
    # Ö — halka ve iki nokta
    if abs(_cember(x, y, 17, 35, 8)) <= KALINLIK:
        harf = True
    if _cember(x, y, 13.5, 20, 1.9) <= 0 or _cember(x, y, 20.5, 20, 1.9) <= 0:
        harf = True
    # N — iki dikey ve köşegen; ardından B'nin dikey çizgisi
    for ax, ay, bx, by in ((32, 25, 32, 45),
                           (43, 25, 43, 45),
                           (32, 25, 43, 45),
                           (49.5, 25, 49.5, 45)):
        if _seg(x, y, ax, ay, bx, by) <= KALINLIK:
            harf = True
    # B — sağa bakan iki yarım halka (uçları yuvarlak)
    for cy in (30, 40):
        if x >= 49.5 and abs(_cember(x, y, 49.5, cy, 5)) <= KALINLIK:
            harf = True
    for uy in (25, 35, 45):
        if _cember(x, y, 49.5, uy, KALINLIK) <= 0:
            harf = True
    return 1, harf


def _kapsam_kucuk(x, y):
    """16 px'te üç harf okunmaz; o boyda yalnız büyük bir Ö çizilir."""
    kx = 14 if x < 14 else 50 if x > 50 else None
    ky = 14 if y < 14 else 50 if y > 50 else None
    if kx is not None and ky is not None:
        ic = ((x - kx) ** 2 + (y - ky) ** 2) <= 14 * 14
    else:
        ic = 0 <= x <= 64 and 0 <= y <= 64
    if not ic:
        return 0, False
    harf = (abs(_cember(x, y, 32, 38, 12.5)) <= 3.25
            or _cember(x, y, 25, 13, 3.4) <= 0
            or _cember(x, y, 39, 13, 3.4) <= 0)
    return 1, harf


def piksel(boy):
    kapsam = _kapsam_kucuk if boy <= 16 else _kapsam
    olcek = 64 / boy
    satirlar = []
    for py in range(boy):
        satir = bytearray()
        for px in range(boy):
            zs = hs = 0
            for sy in range(KAT):
                for sx in range(KAT):
                    x = (px + (sx + .5) / KAT) * olcek
                    y = (py + (sy + .5) / KAT) * olcek
                    ic, harf = kapsam(x, y)
                    zs += ic
                    hs += harf
            n = KAT * KAT
            a = zs / n
            h = hs / n
            if a == 0:
                satir += bytes((0, 0, 0, 0))
            else:
                renk = tuple(round(ZEMIN[i] * (1 - h) + KAGIT[i] * h) for i in range(3))
                satir += bytes(renk) + bytes((round(a * 255),))
        satirlar.append(bytes(satir))
    return satirlar


def png(boy):
    satirlar = piksel(boy)
    ham = b''.join(b'\x00' + s for s in satirlar)

    def yigin(tur, veri):
        g = tur + veri
        return struct.pack('>I', len(veri)) + g + struct.pack('>I', zlib.crc32(g))

    return (b'\x89PNG\r\n\x1a\n'
            + yigin(b'IHDR', struct.pack('>IIBBBBB', boy, boy, 8, 6, 0, 0, 0))
            + yigin(b'IDAT', zlib.compress(ham, 9))
            + yigin(b'IEND', b''))


def ico(boyutlar):
    goruntuler = [png(b) for b in boyutlar]
    bas = struct.pack('<HHH', 0, 1, len(goruntuler))
    ofset = 6 + 16 * len(goruntuler)
    girdiler = b''
    for b, g in zip(boyutlar, goruntuler):
        girdiler += struct.pack('<BBBBHHII', b % 256, b % 256, 0, 0, 1, 32,
                                len(g), ofset)
        ofset += len(g)
    return bas + girdiler + b''.join(goruntuler)


if __name__ == '__main__':
    open(os.path.join(KOK, 'favicon.ico'), 'wb').write(ico([16, 32, 48]))
    open(os.path.join(KOK, 'apple-touch-icon.png'), 'wb').write(png(180))
    print('favicon.ico ve apple-touch-icon.png yazıldı')
