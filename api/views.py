import json
import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.management import call_command

from search.ai_engine import generate_sql_query
from search.query_executor import execute_read_only_query
from products.models import Category, Product, User, Order, Transaction

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    """
    POST /api/chat/
    Accepts: { "message": "What are the top 5 most expensive products?" }
    Returns: SQL query, columns, rows, and explanation.
    """
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'success': False, 'error': 'Invalid JSON body.'}, status=400)

        message = body.get('message', '').strip()
        if not message:
            return JsonResponse({'success': False, 'error': 'Message is required.'}, status=400)

        if len(message) > 500:
            return JsonResponse({'success': False, 'error': 'Query is too long.'}, status=400)

        # 1. Generate SQL via Grok
        ai_res = generate_sql_query(message)
        sql = ai_res.get('sql', '')
        explanation = ai_res.get('explanation', '')

        if not sql:
            return JsonResponse({
                'success': False,
                'error': 'Could not generate a database query for your request.'
            }, status=500)

        # 2. Execute SQL query securely
        query_res = execute_read_only_query(sql)

        if not query_res.get('success', False):
            return JsonResponse({
                'success': False,
                'sql': sql,
                'explanation': explanation,
                'error': query_res.get('error', 'Database execution error.')
            })

        return JsonResponse({
            'success': True,
            'sql': sql,
            'explanation': explanation,
            'columns': query_res.get('columns', []),
            'rows': query_res.get('rows', []),
            'row_count': query_res.get('row_count', 0)
        })


@method_decorator(csrf_exempt, name='dispatch')
class ResetDBAPIView(View):
    """
    POST /api/reset-db/
    Triggers the custom seed_ecommerce command to clear and seed 10k+ rows of data.
    """
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            call_command('seed_ecommerce')
            return JsonResponse({
                'success': True,
                'message': 'Database reset successfully and seeded with 10k+ rows of clean data!'
            })
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to seed database: {str(e)}'
            }, status=500)


class DBStatsAPIView(View):
    """
    GET /api/db-stats/
    Returns the current counts for Category, Product, User, Order, Transaction tables.
    """
    def get(self, request, *args, **kwargs) -> JsonResponse:
        try:
            cat_count = Category.objects.count()
            prod_count = Product.objects.count()
            user_count = User.objects.count()
            order_count = Order.objects.count()
            trans_count = Transaction.objects.count()
            total_count = cat_count + prod_count + user_count + order_count + trans_count

            return JsonResponse({
                'success': True,
                'stats': {
                    'categories': cat_count,
                    'products': prod_count,
                    'users': user_count,
                    'orders': order_count,
                    'transactions': trans_count,
                    'total': total_count
                }
            })
        except Exception as e:
            logger.error(f"Error fetching database statistics: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
