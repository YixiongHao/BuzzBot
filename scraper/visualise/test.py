import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import networkx as nx
import sqlite3

##########################
# Globals and Parameters #
##########################

DB_FILE = "./database/ccdepth5nohcc.db"  # Path to your SQLite database
pos_cache = {}  # Cache for node positions keyed by database file

##########################
# Helper Functions       #
##########################

def get_graph_from_db(db_file):
    """
    Reads the SQLite database and returns a directed graph of pages and links.
    """
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode = wal;")
    conn.execute("PRAGMA synchronous = NORMAL;")

    G = nx.DiGraph()
    cur = conn.cursor()

    # Fetch pages
    cur.execute("SELECT id, url FROM pages")
    pages = {row[0]: row[1] for row in cur.fetchall()}

    # Fetch links
    cur.execute("SELECT parent_id, child_id FROM links")
    links = cur.fetchall()

    # Add edges to the graph
    for parent_id, child_id in links:
        parent_url = pages.get(parent_id)
        child_url = pages.get(child_id)
        if parent_url and child_url:
            G.add_edge(parent_url, child_url)

    conn.close()
    return G

def get_positions(G, db_file):
    """
    Retrieve cached positions or generate new ones if they don't exist.
    """
    global pos_cache

    if db_file not in pos_cache:
        pos_cache[db_file] = nx.spring_layout(G, seed=42, iterations=50)

    return pos_cache[db_file]

def build_figure(G, pos, highlighted_nodes=None, highlighted_edges=None):
    """
    Build a Plotly figure (node+edge traces) given the graph, positions, and highlighting.
    """
    highlighted_nodes = highlighted_nodes or []
    highlighted_edges = highlighted_edges or []

    # Edge lines
    edge_x, edge_y, edge_color = [], [], []
    for source, target in G.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_color.append('#ff7f0e' if (source, target) in highlighted_edges else '#888')

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color='#888'),  # All edges get the same color trace
        hoverinfo='none',
        mode='lines'
    )

    # Nodes
    node_x, node_y, node_text, node_color = [], [], [], []
    for node, coords in pos.items():
        node_x.append(coords[0])
        node_y.append(coords[1])
        node_text.append(node)
        if node in highlighted_nodes:
            node_color.append('#ff7f0e')  # Highlighted nodes are orange
        else:
            node_color.append(G.degree(node))  # Other nodes are colored by degree

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='RdBu_r',
            size=10,
            color=node_color,  # Node coloring based on degree or highlight
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
        ),
        text=node_text
    )

    # Construct final figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title='Webpage Network',
            titlefont=dict(size=16),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)
        )
    )
    
    return fig

##########################
# Dash App Setup         #
##########################

app = dash.Dash(__name__)
app.layout = html.Div(
    style={
        'width': '100vw',
        'height': '100vh',
        'margin': '0',
        'padding': '0',
        'overflow': 'hidden',
        'display': 'flex',
        'flexDirection': 'column'
    },
    children=[
        # Header row
        html.Div([
            html.H3("Live Webpage Network")
        ], style={'flex': '0 0 auto', 'padding': '10px'}),

        # Graph takes remaining space
        html.Div([
            dcc.Graph(
                id='live-graph',
                style={
                    'width': '100%',
                    'height': '100%'
                }
            )
        ], style={'flex': '1 1 auto'}),

        dcc.Interval(
            id='interval-component',
            interval=60 * 1000,  # 10 seconds
            n_intervals=0
        )
    ]
)

@app.callback(
    Output('live-graph', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('live-graph', 'clickData')],
)
def update_graph_live(n, clickData):
    # 1) Get the current graph from DB
    G = get_graph_from_db(DB_FILE)

    # 2) Retrieve node positions (cached)
    pos = get_positions(G, DB_FILE)

    # 3) Determine highlighted nodes and edges
    highlighted_nodes = []
    highlighted_edges = []
    if clickData and 'points' in clickData:
        clicked_node = clickData['points'][0]['text']
        highlighted_nodes = [clicked_node] + list(G.neighbors(clicked_node))
        highlighted_edges = [(clicked_node, neighbor) for neighbor in G.neighbors(clicked_node)]

    # 4) Build the Plotly figure with highlights
    fig = build_figure(G, pos, highlighted_nodes, highlighted_edges)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
