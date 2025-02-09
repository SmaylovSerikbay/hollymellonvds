from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Brand, City, BrandTicker, BrandsPageSettings, PhotoAlbum, SiteSettings, Announcement, HomeHero, SiteLogo, Photographer
import json
from django.views.decorators.cache import cache_page
import requests
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt

def get_yandex_token():
    """Получает токен Яндекс.Диска из настроек"""
    settings = SiteSettings.objects.first()
    return settings.yandex_token if settings else ''

# Create your views here.

def home(request):
    current_city_id = request.session.get('current_city_id')
    if current_city_id:
        latest_brands = Brand.objects.filter(location_id=current_city_id).order_by('-id')[:4]
        latest_albums = PhotoAlbum.objects.filter(brand__location_id=current_city_id).order_by('-date')[:10]
        announcements = Announcement.objects.filter(
            is_active=True,
            city_id=current_city_id
        ).order_by('order', '-created_at')
        current_city = City.objects.get(id=current_city_id).name
    else:
        latest_brands = Brand.objects.all().order_by('-id')[:4]
        latest_albums = PhotoAlbum.objects.all().order_by('-date')[:10]
        announcements = Announcement.objects.filter(is_active=True).order_by('order', '-created_at')
        current_city = None
    
    context = get_base_context(request)
    context.update({
        'hero_slides': HomeHero.objects.filter(is_active=True).order_by('order'),
        'announcements': announcements,
        'site_settings': SiteSettings.objects.first(),
        'latest_brands': latest_brands,
        'latest_albums': latest_albums,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city
    })
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
    
    context = get_base_context(request)
    context.update({
        'brands': brands,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city,
        'ticker_texts': ticker_texts,
        'page_settings': page_settings,
    })
    return render(request, 'main/brands.html', context)

def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    current_city_id = request.session.get('current_city_id')
    current_city = City.objects.get(id=current_city_id).name if current_city_id else None
    
    context = get_base_context(request)
    context.update({
        'brand': brand,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city,
        'top_gallery': brand.top_gallery.all(),
        'bottom_gallery': brand.bottom_gallery.all()
    })
    return render(request, 'main/brand_detail.html', context)

def photo_gallery(request):
    current_city_id = request.session.get('current_city_id')
    
    # Начинаем с базового QuerySet
    albums = PhotoAlbum.objects.filter(is_active=True)
    
    # Применяем фильтры из GET-параметров
    if 'date' in request.GET:
        date = request.GET.get('date')
        albums = albums.filter(date=date)
    
    if 'city' in request.GET:
        city_id = request.GET.get('city')
        albums = albums.filter(brand__location_id=city_id)
        current_city = City.objects.get(id=city_id).name
    elif current_city_id:
        albums = albums.filter(brand__location_id=current_city_id)
        current_city = City.objects.get(id=current_city_id).name
    else:
        current_city = None
    
    # Фильтрация по заведению
    selected_venue = None
    if 'venue' in request.GET:
        venue_id = request.GET.get('venue')
        albums = albums.filter(brand_id=venue_id)
        selected_venue = Brand.objects.get(id=venue_id)
    
    # Фильтрация по фотографу
    selected_photographer = None
    if 'photographer' in request.GET:
        photographer_id = request.GET.get('photographer')
        albums = albums.filter(photographer_id=photographer_id)
        selected_photographer = Photographer.objects.get(id=photographer_id)
    
    # Получаем список всех брендов и фотографов для фильтров
    if current_city_id:
        brands = Brand.objects.filter(location_id=current_city_id).order_by('name')
    else:
        brands = Brand.objects.all().order_by('name')
    
    photographers = Photographer.objects.filter(is_active=True).order_by('name')
    
    context = get_base_context(request)
    context.update({
        'albums': albums.order_by('-date'),
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city,
        'brands': brands,
        'photographers': photographers,
        'selected_venue': selected_venue,
        'selected_photographer': selected_photographer
    })
    return render(request, 'main/photo_gallery.html', context)

def album_detail(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk)
    yandex_token = get_yandex_token()
    
    # Получаем текущий город
    current_city_id = request.session.get('current_city_id')
    current_city = City.objects.get(id=current_city_id).name if current_city_id else None
    
    # Проверяем наличие токена
    if not yandex_token:
        context = get_base_context(request)
        context.update({
            'album': album,
            'error': 'Не настроен токен Яндекс.Диска',
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city,
            'photos': []
        })
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
                'preview_size': 'L'
            },
            headers={'Authorization': f'OAuth {yandex_token}'}
        )
        
        response.raise_for_status()
        data = response.json()
        
        photos = []
        if '_embedded' in data and 'items' in data['_embedded']:
            for item in data['_embedded']['items']:
                if item.get('mime_type', '').startswith('image/'):
                    preview_url = item.get('preview', '')
                    file_url = item.get('file', '')
                    
                    if preview_url or file_url:
                        photo_data = {
                            'name': item.get('name', ''),
                            'preview': preview_url,
                            'thumbnail': preview_url,
                            'url': file_url or preview_url
                        }
                        photos.append(photo_data)
        
        photos.sort(key=lambda x: x['name'])
        
        context = get_base_context(request)
        context.update({
            'album': album,
            'photos': photos,
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city
        })
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
        
        context = get_base_context(request)
        context.update({
            'album': album,
            'error': error_message,
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city,
            'photos': []
        })
        return render(request, 'main/album_detail.html', context)
    except Exception as e:
        print(f"Unexpected error: {e}")
        context = get_base_context(request)
        context.update({
            'album': album,
            'error': 'Произошла неожиданная ошибка',
            'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
            'current_city': current_city,
            'photos': []
        })
        return render(request, 'main/album_detail.html', context)

