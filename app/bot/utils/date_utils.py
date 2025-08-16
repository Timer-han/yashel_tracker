from datetime import date, datetime
from typing import Optional

def parse_date(date_string: str) -> Optional[date]:
    """Парсинг даты из строки"""
    try:
        return datetime.strptime(date_string, "%d.%m.%Y").date()
    except ValueError:
        return None

def format_date(date_obj: date) -> str:
    """Форматирование даты для отображения"""
    return date_obj.strftime("%d.%m.%Y")

def calculate_age(birth_date: date, reference_date: date = None) -> int:
    """Расчет возраста"""
    if reference_date is None:
        reference_date = date.today()
    
    age = reference_date.year - birth_date.year
    if reference_date.month < birth_date.month or \
       (reference_date.month == birth_date.month and reference_date.day < birth_date.day):
        age -= 1
    
    return age

def is_valid_date(date_obj: date, min_age: int = 8, max_age: int = 100) -> bool:
    """Проверка валидности даты рождения"""
    age = calculate_age(date_obj)
    return min_age <= age <= max_age
