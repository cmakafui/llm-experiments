import duckdb

# Connect to DuckDB (this will create a new file 'crypto_data.duckdb' if it does not exist)
conn = duckdb.connect('data/crypto_data.duckdb')

# Create the table with comments
create_tbl_query = """
DROP TABLE IF EXISTS crypto_data;
CREATE TABLE crypto_data (
    date DATE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume DOUBLE,
    symbol VARCHAR(10)
);

COMMENT ON COLUMN crypto_data.date IS 'The date of the data point';
COMMENT ON COLUMN crypto_data.high IS 'The high price for the crypto on the date';
COMMENT ON COLUMN crypto_data.low IS 'The low price for the crypto on the date';
COMMENT ON COLUMN crypto_data.close IS 'The closing price for the crypto on the date';
COMMENT ON COLUMN crypto_data.volume IS 'The trading volume on the date';
COMMENT ON COLUMN crypto_data.symbol IS 'The trading symbol of the cryptocurrency, either BTC, ETH, or SOL';
"""
conn.execute(create_tbl_query)

# Read and insert the data from CSV files directly into DuckDB
read_insert_query = """
INSERT INTO crypto_data
SELECT 
    CAST(timestamp AS DATE) AS date,
    high AS high,
    low AS low,
    close AS close,
    volume AS volume,
    'BTC' AS symbol
FROM read_csv_auto('data/bitcoin_data.csv', delim=';')
UNION ALL
SELECT 
    CAST(timestamp AS DATE) AS date,
    high AS high,
    low AS low,
    close AS close,
    volume AS volume,
    'ETH' AS symbol
FROM read_csv_auto('data/ethereum_data.csv', delim=';')
UNION ALL
SELECT 
    CAST(timestamp AS DATE) AS date,
    high AS high,
    low AS low,
    close AS close,
    volume AS volume,
    'SOL' AS symbol
FROM read_csv_auto('data/solana_data.csv', delim=';');
"""
conn.execute(read_insert_query)

# Verify the table
print(conn.execute("SELECT * FROM crypto_data LIMIT 5").fetchall())

# Close the connection
conn.close()
