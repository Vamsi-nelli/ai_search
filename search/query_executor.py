import re
import logging
from datetime import datetime, date
from django.db import connection, transaction

logger = logging.getLogger(__name__)


def _is_aggregate_query(sql: str) -> bool:
    """
    Returns True if the query is an aggregate query (returns a single summary row)
    and should NOT have LIMIT appended.
    An aggregate query:
      - Contains COUNT(*), SUM(...), AVG(...), MIN(...), MAX(...) at the top level
      - Does NOT have a GROUP BY (or has GROUP BY but a small, fixed number of groups)
    """
    sql_upper = sql.upper()
    has_aggregate = bool(re.search(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', sql_upper))
    has_group_by = 'GROUP BY' in sql_upper
    has_limit = 'LIMIT' in sql_upper

    # If it's a pure aggregate with no GROUP BY, definitely don't add LIMIT
    if has_aggregate and not has_group_by and not has_limit:
        return True

    return False


def execute_read_only_query(sql_query: str) -> dict:
    """
    Executes a SQL query in a read-only transaction and returns the results.
    Restricts to SELECT statements, sanitizes dangerous keywords,
    and enforces a max of 10 rows for listing queries.
    """
    sql_query_stripped = sql_query.strip()
    sql_clean = sql_query_stripped.lower()

    # --- 1. Ensure it's a SELECT ---
    if not sql_clean.startswith('select'):
        return {
            'success': False,
            'error': 'Only SELECT queries are allowed.'
        }

    # --- 2. Block write/DDL keywords ---
    forbidden = ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'truncate', 'grant']
    words_in_query = re.findall(r'\b\w+\b', sql_clean)
    for keyword in forbidden:
        if keyword in words_in_query:
            return {
                'success': False,
                'error': f'Execution blocked: forbidden operation "{keyword}" detected in query.'
            }

    # --- 3. Append LIMIT 10 only for non-aggregate queries ---
    if 'limit' not in sql_clean and not _is_aggregate_query(sql_query_stripped):
        # Remove trailing semicolon before adding LIMIT
        sql_query_stripped = sql_query_stripped.rstrip(';') + ' LIMIT 10;'
    elif 'limit' not in sql_clean and _is_aggregate_query(sql_query_stripped):
        # Aggregate query — just ensure it ends with semicolon
        if not sql_query_stripped.endswith(';'):
            sql_query_stripped += ';'

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql_query_stripped)
                columns = [col[0] for col in cursor.description] if cursor.description else []
                # Fetch at most 10 rows regardless
                rows = cursor.fetchmany(10)

                # Serialize rows to JSON-safe types
                formatted_rows = []
                for row in rows:
                    formatted_row = []
                    for val in row:
                        if isinstance(val, (datetime, date)):
                            formatted_row.append(val.isoformat())
                        elif hasattr(val, '__float__'):  # Decimal
                            formatted_row.append(round(float(val), 2))
                        elif isinstance(val, bytes):
                            formatted_row.append(val.decode('utf-8', errors='ignore'))
                        else:
                            formatted_row.append(val)
                    formatted_rows.append(formatted_row)

                return {
                    'success': True,
                    'query': sql_query_stripped,
                    'columns': columns,
                    'rows': formatted_rows,
                    'row_count': len(formatted_rows)
                }

    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        return {
            'success': False,
            'query': sql_query_stripped,
            'error': str(e)
        }
