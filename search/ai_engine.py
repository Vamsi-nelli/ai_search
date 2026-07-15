import json
import re
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert PostgreSQL SQL Agent for an Ecommerce analytics platform.
Your ONLY job: read the user's natural language question and produce a precise, correct PostgreSQL SELECT query.

═══════════════════════════════════════════════════════════
  DATABASE SCHEMA (5 tables with full relationship map)
═══════════════════════════════════════════════════════════

TABLE: categories
  - id          SERIAL PRIMARY KEY
  - name        VARCHAR(100) UNIQUE
  - slug        VARCHAR(120) UNIQUE
  - description TEXT
  Relation: One category → MANY products via products.category_id

TABLE: products
  - id          SERIAL PRIMARY KEY
  - category_id INTEGER FK → categories(id)
  - name        VARCHAR(255)
  - price       DECIMAL(10,2)
  - stock       INTEGER
  - rating      DECIMAL(3,1)   [0.0 – 5.0]
  - created_at  TIMESTAMP
  Relation: Many products → one category; one product → MANY orders via orders.product_id

TABLE: users
  - id          SERIAL PRIMARY KEY
  - first_name  VARCHAR(100)
  - last_name   VARCHAR(100)
  - email       VARCHAR(150) UNIQUE
  - phone       VARCHAR(50)
  - city        VARCHAR(100)
  - country     VARCHAR(100)
  - created_at  TIMESTAMP
  Relation: One user → MANY orders via orders.user_id

TABLE: orders
  - id           SERIAL PRIMARY KEY
  - user_id      INTEGER FK → users(id)
  - product_id   INTEGER FK → products(id)
  - quantity     INTEGER
  - total_amount DECIMAL(10,2)
  - status       VARCHAR(50)   VALUES: 'Pending' | 'Shipped' | 'Delivered' | 'Cancelled'
  - created_at   TIMESTAMP
  Relation: One order → one user; one order → one product; one order → one transaction

TABLE: transactions
  - id              SERIAL PRIMARY KEY
  - order_id        INTEGER FK → orders(id)
  - payment_method  VARCHAR(50)   VALUES: 'Credit Card' | 'PayPal' | 'Bank Transfer' | 'Cryptocurrency' | 'Apple Pay'
  - status          VARCHAR(50)   VALUES: 'Success' | 'Failed' | 'Refunded'
  - amount          DECIMAL(10,2)
  - transaction_fee DECIMAL(10,2)
  - created_at      TIMESTAMP

JOIN PATHS:
  transactions ↔ orders:      transactions.order_id  = orders.id
  orders       ↔ users:       orders.user_id         = users.id
  orders       ↔ products:    orders.product_id      = products.id
  products     ↔ categories:  products.category_id   = categories.id

═══════════════════════════════════════════════════════════
  DATE / TIME VOCABULARY — CRITICAL
═══════════════════════════════════════════════════════════

Always translate these time words to PostgreSQL date expressions:
  "today"           → DATE(created_at) = CURRENT_DATE
  "yesterday"       → DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
  "this week"       → DATE(created_at) >= DATE_TRUNC('week', CURRENT_DATE)
  "last week"       → DATE(created_at) BETWEEN DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '7 days'
                      AND DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '1 day'
  "this month"      → DATE(created_at) >= DATE_TRUNC('month', CURRENT_DATE)
  "last month"      → DATE(created_at) >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                      AND DATE(created_at) < DATE_TRUNC('month', CURRENT_DATE)
  "this year"       → EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)
  "last N days"     → created_at >= CURRENT_DATE - INTERVAL 'N days'
  "last N months"   → created_at >= CURRENT_DATE - INTERVAL 'N months'

═══════════════════════════════════════════════════════════
  QUERY INTENT RULES
═══════════════════════════════════════════════════════════

RULE 1 — SPECIFIC STATUS / FIELD FILTER:
  If the user names a SPECIFIC value (e.g., "Cancelled", "PayPal", "Success", "India"),
  always add WHERE to filter on that exact value using ILIKE for strings.
  Do NOT use GROUP BY instead — filter first, THEN aggregate.

  ✓ Correct: "today cancelled orders count"
    → SELECT COUNT(*) AS cancelled_count
       FROM orders
       WHERE DATE(created_at) = CURRENT_DATE
         AND status ILIKE 'Cancelled';

  ✗ Wrong:
    → SELECT status, COUNT(*) FROM orders GROUP BY status;  ← this ignores 'today' and 'Cancelled'

RULE 2 — AGGREGATE vs LISTING:
  Words signaling AGGREGATE (return ONE or FEW summary rows — never add LIMIT):
    total, count, how many, number of, sum, average, avg, min, max

  Words signaling LISTING (return individual rows — add LIMIT N, max 10):
    show, list, find, get, give me, display, top N, recent, latest

  Exception: "top N by X" → SELECT ... ORDER BY X DESC LIMIT N  (still a listing)

