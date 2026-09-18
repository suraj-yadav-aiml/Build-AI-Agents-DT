def build_sql_generation_prompt(
    user_request: str,
    database_type: str,
) -> str:
    """
    Build a prompt for SQL generation.

    Args:
        user_request: User's SQL requirement.
        database_type: Target database engine.

    Returns:
        SQL generation prompt.
    """
    return f"""
You are an expert SQL engineer.

Generate a SQL query based on the user's request.

Database Type:
{database_type}

User Request:
{user_request}

Requirements:
- Generate syntactically correct SQL for the specified database.
- Use clean and readable formatting.
- Use meaningful aliases.
- Add comments only when they improve understanding.
- Briefly explain the generated query.
- Do not use features that are unavailable in the specified database.
""".strip()


def build_sql_explanation_prompt(
    sql_query: str,
    database_type: str,
) -> str:
    """
    Build a prompt for SQL explanation.

    Args:
        sql_query: SQL query to explain.
        database_type: Database engine.
        
    Returns:
        SQL explanation prompt.
    """
    return f"""
You are an expert SQL teacher.

Explain the following SQL query in beginner-friendly language.

Database Type:
{database_type}

SQL Query:
{sql_query}

Requirements:
- Explain the query step-by-step.
- Explain each important clause.
- Explain joins if present.
- Explain filters and conditions if present.
- Explain grouping and aggregation if present.
- Explain subqueries or CTEs if present.
- Keep the language simple and practical.
""".strip()


def build_sql_optimization_prompt(
    sql_query: str,
    database_type: str,
) -> str:
    """
    Build a prompt for SQL optimization.

    Args:
        sql_query: SQL query to optimize.
        database_type: Database engine.

    Returns:
        SQL optimization prompt.
    """
    return f"""
You are an expert database performance engineer.

Analyze and optimize the following SQL query.

Database Type:
{database_type}

SQL Query:
{sql_query}

Requirements:
- Identify potential performance problems.
- Provide an optimized version where appropriate.
- Improve readability where possible.
- Discuss indexing opportunities.
- Consider joins, filters, grouping, and sorting.
- Mention database-specific considerations.
- Explain each important optimization.
- Do not change the intended result of the query.
""".strip()


def build_sql_debug_prompt(
    sql_query: str,
    database_type: str,
) -> str:
    """
    Build a prompt for SQL debugging.

    Args:
        sql_query: SQL query to debug.
        database_type: Database engine.

    Returns:
        SQL debugging prompt.
    """
    return f"""
You are an expert SQL debugger.

Analyze the following SQL query and identify possible problems.

Database Type:
{database_type}

SQL Query:
{sql_query}

Requirements:
- Identify syntax errors.
- Identify logical errors.
- Identify potential runtime problems.
- Identify database-specific issues.
- Suggest corrected SQL when possible.
- Explain why each correction is necessary.
- Keep the explanation clear and practical.
""".strip()