import streamlit as st
import tempfile
import os
from pathlib import Path

from vaiger import AigerVisualizer, AigerGraph, AigerWrapper
from vaiger import stats
from vaiger.svg_viewer import make_zoomable_svg_html
from vaiger.visualizer import DEFAULT_STYLE
from vaiger.stats import compute_critical_path, compute_all_critical_paths
import networkx as nx

AIGER_EXAMPLES = Path("aiger/examples")

THEMES = {
    "Default": {},
    "Dark": {
        "and_fillcolor": "#6C5CE7",
        "and_fontcolor": "#FFFFFF",
        "complemented_edge_color": "#FF6B6B",
        "normal_edge_color": "#74B9FF",
        "input_fillcolor": "#00CEC9",
        "input_fontcolor": "#2D3436",
        "latch_fillcolor": "#FDCB6E",
        "bg_color": "#2D3436",
        "font_name": "Courier",
    },
    "Pastel": {
        "and_fillcolor": "#FFB5E8",
        "complemented_edge_color": "#FF6B6B",
        "normal_edge_color": "#B5DEFF",
        "input_fillcolor": "#E7FFAC",
        "latch_fillcolor": "#FFC9DE",
        "label_input_color": "#6EB5FF",
        "label_output_color": "#85E3FF",
        "bg_color": "#F0F0F0",
    },
    "Monochrome": {
        "and_fillcolor": "#FFFFFF",
        "and_fontcolor": "#000000",
        "complemented_edge_color": "#000000",
        "normal_edge_color": "#666666",
        "input_fillcolor": "#EEEEEE",
        "input_fontcolor": "#000000",
        "latch_fillcolor": "#DDDDDD",
        "bg_color": "#FFFFFF",
    },
}

st.set_page_config(
    page_title="VAiger — AIG Viewer",
    page_icon="🔌",
    layout="wide",
)


def _get_theme_overrides(theme_name, rankdir):
    overrides = dict(THEMES.get(theme_name, {}))
    overrides["rankdir"] = rankdir
    return overrides


@st.cache_data
def load_raw_graph(aig_path):
    ag = AigerGraph()
    return ag.load(aig_path)


def render_svg(aig_path, theme_name, rankdir, highlight_paths=None):
    overrides = _get_theme_overrides(theme_name, rankdir)
    viz = AigerVisualizer(**overrides)
    dot_str, legend = viz.render_dot(aig_path, highlight_paths=highlight_paths)
    import pydot
    pydot_graphs = pydot.graph_from_dot_data(dot_str)
    if not pydot_graphs:
        return None, legend
    graph = pydot_graphs[0]
    return graph.create_svg().decode("utf-8"), legend


def render_dot_string(aig_path, theme_name, rankdir, highlight_paths=None):
    overrides = _get_theme_overrides(theme_name, rankdir)
    viz = AigerVisualizer(**overrides)
    dot_str, _ = viz.render_dot(aig_path, highlight_paths=highlight_paths)
    return dot_str


@st.cache_data
def get_analysis(aig_path):
    ag = AigerGraph()
    _, stat_dict = ag.analyze(aig_path)
    return stat_dict


def get_stats_plots(aig_path, selected_keys=None):
    if selected_keys is None:
        selected_keys = ["degree", "node_type", "fan", "edge_type"]
    raw_G = load_raw_graph(aig_path)
    result = {}
    if "degree" in selected_keys:
        result["degree"] = stats.plot_degree_distribution(raw_G)
    if "node_type" in selected_keys:
        result["node_type"] = stats.plot_node_type_pie(raw_G)
    if "fan" in selected_keys:
        result["fan"] = stats.plot_fan_distribution(raw_G)
    if "edge_type" in selected_keys:
        result["edge_type"] = stats.plot_edge_type_counts(raw_G)
    if "logic_depth" in selected_keys:
        result["logic_depth"] = stats.plot_logic_depth(raw_G)
    if "level_and" in selected_keys:
        result["level_and"] = stats.plot_level_and_count(raw_G)
    if "cone_size" in selected_keys:
        result["cone_size"] = stats.plot_cone_size(raw_G)
    if "betweenness" in selected_keys:
        result["betweenness"] = stats.plot_betweenness(raw_G)
    if "adjacency" in selected_keys:
        result["adjacency"] = stats.plot_adjacency_heatmap(raw_G)
    return result


def get_example_files():
    if AIGER_EXAMPLES.exists():
        return sorted([f.name for f in AIGER_EXAMPLES.iterdir() if f.suffix in (".aag", ".aig")])
    return []


def _color_box(hex_color, width=16, height=16):
    return f'<span style="display:inline-block;width:{width}px;height:{height}px;' \
           f'background:{hex_color};border:1px solid #999;border-radius:3px;' \
           f'vertical-align:middle;margin-right:6px;"></span>'