RULE 3 — GROUP BY:
  Only use GROUP BY when the user asks for breakdown/comparison PER something:
  "per category", "by payment method", "for each status", "grouped by country"
  → Use GROUP BY + aggregate function
  → Add LIMIT 10 unless the group is guaranteed small (e.g., status has only 4 values)

RULE 4 — DATE + STATUS COMBINATION:
  When the user combines a date expression with a specific status, BOTH must appear in WHERE.
  Never replace date+status filters with a generic GROUP BY.

  ✓ "today orders count status Cancelled"
    → WHERE DATE(created_at) = CURRENT_DATE AND status ILIKE 'Cancelled'

  ✓ "this week PayPal success transactions total"
    → WHERE DATE(created_at) >= DATE_TRUNC('week', CURRENT_DATE)
        AND payment_method ILIKE 'PayPal'
        AND status ILIKE 'Success'

RULE 5 — CASE-INSENSITIVE MATCHING:
  Always use ILIKE for VARCHAR comparisons. Never use = for user-supplied string values.

RULE 6 — ALIASES:
  All aggregate columns MUST have aliases: COUNT(*) AS total_count, SUM(x) AS total_x

RULE 7 — READ-ONLY:
  ONLY SELECT. Never INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE.

═══════════════════════════════════════════════════════════
  WORKED EXAMPLES
═══════════════════════════════════════════════════════════

Q: "today orders count status is Cancelled"
A: SELECT COUNT(*) AS cancelled_orders_today
   FROM orders
   WHERE DATE(created_at) = CURRENT_DATE
     AND status ILIKE 'Cancelled';

Q: "total PayPal success transactions"
A: SELECT COUNT(*) AS total_count, SUM(amount) AS total_amount
   FROM transactions
   WHERE payment_method ILIKE 'PayPal'
     AND status ILIKE 'Success';

Q: "show top 5 products by rating"
A: SELECT name, price, stock, rating FROM products ORDER BY rating DESC LIMIT 5;

Q: "how many users registered this month"
A: SELECT COUNT(*) AS new_users_this_month
   FROM users
   WHERE DATE(created_at) >= DATE_TRUNC('month', CURRENT_DATE);

Q: "average order amount per status"
A: SELECT status, COUNT(*) AS order_count, AVG(total_amount) AS avg_order_amount
   FROM orders
   GROUP BY status
   ORDER BY avg_order_amount DESC;

Q: "top 5 users by total spending"
A: SELECT u.first_name, u.last_name, u.email, SUM(o.total_amount) AS total_spent
   FROM users u
   JOIN orders o ON o.user_id = u.id
   GROUP BY u.id, u.first_name, u.last_name, u.email
   ORDER BY total_spent DESC LIMIT 5;

Q: "list orders placed yesterday that are Shipped"
A: SELECT o.id, o.quantity, o.total_amount, o.status, o.created_at
   FROM orders o
   WHERE DATE(o.created_at) = CURRENT_DATE - INTERVAL '1 day'
     AND o.status ILIKE 'Shipped'
   LIMIT 10;

Q: "total revenue this month from delivered orders"
A: SELECT COUNT(*) AS delivered_count, SUM(total_amount) AS total_revenue
   FROM orders
   WHERE DATE(created_at) >= DATE_TRUNC('month', CURRENT_DATE)
     AND status ILIKE 'Delivered';

═══════════════════════════════════════════════════════════
  RESPONSE FORMAT — STRICT
═══════════════════════════════════════════════════════════
Return ONLY a raw JSON object. No markdown, no backticks, no extra text.

