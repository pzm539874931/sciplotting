"""
Statistical analysis engine — Prism-style significance testing.

Supports:
  - Unpaired / Paired / Welch t-test
  - Mann-Whitney U / Wilcoxon signed-rank (nonparametric)
  - One-way ANOVA + post-hoc (Tukey, Bonferroni, Dunnett-style, Holm)
  - Kruskal-Wallis + Dunn's post-hoc (nonparametric)
  - Automatic p-value → asterisk annotation

All results are returned as ComparisonResult objects that the PlotEngine
can render as significance brackets on bar/errorbar/box/violin charts.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from scipy import stats as sp

# ---------------------------------------------------------------------------
#  Thresholds (GraphPad style)
# ---------------------------------------------------------------------------
P_THRESHOLDS = [
    (0.0001, "****"),
    (0.001,  "***"),
    (0.01,   "**"),
    (0.05,   "*"),
]


def p_to_stars(p: float) -> str:
    """Convert p-value to asterisk string (Prism GraphPad style)."""
    for threshold, label in P_THRESHOLDS:
        if p < threshold:
            return label
    return "ns"


def p_to_display(p: float, mode: str = "stars") -> str:
    """
    Format p for display.
    mode: 'stars' | 'value' | 'both'
    """
    if mode == "stars":
        return p_to_stars(p)
    elif mode == "value":
        if p < 0.0001:
            return "p<0.0001"
        return f"p={p:.4f}"
    else:  # both
        stars = p_to_stars(p)
        if p < 0.0001:
            return f"{stars}\np<0.0001"
        return f"{stars}\np={p:.4f}"


# ---------------------------------------------------------------------------
#  Data structures
# ---------------------------------------------------------------------------

@dataclass
class ComparisonResult:
    """One pairwise comparison result."""
    group_a: int           # index of first group (0-based)
    group_b: int           # index of second group (0-based)
    label_a: str = ""
    label_b: str = ""
    p_value: float = 1.0
    stars: str = "ns"
    test_name: str = ""
    statistic: float = 0.0

    def display(self, mode: str = "stars") -> str:
        return p_to_display(self.p_value, mode)


@dataclass
class StatsResult:
    """Full statistical analysis result."""
    test_name: str = ""
    global_statistic: float = 0.0
    global_p: float = 1.0
    comparisons: list[ComparisonResult] = field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
#  Available test definitions
# ---------------------------------------------------------------------------

STAT_TESTS = [
    "(None)",
    "Unpaired t-test",
    "Paired t-test",
    "Welch's t-test",
    "Mann-Whitney U",
    "Wilcoxon signed-rank",
    "One-way ANOVA",
    "Kruskal-Wallis",
]

POSTHOC_METHODS = [
    "Tukey HSD",
    "Bonferroni",
    "Holm-Bonferroni",
    "Compare to control (Dunnett-like)",
]

COMPARE_MODES = [
    "All pairs",
    "Compare to control",
]

DISPLAY_MODES = [
    "stars",
    "value",
    "both",
]


# ---------------------------------------------------------------------------
#  Engine
# ---------------------------------------------------------------------------

class StatsEngine:
    """Runs statistical tests on grouped data."""

    @staticmethod
    def run(
        groups: list[np.ndarray],
        labels: list[str],
        test: str = "One-way ANOVA",
        posthoc: str = "Tukey HSD",
        compare_mode: str = "All pairs",
        control_index: int = 0,
        paired: bool = False,
    ) -> StatsResult:
        """
        Run a statistical test on two or more groups.

        Parameters
        ----------
        groups : list of 1-D arrays, each representing one group's data
        labels : list of group name strings
        test   : name from STAT_TESTS
        posthoc: name from POSTHOC_METHODS (for ANOVA / Kruskal)
        compare_mode : 'All pairs' or 'Compare to control'
        control_index: which group is the control (for Dunnett-like)

        Returns
        -------
        StatsResult with all pairwise comparisons
        """
        if test == "(None)" or len(groups) < 2:
            return StatsResult(test_name="(None)", summary="No test selected.")

        # Clean NaN
        groups = [g[~np.isnan(g)] for g in groups]
        groups = [g for g in groups if len(g) >= 2]
        if len(groups) < 2:
            return StatsResult(test_name=test, summary="Not enough valid data (n≥2) in each group.")

        # ---- Two-group tests ----
        if test in ("Unpaired t-test", "Paired t-test", "Welch's t-test",
                     "Mann-Whitney U", "Wilcoxon signed-rank"):
            return StatsEngine._two_group(groups[:2], labels[:2], test)

        # ---- Multi-group tests ----
        if test == "One-way ANOVA":
            return StatsEngine._anova(groups, labels, posthoc, compare_mode, control_index)
        if test == "Kruskal-Wallis":
            return StatsEngine._kruskal(groups, labels, posthoc, compare_mode, control_index)

        return StatsResult(test_name=test, summary=f"Unknown test: {test}")

    # ------------------------------------------------------------------
    #  Two-group tests
    # ------------------------------------------------------------------

    @staticmethod
    def _two_group(groups, labels, test) -> StatsResult:
        a, b = groups[0], groups[1]
        la, lb = (labels + ["A", "B"])[:2]

        if test == "Unpaired t-test":
            stat, p = sp.ttest_ind(a, b, equal_var=True)
            tname = "Unpaired t-test"
        elif test == "Paired t-test":
            n = min(len(a), len(b))
            stat, p = sp.ttest_rel(a[:n], b[:n])
            tname = "Paired t-test"
        elif test == "Welch's t-test":
            stat, p = sp.ttest_ind(a, b, equal_var=False)
            tname = "Welch's t-test"
        elif test == "Mann-Whitney U":
            stat, p = sp.mannwhitneyu(a, b, alternative="two-sided")
            tname = "Mann-Whitney U"
        elif test == "Wilcoxon signed-rank":
            n = min(len(a), len(b))
            stat, p = sp.wilcoxon(a[:n], b[:n])
            tname = "Wilcoxon signed-rank"
        else:
            return StatsResult(test_name=test, summary=f"Unknown test: {test}")

        comp = ComparisonResult(
            group_a=0, group_b=1,
            label_a=la, label_b=lb,
            p_value=float(p), stars=p_to_stars(float(p)),
            test_name=tname, statistic=float(stat),
        )
        summary = (f"{tname}: statistic={stat:.4f}, p={p:.6f} ({comp.stars})\n"
                   f"  {la} (n={len(a)}) vs {lb} (n={len(b)})")
        return StatsResult(
            test_name=tname,
            global_statistic=float(stat),
            global_p=float(p),
            comparisons=[comp],
            summary=summary,
        )

    # ------------------------------------------------------------------
    #  One-way ANOVA + post-hoc
    # ------------------------------------------------------------------

    @staticmethod
    def _anova(groups, labels, posthoc, compare_mode, control_index) -> StatsResult:
        stat_f, p_global = sp.f_oneway(*groups)
        result = StatsResult(
            test_name="One-way ANOVA",
            global_statistic=float(stat_f),
            global_p=float(p_global),
        )
        lines = [f"One-way ANOVA: F={stat_f:.4f}, p={p_global:.6f} ({p_to_stars(float(p_global))})"]
        lines.append(f"Groups: {', '.join(f'{l}(n={len(g)})' for l, g in zip(labels, groups))}")

        # Determine pairs
        pairs = StatsEngine._get_pairs(len(groups), compare_mode, control_index)

        # Post-hoc pairwise
        if posthoc == "Tukey HSD":
            result.comparisons = StatsEngine._tukey_posthoc(groups, labels, pairs)
        elif posthoc in ("Bonferroni", "Holm-Bonferroni"):
            result.comparisons = StatsEngine._bonferroni_posthoc(
                groups, labels, pairs, holm=(posthoc == "Holm-Bonferroni")
            )
        elif posthoc == "Compare to control (Dunnett-like)":
            ctrl_pairs = [(control_index, j) for j in range(len(groups)) if j != control_index]
            result.comparisons = StatsEngine._bonferroni_posthoc(
                groups, labels, ctrl_pairs, holm=False
            )
        else:
            result.comparisons = StatsEngine._tukey_posthoc(groups, labels, pairs)

        for c in result.comparisons:
            lines.append(f"  {c.label_a} vs {c.label_b}: p={c.p_value:.6f} ({c.stars})")
        result.summary = "\n".join(lines)
        return result

    @staticmethod
    def _tukey_posthoc(groups, labels, pairs) -> list[ComparisonResult]:
        """Tukey HSD via scipy."""
        try:
            from scipy.stats import tukey_hsd
            res = tukey_hsd(*groups)
            comps = []
            for i, j in pairs:
                p_val = float(res.pvalue[i][j])
                comps.append(ComparisonResult(
                    group_a=i, group_b=j,
                    label_a=labels[i], label_b=labels[j],
                    p_value=p_val, stars=p_to_stars(p_val),
                    test_name="Tukey HSD",
                    statistic=float(res.statistic[i][j]),
                ))
            return comps
        except (ImportError, AttributeError):
            # Fallback: pairwise t-tests with Bonferroni
            return StatsEngine._bonferroni_posthoc(groups, labels, pairs, holm=False)

    @staticmethod
    def _bonferroni_posthoc(groups, labels, pairs, holm=False) -> list[ComparisonResult]:
        """Pairwise t-tests with Bonferroni or Holm correction."""
        raw = []
        for i, j in pairs:
            stat, p = sp.ttest_ind(groups[i], groups[j], equal_var=False)
            raw.append((i, j, float(stat), float(p)))

        m = len(raw)
        if m == 0:
            return []

        if holm:
            # Holm-Bonferroni step-down
            sorted_raw = sorted(raw, key=lambda x: x[3])
            adjusted = []
            for rank, (i, j, stat, p) in enumerate(sorted_raw):
                adj_p = min(p * (m - rank), 1.0)
                adjusted.append((i, j, stat, adj_p))
        else:
            adjusted = [(i, j, stat, min(p * m, 1.0)) for i, j, stat, p in raw]

        comps = []
        for i, j, stat, p_adj in adjusted:
            comps.append(ComparisonResult(
                group_a=i, group_b=j,
                label_a=labels[i], label_b=labels[j],
                p_value=p_adj, stars=p_to_stars(p_adj),
                test_name="Bonferroni" if not holm else "Holm-Bonferroni",
                statistic=stat,
            ))
        # Re-sort by original pair order
        comps.sort(key=lambda c: (c.group_a, c.group_b))
        return comps

    # ------------------------------------------------------------------
    #  Kruskal-Wallis + Dunn's
    # ------------------------------------------------------------------

    @staticmethod
    def _kruskal(groups, labels, posthoc, compare_mode, control_index) -> StatsResult:
        stat_h, p_global = sp.kruskal(*groups)
        result = StatsResult(
            test_name="Kruskal-Wallis",
            global_statistic=float(stat_h),
            global_p=float(p_global),
        )
        lines = [f"Kruskal-Wallis: H={stat_h:.4f}, p={p_global:.6f} ({p_to_stars(float(p_global))})"]

        pairs = StatsEngine._get_pairs(len(groups), compare_mode, control_index)
        # Dunn's approximation: Mann-Whitney per pair with Bonferroni correction
        raw = []
        for i, j in pairs:
            stat, p = sp.mannwhitneyu(groups[i], groups[j], alternative="two-sided")
            raw.append((i, j, float(stat), float(p)))

        m = len(raw) if raw else 1
        comps = []
        for i, j, stat, p in raw:
            p_adj = min(p * m, 1.0)
            comps.append(ComparisonResult(
                group_a=i, group_b=j,
                label_a=labels[i], label_b=labels[j],
                p_value=p_adj, stars=p_to_stars(p_adj),
                test_name="Dunn's (Bonferroni)",
                statistic=stat,
            ))
            lines.append(f"  {labels[i]} vs {labels[j]}: p={p_adj:.6f} ({p_to_stars(p_adj)})")

        result.comparisons = comps
        result.summary = "\n".join(lines)
        return result

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_pairs(n: int, mode: str, control: int) -> list[tuple[int, int]]:
        if mode == "Compare to control":
            return [(control, j) for j in range(n) if j != control]
        else:
            return [(i, j) for i in range(n) for j in range(i + 1, n)]
