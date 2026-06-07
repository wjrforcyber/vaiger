# VAiger

Interactive viewer and analyzer for AIGER circuits (`.aag` / `.aig` files).

Built with Streamlit, NetworkX, and the [aiger](https://github.com/wjrforcyber/aiger) C library.

## Setup

```bash
# Clone with submodule
git clone --recurse-submodules https://github.com/<you>/vaiger.git
cd vaiger

# Build the aiger C tools
make -C aiger

# Create venv and install dependencies
python -m venv .env
source .env/bin/activate
pip install streamlit networkx pydot matplotlib seaborn pandas

# Run
streamlit run app.py
```

## Usage

1. Open the app — `streamlit run app.py`
2. Upload an `.aag` / `.aig` file, or pick an example from the sidebar
3. Browse the **Graph** tab (interactive SVG), **Statistics** tab (plots), or **DOT Source** tab


## Requirements

- Python 3.10+
- C compiler (to build the aiger tools)
- [Graphviz](https://graphviz.org/) installed and on `PATH`
