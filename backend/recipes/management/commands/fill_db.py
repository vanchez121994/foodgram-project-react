import csv
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Filling ingredients with prepared CSV-files."
    data_folder = "static/data"
    schema = (
        (Ingredient, "ingredients.csv"),
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            help='Путь до файла ингредиентов'
        )

    def handle(self, *args, **options):
        with open(
            os.path.join(
                options.get('path', ''),
                'ingredients.csv'
            ),
            encoding="UTF-8"
        ) as file:
            reader = csv.reader(file)
            result = [Ingredient(
                name=name, measurement_unit=unit
            ) for name, unit in reader]
        Ingredient.objects.bulk_create(result)
