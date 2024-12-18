import networkx as nx
import matplotlib.pyplot as plt
import random
import math


def create_internet_simulation_graph(num_nodes=100, num_edges=300):
    """
    Creates a directed graph representing a simulated internet for practicing PageRank.

    Args:
        num_nodes (int): Number of nodes in the graph.
        num_edges (int): Number of edges in the graph.

    Returns:
        G (networkx.DiGraph): A directed graph representing the simulated internet.
    """
    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes
    G.add_nodes_from(range(num_nodes))

    # Add edges
    for _ in range(num_edges):
        while True:
            source = random.randint(0, num_nodes - 1)
            target = random.randint(0, num_nodes - 1)
            if source != target and not G.has_edge(source, target):
                G.add_edge(source, target)
                break

    return G


def plot_internet_graph(G):
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color='skyblue', alpha=0.8)

    nx.draw_networkx_edges(
        G, pos, edge_color='gray', arrows=True, arrowsize=10, connectionstyle='arc3,rad=0.2'
    )


    nx.draw_networkx_labels(G, pos, font_size=8, font_color='black')
    plt.title("Simulated Internet Graph")
    plt.axis("off")
    plt.show()


class MCTSCrawler:
    def __init__(self, G, max_depth=3, exploration_weight=1.41):
        """
        Initialize the MCTS Crawler.
        
        Args:
            G (networkx.DiGraph): The graph to traverse.
            max_depth (int): Maximum depth for simulations.
            exploration_weight (float): Weight for exploration in UCT.
        """
        self.G = G
        self.max_depth = max_depth
        self.exploration_weight = exploration_weight
        self.visits = {}
        self.scores = {}

    def uct(self, node):
        """
        Calculate the Upper Confidence Bound for Trees (UCT) score for a node.
        """
        if self.visits.get(node, 0) == 0:
            return float('inf')  # Explore unvisited nodes
        exploitation = self.scores.get(node, 0) / self.visits[node]
        exploration = self.exploration_weight * math.sqrt(
            math.log(sum(self.visits.values())) / self.visits[node]
        )
        return exploitation + exploration

    def select(self, node):
        """
        Select the best child node using UCT.
        """
        neighbors = list(self.G.neighbors(node))
        if not neighbors:
            return None  # Dead-end
        return max(neighbors, key=self.uct)

    def simulate(self, node):
        """
        Perform a random walk to estimate the reward of a node.
        """
        current_node = node
        depth = 0
        reward = 0
        while depth < self.max_depth and current_node is not None:
            reward += 1  # Increment reward for reaching this node
            neighbors = list(self.G.neighbors(current_node))
            current_node = random.choice(neighbors) if neighbors else None
            depth += 1
        return reward

    def backpropagate(self, path, reward):
        """
        Update the scores and visits of nodes along the path.
        """
        for node in path:
            self.visits[node] = self.visits.get(node, 0) + 1
            self.scores[node] = self.scores.get(node, 0) + reward

    def crawl(self, start_node, iterations=3):
        """
        Perform the MCTS-based crawl starting from a given node.
        
        Args:
            start_node (int): The starting node for the crawl.
            iterations (int): Number of MCTS iterations to perform.
        
        Returns:
            visited_order (list): List of visited nodes in priority order.
        """
        visited_order = []
        for _ in range(iterations):
            # Phase 1: Selection
            node = start_node
            path = [node]
            while True:
                next_node = self.select(node)
                if next_node is None or next_node in path:
                    break
                path.append(next_node)
                node = next_node
            
            # Phase 2: Expansion
            neighbors = list(self.G.neighbors(node))
            if neighbors:
                new_node = random.choice(neighbors)
                path.append(new_node)
            
            # Phase 3: Simulation
            reward = self.simulate(path[-1])
            
            # Phase 4: Backpropagation
            self.backpropagate(path, reward)

        # Sort nodes by their importance scores
        visited_order = sorted(self.scores, key=self.scores.get, reverse=True)
        return visited_order


# Create the graph
simulated_internet = create_internet_simulation_graph(num_nodes=2000, num_edges=5000)

plot_internet_graph(simulated_internet)
crawler = MCTSCrawler(simulated_internet, max_depth=10, exploration_weight=1.41)
visited_order = crawler.crawl(start_node=0, iterations=200)

print("Visited nodes in priority order:", visited_order)