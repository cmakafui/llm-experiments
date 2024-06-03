import plotly.graph_objects as go
import networkx as nx

def extract_chart_data(data, x_field, y_field, group_field=None):
    grouped_data = {}
    if group_field:
        for entry in data:
            group = entry.get(group_field, None)
            x_value = entry.get(x_field, None)
            y_value = entry.get(y_field, 0)
            if group is not None:
                if group not in grouped_data:
                    grouped_data[group] = {"x": [], "y": []}
                grouped_data[group]["x"].append(x_value)
                grouped_data[group]["y"].append(y_value)
    else:
        x_values = [entry.get(x_field, None) for entry in data if entry.get(x_field, None) is not None]
        y_values = [entry.get(y_field, 0) for entry in data]
        return {"x": x_values, "y": y_values}
    
    return grouped_data

def get_bar_chart(data, title, x_field="department", y_field="value", group_field=None, barmode="group"):
    grouped_data = extract_chart_data(data, x_field, y_field, group_field)
    print(grouped_data)
    if group_field:
        traces = [
            go.Bar(name=group, x=values["x"], y=values["y"], offsetgroup=idx)
            for idx, (group, values) in enumerate(grouped_data.items())
        ]
    else:
        traces = [go.Bar(x=grouped_data["x"], y=grouped_data["y"])]

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode=barmode,
        title=title,
        xaxis_title=x_field.replace("_", " ").capitalize(),
        yaxis_title=y_field.replace("_", " ").capitalize(),
        legend_title=group_field.replace("_", " ").capitalize() if group_field else None,
    )
    return fig

def get_pie_chart(data, title, value_field="value", name_field="department"):
    chart_data = extract_chart_data(data, name_field, value_field)
    print(chart_data)
    
    fig = go.Figure(data=[go.Pie(labels=chart_data["x"], values=chart_data["y"], hole=0.4)])
    fig.update_layout(title_text=title)
    return fig

def get_line_chart(data, title, x_field="interaction_date", y_field="interaction_count", group_field="department"):
    grouped_data = extract_chart_data(data, x_field, y_field, group_field)
    print("Grouped Data:", grouped_data)
    
    if group_field:
        traces = [
            go.Scatter(name=group, x=values["x"], y=values["y"], mode='lines')
            for group, values in grouped_data.items()
        ]
    else:
        traces = [go.Scatter(x=grouped_data["x"], y=grouped_data["y"], mode='lines')]

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title,
        xaxis_title=x_field.replace("_", " ").capitalize(),
        yaxis_title=y_field.replace("_", " ").capitalize(),
        legend_title=group_field.replace("_", " ").capitalize() if group_field else None,
    )
    return fig

def get_network_graph(data, title, source_field, target_field, edge_field, graph_type='undirected'):
    G = nx.DiGraph() if graph_type == 'directed' else nx.Graph()

    node_pairs = set()  # To ensure unique node pairs

    for entry in data:
        source_node = entry[source_field]
        target_node = entry[target_field]
        edge_weight = entry.get(edge_field, 1)
        if (source_node, target_node) not in node_pairs and (target_node, source_node) not in node_pairs:
            G.add_edge(source_node, target_node, weight=edge_weight)
            node_pairs.add((source_node, target_node))

    pos = nx.spring_layout(G)
    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    node_text = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=node_text,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            color=[],
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            )
        )
    )

    node_adjacencies = []
    for node in G.nodes():
        node_adjacencies.append(len(list(G.neighbors(node))))
    
    node_trace.marker.color = node_adjacencies

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=title,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text="Network Graph",
                            showarrow=False,
                            xref="paper", yref="paper"
                        )],
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False)
                    ))
    return fig
