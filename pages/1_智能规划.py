"""Smart planning page.

The original planner remains in smart_nav_app.py.  This page keeps the
calculation and Folium interaction logic untouched while allowing Streamlit's
multipage navigation to present it as one module in a product-style app.
"""

from __future__ import annotations

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[1] / "smart_nav_app.py"), run_name="__main__")
