from .models import City

def cities(request):
    current_city_id = request.session.get('current_city_id')
    try:
        current_city = City.objects.get(id=current_city_id).name if current_city_id else None
    except City.DoesNotExist:
        current_city = None
        
    return {
        'cities': City.objects.filter(is_active=True).order_by('order', 'name'),
        'current_city': current_city
    } 