"""
Django Management Command: seed_products
Generates 10,000 realistic products across 20 categories and 200 brands.
Uses bulk_create for performance.

Usage:
    python manage.py seed_products
    python manage.py seed_products --products 500  (custom count)
    python manage.py seed_products --clear         (clear existing data first)
"""

import random
import uuid
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Brand, Product


# ─── Static Data ─────────────────────────────────────────────────────────────

CATEGORIES = [
    ('Electronics', 'Latest gadgets and electronic devices'),
    ('Laptop Accessories', 'Everything you need to enhance your laptop experience'),
    ('Phone Accessories', 'Cases, chargers, and accessories for your smartphone'),
    ('Home Appliances', 'Smart appliances to make your home more comfortable'),
    ('Kitchen', 'Cookware, appliances, and kitchen essentials'),
    ('Furniture', 'Ergonomic and stylish furniture for every room'),
    ('Health', 'Products to support your health and wellness'),
    ('Fitness', 'Exercise equipment and fitness accessories'),
    ('Beauty', 'Skincare, makeup, and personal care products'),
    ('Office', 'Office supplies and productivity tools'),
    ('Gaming', 'Gaming peripherals, accessories, and merchandise'),
    ('Books', 'Educational books, novels, and reference materials'),
    ('Pet Supplies', 'Everything your pet needs to be happy and healthy'),
    ('Baby Care', 'Safe and gentle products for infants and toddlers'),
    ('Automotive', 'Car accessories and maintenance products'),
    ('Travel', 'Luggage, travel accessories, and essentials'),
    ('Garden', 'Gardening tools, seeds, and outdoor essentials'),
    ('Lighting', 'Smart lighting solutions for every space'),
    ('Medical', 'Medical devices and health monitoring equipment'),
    ('Fashion', 'Clothing, shoes, and fashion accessories'),
]

BRAND_NAMES = [
    'TechNova', 'AeroCool', 'SwiftByte', 'NexGen', 'PrimeEdge', 'ZenTech', 'BluePeak',
    'FrostLine', 'VortexPro', 'EchoWave', 'SolarBright', 'TurboMate', 'CrystalX',
    'IronShield', 'QuantumLeap', 'VividCore', 'StealthMode', 'Luminary', 'AlphaFlex',
    'DeltaForce', 'GigaBoost', 'HyperSync', 'InfraRed', 'JetStream', 'KineticPro',
    'LuminoTech', 'MegaWave', 'NitroBlast', 'OmniSense', 'PulseX', 'QuantumSafe',
    'RapidFire', 'SkyBridge', 'ThermaCore', 'UltraSpeed', 'VelocityMax', 'WarpDrive',
    'XcelTech', 'YieldPoint', 'ZephyrBrand', 'AbsolutePro', 'BoldStrike', 'ClearVision',
    'DynaFit', 'EcoSmart', 'FluxTech', 'GreenWave', 'HorizonPro', 'InnoVibe',
    'JadeCore', 'KryptonX', 'LaserEdge', 'MindfulTech', 'NovaBurst', 'OceanBreeze',
    'PeakPerform', 'QualityFirst', 'RiverFlow', 'SilverBolt', 'TitanForce', 'UniqueX',
    'VibrantPro', 'WildEdge', 'XtremeFit', 'YellowPeak', 'ZenCore', 'AquaShield',
    'BioNova', 'ClearPath', 'DigitalEdge', 'EnergyMax', 'FocusPro', 'GigaForce',
    'HealthFirst', 'IceBreaker', 'JoltPower', 'KineticWave', 'LightSpeed', 'MasterX',
    'NaturalFit', 'OptimumPro', 'PowerBlast', 'QuickStrike', 'RapidX', 'SafeGuard',
    'TechEdge', 'UltraFit', 'VigorPro', 'WellnessTech', 'XpertCore', 'YieldMax',
    'ZenFlex', 'ApexForce', 'BrightSide', 'CoordPro', 'DreamTech', 'EliteFit',
    'FlexWave', 'GlowUp', 'HighPoint', 'IdealTech', 'JustRight', 'KeenEdge',
    'LucidCore', 'MaxFlow', 'NetPro', 'OpenPath', 'PrimeFit', 'QuantumFlex',
    'ReliableX', 'SmartWave', 'TrustedPro', 'UrbanEdge', 'VitalCore', 'WiseChoice',
    'XcelFit', 'YouthPeak', 'ZeroLimit', 'ActivePro', 'BoostMax', 'ClearEdge',
    'DriveForce', 'EcoFlex', 'FastLane', 'GripTech', 'HomeBase', 'ImpactPro',
    'JumpStart', 'KomfortX', 'LiveWell', 'ModernFit', 'NaturePro', 'OnTarget',
    'PrecisionX', 'QualEdge', 'RiseTech', 'StrongCore', 'TopGear', 'UpTrend',
    'VividFlex', 'WarmCore', 'XtraFit', 'YearRound', 'ZestPro', 'AllRound',
    'BestChoice', 'CleanTech', 'DailyPro', 'EasyFit', 'FreshWave', 'GoodLife',
    'HappyCore', 'InfinityX', 'JoyTech', 'KindEdge', 'LifePlus', 'MoodBoost',
    'NiceTouch', 'OrderlyX', 'PureFit', 'QualityX', 'ReachPro', 'SmileTech',
    'TrueEdge', 'UnityPro', 'ValueMax', 'WholeFit', 'XcellenceX', 'YoungerX',
    'ZestfulPro', 'AimHigh', 'BraveCore', 'CommitX', 'DedicatedPro', 'EarnedEdge',
    'FocusedFit', 'GoalTech', 'HardenedX', 'IntensePro', 'JourneyMax', 'KnowledgeX',
    'LeapFrog', 'Milestone', 'NextLevel', 'OnwardPro', 'PinnaclePro', 'QuestEdge',
    'ReachMax', 'StriveCore', 'TargetFit', 'UpperEdge', 'VisionPro', 'WinningX',
    'XcelMax', 'YellowBolt', 'ZeroGravity', 'AcePro', 'BlazePath', 'ChargeMax',
    'DashEdge', 'ElectroFit', 'FlashCore', 'GlideWave', 'HighFly', 'ImpulsePro',
    'JoltEdge', 'KickStart', 'LiftOff', 'MachSpeed', 'NitroCore', 'OrbitX',
    'PlasmaFit', 'QuasarPro', 'RocketEdge', 'SonicWave', 'ThrustCore', 'UltraX',
    'VectorPro', 'WhirlCore', 'XplosiveFit', 'YieldPro', 'ZapTech', 'AtomicEdge',
    'BouncePro', 'CrashTest', 'DrillCore', 'ExplosiveX', 'FrequencyPro', 'GridEdge',
    'HeatWave', 'ImpactEdge', 'JumpMax', 'KnockoutPro', 'LaunchX',
]

COUNTRIES = ['USA', 'Germany', 'Japan', 'South Korea', 'China', 'Taiwan', 'UK', 'France', 'India', 'Canada']

# ─── Product Templates by Category ──────────────────────────────────────────

