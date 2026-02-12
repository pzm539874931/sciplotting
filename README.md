# SciPlotGUI

A powerful, user-friendly GUI application for creating publication-ready scientific figures, inspired by GraphPad Prism.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-lightgrey.svg)

## Features

### Plot Types
- **Line plots** - Time series, continuous data
- **Scatter plots** - Correlation, distribution analysis
- **Bar charts** - Category comparisons
- **Grouped bar charts** - Multi-factor comparisons with sub-grouping
- **Error bar plots** - Mean ± SD/SEM/CI visualization
- **Histograms** - Distribution analysis
- **Box plots** - Statistical summaries
- **Violin plots** - Distribution shape visualization
- **Heatmaps** - Matrix data visualization
- **Area plots** - Cumulative data
- **Pie charts** - Proportional data

### Data Management
- **CSV/Excel import** - Load data from common formats
- **Clipboard paste** - Quick data entry from spreadsheets
- **Replicate grouping** - Prism-style automatic Mean/SD/SEM/CI calculation
- **Multiple data series** - Compare multiple datasets on one plot
- **Embedded data** - Project files include all data for portability

### Statistical Analysis
- **T-tests** - Two-group comparisons (paired/unpaired)
- **One-way ANOVA** - Multi-group comparisons with post-hoc tests
- **Significance brackets** - Automatic p-value annotation on plots
- **Post-hoc tests** - Tukey HSD for pairwise comparisons

### Curve Fitting
- **Linear regression** - y = ax + b
- **Polynomial fits** - Quadratic, cubic, quartic
- **Exponential models** - Growth, decay, double exponential
- **Sigmoidal curves** - 4PL, 5PL dose-response
- **Gaussian/Lorentzian** - Peak fitting
- **Custom equations** - Define your own models
- **Confidence bands** - 95% CI visualization

### Styling & Export
- **Journal presets** - Nature, Science, IEEE styles
- **SciencePlots integration** - Professional scientific aesthetics
- **Background customization** - Solid colors, gradients
- **Highlight zones** - Horizontal/vertical bands with labels
- **Multiple export formats** - PNG, SVG, PDF, TIFF at various DPIs
- **Template system** - Save and reuse plot configurations

### Project Management
- **Multi-figure tabs** - Work on multiple figures simultaneously
- **Project files (.sciplot)** - Save entire workspace with embedded data
- **Template library** - Built-in and custom templates

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/pzm539874931/sciplotting.git
cd sciplotting

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Dependencies
- PyQt6 - GUI framework
- matplotlib - Plotting engine
- numpy - Numerical operations
- scipy - Statistical functions
- pandas - Data handling (optional but recommended)
- lmfit - Curve fitting
- SciencePlots - Scientific plot styles (optional but recommended)

## Usage

### Quick Start

1. **Launch the application**
   ```bash
   python main.py
   ```

2. **Load your data**
   - Click "Load CSV" or "Load Excel" to import data
   - Or paste data directly from clipboard (Ctrl/Cmd+V in data panel)
   - Or use "Demo Data" to explore features

3. **Configure your plot**
   - Select plot type from the Config panel
   - Customize axes labels, title, colors
   - Choose a style preset (Nature, Science, IEEE, etc.)

4. **Add analysis** (optional)
   - Run statistical tests from the Statistics tab
   - Fit curves from the Fitting tab
   - Add highlight zones from the Zones tab

5. **Export your figure**
   - File → Export Figure
   - Choose format (PNG, SVG, PDF) and DPI

### Data Format

SciPlotGUI expects data in tabular format:

```csv
Time,Control,Treatment_A,Treatment_B
0,10.2,10.5,10.1
1,15.3,18.2,22.1
2,18.7,25.4,35.2
3,20.1,28.9,42.8
```

For replicate data, use multiple columns per condition:

```csv
Time,Control_1,Control_2,Control_3,Drug_1,Drug_2,Drug_3
0,10.2,9.8,10.5,10.1,10.3,9.9
1,15.3,14.8,15.9,18.2,17.5,18.8
```

### Templates

Save time with templates:

1. Configure your plot style
2. File → Save as Template
3. Give it a name and category
4. Reuse via File → Load Template

Built-in templates include:
- **Journal styles**: Nature, Science, IEEE
- **Chart types**: Scatter with Fit, Time Series, Statistical Box Plot
- **Color schemes**: Vibrant, Muted Academic, Dark Background

## Screenshots

*Coming soon*

## Project Structure

```
sciplotgui/
├── main.py              # Application entry point
├── core/
│   ├── plot_engine.py   # Matplotlib wrapper for plotting
│   ├── data_manager.py  # Data loading and processing
│   ├── stats_engine.py  # Statistical analysis
│   ├── fitting_engine.py # Curve fitting with lmfit
│   ├── zones_manager.py # Highlight zones/bands
│   ├── template_manager.py # Template save/load
│   └── project_manager.py # Project file handling
├── gui/
│   ├── main_window.py   # Main application window
│   ├── figure_tab.py    # Figure editor tab
│   ├── data_panel.py    # Data input panel
│   ├── config_panel.py  # Plot configuration
│   ├── stats_panel.py   # Statistics controls
│   ├── fitting_panel.py # Curve fitting controls
│   ├── zones_panel.py   # Highlight zones editor
│   └── canvas_widget.py # Matplotlib canvas
└── tests/
    └── test_*.py        # Unit tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/pzm539874931/sciplotting.git
cd sciplotting
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run tests
pytest tests/

# Run with debug output
python main.py --debug
```

### Coding Standards
- Follow PEP 8 style guidelines
- Add docstrings to all public functions
- Write tests for new features
- Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [SciencePlots](https://github.com/garrettj403/SciencePlots) - Scientific plotting styles
- [lmfit](https://lmfit.github.io/lmfit-py/) - Curve fitting library
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [matplotlib](https://matplotlib.org/) - Plotting library

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Support

- **Issues**: Report bugs via [GitHub Issues](https://github.com/pzm539874931/sciplotting/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/pzm539874931/sciplotting/discussions)

---

Made with ❤️ for the scientific community
