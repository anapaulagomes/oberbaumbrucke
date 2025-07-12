import base64
import io
import json

import dash
import networkx as nx
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
from networkx.drawing.nx_agraph import graphviz_layout

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Create the navigation header
header = html.Div(
    [
        html.Div(
            [
                html.H2("ICD-10 Explorer", style={"margin": "0"}),
                html.Div(
                    [
                        dcc.Link("Tree View", href="/", style={"marginRight": "20px"}),
                        dcc.Link(
                            "Compare Graphs",
                            href="/compare",
                            style={"marginRight": "20px"},
                        ),
                    ],
                    style={"marginTop": "10px"},
                ),
            ],
            style={
                "backgroundColor": "#f8f9fa",
                "padding": "20px",
                "borderBottom": "1px solid #dee2e6",
            },
        ),
    ]
)

# Tree View Layout
tree_view_layout = html.Div(
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
        html.Div(id="tree-graph-container"),
        dcc.Store(id="graph-data"),
        dcc.Store(id="expanded-nodes", data=json.dumps([])),
    ]
)

# Comparison Layout
comparison_layout = html.Div(
    [
        html.H1("ICD-10 Comparison", style={"textAlign": "center"}),
        # Search bar
        html.Div(
            [
                dcc.Input(
                    id="search-input",
                    type="text",
                    placeholder="Search for a node...",
                    style={"width": "300px", "margin": "10px", "padding": "5px"},
                ),
                html.Button(
                    "Search",
                    id="search-button",
                    style={"margin": "10px", "padding": "5px 15px"},
                ),
            ],
            style={"textAlign": "center", "marginBottom": "20px"},
        ),
        # Error message
        html.Div(
            id="error-message",
            style={"color": "red", "margin": "10px", "textAlign": "center"},
        ),
        # Top row of graphs
        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                            id="graph-1-title",
                            children="Graph 1",
                            style={"textAlign": "center"},
                        ),
                        dcc.Store(id="filename-1"),
                        dcc.Upload(
                            id="upload-gml-1",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Graph 1")]
                            ),
                            style={
                                "width": "90%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px auto",
                                "backgroundColor": "#f8f9fa",
                            },
                        ),
                        dcc.Graph(id="graph-1", style={"height": "40vh"}),
                        dcc.Store(id="graph-data-1"),
                        dcc.Store(id="expanded-nodes-1", data=json.dumps([])),
                    ],
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                    },
                ),
                html.Div(
                    [
                        html.H3(
                            id="graph-2-title",
                            children="Graph 2",
                            style={"textAlign": "center"},
                        ),
                        dcc.Store(id="filename-2"),
                        dcc.Upload(
                            id="upload-gml-2",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Graph 2")]
                            ),
                            style={
                                "width": "90%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px auto",
                                "backgroundColor": "#f8f9fa",
                            },
                        ),
                        dcc.Graph(id="graph-2", style={"height": "40vh"}),
                        dcc.Store(id="graph-data-2"),
                        dcc.Store(id="expanded-nodes-2", data=json.dumps([])),
                    ],
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                    },
                ),
            ],
            style={"width": "100%", "marginBottom": "20px"},
        ),
        # Bottom row of graphs
        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                            id="graph-3-title",
                            children="Graph 3",
                            style={"textAlign": "center"},
                        ),
                        dcc.Store(id="filename-3"),
                        dcc.Upload(
                            id="upload-gml-3",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Graph 3")]
                            ),
                            style={
                                "width": "90%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px auto",
                                "backgroundColor": "#f8f9fa",
                            },
                        ),
                        dcc.Graph(id="graph-3", style={"height": "40vh"}),
                        dcc.Store(id="graph-data-3"),
                        dcc.Store(id="expanded-nodes-3", data=json.dumps([])),
                    ],
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                    },
                ),
                html.Div(
                    [
                        html.H3(
                            id="graph-4-title",
                            children="Graph 4",
                            style={"textAlign": "center"},
                        ),
                        dcc.Store(id="filename-4"),
                        dcc.Upload(
                            id="upload-gml-4",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Graph 4")]
                            ),
                            style={
                                "width": "90%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px auto",
                                "backgroundColor": "#f8f9fa",
                            },
                        ),
                        dcc.Graph(id="graph-4", style={"height": "40vh"}),
                        dcc.Store(id="graph-data-4"),
                        dcc.Store(id="expanded-nodes-4", data=json.dumps([])),
                    ],
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                    },
                ),
            ],
            style={"width": "100%"},
        ),
    ],
    style={"padding": "20px", "width": "100%"},
)

