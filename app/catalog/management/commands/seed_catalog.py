import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from app.catalog.models import Category, Product


class Command(BaseCommand):
    help = _("Seed 3 categories and 10 demo products")

    def handle(self, *args, **options):
        # 1. Create categories
        root = Category.objects.get_or_create(name="Обувь", slug="obuv", parent=None)[0]
        men = Category.objects.get_or_create(
            name="Мужская", slug="muzhskaya", parent=root
        )[0]
        women = Category.objects.get_or_create(
            name="Женская", slug="zhenskaya", parent=root
        )[0]

        self.stdout.write(
            self.style.SUCCESS(f"Categories created: {root}, {men}, {women}")
        )

        # 2. Create 10 products
        for i in range(1, 11):
            cat = random.choice([men, women])
            product, created = Product.objects.get_or_create(
                slug=f"product-{i}",
                defaults={
                    "name": f"Product {i}",
                    "category": cat,
                    "photo_url": f"https://picsum.photos/seed/{i}/400/400",
                    "absolute_position": i,
                    "price": Decimal(random.randint(1000, 10000)) / 100,
                    "sellers_count": random.randint(1, 5),
                    "sales_30d": random.randint(0, 200),
                    "reviews_count": random.randint(0, 50),
                    "rating": round(random.uniform(1.0, 5.0), 1),
                    "weight_kg": round(random.uniform(0.5, 2.5), 2),
                },
            )
            status = "created" if created else "already exists"
            self.stdout.write(f"{product} -> {status}")

        self.stdout.write(self.style.SUCCESS("✅ Seeded catalog successfully"))
