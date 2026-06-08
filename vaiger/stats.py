import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import networkx as nx
from collections import Counter

from vaiger.graph import AigerGraph
from vaiger.visualizer import _classify_node, _classify_edge

PALETTE = {
    "AND gate": "#FF6B6B",
    "Input": "#A8DADC",
    "Latch": "#F4A261",
    "Constant": "#E63946",
    "Input label": "#457B9D",
    "Output label": "#2A9D8F",
    "Bad label": "#E63946",
    "Constraint label": "#2D6A4F",
    "Latch label": "#F4A261",
    "Other": "#CCCCCC",
}

EDGE_PALETTE = {
    "Complemented": "#E63946",
    "Normal": "#457B9D",
    "Latch feedback": "#F4A261",
}

_DISPLAY_NAMES = {
    "and": "AND gate",
    "input": "Input",
    "latch": "Latch",
    "constant": "Constant",
    "label_input": "Input label",
    "label_output": "Output label",
    "label_bad": "Bad label",
    "label_constraint": "Constraint label",
    "label_latch": "Latch label",
    "other": "Other",
}

_EDGE_DISPLAY = {
    "complemented": "Complemented",
    "normal": "Normal",
    "latch_feedback": "Latch feedback",
}


def _get_node_types_from_raw(G):
    result = {}
    for node, data in G.nodes(data=True):
        ntype = _classify_node(node, dict(data))
        result[node] = _DISPLAY_NAMES.get(ntype, "Other")
    return result


def _get_edge_types(G):
    result = []
    for u, v, data in G.edges(data=True):
        etype = _classify_edge(dict(data))
        result.append(_EDGE_DISPLAY.get(etype, "Other"))
    return result


def plot_degree_distribution(G, raw_graph=None, figsize=(10, 4)):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)
    degrees = dict(G.degree())

    records = []
    for node, deg in degrees.items():
        records.append({"node": node, "degree": deg, "type": node_types.get(node, "Other")})
    df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=figsize)
    if len(df) > 0:
        sns.histplot(
            data=df, x="degree", hue="type", multiple="stack",
            palette=PALETTE, ax=ax, discrete=True,
            shrink=0.8, edgecolor="white",
        )
    ax.set_title("Node Degree Distribution", fontweight="bold")
    ax.set_xlabel("Degree")
    ax.set_ylabel("Count")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def plot_node_type_pie(G, raw_graph=None, figsize=(6, 6)):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)
    counts = Counter(node_types.values())

    structural = {"AND gate", "Input", "Latch", "Constant"}
    labels = []
    sizes = []
    colors = []
    for ntype in structural:
        if ntype in counts:
            labels.append(ntype)
            sizes.append(counts[ntype])
            colors.append(PALETTE.get(ntype, "#CCCCCC"))

    fig, ax = plt.subplots(figsize=figsize)
    if sizes:
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct="%1.1f%%",
            startangle=90, pctdistance=0.85,
            wedgeprops=dict(width=0.4, edgecolor="white"),
        )
        for t in autotexts:
            t.set_fontsize(10)
            t.set_fontweight("bold")
    ax.set_title("Node Type Distribution", fontweight="bold")
    fig.tight_layout()
    return fig


def plot_fan_distribution(G, raw_graph=None, figsize=(10, 4)):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)

    records = []
    for node in G.nodes():
        ntype = node_types.get(node, "Other")
        records.append({
            "node": node,
            "type": ntype,
            "fan_in": G.out_degree(node),
            "fan_out": G.in_degree(node),
        })
    df = pd.DataFrame(records)

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    if len(df) > 0:
        sns.histplot(
            data=df, x="fan_in", hue="type", multiple="stack",
            palette=PALETTE, ax=axes[0], discrete=True,
            shrink=0.8, edgecolor="white",
        )
    axes[0].set_title("Fan-in Distribution", fontweight="bold")
    axes[0].set_xlabel("Fan-in (number of gate inputs)")
    axes[0].set_ylabel("Count")
    axes[0].xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    if len(df) > 0:
        sns.histplot(
            data=df, x="fan_out", hue="type", multiple="stack",
            palette=PALETTE, ax=axes[1], discrete=True,
            shrink=0.8, edgecolor="white",
        )
    axes[1].set_title("Fan-out Distribution", fontweight="bold")
    axes[1].set_xlabel("Fan-out (number of gates driven)")
    axes[1].set_ylabel("Count")
    axes[1].xaxis.set_major_locator(plt.MaxNLocator(integer=True))

    for ax in axes:
        sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def plot_edge_type_counts(G, figsize=(6, 4)):
    edge_types = _get_edge_types(G)
    counts = Counter(edge_types)

    labels = []
    sizes = []
    colors = []
    for etype in ["Normal", "Complemented", "Latch feedback"]:
        if etype in counts:
            labels.append(etype)
            sizes.append(counts[etype])
            colors.append(EDGE_PALETTE.get(etype, "#CCCCCC"))

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(labels, sizes, color=colors, edgecolor="white", width=0.6)
    for bar, size in zip(bars, sizes):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(size), ha="center", fontweight="bold", fontsize=11)
    ax.set_title("Edge Type Breakdown", fontweight="bold")
    ax.set_ylabel("Count")
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def get_node_dataframe(G, raw_graph=None):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)
    records = []
    for node, data in G.nodes(data=True):
        ntype = node_types.get(node, "Other")
        label = data.get("label", "")
        if isinstance(label, str):
            label = label.strip('"')
        records.append({
            "node": str(node),
            "type": ntype,
            "label": label,
            "in_degree": G.in_degree(node),
            "out_degree": G.out_degree(node),
        })
    return pd.DataFrame(records)


