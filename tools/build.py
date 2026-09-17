# -*- coding: utf-8 -*-
"""omernasuhibilmen.github.io — v2.0 site üreteci.

Kaynak: tools/kaynak/ altındaki v1 HTML dosyaları (ilk çalıştırmada proje
kökünden kopyalanır). Çıktı: proje kökündeki index.html, about.html ve
articles/*.html dosyaları.

    python3 tools/build.py

Yeniden çalıştırmak güvenlidir; çıktı her seferinde kaynaktan üretilir.
"""
import collections
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BASE)
KAYNAK = os.path.join(BASE, 'kaynak')
sys.path.insert(0, BASE)
import dia  # noqa: E402

DUZELTME = os.path.join(BASE, 'arapca-duzeltmeler.json')
SITE = 'https://omernasuhibilmen.github.io'
YAZARLAR = 'Ahmet Şengül, Mevlüt Çelik'
SURUM = '2.0'

AYLAR = {'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'haziran': 6,
         'temmuz': 7, 'ağustos': 8, 'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12}
DIL_ADI = {'ottoman': 'Osmanlı Türkçesi', 'turkish': 'Türkçe'}

# Makalelerin neşredildiği süreli yayınlar (yüzey yazımı -> künye adı)
DERGILER = [
    (r'Bey[âa]n[üu][\s\'’-]*l[\s\'’-]*[Hh]a[kḳ]', 'Beyânü’l-Hak'),
    (r'Sebil[üu]rre[şs][âa]?d', 'Sebîlürreşâd'),
    (r'İsl[âa]m[\'’]?[ıi]n N[ûu]ru', 'İslâm’ın Nûru'),
    (r'İsl[âa]m Yolu', 'İslâm Yolu'),
    (r'Sel[âa]met', 'Selâmet'),
    (r'Hil[âa]l', 'Hilâl'),
    (r'Mahfil', 'Mahfil'),
    (r'Medrese İtikad', 'Medrese İtikadları'),
    (r'Muhit[üu]lmaarif|İsl[âa]m[\s-]*T[üu]rk Ansiklopedisi',
     'İslâm-Türk Ansiklopedisi Muhitülmaarif Mecmuası'),
    (r'İtis[âa]m', 'İtisâm'),
    (r'İhlas', 'İhlas'),
]


def dergi_bul(ham):
    """Makalenin ham metninden süreli yayın adını ve künye sayılarını çıkarır."""
    metin = duz(ham)
    ad = None
    for kalip, isim in DERGILER:
        if re.search(kalip, metin, re.I):
            ad = isim
            break
    def _say(kalip):
        m = re.search(kalip, metin)
        return m.group(1) if m else None
    return {
        'ad': ad,
        'cilt': _say(r'(\d+)\.\s*[Cc]ilt'),
        'sayi': _say(r'(\d+)\.\s*[Ss]ayı'),
        'sayfa': _say(r'(\d+)\.\s*[Ss]ayfa'),
    }


# --------------------------------------------------------------------------- #
# Kaynak yönetimi
# --------------------------------------------------------------------------- #
def duzeltmeler_yukle():
    """Arapça/Farsça pasajlar için elle doğrulanmış onarımlar."""
    if not os.path.exists(DUZELTME):
        return {}
    kayit = {}
    with open(DUZELTME, encoding='utf-8') as fh:
        for d in json.load(fh):
            kayit.setdefault(d['dosya'], []).append(d)
    return kayit


DUZELTMELER = duzeltmeler_yukle()


def duzeltme_uygula(ham, dosya):
    """Onarımları uygular; her kalıp tam bir kez eşleşmezse hata verir."""
    notlar = []
    for d in DUZELTMELER.get(dosya, []):
        sayi = ham.count(d['ara'])
        if sayi != 1:
            raise SystemExit(
                'DÜZELTME EŞLEŞMEDİ: %s / %s (%d kez bulundu). '
                'Kaynak değiştiyse tools/arapca-duzeltmeler.json güncellenmeli.'
                % (dosya, d['baslik'], sayi))
        ham = ham.replace(d['ara'], d['yaz'])
        notlar.append(d)
    return ham, notlar


def kaynak_hazirla():
    """v1 dosyalarını bir kereye mahsus tools/kaynak/ altına al."""
    if os.path.isdir(KAYNAK):
        return
    os.makedirs(os.path.join(KAYNAK, 'articles'))
    for ad in ('index.html', 'about.html'):
        shutil.copy2(os.path.join(KOK, ad), os.path.join(KAYNAK, ad))
    for ad in sorted(os.listdir(os.path.join(KOK, 'articles'))):
        if ad.endswith('.html'):
            shutil.copy2(os.path.join(KOK, 'articles', ad),
                         os.path.join(KAYNAK, 'articles', ad))
    print('  v1 kaynakları tools/kaynak/ altına alındı.')


# --------------------------------------------------------------------------- #
# Yardımcılar
# --------------------------------------------------------------------------- #
ETIKETSIZ = re.compile(r'<[^>]+>')
RTL_PARCA = re.compile(r'(<span[^>]*dir="rtl"[^>]*>.*?</span>)', re.S)


_DIA_DUZ = {0x1e25:'h',0x1e24:'h',0x1e2b:'h',0x1e2a:'h',0x1e95:'z',0x1e94:'z',
            0x1e63:'s',0x1e62:'s',0x17c:'z',0x17b:'z',0x1e0d:'d',0x1e0c:'d',
            0x1e6d:'t',0x1e6c:'t',0x1e93:'z',0x1e92:'z',0x121:'g',0x120:'g',
            0x1e33:'k',0x1e32:'k',0x2bf:'',0x2be:'',0x2018:'',0x2019:'',0x27:''}


def kiyas(s):
    """Başlık karşılaştırması için: transkripsiyon işaretlerini ve aksanları düşür."""
    s = duz(s).replace('I', 'ı').replace('İ', 'i').lower().translate(_DIA_DUZ)
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9çğıöşü]', '', s)


