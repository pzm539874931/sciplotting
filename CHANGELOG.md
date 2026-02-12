# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-12

### Added
- Initial release with full feature set
- **Plot Types**
  - Line, scatter, bar, grouped bar, error bar plots
  - Histogram, box, violin plots
  - Heatmap, area, pie charts
- **Data Management**
  - CSV and Excel file import
  - Clipboard paste support
  - Prism-style replicate grouping with automatic Mean/SD/SEM/CI
  - Multiple data series support
  - Embedded data in project files
- **Statistical Analysis**
  - Unpaired and paired t-tests
  - One-way ANOVA with Tukey HSD post-hoc
  - Automatic significance brackets on plots
- **Curve Fitting**
  - Linear and polynomial regression
  - Exponential growth/decay models
  - Sigmoidal dose-response (4PL, 5PL)
  - Gaussian and Lorentzian peak fitting
  - Custom equation support
  - 95% confidence band visualization
- **Styling**
  - Journal style presets (Nature, Science, IEEE)
  - SciencePlots integration
  - Figure and plot area background colors
  - Gradient background support
  - Highlight zones (horizontal, vertical, rectangular)
- **Export**
  - PNG, SVG, PDF, TIFF formats
  - Multiple DPI options (150, 300, 600)
- **Project Management**
  - Multi-figure tabs
  - Project save/load (.sciplot files)
  - Template library with built-in and custom templates

### Technical
- PyQt6-based GUI
- matplotlib plotting engine
- lmfit curve fitting
- scipy statistics
- pandas data handling

## [Unreleased]

### Planned
- Layout composer for multi-panel figures
- More statistical tests (two-way ANOVA, chi-square)
- Additional curve fitting models
- Figure annotation tools (text, arrows, shapes)
- Dark mode UI theme
- Plugin system for custom extensions