def index(request):
    context = get_base_context(request)
    context.update({
        'announcements': Announcement.objects.filter(is_active=True),
        'site_settings': SiteSettings.objects.first(),
        'latest_brands': Brand.objects.all().order_by('-id')[:4],
        'latest_albums': PhotoAlbum.objects.all().order_by('-date')[:10],
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': None
    })
    return render(request, 'main/index.html', context)

def get_base_context(request):
    print("\n=== Starting get_base_context ===")
    context = {}
    try:
        print("Trying to get active logo...")
        active_logo = SiteLogo.objects.get(is_active=True)
        print(f"Found active logo: ID={active_logo.id}")
        print(f"Light logo path: {active_logo.light_theme_logo.path}")
        print(f"Dark logo path: {active_logo.dark_theme_logo.path}")
        context['light_logo'] = active_logo.light_theme_logo.url
        context['dark_logo'] = active_logo.dark_theme_logo.url
        print(f"Added to context: light_logo={context['light_logo']}, dark_logo={context['dark_logo']}")
    except SiteLogo.DoesNotExist:
        print("No active logo found in database, using defaults")
        context['light_logo'] = static('images/default-logo-light.png')
        context['dark_logo'] = static('images/default-logo-dark.png')
    except Exception as e:
        print(f"Error in get_base_context: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        context['light_logo'] = static('images/default-logo-light.png')
        context['dark_logo'] = static('images/default-logo-dark.png')
    
    print(f"Final context: {context}")
    print("=== Finished get_base_context ===\n")
    return context

def photo_albums(request):
    # Получаем активные альбомы
    albums = PhotoAlbum.objects.filter(is_active=True)
    
    # Фильтрация по городу
    city_id = request.GET.get('city')
    if city_id:
        albums = albums.filter(brand__location_id=city_id)
        current_city = City.objects.get(id=city_id).name
        brands = Brand.objects.filter(location_id=city_id, is_active=True)
    else:
        current_city = None
        brands = Brand.objects.filter(is_active=True)

    # Фильтрация по заведению
    brand_id = request.GET.get('brand')
    if brand_id:
        albums = albums.filter(brand_id=brand_id)

    # Фильтрация по дате
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        albums = albums.filter(date__gte=date_from)
    if date_to:
        albums = albums.filter(date__lte=date_to)

    # Получаем базовый контекст
    context = get_base_context(request)
    context.update({
        'albums': albums,
        'brands': brands,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city,
        'selected_city': city_id,
        'selected_brand': brand_id,
        'date_from': date_from,
        'date_to': date_to,
    })
    return render(request, 'main/photo_albums.html', context)

def download_yandex_folder(request):
    """API endpoint для получения ссылки на скачивание папки с Яндекс.Диска"""
    path = request.GET.get('path')
    if not path:
        return JsonResponse({'error': 'Не указан путь к папке'}, status=400)

    yandex_token = get_yandex_token()
    if not yandex_token:
        return JsonResponse({'error': 'Не настроен токен Яндекс.Диска'}, status=401)

    try:
        # Получаем ссылку на скачивание папки
        response = requests.get(
            'https://cloud-api.yandex.net/v1/disk/resources/download',
            params={'path': path},
            headers={'Authorization': f'OAuth {yandex_token}'}
        )
        response.raise_for_status()
        data = response.json()
        
        return JsonResponse({'href': data['href']})
    except requests.RequestException as e:
        print(f"Error getting download link: {e}")
        return JsonResponse({'error': 'Ошибка при получении ссылки на скачивание'}, status=500)

@csrf_exempt
def proxy_yandex_photo(request):
    """Проксирует запросы к фотографиям на Яндекс.Диске"""
    # Добавляем CORS заголовки
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Max-Age': '86400',  # 24 часа
    }
    
    # Обработка OPTIONS запросов
    if request.method == 'OPTIONS':
        response = HttpResponse()
        for key, value in cors_headers.items():
            response[key] = value
        return response
    
    url = request.GET.get('url')
    if not url:
        return JsonResponse({'error': 'URL не указан'}, status=400)
    
    # Получаем токен Яндекс.Диска
    yandex_token = get_yandex_token()
    if not yandex_token:
        return JsonResponse({'error': 'Не настроен токен Яндекс.Диска'}, status=401)
    
    try:
        # Добавляем токен авторизации в заголовки запроса
        headers = {'Authorization': f'OAuth {yandex_token}'}
        
        # Добавляем обработку редиректов
        response = requests.get(url, stream=True, allow_redirects=True, headers=headers)
        response.raise_for_status()
        
        # Копируем заголовки ответа
        proxy_response = HttpResponse(
            response.raw,
            content_type=response.headers.get('content-type', 'application/octet-stream')
        )
        
        # Добавляем CORS заголовки к ответу
        for key, value in cors_headers.items():
            proxy_response[key] = value
        
        # Добавляем заголовки кэширования
        proxy_response['Cache-Control'] = 'public, max-age=31536000'  # 1 год
        
        return proxy_response
        
    except requests.RequestException as e:
        error_message = str(e)
        if hasattr(e.response, 'status_code'):
            status_code = e.response.status_code
        else:
            status_code = 500
        print(f"Proxy error: {error_message}")  # Добавляем логирование ошибки
        return JsonResponse({'error': error_message}, status=status_code)
    except Exception as e:
        print(f"Unexpected proxy error: {str(e)}")  # Добавляем логирование неожиданных ошибок
        return JsonResponse({'error': str(e)}, status=500)
