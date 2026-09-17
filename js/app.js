/* Ömer Nasûhi Bilmen — Makaleler · v2.0
   Bağımlılıksız arayüz betiği: tema, arama/süzme, okuma araçları. */
(function () {
  'use strict';

  var kok = document.documentElement;

  /* --- Tema ------------------------------------------------------------- */
  function temaKur() {
    var dugme = document.querySelector('[data-tema-dugme]');
    if (!dugme) return;
    function etiketle() {
      var koyu = kok.getAttribute('data-tema') === 'koyu' ||
        (!kok.getAttribute('data-tema') &&
          window.matchMedia('(prefers-color-scheme: dark)').matches);
      dugme.setAttribute('aria-label', koyu ? 'Açık temaya geç' : 'Koyu temaya geç');
      dugme.setAttribute('aria-pressed', String(koyu));
    }
    dugme.addEventListener('click', function () {
      var koyu = kok.getAttribute('data-tema') === 'koyu' ||
        (!kok.getAttribute('data-tema') &&
          window.matchMedia('(prefers-color-scheme: dark)').matches);
      var yeni = koyu ? 'acik' : 'koyu';
      kok.setAttribute('data-tema', yeni);
      try { localStorage.setItem('onb-tema', yeni); } catch (e) { /* yok sayılır */ }
      etiketle();
    });
    etiketle();
  }

  /* --- Arama ve süzme (ana sayfa) --------------------------------------- */
  function arsivKur() {
    var liste = document.querySelector('[data-kartlar]');
    if (!liste) return;
    var kartlar = Array.prototype.slice.call(liste.querySelectorAll('[data-dil]'));
    var kutu = document.querySelector('[data-ara]');
    var dugmeler = Array.prototype.slice.call(document.querySelectorAll('[data-suzgec] button'));
    var sayac = document.querySelector('[data-sonuc]');
    var bos = document.querySelector('[data-bos]');
    var yilDugmeleri = Array.prototype.slice.call(
      document.querySelectorAll('.zaman-serisi__cubuklar button'));
    var secilenDil = 'hepsi';
    var secilenYil = null;

    // Aksanları ve transkripsiyon işaretlerini düşürerek arama anahtarı üret
    function sadelestir(s) {
      return s.toLocaleLowerCase('tr')
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .replace(/[ʿʾ'’‘]/g, '')
        .replace(/ı/g, 'i').replace(/ğ/g, 'g').replace(/ş/g, 's')
        .replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ç/g, 'c');
    }

    kartlar.forEach(function (k) {
      k.dataset.anahtar = sadelestir(k.textContent + ' ' + (k.dataset.dilAdi || ''));
    });

    function uygula() {
      var q = sadelestir(kutu ? kutu.value.trim() : '');
      var gorunen = 0;
      kartlar.forEach(function (k) {
        var dilUygun = secilenDil === 'hepsi' || k.dataset.dil === secilenDil;
        var yilUygun = !secilenYil || k.dataset.yil === secilenYil;
        var metinUygun = !q || k.dataset.anahtar.indexOf(q) !== -1;
        var goster = dilUygun && yilUygun && metinUygun;
        k.hidden = !goster;
        if (goster) gorunen++;
      });
      if (sayac) {
        sayac.textContent = gorunen === kartlar.length
          ? kartlar.length + ' makale'
          : gorunen + ' / ' + kartlar.length + ' makale';
      }
      if (bos) bos.hidden = gorunen !== 0;
      yilDugmeleri.forEach(function (d) {
        d.setAttribute('aria-pressed', String(d.dataset.yil === secilenYil));
      });
    }

    if (kutu) {
      kutu.addEventListener('input', uygula);
      kutu.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { kutu.value = ''; uygula(); }
      });
    }
    dugmeler.forEach(function (d) {
      d.addEventListener('click', function () {
        secilenDil = d.dataset.dil;
        dugmeler.forEach(function (x) {
          x.setAttribute('aria-pressed', String(x === d));
        });
        uygula();
      });
    });
    yilDugmeleri.forEach(function (d) {
      d.addEventListener('click', function () {
        secilenYil = secilenYil === d.dataset.yil ? null : d.dataset.yil;
        uygula();
      });
    });
    uygula();
  }

  /* --- Türkçe heceleme ---------------------------------------------------
     Tarayıcılarda Türkçe tireleme sözlüğü çoğunlukla bulunmadığı için
     `hyphens: auto` işlemez ve iki yana yaslı metin kelime aralarını açar.
     Türkçe hece yapısı kurallı olduğundan yumuşak tireleri (U+00AD) burada
     kendimiz yerleştiriyoruz. Kaynak HTML'e dokunulmaz: ekleme yalnız
     tarayıcıda yapılır, kopyalarken de temizlenir. */
  var UNLU = 'aeıioöuüâîûāīūAEIİOÖUÜÂÎÛĀĪŪ';
  var YUMUSAK = '\u00ad';

  function unluMu(c) { return UNLU.indexOf(c) !== -1; }

  function heceBol(kelime) {
    // Birleşik işaretleri (ör. s̱ = s + U+0331) önceki harfe bağlı say.
    var harfler = [], i;
    for (i = 0; i < kelime.length; i++) {
      var k = kelime.charCodeAt(i);
      if (harfler.length && k >= 0x300 && k <= 0x36f) {
        harfler[harfler.length - 1] += kelime[i];
      } else {
        harfler.push(kelime[i]);
      }
    }
    if (harfler.length < 7) return kelime;

    var unluler = [];
    for (i = 0; i < harfler.length; i++) {
      if (unluMu(harfler[i][0])) unluler.push(i);
    }
    if (unluler.length < 2) return kelime;

    // Türkçe kuralı: bir ünlüden önceki son ünsüz, o ünlünün hecesine katılır.
    // (ka-lem, kar-tal, e-lekt-rik); iki ünlü yan yanaysa arada bölünür (sa-at).
    var sinirlar = [];
    for (i = 0; i < unluler.length - 1; i++) {
      var a = unluler[i], b = unluler[i + 1];
      var sinir = (b - a === 1) ? b : b - 1;
      var onceki = harfler[sinir - 1];
      if (sinir >= 2 && harfler.length - sinir >= 3 &&
          onceki !== '\u2019' && onceki !== "'") {
        sinirlar.push(sinir);
      }
    }
    if (!sinirlar.length) return kelime;

    var cikti = '', j = 0;
    for (i = 0; i < harfler.length; i++) {
      if (j < sinirlar.length && i === sinirlar[j]) { cikti += YUMUSAK; j++; }
      cikti += harfler[i];
    }
    return cikti;
  }

  var KELIME_RE = /[A-Za-zÇĞİIŞÖÜçğışöüÂÎÛâîûĀĪŪāīū\u0300-\u036f\u1e00-\u1eff\u02bf\u02be'’]+/g;

  function heceleDugum(kok) {
    var atla = 'h1,h2,h3,[dir="rtl"],.arapca,.kunye,code,pre';
    var gez = document.createTreeWalker(kok, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var ust = n.parentElement;
        if (!ust || ust.closest(atla)) return NodeFilter.FILTER_REJECT;
        return /\S{7,}/.test(n.nodeValue)
          ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var dugumler = [], d;
    while ((d = gez.nextNode())) dugumler.push(d);
    dugumler.forEach(function (n) {
      n.nodeValue = n.nodeValue.replace(KELIME_RE, heceBol);
    });
  }

  /* --- Okuma araçları (makale sayfası) ---------------------------------- */
  var SADE = {
    'ḥ': 'h', 'Ḥ': 'H', 'ḫ': 'h', 'Ḫ': 'H', 'ẕ': 'z', 'Ẕ': 'Z',
    'ṣ': 's', 'Ṣ': 'S', 'ż': 'z', 'Ż': 'Z', 'ṭ': 't', 'Ṭ': 'T',
    'ẓ': 'z', 'Ẓ': 'Z', 'ġ': 'g', 'Ġ': 'G', 'ḳ': 'k', 'Ḳ': 'K',
    'ḍ': 'd', 'Ḍ': 'D', 'ā': 'â', 'Ā': 'Â', 'ī': 'î', 'Ī': 'Î',
    'ū': 'û', 'Ū': 'Û', 'ʿ': '’', 'ʾ': '’'
  };

  function sadeMetin(s) {
    return s.replace(/[̱̲]/g, '')
      .replace(/[ḥḤḫḪẕẔṣṢżŻṭṬẓẒġĠḳḲḍḌāĀīĪūŪʿʾ]/g, function (c) {
        return SADE[c] || c;
      });
  }

  function makaleKur() {
    var govde = document.querySelector('[data-metin]');
    if (!govde) return;

    heceleDugum(govde);
    // kopyalanan metinde yumuşak tire kalmasın
    govde.addEventListener('copy', function (e) {
      var sec = window.getSelection();
      if (!sec || !sec.toString()) return;
      e.clipboardData.setData('text/plain',
        sec.toString().split(YUMUSAK).join(''));
      e.preventDefault();
    });

    /* okuma ilerlemesi */
    var cubuk = document.querySelector('[data-ilerleme]');
    if (cubuk) {
      var guncelle = function () {
        var k = govde.getBoundingClientRect();
        var toplam = k.height - window.innerHeight;
        var oran = toplam <= 0 ? 1 : Math.min(1, Math.max(0, -k.top / toplam));
        cubuk.style.transform = 'scaleX(' + oran + ')';
      };
      window.addEventListener('scroll', guncelle, { passive: true });
      window.addEventListener('resize', guncelle);
      guncelle();
    }

    /* yazı boyutu */
    var boyutlar = [1, 1.12, 1.25];
    var boyutDugme = document.querySelector('[data-boyut]');
    if (boyutDugme) {
      var i = 0;
      try {
        var kayit = parseInt(localStorage.getItem('onb-boyut'), 10);
        if (kayit >= 0 && kayit < boyutlar.length) i = kayit;
      } catch (e) { /* yok sayılır */ }
      var boyutUygula = function () {
        govde.style.setProperty('--metin-olcek', boyutlar[i]);
        boyutDugme.setAttribute('aria-pressed', String(i > 0));
        boyutDugme.querySelector('[data-boyut-etiket]').textContent =
          ['Normal', 'Büyük', 'Daha büyük'][i];
      };
      boyutDugme.addEventListener('click', function () {
        i = (i + 1) % boyutlar.length;
        try { localStorage.setItem('onb-boyut', String(i)); } catch (e) { /* yok sayılır */ }
        boyutUygula();
      });
      boyutUygula();
    }

    /* PDF olarak indir — tarayıcının "PDF olarak kaydet" çıktısı kullanılır */
    var pdfDugme = document.querySelector('[data-pdf]');
    if (pdfDugme) {
      pdfDugme.addEventListener('click', function () { window.print(); });
    }

    /* transkripsiyonu sadeleştir */
    var sadeDugme = document.querySelector('[data-sade]');
    if (sadeDugme) {
      var dugumler = [];
      var gez = document.createTreeWalker(govde, NodeFilter.SHOW_TEXT, {
        acceptNode: function (n) {
          var ust = n.parentElement;
          if (ust && ust.closest('[dir="rtl"]')) return NodeFilter.FILTER_REJECT;
          return /[̱ḥḫẕṣżṭẓġḳāīūʿʾ]/.test(n.nodeValue)
            ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
        }
      });
      var d;
      while ((d = gez.nextNode())) dugumler.push([d, d.nodeValue, sadeMetin(d.nodeValue)]);

      var sade = false;
      try { sade = localStorage.getItem('onb-sade') === '1'; } catch (e) { /* yok sayılır */ }
      var sadeUygula = function () {
        dugumler.forEach(function (p) { p[0].nodeValue = sade ? p[2] : p[1]; });
        sadeDugme.setAttribute('aria-pressed', String(sade));
      };
      sadeDugme.addEventListener('click', function () {
        sade = !sade;
        try { localStorage.setItem('onb-sade', sade ? '1' : '0'); } catch (e) { /* yok sayılır */ }
        sadeUygula();
      });
      sadeUygula();
    }
  }

  /* --- Yukarı çık -------------------------------------------------------- */
  function yukariKur() {
    var d = document.querySelector('[data-yukari]');
    if (!d) return;
    var gorunur = function () {
      d.dataset.gorunur = window.scrollY > 600 ? 'evet' : 'hayir';
    };
    window.addEventListener('scroll', gorunur, { passive: true });
    d.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      var ilk = document.querySelector('main a, main h1');
      if (ilk) ilk.focus({ preventScroll: true });
    });
    gorunur();
  }

  function baslat() { temaKur(); arsivKur(); makaleKur(); yukariKur(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', baslat);
  } else { baslat(); }
})();