def get_edge_dataframe(G):
    records = []
    for u, v, data in G.edges(data=True):
        etype = _classify_edge(dict(data))
        records.append({
            "source": str(u),
            "target": str(v),
            "type": _EDGE_DISPLAY.get(etype, "Other"),
        })
    return pd.DataFrame(records)


def _get_circuit_depth(G):
    R = G.reverse()
    node_types = _get_node_types_from_raw(G)
    pi_nodes = {n for n, t in node_types.items() if t == "Input label"}
    input_boxes = {n for n, t in node_types.items() if t == "Input"}

    sources = pi_nodes | input_boxes
    topo = list(nx.topological_sort(R))
    depth = {}
    for node in topo:
        if node in sources:
            depth[node] = 0
        else:
            preds = list(R.predecessors(node))
            if not preds:
                depth[node] = 0
            else:
                depth[node] = max(depth.get(p, 0) for p in preds) + 1
    return depth, R


def compute_logic_depth(G):
    depth, _ = _get_circuit_depth(G)
    return depth


def _trace_critical_subgraph(po, depth, R, sources):
    nodes = set()
    edges = set()
    queue = [po]
    visited = {po}
    while queue:
        current = queue.pop(0)
        current_depth = depth.get(current, 0)
        if current_depth == 0:
            continue
        for pred in R.predecessors(current):
            edges.add((pred, current))
            edges.add((current, pred))
            if pred in visited:
                continue
            pred_depth = depth.get(pred, 0)
            if pred_depth == current_depth - 1:
                visited.add(pred)
                nodes.add(pred)
                if pred not in sources:
                    queue.append(pred)
    nodes.add(po)
    return nodes, edges


def _trace_single_critical_path(po, depth, R, sources):
    nodes = set()
    edges = set()
    current = po
    nodes.add(current)
    while current not in sources:
        current_depth = depth.get(current, 0)
        if current_depth == 0:
            break
        chosen = None
        for pred in R.predecessors(current):
            if depth.get(pred, -1) == current_depth - 1:
                chosen = pred
                break
        if chosen is None:
            break
        nodes.add(chosen)
        edges.add((chosen, current))
        edges.add((current, chosen))
        current = chosen
    return nodes, edges


def compute_all_critical_paths(G):
    depth, R = _get_circuit_depth(G)
    node_types = _get_node_types_from_raw(G)
    po_labels = sorted([n for n, t in node_types.items() if t == "Output label"])
    pi_nodes = {n for n, t in node_types.items() if t == "Input label"}
    input_boxes = {n for n, t in node_types.items() if t == "Input"}
    sources = pi_nodes | input_boxes

    result = {}
    for po in po_labels:
        nodes, edges = _trace_critical_subgraph(po, depth, R, sources)
        result[po] = (nodes, edges, depth.get(po, 0))
    return result


def compute_critical_path(G):
    all_paths = compute_all_critical_paths(G)
    if not all_paths:
        return set(), set(), 0
    best_po = max(all_paths, key=lambda po: all_paths[po][2])
    return all_paths[best_po]


def compute_cone_sizes(G):
    node_types = _get_node_types_from_raw(G)
    po_labels = sorted([n for n, t in node_types.items() if t == "Output label"])
    R = G.reverse()
    result = {}
    for po in po_labels:
        ancestors = nx.ancestors(R, po)
        and_ancestors = sum(1 for a in ancestors if node_types.get(a) == "AND gate")
        result[po] = and_ancestors
    return result


