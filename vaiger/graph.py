import networkx as nx
from io import StringIO
from vaiger.wrapper import AigerWrapper


class AigerGraph:
    def __init__(self, aiger_dir=None):
        self.wrapper = AigerWrapper(aiger_dir)

    def load(self, aig_path, strip=False, integer_lits=False):
        dot_str = self.wrapper.to_dot(aig_path, strip=strip, integer_lits=integer_lits)
        return self._dot_to_networkx(dot_str)

    @staticmethod
    def _dot_to_networkx(dot_str):
        try:
            import pydot
        except ImportError:
            raise ImportError("pydot is required: pip install pydot")

        pydot_graphs = pydot.graph_from_dot_data(dot_str)
        if not pydot_graphs:
            raise ValueError("Failed to parse DOT output")
        pydot_graph = pydot_graphs[0]
        return nx.nx_pydot.from_pydot(pydot_graph)

    def analyze(self, aig_path, strip=False, integer_lits=False):
        G = self.load(aig_path, strip=strip, integer_lits=integer_lits)
        stats = {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "is_directed": G.is_directed(),
            "density": nx.density(G),
            "num_connected_components": nx.number_weakly_connected_components(G)
            if G.is_directed()
            else nx.number_connected_components(G.to_undirected()),
        }
        if G.number_of_nodes() > 0:
            degree_stats = dict(G.degree())
            stats["avg_degree"] = sum(degree_stats.values()) / len(degree_stats)
            stats["max_degree"] = max(degree_stats.values())
            stats["min_degree"] = min(degree_stats.values())
        return G, stats