PRODUCT_TEMPLATES = {
    'Electronics': [
        ('4K Smart TV {size}"', 'Ultra-high-definition smart television with HDR support and built-in streaming apps.',
         ['TV', 'Smart TV', '4K', 'HDR', 'Television', 'Streaming'], {'Display': '{size}" 4K UHD', 'Smart Features': 'Built-in Apps', 'HDR': 'Yes'}),
        ('Wireless Bluetooth Speaker', 'Portable Bluetooth speaker with 360-degree sound and 24-hour battery life.',
         ['Speaker', 'Bluetooth', 'Wireless', 'Portable', 'Audio'], {'Battery': '24 hours', 'Connectivity': 'Bluetooth 5.0', 'Waterproof': 'IPX7'}),
        ('True Wireless Earbuds', 'Premium TWS earbuds with active noise cancellation and 30h total battery.',
         ['Earbuds', 'TWS', 'Noise Cancellation', 'Wireless', 'Audio'], {'ANC': 'Yes', 'Battery': '30 hours', 'Driver': '10mm'}),
        ('Smart Watch Pro Series', 'Advanced smartwatch with health monitoring, GPS, and 7-day battery life.',
         ['Smartwatch', 'GPS', 'Health', 'Watch', 'Fitness Tracker'], {'Display': 'AMOLED', 'Battery': '7 days', 'GPS': 'Built-in'}),
        ('Portable Power Bank {capacity}mAh', 'Fast-charging power bank with multiple ports and LED indicator.',
         ['Power Bank', 'Charger', 'Portable', 'Battery', 'Fast Charge'], {'Capacity': '{capacity}mAh', 'Ports': '3 USB', 'Charging': 'PD 65W'}),
        ('Noise Cancelling Headphones', 'Over-ear headphones with premium ANC and studio-quality sound.',
         ['Headphones', 'ANC', 'Noise Cancelling', 'Audio', 'Wireless'], {'ANC': 'Hybrid ANC', 'Battery': '40 hours', 'Foldable': 'Yes'}),
        ('USB-C Docking Station', 'Multi-port docking station with HDMI, USB-A, USB-C, and Ethernet.',
         ['Docking Station', 'USB-C', 'HDMI', 'Hub', 'Laptop'], {'Ports': '12-in-1', 'Video Output': '4K@60Hz', 'Power': '100W PD'}),
        ('Digital Camera Mirrorless', 'Professional mirrorless camera with 24MP sensor and 4K video recording.',
         ['Camera', 'Mirrorless', 'Photography', '4K', 'Digital'], {'Sensor': '24MP APS-C', 'Video': '4K 30fps', 'ISO': '100-51200'}),
    ],
    'Laptop Accessories': [
        ('Laptop Cooling Pad {fans}-Fan', 'High-performance cooling pad with silent fans for gaming laptops.',
         ['Cooling Pad', 'Laptop', 'Gaming', 'Fan', 'Overheating', 'Heat', 'Cooling'], {'Fans': '{fans} Silent Fans', 'Power': 'USB', 'Compatible': 'Up to 17"'}),
        ('Ergonomic Laptop Stand', 'Adjustable aluminum laptop stand for improved posture and cooling.',
         ['Laptop Stand', 'Ergonomic', 'Aluminum', 'Posture', 'Desk'], {'Material': 'Aluminum', 'Angles': '6 adjustable', 'Foldable': 'Yes'}),
        ('Laptop Bag Backpack {size}L', 'Water-resistant laptop backpack with multiple compartments.',
         ['Laptop Bag', 'Backpack', 'Laptop', 'Travel', 'Water Resistant'], {'Capacity': '{size}L', 'Material': 'Nylon', 'Fits': 'Up to 17" Laptop'}),
        ('Mechanical Keyboard Wireless', 'Compact TKL wireless mechanical keyboard with RGB backlight.',
         ['Keyboard', 'Mechanical', 'Wireless', 'RGB', 'Gaming', 'TKL'], {'Layout': 'TKL 87-Key', 'Switches': 'Blue/Red/Brown', 'Backlight': 'RGB'}),
        ('Wireless Ergonomic Mouse', 'Vertical ergonomic wireless mouse to reduce wrist strain.',
         ['Mouse', 'Ergonomic', 'Wireless', 'Wrist Pain', 'Vertical'], {'DPI': '800-3200', 'Battery': '18 months', 'Design': 'Vertical Ergonomic'}),
        ('USB-C Laptop Charger {watts}W', 'Fast GaN charger compatible with most laptops and MacBooks.',
         ['Charger', 'USB-C', 'GaN', 'Laptop', 'Fast Charge'], {'Power': '{watts}W', 'Technology': 'GaN', 'Ports': '2 USB-C + 1 USB-A'}),
        ('Laptop Privacy Screen Filter', 'Anti-spy privacy filter for 15.6" laptops.',
         ['Privacy Screen', 'Laptop', 'Anti Spy', 'Screen', 'Security'], {'Size': '15.6"', 'Type': 'Polarized', 'Viewing Angle': '60°'}),
        ('Thermal Paste Premium', 'High-conductivity thermal paste for CPU/GPU cooling improvement.',
         ['Thermal Paste', 'Cooling', 'CPU', 'GPU', 'Heat', 'Overheating'], {'Conductivity': '8.5 W/mK', 'Weight': '4g', 'Compatibility': 'CPU/GPU'}),
    ],
    'Phone Accessories': [
        ('Magnetic Phone Stand Wireless Charger', 'Magsafe-compatible wireless charger and phone stand combo.',
         ['Phone Stand', 'Wireless Charger', 'Magsafe', 'Phone', 'Charger'], {'Power': '15W', 'Compatible': 'MagSafe', 'Material': 'Aluminum'}),
        ('Phone Case Shockproof {model}', 'Military-grade drop protection phone case with kickstand.',
         ['Phone Case', 'Shockproof', 'Case', 'Protection', 'Kickstand'], {'Protection': 'Military Grade', 'Drop Test': '6ft', 'Kickstand': 'Yes'}),
        ('Screen Protector Tempered Glass', 'Edge-to-edge tempered glass with 9H hardness.',
         ['Screen Protector', 'Tempered Glass', 'Phone', 'Screen', 'Protection'], {'Hardness': '9H', 'Thickness': '0.33mm', 'Coverage': 'Full Screen'}),
        ('Fast Car Charger {watts}W', 'Dual-port fast car charger with USB-C and USB-A outputs.',
         ['Car Charger', 'Fast Charge', 'Phone', 'Charger', 'USB-C'], {'Power': '{watts}W', 'Ports': 'USB-C + USB-A', 'Compatible': 'All Phones'}),
        ('Selfie Ring Light Phone Holder', 'LED ring light with phone holder for content creators.',
         ['Ring Light', 'Selfie', 'LED', 'Phone Holder', 'Photography'], {'LED Count': '36 LEDs', 'Diameter': '10 inch', 'Colors': '3 Light Modes'}),
        ('Phone Battery Case {capacity}mAh', 'Rechargeable battery case to extend phone battery life.',
         ['Battery Case', 'Phone', 'Battery', 'Power Bank', 'Case'], {'Capacity': '{capacity}mAh', 'Charging': 'Pass-through', 'Wireless': 'No'}),
        ('Retractable Phone Cable 3-in-1', '3-in-1 retractable cable (USB-C, Lightning, Micro-USB).',
         ['Cable', 'Phone', 'Charger', 'USB-C', 'Lightning', 'Micro USB'], {'Connectors': 'USB-C/Lightning/Micro-USB', 'Length': '1.2m', 'Fast Charge': '3A'}),
    ],
    'Home Appliances': [
        ('Tower Air Cooler {liter}L', 'Energy-efficient tower air cooler with remote control and timer.',
         ['Air Cooler', 'Room Cooling', 'Fan', 'Hot Room', 'Summer', 'Heat', 'Temperature'], {'Capacity': '{liter}L', 'Coverage': '400 sq ft', 'Remote': 'Yes'}),
        ('Smart Ceiling Fan', 'Wi-Fi enabled ceiling fan with app control and 5 speed settings.',
         ['Ceiling Fan', 'Smart Fan', 'Fan', 'Room Cooling', 'Wi-Fi', 'Hot', 'Heat'], {'Speeds': '5', 'Control': 'App + Remote', 'Blade': '52 inch'}),
        ('Portable Air Conditioner {btu}BTU', 'Portable AC unit for rooms up to 400 sq ft.',
         ['Air Conditioner', 'AC', 'Cooling', 'Room Cooling', 'Portable', 'Hot Room', 'Heat'], {'BTU': '{btu}', 'Coverage': '400 sq ft', 'Timer': '24hr'}),
        ('Electric Mosquito Killer Trap', 'UV light mosquito killer trap — silent and chemical-free.',
         ['Mosquito Killer', 'Insect Trap', 'Mosquito', 'Pest', 'Bug', 'UV Light'], {'Area': '60 sq m', 'Power': 'USB/AC', 'Chemical': 'Free'}),
        ('Air Purifier HEPA {coverage}sqft', 'True HEPA air purifier removes 99.97% of airborne particles.',
         ['Air Purifier', 'HEPA', 'Dust', 'Allergy', 'Air Quality', 'Pollution'], {'Coverage': '{coverage} sq ft', 'Filter': 'True HEPA', 'CADR': '250 m³/h'}),
        ('Robot Vacuum Cleaner Auto', 'Smart robot vacuum with auto-mapping and mopping function.',
         ['Robot Vacuum', 'Vacuum', 'Cleaning', 'Robot', 'Auto Mop'], {'Suction': '2500 Pa', 'Battery': '150 min', 'Mapping': 'LiDAR'}),
        ('Table Fan USB Quiet', 'Ultra-quiet USB-powered desktop table fan with 3 speed settings.',
         ['Table Fan', 'Desk Fan', 'Fan', 'USB', 'Quiet', 'Hot', 'Cooling', 'Heat'], {'Speeds': '3', 'Power': 'USB 5V', 'Noise': '<30dB'}),
        ('Smart Dehumidifier {pint}Pint', 'Smart dehumidifier with Wi-Fi control for damp rooms.',
         ['Dehumidifier', 'Humidity', 'Damp Room', 'Mold', 'Smart Home'], {'Capacity': '{pint} pints/day', 'Control': 'Wi-Fi App', 'Tank': '2.5L'}),
    ],
    'Kitchen': [
        ('Digital Air Fryer {liter}L', 'Oil-free air fryer with 8 preset cooking modes.',
         ['Air Fryer', 'Cooking', 'Oil Free', 'Healthy', 'Kitchen', 'Fry'], {'Capacity': '{liter}L', 'Presets': '8', 'Temperature': '80-200°C'}),
        ('Instant Electric Kettle', '1.7L BPA-free electric kettle with temperature control.',
         ['Kettle', 'Electric Kettle', 'Tea', 'Coffee', 'Kitchen'], {'Capacity': '1.7L', 'Temperature': 'Variable', 'Material': 'BPA Free'}),
        ('Stand Mixer Professional', 'Professional 5.5L stand mixer with 10-speed settings.',
         ['Stand Mixer', 'Mixer', 'Baking', 'Kitchen', 'Dough'], {'Bowl': '5.5L', 'Speed': '10 settings', 'Power': '1000W'}),
        ('Knife Set Professional 7-Piece', 'German steel knife set with ergonomic handles.',
         ['Knife Set', 'Knives', 'Kitchen', 'Cooking', 'Chef'], {'Pieces': '7', 'Material': 'German Steel', 'Handle': 'Ergonomic'}),
        ('Blender High Speed Professional', 'Commercial-grade high-speed blender for smoothies and soups.',
         ['Blender', 'Smoothie', 'Kitchen', 'High Speed', 'Juicer'], {'Power': '1500W', 'Capacity': '2L', 'Presets': '6 programs'}),
        ('Electric Pressure Cooker {liter}L', 'Multi-function electric pressure cooker with 15 smart programs.',
         ['Pressure Cooker', 'Instant Pot', 'Cooking', 'Kitchen', 'Slow Cooker'], {'Capacity': '{liter}L', 'Programs': '15', 'Safety': 'Auto-lock'}),
        ('Non-stick Cookware Set 10-Piece', 'PFOA-free non-stick pots and pans with glass lids.',
         ['Cookware', 'Pan', 'Pot', 'Non-stick', 'Kitchen', 'Cooking'], {'Pieces': '10', 'Material': 'Aluminum', 'Compatible': 'All Stovetops'}),
    ],
    'Furniture': [
        ('Ergonomic Office Chair Lumbar Support', 'Breathable mesh office chair with adjustable lumbar and armrests.',
         ['Office Chair', 'Ergonomic', 'Lumbar Support', 'Back Pain', 'Posture', 'Neck Pain', 'Sitting'], {'Material': 'Mesh', 'Lumbar': 'Adjustable', 'Weight Limit': '150kg'}),
        ('Height Adjustable Standing Desk', 'Electric standing desk with memory settings and dual motors.',
         ['Standing Desk', 'Desk', 'Height Adjustable', 'Ergonomic', 'Office', 'Posture'], {'Width': '140cm', 'Height Range': '70-120cm', 'Motors': 'Dual'}),
        ('Memory Foam Lumbar Cushion', 'Orthopedic memory foam cushion for car and office chair.',
         ['Lumbar Cushion', 'Back Support', 'Back Pain', 'Memory Foam', 'Posture', 'Ergonomic'], {'Material': 'Memory Foam', 'Cover': 'Washable', 'Universal': 'Yes'}),
        ('Monitor Arm Dual Adjustable', 'VESA dual monitor arm with full articulation and cable management.',
         ['Monitor Arm', 'Monitor Stand', 'Desk', 'Office', 'Dual Monitor'], {'VESA': '75x75-100x100', 'Load': 'Up to 8kg each', 'Rotation': '360°'}),
        ('Footrest Under Desk Ergonomic', 'Adjustable ergonomic footrest for office chairs.',
         ['Footrest', 'Ergonomic', 'Foot Rest', 'Office', 'Comfort', 'Posture'], {'Angle': '0-30°', 'Surface': 'Non-slip', 'Material': 'PP+TPE'}),
        ('Bookshelf Storage 5-Tier', '5-tier wooden bookshelf with metal frame for living room.',
         ['Bookshelf', 'Storage', 'Shelf', 'Books', 'Living Room', 'Organization'], {'Tiers': '5', 'Material': 'Wood + Metal', 'Weight Limit': '30kg/shelf'}),
    ],
    'Health': [
        ('Digital Blood Pressure Monitor', 'Upper arm blood pressure monitor with irregular heartbeat detection.',
         ['Blood Pressure', 'Monitor', 'Health', 'Medical', 'Heart', 'Hypertension'], {'Type': 'Upper Arm', 'Memory': '60 readings', 'IHB': 'Yes'}),
        ('Pulse Oximeter Fingertip', 'Accurate fingertip pulse oximeter with OLED display.',
         ['Pulse Oximeter', 'SpO2', 'Oxygen', 'Health', 'Monitor'], {'Accuracy': '±2%', 'Display': 'OLED', 'Battery': 'AAA x2'}),
        ('Electric Heating Pad Large', 'Fast-heating electric heating pad for back and neck pain relief.',
         ['Heating Pad', 'Back Pain', 'Pain Relief', 'Electric', 'Heat Therapy', 'Muscle Pain'], {'Size': '30x60cm', 'Settings': '6 heat levels', 'Auto-off': '90 min'}),
        ('Orthopedic Cervical Pillow', 'Memory foam cervical pillow for neck pain and sleep quality.',
         ['Neck Pillow', 'Cervical Pillow', 'Neck Pain', 'Sleep', 'Memory Foam', 'Orthopedic'], {'Material': 'Memory Foam', 'Height': 'Adjustable', 'Cover': 'Removable'}),
        ('Foot Massager Electric Shiatsu', 'Deep kneading shiatsu foot massager with heat function.',
         ['Foot Massager', 'Massager', 'Foot Pain', 'Shiatsu', 'Relaxation'], {'Nodes': '18 massage nodes', 'Heat': 'Yes', 'Intensity': '3 levels'}),
        ('Smart Scale Body Composition', 'Wi-Fi smart scale measuring 13 body metrics.',
         ['Scale', 'Body Scale', 'Weight', 'BMI', 'Smart', 'Health Monitor'], {'Metrics': '13', 'Sync': 'Wi-Fi + Bluetooth', 'Capacity': '180kg'}),
        ('Muscle Pain Relief Massager Gun', 'Percussive therapy massage gun with 30 speed settings.',
         ['Massage Gun', 'Muscle Pain', 'Recovery', 'Percussive', 'Physiotherapy'], {'Speed': '30 levels', 'Battery': '6 hours', 'Attachments': '6 heads'}),
    ],
    'Fitness': [
        ('Adjustable Dumbbell Set {weight}kg', 'Quick-adjust dumbbell set replacing 15 pairs of weights.',
         ['Dumbbell', 'Weights', 'Fitness', 'Strength Training', 'Gym', 'Weight Training'], {'Weight Range': '2-{weight}kg', 'Adjustment': 'Quick-select', 'Material': 'Cast Iron'}),
        ('Yoga Mat Non-slip {thickness}mm', 'Extra-thick non-slip yoga mat with alignment lines.',
         ['Yoga Mat', 'Yoga', 'Exercise', 'Fitness', 'Non-slip', 'Pilates'], {'Thickness': '{thickness}mm', 'Material': 'TPE', 'Dimensions': '183x61cm'}),
        ('Resistance Bands Set 5-Pack', 'Latex resistance bands set with varying resistance levels.',
         ['Resistance Bands', 'Exercise', 'Fitness', 'Bands', 'Strength', 'Stretching'], {'Pieces': '5 levels', 'Material': 'Natural Latex', 'Max Resistance': '150 lbs'}),
        ('Fitness Tracker Smart Band', 'Smart fitness band with heart rate, sleep, and 50+ sport modes.',
         ['Fitness Tracker', 'Smart Band', 'Heart Rate', 'Steps', 'Sleep', 'Fitness'], {'Battery': '14 days', 'Water Resist': '5ATM', 'Sports': '50+ modes'}),
        ('Jump Rope Speed Bearing', 'Professional speed jump rope with ball bearings for fast rotation.',
         ['Jump Rope', 'Skipping', 'Cardio', 'Fitness', 'Boxing', 'Speed'], {'Material': 'Steel + PVC', 'Bearing': 'Ball Bearing', 'Length': 'Adjustable'}),
        ('Pull Up Bar Doorway', 'No-screw doorway pull-up bar supporting up to 150kg.',
         ['Pull Up Bar', 'Chin Up', 'Door Bar', 'Fitness', 'Strength', 'Upper Body'], {'Weight Limit': '150kg', 'Installation': 'No screws', 'Grip': 'Multi-grip'}),
        ('Treadmill Foldable Electric', 'Compact foldable electric treadmill for home workouts.',
         ['Treadmill', 'Running', 'Cardio', 'Fitness', 'Walking', 'Home Gym'], {'Speed': '1-12 km/h', 'Motor': '1.5HP', 'Foldable': 'Yes'}),
    ],
    'Beauty': [
        ('Facial Cleansing Brush Sonic', 'Sonic facial cleansing brush with 5 speed modes for deep pore cleansing.',
         ['Facial Brush', 'Cleansing', 'Skincare', 'Pore', 'Beauty', 'Face Wash'], {'Speeds': '5', 'Waterproof': 'IPX7', 'Battery': '30 days'}),
        ('Hair Dryer Professional {watt}W', 'Professional ionic hair dryer with diffuser and concentrator.',
         ['Hair Dryer', 'Hair', 'Ionic', 'Blow Dry', 'Beauty', 'Salon'], {'Power': '{watt}W', 'Technology': 'Ionic', 'Attachments': '3'}),
        ('Electric Face Massager Roller', 'T-bar face roller massager for lymphatic drainage and glow.',
         ['Face Massager', 'Roller', 'Skincare', 'Glow', 'Anti-aging', 'Beauty'], {'Material': 'Zinc Alloy', 'Vibration': 'Yes', 'Temperature': 'Cooling'}),
        ('Nail Gel Polish UV LED Kit', 'Complete gel nail polish kit with UV LED lamp.',
         ['Nail Polish', 'Gel Nail', 'UV LED', 'Manicure', 'Beauty', 'Nails'], {'Lamp': '48W LED', 'Colors': '12 included', 'Curing': '30-60 sec'}),
        ('Eyebrow Shaping Kit', 'Professional eyebrow stencils and shaping kit.',
         ['Eyebrow Kit', 'Eyebrow', 'Beauty', 'Makeup', 'Brows'], {'Stencils': '12 shapes', 'Includes': 'Brush + Razor', 'Reusable': 'Yes'}),
        ('Moisturizer SPF50 Face Cream', 'Lightweight daily moisturizer with SPF50 sun protection.',
         ['Moisturizer', 'Sunscreen', 'SPF50', 'Face Cream', 'Skincare', 'UV'], {'SPF': '50', 'Volume': '50ml', 'Type': 'Lightweight'}),
    ],
    'Office': [
        ('A4 Laser Printer Wireless', 'Fast wireless laser printer with duplex printing.',
         ['Printer', 'Laser Printer', 'Office', 'Wireless', 'A4'], {'Speed': '30 ppm', 'Resolution': '600dpi', 'Duplex': 'Automatic'}),
        ('Desk Organizer Bamboo {compartments}-Slot', 'Eco-friendly bamboo desk organizer for office supplies.',
         ['Desk Organizer', 'Office', 'Storage', 'Organization', 'Bamboo'], {'Compartments': '{compartments}', 'Material': 'Bamboo', 'Include': 'Drawer'}),
        ('LED Desk Lamp USB Charging', 'Dimmable LED desk lamp with wireless charging pad.',
         ['Desk Lamp', 'LED', 'Office', 'Lighting', 'USB Charging'], {'Brightness': '10 levels', 'Color Temp': '5 modes', 'USB': 'Yes'}),
        ('Pen Holder Set Office', 'Metal mesh pen holder with sticky note holder combo.',
         ['Pen Holder', 'Pen', 'Office', 'Stationery', 'Desk'], {'Material': 'Metal Mesh', 'Compartments': '3', 'Finish': 'Chrome'}),
        ('Whiteboard Magnetic 60x90cm', 'Magnetic dry-erase whiteboard with marker tray.',
         ['Whiteboard', 'Board', 'Office', 'Presentation', 'Marker'], {'Size': '60x90cm', 'Surface': 'Magnetic', 'Includes': 'Markers + Eraser'}),
        ('File Cabinet 4-Drawer Steel', 'Lockable 4-drawer steel filing cabinet with smooth rails.',
         ['File Cabinet', 'Storage', 'Office', 'Filing', 'Drawer'], {'Drawers': '4', 'Material': 'Steel', 'Lock': 'Yes'}),
    ],
    'Gaming': [
        ('Gaming Mouse RGB {dpi}DPI', 'High-precision gaming mouse with programmable RGB and {dpi}DPI sensor.',
         ['Gaming Mouse', 'Mouse', 'RGB', 'Gaming', 'FPS', 'Precision'], {'DPI': '{dpi}', 'Buttons': '7 programmable', 'RGB': 'Yes'}),
        ('Gaming Headset 7.1 Surround', 'Surround sound gaming headset with noise-cancelling microphone.',
         ['Gaming Headset', 'Headset', 'Gaming', 'Surround Sound', '7.1', 'Microphone'], {'Surround': '7.1 Virtual', 'Mic': 'Noise Cancelling', 'Platform': 'PC/PS/Xbox'}),
        ('Gaming Chair Racing Style', 'Ergonomic gaming chair with lumbar pillow and recline.',
         ['Gaming Chair', 'Chair', 'Gaming', 'Ergonomic', 'Racing', 'Lumbar'], {'Recline': '90-180°', 'Material': 'PU Leather', 'Height': 'Adjustable'}),
        ('Gaming Controller Wireless', 'Wireless gaming controller with haptic feedback and 40h battery.',
         ['Gaming Controller', 'Controller', 'Gamepad', 'Gaming', 'Console'], {'Battery': '40 hours', 'Haptic': 'Yes', 'Compatible': 'PC/PS/Xbox'}),
        ('Gaming Monitor {size}" {hz}Hz', 'Ultra-fast gaming monitor with {hz}Hz and 1ms response time.',
         ['Gaming Monitor', 'Monitor', 'Gaming', '{hz}Hz', 'Fast Refresh', 'Low Latency'], {'Size': '{size}"', 'Refresh': '{hz}Hz', 'Response': '1ms'}),
        ('Gaming Desk XXL Mouse Pad', 'Full-desk XXL gaming mouse pad with RGB edges.',
         ['Mouse Pad', 'Gaming Desk Pad', 'Gaming', 'RGB', 'Desk Mat', 'Large'], {'Size': '900x400mm', 'Thickness': '4mm', 'RGB': 'Edge Lighting'}),
        ('Gaming Keyboard Mechanical RGB', 'Full-size mechanical gaming keyboard with per-key RGB.',
         ['Gaming Keyboard', 'Keyboard', 'Mechanical', 'RGB', 'Gaming'], {'Layout': 'Full Size', 'Switches': 'Red/Blue/Brown', 'RGB': 'Per-key'}),
    ],
    'Books': [
        ('Python Programming {level} Guide', 'Complete Python programming guide for {level} developers.',
         ['Python', 'Programming', 'Book', 'Coding', 'Learning', 'Software'], {'Pages': '450+', 'Level': '{level}', 'Format': 'Paperback + eBook'}),
        ('Machine Learning Handbook', 'Practical machine learning with Python and scikit-learn.',
         ['Machine Learning', 'AI', 'Python', 'Data Science', 'Book', 'Learning'], {'Pages': '520', 'Level': 'Intermediate', 'Code': 'GitHub included'}),
        ('Business Strategy Masterclass', 'Award-winning business strategy book used in top MBA programs.',
         ['Business', 'Strategy', 'Book', 'Management', 'MBA', 'Leadership'], {'Pages': '380', 'Edition': '3rd', 'Format': 'Hardcover'}),
        ('Mindfulness for Beginners', 'Guided mindfulness and meditation practices for daily life.',
         ['Mindfulness', 'Meditation', 'Self Help', 'Wellness', 'Book', 'Stress'], {'Pages': '220', 'Level': 'Beginner', 'Exercises': '30 guided'}),
        ('Cooking Book World Cuisines', 'Global recipes from 50 countries with step-by-step instructions.',
         ['Cookbook', 'Recipes', 'Cooking', 'Food', 'Kitchen', 'Book'], {'Recipes': '300+', 'Cuisines': '50 countries', 'Photos': 'Full color'}),
        ('Personal Finance Investment Guide', 'Comprehensive guide to saving, investing, and financial freedom.',
         ['Finance', 'Investment', 'Money', 'Savings', 'Book', 'Wealth'], {'Pages': '340', 'Topics': 'Stocks, Bonds, ETFs', 'Workbook': 'Yes'}),
    ],
    'Pet Supplies': [
        ('Dog Automatic Feeder {liter}L', 'Programmable automatic pet feeder with camera and app control.',
         ['Dog Feeder', 'Pet Feeder', 'Automatic', 'Dog', 'Pet', 'Cat'], {'Capacity': '{liter}L', 'Camera': 'HD', 'App': 'iOS + Android'}),
        ('Cat Tree Tower Luxury', 'Multi-level cat tree with scratching posts and cozy hammock.',
         ['Cat Tree', 'Cat Tower', 'Cat', 'Scratching Post', 'Pet'], {'Height': '150cm', 'Levels': '5', 'Material': 'Sisal + Plush'}),
        ('Pet Carrier Airline Approved', 'Airline-approved soft pet carrier for cats and small dogs.',
         ['Pet Carrier', 'Cat Carrier', 'Dog Carrier', 'Travel', 'Pet', 'Airline'], {'Capacity': 'Up to 7kg', 'Airline': 'Approved', 'Ventilation': '4 sides'}),
        ('Dog Grooming Kit Electric', 'Quiet electric dog grooming kit with 5 attachments.',
         ['Dog Grooming', 'Pet Grooming', 'Dog', 'Clipper', 'Grooming'], {'Noise': 'Low noise', 'Attachments': '5', 'Battery': 'Rechargeable'}),
        ('Interactive Cat Toy Laser', 'Automatic rotating laser toy to keep cats entertained.',
         ['Cat Toy', 'Laser Toy', 'Cat', 'Interactive', 'Pet Toy'], {'Pattern': 'Random', 'Timer': 'Auto off', 'Safe': 'Class IIIA laser'}),
        ('Pet Odor Eliminator Spray', 'Enzyme-based pet odor and stain remover for all surfaces.',
         ['Pet Odor', 'Stain Remover', 'Pet', 'Cleaner', 'Odor'], {'Volume': '500ml', 'Formula': 'Enzyme-based', 'Safe': 'Pet & Family safe'}),
    ],
    'Baby Care': [
        ('Baby Monitor WiFi Camera', 'HD baby monitor with night vision and two-way audio.',
         ['Baby Monitor', 'Baby Camera', 'Baby', 'Monitor', 'Night Vision'], {'Resolution': '1080p', 'Night Vision': 'Infrared', 'Two-way': 'Yes'}),
        ('Bottle Sterilizer UV Electric', 'UV electric sterilizer for baby bottles and accessories.',
         ['Bottle Sterilizer', 'Baby', 'Sterilizer', 'UV', 'Baby Bottle'], {'Capacity': '6 bottles', 'UV': 'Yes', 'Cycle': '5 min'}),
        ('Baby Stroller Lightweight Foldable', 'Compact lightweight stroller with one-hand fold.',
         ['Baby Stroller', 'Stroller', 'Pram', 'Baby', 'Travel', 'Foldable'], {'Weight': '5.5kg', 'Fold': 'One-hand', 'Canopy': 'UPF50'}),
        ('Baby Carrier Ergonomic', 'Ergonomic hip-seat baby carrier for newborns to 20kg.',
         ['Baby Carrier', 'Carrier', 'Baby', 'Ergonomic', 'Newborn'], {'Weight Range': '3.5-20kg', 'Positions': '4', 'Material': 'Breathable Mesh'}),
        ('Electric Breast Pump Wearable', 'Hands-free wearable electric breast pump.',
         ['Breast Pump', 'Pump', 'Baby', 'Nursing', 'Wearable', 'Electric'], {'Mode': 'Expression + Massage', 'Suction': '5 levels', 'Hands-free': 'Yes'}),
        ('Diaper Bag Backpack', 'Large-capacity waterproof diaper bag with insulated pockets.',
         ['Diaper Bag', 'Baby Bag', 'Backpack', 'Baby', 'Nappy'], {'Capacity': '30L', 'Pockets': '15+', 'Material': 'Waterproof Nylon'}),
    ],
    'Automotive': [
        ('Dash Cam 4K Front Rear', 'Dual 4K dash cam with night vision and parking mode.',
         ['Dash Cam', 'Car Camera', 'Dashcam', 'Car', 'Driving', 'Safety'], {'Resolution': '4K Front + 1080p Rear', 'Night Vision': 'Sony Sensor', 'Parking': 'Mode included'}),
        ('Car Vacuum Cleaner Portable', 'Handheld car vacuum with powerful suction and HEPA filter.',
         ['Car Vacuum', 'Vacuum', 'Car Cleaner', 'Portable', 'Car'], {'Suction': '6000Pa', 'Filter': 'HEPA', 'Power': 'DC12V'}),
        ('Tyre Inflator Portable Electric', 'Portable electric tire inflator with digital pressure gauge.',
         ['Tyre Inflator', 'Tire Pump', 'Car', 'Pump', 'Inflation', 'Tyre'], {'Pressure': 'Up to 150 PSI', 'Auto-stop': 'Yes', 'Battery': '6000mAh'}),
        ('Car Phone Mount Magnetic', 'Strong magnetic car phone mount for dashboard and vent.',
         ['Car Mount', 'Phone Mount', 'Car', 'Magnetic', 'Phone Holder', 'Car Holder'], {'Mount': 'Dashboard + Vent', 'Rotation': '360°', 'Compatible': 'All Phones'}),
        ('Car Jump Starter Pack {amp}A', 'Portable lithium jump starter for cars up to {amp}A.',
         ['Jump Starter', 'Car Battery', 'Car', 'Battery Booster', 'Emergency'], {'Peak Current': '{amp}A', 'Capacity': '12000mAh', 'USB Charging': 'Yes'}),
    ],
    'Travel': [
        ('Luggage Hardshell {size}" Spinner', 'Lightweight hardshell spinner luggage with TSA lock.',
         ['Luggage', 'Suitcase', 'Travel', 'Spinner', 'TSA Lock', 'Hardshell'], {'Size': '{size}"', 'TSA Lock': 'Built-in', 'Wheels': '360° spinner'}),
        ('Packing Cubes Set 6-Piece', 'Lightweight packing cubes in 3 sizes for organized travel.',
         ['Packing Cubes', 'Travel Organizer', 'Luggage Organizer', 'Travel', 'Bag'], {'Pieces': '6', 'Sizes': 'S/M/L', 'Material': 'Ripstop Nylon'}),
        ('Travel Neck Pillow Memory Foam', 'Ergonomic memory foam travel neck pillow with carry bag.',
         ['Travel Pillow', 'Neck Pillow', 'Travel', 'Flight', 'Neck Pain', 'Sleep'], {'Material': 'Memory Foam', 'Cover': 'Washable', 'Packable': 'Yes'}),
        ('Universal Travel Adapter', 'All-in-one travel adapter for 200+ countries with USB ports.',
         ['Travel Adapter', 'Power Adapter', 'Travel', 'Plug', 'Universal', 'USB'], {'Countries': '200+', 'USB Ports': '4', 'Type': 'Universal'}),
        ('Anti-theft Backpack Travel', 'Hidden-zip anti-theft backpack with USB charging port.',
         ['Anti-theft Backpack', 'Travel Backpack', 'Bag', 'Security', 'Travel'], {'Capacity': '30L', 'Anti-theft': 'Hidden zip', 'USB': 'External port'}),
    ],
    'Garden': [
        ('Garden Hose Expandable {feet}ft', 'Expandable lightweight garden hose with 9-pattern spray nozzle.',
         ['Garden Hose', 'Hose', 'Garden', 'Watering', 'Spray'], {'Length': '{feet}ft', 'Expandable': 'Yes', 'Nozzle': '9 patterns'}),
        ('Electric Lawn Mower Cordless', 'Battery-powered cordless lawn mower with mulching function.',
         ['Lawn Mower', 'Mower', 'Garden', 'Grass', 'Cordless', 'Electric'], {'Battery': '40V Li-ion', 'Width': '38cm', 'Mulching': 'Yes'}),
        ('Plant Pot Self Watering {size}cm', 'Self-watering planter with water indicator and drainage.',
         ['Plant Pot', 'Planter', 'Garden', 'Self Watering', 'Indoor Plant'], {'Size': '{size}cm', 'Watering': 'Self-watering', 'Indicator': 'Water level'}),
        ('Pruning Shears Professional', 'Titanium-coated pruning shears with ergonomic handle.',
         ['Pruning Shears', 'Garden Scissors', 'Pruner', 'Garden', 'Trimming'], {'Blade': 'Titanium coated', 'Opening': 'Spring-loaded', 'Handle': 'Ergonomic'}),
        ('Smart Irrigation Controller', 'Wi-Fi smart irrigation controller with weather-based scheduling.',
         ['Irrigation Controller', 'Smart Water', 'Garden', 'Irrigation', 'Wi-Fi', 'Smart'], {'Zones': '12', 'Control': 'App + Voice', 'Weather': 'Adaptive'}),
    ],
    'Lighting': [
        ('Smart LED Bulb {watt}W RGBW', 'Wi-Fi smart LED bulb with 16M colors and voice control.',
         ['Smart Bulb', 'LED', 'Smart Lighting', 'RGB', 'Wi-Fi', 'Voice Control'], {'Power': '{watt}W', 'Colors': '16 Million', 'Compatible': 'Alexa + Google'}),
        ('Solar Garden Light Set 12-Pack', 'Waterproof solar-powered outdoor garden path lights.',
         ['Solar Light', 'Garden Light', 'Outdoor Light', 'Solar', 'Garden', 'Path Light'], {'Quantity': '12 pack', 'IP Rating': 'IP67', 'Solar': 'Yes'}),
        ('LED Strip Light {meter}m RGB', 'Flexible RGB LED strip with app control and music sync.',
         ['LED Strip', 'Strip Light', 'RGB', 'Ambient Light', 'Room Lighting', 'Gaming'], {'Length': '{meter}m', 'Colors': 'RGB', 'Sync': 'Music sync'}),
        ('Bedside Lamp Touch Dimmable', 'Touch-sensitive bedside lamp with 3 color temperatures.',
         ['Bedside Lamp', 'Lamp', 'Touch Lamp', 'Dimmable', 'Night Light'], {'Touch': 'Yes', 'Color Temp': '2700-6500K', 'USB': 'Charging port'}),
        ('Flood Light Outdoor Solar {watt}W', 'Motion-sensor solar flood light for outdoor security.',
         ['Flood Light', 'Security Light', 'Outdoor', 'Motion Sensor', 'Solar', 'Security'], {'Power': '{watt}W', 'Motion Sensor': 'Yes', 'Battery': 'Built-in'}),
    ],
    'Medical': [
        ('Digital Thermometer Infrared', 'Non-contact infrared thermometer with 1-second reading.',
         ['Thermometer', 'Infrared', 'Temperature', 'Medical', 'Fever', 'Baby'], {'Type': 'Non-contact', 'Time': '1 second', 'Memory': '32 readings'}),
        ('TENS Machine Pain Relief', 'Dual-channel TENS EMS machine for muscle and nerve pain.',
         ['TENS Machine', 'Pain Relief', 'Muscle Pain', 'EMS', 'Physical Therapy'], {'Channels': 'Dual', 'Programs': '20', 'Intensity': '0-100mA'}),
        ('Glucose Monitor Kit', 'Blood glucose monitoring kit with 50 test strips included.',
         ['Glucose Monitor', 'Blood Sugar', 'Diabetes', 'Medical', 'Monitor'], {'Strips Included': '50', 'Result': '5 seconds', 'Memory': '500 readings'}),
        ('Nebulizer Machine Portable', 'Quiet portable compressor nebulizer for asthma and respiratory.',
         ['Nebulizer', 'Asthma', 'Respiratory', 'Medical', 'Inhaler', 'Breathing'], {'Type': 'Compressor', 'Noise': '<45dB', 'Particle': '1-5 micron'}),
        ('First Aid Kit Complete 200-Piece', 'Comprehensive 200-piece first aid kit in waterproof case.',
         ['First Aid', 'First Aid Kit', 'Medical', 'Emergency', 'Safety'], {'Pieces': '200+', 'Case': 'Waterproof', 'Compartments': '5'}),
    ],
    'Fashion': [
        ('Running Shoes {type} Performance', 'Lightweight performance running shoes with energy return foam.',
         ['Running Shoes', 'Shoes', 'Running', 'Sport', 'Athletic', 'Fitness'], {'Upper': 'Knit mesh', 'Sole': 'Energy foam', 'Drop': '8mm'}),
        ('Smartwatch Fitness Band Fashion', 'Stylish smartwatch band with health tracking and AMOLED display.',
         ['Smartwatch', 'Fashion Watch', 'Watch', 'Fitness', 'Wearable'], {'Display': 'AMOLED', 'Strap': 'Interchangeable', 'Battery': '10 days'}),
        ('Winter Jacket Puffer {fill}', 'Lightweight puffer jacket with {fill} fill and packable design.',
         ['Puffer Jacket', 'Winter Jacket', 'Jacket', 'Warm', 'Winter', 'Cold'], {'Fill': '{fill}', 'Weight': 'Lightweight', 'Packable': 'Yes'}),
        ('Sunglasses Polarized UV400', 'Polarized UV400 sunglasses with anti-glare lens.',
         ['Sunglasses', 'Polarized', 'UV400', 'Sun', 'Glasses', 'Eye Protection'], {'UV Protection': 'UV400', 'Lens': 'Polarized', 'Frame': 'TR90'}),
        ('Leather Wallet RFID Blocking', 'Slim genuine leather wallet with RFID blocking technology.',
         ['Wallet', 'RFID Wallet', 'Leather', 'Slim Wallet', 'Card Holder'], {'RFID': 'Blocking', 'Material': 'Genuine Leather', 'Capacity': '12 cards'}),
        ('Sport Socks Athletic 6-Pack', 'Moisture-wicking athletic socks with arch support.',
         ['Socks', 'Sport Socks', 'Athletic', 'Running', 'Comfort'], {'Pack': '6 pairs', 'Material': 'Nylon + Spandex', 'Cushion': 'Mid-cushion'}),
        ('Windproof Compact Umbrella', 'Durable windproof compact travel umbrella with automatic open-close.',
         ['Umbrella', 'Rain', 'Rainy', 'Travel', 'Windproof', 'Storm'], {'Ribs': '9 fiberglass', 'Canopy': '210T Teflon', 'Auto-Open': 'Yes'}),
        ('Waterproof Hooded Raincoat', 'Breathable and fully waterproof hooded raincoat for outdoor activities.',
         ['Rain Coat', 'Raincoat', 'Rainy', 'Waterproof', 'Jacket', 'Fashion'], {'Material': 'Polyester', 'Waterproof Rating': '10000mm', 'Breathable': 'Yes'}),
        ('Waterproof Rain Boots', 'Comfortable and stylish waterproof rubber rain boots for wet weather.',
         ['Rain Boots', 'Boots', 'Rainy', 'Waterproof', 'Shoes', 'Footwear'], {'Material': 'Natural Rubber', 'Insole': 'Cushioned', 'Sole': 'Slip-resistant'}),
        ('Water-Resistant Backpack Cover', 'Ultra-light water-resistant nylon backpack cover for monsoon hiking.',
         ['Backpack Cover', 'Rainy', 'Waterproof', 'Bag', 'Cover', 'Travel'], {'Material': '190T Nylon', 'Capacity': '30-45L', 'Reflective': 'Yes'}),
    ],
}

