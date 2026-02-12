"""
Data manager - handles loading data from CSV/Excel/clipboard
and converting to the dataset format used by PlotEngine.

Supports Prism-style replicate grouping: multiple columns are treated
as replicates of the same condition, and Mean/SD/SEM/CI95 are auto-computed.
"""

import csv
import json
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import stats as sp_stats  # for CI; fallback below

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Error bar types (like Prism)
ERROR_BAR_TYPES = ["SD", "SEM", "95% CI", "Range"]
CENTRAL_TYPES = ["Mean", "Median"]


def _ci95(arr):
    """Return 95% CI half-width for array."""
    n = len(arr)
    if n < 2:
        return 0.0
    se = np.nanstd(arr, ddof=1) / np.sqrt(n)
    try:
        t_val = sp_stats.t.ppf(0.975, df=n - 1)
    except Exception:
        t_val = 1.96
    return se * t_val


class ReplicateGroup:
    """Defines a group of replicate columns that share one condition."""

    def __init__(self, label: str, columns: list[str],
                 central: str = "Mean", error_type: str = "SD"):
        self.label = label
        self.columns = columns          # list of column names (replicates)
        self.central = central          # "Mean" or "Median"
        self.error_type = error_type    # "SD", "SEM", "95% CI", "Range"

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "columns": self.columns,
            "central": self.central,
            "error_type": self.error_type,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReplicateGroup":
        return cls(
            label=d["label"],
            columns=d["columns"],
            central=d.get("central", "Mean"),
            error_type=d.get("error_type", "SD"),
        )


