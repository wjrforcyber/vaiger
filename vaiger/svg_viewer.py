SVG_PAN_ZOOM_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
  #toolbar {{
    position: fixed; top: 8px; right: 8px; z-index: 100;
    display: flex; gap: 4px; flex-direction: column;
  }}
  #toolbar button {{
    width: 36px; height: 36px; font-size: 18px; border: 1px solid #ccc;
    border-radius: 6px; background: #fff; cursor: pointer; color: #333;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  }}
  #toolbar button:hover {{ background: #f0f0f0; }}
  #toolbar .label {{
    font-size: 10px; text-align: center; color: #666; margin-top: -2px;
  }}
  #zoom-level {{
    position: fixed; bottom: 8px; right: 8px; z-index: 100;
    font-size: 12px; color: #666; background: #fff; padding: 2px 8px;
    border: 1px solid #ccc; border-radius: 4px;
  }}
  #svg-container {{
    width: 100%; height: 100%;
  }}
  #svg-container svg {{
    width: 100%; height: 100%;
  }}
</style>
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
</head>
<body>
<div id="toolbar">
  <button id="btn-zoom-in" title="Zoom In">+</button>
  <button id="btn-zoom-out" title="Zoom Out">&minus;</button>
  <button id="btn-fit" title="Fit to Screen">&#x2922;</button>
  <button id="btn-center" title="Reset / Center">&#x21BA;</button>
</div>
<div id="zoom-level">100%</div>
<div id="svg-container">
{svg_content}
</div>
<script>
  var panZoom = null;
  function init() {{
    var svgEl = document.querySelector('#svg-container svg');
    if (!svgEl) return;
    svgEl.removeAttribute('width');
    svgEl.removeAttribute('height');
    panZoom = svgPanZoom(svgEl, {{
      zoomEnabled: true,
      controlIconsEnabled: false,
      fit: true,
      center: true,
      minZoom: 0.05,
      maxZoom: 50,
      zoomScaleSensitivity: 0.3,
      dblClickZoomEnabled: true,
      mouseWheelZoomEnabled: true,
      preventMouseEventsDefault: true,
      onZoom: function(scale) {{
        document.getElementById('zoom-level').textContent = Math.round(scale * 100) + '%';
      }},
      onPan: function() {{}}
    }});
  }}
  document.getElementById('btn-zoom-in').addEventListener('click', function() {{
    if (panZoom) panZoom.zoomIn();
  }});
  document.getElementById('btn-zoom-out').addEventListener('click', function() {{
    if (panZoom) panZoom.zoomOut();
  }});
  document.getElementById('btn-fit').addEventListener('click', function() {{
    if (panZoom) panZoom.fit(); if (panZoom) panZoom.center();
  }});
  document.getElementById('btn-center').addEventListener('click', function() {{
    if (panZoom) panZoom.resetZoom(); if (panZoom) panZoom.resetPan();
  }});
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', init);
  }} else {{
    init();
  }}
</script>
</body>
</html>
"""


def make_zoomable_svg_html(svg_content, height=800):
    html = SVG_PAN_ZOOM_TEMPLATE.format(svg_content=svg_content)
    return html, height