# ─── Image Pool ───────────────────────────────────────────────────────────────

def _get_image_url(category_name: str, index: int) -> str:
    """Return a realistic Unsplash-style placeholder image URL."""
    keyword_map = {
        'Electronics': 'electronics,gadget',
        'Laptop Accessories': 'laptop,computer',
        'Phone Accessories': 'smartphone,phone',
        'Home Appliances': 'home,appliance',
        'Kitchen': 'kitchen,cooking',
        'Furniture': 'furniture,interior',
        'Health': 'health,wellness',
        'Fitness': 'fitness,gym',
        'Beauty': 'beauty,cosmetics',
        'Office': 'office,desk',
        'Gaming': 'gaming,controller',
        'Books': 'book,library',
        'Pet Supplies': 'pet,dog,cat',
        'Baby Care': 'baby,child',
        'Automotive': 'car,automotive',
        'Travel': 'travel,luggage',
        'Garden': 'garden,plants',
        'Lighting': 'lighting,lamp',
        'Medical': 'medical,health',
        'Fashion': 'fashion,clothing',
    }
    kw = keyword_map.get(category_name, 'product')
    seed = (index * 7 + hash(category_name)) % 1000
    return f'https://picsum.photos/seed/{kw.replace(",", "")}{seed}/400/400'