def duz(s):
    return re.sub(r'\s+', ' ', html.unescape(ETIKETSIZ.sub('', s))).strip()


def tarih_coz(metin):
    """'7 Şubat 1911' -> ('1911-02-07', 1911). Çözülemezse ('', 0)."""
    m = re.search(r'(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})', metin)
    if m:
        ay = AYLAR.get(m.group(2).lower().replace('I', 'ı'))
        if ay:
            return '%s-%02d-%02d' % (m.group(3), ay, int(m.group(1))), int(m.group(3))
    m = re.search(r'(\d{4})', metin)
    return (m.group(1), int(m.group(1))) if m else ('', 0)


# Kaynak metinde virgül/noktalı virgülden sonra boşluk sık sık düşmüş.
# Yalnız iki harf arasında kalan işaretler düzeltilir; "1,5" veya "http://"
# gibi durumlara dokunulmaz.
NOKTALAMA = re.compile(r'(?<=[^\W\d_])([,;:])(?=[^\W\d_])')


def noktalama_duzelt(metin):
    return NOKTALAMA.sub(r'\1 ', metin)


def cevir_html(parca, dia_uygula=True):
    """HTML parçasındaki metin düğümlerini çevirir; etiketleri ve Arapçayı atlar."""
    cikti, acik_tirnak = [], False
    for bolum in RTL_PARCA.split(parca):
        if bolum.startswith('<span') and 'dir="rtl"' in bolum[:40]:
            cikti.append(bolum)
            continue
        alt = []
        for kesit in re.split(r'(<[^>]+>)', bolum):
            if kesit.startswith('<'):
                alt.append(kesit)
                continue
            metin = noktalama_duzelt(html.unescape(kesit))
            if dia_uygula:
                metin = dia.metin_cevir(metin)
            metin, acik_tirnak = dia.tirnak_onar(metin)
            alt.append(html.escape(metin, quote=False))
        cikti.append(''.join(alt))
    return ''.join(cikti)


# --------------------------------------------------------------------------- #
# İçerik temizliği
# --------------------------------------------------------------------------- #
def metin_notu(notlar):
    if not notlar:
        return ''
    satir = []
    for d in notlar:
        satir.append('      <li><b>%s.</b> %s</li>' % (d['baslik'], html.escape(d['gerekce'])))
    return ('\n  <section class="metin-notu" aria-labelledby="metin-notu-baslik">\n'
            '    <h2 id="metin-notu-baslik">Metin notu</h2>\n'
            '    <p>Bu makalenin kaynak dosyasında Arapça ve Farsça pasajlar, vaktiyle '
            'PDF’ten kopyalanırken bozulmuştur: harflerin bir kısmı font glifleriyle '
            'yer değiştirmiş, harekeler harflerinden kopmuştur. Aşağıdaki pasajlar '
            'makalenin kendi tercümeleri ve dipnotlarındaki künyeler esas alınarak '
            'onarılmış, metinde <span class="onarildi">noktalı çizgiyle</span> '
            'işaretlenmiştir. Asıl dergi sayfasından teyit edilmeleri beklemektedir.</p>\n'
            '    <ul>\n' + '\n'.join(satir) + '\n    </ul>\n  </section>')


def icerik_ayikla(ham, baslik):
    """Makale gövdesini ayıklar; mükerrer başlıkları, dipnotları ve imzayı ayırır."""
    m = re.search(r'<div class="content">(.*?)\n\s*</div>\s*</article>', ham, re.S)
    govde = m.group(1) if m else ''

    dipnotlar = {}

    # 1) pandoc'un ürettiği dipnot bölümü
    def _bolum(mm):
        for li in re.finditer(r'<li id="fn(\d+)">(.*?)</li>', mm.group(0), re.S):
            dipnotlar[int(li.group(1))] = li.group(2)
        return ''
    govde = re.sub(r'<section[^>]*class="footnotes[^"]*"[^>]*>.*?</section>',
                   _bolum, govde, flags=re.S)

    # 2) <p><sup>N</sup> ...</p> biçimindeki dipnot tanımları
    def _paragraf(mm):
        dipnotlar.setdefault(int(mm.group(1)), '<p>%s</p>' % mm.group(2).strip())
        return ''
    govde = re.sub(r'<p><sup>(\d+)</sup>(.*?)</p>', _paragraf, govde, flags=re.S)

    # 3) gövdedeki mükerrer başlıklar (sup dipnot çağrısı korunur)
    bnorm = kiyas(baslik)
    basliktaki_sup = []

    def _h1(mm):
        icerik = mm.group(1)
        norm = kiyas(icerik)
        if norm and (norm.startswith(bnorm[:14]) or bnorm.startswith(norm[:14])):
            basliktaki_sup.extend(re.findall(r'<sup>(\d+)</sup>', icerik))
            return ''
        return '<h2>%s</h2>' % icerik
    govde = re.sub(r'<h1[^>]*>(.*?)</h1>', _h1, govde, flags=re.S)

    # 4) pandoc geri bağlantılarını ve boş kalıntıları at
    govde = re.sub(r'<a\s[^>]*href="#fnref\d*"[^>]*>.*?</a>', '', govde, flags=re.S)
    govde = re.sub(r'<a\s[^>]*href="#fn(\d+)"[^>]*>\s*<sup>.*?</sup>\s*</a>',
                   lambda mm: '<sup>%s</sup>' % mm.group(1), govde, flags=re.S)
    govde = re.sub(r'<p>\s*</p>', '', govde)
    govde = re.sub(r'<blockquote>\s*</blockquote>', '', govde)
    govde = re.sub(r'\n{3,}', '\n\n', govde).strip()

    # 5) imza paragrafı
    imza = ''
    son = list(re.finditer(r'<p>((?:(?!</p>).)*)</p>\s*$', govde, re.S))
    if son:
        ic = duz(son[0].group(1))
        if len(ic) < 90 and re.search(r'(Ömer Nasuhi|Nasûhi|Erzurumlu)', ic):
            imza = ic
            govde = govde[:son[0].start()].rstrip()

    return govde, dipnotlar, basliktaki_sup, imza


