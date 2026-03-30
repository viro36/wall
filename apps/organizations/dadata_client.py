from dadata import Dadata
from django.conf import settings


def get_organization_by_inn(inn: str):
    """
    Получает данные об организации по ИНН через API DaData.
    Возвращает словарь с нужными полями или None в случае ошибки.
    """
    token = settings.DADATA_API_KEY
    secret = settings.DADATA_SECRET_KEY

    # Если секретный ключ не нужен, можно передать только token
    with Dadata(token, secret) as dadata:
        try:
            # Метод find_by_id (для точного поиска по ИНН)
            result = dadata.find_by_id(name="party", query=inn, count=1)
            if result:
                return parse_dadata_response(result[0])
            else:
                return None
        except Exception as e:
            print(f"Ошибка при запросе к DaData: {e}")
            return None


def parse_dadata_response(data: dict):
    """
    Преобразует ответ DaData в удобный для нашей модели словарь.
    data — это словарь, который приходит в поле 'data' ответа API.
    """
    # Базовая структура
    org_data = data.get("data", {})
    address_data = org_data.get("address", {}).get("data", {})

    return {
        "inn": org_data.get("inn"),
        "kpp": org_data.get("kpp"),
        "ogrn": org_data.get("ogrn"),
        "full_name": org_data.get("name", {}).get("full_with_opf"),
        "short_name": org_data.get("name", {}).get("short_with_opf"),
        "address_raw": org_data.get("address", {}).get("unrestricted_value"),
        "postal_code": address_data.get("postal_code"),
        "region": address_data.get("region_with_type"),
        "city": address_data.get("city_with_type"),
        "street": address_data.get("street_with_type"),
        "house": address_data.get("house"),
        "status": org_data.get("state", {}).get("status"),
    }
