import base64
import io
import json

import dash
import networkx as nx
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from networkx.drawing.nx_agraph import graphviz_layout

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.H1("ICD-10 versions", style={"textAlign": "center"}),
        dcc.Upload(
            id="upload-gml",
            children=html.Div(["Drag and Drop or ", html.A("Select a GML File")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=False,
        ),
        html.Div(id="error-message", style={"color": "red", "margin": "10px"}),
        dcc.Graph(
            id="tree-graph", style={"height": "80vh"}, config={"displayModeBar": True}
        ),
        dcc.Store(id="graph-data"),
        dcc.Store(id="expanded-nodes", data=json.dumps([])),
    ]
)


def parse_gml(contents):
    """Parse GML file content and return a NetworkX graph."""
    if contents is None:
        return None, None

    try:
        _, content_string = contents.split(",")
        decoded = io.BytesIO(base64.b64decode(content_string))
        G = nx.read_gml(decoded)

        return G, None
    except Exception as e:
        error_msg = f"Error parsing GML file: {str(e)}"
        print(error_msg)  # Keep console logging for debugging
        return None, error_msg


def get_root_node(G):
    """Find the root node of the tree."""
    for node in G.nodes():
        if G.in_degree(node) == 0:
            return node
    return None


def get_visible_nodes(G, expanded_nodes):
    """Get the set of visible nodes based on expanded state."""
    visible_nodes = set()
    root = get_root_node(G)
    if root:
        # Always include root and its immediate children
        visible_nodes.add(root)
        visible_nodes.update(G.successors(root))

        # Add expanded nodes and their children
        for node in expanded_nodes:
            visible_nodes.add(node)
            visible_nodes.update(G.successors(node))

    return visible_nodes


def create_tree_visualization(G, expanded_nodes=None):
    """Create an interactive tree visualization using Plotly."""
    if G is None:
        return go.Figure()

    if expanded_nodes is None:
        expanded_nodes = []

    visible_nodes = get_visible_nodes(G, expanded_nodes)

    # Create a subgraph with only visible nodes
    visible_edges = [
        (u, v) for u, v in G.edges() if u in visible_nodes and v in visible_nodes
    ]
    subgraph = G.edge_subgraph(visible_edges)

    pos = graphviz_layout(subgraph, prog="dot")

    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in subgraph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_names = []
    node_colors = []

    for node in subgraph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # Create hover text with node attributes
        hover_text = f"Node: {node}<br>"
        for attr, value in G.nodes[node].items():
            hover_text += f"{attr}: {value}<br>"
        node_text.append(hover_text)
        node_names.append(str(node))

        # Color nodes based on whether they have children
        has_children = len(list(G.successors(node))) > 0
        node_colors.append(1 if has_children else 0)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=node_names,
        textposition="top center",
        hovertext=node_text,
        marker=dict(
            showscale=True,
            colorscale="YlGnBu",
            size=10,
            color=node_colors,
            colorbar=dict(thickness=15, title="Has Children", xanchor="left"),
        ),
    )

    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    return fig


@callback(
    [
        Output("graph-data", "data"),
        Output("tree-graph", "figure"),
        Output("error-message", "children"),
    ],
    [Input("upload-gml", "contents")],
    [State("upload-gml", "filename")],
)
def update_graph(contents, filename):
    """Update the graph visualization when a new file is uploaded."""
    if contents is None:
        return None, go.Figure(), None

    G, error = parse_gml(contents)
    if G is None:
        return None, go.Figure(), error

    graph_data = nx.node_link_data(G)
    fig = create_tree_visualization(G)

    return graph_data, fig, None


@callback(
    Output("tree-graph", "figure", allow_duplicate=True),
    Output("expanded-nodes", "data"),
    [Input("tree-graph", "clickData")],
    [State("graph-data", "data"), State("expanded-nodes", "data")],
    prevent_initial_call=True,
)
def handle_node_click(clickData, graph_data, expanded_nodes_json):
    """Handle node clicks to expand/collapse the tree."""
    if not clickData or not graph_data:
        return dash.no_update, dash.no_update

    # Get the clicked node from the text field
    clicked_node = clickData["points"][0]["text"]
    expanded_nodes = json.loads(expanded_nodes_json)

    if clicked_node in expanded_nodes:
        # Collapse node by removing it and its descendants
        G = nx.node_link_graph(graph_data)
        descendants = set()
        for node in expanded_nodes:
            if nx.has_path(G, clicked_node, node):
                descendants.add(node)
        expanded_nodes = [n for n in expanded_nodes if n not in descendants]
    else:
        # Expand node
        expanded_nodes.append(clicked_node)

    fig = create_tree_visualization(nx.node_link_graph(graph_data), expanded_nodes)
    return fig, json.dumps(expanded_nodes)


if __name__ == "__main__":
    app.run(debug=True)
