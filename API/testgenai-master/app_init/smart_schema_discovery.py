"""
Smart Schema Discovery - Automatically discovers database metadata
Queries SQL Server system tables to get:
- Tables and columns
- Primary keys
- Foreign key relationships
- Sample data
"""

from target_db.database import execute_query_original


def discover_table_schemas(table_names_list):
    """
    Automatically discover comprehensive schema information for given tables
    """
    tables_string = ','.join([f"'{t.strip()}'" for t in table_names_list])

    # Query 1: Get table and column information
    schema_query = f"""
    SELECT
        t.TABLE_SCHEMA,
        t.TABLE_NAME,
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.IS_NULLABLE,
        CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as IS_PRIMARY_KEY,
        c.ORDINAL_POSITION
    FROM
        INFORMATION_SCHEMA.TABLES t
    INNER JOIN
        INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
    LEFT JOIN (
        SELECT
            ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
        FROM
            INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        INNER JOIN
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        WHERE
            tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
    ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME AND c.TABLE_SCHEMA = pk.TABLE_SCHEMA
    WHERE
        t.TABLE_NAME IN ({tables_string})
        AND t.TABLE_TYPE = 'BASE TABLE'
    ORDER BY
        t.TABLE_NAME, c.ORDINAL_POSITION
    """

    schema_rows, schema_cols = execute_query_original(None, None, None, schema_query, False)[:2]

    # Query 2: Get foreign key relationships
    fk_query = f"""
    SELECT
        fk.name AS FK_Name,
        OBJECT_NAME(fk.parent_object_id) AS Parent_Table,
        COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS Parent_Column,
        OBJECT_NAME(fk.referenced_object_id) AS Referenced_Table,
        COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS Referenced_Column
    FROM
        sys.foreign_keys fk
    INNER JOIN
        sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    WHERE
        OBJECT_NAME(fk.parent_object_id) IN ({tables_string})
        OR OBJECT_NAME(fk.referenced_object_id) IN ({tables_string})
    """

    fk_rows, fk_cols = execute_query_original(None, None, None, fk_query, False)[:2]

    return schema_rows, fk_rows


def build_enhanced_schema_context(table_names_list):
    """
    Build comprehensive schema context with relationships
    """
    schema_rows, fk_rows = discover_table_schemas(table_names_list)

    # Organize schema by table
    tables_schema = {}
    for row in schema_rows:
        schema_name, table_name, col_name, data_type, max_len, nullable, is_pk, ordinal = row

        full_table_name = f"{schema_name}.{table_name}" if schema_name != 'dbo' else table_name

        if full_table_name not in tables_schema:
            tables_schema[full_table_name] = {
                'columns': [],
                'primary_keys': [],
                'foreign_keys': []
            }

        col_def = f"{col_name} {data_type}"
        if max_len and max_len > 0:
            col_def += f"({max_len})"
        if is_pk:
            col_def += " PRIMARY KEY"
            tables_schema[full_table_name]['primary_keys'].append(col_name)
        if nullable == 'NO':
            col_def += " NOT NULL"

        tables_schema[full_table_name]['columns'].append(col_def)

    # Add foreign key information
    for fk_row in fk_rows:
        fk_name, parent_table, parent_col, ref_table, ref_col = fk_row

        if parent_table in tables_schema:
            fk_info = f"{parent_col} → {ref_table}.{ref_col}"
            if fk_info not in tables_schema[parent_table]['foreign_keys']:
                tables_schema[parent_table]['foreign_keys'].append(fk_info)

    # Build CREATE TABLE statements with relationship info
    create_statements = {}
    for table_name, schema_info in tables_schema.items():
        create_stmt = f"CREATE TABLE {table_name} (\n  "
        create_stmt += ",\n  ".join(schema_info['columns'])
        create_stmt += "\n)"

        # Add relationship comments
        if schema_info['foreign_keys']:
            create_stmt += "\n/* Foreign Keys:\n"
            for fk in schema_info['foreign_keys']:
                create_stmt += f"   - {fk}\n"
            create_stmt += "*/"

        create_statements[table_name.upper()] = create_stmt

    return create_statements


def get_sample_data_for_tables(table_names_list):
    """
    Get sample data for tables
    """
    sample_data_dict = {}
    column_names_dict = {}

    for table in table_names_list:
        try:
            sample_query = f"SELECT TOP 3 * FROM {table}"
            sample_rows, column_names = execute_query_original(None, None, None, sample_query, False)[:2]
            sample_data_dict[table.upper()] = sample_rows
            column_names_dict[table.upper()] = column_names
        except Exception as e:
            print(f"Error fetching sample data for {table}: {e}")
            sample_data_dict[table.upper()] = []
            column_names_dict[table.upper()] = []

    return sample_data_dict, column_names_dict


def format_sample_data(sample_rows, column_names):
    """Format sample data as column: value1, value2, value3"""
    if not sample_rows or not column_names:
        return "No sample data available"

    column_data = {column_name: [] for column_name in column_names}

    for row in sample_rows:
        for i, value in enumerate(row):
            column_data[column_names[i]].append(str(value))

    formatted_data = []
    for column_name, values in column_data.items():
        formatted_data.append(f"{column_name}: {', '.join(values)}")

    return "\n".join(formatted_data)


def add_sample_data_to_schema(create_statements_dict, sample_data_dict, column_names_dict):
    """
    Add sample data as comments to CREATE statements
    """
    enhanced_statements = {}

    for table_name, create_stmt in create_statements_dict.items():
        sample_data = format_sample_data(
            sample_data_dict.get(table_name, []),
            column_names_dict.get(table_name, [])
        )

        comment_block = f"/* Sample data:\n{sample_data}\n*/"
        enhanced_statements[table_name] = create_stmt + "\n" + comment_block

    return enhanced_statements
