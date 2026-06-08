import copy
import os
from pathlib import Path

import networkx as nx

try:
    import pydot
except ImportError:
    pydot = None

try:
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from vaiger.wrapper import AigerWrapper
from vaiger.graph import AigerGraph


DEFAULT_STYLE = {
    "and_fillcolor": "#FF6B6B",
    "and_fontcolor": "#1D3557",
    "and_shape": "circle",
    "input_fillcolor": "#A8DADC",
    "input_fontcolor": "#1D3557",
    "input_shape": "box",
    "latch_fillcolor": "#F4A261",
    "latch_fontcolor": "#1D3557",
    "latch_shape": "box",
    "constant_fillcolor": "#E63946",
    "constant_fontcolor": "#FFFFFF",
    "constant_shape": "box3d",
    "label_input_color": "#457B9D",
    "label_output_color": "#2A9D8F",
    "label_bad_color": "#E63946",
    "label_constraint_color": "#2D6A4F",
    "label_latch_color": "#F4A261",
    "complemented_edge_color": "#E63946",
    "complemented_arrowhead": "odot",
    "normal_edge_color": "#457B9D",
    "normal_arrowhead": "none",
    "latch_edge_color": "#F4A261",
    "bg_color": "#FFFFFF",
    "font_name": "Helvetica",
    "dpi": 150,
    "rankdir": "TB",
}


def _classify_node(node_id, attrs):
    if isinstance(node_id, str):
        if node_id.startswith("I") and attrs.get("shape") == "triangle":
            return "label_input"
        if node_id.startswith("O") and attrs.get("shape") == "triangle":
            return "label_output"
        if node_id.startswith("B") and attrs.get("shape") == "triangle":
            return "label_bad"
        if node_id.startswith("C") and attrs.get("shape") == "triangle":
            return "label_constraint"
        if node_id.startswith("L") and attrs.get("shape") == "diamond":
            return "label_latch"
    if attrs.get("shape") == "box":
        if attrs.get("color") == "magenta":
            return "latch"
        return "input"
    if node_id == "0":
        return "constant"
    if not attrs or (not attrs.get("shape") and not attrs.get("color")):
        return "and"
    return "other"


def _classify_edge(attrs):
    if attrs.get("style") == "dashed":
        return "latch_feedback"
    if attrs.get("arrowhead") == "dot":
        return "complemented"
    return "normal"


def _clean_graph(G):
    H = nx.DiGraph()
    for node, data in G.nodes(data=True):
        clean = {k: v for k, v in data.items() if v is not None}
        H.add_node(node, **clean)
    for u, v, data in G.edges(data=True):
        clean = {k: v for k, v in data.items() if v is not None}
        H.add_edge(u, v, **clean)
    return H