KUNYE_IZ = re.compile(
    r'(Sayı|Cilt|Sayfa|Dergi|Hicr[îi]|R[ûu]m[îi]|Mecm[ûu]|Beyân[üu]|Beyan[üu]|'
    r'Sebil[üu]rre|İsl[âa]m[ıi]n N[ûu]ru|İsl[âa]m Yolu|Sel[âa]met|Hil[âa]l|Mahfil|'
    r'Medrese İtikad|İsl[âa]m-T[üu]rk|İtis[âa]m|Hayr|İhlas)')
AY_IZ = re.compile(
    r'\b(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\b'
    r'[^0-9]{0,4}\d{4}|\d{1,2}\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|'
    r'Eylül|Ekim|Kasım|Aralık)\s+\d{4}')


def kunye_ayikla(govde, baslik):
    """Gövdenin başındaki mükerrer başlık ve künye paragraflarını ayırır."""
    bnorm = kiyas(baslik)
    satirlar, supler = [], []
    while True:
        m = re.match(r'\s*<(p|h2)>((?:(?!</\1>).)*)</\1>', govde, re.S)
        if not m:
            break
        ic = duz(m.group(2))
        norm = kiyas(ic)
        n = min(12, len(bnorm), len(norm))
        baslikla_ayni = bool(n >= 3 and norm[:n] == bnorm[:n])
        kunye = len(ic) < 190 and (KUNYE_IZ.search(ic) or AY_IZ.search(ic))
        if not (baslikla_ayni or kunye):
            break
        if baslikla_ayni:
            supler.extend(re.findall(r'<sup>(\d+)</sup>', m.group(2)))
        if kunye and not baslikla_ayni:
            temiz = re.sub(r'^[\s\-–—]+|[\s\-–—]+$', '', ic)
            if temiz and all(kiyas(temiz) != kiyas(v) for v in satirlar):
                satirlar.append(temiz)
        govde = govde[m.end():]
    return govde.lstrip(), satirlar, supler


def arapca_isaretle(govde):
    """Ağırlıklı olarak Arap harfli paragraflara ayrı bir sınıf verir."""
    def _p(mm):
        ic = mm.group(1)
        duz_ic = ETIKETSIZ.sub('', ic)
        ar = sum(1 for c in duz_ic if 0x0600 <= ord(c) <= 0x06FF
                 or 0xFB50 <= ord(c) <= 0xFEFF)
        lat = sum(1 for c in duz_ic if c.isalpha() and ord(c) < 0x0500)
        if ar >= 6 and ar > lat * 3:
            return '<p class="arapca" dir="rtl">%s</p>' % ic
        return mm.group(0)
    return re.sub(r'<p>((?:(?!</p>).)*)</p>', _p, govde, flags=re.S)


def gorsel_duzelt(govde):
    """Makale içi görselleri: yolu düzelt, alt metni ve tembel yüklemeyi ekle."""
    sayac = [0]

    def _img(mm):
        etiket = mm.group(0)
        etiket = re.sub(r'src="(?!\.\./|https?:|data:)', 'src="../', etiket)
        if not re.search(r'\salt=', etiket):
            sayac[0] += 1
            etiket = etiket.replace(
                '<img', '<img alt="Makalenin dergide yayımlanmış asıl sayfası '
                        '(tarama %d)"' % sayac[0], 1)
        if 'loading=' not in etiket:
            etiket = etiket.replace('<img', '<img loading="lazy" decoding="async"', 1)
        return etiket
    return re.sub(r'<img[^>]*>', _img, govde)


def dipnot_bagla(govde, dipnotlar):
    """Gövdedeki <sup>N</sup> çağrılarını dipnotlara bağlar."""
    def _sup(mm):
        n = int(mm.group(1))
        if n not in dipnotlar:
            return mm.group(0)
        return ('<sup class="dipnot-baglanti"><a id="dnr-%d" href="#dn-%d" '
                'aria-describedby="dipnotlar-baslik">%d</a></sup>' % (n, n, n))
    return re.sub(r'<sup>(\d+)</sup>', _sup, govde)


def dipnot_bolumu(dipnotlar):
    if not dipnotlar:
        return ''
    satir = []
    for n in sorted(dipnotlar):
        ic = dipnotlar[n].strip()
        ic = re.sub(r'<a\s[^>]*href="#fnref\d*"[^>]*>.*?</a>', '', ic, flags=re.S)
        ic = cevir_html(ic)
        satir.append(
            '      <li id="dn-%d">%s <a class="geri-don" href="#dnr-%d" '
            'aria-label="Metne dön">↩</a></li>' % (n, ic, n))
    return ('\n  <section class="dipnotlar" aria-labelledby="dipnotlar-baslik">\n'
            '    <h2 id="dipnotlar-baslik">Dipnotlar</h2>\n    <ol>\n'
            + '\n'.join(satir) + '\n    </ol>\n  </section>')


# --------------------------------------------------------------------------- #
# Şablonlar
# --------------------------------------------------------------------------- #
TEMA_BETIK = ('<script>(function(){try{var t=localStorage.getItem("onb-tema");'
              'if(t)document.documentElement.setAttribute("data-tema",t);}'
              'catch(e){}})();</script>')

