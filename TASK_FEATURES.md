# SciPlotting Feature Implementation Task

You are working on SciPlotting, a PyQt6-based academic figure maker at `C:\Users\User\clawd\sciplotting_dev`.

## Architecture Overview
- `core/` — engines (plot_engine.py, data_manager.py, stats_engine.py, fitting_engine.py, zones_manager.py, template_manager.py, project_manager.py)
- `gui/` — PyQt6 panels (main_window.py, figure_tab.py, config_panel.py, data_panel.py, data_table_widget.py, stats_panel.py, fitting_panel.py, zones_panel.py, canvas_widget.py, layout_composer.py, batch_dialog.py, projects_dialog.py)
- Uses matplotlib for rendering, scienceplots for academic styles
- Each figure tab is self-contained with its own data/config/stats/fitting/zones

## Features to Implement

### FEATURE 1: Data Table Right-Click Context Menu
**File:** `gui/data_table_widget.py`
- Add right-click context menu to the data table with:
  - Copy selected cells (Ctrl+C)
  - Paste cells (Ctrl+V) — parse tab/comma-separated clipboard data
  - Insert Row Above / Insert Row Below
  - Insert Column Left / Insert Column Right
  - Delete Selected Rows
  - Delete Selected Columns
  - Sort Column (Ascending / Descending)
  - Clear Selection
- Also support Ctrl+V paste from Excel/Prism (tab-separated values) directly into the table
- If pasting more data than current table size, auto-expand rows/columns

### FEATURE 2: Interactive Canvas (Zoom/Pan/Tooltip)
**Files:** `gui/canvas_widget.py`, `gui/figure_tab.py`
- Add a toolbar toggle button "Interactive Mode" to switch between static preview and interactive matplotlib canvas
- When interactive: use matplotlib's NavigationToolbar2QT for zoom/pan
- Add mouse hover tooltip showing (x, y) coordinates of nearest data point
- Double-click to reset view to original limits
- When exporting, always use the full non-zoomed figure

### FEATURE 3: Color Palette Picker + Per-Series Color
**Files:** `gui/config_panel.py`, `gui/data_panel.py`, `core/plot_engine.py`
- Add a "Color Palette" dropdown in config_panel with academic palettes:
  - Default (matplotlib), Nature, Science, Prism, Colorblind-safe (e.g. Wong), Pastel, Bright, Muted
  - Define these as lists of hex colors
- Add a per-series color picker button in each DataSeriesWidget (data_panel.py)
  - When set, overrides the palette color for that series
  - Include a "Reset to palette" option
- Pass custom colors through to plot_engine.py render()
- Store per-series colors in dataset dict as "custom_color" key

### FEATURE 4: Enhanced Data Import
**Files:** `gui/data_panel.py`, `gui/main_window.py`, `gui/data_table_widget.py`
- Add Excel (.xlsx) import support using openpyxl (with sheet selection dialog if multiple sheets)
- Add drag-and-drop file support on the data panel and main window (accept .csv, .xlsx, .tsv, .txt)
- Add clipboard paste button in data panel toolbar that reads clipboard as tab-separated data
- Add "Recent Files" submenu in File menu (store last 10 files in QSettings)
- When importing Excel, show a sheet selector if workbook has multiple sheets

### FEATURE 5: Annotations Tool
**Files:** new `core/annotations_manager.py`, new `gui/annotations_panel.py`, `gui/figure_tab.py`, `core/plot_engine.py`
- Create an Annotations tab in the right panel
- Support annotation types:
  - **Text**: label text, position (x, y), font size, color, rotation, bbox style
  - **Arrow**: start (x,y) → end (x,y), arrow style, color, width
  - **Reference Line**: horizontal or vertical, value, color, linestyle, width, label
- Each annotation is a dict stored in a list
- Add/remove/edit annotations in the panel
- PlotEngine draws annotations after main plot
- Include presets: "Threshold Line", "Peak Label", "Region Label"
- Store in project save/load

### FEATURE 6: Dual Y-Axis Support
**Files:** `gui/config_panel.py`, `gui/data_panel.py`, `core/plot_engine.py`
- Add "Y Axis" selector per series in DataSeriesWidget: "Left (Y1)" or "Right (Y2)"
- In config_panel add:
  - Y2 label text field
  - Y2 axis limits (min/max)
  - Y2 log scale toggle
- In plot_engine, when any dataset uses Y2:
  - Create twin axis via ax.twinx()
  - Plot those datasets on the right axis
  - Set independent labels/limits/scale
- Handle legend merging from both axes

### FEATURE 7: Data Transforms
**Files:** new `gui/transform_dialog.py`, `gui/data_panel.py`, `core/data_manager.py`
- Add a "Transform" button in data panel
- Opens a dialog with transform options:
  - **Normalize**: 0-1 range, Z-score, % of max, % of control (select control column)
  - **Math**: Log10, Ln, Square root, Reciprocal
  - **Relative**: Fold change vs control, Subtract baseline, Percent change
- Apply transform to selected columns, creating new columns with suffix (e.g. "Y1_normalized")
- Preview before applying (show before/after in a small table)
- Transforms are non-destructive (original data kept)

### FEATURE 8: Export Enhancements
**Files:** `gui/main_window.py`, `gui/figure_tab.py`, `core/plot_engine.py`
- Add "Copy to Clipboard" button in toolbar + Ctrl+C shortcut (when not in table)
  - Copies current figure as image to system clipboard
- Add transparent background option in export dialog
- Add custom DPI spinner in export dialog (100-1200)
- Add "Copy to Clipboard" in right-click context menu of canvas

## Implementation Notes
- All new panels should follow the existing pattern: QGroupBox sections, pyqtSignal for changes
- New features should be included in project save/load (ProjectManager.figure_state_from_tab)
- Use existing color_changed / data_changed / config_changed signal patterns
- Keep imports lazy where possible (openpyxl may not be installed)
- Add sensible defaults so existing projects still load
- Test that the app still launches after changes

## Order of Implementation
1. Feature 1 (data table context menu) — foundation for data editing
2. Feature 4 (enhanced import) — data input improvement
3. Feature 3 (color palette) — visual customization
4. Feature 8 (export enhancements) — output improvement
5. Feature 2 (interactive canvas) — viewing improvement
6. Feature 7 (data transforms) — data processing
7. Feature 5 (annotations) — plot decoration
8. Feature 6 (dual Y-axis) — advanced plotting
