from django.contrib import admin
from django import forms
from .models import (
    Brand, TopGalleryImage, Feature, SpecialOffer, City, BrandTicker,
    BrandsPageSettings, PhotoAlbum, SiteSettings, Announcement,
    AnnouncementItem, AnnouncementMedia, HomeHero, SiteLogo, Photographer,
    TeamPage
)
from .utils import get_yandex_folders

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    ordering = ['order', 'name']

class TopGalleryInline(admin.TabularInline):
    model = TopGalleryImage
    extra = 1
    verbose_name = 'Изображение верхней галереи'
    verbose_name_plural = 'Верхняя галерея (слайдер)'

class FeatureInline(admin.TabularInline):
    model = Feature
    extra = 1

class SpecialOfferInline(admin.TabularInline):
    model = SpecialOffer
    extra = 1

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'show_rating')
    list_filter = ('location', 'rating')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TopGalleryInline, FeatureInline, SpecialOfferInline]

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name', 'slug', 'subtitle', 'description', 
                'brand_history', 'rating'
            )
        }),
        ('Основные изображения', {
            'fields': (
                'hero_image', 'main_image'
            ),
            'description': 'Hero - для верхнего баннера, Main - для карточки бренда'
        }),
        ('Адрес и контакты', {
            'fields': (
                'location', 'address', 'phone', 
                'whatsapp', 'two_gis'
            )
        }),
        ('Время работы', {
            'fields': ('work_hours_weekdays', 'work_hours_weekends')
        })
    )

    def show_rating(self, obj):
        return '⭐' * obj.rating
    show_rating.short_description = 'Рейтинг'

@admin.register(BrandTicker)
class BrandTickerAdmin(admin.ModelAdmin):
    list_display = ('text', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('text',)
    ordering = ('order',)

@admin.register(BrandsPageSettings)
class BrandsPageSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Запрещаем создание новых настроек, если они уже существуют
        return not BrandsPageSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление настроек
        return False

class PhotoAlbumForm(forms.ModelForm):
    yandex_folder = forms.ChoiceField(
        label='Папка на Яндекс.Диске',
        choices=[],
        help_text='Выберите папку из Яндекс.Диска'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем токен из настроек
        settings = SiteSettings.objects.first()
        if settings and settings.yandex_token:
            folders = get_yandex_folders(settings.yandex_token)
            self.fields['yandex_folder'].choices = [
                (folder['path'].strip('/'), folder['name']) for folder in folders
            ]
        else:
            self.fields['yandex_folder'].choices = [('', 'Сначала добавьте токен в настройках сайта')]

    class Meta:
        model = PhotoAlbum
        fields = '__all__'

@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    ordering = ['order', 'name']

@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(admin.ModelAdmin):
    form = PhotoAlbumForm
    list_display = ['brand', 'photographer', 'date', 'is_active']
    list_filter = ['brand', 'photographer', 'is_active', 'date']
    search_fields = ['brand__name', 'photographer__name']
    ordering = ['-date', 'order']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('brand', 'photographer', 'date')
        }),
        ('Медиа', {
            'fields': ('cover_image', 'yandex_folder',)
        }),
        ('Дополнительно', {
            'fields': ('is_active', 'order', 'created_at')
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        settings = SiteSettings.objects.first()
        if not settings or not settings.yandex_token:
            form.base_fields['yandex_folder'].widget.attrs['readonly'] = True
            form.base_fields['yandex_folder'].help_text = 'Для выбора папки необходимо добавить токен Яндекс.Диска в настройках сайта'
        return form

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Настройки Яндекс.Диска', {
            'fields': ('yandex_token',),
        }),
        ('О нас', {
            'fields': ('about_text', 'about_image', 'email', 'instagram_link', 'tiktok_link'),
            'description': 'Настройки для секции "О нас" на главной странице'
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

class AnnouncementMediaInline(admin.TabularInline):
    model = AnnouncementMedia
    extra = 1
    fields = ('file', 'is_video', 'order')
    can_delete = True
    show_change_link = True

class AnnouncementItemInline(admin.TabularInline):
    model = AnnouncementItem
    extra = 1
    fields = ('title', 'description', 'order')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'city', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'type', 'city')
    search_fields = ('header', 'items__title', 'items__description')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-created_at')
    inlines = [AnnouncementMediaInline, AnnouncementItemInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('type', 'city', 'is_active', 'order'),
        }),
        ('Заголовок события', {
            'fields': ('header',),
            'description': 'Заголовок отображается над списком анонсов на главной странице. '
                         'Например: "Готовимся к захватывающему событию: уже [дата] мы ждем вас на [название мероприятия]"'
        }),
    )

    class Media:
        css = {
            'all': ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css']
        }

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'icon':
            field.help_text = field.help_text + ' <br>Доступные иконки можно посмотреть на <a href="https://fontawesome.com/icons" target="_blank">Font Awesome</a>'
        return field

@admin.register(HomeHero)
class HomeHeroAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    ordering = ('order',)
    
    fieldsets = (
        ('Настройки', {
            'fields': ('background_image', 'is_active', 'order'),
        }),
    )

@admin.register(SiteLogo)
class SiteLogoAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_active']
    list_editable = ['is_active']

@admin.register(TeamPage)
class TeamPageAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'subtitle', 'main_text'),
        }),
        ('Статистика', {
            'fields': ('statistics',),
            'description': 'Введите статистические данные в формате JSON списка. Например: ["Средний стаж работы в компании — от 4-х лет", "11 проектов по всему Казахстану"]'
        }),
        ('Набор сотрудников', {
            'fields': ('recruitment_text', 'email'),
        }),
        ('О нас', {
            'fields': ('about_title', 'about_text'),
        }),
        ('Кто мы', {
            'fields': ('who_we_are_title', 'who_we_are_items', 'who_we_are_conclusion'),
            'description': 'Введите пункты "Кто мы" в формате JSON списка. Например: ["Сеть из 11 брендов в сфере HoReCa, которые знают и любят", "Команда из более чем 450 профессионалов"]'
        }),
        ('Изображения', {
            'fields': ('image1', 'image2'),
        }),
    )

    def has_add_permission(self, request):
        return not TeamPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
