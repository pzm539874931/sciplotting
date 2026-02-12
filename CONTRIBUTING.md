# Contributing to SciPlotGUI

Thank you for your interest in contributing to SciPlotGUI! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all experience levels.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/pzm539874931/sciplotting/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)
   - Screenshots if applicable

### Suggesting Features

1. Check existing issues and discussions for similar ideas
2. Create a new issue with:
   - Feature description
   - Use case / motivation
   - Proposed implementation (if any)

### Submitting Code

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/sciplotting.git
   cd sciplotting
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Make your changes**
   - Write clean, readable code
   - Follow existing code style
   - Add docstrings to functions
   - Update tests as needed

5. **Run tests**
   ```bash
   pytest tests/
   ```

6. **Check code quality**
   ```bash
   flake8 core/ gui/
   black --check core/ gui/
   ```

7. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `style:` Code style (formatting)
   - `refactor:` Code refactoring
   - `test:` Adding tests
   - `chore:` Maintenance

8. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable/function names

### Documentation

- Add docstrings to all public functions/classes
- Update README.md for new features
- Add inline comments for complex logic

### Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Aim for good code coverage

### Architecture

```
core/           # Business logic (no GUI dependencies)
├── plot_engine.py      # Matplotlib wrapper
├── data_manager.py     # Data handling
├── stats_engine.py     # Statistics
├── fitting_engine.py   # Curve fitting
├── zones_manager.py    # Highlight zones
├── template_manager.py # Templates
└── project_manager.py  # Project files

gui/            # PyQt6 GUI components
├── main_window.py      # Main window
├── figure_tab.py       # Figure editor
├── data_panel.py       # Data input
├── config_panel.py     # Configuration
├── stats_panel.py      # Statistics UI
├── fitting_panel.py    # Fitting UI
├── zones_panel.py      # Zones UI
└── canvas_widget.py    # Matplotlib canvas

tests/          # Unit tests
```

### Adding New Plot Types

1. Add type to `PLOT_TYPES` in `core/plot_engine.py`
2. Implement drawing logic in `PlotEngine._draw()`
3. Add demo data in `DataManager.generate_demo_data()`
4. Update UI if special controls needed

### Adding Statistical Tests

1. Add test to `STAT_TESTS` in `core/stats_engine.py`
2. Implement in `StatsEngine.run_test()`
3. Handle visualization in `PlotEngine.draw_stats()`

### Adding Fitting Models

1. Add model to `FITTING_MODELS` in `core/fitting_engine.py`
2. Implement in `FittingEngine.fit()`
3. Update UI if special parameters needed

## Questions?

Feel free to ask questions in GitHub Discussions or open an issue.

Thank you for contributing! 🎉
