document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const header = document.querySelector('.header');
    const themeBtn = document.getElementById('themeBtn');
    const searchBtn = document.getElementById('searchBtn');
    const searchModal = document.querySelector('.search-modal');
    const searchInput = document.querySelector('.search-modal__input');
    const searchClose = document.querySelector('.search-modal__close');
    const mobileToggle = document.querySelector('.mobile-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    const citySelect = document.querySelector('.city-select');
    const cityDropdown = document.querySelector('.city-dropdown');
    const cityOptions = document.querySelectorAll('.city-option');
    
    const mobileCities = document.querySelectorAll('.mobile-menu__city');
    const mobileLocationBtn = document.querySelector('.mobile-menu__location-btn');
    const mobileCitiesList = document.querySelector('.mobile-menu__cities');

    // Получаем сохраненную тему или используем светлую по умолчанию
    const savedTheme = localStorage.getItem('theme') || 'light';
    const body = document.body;
    const themeIcon = themeBtn.querySelector('i');

    // Функция установки темы
    function setTheme(theme) {
        if (theme === 'light') {
            body.classList.add('light');
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        } else {
            body.classList.remove('light');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
        localStorage.setItem('theme', theme);
    }

    // Устанавливаем начальную тему
    setTheme(savedTheme);

    // Обработчик клика по кнопке темы
    themeBtn.addEventListener('click', function() {
        const currentTheme = body.classList.contains('light') ? 'dark' : 'light';
        setTheme(currentTheme);
    });

    // Header Scroll Effect
    function handleScroll() {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }

    window.addEventListener('scroll', handleScroll);
    handleScroll();

    // Мобильное меню
    if (mobileToggle && mobileMenu) {
        mobileToggle.addEventListener('click', () => {
            mobileToggle.classList.toggle('active');
            mobileMenu.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
    }

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (mobileMenu && mobileMenu.classList.contains('active')) {
            if (!mobileMenu.contains(e.target) && !mobileToggle.contains(e.target)) {
                mobileToggle.classList.remove('active');
                mobileMenu.classList.remove('active');
                document.body.classList.remove('menu-open');
            }
        }
    });

    // Close menu when pressing Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mobileMenu && mobileMenu.classList.contains('active')) {
            mobileToggle.classList.remove('active');
            mobileMenu.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    });

    // Выбор города
    if (citySelect && cityDropdown && cityOptions) {
        function initCity() {
            const savedCity = localStorage.getItem('selectedCity');
            if (savedCity) {
                document.querySelectorAll('.city-select span').forEach(span => {
                    span.textContent = savedCity;
                });
            }
        }

        citySelect.addEventListener('click', (e) => {
            e.stopPropagation();
            cityDropdown.classList.toggle('active');
        });

        cityOptions.forEach(option => {
            option.addEventListener('click', () => {
                const city = option.textContent;
                document.querySelectorAll('.city-select span').forEach(span => {
                    span.textContent = city;
                });
                localStorage.setItem('selectedCity', city);
                cityDropdown.classList.remove('active');
            });
        });

        // Закрытие выпадающего меню города при клике вне
        document.addEventListener('click', () => {
            cityDropdown.classList.remove('active');
        });

        initCity();
    }

    // Search Modal
    if (searchBtn && searchModal && searchClose) {
        function openSearch() {
            searchModal.classList.add('active');
            document.body.style.overflow = 'hidden';
            if (searchInput) {
                setTimeout(() => searchInput.focus(), 100);
            }
        }

        function closeSearch() {
            searchModal.classList.remove('active');
            document.body.style.overflow = '';
            if (searchInput) {
                searchInput.value = '';
            }
        }

        searchBtn.addEventListener('click', openSearch);
        searchClose.addEventListener('click', closeSearch);

        // Close search on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && searchModal.classList.contains('active')) {
                closeSearch();
            }
        });
    }

    // Плавная прокрутка
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerOffset = header.offsetHeight;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });

                // Закрываем мобильное меню при клике на ссылку
                if (mobileMenu.classList.contains('active')) {
                    mobileToggle.click();
                }
            }
        });
    });

    // Инициализация бегущей строки
    const tickers = document.querySelectorAll('.ticker__content');
    tickers.forEach(ticker => {
        if (!ticker) return;
        
        // Дублируем контент для бесконечной анимации
        const content = ticker.innerHTML;
        ticker.innerHTML = content + content;

        // Обработчики для паузы при наведении
        ticker.addEventListener('mouseenter', () => {
            ticker.style.animationPlayState = 'paused';
        });

        ticker.addEventListener('mouseleave', () => {
            ticker.style.animationPlayState = 'running';
        });
    });

    // Инициализация галереи
    const initGallery = () => {
        const mainImage = document.querySelector('.main-slide');
        const thumbs = document.querySelectorAll('.thumb');
        
        if (!mainImage || !thumbs.length) return;

        thumbs.forEach(thumb => {
            thumb.addEventListener('click', () => {
                mainImage.src = thumb.querySelector('img').src;
                thumbs.forEach(t => t.classList.remove('active'));
                thumb.classList.add('active');
            });
        });
    };

    // Вызываем инициализацию галереи
    initGallery();

    // Обработка выбора города
    const locationButtons = document.querySelectorAll('.location-btn');
    const locationMenus = document.querySelectorAll('.location-menu');
    const locationOptions = document.querySelectorAll('.location-option');

    // Функция для обновления города
    function updateCity(cityId, cityName) {
        fetch('/set-city/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ city_id: cityId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                // Обновляем отображение города во всех меню
                document.querySelectorAll('.location-btn span').forEach(span => {
                    span.textContent = cityName;
                });
                document.querySelector('.mobile-menu__location-btn span').textContent = cityName;
                
                // Обновляем активные классы
                locationOptions.forEach(option => {
                    option.classList.toggle('active', option.dataset.cityId === cityId);
                });
                mobileCities.forEach(city => {
                    city.classList.toggle('active', city.textContent.trim() === cityName);
                });
                
                // Перезагружаем страницу для обновления контента
                window.location.reload();
            }
        });
    }

    // Обработчики для десктопного меню
    locationButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            const menu = button.nextElementSibling;
            menu.classList.toggle('active');
        });
    });

    locationOptions.forEach(option => {
        option.addEventListener('click', () => {
            const cityId = option.dataset.cityId;
            const cityName = option.textContent.trim();
            updateCity(cityId, cityName);
        });
    });

    // Обработчики для мобильного меню
    if (mobileLocationBtn && mobileCitiesList) {
        mobileLocationBtn.addEventListener('click', () => {
            mobileCitiesList.classList.toggle('active');
        });

        mobileCities.forEach(city => {
            city.addEventListener('click', () => {
                const cityId = city.dataset.cityId;
                const cityName = city.textContent.trim();
                updateCity(cityId, cityName);
            });
        });
    }

    // Закрытие меню при клике вне
    document.addEventListener('click', () => {
        locationMenus.forEach(menu => menu.classList.remove('active'));
        if (mobileCitiesList) {
            mobileCitiesList.classList.remove('active');
        }
    });

    // Функция для получения CSRF токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}); 