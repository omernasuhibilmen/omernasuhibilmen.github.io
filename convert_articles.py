import os
from pathlib import Path
import pypandoc
import re
from datetime import datetime
import logging
import shutil

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_filename(title):
    try:
        # Türkçe karakterleri ve boşlukları düzenle
        title = title.lower()
        title = re.sub(r'[ğ]', 'g', title)
        title = re.sub(r'[ü]', 'u', title)
        title = re.sub(r'[ş]', 's', title)
        title = re.sub(r'[ı]', 'i', title)
        title = re.sub(r'[ö]', 'o', title)
        title = re.sub(r'[ç]', 'c', title)
        title = re.sub(r'[^a-z0-9]', '-', title)
        return title
    except Exception as e:
        logger.error(f"Dosya adı düzenlenirken hata: {e}")
        raise

def extract_article_title(content):
    """Makale içeriğinden başlığı çıkarır"""
    # Başlık için regex pattern'ları
    patterns = [
        r'<h1.*?>(.*?)</h1>',                    # HTML h1 tag'i içindeki başlık
        r'<p.*?><strong>(.*?)</strong></p>',     # Strong tag içindeki ilk paragraf
        r'<p[^>]*>([^<.]{10,100})</p>',         # İlk paragraf (10-100 karakter)
        r'(?m)^([^\n\r.]{10,100})$',            # Satır başı ve sonu arasındaki metin
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            try:
                title = match.group(1).strip()
                # HTML taglerini temizle
                title = re.sub(r'<[^>]+>', '', title)
                # Başlık boş değilse ve yeterince uzunsa
                if title and len(title) >= 5:
                    return title
            except (IndexError, AttributeError):
                continue
    
    # Hiçbir pattern eşleşmezse dosya adını kullan
    return None

def convert_docx_to_html(input_file):
    try:
        # Dosya adından başlığı al (yedek olarak)
        file_title = os.path.splitext(os.path.basename(input_file))[0]
        # Dosya adından numara kısmını kaldır
        file_title = re.sub(r'^\d+\s*[-_.]+\s*', '', file_title).strip()
        clean_title = clean_filename(file_title)
        
        logger.info(f"'{file_title}' dosyası işleniyor...")
        
        # Word dosyasını HTML'e çevir
        content = pypandoc.convert_file(
            input_file,
            'html',
            format='docx',
            extra_args=['--extract-media=images']
        )
        
        # Makale başlığını ve tarihini çıkar
        article_title = extract_article_title(content)
        if not article_title:
            article_title = file_title
            
        article_date = extract_article_date(content)
        if not article_date:
            article_date = datetime.now().strftime('%d %B %Y')
        
        # HTML şablonu
        html_template = '''<!DOCTYPE html>
<html lang="tr" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Osmanlıca Makaleler</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <link rel="stylesheet" href="../css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body style="background-color: var(--bg-primary);">
    <nav class="navbar navbar-expand-lg bg-dark-subtle">
        <div class="container">
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="../index.html">Ana Sayfa</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="../index.html#makaleler">Makaleler</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="../about.html">Ömer Nasûhi Bilmen</a>
                    </li>
                </ul>
                <div class="theme-switcher d-flex align-items-center">
                    <i class="bi bi-sun-fill me-2 theme-icon" id="lightIcon"></i>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="themeSwitch">
                    </div>
                    <i class="bi bi-moon-fill ms-2 theme-icon" id="darkIcon"></i>
                </div>
            </div>
        </div>
    </nav>

    <main class="container py-5">
        <article class="latex-article">
            <div class="title-block">
                <h1 class="ottoman-title">{title}</h1>
                <p class="text-muted mt-3">
                    <i class="bi bi-calendar3 me-2"></i>
                    <span class="date">{date}</span>
                </p>
            </div>
            
            <div class="content">
                {content}
            </div>
        </article>
    </main>

    <footer class="bg-dark-subtle text-center py-4 mt-5">
        <div class="container">
            <div class="mb-3">
                <a href="https://github.com/mevlut-celik" class="text-decoration-none" target="_blank">
                    <i class="bi bi-github fs-4"></i>
                </a>
            </div>
            <p class="mb-0">Ahmet Şengül - Mevlüt Çelik</p>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="../js/main.js"></script>
</body>
</html>'''

        # HTML dosyasını oluştur
        output_path = Path('articles') / f'{clean_title}.html'
        output_path.parent.mkdir(exist_ok=True)
        
        final_html = html_template.format(
            title=article_title,
            date=article_date,
            content=content
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        logger.info(f"'{article_title}' başarıyla dönüştürüldü: {output_path}")
        return clean_title, article_title

    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        raise

def extract_article_date(content):
    """Makale içeriğinden tarihi çıkarır"""
    # Yaygın tarih formatları için regex pattern'ları
    patterns = [
        # Tam tarih formatları
        r'(\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4})',
        r'(\d{4}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{1,2})',
        
        # Ay ve yıl formatları
        r'((?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4})',
        
        # Sayısal formatlar
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}/\d{1,2}/\d{1,2})',
        
        # Hicri tarih formatları
        r'(\d{1,2}\s+(?:Muharrem|Safer|Rebiülevvel|Rebiülahir|Cemaziyelevvel|Cemaziyelahir|Recep|Şaban|Ramazan|Şevval|Zilkade|Zilhicce)\s+\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            date_str = match.group(1)
            # Eğer sadece ay ve yıl varsa, ayın 1'ini ekle
            if len(date_str.split()) == 2:
                month, year = date_str.split()
                date_str = f"1 {month} {year}"
            return date_str
    
    return datetime.now().strftime('%d %B %Y')  # Tarih bulunamazsa bugünün tarihi

def parse_turkish_date(date_str):
    """Türkçe tarih stringini datetime objesine çevirir"""
    month_map = {
        'Ocak': 1, 'Şubat': 2, 'Mart': 3, 'Nisan': 4,
        'Mayıs': 5, 'Haziran': 6, 'Temmuz': 7, 'Ağustos': 8,
        'Eylül': 9, 'Ekim': 10, 'Kasım': 11, 'Aralık': 12
    }
    
    try:
        day, month, year = date_str.split()
        return datetime(int(year), month_map[month], int(day))
    except:
        return datetime.now()

def update_index_with_article(article_filename, title, category="ottoman"):
    try:
        index_path = Path('index.html')
        if not index_path.exists():
            logger.error("index.html dosyası bulunamadı!")
            return

        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Kategori badge'ini ayarla
        badge_text = "Osmanlı Türkçesi" if category == "ottoman" else "Türkçe"

        # Makale içeriğini oku ve tarihini çıkar
        article_path = Path('articles') / f'{article_filename}.html'
        if article_path.exists():
            with open(article_path, 'r', encoding='utf-8') as f:
                article_content = f.read()
                article_date = extract_article_date(article_content)
        else:
            article_date = datetime.now().strftime('%d %B %Y')

        # Yeni makale HTML'i
        article_html = f'''
            <div class="col-md-6 col-lg-4" data-category="{category}">
                <div class="card h-100 bg-dark-subtle border-light">
                    <div class="card-body">
                        <span class="badge bg-primary mb-2">{badge_text}</span>
                        <h3 class="card-title h5 ottoman-title">
                            <a href="articles/{article_filename}.html" class="text-dark text-decoration-none">
                                <i class="bi bi-journal-text me-2"></i>{title}
                            </a>
                        </h3>
                        <p class="card-text small text-light-emphasis">
                            <i class="bi bi-calendar3 me-2"></i>{article_date}
                        </p>
                    </div>
                </div>
            </div>'''

        # Mevcut makaleleri topla
        articles = []
        article_section = re.search(r'<div class="row g-4">(.*?)</div>', content, re.DOTALL)
        if article_section:
            existing_articles = re.findall(
                r'<div class="col-md-6 col-lg-4".*?</div>\s*</div>\s*</div>',
                article_section.group(1),
                re.DOTALL
            )
            
            # Mevcut makaleleri parse et
            for article in existing_articles:
                article_date_match = re.search(r'<i class="bi bi-calendar3 me-2"></i>(.*?)</p>', article)
                if article_date_match:
                    article_date_str = article_date_match.group(1).strip()
                    articles.append({
                        'html': article,
                        'date': parse_turkish_date(article_date_str)
                    })

        # Yeni makaleyi ekle
        articles.append({
            'html': article_html,
            'date': parse_turkish_date(article_date)
        })

        # Tarihe göre sırala (en yeni en üstte)
        articles.sort(key=lambda x: x['date'], reverse=True)

        # HTML'i güncelle
        sorted_html = '\n'.join(article['html'] for article in articles)
        new_content = re.sub(
            r'<div class="row g-4">.*?</div>\s*</section>',
            f'<div class="row g-4">{sorted_html}</div></section>',
            content,
            flags=re.DOTALL
        )

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        logger.info(f"index.html güncellendi: {title} eklendi ve makaleler tarihe göre sıralandı")

    except Exception as e:
        logger.error(f"index.html güncellenirken hata: {e}")
        raise

def update_index_with_pdf(pdf_filename, title):
    try:
        index_path = Path('index.html')
        if not index_path.exists():
            logger.error("index.html dosyası bulunamadı!")
            return

        # index.html dosyasını oku
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # PDF numarasını dosya adından çıkar
        pdf_number = re.search(r'^(\d+)--', pdf_filename)
        if pdf_number:
            pdf_number = int(pdf_number.group(1))
        else:
            pdf_number = 999

        # PDF için HTML kartı
        pdf_html = f'''
            <div class="col-md-6 col-lg-4" data-category="ottoman">
                <div class="card h-100 bg-dark-subtle border-light">
                    <div class="card-body">
                        <span class="badge bg-primary mb-2">Osmanlı Türkçesi</span>
                        <h3 class="card-title h5 ottoman-title">
                            <a href="pdfs/{pdf_filename}.pdf" class="text-dark text-decoration-none" target="_blank">
                                <i class="bi bi-file-pdf me-2"></i>{title}
                            </a>
                        </h3>
                        <p class="card-text small text-light-emphasis">
                            <i class="bi bi-calendar3 me-2"></i>{datetime.now().strftime('%d %B %Y')}
                        </p>
                    </div>
                </div>
            </div>'''

        # Makale bölümünü bul ve yeni PDF'i ekle
        article_section = re.search(r'<div class="row g-4">(.*?)</div>', content, re.DOTALL)
        if article_section:
            new_content = content.replace(
                article_section.group(0),
                f'<div class="row g-4">{pdf_html}{article_section.group(1)}</div>'
            )
            
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"index.html güncellendi: PDF {title} eklendi")
        else:
            logger.error("row g-4 div'i bulunamadı!")

    except Exception as e:
        logger.error(f"index.html güncellenirken hata: {e}")
        raise

