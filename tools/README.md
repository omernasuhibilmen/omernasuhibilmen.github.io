# Site araçları — v2.0

Bu klasör sitenin üretim zincirini barındırır. Yayına çıkan dosyalar
(`index.html`, `about.html`, `articles/*.html`, `sitemap.xml`) **elle
düzenlenmez**; hepsi buradan üretilir.

```bash
python3 tools/build.py
```

## Dosyalar

| Dosya | İşlevi |
| --- | --- |
| `build.py` | Bütün sayfaları üretir: şablon, dipnotlar, meta veri, site haritası. |
| `dia.py` | DİA transkripsiyon motoru (sözlük + Türkçe ek çözümleme + tırnak onarımı). |
| `dia-sozluk.tsv` | Transkripsiyon sözlüğü. **Düzeltmeler burada yapılır.** |
| `arapca-duzeltmeler.json` | Bozuk Arapça/Farsça pasajlar için doğrulanmış onarımlar. |
| `simge_uret.py` | `favicon.svg` ile aynı geometriden `favicon.ico` ve `apple-touch-icon.png` üretir (yalnız stdlib). |
| `kaynak/` | v1 sitesinin dokunulmamış hâli. Üretimin girdisi budur. |

`kaynak/` klasörü ilk çalıştırmada proje kökünden bir kez kopyalanmıştır ve
üretim sırasında hiç değiştirilmez; `build.py` her çalıştığında çıktı sıfırdan
buradan üretilir. Yani üretimi istediğiniz kadar tekrarlayabilirsiniz.

## Transkripsiyon sistemi

TDV İslâm Ansiklopedisi'nin (DİA) transkripsiyon alfabesi esas alınmıştır:

| Arap harfi | ء | ث | ح | خ | ذ | ص | ض | ط | ظ | ع | غ | ق |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Karşılığı | ʾ | s̱ | ḥ | ḫ | ẕ | ṣ | ż | ṭ | ẓ | ʿ | ġ | ḳ |

* Uzun ünlüler `â î û`; **ḳ ve ġ'den sonra** `ā ī ū`
  (ör. `ḥaḳīḳat`, `ḥuḳūḳ`, `ṭabaḳāt`, `maḳām`).
* Hemze `ʾ` (U+02BE), ayn `ʿ` (U+02BF) — bunlar tırnak işareti değildir.
* Özel adlara gelen Türkçe ekler normal kesme işaretiyle ayrılır: `İslâm’da`.
* Kelime sonundaki hemze Türkçe ek alınca düşer: `semâʾ` + `lar` → `semâlar`.
* Ünsüz benzeşmesi uygulanır: `mevcûd` + `tur` → `mevcûddur`.

### Sözlüğe kelime eklemek

`dia-sozluk.tsv` iki sütunludur: **metindeki yüzey biçimi** ve **DİA karşılığı**.

```
hikmet	ḥikmet
```

Eşleştirme "en uzun kök + geçerli Türkçe ek" kuralıyla yapılır; tek satır
bütün çekimleri kapsar (`hikmete`, `hikmetin`, `hikmetleri`…).
Anahtar sütununda `'`, `’`, `‘` ve `â î û` işaretleri yok sayılır — yani
`ef'al`, `ef’al` ve `efal` aynı anahtardır.

Sözlükte olmayan kelimeye **hiç dokunulmaz.** Yanlış bir dönüşüm görürseniz
ilgili satırı düzeltin ya da silin, sonra `python3 tools/build.py` çalıştırın.

### Bilinen sınırlar

* **Nisbet `-î` belirsizliği.** `dini` hem "dînî" (sıfat) hem "dîni" (belirtme
  hâli) olabilir; motor sıfat okumasını tercih eder. Sık geçen istisnalar
  (`dinine`, `tarihinde` …) sözlüğe ayrıca yazılmıştır.
* **Arapça pasajlar** için aşağıdaki bölüme bakınız.
* Sözlük ~1.240 kök içerir ve metindeki Arapça/Farsça asıllı kelime hazinesinin
  yüksek frekanslı bölümünü kapsar; nadir kelimeler olduğu gibi bırakılır.

## Site simgesi

Simge **ÖNB** monogramıdır. Harfler yazı tipinden bağımsız olsun diye çember,
doğru parçası ve yay gibi ilkel biçimlerle çizilmiştir — `favicon.svg` elle
yazılmış vektördür, raster karşılıkları ondan türetilir:

```bash
python3 tools/simge_uret.py
```

**Boyuta göre ayrı çizim.** 16 px'te üç harf okunmaz (harf başına ~4 px düşer),
bu yüzden `favicon.ico`'nun 16 px katmanında yalnız büyük bir **Ö** çizilir;
32 ve 48 px katmanlarıyla `apple-touch-icon.png` (180 px) tam **ÖNB**
monogramını taşır. Sekme simgesi yüksek çözünürlüklü ekranlarda zaten 32 px
katmanını kullanır.

