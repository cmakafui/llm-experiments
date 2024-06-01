import duckdb

def get_db_connection(db_path='data/crypto_data.duckdb'):
    return duckdb.connect(db_path, read_only = True)

def get_table_info(conn):
    table_info = "### Table: crypto_data\n"
    
    query = """
        SELECT 
            column_name,
            data_type,
            COALESCE(comment, 'No description') as col_description
        FROM 
            duckdb_columns
        WHERE table_name = 'crypto_data'
    """
    
    result = conn.sql(query).fetchall()
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