def convert_pdf_to_html(pdf_file):
    try:
        # Dosya adından başlığı al
        title = os.path.splitext(os.path.basename(pdf_file))[0]
        clean_title = clean_filename(title)
        
        logger.info(f"'{title}' PDF dosyası işleniyor...")
        
        # PDF için HTML şablonu
        pdf_template = '''<!DOCTYPE html>
<html lang="tr" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Osmanlıca Makaleler</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <link rel="stylesheet" href="../css/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body style="background-color: var(--bg-primary);">
    <nav class="navbar navbar-expand-lg bg-dark-subtle">
        <div class="container">
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="../index.html">Ana Sayfa</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="../index.html#makaleler">Makaleler</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="../about.html">Ömer Nasûhi Bilmen</a>
                    </li>
                </ul>
                <div class="theme-switcher d-flex align-items-center">
                    <i class="bi bi-sun-fill me-2 theme-icon" id="lightIcon"></i>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="themeSwitch">
                    </div>
                    <i class="bi bi-moon-fill ms-2 theme-icon" id="darkIcon"></i>
                </div>
            </div>
        </div>
    </nav>

    <main class="container py-5">
        <article class="latex-article">
            <div class="title-block">
                <h1 class="ottoman-title">{title}</h1>
                <p class="text-muted mt-3">
                    <i class="bi bi-calendar3 me-2"></i>
                    <span class="date">{date}</span>
                </p>
            </div>
            
            <div class="content">
                <div class="pdf-container">
                    <iframe src="../pdfs/{pdf_filename}.pdf" width="100%" height="800px" frameborder="0"></iframe>
                </div>
                <div class="text-center mt-4">
                    <a href="../pdfs/{pdf_filename}.pdf" class="btn btn-outline-light" download>
                        <i class="bi bi-download me-2"></i>PDF İndir
                    </a>
                </div>
            </div>
        </article>
    </main>

    <footer class="bg-dark-subtle text-center py-4 mt-5">
        <div class="container">
            <div class="mb-3">
                <a href="https://github.com/mevlut-celik" class="text-decoration-none" target="_blank">
                    <i class="bi bi-github fs-4"></i>
                </a>
            </div>
            <p class="mb-0">Ahmet Şengül - Mevlüt Çelik</p>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="../js/main.js"></script>
</body>
</html>'''

        # HTML dosyasını oluştur
        output_path = Path('articles') / f'{clean_title}.html'
        output_path.parent.mkdir(exist_ok=True)
        
        final_html = pdf_template.format(
            title=title,
            date=datetime.now().strftime('%d %B %Y'),
            pdf_filename=clean_title
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        logger.info(f"'{title}' PDF'i için HTML sayfası oluşturuldu: {output_path}")
        return clean_title

    except Exception as e:
        logger.error(f"PDF işlenirken hata: {e}")
        raise

def main():
    try:
        # Tüm makaleleri toplayacağımız liste
        all_articles = []
        
        # Osmanlıca makaleleri topla
        ottoman_folder = Path("word_articles")
        ottoman_folder.mkdir(exist_ok=True)
        for file in ottoman_folder.glob("*.docx"):
            logger.info(f"Osmanlıca makale işleniyor: {file}")
            article_filename, article_title = convert_docx_to_html(str(file))
            
            # Makale tarihini çıkar
            article_path = Path('articles') / f'{article_filename}.html'
            with open(article_path, 'r', encoding='utf-8') as f:
                article_content = f.read()
                article_date = extract_article_date(article_content)
            
            # Makale HTML'ini oluştur
            article_html = f'''
                <div class="col-md-6 col-lg-4" data-category="ottoman">
                    <div class="card h-100 bg-dark-subtle border-light">
                        <div class="card-body">
                            <span class="badge bg-primary mb-2">Osmanlı Türkçesi</span>
                            <h3 class="card-title h5 ottoman-title">
                                <a href="articles/{article_filename}.html" class="text-dark text-decoration-none">
                                    <i class="bi bi-journal-text me-2"></i>{article_title}
                                </a>
                            </h3>
                            <p class="card-text small text-light-emphasis">
                                <i class="bi bi-calendar3 me-2"></i>{article_date}
                            </p>
                        </div>
                    </div>
                </div>'''
            
            all_articles.append({
                'html': article_html,
                'date': parse_turkish_date(article_date)
            })

        # Türkçe makaleleri topla
        turkish_folder = Path("turkish_articles")
        turkish_folder.mkdir(exist_ok=True)
        for file in turkish_folder.glob("*.docx"):
            logger.info(f"Türkçe makale işleniyor: {file}")
            article_filename, article_title = convert_docx_to_html(str(file))
            
            # Makale tarihini çıkar
            article_path = Path('articles') / f'{article_filename}.html'
            with open(article_path, 'r', encoding='utf-8') as f:
                article_content = f.read()
                article_date = extract_article_date(article_content)
            
            # Makale HTML'ini oluştur
            article_html = f'''
                <div class="col-md-6 col-lg-4" data-category="turkish">
                    <div class="card h-100 bg-dark-subtle border-light">
                        <div class="card-body">
                            <span class="badge bg-primary mb-2">Türkçe</span>
                            <h3 class="card-title h5 ottoman-title">
                                <a href="articles/{article_filename}.html" class="text-dark text-decoration-none">
                                    <i class="bi bi-journal-text me-2"></i>{article_title}
                                </a>
                            </h3>
                            <p class="card-text small text-light-emphasis">
                                <i class="bi bi-calendar3 me-2"></i>{article_date}
                            </p>
                        </div>
                    </div>
                </div>'''
            
            all_articles.append({
                'html': article_html,
                'date': parse_turkish_date(article_date)
            })

        # Makaleleri tarihe göre sırala
        all_articles.sort(key=lambda x: x['date'], reverse=True)
        sorted_html = '\n'.join(article['html'] for article in all_articles)

        # index.html'i güncelle
        index_path = Path('index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = re.sub(
            r'<div class="row g-4">.*?</div>\s*</section>',
            f'<div class="row g-4">{sorted_html}</div></section>',
            content,
            flags=re.DOTALL
        )

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        logger.info("Tüm makaleler başarıyla işlendi!")

    except Exception as e:
        logger.error(f"Program çalışırken hata oluştu: {e}")
        raise

if __name__ == "__main__":
    main() 