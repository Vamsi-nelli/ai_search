from django.shortcuts import redirect

def search_page(request):
    """Redirect search queries to the home page chat UI."""
    return redirect('core:home')