class AigerVisualizer:
    def __init__(self, aiger_dir=None, **style_overrides):
        self.wrapper = AigerWrapper(aiger_dir)
        self.style = {**DEFAULT_STYLE, **style_overrides}

    def _get_raw_dot(self, aig_path, strip=False, integer_lits=False):
        return self.wrapper.to_dot(aig_path, strip=strip, integer_lits=integer_lits)

    def _get_raw_graph(self, aig_path, strip=False, integer_lits=False):
        dot_str = self._get_raw_dot(aig_path, strip, integer_lits)
        return AigerGraph._dot_to_networkx(dot_str)

    def get_styled_graph(self, aig_path, strip=False, integer_lits=False):
        G = self._get_raw_graph(aig_path, strip, integer_lits)
        return self._apply_styles(G)

    def _apply_styles(self, G):
        G = _clean_graph(G)
        s = self.style

        for node, data in G.nodes(data=True):
            ntype = _classify_node(node, dict(data))
            if ntype == "and":
                data["fillcolor"] = s["and_fillcolor"]
                data["fontcolor"] = s["and_fontcolor"]
                data["shape"] = s["and_shape"]
                data["style"] = "filled"
                data["fontname"] = s["font_name"]
            elif ntype == "input":
                data["fillcolor"] = s["input_fillcolor"]
                data["fontcolor"] = s["input_fontcolor"]
                data["shape"] = s["input_shape"]
                data["style"] = "filled"
                data["fontname"] = s["font_name"]
            elif ntype == "latch":
                data["fillcolor"] = s["latch_fillcolor"]
                data["fontcolor"] = s["latch_fontcolor"]
                data["shape"] = s["latch_shape"]
                data["style"] = "filled"
                data["fontname"] = s["font_name"]
            elif ntype == "constant":
                data["fillcolor"] = s["constant_fillcolor"]
                data["fontcolor"] = s["constant_fontcolor"]
                data["shape"] = s["constant_shape"]
                data["style"] = "filled"
                data["fontname"] = s["font_name"]
            elif ntype == "label_input":
                data["color"] = s["label_input_color"]
                data["fontcolor"] = s["label_input_color"]
                data["fontname"] = s["font_name"]
            elif ntype == "label_output":
                data["color"] = s["label_output_color"]
                data["fontcolor"] = s["label_output_color"]
                data["fontname"] = s["font_name"]
            elif ntype == "label_bad":
                data["color"] = s["label_bad_color"]
                data["fontcolor"] = s["label_bad_color"]
                data["fontname"] = s["font_name"]
            elif ntype == "label_constraint":
                data["color"] = s["label_constraint_color"]
                data["fontcolor"] = s["label_constraint_color"]
                data["fontname"] = s["font_name"]
            elif ntype == "label_latch":
                data["color"] = s["label_latch_color"]
                data["fontcolor"] = s["label_latch_color"]
                data["fontname"] = s["font_name"]

        for u, v, data in G.edges(data=True):
            etype = _classify_edge(dict(data))
            if etype == "complemented":
                data["color"] = s["complemented_edge_color"]
                data["arrowhead"] = s["complemented_arrowhead"]
                data["penwidth"] = 1.5
            elif etype == "latch_feedback":
                data["color"] = s["latch_edge_color"]
                data["style"] = "dashed"
                data["penwidth"] = 1.5
            else:
                data["color"] = s["normal_edge_color"]
                data["arrowhead"] = s["normal_arrowhead"]
                data["penwidth"] = 1.2

        return G

    CP_COLORS = ["#FFD700", "#00CED1", "#7FFF00", "#FF69B4", "#FF8C00", "#9370DB", "#00FA9A", "#DC143C"]
    CP_OVERLAP_COLOR = "#FF00FF"

    def render_dot(self, aig_path, strip=False, integer_lits=False, highlight_paths=None):
        G = self.get_styled_graph(aig_path, strip, integer_lits)
        s = self.style
        rankdir = s["rankdir"]

        cp_node_colors = {}
        cp_edge_colors = {}
        cp_legend = {}

        if highlight_paths:
            from vaiger.stats import _trace_critical_subgraph, _trace_single_critical_path, _get_circuit_depth, _get_node_types_from_raw
            depth, R = _get_circuit_depth(G)
            node_types = _get_node_types_from_raw(G)
            pi_nodes = {n for n, t in node_types.items() if t == "Input label"}
            input_boxes = {n for n, t in node_types.items() if t == "Input"}
            sources = pi_nodes | input_boxes

            node_count = {}
            edge_count = {}
            for idx, (po, mode) in enumerate(sorted(highlight_paths.items())):
                if mode == "single":
                    nodes, edges = _trace_single_critical_path(po, depth, R, sources)
                else:
                    nodes, edges = _trace_critical_subgraph(po, depth, R, sources)
                if not nodes:
                    continue
                color = self.CP_COLORS[idx % len(self.CP_COLORS)]
                cp_legend[po] = color
                for node in nodes:
                    node_count[node] = node_count.get(node, 0) + 1
                    cp_node_colors[node] = color
                for edge in edges:
                    edge_count[edge] = edge_count.get(edge, 0) + 1
                    cp_edge_colors[edge] = color
            for node, cnt in node_count.items():
                if cnt > 1:
                    cp_node_colors[node] = self.CP_OVERLAP_COLOR
            for edge, cnt in edge_count.items():
                if cnt > 1:
                    cp_edge_colors[edge] = self.CP_OVERLAP_COLOR

        pi_labels = []
        po_labels = []
        pi_nodes = set()

        for node, data in G.nodes(data=True):
            ntype = _classify_node(node, dict(data))
            if ntype == "label_input":
                pi_labels.append(node)
            elif ntype == "label_output":
                po_labels.append(node)

        for lbl_node in pi_labels:
            for pred in G.predecessors(lbl_node):
                pi_nodes.add(pred)

        pi_label_set = set(pi_labels)
        pi_node_set = pi_nodes
        po_label_set = set(po_labels)

        circuit = nx.DiGraph()
        for node in G.nodes():
            circuit.add_node(node)
        for u, v in G.edges():
            circuit.add_edge(u, v)

        topo = list(nx.topological_sort(circuit))
        circuit_depth = {}
        for node in topo:
            preds = list(circuit.predecessors(node))
            if not preds:
                circuit_depth[node] = 0
            else:
                circuit_depth[node] = max(circuit_depth[p] for p in preds) + 1

        max_depth = max(circuit_depth.values()) if circuit_depth else 0

        po_at_start = rankdir in ("TB", "BT")
        pi_at_start = rankdir in ("LR", "RL")

        if po_at_start:
            level = {}
            for node, d in circuit_depth.items():
                if node in po_label_set:
                    level[node] = 0
                elif node in pi_node_set:
                    level[node] = max_depth + 1
                elif node in pi_label_set:
                    level[node] = max_depth + 2
                else:
                    level[node] = d + 1
        else:
            level = {}
            for node, d in circuit_depth.items():
                if node in pi_label_set:
                    level[node] = 0
                elif node in pi_node_set:
                    level[node] = 1
                elif node in po_label_set:
                    level[node] = max_depth + 2
                else:
                    level[node] = max_depth - d + 1

        from collections import defaultdict
        level_groups = defaultdict(list)
        for node, lvl in level.items():
            level_groups[lvl].append(node)

        lines = []
        graph_name = Path(aig_path).stem
        lines.append(f'digraph "{graph_name}" {{')
        lines.append(f'  bgcolor="{s["bg_color"]}";')
        lines.append(f'  rankdir={rankdir};')
        lines.append(f'  node [fontname="{s["font_name"]}"];')
        lines.append(f'  edge [fontname="{s["font_name"]}"];')
        lines.append("")

        def _qn(n):
            return n.replace('"', '\\"')

        for node, data in G.nodes(data=True):
            attrs = []
            ntype = _classify_node(node, dict(data))
            label = data.get("label", node)
            if isinstance(label, str) and label.startswith('"') and label.endswith('"'):
                label = label.strip('"')

            for k, v in data.items():
                if k in ("label",):
                    continue
                if isinstance(v, str) and k not in ("shape", "style", "rankdir"):
                    attrs.append(f'{k}="{v}"')
                else:
                    attrs.append(f"{k}={v}")
            if ntype.startswith("label_"):
                attrs.append(f'label="{label}"')

            if cp_node_colors and node in cp_node_colors:
                attrs = [a for a in attrs if not a.startswith("color=")]
                attrs.append(f'color="{cp_node_colors[node]}"')
                attrs.append('penwidth=3')

            attr_str = ", ".join(attrs)
            lines.append(f'  "{_qn(node)}" [{attr_str}];')

        lines.append("")

        for lvl in sorted(level_groups.keys()):
            nodes_at_level = sorted(level_groups[lvl], key=str)
            lines.append(f"  {{ rank=same;")
            for n in nodes_at_level:
                lines.append(f'    "{_qn(n)}";')
            lines.append("  }")

        lines.append("")

        for orig_u, orig_v, data in G.edges(data=True):
            lu = level.get(orig_u, 0)
            lv = level.get(orig_v, 0)
            flipped = lu > lv
            u, v = (orig_v, orig_u) if flipped else (orig_u, orig_v)
            attrs = []
            has_arrowtail = False
            for k, val in data.items():
                if k == "arrowhead":
                    if flipped:
                        if val == "odot":
                            attrs.append("arrowtail=odot")
                            has_arrowtail = True
                    else:
                        attrs.append(f"arrowhead={val}")
                elif k == "arrowtail":
                    if flipped:
                        attrs.append(f"arrowhead={val}")
                    else:
                        if val == "odot":
                            attrs.append("arrowtail=odot")
                            has_arrowtail = True
                elif isinstance(val, str) and k == "style":
                    attrs.append(f"{k}={val}")
                elif isinstance(val, str):
                    attrs.append(f'{k}="{val}"')
                else:
                    attrs.append(f"{k}={val}")
            if has_arrowtail:
                attrs.append("dir=both")
            if cp_edge_colors and (orig_u, orig_v) in cp_edge_colors:
                attrs = [a for a in attrs if not a.startswith("color=")]
                attrs.append(f'color="{cp_edge_colors[(orig_u, orig_v)]}"')
                attrs.append('penwidth=3')
            attr_str = ", ".join(attrs)
            lines.append(f'  "{_qn(u)}" -> "{_qn(v)}" [{attr_str}];')

        lines.append("}")
        return "\n".join(lines), cp_legend

    def render(self, aig_path, output_path=None, strip=False, integer_lits=False, backend=None, highlight_paths=None):
        output_path = str(output_path) if output_path else None

        if backend is None and output_path:
            ext = Path(output_path).suffix.lower()
            if ext in (".png", ".svg", ".pdf"):
                backend = "graphviz"
            else:
                backend = "matplotlib"

        if backend is None:
            backend = "matplotlib"

        if backend == "graphviz":
            return self._render_graphviz(aig_path, output_path, strip, integer_lits, highlight_paths)
        else:
            return self._render_matplotlib(aig_path, output_path, strip, integer_lits)

    def _render_graphviz(self, aig_path, output_path, strip=False, integer_lits=False, highlight_paths=None):
        if pydot is None:
            raise ImportError("pydot is required for graphviz rendering: pip install pydot")

        dot_str, _ = self.render_dot(aig_path, strip, integer_lits, highlight_paths=highlight_paths)
        pydot_graphs = pydot.graph_from_dot_data(dot_str)
        if not pydot_graphs:
            raise ValueError("Failed to parse styled DOT")

        graph = pydot_graphs[0]
        ext = Path(output_path).suffix.lower().lstrip(".") if output_path else "png"

        if output_path:
            output_dir = str(Path(output_path).parent)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            graph.write(output_path, format=ext)
            return output_path
        else:
            return graph.create(format="png")

    def _render_matplotlib(self, aig_path, output_path=None, strip=False, integer_lits=False):
        if plt is None:
            raise ImportError("matplotlib is required: pip install matplotlib")

        G = self.get_styled_graph(aig_path, strip, integer_lits)
        s = self.style

        fig, ax = plt.subplots(1, 1, figsize=(12, 8), facecolor=s["bg_color"])
        ax.set_facecolor(s["bg_color"])

        pos = nx.drawing.layout.spring_layout(G, seed=42, k=2.0 / (G.number_of_nodes() ** 0.5 + 1))

        node_colors = []
        node_sizes = []
        node_labels = {}
        for node, data in G.nodes(data=True):
            ntype = _classify_node(node, dict(data))
            color_map = {
                "and": s["and_fillcolor"],
                "input": s["input_fillcolor"],
                "latch": s["latch_fillcolor"],
                "constant": s["constant_fillcolor"],
                "label_input": s["label_input_color"],
                "label_output": s["label_output_color"],
                "label_bad": s["label_bad_color"],
                "label_constraint": s["label_constraint_color"],
                "label_latch": s["label_latch_color"],
                "other": "#CCCCCC",
            }
            node_colors.append(color_map.get(ntype, "#CCCCCC"))
            size_map = {
                "and": 600,
                "input": 500,
                "latch": 500,
                "constant": 400,
                "label_input": 300,
                "label_output": 300,
                "label_bad": 300,
                "label_constraint": 300,
                "label_latch": 300,
                "other": 400,
            }
            node_sizes.append(size_map.get(ntype, 400))
            label = data.get("label", str(node))
            if isinstance(label, str):
                label = label.strip('"')
            node_labels[node] = label

        complemented_edges = []
        normal_edges = []
        latch_edges = []
        for u, v, data in G.edges(data=True):
            etype = _classify_edge(dict(data))
            if etype == "complemented":
                complemented_edges.append((u, v))
            elif etype == "latch_feedback":
                latch_edges.append((u, v))
            else:
                normal_edges.append((u, v))

        nx.draw_networkx_edges(
            G, pos, edgelist=normal_edges, edge_color=s["normal_edge_color"],
            arrows=True, arrowstyle="-|>", arrowsize=12, ax=ax, alpha=0.8,
        )
        nx.draw_networkx_edges(
            G, pos, edgelist=complemented_edges, edge_color=s["complemented_edge_color"],
            arrows=True, arrowstyle="-|>", arrowsize=12, ax=ax, width=1.5, style="dashed",
        )
        if latch_edges:
            nx.draw_networkx_edges(
                G, pos, edgelist=latch_edges, edge_color=s["latch_edge_color"],
                arrows=True, arrowstyle="-|>", arrowsize=12, ax=ax, style="dashed", alpha=0.7,
            )

        nx.draw_networkx_nodes(
            G, pos, node_color=node_colors, node_size=node_sizes,
            edgecolors="#333333", linewidths=0.8, ax=ax,
        )
        nx.draw_networkx_labels(
            G, pos, labels=node_labels, font_size=8, font_color="#1D3557", ax=ax,
        )

        ax.set_title(f"AIG Graph: {Path(aig_path).stem}", fontsize=14, fontweight="bold")
        ax.axis("off")
        plt.tight_layout()

        if output_path and output_path != ".show":
            fig.savefig(output_path, dpi=s["dpi"], bbox_inches="tight", facecolor=s["bg_color"])
            plt.close(fig)
            return output_path
        else:
            plt.show()
            plt.close(fig)
            return None
