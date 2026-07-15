import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from products.models import Category, Product, User, Order, Transaction

class Command(BaseCommand):
    help = 'Seed the database with 10k+ rows of realistic ecommerce data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Clearing existing data...'))
        
        # 1. Truncate tables to restart IDs from 1 (PostgreSQL restart identity)
        try:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE transactions, orders, users, products, categories RESTART IDENTITY CASCADE;")
            self.stdout.write(self.style.SUCCESS('Successfully truncated tables using raw SQL.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Raw SQL truncate failed ({e}). Falling back to Django ORM delete.'))
            Transaction.objects.all().delete()
            Order.objects.all().delete()
            User.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()

        self.stdout.write(self.style.WARNING('Generating mock data...'))
        
        # Define mock datasets
        categories_data = [
            {"name": "Electronics", "desc": "Gadgets, smartphones, laptops, and home accessories."},
            {"name": "Fashion", "desc": "Men, women, and kids apparel, shoes, and clothing accessories."},
            {"name": "Home Appliances", "desc": "Refrigerators, washing machines, heaters, and vacuum cleaners."},
            {"name": "Kitchenware", "desc": "Pots, pans, cutlery, blenders, and coffee makers."},
            {"name": "Furniture", "desc": "Sofas, beds, dining tables, office desks, and chairs."},
            {"name": "Health & Wellness", "desc": "Vitamins, monitors, yoga gear, and massage tools."},
            {"name": "Beauty & Care", "desc": "Skincare, makeup, hair tools, and perfumes."},
            {"name": "Office Supplies", "desc": "Notebooks, pens, organizers, and stationery items."},
            {"name": "Gaming Gear", "desc": "Consoles, controllers, gaming mice, keyboards, and VR headsets."},
            {"name": "Books & Media", "desc": "Novels, textbooks, ebooks, and audiobooks."},
            {"name": "Automotive Accessories", "desc": "Car chargers, phone mounts, floor mats, and cleaning kits."},
            {"name": "Sports & Outdoors", "desc": "Tents, sleeping bags, dumbbells, and hiking gear."}
        ]

        first_names = [
            "Liam", "Noah", "Oliver", "Elijah", "James", "William", "Benjamin", "Lucas", "Henry", "Alexander",
            "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Charlotte", "Mia", "Amelia", "Harper", "Evelyn",
            "Michael", "Daniel", "Matthew", "David", "Joseph", "Samuel", "Sarah", "Emily", "Jessica", "Ashley"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
        ]

        cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", 
            "Dallas", "San Jose", "Austin", "Jacksonville", "San Francisco", "Indianapolis", "Columbus", "Fort Worth", 
            "Charlotte", "Seattle", "Denver", "Boston", "Detroit", "Miami", "Las Vegas", "Portland"
        ]
        
        countries = ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Japan", "India"]

        payment_methods = ["Credit Card", "PayPal", "Bank Transfer", "Cryptocurrency", "Apple Pay"]

        # Ensure random is deterministic for debugging consistency
        random.seed(42)

        # ─── Create Categories ───
        categories = []
        from django.utils.text import slugify
        for cat in categories_data:
            categories.append(Category(
                name=cat["name"],
                slug=slugify(cat["name"]),
                description=cat["desc"]
            ))
        Category.objects.bulk_create(categories)
        categories = list(Category.objects.all())
        self.stdout.write(f'   [+] Created {len(categories)} categories.')

        # ─── Create Products ───
        # Target: 1,000 products
        products_to_create = []
        brand_prefixes = ["Apex", "Quantum", "Stellar", "Nova", "Zenith", "Volt", "Core", "Aero", "Ember", "Prime"]
        product_suffixes = ["Pro", "Max", "Ultra", "Lite", "Elite", "v2", "x100", "Plus", "Classic", "Premium"]

        for i in range(1000):
            cat = random.choice(categories)
            brand = random.choice(brand_prefixes)
            suffix = random.choice(product_suffixes)
            
            # Category-specific naming
            if cat.name == "Electronics":
                item_name = random.choice(["Smartphone", "Tablet", "Bluetooth Speaker", "Wireless Headphones", "Smartwatch", "Led Projector"])
            elif cat.name == "Fashion":
                item_name = random.choice(["Leather Jacket", "Denim Jeans", "Running Shoes", "Cotton T-Shirt", "Sneakers", "Woolen Sweater"])
            elif cat.name == "Home Appliances":
                item_name = random.choice(["Room Heater", "Air Purifier", "Vacuum Cleaner", "Dehumidifier", "Microwave", "Smart Bulb"])
            elif cat.name == "Kitchenware":
                item_name = random.choice(["Chef Knife Set", "Air Fryer", "Non-stick Pan", "Espresso Machine", "Electric Kettle", "Juicer Mixer"])
            elif cat.name == "Furniture":
                item_name = random.choice(["Ergonomic Office Chair", "Standing Desk", "Coffee Table", "Bookshelf", "Bedside Table", "3-Seater Sofa"])
            elif cat.name == "Health & Wellness":
                item_name = random.choice(["Massage Gun", "Blood Pressure Monitor", "Yoga Mat", "Humidifier", "Orthopedic Pillow", "Electric Toothbrush"])
            elif cat.name == "Beauty & Care":
                item_name = random.choice(["Face Serum", "Hair Dryer", "Matte Lipstick", "Perfume Spray", "Moisturizing Cream", "Shampoo"])
            elif cat.name == "Office Supplies":
                item_name = random.choice(["Dry Erase Whiteboard", "Gel Pen Pack", "Desk Organizer", "Leather Planner", "Stapler Set", "File Folders"])
            elif cat.name == "Gaming Gear":
                item_name = random.choice(["Gaming Mouse", "Mechanical Keyboard", "RGB Headset", "Controller Stand", "Gaming Chair", "Graphics Card"])
            elif cat.name == "Books & Media":
                item_name = random.choice(["Mystery Novel", "Sci-Fi Paperback", "Self-Help Audiobook", "Recipe Handbook", "History Biography"])
            elif cat.name == "Automotive Accessories":
                item_name = random.choice(["Car Phone Mount", "Dashboard Camera", "Leather Seat Covers", "Tire Inflator", "Car Vacuum", "OBD2 Scanner"])
            else: # Sports & Outdoors
                item_name = random.choice(["Camping Tent", "Sleeping Bag", "Adjustable Dumbbells", "Hydration Backpack", "Sports Water Bottle"])

            prod_name = f"{brand} {item_name} {suffix}"
            price = round(random.uniform(9.99, 1499.99), 2)
            stock = random.choice([0, 1, 2, 5, 10, 20, 50, 100, 250, 500])
            rating = round(random.uniform(3.0, 5.0), 1)

            products_to_create.append(Product(
                category=cat,
                name=prod_name,
                price=price,
                stock=stock,
                rating=rating
            ))

        Product.objects.bulk_create(products_to_create)
        products = list(Product.objects.all())
        self.stdout.write(f'   [+] Created {len(products)} products.')

        # ─── Create Users ───
        # Target: 2,000 users
        users_to_create = []
        emails_set = set() # ensure email uniqueness
        for i in range(2000):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            city = random.choice(cities)
            country = random.choice(countries)
            
            # Form email
            email_base = f"{fn.lower()}.{ln.lower()}"
            email = f"{email_base}@example.com"
            counter = 1
            while email in emails_set:
                email = f"{email_base}{counter}@example.com"
                counter += 1
            emails_set.add(email)

            phone = f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
            
            # random registration date in past year
            days_ago = random.randint(1, 365)
            created_at = timezone.now() - timedelta(days=days_ago)

            users_to_create.append(User(
                first_name=fn,
                last_name=ln,
                email=email,
                phone=phone,
                city=city,
                country=country,
                created_at=created_at
            ))

        User.objects.bulk_create(users_to_create)
        users = list(User.objects.all())
        self.stdout.write(f'   [+] Created {len(users)} users.')

        # ─── Create Orders and Transactions ───
        # Target: 4,000 orders & 4,000 transactions
        orders_to_create = []
        statuses = ["Delivered", "Delivered", "Delivered", "Shipped", "Pending", "Cancelled"]

        # To support bulk_create with auto IDs, we will write a transaction
        # and generate Orders in chunks, or just save them. Since order and transaction
        # are linked, we can create the orders, fetch them, and then create transactions.
        # Alternatively, we can save them in bulk, query all orders, and match them up.
        # Let's save Orders in bulk.
        
        self.stdout.write('   [~] Creating orders...')
        for i in range(4000):
            user = random.choice(users)
            prod = random.choice(products)
            qty = random.randint(1, 5)
            total = round(float(prod.price) * qty, 2)
            status = random.choice(statuses)
            
            # Make sure order created_at is after the user's registration date
            user_created_days = (timezone.now() - user.created_at).days
            order_days_ago = random.randint(0, max(0, user_created_days))
            created_at = timezone.now() - timedelta(days=order_days_ago)

            orders_to_create.append(Order(
                user=user,
                product=prod,
                quantity=qty,
                total_amount=total,
                status=status,
                created_at=created_at
            ))
        
        Order.objects.bulk_create(orders_to_create)
        orders = list(Order.objects.all())
        self.stdout.write(f'   [+] Created {len(orders)} orders.')

        # ─── Create Transactions ───
        self.stdout.write('   [~] Creating transactions...')
        transactions_to_create = []
        for order in orders:
            method = random.choice(payment_methods)
            amount = order.total_amount
            fee = round(float(amount) * 0.02, 2) # 2% fee
            
            if order.status == "Cancelled":
                t_status = random.choice(["Failed", "Refunded"])
            else:
                t_status = random.choice(["Success", "Success", "Success", "Failed"])
                
            # Transaction date matches order date + random minutes
            created_at = order.created_at + timedelta(minutes=random.randint(1, 15))

            transactions_to_create.append(Transaction(
                order=order,
                payment_method=method,
                status=t_status,
                amount=amount,
                transaction_fee=fee,
                created_at=created_at
            ))

        Transaction.objects.bulk_create(transactions_to_create)
        self.stdout.write(f'   [+] Created {Transaction.objects.count()} transactions.')
        
        # Output summary
        total_rows = (
            Category.objects.count() +
            Product.objects.count() +
            User.objects.count() +
            Order.objects.count() +
            Transaction.objects.count()
        )
        self.stdout.write(self.style.SUCCESS(f'Database seeded successfully! Total database rows: {total_rows}'))