{
  "sql": "SELECT ... ;",
  "explanation": "One friendly sentence describing what the query computes."
}
"""


def generate_sql_query(user_query: str) -> dict:
    """
    Send user query to Grok AI and return { sql, explanation }.
    Falls back to heuristic generation if API is unavailable.
    """
    api_key = settings.GROK_API_KEY
    if not api_key:
        logger.warning('GROK_API_KEY not configured — using heuristic fallback.')
        return _fallback_sql_generation(user_query)

    payload = {
        'model': settings.GROK_MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_query},
        ],
        'temperature': 0.05,   # very low — we want deterministic SQL
        'max_tokens': 600,
    }

    try:
        response = requests.post(
            settings.GROK_API_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        raw_content = data['choices'][0]['message']['content'].strip()

        # Strip markdown code fences if present
        if '```' in raw_content:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_content)
            raw_content = match.group(1).strip() if match else re.sub(r'```(?:json)?', '', raw_content).replace('```', '').strip()

        if raw_content.lower().startswith('json'):
            raw_content = raw_content[4:].strip()

        result = json.loads(raw_content)

        if not all(k in result for k in ('sql', 'explanation')):
            raise ValueError('AI response missing sql or explanation key.')

        return result

    except Exception as e:
        logger.error(f'Grok SQL generation failed: {e}. Raw: {locals().get("raw_content", "N/A")}')
        return _fallback_sql_generation(user_query)


# ─────────────────────────────────────────────────────────────────────────────
# Heuristic fallback (used when API is offline / fails)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_date_clause(q: str, table_alias: str = '') -> str:
    """Build a WHERE date clause from temporal keywords in the query."""
    col = f"{table_alias}.created_at" if table_alias else "created_at"
    date_col = f"DATE({col})"
    if 'today' in q:
        return f"{date_col} = CURRENT_DATE"
    if 'yesterday' in q:
        return f"{date_col} = CURRENT_DATE - INTERVAL '1 day'"
    if 'this week' in q:
        return f"{col} >= DATE_TRUNC('week', CURRENT_DATE)"
    if 'last week' in q:
        return f"{col} >= DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '7 days' AND {col} < DATE_TRUNC('week', CURRENT_DATE)"
    if 'this month' in q:
        return f"{col} >= DATE_TRUNC('month', CURRENT_DATE)"
    if 'last month' in q:
        return f"{col} >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' AND {col} < DATE_TRUNC('month', CURRENT_DATE)"
    if 'this year' in q:
        return f"EXTRACT(YEAR FROM {col}) = EXTRACT(YEAR FROM CURRENT_DATE)"
    # match "last N days" / "last N months"
    m = re.search(r'last\s+(\d+)\s+(day|days|month|months)', q)
    if m:
        n, unit = m.group(1), m.group(2).rstrip('s') + 's'
        return f"{col} >= CURRENT_DATE - INTERVAL '{n} {unit}'"
    return ''


def _extract_status_clause(q: str, table: str = 'orders') -> str:
    """Detect specific status values mentioned in the query."""
    if table == 'orders':
        for s in ['cancelled', 'delivered', 'shipped', 'pending']:
            if s in q:
                return f"status ILIKE '{s.capitalize()}'"
    elif table == 'transactions':
        for s in ['success', 'failed', 'refunded']:
            if s in q:
                return f"status ILIKE '{s.capitalize()}'"
    return ''


def _is_aggregate(q: str) -> bool:
    return any(w in q for w in ['total', 'count', 'sum', 'average', 'avg', 'how many', 'number of', 'min', 'max'])


def _fallback_sql_generation(user_query: str) -> dict:
    q = user_query.lower()

    # ── TRANSACTIONS ──────────────────────────────────────────────────────────
    if 'transaction' in q or 'payment' in q:
        where = []
        date_clause = _extract_date_clause(q)
        status_clause = _extract_status_clause(q, 'transactions')
        if date_clause:
            where.append(date_clause)
        if status_clause:
            where.append(status_clause)
        for pm in ['paypal', 'credit card', 'bank transfer', 'cryptocurrency', 'apple pay']:
            if pm in q:
                where.append(f"payment_method ILIKE '{pm.title()}'")
                break

        where_str = ('WHERE ' + ' AND '.join(where)) if where else ''

        # Aggregate with no group-by
        if _is_aggregate(q) and 'by' not in q and 'per' not in q and 'each' not in q:
            return {
                "sql": f"SELECT COUNT(*) AS total_count, SUM(amount) AS total_amount FROM transactions {where_str};".strip(),
                "explanation": f"Counting and totalling transactions{' for ' + where_str if where_str else ''}."
            }
        # Group-by breakdown
        if 'by payment' in q or 'per payment' in q or 'each payment' in q or ('group' in q and 'payment' in q):
            return {
                "sql": "SELECT payment_method, COUNT(*) AS total_count, SUM(amount) AS total_amount FROM transactions GROUP BY payment_method ORDER BY total_count DESC;",
                "explanation": "Transactions grouped by payment method."
            }
        if 'by status' in q or 'per status' in q or 'each status' in q:
            return {
                "sql": "SELECT status, COUNT(*) AS total_count, SUM(amount) AS total_amount FROM transactions GROUP BY status ORDER BY total_count DESC;",
                "explanation": "Transactions grouped by status."
            }
        # Listing
        return {
            "sql": f"SELECT id, payment_method, status, amount, transaction_fee, created_at FROM transactions {where_str} ORDER BY created_at DESC LIMIT 10;".strip(),
            "explanation": "Latest 10 matching transactions."
        }

    # ── ORDERS ────────────────────────────────────────────────────────────────
    if 'order' in q:
        where = []
        date_clause = _extract_date_clause(q)
        status_clause = _extract_status_clause(q, 'orders')
        if date_clause:
            where.append(date_clause)
        if status_clause:
            where.append(status_clause)

        where_str = ('WHERE ' + ' AND '.join(where)) if where else ''

        # Specific aggregate (count/total with optional date/status filter)
        if _is_aggregate(q) and 'by' not in q and 'per' not in q and 'each' not in q:
            col_list = "COUNT(*) AS total_orders"
            if 'revenue' in q or 'amount' in q or 'sum' in q:
                col_list += ", SUM(total_amount) AS total_revenue"
            return {
                "sql": f"SELECT {col_list} FROM orders {where_str};".strip(),
                "explanation": f"Counting orders{' for today' if 'today' in q else ''}{' with status ' + status_clause if status_clause else ''}."
            }
        # Group-by status
        if 'by status' in q or 'per status' in q or 'each status' in q or ('group' in q and 'status' in q):
            return {
                "sql": "SELECT status, COUNT(*) AS order_count, SUM(total_amount) AS total_revenue FROM orders GROUP BY status ORDER BY order_count DESC;",
                "explanation": "Orders grouped by status with counts and revenue."
            }
        # Listing
        return {
            "sql": f"SELECT o.id, o.quantity, o.total_amount, o.status, o.created_at FROM orders o {where_str} ORDER BY o.created_at DESC LIMIT 10;".strip(),
            "explanation": "Latest 10 matching orders."
        }

    # ── USERS ─────────────────────────────────────────────────────────────────
    if 'user' in q or 'customer' in q:
        date_clause = _extract_date_clause(q)
        where_str = (f"WHERE {date_clause}") if date_clause else ''
        if _is_aggregate(q):
            return {
                "sql": f"SELECT COUNT(*) AS total_users FROM users {where_str};".strip(),
                "explanation": f"Counting users{' registered today' if 'today' in q else ' this period' if where_str else ''}."
            }
        if 'order' in q or 'most' in q or 'top' in q:
            return {
                "sql": "SELECT u.first_name, u.last_name, u.email, COUNT(o.id) AS order_count FROM users u JOIN orders o ON o.user_id = u.id GROUP BY u.id, u.first_name, u.last_name, u.email ORDER BY order_count DESC LIMIT 10;",
                "explanation": "Top 10 users by order count."
            }
        country = None
        for c in ['india', 'usa', 'united states', 'uk', 'australia', 'canada', 'germany', 'france', 'japan']:
            if c in q:
                country = c.title()
                break
        if country:
            return {
                "sql": f"SELECT first_name, last_name, email, city FROM users WHERE country ILIKE '%{country}%' LIMIT 10;",
                "explanation": f"Listing 10 users from {country}."
            }
        return {
            "sql": f"SELECT first_name, last_name, email, city, country FROM users {where_str} ORDER BY created_at DESC LIMIT 10;".strip(),
            "explanation": "Latest 10 registered users."
        }

    # ── PRODUCTS ─────────────────────────────────────────────────────────────
    if 'product' in q or 'item' in q:
        if _is_aggregate(q):
            if 'category' in q or 'per ' in q or 'each' in q:
                return {
                    "sql": "SELECT c.name AS category, COUNT(p.id) AS product_count, AVG(p.price) AS avg_price FROM products p JOIN categories c ON p.category_id = c.id GROUP BY c.name ORDER BY product_count DESC LIMIT 12;",
                    "explanation": "Product count and average price per category."
                }
            return {
                "sql": "SELECT COUNT(*) AS total_products, AVG(price) AS avg_price, MIN(price) AS min_price, MAX(price) AS max_price FROM products;",
                "explanation": "Aggregate stats across all products."
            }
        if 'stock' in q:
            return {"sql": "SELECT name, price, stock FROM products WHERE stock < 10 ORDER BY stock ASC LIMIT 10;", "explanation": "Products with stock below 10."}
        if 'rating' in q:
            return {"sql": "SELECT name, price, stock, rating FROM products ORDER BY rating DESC LIMIT 10;", "explanation": "Top 10 products by rating."}
        return {"sql": "SELECT name, price, stock, rating FROM products ORDER BY id LIMIT 10;", "explanation": "Sample of 10 products."}

    # ── CATEGORIES ────────────────────────────────────────────────────────────
    if 'categor' in q:
        return {
            "sql": "SELECT c.name, c.description, COUNT(p.id) AS product_count FROM categories c LEFT JOIN products p ON p.category_id = c.id GROUP BY c.id, c.name, c.description ORDER BY product_count DESC;",
            "explanation": "All categories with their product counts."
        }

    # Generic
    return {
        "sql": "SELECT name, price, stock, rating FROM products ORDER BY id LIMIT 10;",
        "explanation": "Showing a sample of 10 products."
    }
