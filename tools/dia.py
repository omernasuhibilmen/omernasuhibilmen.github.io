# -*- coding: utf-8 -*-
"""DİA (TDV İslâm Ansiklopedisi) transkripsiyon motoru.

Sözlük tabanlıdır: tools/dia-sozluk.tsv dosyasındaki köklerle "en uzun önek +
geçerli Türkçe ek" eşleşmesi yapar. Sözlükte bulunmayan kelimelere dokunmaz.

DİA karakter seti (islamansiklopedisi.org.tr kaynaklı):
    ء ʾ   ع ʿ   ث s̱   ح ḥ   خ ḫ   ذ ẕ   ص ṣ   ض ż   ط ṭ   ظ ẓ   غ ġ   ق ḳ
    Uzun ünlüler â î û; ḳ ve ġ'den sonra ā ī ū.
"""
import os
import re
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
SOZLUK = os.path.join(BASE, 'dia-sozluk.tsv')

AYN, HEMZE = 'ʿ', 'ʾ'
KESME = '’'          # Türkçe kesme işareti
TIRNAK_AC, TIRNAK_KAPA = '“', '”'
ISARETLER = "'’‘ʿʾ´`"

# Eşleştirme için sadeleştirme: işaretler ve uzunluk şapkaları düşer.
_SADE = str.maketrans({
    'â': 'a', 'ā': 'a', 'î': 'i', 'ī': 'i', 'û': 'u', 'ū': 'u',
    'Â': 'a', 'Ā': 'a', 'Î': 'i', 'Ī': 'i', 'Û': 'u', 'Ū': 'u',
})


def kucult(s):
    return s.replace('I', 'ı').replace('İ', 'i').lower()


def anahtar(s):
    s = kucult(s).translate(_SADE)
    s = ''.join(c for c in s if c not in ISARETLER)
    # kaynak metin "-iyet" ve "-iyyet" yazımlarını karışık kullanıyor; tek biçime indir
    return s.replace('iyye', 'iye').replace('ıyya', 'ıya').replace('ıyye', 'ıye')


# Türkçe çekim ekleri (yüzey biçimleri). Kök eşleşmesinden artakalan parça
# bunların ardışık dizilimine tam uymazsa eşleşme reddedilir.
_EKLER = [
    'ları', 'leri', 'ların', 'lerin', 'lardan', 'lerden', 'larda', 'lerde',
    'lara', 'lere', 'lar', 'ler',
    'ndan', 'nden', 'nda', 'nde', 'nın', 'nin', 'nun', 'nün',
    'dan', 'den', 'tan', 'ten', 'da', 'de', 'ta', 'te',
    'ın', 'in', 'un', 'ün', 'na', 'ne', 'ya', 'ye',
    'sı', 'si', 'su', 'sü', 'yı', 'yi', 'yu', 'yü',
    'nı', 'ni', 'nu', 'nü', 'ı', 'i', 'u', 'ü', 'a', 'e',
    'ıyla', 'iyle', 'uyla', 'üyle', 'yla', 'yle', 'la', 'le',
    'lık', 'lik', 'luk', 'lük', 'lı', 'li', 'lu', 'lü',
    'sız', 'siz', 'suz', 'süz',
    'dır', 'dir', 'dur', 'dür', 'tır', 'tir', 'tur', 'tür',
    'ımız', 'imiz', 'umuz', 'ümüz', 'ınız', 'iniz', 'unuz', 'ünüz',
    'ım', 'im', 'um', 'üm', 'daki', 'deki', 'taki', 'teki', 'ki',
    'ce', 'ca', 'çe', 'ça', 'cı', 'ci', 'cu', 'cü',
]
_EK_RE = re.compile('(?:%s)*' % '|'.join(sorted(_EKLER, key=len, reverse=True)) + r'\Z')


def sozluk_yukle(yol=SOZLUK):
    d = {}
    with open(yol, encoding='utf-8') as fh:
        for satir in fh:
            satir = satir.rstrip('\n')
            if not satir.strip() or satir.lstrip().startswith('#'):
                continue
            parca = satir.split('\t')
            if len(parca) != 2:
                continue
            d[anahtar(parca[0])] = parca[1]
    return d


SOZ = sozluk_yukle()
EN_UZUN = max(len(k) for k in SOZ)

_HARF = 'A-Za-zÇĞİIŞÖÜçğışöüÂÎÛâîûĀĪŪāīū'
KELIME_RE = re.compile('[%s]+(?:[%s][%s]+)*' % (_HARF, re.escape(ISARETLER), _HARF))


def _harf_mi(c):
    """ʿ ve ʾ birer harf değil, transkripsiyon işaretidir."""
    return c.isalpha() and c not in (AYN, HEMZE)