`favicon.svg`'nin geometrisini değiştirirseniz `simge_uret.py` içindeki
`_kapsam()` (ÖNB) ve `_kapsam_kucuk()` (16 px'lik Ö) fonksiyonlarındaki
değerleri de aynı şekilde güncelleyin, sonra betiği yeniden çalıştırın.
Pillow gerekmez; PNG doğrudan `zlib` ile yazılır.

## Yeni makale eklemek

1. Word dosyasını `convert_articles.py` ile (veya pandoc ile) HTML'e çevirin.
2. Çıkan dosyayı `tools/kaynak/articles/` altına koyun.
3. `tools/kaynak/index.html` içindeki kart listesine bir kart ekleyin
   (dil, bağlantı, başlık, tarih buradan okunur).
4. `python3 tools/build.py` çalıştırın.


## Bozuk Arapça/Farsça pasajlar

Kaynak Word dosyalarındaki bazı Arapça/Farsça pasajlar, vaktiyle bir PDF'ten
kopyalanırken bozulmuştur: harfler Unicode "sunum formu" kodlarına düşmüş,
bir kısmı font gliflerine (`ᗷ`, `ᘘ`, `ᢕ`, `ᖔ` …) dönüşmüş, harekeler
harflerinden kopup ayrı satırlara dağılmıştır. **Hasar HTML dönüşümünden değil,
kaynak `.docx` dosyasının kendisinden gelmektedir.**

Doğrulama için denenen kaynaklar:

| Kaynak | Sonuç |
| --- | --- |
| `word_articles/*.docx` | Aynı bozuk metni içeriyor — işe yaramıyor. |
| `pdfs/2. mehasin-i edep.pdf` | Gömülü font/görsel yok; aynı metnin yeniden dışa aktarımı. |
| `katalog.idp.org.tr` (dipnottaki bağlantı) | Alt alan adı artık çözülmüyor. |
| Web arşivi (2020 anlık görüntüsü) | Kayıt duruyor, ama "PDF Önizleme" üyelik girişi arkasında. |

Bu yüzden onarımlar **metin tenkidi yoluyla** yapılmıştır: her pasaj, makalenin
kendi Türkçe tercümesi ve dipnotundaki künye ile karşılaştırılarak okunmuştur.

Hasar pratikte tek makalede toplanmıştır: `mehasin-i-edep.html` (dört pasaj).
Diğer makalelerdeki Arap harfli metinler sağlamdır.

Onarılan pasajlar `arapca-duzeltmeler.json` dosyasında, her biri için gerekçesi
ve güven derecesiyle birlikte kayıtlıdır. Sayfada noktalı çizgiyle işaretlenir
(`.onarildi`) ve makale sonundaki **Metin notu** bölümünde açıklanır — yani
okuyucudan gizlenmez.

`build.py`, her kalıbın kaynakta **tam bir kez** eşleşmesini şart koşar; kaynak
değişirse üretim hata verip durur. Bir onarımı geri almak için ilgili kaydı
JSON'dan silmeniz yeterlidir.

Asıl dergi taramalarına (Beyânü'l-Hak, 4. cilt 96. sayı) erişebilirseniz bu dört
pasajın teyidi yerinde olur.


## v2.0'da eklenenler (ikinci tur)

**Dizgi.** Gövde metni iki yana yaslıdır (`text-align: justify`); yaslamanın
"ırmak" boşlukları açmaması için otomatik tireleme (`hyphens: auto`,
`hyphenate-limit-chars: 7 4 3`) birlikte kullanılır. Kısa alıntı/şiir satırları
ve Arapça pasajlar yaslamanın dışındadır — orada yaslama boşlukları çirkinleşir.

**PDF çıktısı.** Her makalede "PDF olarak indir" düğmesi `window.print()`
çağırır; çıktıyı `@media print` bloğu biçimlendirir (A4, 18/17/20 mm kenar).
Ek bir bağımlılık yoktur. Çıktının kaynağı iki yerden bellidir:

* üstte künye şeridi — *Ömer Nasûhi Bilmen · Makaleler Arşivi* + alan adı;
* altta **kaynak künyesi** — makale adı, dergi/cilt/sayı/sayfa/tarih, sayfanın
  tam adresi, transkripsiyon sistemi ve yayına hazırlayanlar.

Bu bloklar ekranda gizli (`.baski-yalniz`), yalnız baskıda görünür.

**Süreli yayın bilgisi.** `dergi_bul()` her makalenin ham metninden dergi adını,
cildini, sayısını ve sayfasını çıkarır (51/51). Bu bilgi kartlarda, baskı
künyesinde, `llms.txt`'te ve JSON-LD'de kullanılır.

**Zaman serisi.** Ana sayfadaki çubuk grafik makalelerin yıllara dağılımını
gösterir; çubuklar aynı zamanda süzgeçtir ve dil süzgeciyle birlikte çalışır.
Klavyeyle gezilebilir, her çubuğun ekran okuyucu etiketi vardır.

## SEO ve LLM'ler

* **JSON-LD.** Makalelerde `Article` + `BreadcrumbList`; makale, süreli yayın
  künyesine `PublicationIssue → PublicationVolume → Periodical` zinciriyle
  bağlanır (ilmî atıf için doğru şema). Ana sayfada `WebSite` +
  `CollectionPage` + 51 maddelik `ItemList`; hayatı sayfasında `ProfilePage` +
  `Person` (doğum/ölüm, görevler, `sameAs` ile DİA ve Vikipedi).
* **Meta.** Makalelerde `og:type=article`, `article:published_time`,
  `article:author`, `article:section`; her sayfada `robots` yönergesi
  (`max-snippet:-1, max-image-preview:large`), kanonik adres, `og`/`twitter`
  etiketleri.
* **`llms.txt`.** Kök dizinde, [llmstxt.org](https://llmstxt.org) sözleşmesine
  göre üretilir: arşivin ne olduğu, kullanılan transkripsiyon alfabesi ve
  51 makalenin tamamı künyeleriyle birlikte tek bir düz metin dosyasında.
  Model ve ajanların siteyi doğru künyelemesi için `build.py` her çalıştığında
  yeniden yazılır.
* **`sitemap.xml`** ve **`robots.txt`** üretimle birlikte güncellenir.
