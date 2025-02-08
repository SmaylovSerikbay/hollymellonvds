from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import requests
from django.core.cache import cache

def compress_image(image):
    im = Image.open(image)
    output = BytesIO()
    
    # Конвертируем в JPEG и оптимизируем
    if im.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', im.size, (255, 255, 255))
        background.paste(im, mask=im.split()[-1])
        im = background
    
    # Максимальный размер
    MAX_SIZE = (1200, 1200)
    im.thumbnail(MAX_SIZE, Image.LANCZOS)
    
    # Сохраняем с оптимизацией
    im.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    
    return InMemoryUploadedFile(output, 'ImageField',
                               f"{image.name.split('.')[0]}.jpg",
                               'image/jpeg',
                               sys.getsizeof(output), None)

def get_yandex_folders(token):
    """Получает список папок с Яндекс.Диска"""
    # Проверяем кэш
    cache_key = f'yandex_folders_{token[:10]}'
    cached_folders = cache.get(cache_key)
    if cached_folders:
        return cached_folders

    try:
        response = requests.get(
            'https://cloud-api.yandex.net/v1/disk/resources',
            headers={'Authorization': f'OAuth {token}'},
            params={
                'path': '/',
                'limit': 1000,  # Увеличиваем лимит
                'fields': '_embedded.items.name,_embedded.items.path,_embedded.items.type'  # Оптимизируем запрос
            }
        )
        response.raise_for_status()
        data = response.json()

        folders = []
        if '_embedded' in data and 'items' in data['_embedded']:
            # Получаем корневые папки
            root_folders = [
                {'path': item['path'], 'name': item['name']}
                for item in data['_embedded']['items']
                if item['type'] == 'dir'
            ]
            folders.extend(root_folders)

            # Получаем вложенные папки для каждой корневой папки
            for folder in root_folders:
                try:
                    sub_response = requests.get(
                        'https://cloud-api.yandex.net/v1/disk/resources',
                        headers={'Authorization': f'OAuth {token}'},
                        params={
                            'path': folder['path'],
                            'limit': 1000,
                            'fields': '_embedded.items.name,_embedded.items.path,_embedded.items.type'
                        }
                    )
                    sub_response.raise_for_status()
                    sub_data = sub_response.json()

                    if '_embedded' in sub_data and 'items' in sub_data['_embedded']:
                        sub_folders = [
                            {'path': item['path'], 'name': f"{folder['name']}/{item['name']}"}
                            for item in sub_data['_embedded']['items']
                            if item['type'] == 'dir'
                        ]
                        folders.extend(sub_folders)
                except Exception as e:
                    print(f"Ошибка при получении подпапок для {folder['path']}: {e}")
                    continue

        # Сортируем папки по имени
        folders.sort(key=lambda x: x['name'])

        # Кэшируем результат на 5 минут
        cache.set(cache_key, folders, 300)
        return folders

    except Exception as e:
        print(f"Ошибка при получении списка папок: {e}")
        return [] 