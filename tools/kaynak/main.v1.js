document.addEventListener('DOMContentLoaded', function() {
    const categoryButtons = document.querySelectorAll('.category-list .btn');
    const articles = document.querySelectorAll('.row > [data-category]');

    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Aktif kategori butonunu güncelle
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const selectedCategory = button.dataset.category;

            // Makaleleri filtrele
            articles.forEach(article => {
                const parent = article.parentElement;
                if (selectedCategory === 'all' || article.dataset.category === selectedCategory) {
                    article.style.display = '';
                    // Animasyon ekle
                    article.style.animation = 'fadeIn 0.5s ease-out forwards';
                } else {
                    article.style.display = 'none';
                }
            });
        });
    });

    // Sayfa yüklendiğinde animasyon ekle
    articles.forEach((article, index) => {
        article.style.animationDelay = `${index * 0.1}s`;
    });

    // Tema değiştirme fonksiyonları
    const themeSwitch = document.getElementById('themeSwitch');
    const lightIcon = document.getElementById('lightIcon');
    const darkIcon = document.getElementById('darkIcon');
    
    // Kaydedilmiş temayı kontrol et
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
        themeSwitch.checked = savedTheme === 'dark';
    }
    
    // Tema değiştirici için event listener
    themeSwitch.addEventListener('change', function() {
        const theme = this.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
    });
    
    // İkonları güncelle
    function updateIcons() {
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        lightIcon.style.opacity = isDark ? '0.5' : '1';
        darkIcon.style.opacity = isDark ? '1' : '0.5';
    }
    
    themeSwitch.addEventListener('change', updateIcons);
    updateIcons(); // Sayfa yüklendiğinde ikonları güncelle
}); 