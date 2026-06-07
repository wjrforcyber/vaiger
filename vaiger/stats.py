import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
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
