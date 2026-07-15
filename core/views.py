from django.shortcuts import render

def home(request):
    """Homepage serving the AI chat database explorer."""
    context = {
        'page_title': 'Ecommerce AI Explorer — Natural Language SQL Agent',
        'meta_description': 'Ask any question about categories, products, orders, users, and transactions in natural language and see database results instantly.',
    }
    return render(request, 'home.html', context)