def plot_logic_depth(G, raw_graph=None, figsize=(10, 4)):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)
    depth = compute_logic_depth(G)

    records = []
    for node, d in depth.items():
        ntype = node_types.get(node, "Other")
        if ntype in ("AND gate", "Input", "Output label"):
            records.append({"node": node, "type": ntype, "depth": d})
    df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=figsize)
    if len(df) > 0:
        structural = df[df["type"].isin(["AND gate", "Input", "Output label"])]
        sns.histplot(
            data=structural, x="depth", hue="type", multiple="stack",
            palette=PALETTE, ax=ax, discrete=True,
            shrink=0.8, edgecolor="white",
        )
    ax.set_title("Logic Depth Distribution", fontweight="bold")
    ax.set_xlabel("Logic Depth (levels from primary inputs)")
    ax.set_ylabel("Count")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def plot_level_and_count(G, raw_graph=None, figsize=(10, 4)):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)
    depth = compute_logic_depth(G)

    and_depths = {}
    for node, d in depth.items():
        if node_types.get(node) == "AND gate":
            and_depths[node] = d

    if not and_depths:
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_title("Level-wise AND Gate Count", fontweight="bold")
        ax.text(0.5, 0.5, "No AND gates", ha="center", va="center", transform=ax.transAxes)
        sns.despine(ax=ax)
        fig.tight_layout()
        return fig

    level_counts = Counter(and_depths.values())
    max_level = max(level_counts.keys())
    levels = list(range(max_level + 1))
    counts = [level_counts.get(l, 0) for l in levels]

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(levels, counts, color=PALETTE["AND gate"], edgecolor="white", width=0.7)
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                    str(count), ha="center", fontweight="bold", fontsize=10)
    ax.set_title("Level-wise AND Gate Count", fontweight="bold")
    ax.set_xlabel("Logic Level")
    ax.set_ylabel("AND Gates")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def plot_cone_size(G, raw_graph=None, figsize=(8, 4)):
    cone_sizes = compute_cone_sizes(G)
    if not cone_sizes:
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_title("Transitive Fanin Cone Size per Output", fontweight="bold")
        ax.text(0.5, 0.5, "No outputs found", ha="center", va="center", transform=ax.transAxes)
        sns.despine(ax=ax)
        fig.tight_layout()
        return fig

    labels = sorted(cone_sizes.keys())
    sizes = [cone_sizes[l] for l in labels]

    fig, ax = plt.subplots(figsize=figsize)
    colors = [PALETTE.get("Output label", "#2A9D8F")] * len(labels)
    bars = ax.bar(labels, sizes, color=colors, edgecolor="white", width=0.6)
    for bar, size in zip(bars, sizes):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(size), ha="center", fontweight="bold", fontsize=11)
    ax.set_title("Transitive Fanin Cone Size per Output", fontweight="bold")
    ax.set_xlabel("Output")
    ax.set_ylabel("AND Gates in Cone")
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def plot_betweenness(G, raw_graph=None, figsize=(10, 4)):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)

    centrality = nx.betweenness_centrality(G, normalized=True)

    records = []
    for node, cent in centrality.items():
        ntype = node_types.get(node, "Other")
        records.append({"node": node, "type": ntype, "centrality": cent})
    df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=figsize)
    if len(df) > 0:
        structural = df[df["type"].isin(["AND gate", "Input", "Output label"])]
        if len(structural) > 0:
            sns.histplot(
                data=structural, x="centrality", hue="type", multiple="stack",
                palette=PALETTE, ax=ax, bins=20,
                edgecolor="white",
            )
    ax.set_title("Betweenness Centrality Distribution", fontweight="bold")
    ax.set_xlabel("Betweenness Centrality (normalized)")
    ax.set_ylabel("Count")
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def plot_adjacency_heatmap(G, raw_graph=None, figsize=(8, 8)):
    if raw_graph is not None:
        node_types = _get_node_types_from_raw(raw_graph)
    else:
        node_types = _get_node_types_from_raw(G)

    depth = compute_logic_depth(G)
    nodes = sorted(G.nodes(), key=lambda n: (depth.get(n, 0), str(n)))

    adj = np.zeros((len(nodes), len(nodes)), dtype=int)
    node_idx = {n: i for i, n in enumerate(nodes)}
    for u, v, data in G.edges(data=True):
        if u in node_idx and v in node_idx:
            etype = _classify_edge(dict(data))
            adj[node_idx[u], node_idx[v]] = 2 if etype == "complemented" else 1

    fig, ax = plt.subplots(figsize=figsize)
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(["#FFFFFF", "#457B9D", "#E63946"])
    im = ax.imshow(adj, cmap=cmap, vmin=0, vmax=2, aspect="auto")

    labels = []
    for n in nodes:
        ntype = node_types.get(n, "Other")
        short = n if len(str(n)) <= 5 else str(n)[:4] + ".."
        labels.append(short)

    ax.set_xticks(range(len(nodes)))
    ax.set_yticks(range(len(nodes)))
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_yticklabels(labels, fontsize=7)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#457B9D", label="Normal"),
        Patch(facecolor="#E63946", label="Complemented"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8)

    ax.set_title("Adjacency Heatmap (ordered by logic depth)", fontweight="bold")
    fig.tight_layout()
    return fig