def kafa(baslik, aciklama, kanonik, kok_yol, ekstra=''):
    og_tur = ('' if 'og:type' in ekstra else
              '<meta property="og:type" content="website">')
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{baslik}</title>
<meta name="description" content="{aciklama}">
<meta name="author" content="{YAZARLAR}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="google-site-verification" content="9cCQLKYW6Y48flUiAfRjKjiKEXyiHMSdoUobmq738SE">
<link rel="canonical" href="{kanonik}">
{og_tur}
<meta property="og:locale" content="tr_TR">
<meta property="og:site_name" content="Ömer Nasûhi Bilmen — Makaleler">
<meta property="og:title" content="{baslik}">
<meta property="og:description" content="{aciklama}">
<meta property="og:url" content="{kanonik}">
<meta property="og:image" content="{SITE}/omer-nasuhi-bilmen.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{baslik}">
<meta name="twitter:description" content="{aciklama}">
<meta name="twitter:image" content="{SITE}/omer-nasuhi-bilmen.jpg">
<meta name="theme-color" content="#fbf9f5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14120f" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{kok_yol}favicon.ico" sizes="32x32">
<link rel="icon" href="{kok_yol}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{kok_yol}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gentium+Book+Plus:ital,wght@0,400;0,700;1,400;1,700&amp;display=swap">
<link rel="stylesheet" href="{kok_yol}css/v2.css?v={SURUM}">
{TEMA_BETIK}{ekstra}
</head>
<body>
<a class="atla" href="#icerik">İçeriğe geç</a>
'''


def ust_cubuk(kok_yol, aktif):
    def im(ad, yol, etiket):
        gecerli = ' aria-current="page"' if aktif == ad else ''
        return f'      <a href="{kok_yol}{yol}"{gecerli}>{etiket}</a>'
    return f'''<header class="ust">
  <div class="kap ust__ic">
    <a class="marka" href="{kok_yol}index.html">
      Ömer Nasûhi Bilmen
      <span>Makaleler Arşivi</span>
    </a>
    <nav class="gezinti" aria-label="Ana menü">
{im('arsiv', 'index.html#arsiv', 'Makaleler')}
{im('hakkinda', 'about.html', 'Hayatı')}
    </nav>
    <button class="tema-dugme" type="button" data-tema-dugme aria-label="Temayı değiştir">
      <svg class="gunes" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2M12 19.4v2M2.6 12h2M19.4 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M18.7 5.3l-1.4 1.4M6.7 17.3l-1.4 1.4"/></svg>
      <svg class="ay" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.3A8.5 8.5 0 1 1 9.7 3.5a6.8 6.8 0 0 0 10.8 10.8Z"/></svg>
    </button>
  </div>
</header>
'''


def alt_bilgi(kok_yol):
    return f'''<footer class="alt">
  <div class="kap alt__ic">
    <p>Hazırlayanlar: {YAZARLAR}</p>
    <div class="alt__baglanti">
      <a href="{kok_yol}index.html#arsiv">Makaleler</a>
      <a href="{kok_yol}about.html">Hayatı</a>
      <a href="https://github.com/mevlut-celik" rel="noopener">GitHub</a>
    </div>
  </div>
