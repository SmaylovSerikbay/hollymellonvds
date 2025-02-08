document.addEventListener('DOMContentLoaded', function() {
    let lightbox = null;
    const selectedUrls = new Set();
    const downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
    const downloadAllBtn = document.getElementById('downloadAllBtn');
    const shareBtn = document.getElementById('shareBtn');
    const shareNotification = document.querySelector('.share-notification');
    const loadingOverlay = document.querySelector('.loading-overlay');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const albumPath = document.querySelector('.photos-grid').dataset.folderPath;

    // Создаем индикатор прогресса
    const progressIndicator = document.createElement('div');
    progressIndicator.className = 'progress-indicator';
    progressIndicator.innerHTML = `
        <div class="progress-text">Подготовка архива...</div>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <div class="progress-status">Ожидание ответа от Яндекс.Диска...</div>
    `;
    loadingSpinner.innerHTML = ''; // Очищаем спиннер
    loadingSpinner.appendChild(progressIndicator);

    // Создаем скрытую кнопку для скачивания
    const downloadLink = document.createElement('a');
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);

    // Функция для поделиться альбомом
    const shareAlbum = async () => {
        try {
            if (navigator.share) {
                await navigator.share({
                    title: document.title,
                    url: window.location.href
                });
            } else {
                await navigator.clipboard.writeText(window.location.href);
                shareNotification.classList.add('show');
                setTimeout(() => {
                    shareNotification.classList.remove('show');
                }, 2000);
            }
        } catch (err) {
            console.error('Ошибка при попытке поделиться:', err);
        }
    };

    // Инициализация PhotoSwipe
    const initPhotoSwipe = () => {
        const openPhotoSwipe = (index) => {
            const pswpElement = document.querySelector('.pswp');
            
            // Собираем все фотографии
            const items = Array.from(document.querySelectorAll('.photo-item img')).map(img => ({
                src: img.dataset.fullSize || img.src,
                w: 0,
                h: 0,
                msrc: img.src
            }));

            const options = {
                index: index,
                bgOpacity: 0.9,
                showHideOpacity: true,
                history: false,
                shareEl: false,
                zoomEl: true,
                tapToClose: false,
                clickToCloseNonZoomable: false,
                showAnimationDuration: 333,
                hideAnimationDuration: 333,
                maxSpreadZoom: 2,
                getThumbBoundsFn: (index) => {
                    const thumbnail = document.querySelectorAll('.photo-item img')[index];
                    const pageYScroll = window.pageYOffset || document.documentElement.scrollTop;
                    const rect = thumbnail.getBoundingClientRect();
                    return {x: rect.left, y: rect.top + pageYScroll, w: rect.width};
                }
            };

            // Создаем и инициализируем PhotoSwipe
            const gallery = new PhotoSwipe(pswpElement, PhotoSwipeUI_Default, items, options);
            
            // Загружаем реальные размеры изображений
            gallery.listen('gettingData', (index, item) => {
                if (!item.w || !item.h) {
                    const img = new Image();
                    img.onload = function() {
                        item.w = this.width;
                        item.h = this.height;
                        gallery.updateSize(true);
                    };
                    img.src = item.src;
                }
            });

            gallery.init();
        };

        // Добавляем обработчики для всех фотографий
        document.querySelectorAll('.photo-item').forEach((photo, index) => {
            // Обработчик для кнопки увеличения
            const zoomBtn = photo.querySelector('.zoom-photo');
            if (zoomBtn) {
                zoomBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    openPhotoSwipe(index);
                });
            }

            // Обработчик для клика по фото
            const photoOverlay = photo.querySelector('.photo-overlay');
            if (photoOverlay) {
                photoOverlay.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    openPhotoSwipe(index);
                });
            }
        });
    };

    // Функция для скачивания архива с Яндекс.Диска
    const downloadYandexArchive = async () => {
        loadingOverlay.style.display = 'flex';
        progressIndicator.style.display = 'block';
        progressIndicator.querySelector('.progress-fill').style.width = '50%';
        
        try {
            const response = await fetch(`/api/yandex/download-folder/?path=${encodeURIComponent(albumPath)}`);
            if (!response.ok) throw new Error('Ошибка при получении ссылки на скачивание');
            
            const data = await response.json();
            if (data.href) {
                progressIndicator.querySelector('.progress-fill').style.width = '100%';
                progressIndicator.querySelector('.progress-status').textContent = 'Начинаем скачивание...';
                window.location.href = data.href;
            } else {
                throw new Error('Не удалось получить ссылку на скачивание');
            }
        } catch (error) {
            console.error('Ошибка при скачивании архива:', error);
            alert('Произошла ошибка при подготовке архива для скачивания');
        } finally {
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
                progressIndicator.style.display = 'none';
                progressIndicator.querySelector('.progress-fill').style.width = '0%';
            }, 1000);
        }
    };

    // Функция скачивания отдельного файла
    const downloadFile = (url) => {
        window.open(url, '_blank');
    };

    // Функция для скачивания нескольких файлов
    const downloadMultipleFiles = (urls) => {
        const urlsArray = Array.from(urls);
        let currentIndex = 0;
        let totalFiles = urlsArray.length;

        loadingOverlay.style.display = 'flex';
        progressIndicator.style.display = 'block';

        const downloadNext = () => {
            if (currentIndex < urlsArray.length) {
                downloadFile(urlsArray[currentIndex]);
                currentIndex++;
                const percent = Math.round((currentIndex / totalFiles) * 100);
                progressIndicator.querySelector('.progress-fill').style.width = `${percent}%`;
                progressIndicator.querySelector('.progress-status').textContent = 
                    `Загружено ${currentIndex} из ${totalFiles} файлов`;
                setTimeout(downloadNext, 500);
            } else {
                loadingOverlay.style.display = 'none';
                progressIndicator.style.display = 'none';
            }
        };

        downloadNext();
    };

    // Обработчики для кнопок действий с фотографиями
    document.querySelectorAll('.photo-item').forEach(photo => {
        const downloadBtn = photo.querySelector('.download-photo');
        const selectBtn = photo.querySelector('.select-photo');
        const img = photo.querySelector('img');
        const url = img.getAttribute('data-full-size') || img.src;

        if (downloadBtn) {
            downloadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                downloadFile(url);
            });
        }

        if (selectBtn) {
            selectBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (selectedUrls.has(url)) {
                    selectedUrls.delete(url);
                    photo.classList.remove('selected');
                    selectBtn.querySelector('i').classList.replace('fa-check-square', 'fa-square');
                } else {
                    selectedUrls.add(url);
                    photo.classList.add('selected');
                    selectBtn.querySelector('i').classList.replace('fa-square', 'fa-check-square');
                }

                // Обновляем счетчик выбранных фотографий
                downloadSelectedBtn.querySelector('.counter').textContent = `(${selectedUrls.size})`;
            });
        }
    });

    // Обработчик для скачивания выбранных фотографий
    if (downloadSelectedBtn) {
        downloadSelectedBtn.addEventListener('click', () => {
            if (selectedUrls.size === 0) {
                alert('Пожалуйста, выберите фотографии для скачивания');
                return;
            }
            downloadMultipleFiles(selectedUrls);
        });
    }

    // Обработчик для скачивания всех фотографий
    if (downloadAllBtn) {
        downloadAllBtn.addEventListener('click', () => {
            downloadYandexArchive();
        });
    }

    // Обработчик для кнопки "Поделиться"
    if (shareBtn) {
        shareBtn.addEventListener('click', shareAlbum);
    }

    // Инициализация PhotoSwipe
    initPhotoSwipe();
}); 