# ─── Management Command ────────────────────────────────────────────────────────

class Command(BaseCommand):
    """Seed the database with realistic product data."""

    help = 'Seed database with 10,000 realistic products'

    def add_arguments(self, parser):
        parser.add_argument('--products', type=int, default=10000, help='Number of products to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing products before seeding')

    def handle(self, *args, **options):
        total = options['products']
        clear = options['clear']

        self.stdout.write(self.style.WARNING('\n[+] Smart Commerce AI - Product Seeder\n'))

        if clear:
            self.stdout.write('[-] Clearing existing data...')
            Product.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('[+] Cleared.\n'))

        # ─── 1. Create Categories ──────────────────────────────────────────
        self.stdout.write('[+] Creating categories...')
        categories = {}
        for name, desc in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'slug': slugify(name)},
            )
            categories[name] = cat
        self.stdout.write(self.style.SUCCESS(f'   [+] {len(categories)} categories ready.\n'))

        # ─── 2. Create Brands ──────────────────────────────────────────────
        self.stdout.write('[+] Creating 200 brands...')
        brand_list = []
        for i, name in enumerate(BRAND_NAMES[:200]):
            brand, _ = Brand.objects.get_or_create(
                name=name,
                defaults={
                    'country': random.choice(COUNTRIES),
                    'logo': f'https://ui-avatars.com/api/?name={name.replace(" ", "+")}&background=2563EB&color=fff&size=64',
                }
            )
            brand_list.append(brand)
        self.stdout.write(self.style.SUCCESS(f'   [+] {len(brand_list)} brands ready.\n'))

        # ─── 3. Create Products ────────────────────────────────────────────
        self.stdout.write(f'[+] Generating {total:,} products (this may take a moment)...\n')

        created = 0
        batch_size = 200
        batch = []
        used_skus = set()
        used_slugs = set()

        cat_names = list(PRODUCT_TEMPLATES.keys())

        for i in range(total):
            cat_name = cat_names[i % len(cat_names)]
            templates = PRODUCT_TEMPLATES[cat_name]
            template = templates[i % len(templates)]

            name_tpl, desc_tpl, tags, specs_tpl = template
            category = categories.get(cat_name)
            brand = random.choice(brand_list)

            # Fill template variables
            tpl_vars = {
                'size': random.choice([32, 40, 43, 50, 55, 65, 75]),
                'capacity': random.choice([5000, 10000, 20000, 30000]),
                'fans': random.choice([2, 4, 6]),
                'watts': random.choice([45, 65, 100, 120, 140]),
                'liter': random.choice([2, 3, 5, 6, 8, 10, 15]),
                'btu': random.choice([8000, 10000, 12000, 14000, 18000]),
                'model': random.choice(['iPhone', 'Samsung', 'Pixel', 'OnePlus']),
                'thickness': random.choice([6, 8, 10, 12]),
                'weight': random.choice([24, 32, 40, 52]),
                'pint': random.choice([20, 30, 35, 50, 70]),
                'coverage': random.choice([300, 500, 700, 1000]),
                'watt': random.choice([1200, 1600, 1875, 2200]),
                'meter': random.choice([5, 10, 15, 20]),
                'feet': random.choice([25, 50, 75, 100]),
                'level': random.choice(['Beginner', 'Intermediate', 'Advanced']),
                'compartments': random.choice([5, 7, 9, 12]),
                'dpi': random.choice([16000, 25600, 32000, 52000]),
                'hz': random.choice([144, 165, 240, 360]),
                'amp': random.choice([1000, 1500, 2000, 2500]),
                'fill': random.choice(['800-fill down', '700-fill goose down', 'synthetic']),
                'type': random.choice(['Trail', 'Road', 'Track', 'Cross']),
            }

            try:
                product_name = name_tpl.format(**tpl_vars)
            except KeyError:
                product_name = name_tpl

            try:
                short_desc = desc_tpl.format(**tpl_vars)
            except KeyError:
                short_desc = desc_tpl

            # Add brand variation to name to increase uniqueness
            if i % 3 == 0:
                product_name = f'{brand.name} {product_name}'

            # Price
            base_price = round(random.uniform(5, 2500), 2)
            has_discount = random.random() < 0.4
            discount_price = round(base_price * random.uniform(0.65, 0.92), 2) if has_discount else None

            # Rating
            rating = round(random.uniform(3.0, 5.0), 1)
            review_count = random.randint(0, 15000)

            # Stock
            stock = random.randint(0, 500)

            # Unique slug
            base_slug = slugify(product_name)[:250]
            slug = base_slug
            counter = 1
            while slug in used_slugs:
                slug = f'{base_slug}-{i}-{counter}'
                counter += 1
            used_slugs.add(slug)

            # Unique SKU
            sku = str(uuid.uuid4())[:12].upper()
            while sku in used_skus:
                sku = str(uuid.uuid4())[:12].upper()
            used_skus.add(sku)

            # Image
            image = _get_image_url(cat_name, i)

            # Tags — product-specific + brand
            product_tags = list(set(tags + [brand.name, cat_name]))
            random.shuffle(product_tags)

            # Specs
            try:
                specs = {k: str(v).format(**tpl_vars) for k, v in specs_tpl.items()}
            except (KeyError, ValueError):
                specs = specs_tpl

            # Full description
            full_description = (
                f'{short_desc}\n\n'
                f'Key Features:\n'
                f'• Manufactured by {brand.name} ({brand.country})\n'
                f'• Category: {cat_name}\n'
                f'• {"In Stock" if stock > 0 else "Pre-order"}: {stock} units available\n'
                f'• Rated {rating}/5 by {review_count:,} customers\n\n'
                f'Specifications:\n' +
                '\n'.join(f'• {k}: {v}' for k, v in specs.items())
            )

            p = Product(
                name=product_name,
                slug=slug,
                sku=sku,
                brand=brand,
                category=category,
                price=Decimal(str(base_price)),
                discount_price=Decimal(str(discount_price)) if discount_price else None,
                stock=stock,
                rating=Decimal(str(rating)),
                review_count=review_count,
                image=image,
                short_description=short_desc,
                full_description=full_description,
                specifications=specs,
                tags=product_tags,
                is_active=True,
            )
            batch.append(p)

            if len(batch) >= batch_size:
                Product.objects.bulk_create(batch, ignore_conflicts=True)
                created += len(batch)
                batch = []
                progress = (created / total) * 100
                self.stdout.write(f'\r   Progress: {created:,}/{total:,} ({progress:.1f}%)', ending='')
                self.stdout.flush()

        # Final batch
        if batch:
            Product.objects.bulk_create(batch, ignore_conflicts=True)
            created += len(batch)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('\n[+] Seeding complete!\n'))
        self.stdout.write(f'   [+] Products: {Product.objects.count():,}')
        self.stdout.write(f'   [+] Categories: {Category.objects.count()}')
        self.stdout.write(f'   [+] Brands: {Brand.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n[+] Smart Commerce AI is ready!\n'))
