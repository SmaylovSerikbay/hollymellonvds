from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import Brand, City, BrandTicker, BrandsPageSettings, PhotoAlbum, SiteSettings, Announcement, HomeHero, SiteLogo, Photographer, TeamPage
import json
from django.views.decorators.cache import cache_page
import requests
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
import time

def get_yandex_token():
    """Получает токен Яндекс.Диска из настроек"""
    settings = SiteSettings.objects.first()
    return settings.yandex_token if settings else ''

# Create your views here.

def get_default_city(request):
    """Получает город по умолчанию или устанавливает его, если не установлен"""
    current_city_id = request.session.get('current_city_id')
    
    if not current_city_id:
        try:
            # Пробуем установить город с id=1
            default_city = City.objects.get(id=1, is_active=True)
            current_city_id = default_city.id
            request.session['current_city_id'] = current_city_id
        except City.DoesNotExist:
            # Если город с id=1 не найден или неактивен, берем первый активный город
            first_city = City.objects.filter(is_active=True).first()
            if first_city:
                current_city_id = first_city.id
                request.session['current_city_id'] = current_city_id
    
    return current_city_id

def home(request):
    current_city_id = get_default_city(request)
    if current_city_id:
        latest_brands = Brand.objects.filter(location_id=current_city_id).order_by('-id')[:4]
        latest_albums = PhotoAlbum.objects.filter(brand__location_id=current_city_id).order_by('-date')[:6]
        announcements = Announcement.objects.filter(
            is_active=True,
            city_id=current_city_id
        ).order_by('order', '-created_at')
        current_city = City.objects.get(id=current_city_id).name
    else:
        latest_brands = Brand.objects.all().order_by('-id')[:4]
        latest_albums = PhotoAlbum.objects.all().order_by('-date')[:6]
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

@csrf_exempt
def set_city(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        city_id = data.get('city_id')
        if city_id:
            request.session['current_city_id'] = city_id
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})

def brands(request):
    current_city_id = get_default_city(request)
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
    current_city_id = get_default_city(request)
    current_city = City.objects.get(id=current_city_id).name if current_city_id else None
    
    context = get_base_context(request)
    context.update({
        'brand': brand,
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city,
        'top_gallery': brand.gallery.all(),
        'bottom_gallery': brand.gallery.all()
    })
    return render(request, 'main/brand_detail.html', context)

def photo_gallery(request):
    current_city_id = get_default_city(request)
    
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
    current_city_id = get_default_city(request)
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
                'preview_size': 'XL'
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
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Max-Age': '86400',
    }
    
    if request.method == 'OPTIONS':
        response = HttpResponse()
        for key, value in cors_headers.items():
            response[key] = value
        return response
    
    url = request.GET.get('url')
    if not url:
        return JsonResponse({'error': 'URL не указан'}, status=400)
    
    if '/proxy-photo/' in url:
        return JsonResponse({'error': 'Некорректный URL'}, status=400)
    
    yandex_token = get_yandex_token()
    if not yandex_token:
        return JsonResponse({'error': 'Не настроен токен Яндекс.Диска'}, status=401)
    
    session = requests.Session()
    session.headers.update({
        'Authorization': f'OAuth {yandex_token}',
        'Accept': 'image/*',
        'User-Agent': 'Mozilla/5.0'
    })
    
    max_retries = 3
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            # Получаем ссылку на скачивание
            response = session.get(url, allow_redirects=False, timeout=5)
            response.raise_for_status()
            
            # Если получили редирект, следуем по нему
            if response.status_code in (301, 302):
                download_url = response.headers.get('Location')
                if not download_url:
                    return JsonResponse({'error': 'Не удалось получить ссылку на скачивание'}, status=500)
                
                # Получаем оригинальное имя файла из URL
                filename = download_url.split('/')[-1].split('?')[0]
                
                # Делаем запрос к финальному URL без авторизации
                response = requests.get(download_url, stream=True, timeout=5)
                response.raise_for_status()
            
                # Создаем ответ
                proxy_response = HttpResponse(
                    response.content,
                    content_type=response.headers.get('content-type', 'image/jpeg')
                )
                
                # Добавляем заголовки для скачивания
                proxy_response['Content-Disposition'] = f'attachment; filename="{filename}"'
                proxy_response['Content-Length'] = response.headers.get('content-length', '')
                
                # Добавляем CORS заголовки
                for key, value in cors_headers.items():
                    proxy_response[key] = value
                
                proxy_response['Cache-Control'] = 'public, max-age=31536000'
                
                return proxy_response
            
            # Если нет редиректа, возвращаем контент напрямую
            proxy_response = HttpResponse(
                response.content,
                content_type=response.headers.get('content-type', 'image/jpeg')
            )
            
            for key, value in cors_headers.items():
                proxy_response[key] = value
            
            proxy_response['Cache-Control'] = 'public, max-age=31536000'
            
            return proxy_response
            
        except requests.RequestException as e:
            last_error = e
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(1)
            continue
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Если все попытки неудачны
    error_message = str(last_error)
    status_code = last_error.response.status_code if hasattr(last_error, 'response') else 503
    
    return JsonResponse({
        'error': error_message,
        'retry_after': '5'
    }, status=status_code, headers={'Retry-After': '5'})