class DataManager:
    """Manages data loading, parsing, and conversion for plotting."""

    def __init__(self):
        self.raw_df = None  # pandas DataFrame if available
        self.datasets: list[dict] = []

    # ---- Loading ----

    def load_csv(self, path: str, delimiter: str = ",") -> list[str]:
        """Load CSV file, return column names."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if HAS_PANDAS:
            self.raw_df = pd.read_csv(p, delimiter=delimiter)
            return list(self.raw_df.columns)
        else:
            with open(p, newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader)
                data = list(reader)
            self.raw_df = {h: [] for h in headers}
            for row in data:
                for i, h in enumerate(headers):
                    val = row[i] if i < len(row) else ""
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                    self.raw_df[h].append(val)
            return headers

    def load_excel(self, path: str, sheet_name=0) -> list[str]:
        if not HAS_PANDAS:
            raise ImportError("pandas is required to load Excel files.")
        self.raw_df = pd.read_excel(path, sheet_name=sheet_name)
        return list(self.raw_df.columns)

    def load_from_text(self, text: str, delimiter: str = "\t") -> list[str]:
        lines = text.strip().split("\n")
        if not lines:
            return []
        if HAS_PANDAS:
            import io
            self.raw_df = pd.read_csv(io.StringIO(text), delimiter=delimiter)
            return list(self.raw_df.columns)
        else:
            headers = lines[0].split(delimiter)
            self.raw_df = {h.strip(): [] for h in headers}
            for line in lines[1:]:
                parts = line.split(delimiter)
                for i, h in enumerate(headers):
                    h = h.strip()
                    val = parts[i].strip() if i < len(parts) else ""
                    try:
                        val = float(val)
                    except ValueError:
                        pass
                    self.raw_df[h].append(val)
            return [h.strip() for h in headers]

    # ---- Column access ----

    def get_column(self, col_name: str, as_float: bool = True) -> np.ndarray:
        if HAS_PANDAS and hasattr(self.raw_df, "columns"):
            if as_float:
                try:
                    return pd.to_numeric(self.raw_df[col_name], errors="coerce").to_numpy(dtype=float)
                except Exception:
                    return self.raw_df[col_name].to_numpy()
            return self.raw_df[col_name].to_numpy()
        elif isinstance(self.raw_df, dict):
            if as_float:
                try:
                    return np.array(self.raw_df[col_name], dtype=float)
                except (ValueError, TypeError):
                    return np.array(self.raw_df[col_name])
            return np.array(self.raw_df[col_name])
        raise ValueError(f"Column '{col_name}' not found.")

    def get_columns(self) -> list[str]:
        if self.raw_df is None:
            return []
        if HAS_PANDAS and hasattr(self.raw_df, "columns"):
            return list(self.raw_df.columns)
        elif isinstance(self.raw_df, dict):
            return list(self.raw_df.keys())
        return []

    def get_row_count(self) -> int:
        if self.raw_df is None:
            return 0
        if HAS_PANDAS and hasattr(self.raw_df, "shape"):
            return self.raw_df.shape[0]
        elif isinstance(self.raw_df, dict):
            first_key = next(iter(self.raw_df))
            return len(self.raw_df[first_key])
        return 0

    # ---- Replicate computation (Prism-style) ----

    def compute_replicate_stats(self, group: ReplicateGroup, x_col: Optional[str] = None) -> dict:
        """
        Given a ReplicateGroup, compute central tendency + error from replicate columns.

        Returns a dataset dict with keys:
          x, y (central), yerr, label, raw_points (list of arrays for scatter overlay)
        """
        arrays = []
        for c in group.columns:
            arrays.append(self.get_column(c))

        # Stack: shape (n_replicates, n_rows)
        stacked = np.vstack(arrays)  # (n_rep, n_rows)

        if group.central == "Mean":
            central_vals = np.nanmean(stacked, axis=0)
        else:
            central_vals = np.nanmedian(stacked, axis=0)

        if group.error_type == "SD":
            err_vals = np.nanstd(stacked, axis=0, ddof=1)
        elif group.error_type == "SEM":
            n_rep = np.sum(~np.isnan(stacked), axis=0)
            err_vals = np.nanstd(stacked, axis=0, ddof=1) / np.sqrt(n_rep)
        elif group.error_type == "95% CI":
            err_vals = np.array([_ci95(stacked[:, i]) for i in range(stacked.shape[1])])
        elif group.error_type == "Range":
            err_low = central_vals - np.nanmin(stacked, axis=0)
            err_high = np.nanmax(stacked, axis=0) - central_vals
            err_vals = np.vstack([err_low, err_high])  # asymmetric
        else:
            err_vals = np.nanstd(stacked, axis=0, ddof=1)

        if x_col:
            x_raw = self.get_column(x_col, as_float=False)
            # Try numeric first; if not, use as labels
            try:
                x = np.array(x_raw, dtype=float).tolist()
                x_labels = None
            except (ValueError, TypeError):
                x_labels = [str(v) for v in x_raw]
                x = list(range(len(central_vals)))
        else:
            x = list(range(len(central_vals)))
            x_labels = None

        ds = {
            "x": x,
            "y": central_vals.tolist(),
            "label": group.label,
            "raw_points": [a.tolist() for a in arrays],  # individual replicates
        }
        if x_labels is not None:
            ds["x_labels"] = x_labels

        if group.error_type == "Range":
            ds["yerr"] = err_vals.tolist()  # [[low...], [high...]]
        else:
            ds["yerr"] = err_vals.tolist()

        return ds

    # ---- Simple dataset building (original) ----

    def build_dataset(self, x_col: Optional[str], y_col: str, label: str = "",
                      yerr_col: Optional[str] = None, xerr_col: Optional[str] = None) -> dict:
        ds = {}
        if x_col:
            x_raw = self.get_column(x_col, as_float=False)
            try:
                ds["x"] = np.array(x_raw, dtype=float).tolist()
            except (ValueError, TypeError):
                ds["x_labels"] = [str(v) for v in x_raw]
                ds["x"] = list(range(len(x_raw)))
        else:
            ds["x"] = list(range(self.get_row_count()))
        ds["y"] = self.get_column(y_col).tolist()
        ds["label"] = label or y_col
        if yerr_col:
            ds["yerr"] = self.get_column(yerr_col).tolist()
        if xerr_col:
            ds["xerr"] = self.get_column(xerr_col).tolist()
        return ds

    def build_datasets_from_selections(self, selections: list[dict]) -> list[dict]:
        results = []
        for sel in selections:
            # Check if this is a replicate selection
            if sel.get("replicate_cols"):
                group = ReplicateGroup(
                    label=sel.get("label", ""),
                    columns=sel["replicate_cols"],
                    central=sel.get("central", "Mean"),
                    error_type=sel.get("error_type", "SD"),
                )
                ds = self.compute_replicate_stats(group, x_col=sel.get("x_col"))
                results.append(ds)
            else:
                ds = self.build_dataset(
                    x_col=sel.get("x_col"),
                    y_col=sel["y_col"],
                    label=sel.get("label", ""),
                    yerr_col=sel.get("yerr_col"),
                    xerr_col=sel.get("xerr_col"),
                )
                results.append(ds)
        return results

    # ---- Data persistence (for project files) ----

    def export_raw_data(self) -> dict:
        """
        Export raw data as a JSON-serializable dict for project persistence.

        Returns:
            Dict with 'columns' list and 'data' dict mapping column names to values.
        """
        if self.raw_df is None:
            return {"columns": [], "data": {}}

        columns = self.get_columns()
        data = {}

        for col in columns:
            col_data = self.get_column(col, as_float=False)
            # Convert numpy types to Python types for JSON serialization
            values = []
            for val in col_data:
                if isinstance(val, (np.floating, float)):
                    if np.isnan(val):
                        values.append(None)
                    else:
                        values.append(float(val))
                elif isinstance(val, (np.integer, int)):
                    values.append(int(val))
                elif isinstance(val, np.ndarray):
                    values.append(val.tolist())
                else:
                    values.append(val)  # Keep strings as-is
            data[col] = values

        return {
            "columns": columns,
            "data": data,
        }

    def import_raw_data(self, export_data: dict) -> list[str]:
        """
        Import raw data from a project file dict.

        Args:
            export_data: Dict with 'columns' and 'data' keys

        Returns:
            List of column names
        """
        columns = export_data.get("columns", [])
        data = export_data.get("data", {})

        if not columns or not data:
            return []

        if HAS_PANDAS:
            import pandas as pd
            self.raw_df = pd.DataFrame(data)
        else:
            # Dict-based storage for non-pandas fallback
            self.raw_df = data.copy()

        return columns

    def has_data(self) -> bool:
        """Check if data is loaded."""
        return self.raw_df is not None and len(self.get_columns()) > 0

    # ---- Demo data ----

    @staticmethod
    def generate_demo_data(plot_type: str = "line") -> list[dict]:
        x = np.linspace(0, 2 * np.pi, 50)
        if plot_type == "line":
            return [
                {"x": x.tolist(), "y": np.sin(x).tolist(), "label": "sin(x)"},
                {"x": x.tolist(), "y": np.cos(x).tolist(), "label": "cos(x)"},
            ]
        elif plot_type == "scatter":
            rng = np.random.default_rng(42)
            return [
                {"x": (x + rng.normal(0, 0.1, len(x))).tolist(),
                 "y": (np.sin(x) + rng.normal(0, 0.15, len(x))).tolist(), "label": "Data A"},
                {"x": (x + rng.normal(0, 0.1, len(x))).tolist(),
                 "y": (np.cos(x) + rng.normal(0, 0.15, len(x))).tolist(), "label": "Data B"},
            ]
        elif plot_type == "bar":
            return [
                {"x": [1, 2, 3, 4, 5], "y": [23, 45, 56, 78, 32],
                 "x_labels": ["A", "B", "C", "D", "E"], "label": "Group 1"},
                {"x": [1, 2, 3, 4, 5], "y": [30, 38, 62, 70, 45],
                 "x_labels": ["A", "B", "C", "D", "E"], "label": "Group 2"},
            ]
        elif plot_type == "grouped_bar":
            # Grouped bar: Primary groups (x) with sub-groups (series)
            # Example: Timepoints (Day 1, Day 3, Day 7) with treatments (Control, Drug A, Drug B)
            return [
                {"x": [1, 2, 3], "y": [12.5, 18.3, 22.1],
                 "yerr": [1.2, 1.5, 1.8],
                 "x_labels": ["Day 1", "Day 3", "Day 7"], "label": "Control"},
                {"x": [1, 2, 3], "y": [15.2, 28.5, 45.3],
                 "yerr": [1.8, 2.1, 3.2],
                 "x_labels": ["Day 1", "Day 3", "Day 7"], "label": "Drug A"},
                {"x": [1, 2, 3], "y": [13.8, 35.2, 52.8],
                 "yerr": [1.4, 2.8, 4.1],
                 "x_labels": ["Day 1", "Day 3", "Day 7"], "label": "Drug B"},
            ]
        elif plot_type == "errorbar":
            rng = np.random.default_rng(42)
            # Demo replicate-style data with raw_points
            x_vals = list(range(1, 6))
            means = [23.5, 45.2, 56.1, 78.3, 32.0]
            sds = [3.2, 4.1, 5.5, 6.2, 3.8]
            raw = []
            for m, s in zip(means, sds):
                raw.append(rng.normal(m, s, 5).tolist())
            return [
                {"x": x_vals, "y": means, "yerr": sds,
                 "x_labels": ["A", "B", "C", "D", "E"],
                 "raw_points": raw, "label": "Measurement (n=5)"}
            ]
        elif plot_type in ("hist", "box", "violin"):
            rng = np.random.default_rng(42)
            return [
                {"x": [], "y": rng.normal(0, 1, 200).tolist(), "label": "Normal(0,1)"},
                {"x": [], "y": rng.normal(2, 1.5, 200).tolist(), "label": "Normal(2,1.5)"},
            ]
        elif plot_type == "heatmap":
            rng = np.random.default_rng(42)
            z = rng.random((10, 10))
            return [{"x": [], "y": [], "z": z.tolist(), "label": "Heatmap"}]
        elif plot_type == "area":
            return [
                {"x": x.tolist(), "y": np.abs(np.sin(x)).tolist(), "label": "Area A"},
                {"x": x.tolist(), "y": np.abs(np.cos(x)).tolist(), "label": "Area B"},
            ]
        elif plot_type == "pie":
            return [
                {"x": ["Cat A", "Cat B", "Cat C", "Cat D"],
                 "y": [35, 25, 22, 18],
                 "x_labels": ["Cat A", "Cat B", "Cat C", "Cat D"],
                 "label": "Distribution"},
            ]
        return [{"x": x.tolist(), "y": np.sin(x).tolist(), "label": "sin(x)"}]
