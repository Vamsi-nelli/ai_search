from django.shortcuts import redirect

def product_detail(request, slug: str):
    """Redirect product detail requests to the home page chat UI."""
    return redirect('core:home')
