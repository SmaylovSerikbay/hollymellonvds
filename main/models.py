from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from .utils import compress_image

# Create your models here.

class City(models.Model):
    name = models.CharField('Название города', max_length=100)
    is_active = models.BooleanField('Активен', default=True)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class Brand(models.Model):
    # Основная информация
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('URL', unique=True, blank=True)
    subtitle = models.CharField('Подзаголовок', max_length=200, blank=True)
    description = models.TextField('Описание', blank=True)
    brand_history = models.TextField('История бренда', blank=True)
    rating = models.IntegerField('Рейтинг', default=5, choices=[(i, str(i)) for i in range(1, 6)])
    ticker_text = models.TextField(
        verbose_name='Текст бегущей строки',
        blank=True,
        help_text='Каждое слово или фраза с новой строки'
    )

    # Адрес и контакты
    location = models.ForeignKey(City, on_delete=models.PROTECT, verbose_name='Город')
    address = models.CharField('Адрес', max_length=255, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True)
    two_gis = models.URLField('2GIS', blank=True)

    # Время работы
    work_hours_weekdays = models.CharField('Время работы (Пн-Пт)', max_length=50, blank=True)
    work_hours_weekends = models.CharField('Время работы (Сб-Вс)', max_length=50, blank=True)

    # Основные изображения
    hero_image = models.ImageField('Hero изображение (верхний баннер)', upload_to='brands/hero/', blank=True)
    main_image = models.ImageField('Главное изображение (карточка)', upload_to='brands/main/', blank=True)

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('brand_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Сжимаем изображения перед сохранением
        if self.hero_image:
            self.hero_image = compress_image(self.hero_image)
        super().save(*args, **kwargs)

class TopGalleryImage(models.Model):
    """Галерея изображений бренда"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField('Изображение', upload_to='brands/gallery/')

    class Meta:
        verbose_name = 'Изображение галереи'
        verbose_name_plural = 'Галерея'

    def __str__(self):
        return f'Изображение галереи {self.brand.name}'

    def save(self, *args, **kwargs):
        if self.image:
            self.image = compress_image(self.image)
        super().save(*args, **kwargs)

class Feature(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='features')
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')

    class Meta:
        verbose_name = 'Особенность'
        verbose_name_plural = 'Особенности'

    def __str__(self):
        return self.title

class SpecialOffer(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='special_offers')
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'

    def __str__(self):
        return self.title

class BrandTicker(models.Model):
    text = models.CharField(max_length=500, verbose_name="Текст бегущей строки")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    hero_image = models.ImageField('Hero изображение', upload_to='brands/hero/', blank=True)

    class Meta:
        verbose_name = "Бегущая строка брендов"
        verbose_name_plural = "Бегущие строки брендов"
        ordering = ['order']

    def __str__(self):
        return self.text[:50]

class BrandsPageSettings(models.Model):
    show_hero = models.BooleanField('Показывать Hero секцию', default=True)
    show_ticker = models.BooleanField('Показывать бегущую строку', default=True)

    class Meta:
        verbose_name = 'Настройки страницы брендов'
        verbose_name_plural = 'Настройки страницы брендов'

    def save(self, *args, **kwargs):
        if not self.pk and BrandsPageSettings.objects.exists():
            return  # Предотвращаем создание более одной записи
        return super(BrandsPageSettings, self).save(*args, **kwargs)

    def __str__(self):
        return 'Настройки страницы брендов'

class SiteSettings(models.Model):
    yandex_token = models.CharField(
        max_length=200,
        verbose_name='Токен Яндекс.Диска',
        help_text='OAuth токен для доступа к Яндекс.Диску'
    )
    
    # Поля для секции "О нас"
    about_text = models.TextField(
        verbose_name='О нас',
        help_text='Текст для секции "О нас"',
        blank=True
    )
    about_image = models.ImageField(
        upload_to='about/',
        verbose_name='Изображение для секции "О нас"',
        help_text='Рекомендуемый размер: 1920x1080px',
        blank=True,
        null=True
    )
    email = models.EmailField(
        verbose_name='Email',
        help_text='Контактный email',
        blank=True
    )
    instagram_link = models.URLField(
        verbose_name='Ссылка на Instagram',
        help_text='Полный URL вашего Instagram аккаунта',
        blank=True
    )
    tiktok_link = models.URLField(
        verbose_name='Ссылка на TikTok',
        help_text='Полный URL вашего TikTok аккаунта',
        blank=True
    )

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            return  # Предотвращаем создание более одной записи
        return super(SiteSettings, self).save(*args, **kwargs)

    def __str__(self):
        return 'Настройки сайта'

class Photographer(models.Model):
    name = models.CharField('Имя фотографа', max_length=100)
    is_active = models.BooleanField('Активен', default=True)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фотограф'
        verbose_name_plural = 'Фотографы'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class PhotoAlbum(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, verbose_name='Заведение', null=True, blank=True)
    photographer = models.ForeignKey(Photographer, on_delete=models.PROTECT, verbose_name='Фотограф', null=True, blank=True)
    cover_image = models.ImageField('Обложка', upload_to='albums/covers/', blank=True)
    yandex_folder = models.CharField(
        max_length=200, 
        verbose_name='Папка на Яндекс.Диске',
        help_text='Укажите путь к папке на Яндекс.Диске (например: Photos/Events/2024)'
    )
    date = models.DateField(verbose_name='Дата')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.IntegerField(default=0, verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True)
    yandex_preview_url = models.URLField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'Фотоальбом'
        verbose_name_plural = 'Фотоальбомы'
        ordering = ['-date', 'order']

    def __str__(self):
        return f"{self.brand.name} - {self.date.strftime('%d.%m.%Y')}"

class Announcement(models.Model):
    ANNOUNCEMENT_TYPES = [
        ('event', 'Событие'),
        ('promo', 'Акция'),
        ('news', 'Новость'),
    ]

    type = models.CharField('Тип анонса', max_length=20, choices=ANNOUNCEMENT_TYPES, default='promo')
    header = models.TextField('Заголовок анонса', blank=True, help_text='Например: "Готовимся к захватывающему событию: уже [дата] мы ждем вас на [название мероприятия]"')
    city = models.ForeignKey(City, on_delete=models.PROTECT, verbose_name='Город', null=True, blank=True)
    is_active = models.BooleanField('Активно', default=True)
    order = models.IntegerField('Порядок', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Анонс'
        verbose_name_plural = 'Анонсы'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"Анонс #{self.id}"

class AnnouncementMedia(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='media', verbose_name='Анонс')
    file = models.FileField('Медиафайл', upload_to='announcements/')
    is_video = models.BooleanField('Это видео', default=False)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Медиафайл анонса'
        verbose_name_plural = 'Медиафайлы анонса'
        ordering = ['order']

    def __str__(self):
        return f'Медиафайл для {self.announcement}'

    def delete(self, *args, **kwargs):
        # Удаляем файл с диска
        if self.file:
            storage = self.file.storage
            if storage.exists(self.file.name):
                storage.delete(self.file.name)
        super().delete(*args, **kwargs)

class AnnouncementItem(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='items', verbose_name='Анонс')
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание')
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Элемент анонса'
        verbose_name_plural = 'Элементы анонса'
        ordering = ['order']

    def __str__(self):
        return self.title

class HomeHero(models.Model):
    background_image = models.ImageField('Фоновое изображение', upload_to='hero/')
    is_active = models.BooleanField('Активно', default=True)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Hero секция'
        verbose_name_plural = 'Hero секции'
        ordering = ['order']

    def __str__(self):
        return f"Hero изображение #{self.id}"

class SiteLogo(models.Model):
    light_theme_logo = models.ImageField(upload_to='logos/', verbose_name='Логотип для светлой темы')
    dark_theme_logo = models.ImageField(upload_to='logos/', verbose_name='Логотип для темной темы')
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    
    class Meta:
        verbose_name = 'Логотип сайта'
        verbose_name_plural = 'Логотипы сайта'
    
    def save(self, *args, **kwargs):
        if self.is_active:
            # Деактивируем все другие логотипы
            SiteLogo.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

class TeamStatistic(models.Model):
    team = models.ForeignKey('TeamPage', on_delete=models.CASCADE, related_name='statistics', verbose_name='Страница команды')
    text = models.CharField('Текст', max_length=255)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Статистика команды'
        verbose_name_plural = 'Статистика команды'
        ordering = ['order']

    def __str__(self):
        return self.text

class TeamWhoWeAreItem(models.Model):
    team = models.ForeignKey('TeamPage', on_delete=models.CASCADE, related_name='who_we_are_items', verbose_name='Страница команды')
    text = models.CharField('Текст', max_length=255)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Пункт "Кто мы"'
        verbose_name_plural = 'Пункты "Кто мы"'
        ordering = ['order']

    def __str__(self):
        return self.text

class TeamPage(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    subtitle = models.CharField('Подзаголовок', max_length=200)
    main_text = models.TextField('Основной текст')
    recruitment_text = models.TextField('Текст о наборе сотрудников')
    email = models.EmailField('Email для связи')
    about_title = models.CharField('Заголовок "О нас"', max_length=200)
    about_text = models.TextField('Текст "О нас"')
    who_we_are_title = models.CharField('Заголовок "Кто мы"', max_length=200)
    who_we_are_conclusion = models.TextField('Заключение "Кто мы"')
    image1 = models.ImageField('Изображение 1', upload_to='team/')
    image2 = models.ImageField('Изображение 2', upload_to='team/')

    class Meta:
        verbose_name = 'Страница команды'
        verbose_name_plural = 'Страница команды'

    def __str__(self):
        return 'Настройки страницы команды'

    def save(self, *args, **kwargs):
        if not self.pk and TeamPage.objects.exists():
            return  # Предотвращаем создание более одной записи
        return super(TeamPage, self).save(*args, **kwargs)

class TeamEstablishment(models.Model):
    team = models.ForeignKey('TeamPage', on_delete=models.CASCADE, related_name='establishments', verbose_name='Страница команды')
    city = models.CharField('Город', max_length=100)
    name = models.CharField('Название', max_length=200)
    year = models.CharField('Год', max_length=20)
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Заведение'
        verbose_name_plural = 'Заведения'
        ordering = ['city', 'order']

    def __str__(self):
        return f"{self.name} — {self.year}"