def _line_sample(hex_color, dashed=False, width=30):
    dash = "stroke-dasharray:4 2;" if dashed else ""
    return f'<svg width="{width}" height="8" style="vertical-align:middle;margin-right:6px;">' \
           f'<line x1="0" y1="4" x2="{width}" y2="4" stroke="{hex_color}" stroke-width="2.5" {dash}/>' \
           f'</svg>'


def render_legend(theme_overrides):
    s = {**DEFAULT_STYLE, **theme_overrides}

    node_items = [
        ("AND Gate", s["and_fillcolor"], "circle"),
        ("Input", s["input_fillcolor"], "box"),
        ("Latch", s["latch_fillcolor"], "box"),
        ("Constant (0/1)", s["constant_fillcolor"], "box"),
        ("Input label (I#)", s["label_input_color"], "triangle"),
        ("Output label (O#)", s["label_output_color"], "triangle"),
        ("Bad state label (B#)", s["label_bad_color"], "triangle"),
        ("Constraint label (C#)", s["label_constraint_color"], "triangle"),
        ("Latch label (L#)", s["label_latch_color"], "diamond"),
    ]

    shape_css = {
        "circle": "border-radius:50%;",
        "box": "border-radius:3px;",
        "triangle": "width:0;height:0;border-left:8px solid transparent;"
                     "border-right:8px solid transparent;border-bottom:16px solid {};display:inline-block;background:none !important;",
        "diamond": "width:12px;height:12px;transform:rotate(45deg);border-radius:2px;",
    }

    rows = []
    for label, color, shape in node_items:
        if shape == "triangle":
            box = f'<span style="display:inline-block;width:0;height:0;border-left:8px solid transparent;' \
                  f'border-right:8px solid transparent;border-bottom:16px solid {color};' \
                  f'vertical-align:middle;margin-right:6px;"></span>'
        else:
            extra = shape_css.get(shape, "")
            box = f'<span style="display:inline-block;width:16px;height:16px;background:{color};' \
                  f'border:1px solid #999;vertical-align:middle;margin-right:6px;{extra}"></span>'
        rows.append(f"<tr><td>{box}</td><td style='padding:2px 6px;font-size:13px;'>{label}</td></tr>")

    edge_items = [
        ("Normal edge", s["normal_edge_color"], False),
        ("Complemented edge (inverted)", s["complemented_edge_color"], False),
        ("Latch feedback edge", s["latch_edge_color"], True),
    ]
    for label, color, dashed in edge_items:
        sample = _line_sample(color, dashed)
        rows.append(f"<tr><td>{sample}</td><td style='padding:2px 6px;font-size:13px;'>{label}</td></tr>")

    table_html = (
        "<table style='border:none;margin-top:4px;'>"
        + "".join(rows)
        + "</table>"
    )
    return table_html


