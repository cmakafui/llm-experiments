from faker import Faker
import duckdb
import pandas as pd
import random

fake = Faker()

def create_synthetic_data(n=1000):
    data = []
    departments = ['HR', 'Engineering', 'Sales', 'Marketing']
    projects = ['Project A', 'Project B', 'Project C', 'Project D']
    
    # Create hierarchical relationships within departments
    department_heads = {dept: fake.name() for dept in departments}
    
    # Generate unique employee IDs
    employee_ids = random.sample(range(1, n + 1), n)
    
    for employee_id in employee_ids:
        department = random.choice(departments)
        
        data.append({
            'employee_id': employee_id,
            'name': fake.name(),
            'department': department,
            'department_head': department_heads[department],
            'interaction_date': fake.date_this_year(),
            'interaction_count': random.randint(1, 50),
            'project': random.choice(projects),
            'interaction_with': fake.name()
        })
    
    return pd.DataFrame(data)

df = create_synthetic_data()

conn = duckdb.connect(database='data/graph_data.duckdb', read_only=False)
create_tbl_query = """
DROP TABLE IF EXISTS employee_interactions;
CREATE TABLE employee_interactions (
    employee_id INT,
    name VARCHAR,
    department VARCHAR,
    department_head VARCHAR,
    interaction_date DATE,
    interaction_count INT,
    project VARCHAR,
    interaction_with VARCHAR
);

COMMENT ON COLUMN employee_interactions.employee_id IS 'The unique identifier for the employee';
COMMENT ON COLUMN employee_interactions.name IS 'The name of the employee';
COMMENT ON COLUMN employee_interactions.department IS 'The department the employee belongs to';
COMMENT ON COLUMN employee_interactions.department_head IS 'The head of the department';
COMMENT ON COLUMN employee_interactions.interaction_date IS 'The date of the interaction';
COMMENT ON COLUMN employee_interactions.interaction_count IS 'The number of interactions the employee had on the date';
COMMENT ON COLUMN employee_interactions.project IS 'The project the employee is working on';
COMMENT ON COLUMN employee_interactions.interaction_with IS 'The name of the person the employee interacted with';
"""

conn.sql(create_tbl_query)
conn.register("df", df)
conn.execute("INSERT INTO employee_interactions SELECT * FROM df")

# Verify the table
print(conn.sql("SELECT * FROM employee_interactions LIMIT 5").fetchall())
conn.close()
