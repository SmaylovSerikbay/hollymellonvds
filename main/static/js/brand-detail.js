document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для истории бренда
    const brandHistory = document.querySelector('.brand-history');
    const historyHeader = document.querySelector('.brand-history-header');

    if (historyHeader) {
        historyHeader.addEventListener('click', function() {
            brandHistory.classList.toggle('active');
        });
    }

    // Обработчик для галереи
    const thumbs = document.querySelectorAll('.thumb');
    const mainImage = document.querySelector('.main-slide');

    thumbs.forEach(thumb => {
        thumb.addEventListener('click', function() {
            // Убираем активный класс у всех миниатюр
            thumbs.forEach(t => t.classList.remove('active'));
            // Добавляем активный класс текущей миниатюре
            this.classList.add('active');
            // Обновляем основное изображение
            mainImage.src = this.querySelector('img').src;
        });
    });
}); 