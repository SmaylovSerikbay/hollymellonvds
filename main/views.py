from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Brand, City, BrandTicker, BrandsPageSettings, PhotoAlbum, SiteSettings, Announcement
import json
from django.views.decorators.cache import cache_page
import requests

def get_yandex_token():
    """Получает токен Яндекс.Диска из настроек"""
    settings = SiteSettings.objects.first()
    return settings.yandex_token if settings else ''

# Create your views here.

def home(request):
    current_city_id = request.session.get('current_city_id')
    if current_city_id:
        latest_brands = Brand.objects.filter(location_id=current_city_id).order_by('-id')[:4]
        latest_albums = PhotoAlbum.objects.filter(city_id=current_city_id).order_by('-date')[:10]
        current_city = City.objects.get(id=current_city_id).name
    else:
        latest_brands = Brand.objects.all().order_by('-id')[:4]
        latest_albums = PhotoAlbum.objects.all().order_by('-date')[:10]
        current_city = None
    
    context = {
        'announcements': Announcement.objects.filter(is_active=True),
        'site_settings': SiteSettings.objects.first(),
        'latest_brands': latest_brands,
        'latest_albums': latest_albums,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city
    }
    return render(request, 'main/home.html', context)

def get_cities(request):
    return City.objects.filter(is_active=True).order_by('order', 'name')

def set_city(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        city_id = data.get('city_id')
        if city_id:
            request.session['current_city_id'] = city_id
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})

def brands(request):
    current_city_id = request.session.get('current_city_id')
    if current_city_id:
        brands = Brand.objects.filter(location_id=current_city_id)
        current_city = City.objects.get(id=current_city_id).name
    else:
        brands = Brand.objects.all()
        current_city = None
    
    ticker_texts = BrandTicker.objects.filter(is_active=True)
    page_settings = BrandsPageSettings.objects.first() or BrandsPageSettings.objects.create()
    
    context = {
        'brands': brands,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city,
        'ticker_texts': ticker_texts,
        'page_settings': page_settings,
    }
    return render(request, 'main/brands.html', context)

def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    current_city_id = request.session.get('current_city_id')
    current_city = City.objects.get(id=current_city_id).name if current_city_id else None
    
    context = {
        'brand': brand,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city,
        'top_gallery': brand.top_gallery.all(),
        'bottom_gallery': brand.bottom_gallery.all()
    }
    return render(request, 'main/brand_detail.html', context)

def photo_gallery(request):
    current_city_id = request.session.get('current_city_id')
    if current_city_id:
        albums = PhotoAlbum.objects.filter(city_id=current_city_id)
        current_city = City.objects.get(id=current_city_id).name
    else:
        albums = PhotoAlbum.objects.all()
        current_city = None
    
    context = {
        'albums': albums,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city
    }
    return render(request, 'main/photo_gallery.html', context)

def album_detail(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk)
    yandex_token = get_yandex_token()
    
    # Получаем текущий город
    current_city_id = request.session.get('current_city_id')
    current_city = City.objects.get(id=current_city_id).name if current_city_id else None
    
    # Проверяем наличие токена
    if not yandex_token:
        context = {
            'album': album,
            'error': 'Не настроен токен Яндекс.Диска',
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city,
            'photos': []
        }
        return render(request, 'main/album_detail.html', context)
    
    try:
        # Форматируем путь к папке
        folder_path = album.yandex_folder
        if folder_path.startswith('disk:'):
            folder_path = folder_path[5:]  # Убираем 'disk:'
        folder_path = folder_path.strip('/')  # Убираем слэши в начале и конце
        
        print(f"Debug: Folder path = {folder_path}")  # Выводим путь к папке
        
        # Получаем информацию о папке с превью
        response = requests.get(
            'https://cloud-api.yandex.net/v1/disk/resources',
            params={
                'path': folder_path,
                'limit': 100,
                'sort': 'name',
                'fields': '_embedded.items.name,_embedded.items.mime_type,_embedded.items.path,_embedded.items.file,_embedded.items.preview,_embedded.items.size',
                'preview_size': 'L'  # Изменил на L, так как XXL может не поддерживаться
            },
            headers={'Authorization': f'OAuth {yandex_token}'}
        )
        
        # Выводим отладочную информацию
        print(f"Debug: Request URL = {response.url}")
        print(f"Debug: Response Status = {response.status_code}")
        print(f"Debug: Response Content = {response.text}")  # Выводим весь ответ
        
        response.raise_for_status()
        data = response.json()
        
        photos = []
        if '_embedded' in data and 'items' in data['_embedded']:
            print(f"Debug: Found {len(data['_embedded']['items'])} items")
            
            for item in data['_embedded']['items']:
                print(f"\nDebug: Processing item: {item.get('name')}")
                print(f"Debug: Item type: {item.get('type')}")
                print(f"Debug: Mime type: {item.get('mime_type')}")
                print(f"Debug: Preview URL: {item.get('preview')}")
                print(f"Debug: File URL: {item.get('file')}")
                
                # Убираем проверку item.get('type'), так как оно всегда None
                if item.get('mime_type', '').startswith('image/'):
                    preview_url = item.get('preview', '')
                    file_url = item.get('file', '')
                    
                    # Добавляем фото только если есть хотя бы один URL
                    if preview_url or file_url:
                        photo_data = {
                            'name': item.get('name', ''),
                            'preview': preview_url,
                            'thumbnail': preview_url,  # Используем тот же URL для миниатюры
                            'url': file_url or preview_url  # Если нет file_url, используем preview_url
                        }
                        photos.append(photo_data)
                        print(f"Debug: Added photo: {photo_data}")
        
        print(f"\nDebug: Total photos added: {len(photos)}")
        
        # Сортируем фотографии по имени
        photos.sort(key=lambda x: x['name'])
        
        context = {
            'album': album,
            'photos': photos,
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city
        }
        return render(request, 'main/album_detail.html', context)
        
    except requests.RequestException as e:
        print(f"Error fetching photos: {e}")
        error_message = 'Не удалось загрузить фотографии'
        if hasattr(e.response, 'status_code'):
            if e.response.status_code == 404:
                error_message = f'Папка "{folder_path}" не найдена на Яндекс.Диске'
            elif e.response.status_code == 401:
                error_message = 'Ошибка авторизации в Яндекс.Диске'
            elif e.response.status_code == 400:
                error_message = f'Неверный путь к папке на Яндекс.Диске: "{folder_path}"'
        
        context = {
            'album': album,
            'error': error_message,
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city,
            'photos': []
        }
        return render(request, 'main/album_detail.html', context)
    except Exception as e:
        print(f"Unexpected error: {e}")
        context = {
            'album': album,
            'error': 'Произошла неожиданная ошибка',
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city,
            'photos': []
        }
        return render(request, 'main/album_detail.html', context)

def index(request):
    context = {
        'announcements': Announcement.objects.filter(is_active=True),
        'site_settings': SiteSettings.get_solo(),
        'latest_brands': Brand.objects.all().order_by('-id')[:4],
        'latest_albums': PhotoAlbum.objects.all().order_by('-date')[:10],
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': None
    }
    return render(request, 'main/index.html', context)