</footer>
<button class="yukari" type="button" data-yukari aria-label="Sayfa başına dön">
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
</button>
<script src="{kok_yol}js/app.js?v={SURUM}" defer></script>
</body>
</html>
'''


# --------------------------------------------------------------------------- #
# Sayfalar
# --------------------------------------------------------------------------- #
def meta_oku():
    ham = open(os.path.join(KAYNAK, 'index.html'), encoding='utf-8').read()
    kartlar = re.findall(
        r'<div class="col-md-6 col-lg-4" data-category="(\w+)">\s*<a href="([^"]+)"'
        r'[^>]*>.*?<h3[^>]*>\s*<i[^>]*></i>(.*?)</h3>.*?'
        r'<i class="bi bi-calendar3 me-2"></i>\s*(.*?)\s*</p>', ham, re.S)
    kayit = []
    for dil, yol, baslik, tarih in kartlar:
        baslik = duz(baslik)
        iso, yil = tarih_coz(tarih)
        kayit.append({
            'dil': dil,
            'yol': yol,
            'dosya': os.path.basename(yol),
            'baslik_ham': baslik,
            'baslik': dia.tirnak_onar(dia.metin_cevir(baslik))[0],
            'tarih': duz(tarih),
            'iso': iso,
            'yil': yil,
        })
    kayit.sort(key=lambda k: (k['iso'] or '0000'), reverse=True)
    return kayit


def makale_yaz(k, onceki, sonraki):
    ham = open(os.path.join(KAYNAK, 'articles', k['dosya']), encoding='utf-8').read()
    k['dergi'] = dergi_bul(ham)
    ham, notlar = duzeltme_uygula(ham, k['dosya'])
    govde, dipnotlar, baslik_sup, imza = icerik_ayikla(ham, k['baslik_ham'])
    govde = cevir_html(govde)
    govde, kunye, ek_sup = kunye_ayikla(govde, k['baslik'])
    baslik_sup = baslik_sup + ek_sup
    govde = dipnot_bagla(govde, dipnotlar)
    govde = gorsel_duzelt(govde)
    govde = arapca_isaretle(govde)
    imza = dia.tirnak_onar(dia.metin_cevir(imza))[0] if imza else ''

    kanonik = f"{SITE}/articles/{k['dosya']}"
    ozet = f"{k['baslik']} — Ömer Nasûhi Bilmen'in {k['tarih']} tarihli yazısı. " \
           f"{DIL_ADI[k['dil']]} aslından DİA transkripsiyonuyla."
    baslik_sup_html = ''
    if baslik_sup and int(baslik_sup[0]) in dipnotlar:
        n = int(baslik_sup[0])
        baslik_sup_html = (f'<sup class="dipnot-baglanti"><a id="dnr-{n}" href="#dn-{n}">'
                           f'{n}</a></sup>')

    dg = k['dergi']
    kismi = ''
    if dg['ad']:
        sayi_alan = ''
        if dg['sayi']:
            sayi_alan += ',"issueNumber":"%s"' % dg['sayi']
        if dg['cilt']:
            sayi_alan += (',"isPartOf":{"@type":"PublicationVolume",'
                          '"volumeNumber":"%s","isPartOf":{"@type":"Periodical",'
                          '"name":%s}}' % (dg['cilt'], _js(dg['ad'])))
        else:
            sayi_alan += ',"isPartOf":{"@type":"Periodical","name":%s}' % _js(dg['ad'])
        kismi = ('"isPartOf":{"@type":"PublicationIssue"%s},' % sayi_alan)
        if dg['sayfa']:
            kismi += '"pagination":"%s",' % dg['sayfa']

    jsonld = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Article",
"@id":"{kanonik}#makale",
"headline":{_js(k['baslik'])},
"name":{_js(k['baslik'])},
"datePublished":"{k['iso']}",
"inLanguage":"tr",
"isAccessibleForFree":true,
"articleSection":{_js(DIL_ADI[k['dil']])},
{kismi}"author":{{"@type":"Person","name":"Ömer Nasûhi Bilmen",
  "birthDate":"1883","deathDate":"1971-10-12",
  "sameAs":"https://islamansiklopedisi.org.tr/bilmen-omer-nasuhi"}},
"publisher":{{"@type":"Organization","name":"Ömer Nasûhi Bilmen Makaleler Arşivi",
  "url":"{SITE}/"}},
"mainEntityOfPage":"{kanonik}"}},
{{"@type":"BreadcrumbList","itemListElement":[
 {{"@type":"ListItem","position":1,"name":"Ana sayfa","item":"{SITE}/"}},
 {{"@type":"ListItem","position":2,"name":"Makaleler","item":"{SITE}/#arsiv"}},
 {{"@type":"ListItem","position":3,"name":{_js(k['baslik'])},"item":"{kanonik}"}}]}}
]}}
</script>'''

    komsu = []
    if onceki:
        komsu.append(f'''  <a href="{onceki['dosya']}" rel="prev">
    <small>Önceki (daha yeni)</small>
    <strong>{onceki['baslik']}</strong>
  </a>''')
    if sonraki:
        komsu.append(f'''  <a href="{sonraki['dosya']}" rel="next">
    <small>Sonraki (daha eski)</small>
    <strong>{sonraki['baslik']}</strong>
  </a>''')
    kunye_html = ''
    if kunye:
        kunye_html = ('      <ul class="kunye" aria-label="Neşir künyesi">\n'
                      + '\n'.join('        <li>%s</li>' % x for x in kunye)
                      + '\n      </ul>')

    dergi_satiri = ''
    if k['dergi']['ad']:
        parca = [k['dergi']['ad']]
        if k['dergi']['cilt']:
            parca.append(k['dergi']['cilt'] + '. cilt')
        if k['dergi']['sayi']:
            parca.append(k['dergi']['sayi'] + '. sayı')
        if k['dergi']['sayfa']:
            parca.append('s. ' + k['dergi']['sayfa'])
        dergi_satiri = ', '.join(parca) + ', ' + k['tarih'] + '. '

    baski_altbilgi = (
        '    <div class="baski-yalniz baski-altbilgi">\n'
        '      <p><b>Kaynak künyesi.</b> Ömer Nasûhi Bilmen, &#8220;%s&#8221;, %s</p>\n'
        '      <p>Bu metin <b>Ömer Nasûhi Bilmen Makaleler Arşivi</b>&#8217;nden '
        'alınmıştır: <b>%s</b></p>\n'
        '      <p>Osmanlıca kelimeler TDV İslâm Ansiklopedisi (DİA) transkripsiyon '
        'alfabesiyle gösterilmiştir. Yayına hazırlayanlar: %s.</p>\n'
        '    </div>' % (k['baslik'], dergi_satiri, kanonik, YAZARLAR))

    komsu_html = ('\n<nav class="komsu" aria-label="Diğer makaleler">\n'
                  + '\n'.join(komsu) + '\n</nav>') if komsu else ''

    icerik = f'''<div class="ilerleme" data-ilerleme aria-hidden="true"></div>
{ust_cubuk('../', 'arsiv')}
<main id="icerik" class="makale">
<div class="kap makale__kap">

  <a class="geri" href="../index.html#arsiv">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>
    Bütün makaleler
  </a>

  <article>
    <div class="baski-yalniz baski-ustbilgi" aria-hidden="true">
      <b>Ömer Nasûhi Bilmen · Makaleler Arşivi</b>
      <span>omernasuhibilmen.github.io</span>
    </div>

    <header class="makale__ust">
      <span class="rozet rozet--{k['dil']}">{DIL_ADI[k['dil']]}</span>
      <h1>{k['baslik']}{baslik_sup_html}</h1>
      <p class="makale__meta">
        <span class="yazar">Ömer Nasûhi Bilmen</span>
        <time datetime="{k['iso']}">{k['tarih']}</time>
      </p>
{kunye_html}
    </header>

    <div class="okuma-araclari">
      <span>Okuma</span>
      <button type="button" data-boyut aria-pressed="false">
        Yazı boyutu:<span data-boyut-etiket>Normal</span>
      </button>
      <button type="button" data-sade aria-pressed="false">
        Transkripsiyonu sadeleştir
      </button>
      <button type="button" data-pdf>
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v11m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>
        PDF olarak indir
      </button>
    </div>

    <div class="metin" data-metin>
{govde}
    </div>
{f'    <p class="imza">{imza}</p>' if imza else ''}
{dipnot_bolumu(dipnotlar)}
{metin_notu(notlar)}
{baski_altbilgi}
  </article>
{komsu_html}
</div>
</main>
{alt_bilgi('../')}'''

    og_ek = (f'<meta property="og:type" content="article">\n'
             f'<meta property="article:published_time" content="{k["iso"]}">\n'
             f'<meta property="article:author" content="Ömer Nasûhi Bilmen">\n'
             f'<meta property="article:section" content="{DIL_ADI[k["dil"]]}">')
    sayfa = kafa(f"{k['baslik']} — Ömer Nasûhi Bilmen", html.escape(ozet, quote=True),
                 kanonik, '../', '\n' + og_ek + '\n' + jsonld) + icerik
    with open(os.path.join(KOK, 'articles', k['dosya']), 'w', encoding='utf-8') as fh:
        fh.write(sayfa)


