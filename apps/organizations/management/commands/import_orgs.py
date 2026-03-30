import csv
from django.core.management.base import BaseCommand
from apps.organizations.models import Organization, District, OrganizationType

class Command(BaseCommand):
    help = "Импорт организаций из CSV файла (только базовые поля)"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу')
        parser.add_argument('--clear', action='store_true', help='Очистить таблицу перед импортом')

    def get_district(self, district_name):
        """Получает район по названию"""
        if not district_name or district_name.strip() == '':
            return None
        try:
            return District.objects.get(short_name=district_name.strip())
        except District.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'Район "{district_name}" не найден, создаем...')
            )
            return District.objects.create(
                full_name=district_name.strip(),
                short_name=district_name.strip()
            )

    def get_org_type(self, type_name):
        """Получает или создает тип организации"""
        if not type_name or type_name.strip() == '':
            return None
        type_name = type_name.strip()
        org_type, created = OrganizationType.objects.get_or_create(name=type_name)
        if created:
            self.stdout.write(f'  Создан новый тип: "{type_name}"')
        return org_type

    def parse_coordinates(self, coord_str):
        """Парсит координаты из формата '51.6853497, 39.1751079'"""
        if not coord_str or coord_str.strip() == '':
            return None
        return coord_str.strip()

    def handle(self, *args, **options):
        file_path = options['csv_file']
        clear_existing = options['clear']
        
        if clear_existing:
            self.stdout.write('Очищаем таблицу организаций...')
            Organization.objects.all().delete()
        
        self.stdout.write(f'Импорт из файла: {file_path}')
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            # Определяем разделитель (табуляция или запятая)
            sample = f.read(1024)
            f.seek(0)
            
            if '\t' in sample:
                reader = csv.DictReader(f, delimiter='\t')
                self.stdout.write('Используется разделитель: TAB')
            else:
                reader = csv.DictReader(f)  # По умолчанию запятая
                self.stdout.write('Используется разделитель: ЗАПЯТАЯ')
            
            count = 0
            errors = 0
            
            for row in reader:
                try:
                    # Получаем связанные объекты
                    district = self.get_district(row.get('Район'))
                    org_type = self.get_org_type(row.get('Тип организации'))
                    
                    # Извлекаем адрес для разбора (пока сохраняем как есть)
                    address = row.get('Адрес одной строкой как в ЕГРЮЛ', '')
                    
                    # Создаем организацию
                    org, created = Organization.objects.update_or_create(
                        inn=row['ИНН'].strip(),
                        defaults={
                            'district': district,
                            'organization_type': org_type,
                            'short_name': row.get('Сокращённое название', '')[:500],
                            'full_name': row.get('Полное название', ''),
                            'kpp': row.get('КПП', '').strip() or None,
                            'ogrn': row.get('ОГРН', '').strip() or None,
                            'address_raw': address,
                            'coordinates': self.parse_coordinates(row.get('Координаты')),
                            'status': self.translate_status(row.get('Статус организации', '')),
                            # Адрес пока без разбора, можно добавить позже
                            'postal_code': None,
                            'region': None,
                            'city': None,
                            'street': None,
                            'house': None,
                        }
                    )
                    
                    if created:
                        count += 1
                        self.stdout.write(f'  + Добавлена: {org.short_name}')
                    else:
                        self.stdout.write(f'  ~ Обновлена: {org.short_name}')
                        
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'  Ошибка при импорте строки: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'\nИмпорт завершен. Добавлено: {count}, Ошибок: {errors}')
            )

    def translate_status(self, status_ru):
        """Переводит статус с русского на английский для БД"""
        status_map = {
            'действующая': 'ACTIVE',
            'ликвидируется': 'LIQUIDATING',
            'ликвидирована': 'LIQUIDATED',
        }
        return status_map.get(status_ru.lower().strip(), status_ru)
