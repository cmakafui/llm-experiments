import duckdb

def get_db_connection():
    return duckdb.connect(database='data/graph_data.duckdb', read_only=True)

def get_table_info(conn):
    table_info = "### Table: employee_interactions\n"
    
    query = """
        SELECT 
            column_name,
            data_type,
            COALESCE(comment, 'No description') as col_description
        FROM 
            duckdb_columns
        WHERE table_name = 'employee_interactions'
    """
    
    result = conn.execute(query).fetchall()
    for row in result:
        column_name, data_type, col_description = row
        table_info += f"col_name: {column_name}, dtype: {data_type}, description: {col_description}\n"
    
    return table_info

# Example usage:
if __name__ == "__main__":
    conn = get_db_connection()
    info = get_table_info(conn)
    print(info)
    conn.close()
