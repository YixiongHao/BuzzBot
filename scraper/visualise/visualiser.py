import sqlite3
import networkx as nx
import plotly.graph_objects as go

def visualise(db_file):
    # Connect to the database
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

    # Node positions
    pos = nx.spring_layout(G)

    # Node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []

    for node, coords in pos.items():
        node_x.append(coords[0])
        node_y.append(coords[1])
        node_text.append(node)
        node_color.append(G.degree(node))

    # Edge traces
    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
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

    # Build the figure
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
    
    # Show the figure
    fig.show()

if __name__ == "__main__":
    visualise("./testcrawler.db")