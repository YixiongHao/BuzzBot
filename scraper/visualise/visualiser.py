import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import networkx as nx
import sqlite3

##########################
# Globals and Parameters #
##########################

DB_FILE = "./database/testcrawler.db"  # Path to your DB
pos_cache = {}                # Caches node positions keyed by DB file

##########################
# Helper Functions       #
##########################

def get_graph_from_db(db_file):
    """
    Reads the SQLite database and returns a DiGraph of the pages and links.
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

def update_positions(G, db_file, iterations=10):
    """
    Update or initialize the node positions for the given graph.

    - Reuses old positions from pos_cache if available,
      otherwise generates new positions from scratch.
    - This function returns the updated `pos` for the graph.
    """
    global pos_cache

    if db_file not in pos_cache:
        # If we have no positions for this DB yet, compute from scratch
        pos = nx.spring_layout(G, seed=42, iterations=iterations)
        pos_cache[db_file] = pos
    else:
        # Reuse existing positions
        old_pos = pos_cache[db_file]
        # Start from old_pos, run a few iterations to place new nodes
        pos = nx.spring_layout(G, pos=old_pos, iterations=iterations)
        pos_cache[db_file] = pos

    return pos_cache[db_file]

def build_figure(G, pos):
    """
    Build a Plotly figure (node+edge traces) given the graph and positions.
    """
    # Edge lines
    edge_x, edge_y = [], []
    for source, target in G.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Nodes
    node_x, node_y, node_text, node_color = [], [], [], []
    for node, coords in pos.items():
        node_x.append(coords[0])
        node_y.append(coords[1])
        node_text.append(node)
        node_color.append(G.degree(node))  # color by degree

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='RdBu_r',
            size=10,
            color=node_color,
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
# Top-level style: 100% viewport with flex layout
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
        # Header row (fixed height or auto)
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
            interval=10*1000,  # 5 seconds
            n_intervals=0
        )
    ]
)

@app.callback(
    Output('live-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph_live(n):
    if not n:
        raise dash.exceptions.PreventUpdate
    # 1) Get the current graph from DB
    G = get_graph_from_db(DB_FILE)


    # 2) Update or reuse the layout positions
    pos = update_positions(G, DB_FILE, iterations=10)
    # 3) Build the Plotly figure
    fig = build_figure(G, pos)
    return fig

if __name__ == '__main__':
    # Run the Dash app
    app.run_server(debug=True)