def _js(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def dergi_rozeti(k):
    d = k.get('dergi') or {}
    if not d.get('ad'):
        return ''
    return '<span class="kart__dergi">%s</span>' % html.escape(d['ad'])


def zaman_serisi(kayit):
    """Yıllara göre makale dağılımı: hem görsel hem süzgeç."""
    yillar = [k['yil'] for k in kayit if k['yil']]
    if not yillar:
        return ''
    ilk, son = min(yillar), max(yillar)
    sayim = collections.Counter(yillar)
    enbuyuk = max(sayim.values())
    cubuk = []
    for y in range(ilk, son + 1):
        n = sayim.get(y, 0)
        if n:
            cubuk.append(
                '      <li><button type="button" data-yil="%d" aria-pressed="false" '
                'style="--oran:%.3f" title="%d — %d makale">'
                '<span class="gizli-gorsel">%d yılı, %d makale</span></button></li>'
                % (y, max(.16, n / enbuyuk), y, n, y, n))
        else:
            cubuk.append('      <li><span class="bos" aria-hidden="true"></span></li>')
    return ('''
    <div class="zaman-serisi">
      <p class="zaman-serisi__baslik" id="zaman-serisi-baslik">Yıllara göre dağılım
        <span>— bir yıla tıklayarak süzebilirsiniz</span></p>
      <ol class="zaman-serisi__cubuklar" role="group" aria-labelledby="zaman-serisi-baslik">
''' + '\n'.join(cubuk) + '''
      </ol>
      <div class="zaman-serisi__eksen"><span>%d</span><span>%d</span></div>
    </div>''' % (ilk, son))


def anasayfa_yaz(kayit):
    osmanli = sum(1 for k in kayit if k['dil'] == 'ottoman')
    turkce = len(kayit) - osmanli
    yillar = [k['yil'] for k in kayit if k['yil']]
    aralik = f'{min(yillar)}–{max(yillar)}' if yillar else ''

    kartlar = []
    for k in kayit:
        kartlar.append(f'''    <li class="kart" data-dil="{k['dil']}" data-yil="{k['yil']}" data-dil-adi="{DIL_ADI[k['dil']]}">
      <a href="{k['yol']}">
        <span class="rozet rozet--{k['dil']}">{DIL_ADI[k['dil']]}</span>
        <h3>{k['baslik']}</h3>
        <p class="kart__alt">
          <time datetime="{k['iso']}">{k['tarih']}</time>
          {dergi_rozeti(k)}
        </p>
      </a>
    </li>''')

    giris = '''Ömer Nasûhi Bilmen hazretleri Osmanlı Devleti’nde doğmuş, kendisini
yetiştirmiş ve Cumhuriyet devri ilk dönem ulemâmızın önemli şahsiyetlerinden birisi
olmuştur. Hem talebeliği hem de muallimliği vakitlerinde çeşitli makaleler te’lîf
etmiş, bu makaleler muhtelif dergilerde Osmanlıca veya Türkçe olarak neşredilmiştir.
Lâkin günümüzde temiz bir baskısı ne yazık ki bulunmamaktadır.'''
    giris2 = '''Biz de nâçizâne kendimizi hazretin fahrî talebesi olarak gördüğümüzden
makalelerini yayına hazırlamaya karar verdik. Metinler hem latinize edilerek hem de
latin harflerinden temize çekilerek hazırlanmakta; Osmanlıca kelimeler TDV İslâm
Ansiklopedisi (DİA) transkripsiyon alfabesiyle gösterilmektedir.
Niyâzımız o ola ki istifâdeli olsun.'''

    icerik = f'''{ust_cubuk('', 'anasayfa')}
<main id="icerik">

<section class="giris">
  <div class="kap giris__izgara">
    <div class="giris__gorsel">
      <img src="omer-nasuhi-bilmen.jpg" width="800" height="1000"
           alt="Ömer Nasûhi Bilmen’in portre fotoğrafı" fetchpriority="high">
    </div>
    <div>
      <p class="giris__ustbaslik">Makaleler Arşivi · v{SURUM}</p>
      <h1>Ömer Nasûhi Bilmen</h1>
      <p>{giris}</p>
      <p>{giris2}</p>
      <div class="giris__eylem">
        <a class="dugme dugme--dolu" href="#arsiv">Makaleleri incele</a>
        <a class="dugme dugme--bos" href="about.html">Hayatı ve eserleri</a>
      </div>
    </div>
  </div>
</section>

<div class="kap">
  <dl class="sayilar">
    <div><dt>{len(kayit)}</dt><dd>Makale</dd></div>
    <div><dt>{osmanli}</dt><dd>Osmanlı Türkçesi</dd></div>
    <div><dt>{turkce}</dt><dd>Türkçe</dd></div>
    <div><dt>{aralik}</dt><dd>Neşir yılları</dd></div>
  </dl>
</div>

<section class="arsiv" id="arsiv">
  <div class="kap">
    <div class="bolum-baslik">
      <h2>Makaleler</h2>
      <p>Dergilerde neşredilmiş yazılar, en yeniden en eskiye doğru sıralanmıştır.
         Başlıkta veya tarihte arama yapabilir, dile göre süzebilirsiniz.</p>
    </div>

    <div class="araclar">
      <div class="ara">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>
        <label class="gizli-gorsel" for="ara">Makalelerde ara</label>
        <input id="ara" type="search" data-ara autocomplete="off"
               placeholder="Başlık veya tarih ara…">
      </div>
      <div class="suzgec" data-suzgec role="group" aria-label="Dile göre süz">
        <button type="button" data-dil="hepsi" aria-pressed="true">Tümü</button>
        <button type="button" data-dil="ottoman" aria-pressed="false">Osmanlı Türkçesi</button>
        <button type="button" data-dil="turkish" aria-pressed="false">Türkçe</button>
      </div>
    </div>

{zaman_serisi(kayit)}

    <p class="sonuc-sayisi" data-sonuc role="status" aria-live="polite">{len(kayit)} makale</p>

    <ul class="kartlar" data-kartlar>
{chr(10).join(kartlar)}
    </ul>
    <p class="bos-sonuc" data-bos hidden>Aramanıza uyan makale bulunamadı.</p>
  </div>
</section>

</main>
{alt_bilgi('')}'''

    ozet = ("Ömer Nasûhi Bilmen'in Osmanlıca ve Türkçe makaleleri: DİA transkripsiyonuyla "
            "hazırlanmış, aranabilir ve erişilebilir dijital arşiv.")
    ogeler = ',\n'.join(
        '  {"@type":"ListItem","position":%d,"url":"%s/%s","name":%s}'
        % (i + 1, SITE, k['yol'], _js(k['baslik'])) for i, k in enumerate(kayit))
    jsonld = ('<script type="application/ld+json">\n'
              '{"@context":"https://schema.org","@graph":[\n'
              '{"@type":"WebSite","@id":"%s/#site",'
              '"url":"%s/","name":"Ömer Nasûhi Bilmen — Makaleler Arşivi",'
              '"inLanguage":"tr","description":%s},\n'
              '{"@type":"CollectionPage","@id":"%s/#sayfa","url":"%s/",'
              '"name":"Ömer Nasûhi Bilmen Makaleleri","isPartOf":{"@id":"%s/#site"},'
              '"about":{"@type":"Person","name":"Ömer Nasûhi Bilmen",'
              '"sameAs":"https://islamansiklopedisi.org.tr/bilmen-omer-nasuhi"},'
              '"mainEntity":{"@type":"ItemList","numberOfItems":%d,"itemListElement":[\n%s\n]}}\n'
              ']}\n</script>'
              % (SITE, SITE, _js(ozet), SITE, SITE, SITE, len(kayit), ogeler))
    sayfa = kafa("Ömer Nasûhi Bilmen — Makaleler Arşivi", ozet, SITE + '/', '',
                 '\n' + jsonld) + icerik
    open(os.path.join(KOK, 'index.html'), 'w', encoding='utf-8').write(sayfa)


def hakkinda_yaz():
    ham = open(os.path.join(KAYNAK, 'about.html'), encoding='utf-8').read()
    m = re.search(r'<main[^>]*>(.*?)</main>', ham, re.S)
    govde = m.group(1) if m else ''
    govde = re.sub(r'<img[^>]*>', '', govde)
    govde = re.sub(r'<h1[^>]*>.*?</h1>', '', govde, count=1, flags=re.S)
    govde = re.sub(r'<p[^>]*class="[^"]*author-caption[^"]*"[^>]*>.*?</p>', '',
                   govde, flags=re.S)
    govde = re.sub(r'</?div[^>]*>', '', govde)
    govde = re.sub(r'</?article[^>]*>', '', govde)
    govde = re.sub(r'\sclass="[^"]*"', '', govde)
    govde = re.sub(r'<h2[^>]*>', '<h2>', govde)
    govde = re.sub(r'\n{3,}', '\n\n', govde).strip()

    # Kaynakça listesini gövdeden ayır
    kaynakca = ''
    kes = re.search(r'<h2>\s*Kaynak(?:ça|ca)\s*</h2>', govde)
    if kes:
        kuyruk = govde[kes.end():]
        govde = govde[:kes.start()].rstrip()
        maddeler = []
        for li in re.findall(r'<li[^>]*>(.*?)</li>', kuyruk, re.S):
            mm = re.match(r'\s*\[(\d{1,2})\]\s*(.*)', li, re.S)
            if not mm:
                continue
            n, ic = int(mm.group(1)), mm.group(2).strip()
            maddeler.append(
                f'      <li id="kn-{n}">{ic} '
                f'<a class="geri-don" href="#knr-{n}" aria-label="Metne dön">↩</a></li>')
        if maddeler:
            kaynakca = ('\n  <section class="dipnotlar" aria-labelledby="kaynakca-baslik">\n'
                        '    <h2 id="kaynakca-baslik">Kaynakça</h2>\n    <ol>\n'
                        + '\n'.join(maddeler) + '\n    </ol>\n  </section>')

    # metindeki [n] çağrılarını dipnot bağlantısına çevir
    govde = re.sub(r'\[(\d{1,2})\]',
                   lambda mm: f'<sup class="dipnot-baglanti"><a id="knr-{mm.group(1)}"'
                              f' href="#kn-{mm.group(1)}"'
                              f' aria-describedby="kaynakca-baslik">{mm.group(1)}</a></sup>',
                   govde)
    govde = cevir_html(govde, dia_uygula=False)
    kaynakca = cevir_html(kaynakca, dia_uygula=False)

    icerik = f'''{ust_cubuk('', 'hakkinda')}
<main id="icerik" class="hakkinda">
<div class="kap hakkinda__kap">
  <article>
    <div class="baski-yalniz baski-ustbilgi" aria-hidden="true">
      <b>Ömer Nasûhi Bilmen · Makaleler Arşivi</b>
      <span>omernasuhibilmen.github.io</span>
    </div>

    <header class="makale__ust">
      <h1>Ömer Nasûhi Bilmen’in hayatı ve eserleri</h1>
      <p class="makale__meta">
        <span class="yazar">1883 – 12 Ekim 1971</span>
        <span>Dersiâm, İstanbul müftüsü, Diyanet İşleri Başkanı</span>
      </p>
    </header>
    <img class="portre" src="ansiklopedi.jpg" width="640" height="800" loading="lazy"
         alt="Ömer Nasûhi Bilmen’in TDV İslâm Ansiklopedisi’ndeki fotoğrafı">
    <p class="portre-alt">Kaynak: TDV İslâm Ansiklopedisi</p>
    <div class="metin" data-metin>
{govde}
    </div>
{kaynakca}
  </article>
</div>
</main>
{alt_bilgi('')}'''

    ozet = ("Ömer Nasûhi Bilmen'in hayatı, ilmî çalışmaları ve eserleri: Erzurum’dan "
            "Diyanet İşleri Başkanlığı’na uzanan bir âlimin biyografisi.")
    kisi = ('<script type="application/ld+json">\n'
            '{"@context":"https://schema.org","@type":"ProfilePage",'
            '"mainEntity":{"@type":"Person","name":"Ömer Nasûhi Bilmen",'
            '"alternateName":"Ömer Nasuhi Bilmen","birthDate":"1883",'
            '"birthPlace":{"@type":"Place","name":"Salasar, Erzurum"},'
            '"deathDate":"1971-10-12",'
            '"deathPlace":{"@type":"Place","name":"İstanbul"},'
            '"nationality":"Türkiye","jobTitle":"Dersiâm, müftü, Diyanet İşleri Başkanı",'
            '"description":"Osmanlı\'nın son ve Cumhuriyet\'in ilk dönem ulemâsından '
            'fakih, müfessir ve kelâmcı. İstanbul müftülüğü (1943-1960) ve Diyanet '
            'İşleri Başkanlığı (1960-1961) yapmıştır.",'
            '"knowsAbout":["fıkıh","tefsir","kelâm","İslâm hukuku"],'
            '"sameAs":["https://islamansiklopedisi.org.tr/bilmen-omer-nasuhi",'
            '"https://tr.wikipedia.org/wiki/%C3%96mer_Nasuhi_Bilmen"]}}\n</script>')
    sayfa = kafa("Hayatı ve Eserleri — Ömer Nasûhi Bilmen", ozet,
                 SITE + '/about.html', '', '\n' + kisi) + icerik
    open(os.path.join(KOK, 'about.html'), 'w', encoding='utf-8').write(sayfa)


def site_haritasi(kayit):
    bugun = date.today().isoformat()
    satir = [f'  <url><loc>{SITE}/</loc><lastmod>{bugun}</lastmod>'
             f'<changefreq>monthly</changefreq><priority>1.0</priority></url>',
             f'  <url><loc>{SITE}/about.html</loc><lastmod>{bugun}</lastmod>'
             f'<changefreq>yearly</changefreq><priority>0.8</priority></url>']
    for k in kayit:
        satir.append(f'  <url><loc>{SITE}/articles/{k["dosya"]}</loc>'
                     f'<lastmod>{bugun}</lastmod><changefreq>yearly</changefreq>'
                     f'<priority>0.7</priority></url>')
    open(os.path.join(KOK, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(satir) + '\n</urlset>\n')


def llms_txt(kayit):
    """LLM'ler için sitenin makine okunur özeti (llmstxt.org sözleşmesi)."""
    satir = [
        '# Ömer Nasûhi Bilmen — Makaleler Arşivi',
        '',
        "> Ömer Nasûhi Bilmen'in (1883-1971) 1911-1963 arasında Osmanlıca ve Türkçe "
        "süreli yayınlarda neşredilmiş %d makalesinin tam metni. Osmanlıca kelimeler "
        "TDV İslâm Ansiklopedisi (DİA) transkripsiyon alfabesiyle gösterilmiştir "
        "(ḥ ḫ s̱ ẕ ṣ ż ṭ ẓ ġ ḳ; ayn ʿ, hemze ʾ; uzun ünlüler â î û, ḳ ve ġ'den "
        "sonra ā ī ū)." % len(kayit),
        '',
        'Müellif: Ömer Nasûhi Bilmen — Osmanlı’nın son, Cumhuriyet’in ilk dönem',
        'ulemâsından fakih, müfessir ve kelâmcı; İstanbul müftüsü (1943-1960) ve',
        'Diyanet İşleri Başkanı (1960-1961).',
        '',
        'Yayına hazırlayanlar: %s' % YAZARLAR,
        'Lisans: metinler kamuya açıktır; alıntılarken kaynak gösteriniz.',
        '',
        '## Hayatı',
        '',
        '- [Ömer Nasûhi Bilmen’in hayatı ve eserleri](%s/about.html): biyografi, '
        'eserlerinin tanıtımı ve kaynakça.' % SITE,
        '',
        '## Makaleler',
        '',
    ]
    for k in kayit:
        d = k.get('dergi') or {}
        kunye = []
        if d.get('ad'):
            kunye.append(d['ad'])
        if d.get('cilt'):
            kunye.append(d['cilt'] + '. cilt')
        if d.get('sayi'):
            kunye.append(d['sayi'] + '. sayı')
        kunye.append(k['tarih'])
        satir.append('- [%s](%s/%s): %s. %s.'
                     % (k['baslik'], SITE, k['yol'], ', '.join(kunye),
                        DIL_ADI[k['dil']]))
    satir.append('')
    open(os.path.join(KOK, 'llms.txt'), 'w', encoding='utf-8').write(
        '\n'.join(satir))


def main():
    kaynak_hazirla()
    kayit = meta_oku()
    print(f'  {len(kayit)} makale bulundu.')
    for i, k in enumerate(kayit):
        makale_yaz(k, kayit[i - 1] if i else None,
                   kayit[i + 1] if i + 1 < len(kayit) else None)
    anasayfa_yaz(kayit)
    hakkinda_yaz()
    site_haritasi(kayit)
    llms_txt(kayit)
    print('  index.html, about.html, sitemap.xml, llms.txt ve makaleler yazıldı.')


if __name__ == '__main__':
    main()