# Main app layout with routing
app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), header, html.Div(id="page-content")]
)


# Callback for page routing
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/compare":
        return comparison_layout
    else:
        return tree_view_layout


def parse_gml(contents):
    """Parse GML file content and return a NetworkX graph."""
    if contents is None:
        return None, None

    try:
        # Split the content string to get the base64 encoded data
        content_type, content_string = contents.split(",")

        # Decode the base64 string
        decoded = base64.b64decode(content_string)

        # Create a file-like object from the decoded data
        file_obj = io.BytesIO(decoded)

        # Read the GML file
        G = nx.read_gml(file_obj)

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


def create_tree_visualization(
    G, expanded_nodes=None, highlight_node=None, filename=None
):
    """Create an interactive tree visualization using Plotly."""
    if G is None:
        return go.Figure()

    if expanded_nodes is None:
        expanded_nodes = []

    visible_nodes = get_visible_nodes(G, expanded_nodes)

    # Identify root node
    root = get_root_node(G)

    # Create a subgraph with only visible nodes
    visible_edges = [
        (u, v) for u, v in G.edges() if u in visible_nodes and v in visible_nodes
    ]
    subgraph = G.edge_subgraph(visible_edges)

    pos = graphviz_layout(subgraph, prog="dot")

    # After pos is computed and before creating the figure
    x_vals = [p[0] for p in pos.values()]
    y_vals = [p[1] for p in pos.values()]
    x_range = [min(x_vals) - 50, max(x_vals) + 50]
    y_range = [min(y_vals) - 50, max(y_vals) + 50]

    # --- EDGE STYLING ---
    edge_x_solid = []
    edge_y_solid = []
    edge_x_dashed = []
    edge_y_dashed = []
    edge_width_solid = []
    edge_width_dashed = []
    for u, v in subgraph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        overlap_u = G.nodes[u].get("overlap", None)
        overlap_v = G.nodes[v].get("overlap", None)
        # Edge is dashed if either node has overlap==None (i.e., missing overlap info)
        # But if root is involved, always solid and thin
        if (root is not None) and (u == root or v == root):
            edge_x_solid.extend([x0, x1, None])
            edge_y_solid.extend([y0, y1, None])
            edge_width_solid.append(1)
        elif overlap_u is None or overlap_v is None:
            edge_x_dashed.extend([x0, x1, None])
            edge_y_dashed.extend([y0, y1, None])
            edge_width_dashed.append(2.5)
        elif (overlap_u and not overlap_v) or (not overlap_u and overlap_v):
            edge_x_dashed.extend([x0, x1, None])
            edge_y_dashed.extend([y0, y1, None])
            edge_width_dashed.append(2.5)
        else:
            edge_x_solid.extend([x0, x1, None])
            edge_y_solid.extend([y0, y1, None])
            edge_width_solid.append(1)

    edge_traces = []
    # For solid edges, Plotly only supports one width per trace, so we use the max width (should be 1)
    if edge_x_solid:
        edge_traces.append(
            go.Scatter(
                x=edge_x_solid,
                y=edge_y_solid,
                line=dict(width=2.5, color="#888", dash="solid"),
                hoverinfo="none",
                mode="lines",
                showlegend=False,
            )
        )
    if edge_x_dashed:
        edge_traces.append(
            go.Scatter(
                x=edge_x_dashed,
                y=edge_y_dashed,
                line=dict(width=1, color="#888", dash="dash"),
                hoverinfo="none",
                mode="lines",
                showlegend=False,
            )
        )

    # --- NODE COLORING ---
    def get_filename_color(filename):
        if not filename:
            return "#636EFA"  # fallback blue
        fname = filename.lower()
        if "icd-10-cm" in fname:
            return "#EF553B"  # red
        elif "cid-10-bra-2008" in fname:
            return "#00FF00"  # green
        elif "icd-10-gm" in fname:
            return "#FFD700"  # gold
        elif "icd-10-who" in fname:
            return "#87CEFA"  # lightblue
        return "#636EFA"  # fallback blue

    node_x = []
    node_y = []
    node_text = []
    node_names = []
    node_colors = []
    node_sizes = []
    for node in subgraph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        hover_text = f"Node: {node}<br>"
        for attr, value in G.nodes[node].items():
            hover_text += f"{attr}: {value}<br>"
        node_text.append(hover_text)
        node_names.append(str(node))
        overlap = G.nodes[node].get("overlap", None)
        if node == root:
            node_colors.append("#333333")  # dark grey for root
            node_sizes.append(10)
        elif overlap is not None:
            node_colors.append("#000000")  # black for overlap
            node_sizes.append(18)
        else:
            node_colors.append(get_filename_color(filename))
            node_sizes.append(12)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=node_names,
        textposition="top center",
        hovertext=node_text,
        customdata=node_names,  # ensure node name is available in clickData
        marker=dict(
            size=node_sizes,  # list of sizes
            color=node_colors,  # list of hex color strings
            line_width=2,
        ),
    )

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=40, l=5, r=5, t=40),
            xaxis=dict(
                showgrid=False, zeroline=False, showticklabels=False, range=x_range
            ),
            yaxis=dict(
                showgrid=False, zeroline=False, showticklabels=False, range=y_range
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# Callback for single graph upload
@app.callback(
    [
        Output("graph-data", "data"),
        Output("tree-graph-container", "children"),
        Output("error-message", "children"),
    ],
    [Input("upload-gml", "contents")],
    [State("upload-gml", "filename")],
)
def update_single_graph(contents, filename):
    """Update the single graph visualization when a new file is uploaded."""
    if contents is None:
        return None, None, None

    G, error = parse_gml(contents)
    if G is None:
        return None, None, error

    graph_data = nx.node_link_data(G)
    fig = create_tree_visualization(G, filename=filename)
    graph_component = dcc.Graph(
        id="tree-graph",
        figure=fig,
        style={"height": "120vh"},
        config={"displayModeBar": True},
    )
    return graph_data, graph_component, None


# Callback for multiple graph uploads
@app.callback(
    [
        Output("graph-data-1", "data"),
        Output("graph-1", "figure"),
        Output("filename-1", "data"),
        Output("graph-data-2", "data"),
        Output("graph-2", "figure"),
        Output("filename-2", "data"),
        Output("graph-data-3", "data"),
        Output("graph-3", "figure"),
        Output("filename-3", "data"),
        Output("graph-data-4", "data"),
        Output("graph-4", "figure"),
        Output("filename-4", "data"),
        Output("error-message", "children", allow_duplicate=True),
    ],
    [
        Input("upload-gml-1", "contents"),
        Input("upload-gml-2", "contents"),
        Input("upload-gml-3", "contents"),
        Input("upload-gml-4", "contents"),
    ],
    [
        State("upload-gml-1", "filename"),
        State("upload-gml-2", "filename"),
        State("upload-gml-3", "filename"),
        State("upload-gml-4", "filename"),
    ],
    prevent_initial_call=True,
)
def update_multiple_graphs(
    content1, content2, content3, content4, filename1, filename2, filename3, filename4
):
    """Update multiple graph visualizations when files are uploaded."""
    contents = [content1, content2, content3, content4]
    filenames = [filename1, filename2, filename3, filename4]
    outputs = [None] * 12  # 4x (data, fig, filename)
    error = None
    for i, (content, filename) in enumerate(zip(contents, filenames)):
        if content is not None:
            G, error = parse_gml(content)
            if G is not None:
                graph_data = nx.node_link_data(G)
                fig = create_tree_visualization(G, filename=filename)
                fig.update_layout(title=filename)
                outputs[i * 3] = graph_data
                outputs[i * 3 + 1] = fig
                outputs[i * 3 + 2] = filename
            else:
                return [None] * 12 + [error]
    return outputs + [error]


# Callback for single graph node clicks
@app.callback(
    Output("tree-graph", "figure", allow_duplicate=True),
    Output("expanded-nodes", "data"),
    [Input("tree-graph", "clickData")],
    [
        State("graph-data", "data"),
        State("expanded-nodes", "data"),
        State("upload-gml", "filename"),
    ],
    prevent_initial_call=True,
)
def handle_node_click(clickData, graph_data, expanded_nodes_json, filename):
    """Handle node clicks to expand/collapse the tree."""
    if not clickData or not graph_data:
        return dash.no_update, dash.no_update

    point = clickData["points"][0]
    clicked_node = point.get("customdata")
    if clicked_node is None:
        # print('Available keys in point:', list(point.keys()))
        return dash.no_update, dash.no_update

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
        expanded_nodes.append(clicked_node)

    fig = create_tree_visualization(
        nx.node_link_graph(graph_data), expanded_nodes, filename=filename
    )
    return fig, json.dumps(expanded_nodes)


# Callback for multiple graph node clicks
@app.callback(
    [
        Output("graph-1", "figure", allow_duplicate=True),
        Output("expanded-nodes-1", "data"),
        Output("graph-2", "figure", allow_duplicate=True),
        Output("expanded-nodes-2", "data"),
        Output("graph-3", "figure", allow_duplicate=True),
        Output("expanded-nodes-3", "data"),
        Output("graph-4", "figure", allow_duplicate=True),
        Output("expanded-nodes-4", "data"),
    ],
    [
        Input("graph-1", "clickData"),
        Input("graph-2", "clickData"),
        Input("graph-3", "clickData"),
        Input("graph-4", "clickData"),
    ],
    [
        State("graph-data-1", "data"),
        State("expanded-nodes-1", "data"),
        State("graph-data-2", "data"),
        State("expanded-nodes-2", "data"),
        State("graph-data-3", "data"),
        State("expanded-nodes-3", "data"),
        State("graph-data-4", "data"),
        State("expanded-nodes-4", "data"),
    ],
    prevent_initial_call=True,
)
def handle_node_clicks(
    click1,
    click2,
    click3,
    click4,
    data1,
    nodes1,
    data2,
    nodes2,
    data3,
    nodes3,
    data4,
    nodes4,
):
    clicks = [click1, click2, click3, click4]
    datas = [data1, data2, data3, data4]
    nodes = [nodes1, nodes2, nodes3, nodes4]

    outputs = []
    for click, data, nodes_json in zip(clicks, datas, nodes):
        if click and data:
            clicked_node = click["points"][0]["text"]
            expanded_nodes = json.loads(nodes_json)

            if clicked_node in expanded_nodes:
                G = nx.node_link_graph(data)
                descendants = set()
                for node in expanded_nodes:
                    if nx.has_path(G, clicked_node, node):
                        descendants.add(node)
                expanded_nodes = [n for n in expanded_nodes if n not in descendants]
            else:
                expanded_nodes.append(clicked_node)

            fig = create_tree_visualization(nx.node_link_graph(data), expanded_nodes)
            outputs.extend([fig, json.dumps(expanded_nodes)])
        else:
            outputs.extend([dash.no_update, dash.no_update])

    return outputs


# Callback for search
@app.callback(
    [
        Output("graph-1", "figure", allow_duplicate=True),
        Output("graph-2", "figure", allow_duplicate=True),
        Output("graph-3", "figure", allow_duplicate=True),
        Output("graph-4", "figure", allow_duplicate=True),
    ],
    [Input("search-button", "n_clicks")],
    [
        State("search-input", "value"),
        State("graph-data-1", "data"),
        State("graph-data-2", "data"),
        State("graph-data-3", "data"),
        State("graph-data-4", "data"),
    ],
    prevent_initial_call=True,
)
def handle_search(n_clicks, search_value, data1, data2, data3, data4):
    if not search_value:
        return [dash.no_update] * 4

    outputs = []
    for data in [data1, data2, data3, data4]:
        if data:
            G = nx.node_link_graph(data)
            fig = create_tree_visualization(G, highlight_node=search_value)
            outputs.append(fig)
        else:
            outputs.append(dash.no_update)

    return outputs


# Add callbacks to update the graph titles
for i in range(1, 5):

    @app.callback(
        Output(f"graph-{i}-title", "children"),
        Input(f"filename-{i}", "data"),
    )
    def update_graph_title(filename, i=i):
        return filename if filename else f"Graph {i}"


if __name__ == "__main__":
    app.run(debug=True)