def team_view(request):
    team_page = TeamPage.objects.first()
    if not team_page:
        team_page = TeamPage.objects.create(
            title='В центре Holy Melon — люди!',
            subtitle='Команда — наша душа, наш успех.',
            main_text='В каждом проекте, в каждой детали и в каждом достижении есть одна важная составляющая — люди. В Holy Melon Management мы уверены, что настоящая сила компании заключается в её команде. Мы гордимся тем, что наши сотрудники не просто профессионалы, а те, кто вдохновляет и вкладывает свою энергию в создание уникальных впечатлений. Мы понимаем, что успех — это результат не только труда, но и страсти, с которой мы работаем.\n\nРабота в Holy Melon — это путь, который мы проходим вместе, поддерживая и вдохновляя друг друга. Каждый день мы растём и развиваемся, двигаясь к общей цели.\n\nHoly Melon Management — это еще и эмоции, которые мы создаем для наших гостей, а также амбиции, которые мы реализуем вместе.',
            statistics=[
                'Средний стаж работы в компании — от 4-х лет',
                '11 проектов по всему Казахстану',
                'Более + 450 сотрудников',
                'Ежегодно обслуживаем свыше (кол-во) гостей',
                'В Академии гостеприимства прошли обучение более (кол-во) специалистов'
            ],
            recruitment_text='Ключ к нашему успеху — в единстве и взаимной поддержке. Каждый день мы вдохновляем друг друга на новые достижения, а вместе достигаем высоких результатов и стремимся к новым вершинам.\n\nХотите стать частью нашей команды?',
            email='holymelon.mgmt@gmail.com',
            about_title='Что такое Holy Melon Management?',
            about_text='Представьте себе место, где каждый день превращается в праздник. Мы — это мощная команда, объединенная общей страстью к кулинарии и гостеприимству, создающая уникальные впечатления для каждого посетителя.\n\nHoly Melon Management — это семья, в которой работают лучшие из лучших, чтобы дарить нашим гостям незабываемые впечатления.',
            who_we_are_title='Кто мы?',
            who_we_are_items=[
                'Сеть из 11 брендов в сфере HoReCa, которые знают и любят.',
                'Команда из более чем 450 профессионалов, каждый из которых — неотъемлемая часть нашей истории.',
                'Лидеры в области гостеприимства, стремящиеся к постоянному росту и развитию.'
            ],
            who_we_are_conclusion='Добро пожаловать в команду, где каждый день — это новый вызов и новая победа. Вместе мы пишем историю, которой можем гордиться.'
        )
    return render(request, 'main/team.html', {'team': team_page})
