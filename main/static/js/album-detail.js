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
    const qualityDialog = document.querySelector('.quality-dialog');
    let currentDownloadUrl = null;
    let currentDownloadCallback = null;

    // Создаем индикатор прогресса
    const progressIndicator = document.createElement('div');
    progressIndicator.className = 'progress-indicator';
    progressIndicator.innerHTML = `
        <div class="progress-text">Подготовка файлов...</div>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        <div class="progress-status">Ожидание ответа от Яндекс.Диска...</div>
    `;
    loadingSpinner.innerHTML = ''; // Очищаем спиннер
    loadingSpinner.appendChild(progressIndicator);

    // Функция для показа индикатора загрузки
    function showLoading(message = 'Загрузка...') {
        loadingOverlay.style.display = 'flex';
        progressIndicator.style.display = 'block';
        progressIndicator.querySelector('.progress-text').textContent = message;
    }

    // Функция для скрытия индикатора загрузки
    function hideLoading() {
        loadingOverlay.style.display = 'none';
        progressIndicator.style.display = 'none';
    }

    // Функция для обновления прогресса
    function updateProgress(percent, status) {
        progressIndicator.querySelector('.progress-fill').style.width = `${percent}%`;
        progressIndicator.querySelector('.progress-status').textContent = status;
    }

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

    // Функция для получения размеров изображения
    function getImageDimensions(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = function() {
                resolve({ width: this.width, height: this.height });
            };
            img.onerror = reject;
            img.src = url;
        });
    }

    // Обработка клика по фотографии
    async function openPhotoSwipe(index) {
        const items = Array.from(gallery.querySelectorAll('.photo-item')).map(item => {
            const img = item.querySelector('img');
            const naturalWidth = img.naturalWidth || 800;
            const naturalHeight = img.naturalHeight || 600;
            const aspectRatio = naturalHeight / naturalWidth;
            
            return {
                src: img.dataset.fullSize,
                msrc: img.src,
                w: naturalWidth || 800,
                h: naturalHeight || Math.round(800 * aspectRatio),
                title: img.alt
            };
        });

        const options = {
            index: index,
            bgOpacity: 0.9,
            showHideOpacity: true,
            history: false,
            shareEl: false,
            showAnimationDuration: 333,
            hideAnimationDuration: 333,
            getThumbBoundsFn: (index) => {
                const thumbnail = gallery.querySelectorAll('.photo-item img')[index];
                const pageYScroll = window.pageYOffset || document.documentElement.scrollTop;
                const rect = thumbnail.getBoundingClientRect();
                return {x: rect.left, y: rect.top + pageYScroll, w: rect.width};
            },
            zoomEl: true,
            getDoubleTapZoom: function(isMouseClick, item) {
                return isMouseClick ? 2 : 1;
            },
            pinchToClose: true,
            closeOnScroll: false,
            closeOnVerticalDrag: true,
            captionEl: false,
            fullscreenEl: true,
            tapToToggleControls: true
        };

        const pswp = new PhotoSwipe(document.querySelector('.pswp'), PhotoSwipeUI_Default, items, options);
        
        // Загружаем реальные размеры изображения в фоновом режиме для уточнения
        pswp.listen('gettingData', function(index, item) {
            if (!item.loaded) {
                const img = new Image();
                img.onload = function() {
                    // Обновляем размеры только если они существенно отличаются
                    if (Math.abs(item.w - this.width) > 50 || Math.abs(item.h - this.height) > 50) {
                        item.w = this.width;
                        item.h = this.height;
                        item.loaded = true;
                        pswp.updateSize(true);
                    }
                };
                img.src = item.src;
            }
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

    // Функция для показа диалога выбора качества
    function showQualityDialog(url, callback) {
        currentDownloadUrl = url;
        currentDownloadCallback = callback;
        qualityDialog.style.display = 'flex';
    }

    // Обработчики для диалога выбора качества
    qualityDialog.querySelector('.quality-dialog-close').addEventListener('click', () => {
        qualityDialog.style.display = 'none';
    });

    qualityDialog.querySelectorAll('.quality-option').forEach(button => {
        button.addEventListener('click', () => {
            const quality = button.dataset.quality;
            qualityDialog.style.display = 'none';
            
            if (currentDownloadCallback) {
                const finalUrl = quality === 'mobile' ? 
                    currentDownloadUrl.replace('&preview=1', '') : 
                    currentDownloadUrl;
                currentDownloadCallback(finalUrl, quality === 'mobile');
            }
        });
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
                showQualityDialog(url, downloadPhoto);
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

    // Функция скачивания фото с индикацией прогресса
    async function downloadPhoto(url, showProgress = true, isMobileQuality = false) {
        if (isMobileQuality) {
            // Для мобильной версии используем прямую ссылку на превью
            const img = document.querySelector(`img[data-full-size="${url}"]`);
            if (img) {
                const previewUrl = img.src.replace('/proxy-photo/?url=', '');
                window.location.href = decodeURIComponent(previewUrl);
                return;
            }
        }

        // Для оригинального качества
        if (showProgress) {
            showLoading('Подготовка файла к скачиванию...');
        }
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Ошибка при загрузке фотографии');
            
            const blob = await response.blob();
            const filename = url.split('/').pop().split('?')[0];
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Ошибка при скачивании:', error);
            alert('Произошла ошибка при скачивании фотографии');
        } finally {
            if (showProgress) {
                hideLoading();
            }
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

    // Функция для скачивания архива с Яндекс.Дискав
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
    async function downloadMultipleFiles(urls) {
        showQualityDialog(null, async (_, isMobileQuality) => {
            if (isMobileQuality) {
                // Для мобильной версии открываем все превью в новых вкладках
                Array.from(urls).forEach(url => {
                    const img = document.querySelector(`img[data-full-size="${url}"]`);
                    if (img) {
                        const previewUrl = img.src.replace('/proxy-photo/?url=', '');
                        window.open(decodeURIComponent(previewUrl), '_blank');
                    }
                });
                return;
            }

            // Для оригинального качества оставляем как есть
            const urlsArray = Array.from(urls);
            let currentIndex = 0;
            let totalFiles = urlsArray.length;

            showLoading('Подготовка файлов к скачиванию...');

            for (const url of urlsArray) {
                currentIndex++;
                const percent = Math.round((currentIndex / totalFiles) * 100);
                updateProgress(percent, `Загружено ${currentIndex} из ${totalFiles} файлов`);
                
                await downloadPhoto(url, false, false);
                await new Promise(resolve => setTimeout(resolve, 300));
            }

            hideLoading();
        });
    }
}); 