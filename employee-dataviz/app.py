# app.py
import asyncio
from timeit import default_timer as timer
import streamlit as st
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from openai import AsyncOpenAI
from decouple import config
from string import Template
import instructor
from visualization import get_bar_chart, get_pie_chart, get_line_chart, get_network_graph
from db import get_db_connection, get_table_info

# Initialize OpenAI client
async_client = instructor.from_openai(AsyncOpenAI(api_key=config("OPENAI_API_KEY")))

# Set Streamlit page configuration
st.set_page_config(layout="wide")

# Cache the database connection and cursor
@st.cache_resource
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    return cursor, conn

cur, conn = init_db()

analysis_system_message = """
You are a DuckDB and data visualization expert. Given a data visualization request, you return a visualization plan consisting of visualization tasks.
Each visualization task consists of:
1. Syntactically correct SQL query to get the data necessary to answer the request.
2. The correct visualization type to use (BAR_CHART, PIE_CHART, LINE_CHART, or NETWORK_GRAPH), with the required parameters.
3. Parameters for the task, as a dictionary:
    - Pie chart tasks require no parameters
    - Bar chart tasks require a 'bar_mode', either "group" or "stack"
    - Line chart tasks require no parameters
    - Network graph tasks require 'source_field', 'target_field' for the nodes, 'edge_field' for the edge weight, and 'graph_type' to define the type of network graph (e.g., 'directed', 'undirected', 'weighted', 'clustered').
4. The x-axis field, y-axis field, and group field (if applicable) for the chart.

Example parameters:
    - bar chart: {"bar_mode": "group"}
    - pie chart: {}
    - line chart: {}
    - network graph: {"source_field": "source", "target_field": "target", "edge_field": "value", "graph_type": "directed"}

You will NEVER return a visualization task with empty parameters.

When generating the SQL queries, follow the instructions below:
- Remember to aggregate when possible to return only the necessary number of rows.
- Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
- Pay attention to use only the column names you can see in the table given below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
- If the question involves "today", remember to use the CURRENT_DATE function.
- Always include the "department" column in the query if relevant.
- Always use the alias "value" for the numerical value in the query if appropriate.
- Always use the alias "date" for the date column in the query if appropriate.
- Write the SQL query without formatting it in a code block.

Think step by step before writing the query plan.
"""

# Define Enums and BaseModel classes
class VisualizationType(Enum):
    BAR_CHART = "BAR_CHART"
    PIE_CHART = "PIE_CHART"
    LINE_CHART = "LINE_CHART"
    NETWORK_GRAPH = "NETWORK_GRAPH"

class VisualizationTask(BaseModel):
    query: str = Field(..., description="SQL query to fetch data for visualization")
    type: VisualizationType
    title: str = Field(..., description="Title of the visualization")
    parameters: dict = Field(..., description="Parameters for the visualization task, as a dictionary")
    x_field: Optional[str] = Field(None, description="Field for the x-axis")
    y_field: Optional[str] = Field(None, description="Field for the y-axis")
    group_field: Optional[str] = Field(None, description="Field for grouping data")

    def _execute_query(self):
        try:
            result = cur.execute(self.query).fetchall()
            cols = [desc[0] for desc in cur.description]
            data = [dict(zip(cols, row)) for row in result]
        except Exception as e:
            print(f"An error occurred: {e}")
            return []
        return data

    def run(self):
        print(f"Running task for {self.title}")
        data = self._execute_query()
        print(f"Data for {self.title}: {data}")
        if data:
            if self.type == VisualizationType.BAR_CHART:
                fig = get_bar_chart(data=data, title=self.title, x_field=self.x_field, y_field=self.y_field, group_field=self.group_field, barmode=self.parameters.get("bar_mode"))
                st.plotly_chart(fig)
            elif self.type == VisualizationType.PIE_CHART:
                fig = get_pie_chart(data=data, title=self.title, value_field=self.y_field, name_field=self.x_field)
                st.plotly_chart(fig)
            elif self.type == VisualizationType.LINE_CHART:
                fig = get_line_chart(data=data, title=self.title, x_field=self.x_field, y_field=self.y_field, group_field=self.group_field)
                st.plotly_chart(fig)
            elif self.type == VisualizationType.NETWORK_GRAPH:
                fig = get_network_graph(data=data, title=self.title, source_field=self.parameters.get("source_field"), target_field=self.parameters.get("target_field"), edge_field=self.parameters.get("edge_field"), graph_type=self.parameters.get("graph_type", "undirected"))
                st.plotly_chart(fig)

class VisualizationPlan(BaseModel):
    plan: List[VisualizationTask]

    def run(self):
        num_tasks = len(self.plan)
        num_rows = (num_tasks + 1) // 2
        for row in range(num_rows):
            st_cols = st.columns(2)
            for col in range(2):
                task_index = row * 2 + col
                if task_index < num_tasks:
                    with st_cols[col]:
                        self.plan[task_index].run()

# Template for LLM request prompt
request_prompt_template = Template(
    """
    Request: $input

    Use the following tables:
    $table_info
    """
)

# Function to generate visualization plan asynchronously
async def async_generate_visualization_plan(table_info, question):
    placeholder = st.empty()
    plan = await async_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": analysis_system_message},
            {
                "role": "user",
                "content": request_prompt_template.substitute(
                    input=question, table_info=table_info
                ),
            },
        ],
        stream=True,
        response_model=instructor.Partial[VisualizationPlan],
    )
    result = None
    async for obj in plan:
        placeholder.empty()
        placeholder.write(obj.model_dump())
        result = obj

    # Ensure parameters and fields are set correctly
    for task in result.plan:
        if task.parameters is None:
            task.parameters = {}
        if task.type == VisualizationType.PIE_CHART:
            task.x_field = "department"
            task.y_field = "value"
        if task.type == VisualizationType.NETWORK_GRAPH:
            task.x_field = "source"
            task.y_field = "target"
            if task.parameters == {}:
                task.parameters = {"source_field": "source", "target_field": "target", "edge_field": "value", "graph_type": "undirected"}

    placeholder.empty()
    return result

# Initialize session state
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

st.title("Text to Network Graph Visualizer 🌐📈")

# Functions to set user input
def set_user_input(question):
    st.session_state.user_input = question

def set_user_input_from_field():
    st.session_state.user_input = st.session_state.input_field_value

# Input field for user question
input_field = st.text_input("Enter a question", value=st.session_state.get("user_input"), key="input_field_value", on_change=set_user_input_from_field)

# Example questions for quick selection
example_questions = ["Connections between departments", "Interactions between employees", "Employee interactions by department", "Interactions by employee"]
button_cols = st.columns([1, 1, 1, 2, 2])

for i, question in enumerate(example_questions):
    with button_cols[i]:
        st.button(question, on_click=set_user_input, args=(question,))

# Generate visualization plan and run tasks
if len(st.session_state.user_input) > 0:
    user_input = st.session_state.user_input
    with st.spinner("Generating query plan..."):
        start = timer()
        visualization_plan = asyncio.run(async_generate_visualization_plan(get_table_info(conn), user_input))
        end = timer()
        st.info(f"Query plan generated in {round(end - start, 2)} seconds")
        print(visualization_plan.model_dump())
    st.write(visualization_plan.model_dump())
    visualization_plan.run()