def _buyuk_harfe(s):
    """DİA formunun ilk harfini büyüt (ʿ/ʾ ile başlıyorsa sonraki harfi)."""
    for i, c in enumerate(s):
        if _harf_mi(c):
            return s[:i] + s[i].replace('i', 'İ').upper() + s[i + 1:]
    return s


def kelime_cevir(kelime):
    """Tek kelimeyi çevirir. (yeni_kelime, eslesti_mi) döndürür."""
    sade = anahtar(kelime)
    if len(sade) < 3:
        return kelime, False
    # kesme işaretinin sade dizideki karşılık konumları
    konum, j = [], 0
    for c in kucult(kelime):
        if c in ISARETLER:
            konum.append(j)
        else:
            j += 1
    for k in range(min(len(sade), EN_UZUN), 2, -1):
        karsilik = SOZ.get(sade[:k])
        if karsilik is None:
            continue
        artan = sade[k:]
        if artan and not _EK_RE.fullmatch(artan):
            continue
        # kök sınırındaki kesme işareti Türkçe eki ayırıyorsa korunur
        ayirac = KESME if (artan and k in konum) else ''
        if artan and karsilik.endswith(HEMZE):
            # kelime sonu hemzesi Türkçe ek aldığında düşer: semâʾ + lar -> semâlar
            karsilik = karsilik[:-1]
        if artan and not ayirac and karsilik[-1:] in 'bcdġ' and artan[0] == 't':
            artan = 'd' + artan[1:]   # ünsüz benzeşmesi: mevcûd + tur -> mevcûddur
        sonuc = karsilik + ayirac + artan
        ilk = next((c for c in kelime if _harf_mi(c)), '')
        dia_ozel = _ilk_harf_buyuk(karsilik)
        if not dia_ozel:
            if kelime.isupper() and len(kelime) > 1:
                sonuc = sonuc.upper()
            elif ilk.isupper():
                sonuc = _buyuk_harfe(sonuc)
        return sonuc, True
    return kelime, False


def _ilk_harf_buyuk(s):
    for c in s:
        if _harf_mi(c):
            return c.isupper()
    return False


def metin_cevir(metin, istatistik=None):
    """Bir metin parçasındaki kelimeleri çevirir."""
    def _dv(m):
        eski = m.group(0)
        yeni, oldu = kelime_cevir(eski)
        if istatistik is not None and oldu and yeni != eski:
            istatistik[(eski, yeni)] = istatistik.get((eski, yeni), 0) + 1
        return yeni
    return KELIME_RE.sub(_dv, metin)


# --- tırnak onarımı -------------------------------------------------------
# pandoc dönüşümü çift tırnakları ’’ / ‘’ ikililerine ve tekil ’ ‘ işaretlerine
# bozmuş durumda. Sözlük geçişinden sonra artakalan işaretler burada onarılır.

def tirnak_onar(metin):
    sonuc = []
    acik = False
    i, n = 0, len(metin)
    while i < n:
        c = metin[i]
        if c not in '’‘':
            sonuc.append(c)
            i += 1
            continue
        cift = i + 1 < n and metin[i + 1] in '’‘'
        son = i + (2 if cift else 1)
        onceki = metin[i - 1] if i else ' '
        sonraki = metin[son] if son < n else ' '
        if cift:
            if sonraki.isalpha() or (sonraki == ' ' and not acik):
                sonuc.append(TIRNAK_AC); acik = True
            else:
                sonuc.append(TIRNAK_KAPA); acik = False
        elif onceki.isalpha() and sonraki.isalpha():
            # kelime içi: özel ada gelen Türkçe eki mi, kapanan tırnak mı?
            bas = len(sonuc) - 1
            while bas >= 0 and sonuc[bas].isalpha():
                bas -= 1
            ilk = sonuc[bas + 1] if bas + 1 < len(sonuc) else ''
            j = son
            while j < n and metin[j].isalpha():
                j += 1
            sonra_ek = metin[son:j]
            if len(sonra_ek) <= 2 and all(c in 'tlnsşzdrc' for c in sonra_ek):
                sonuc.append(KESME)          # Arapça harf-i tarif: târîḫu’t-teşrîʿ
                i = son
                continue
            if acik and not ilk.isupper():
                sonuc.append(TIRNAK_KAPA); acik = False
            else:
                sonuc.append(KESME)
        elif sonraki.isalpha() and not onceki.isalpha():
            sonuc.append(TIRNAK_AC); acik = True
        elif onceki.isalpha() and not sonraki.isalpha():
            if acik:
                sonuc.append(TIRNAK_KAPA); acik = False
            else:
                sonuc.append(AYN)          # kelime sonu ayn
        else:
            sonuc.append(TIRNAK_AC if not acik else TIRNAK_KAPA)
            acik = not acik
        i = son
    return ''.join(sonuc), acik