def main():
    st.title("VAiger — AIG File Viewer & Analyzer")
    st.markdown("Upload an AIGER file (`.aag` / `.aig`) or select an example to visualize and analyze And-Inverter Graphs.")

    with st.sidebar:
        st.header("Input")
        uploaded = st.file_uploader(
            "Upload AIG file",
            type=["aag", "aig"],
            help="Upload an ASCII (.aag) or binary (.aig) AIGER file",
        )

        examples = get_example_files()
        selected_example = None
        if examples:
            selected_example = st.selectbox(
                "Or pick an example",
                [""] + examples,
                help="Select a built-in example file from the aiger submodule",
            )

        st.divider()
        st.header("Rendering")
        theme = st.selectbox("Color theme", list(THEMES.keys()), index=0)
        rankdir = st.selectbox(
            "Layout direction",
            ["TB", "LR", "BT", "RL"],
            format_func=lambda x: {
                "TB": "TB  (outputs top, inputs bottom)",
                "LR": "LR  (inputs left, outputs right)",
                "BT": "BT  (inputs top, outputs bottom)",
                "RL": "RL  (outputs left, inputs right)",
            }[x],
            index=0,
        )

        st.divider()
        st.header("Legend")
        legend_html = render_legend(THEMES[theme])
        st.markdown(legend_html, unsafe_allow_html=True)

    aig_path = None
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            aig_path = tmp.name
        if selected_example:
            st.sidebar.caption(f"Using uploaded file (ignoring example: {selected_example})")
    elif selected_example and selected_example in examples:
        aig_path = str(AIGER_EXAMPLES / selected_example)

    if aig_path is None:
        st.info("Upload an AIG file or select an example to get started.")
        return

    try:
        with st.spinner("Loading AIG..."):
            raw_G = load_raw_graph(aig_path)
            stat_dict = get_analysis(aig_path)

        file_name = uploaded.name if uploaded else selected_example
        st.subheader(f":bar_chart: {file_name}")

        all_cp = compute_all_critical_paths(raw_G)
        _, _, cp_length = compute_critical_path(raw_G)

        cp_options = ["None"]
        cp_path_map = {"None": None}
        if all_cp:
            cp_options.append("All critical paths")
            cp_path_map["All critical paths"] = {po: "all" for po in all_cp}
            for po, (_, _, length) in sorted(all_cp.items()):
                label = f"{po} — {length} levels"
                cp_options.append(label)
                cp_path_map[label] = {po: "single"}

        cp_selection = st.selectbox("Critical path highlight", cp_options, index=0)

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Nodes", stat_dict["num_nodes"])
        col2.metric("Edges", stat_dict["num_edges"])
        col3.metric("Density", f"{stat_dict['density']:.3f}")
        col4.metric("Avg Degree", f"{stat_dict['avg_degree']:.1f}" if "avg_degree" in stat_dict else "N/A")
        col5.metric("Components", stat_dict["num_connected_components"])
        col6.metric("Crit. Path", f"{cp_length} levels")

        tab_graph, tab_stats, tab_dot = st.tabs([
            "Graph", "Statistics", "DOT Source"
        ])

        highlight = cp_path_map.get(cp_selection)

        with tab_graph:
            with st.spinner("Rendering graph SVG..."):
                svg_html, cp_legend = render_svg(aig_path, theme, rankdir, highlight_paths=highlight)
            if svg_html:
                zoomable_html, _ = make_zoomable_svg_html(svg_html, height=750)
                st.components.v1.html(zoomable_html, height=750)
                if cp_legend:
                    items = []
                    for po, color in sorted(cp_legend.items()):
                        items.append(
                            f'<span style="display:inline-block;width:14px;height:14px;'
                            f'background:{color};border:1px solid #999;border-radius:2px;'
                            f'vertical-align:middle;margin-right:4px;"></span>'
                            f'<span style="font-size:13px;margin-right:12px;">{po}</span>'
                        )
                    overlap_item = (
                        f'<span style="display:inline-block;width:14px;height:14px;'
                        f'background:#FF00FF;border:1px solid #999;border-radius:2px;'
                        f'vertical-align:middle;margin-right:4px;"></span>'
                        f'<span style="font-size:13px;margin-right:12px;">overlap</span>'
                    )
                    st.markdown(
                        '<div style="margin-top:4px;">'
                        + "".join(items) + overlap_item + "</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.error("Failed to render graph SVG.")

        with tab_stats:
            PLOT_OPTIONS = {
                "Degree Distribution": "degree",
                "Node Type Distribution": "node_type",
                "Edge Type Breakdown": "edge_type",
                "Fan-in / Fan-out Distribution": "fan",
                "Logic Depth Distribution": "logic_depth",
                "Level-wise AND Count": "level_and",
                "Cone Size per Output": "cone_size",
                "Betweenness Centrality": "betweenness",
                "Adjacency Heatmap": "adjacency",
            }
            selected_labels = st.multiselect(
                "Select plots to display",
                options=list(PLOT_OPTIONS.keys()),
                default=list(PLOT_OPTIONS.keys()),
            )

            if not selected_labels:
                st.info("Select at least one plot type above.")
            else:
                selected_keys = [PLOT_OPTIONS[l] for l in selected_labels]
                with st.spinner("Generating plots..."):
                    plots = get_stats_plots(aig_path, selected_keys)

                if "expanded_plot" not in st.session_state:
                    st.session_state.expanded_plot = None

                if st.session_state.expanded_plot is not None:
                    exp_key = st.session_state.expanded_plot
                    exp_label = next(
                        (l for l, k in PLOT_OPTIONS.items() if k == exp_key),
                        exp_key,
                    )
                    col_back, col_spacer = st.columns([1, 10])
                    with col_back:
                        if st.button("Back to grid", key="btn_back"):
                            st.session_state.expanded_plot = None
                            st.rerun()
                    st.subheader(exp_label)
                    st.pyplot(plots[exp_key], use_container_width=True)
                else:
                    labels_list = list(selected_labels)
                    for row_start in range(0, len(labels_list), 3):
                        row_labels = labels_list[row_start:row_start + 3]
                        cols = st.columns(3)
                        for i, label in enumerate(row_labels):
                            key = PLOT_OPTIONS[label]
                            with cols[i]:
                                if st.button(
                                    label,
                                    key=f"btn_{key}",
                                    use_container_width=True,
                                ):
                                    st.session_state.expanded_plot = key
                                    st.rerun()
                                st.pyplot(plots[key], use_container_width=True)

        with tab_dot:
            dot_str = render_dot_string(aig_path, theme, rankdir, highlight_paths=highlight)
            st.code(dot_str, language="dot")

    except Exception as e:
        st.error(f"Error processing file: {e}")
    finally:
        if uploaded is not None and aig_path and os.path.exists(aig_path):
            os.unlink(aig_path)


if __name__ == "__main__":
    main()
