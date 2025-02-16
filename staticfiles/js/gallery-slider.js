document.addEventListener('DOMContentLoaded', function() {
    const mainSlide = document.querySelector('.main-slide');
    const thumbs = document.querySelectorAll('.thumb');
    
    thumbs.forEach((thumb, index) => {
        thumb.addEventListener('click', () => {
            // Обновляем главное изображение
            mainSlide.src = thumb.querySelector('img').src;
            
            // Обновляем активный класс
            thumbs.forEach(t => t.classList.remove('active'));
            thumb.classList.add('active');
        });
        
        // Устанавливаем первый слайд как активный
        if (index === 0) {
            thumb.classList.add('active');
        }
    });
}); 