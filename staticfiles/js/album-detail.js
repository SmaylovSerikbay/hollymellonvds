document.addEventListener('DOMContentLoaded', function() {
    const gallery = document.getElementById('gallery');
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

    // Обработка клика по фотографии
    function openPhotoSwipe(index) {
        const items = Array.from(gallery.querySelectorAll('.photo-item')).map(item => {
            const url = item.querySelector('img').dataset.fullSize;
            const previewUrl = item.querySelector('img').dataset.preview;
            // Всегда используем прокси для превью
            const proxyPreviewUrl = `/proxy-photo/?url=${encodeURIComponent(previewUrl)}`;
            return {
                src: proxyPreviewUrl,
                w: 1200,
                h: 800,
                originalUrl: url,
                msrc: item.querySelector('img').src
            };
        });

        const options = {
            index: index,
            bgOpacity: 0.9,
            showHideOpacity: true,
            history: false,
            shareEl: false,
            loadingIndicatorDelay: 0,
            showAnimationDuration: 0,
            hideAnimationDuration: 0,
            maxSpreadZoom: 2,
            getThumbBoundsFn: (index) => {
                const thumbnail = gallery.querySelectorAll('.photo-item img')[index];
                const pageYScroll = window.pageYOffset || document.documentElement.scrollTop;
                const rect = thumbnail.getBoundingClientRect();
                return {x: rect.left, y: rect.top + pageYScroll, w: rect.width};
            }
        };

        const pswp = new PhotoSwipe(document.querySelector('.pswp'), PhotoSwipeUI_Default, items, options);
        
        // Предзагрузка текущего и соседних изображений
        let loadQueue = [];
        let loadedImages = new Set();

        function preloadImage(index) {
            if (index < 0 || index >= items.length || loadedImages.has(index)) return;
            
            const item = items[index];
            loadQueue.push(index);
            loadedImages.add(index);

            const img = new Image();
            
            img.onload = function() {
                const loadIndex = loadQueue.indexOf(index);
                if (loadIndex !== -1) {
                    loadQueue.splice(loadIndex, 1);
                }
                
                item.w = this.width;
                item.h = this.height;
                
                if (pswp.currItem === item) {
                    pswp.updateSize(true);
                }
            };

            img.onerror = function() {
                const loadIndex = loadQueue.indexOf(index);
                if (loadIndex !== -1) {
                    loadQueue.splice(loadIndex, 1);
                }
                
                console.error('Ошибка загрузки изображения:', item.src);
                
                // Пробуем повторить загрузку через 1 секунду
                setTimeout(() => {
                    if (!loadedImages.has(index)) {
                        loadedImages.delete(index);
                        preloadImage(index);
                    }
                }, 1000);
            };

            img.src = item.src;
        }

        // Загружаем только текущее изображение при открытии
        pswp.listen('beforeChange', function() {
            const index = pswp.getCurrentIndex();
            loadQueue = [];
            preloadImage(index);
        });

        // После успешной загрузки текущего, загружаем соседние
        pswp.listen('imageLoadComplete', function(index) {
            setTimeout(() => {
                preloadImage(index - 1);
                preloadImage(index + 1);
            }, 100);
        });

        pswp.init();
    }

    // Обработка клика по фотографии или кнопке увеличения
    gallery.addEventListener('click', function(e) {
        const photoItem = e.target.closest('.photo-item');
        if (!photoItem) return;

        // Если клик был по кнопке скачивания или выбора, не открываем просмотрщик
        if (e.target.closest('.download-photo') || e.target.closest('.select-photo')) return;

        // Если клик был по кнопке увеличения или по самому фото
        if (e.target.closest('.zoom-photo') || e.target.closest('img')) {
            const index = Array.from(gallery.children).indexOf(photoItem);
            openPhotoSwipe(index);
        }
    });

    // Обработчики для кнопок действий с фотографиями
    document.querySelectorAll('.photo-item').forEach(photo => {
        const downloadBtns = photo.querySelectorAll('.download-photo');
        const selectBtns = photo.querySelectorAll('.select-photo');
        const img = photo.querySelector('img');
        const url = img.getAttribute('data-full-size') || img.src;

        downloadBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                downloadPhoto(url);
            });
        });

        selectBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                if (selectedUrls.has(url)) {
                    selectedUrls.delete(url);
                    photo.classList.remove('selected');
                } else {
                    selectedUrls.add(url);
                    photo.classList.add('selected');
                }

                // Обновляем счетчик выбранных фотографий
                downloadSelectedBtn.querySelector('.counter').textContent = `(${selectedUrls.size})`;
            });
        });
    });

    // Функция скачивания фото
    async function downloadPhoto(url) {
        try {
            loadingOverlay.style.display = 'flex';
            progressIndicator.style.display = 'block';
            progressIndicator.querySelector('.progress-text').textContent = 'Подготовка к скачиванию...';
            progressIndicator.querySelector('.progress-fill').style.width = '50%';

            // Создаем ссылку для скачивания
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank'; // Открываем в новой вкладке
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            progressIndicator.querySelector('.progress-fill').style.width = '100%';
            progressIndicator.querySelector('.progress-text').textContent = 'Скачивание начато';
            
        } catch (error) {
            console.error('Ошибка при скачивании:', error);
            alert(`Ошибка при скачивании фотографии: ${error.message}`);
        } finally {
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
                progressIndicator.style.display = 'none';
                progressIndicator.querySelector('.progress-fill').style.width = '0%';
            }, 1000);
        }
    }

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
        downloadAllBtn.addEventListener('click', downloadYandexArchive);
    }

    // Обработчик для кнопки "Поделиться"
    if (shareBtn) {
        shareBtn.addEventListener('click', shareAlbum);
    }

    // Функция для скачивания архива с Яндекс.Диска
    async function downloadYandexArchive() {
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
    }

    // Функция для скачивания нескольких файлов
    function downloadMultipleFiles(urls) {
        const urlsArray = Array.from(urls);
        let currentIndex = 0;
        let totalFiles = urlsArray.length;

        loadingOverlay.style.display = 'flex';
        progressIndicator.style.display = 'block';

        function downloadNext() {
            if (currentIndex < urlsArray.length) {
                downloadPhoto(urlsArray[currentIndex]);
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
        }

        downloadNext();
    }
}); 