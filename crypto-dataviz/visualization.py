import plotly.graph_objects as go

def extract_chart_data(data, x_field, y_field, group_field=None):
    """
    Extracts and organizes data for chart plotting.

    Parameters:
    - data: List of dictionaries representing the data points.
    - x_field: The field to be used for x-axis values.
    - y_field: The field to be used for y-axis values.
    - group_field: Optional field for grouping data (used in bar charts).

    Returns:
    - If group_field is provided: Dictionary with groups as keys and (x, y) pairs as values.
    - If group_field is not provided: Tuple of (x_values, y_values).
    """
    grouped_data = {}
    if group_field:
        for entry in data:
            group = entry.get(group_field, "Unknown")
            x_value = entry.get(x_field, "Unknown")
            y_value = entry.get(y_field, 0)
            if group not in grouped_data:
                grouped_data[group] = {"x": [], "y": []}
            grouped_data[group]["x"].append(x_value)
            grouped_data[group]["y"].append(y_value)
        return grouped_data
    else:
        x_values = [entry.get(x_field, "Unknown") for entry in data]
        y_values = [entry.get(y_field, 0) for entry in data]
        return {"x": x_values, "y": y_values}

def get_bar_chart(data, title, x_field="date", y_field="value", group_field="symbol", barmode="group"):
    grouped_data = extract_chart_data(data, x_field, y_field, group_field)
    traces = [
        go.Bar(name=group, x=values["x"], y=values["y"], offsetgroup=idx)
        for idx, (group, values) in enumerate(grouped_data.items())
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode=barmode,
        title=title,
        xaxis_title=x_field.capitalize(),
        yaxis_title=y_field.capitalize(),
        legend_title=group_field.capitalize(),
    )
    return fig

def get_pie_chart(data, title, value_field="value", name_field="symbol"):
    chart_data = extract_chart_data(data, name_field, value_field)
    fig = go.Figure(data=[go.Pie(labels=chart_data["x"], values=chart_data["y"], hole=0.4)])
    fig.update_layout(title_text=title)
    return fig

def get_line_chart(data, title, x_field="date", y_field="value", group_field="symbol"):
    grouped_data = extract_chart_data(data, x_field, y_field, group_field)
    traces = [
        go.Scatter(name=group, x=values["x"], y=values["y"], mode='lines')
        for group, values in grouped_data.items()
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title,
        xaxis_title=x_field.capitalize(),
        yaxis_title=y_field.capitalize(),
        legend_title=group_field.capitalize(),
    )
    return fig
