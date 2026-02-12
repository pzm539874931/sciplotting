"""
Curve fitting engine using lmfit for scientific data analysis.

Provides common fitting models: Linear, Polynomial, Exponential, Gaussian, etc.
Returns fit results with parameters, uncertainties, R², and fitted curve data.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

try:
    import lmfit
    from lmfit import models as lm_models
    HAS_LMFIT = True
except ImportError:
    HAS_LMFIT = False

from scipy import stats as sp_stats
from scipy.optimize import curve_fit


# Available fitting models
FITTING_MODELS = {
    "(None)": None,
    "Linear": "linear",
    "Quadratic": "quadratic",
    "Polynomial (3rd)": "poly3",
    "Polynomial (4th)": "poly4",
    "Exponential Decay": "exp_decay",
    "Exponential Growth": "exp_growth",
    "Gaussian": "gaussian",
    "Lorentzian": "lorentzian",
    "Sigmoidal (Logistic)": "sigmoid",
    "Power Law": "power",
    "Logarithmic": "logarithmic",
    "Michaelis-Menten": "michaelis",
    "Hill Equation": "hill",
    "Dose-Response (4PL)": "dose_response_4pl",
}


@dataclass
class FitParameter:
    """A single fitted parameter with uncertainty."""
    name: str
    value: float
    stderr: Optional[float] = None

    def __str__(self):
        if self.stderr is not None:
            return f"{self.name} = {self.value:.6g} ± {self.stderr:.3g}"
        return f"{self.name} = {self.value:.6g}"


@dataclass
class FitResult:
    """Result of a curve fit operation."""
    success: bool = False
    model_name: str = ""
    equation: str = ""
    parameters: list = field(default_factory=list)
    r_squared: float = 0.0
    adj_r_squared: float = 0.0
    rmse: float = 0.0
    aic: float = 0.0
    bic: float = 0.0
    x_fit: list = field(default_factory=list)
    y_fit: list = field(default_factory=list)
    residuals: list = field(default_factory=list)
    message: str = ""

    def summary(self) -> str:
        """Generate a text summary of the fit results."""
        if not self.success:
            return f"Fit failed: {self.message}"

        lines = [
            f"Model: {self.model_name}",
            f"Equation: {self.equation}",
            "",
            "Parameters:",
        ]
        for p in self.parameters:
            lines.append(f"  {p}")
        lines.extend([
            "",
            f"R² = {self.r_squared:.6f}",
            f"Adjusted R² = {self.adj_r_squared:.6f}",
            f"RMSE = {self.rmse:.6g}",
            f"AIC = {self.aic:.2f}",
            f"BIC = {self.bic:.2f}",
        ])
        return "\n".join(lines)


class FittingEngine:
    """Engine for performing curve fits on data."""

    @staticmethod
    def fit(x: np.ndarray, y: np.ndarray, model_key: str,
            weights: Optional[np.ndarray] = None,
            x_range: Optional[tuple] = None) -> FitResult:
        """
        Fit data to the specified model.

        Args:
            x: X data (independent variable)
            y: Y data (dependent variable)
            model_key: Key from FITTING_MODELS dict
            weights: Optional weights for weighted least squares
            x_range: Optional (min, max) for fit curve extrapolation

        Returns:
            FitResult with parameters, statistics, and fitted curve
        """
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)

        # Remove NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        x = x[mask]
        y = y[mask]

        if len(x) < 2:
            return FitResult(success=False, message="Not enough data points")

        model_type = FITTING_MODELS.get(model_key)
        if model_type is None:
            return FitResult(success=False, message="No model selected")

        # Generate x values for fitted curve
        if x_range:
            x_fit = np.linspace(x_range[0], x_range[1], 200)
        else:
            x_min, x_max = x.min(), x.max()
            margin = (x_max - x_min) * 0.05
            x_fit = np.linspace(x_min - margin, x_max + margin, 200)

        try:
            if HAS_LMFIT:
                return FittingEngine._fit_lmfit(x, y, model_type, x_fit, weights)
            else:
                return FittingEngine._fit_scipy(x, y, model_type, x_fit, weights)
        except Exception as e:
            return FitResult(success=False, message=str(e))

    @staticmethod
    def _fit_lmfit(x, y, model_type, x_fit, weights) -> FitResult:
        """Fit using lmfit library (preferred)."""
        result = FitResult()

        # Create model based on type
        if model_type == "linear":
            model = lm_models.LinearModel()
            result.model_name = "Linear"
            result.equation = "y = slope·x + intercept"
        elif model_type == "quadratic":
            model = lm_models.QuadraticModel()
            result.model_name = "Quadratic"
            result.equation = "y = a·x² + b·x + c"
        elif model_type == "poly3":
            model = lm_models.PolynomialModel(degree=3)
            result.model_name = "Polynomial (3rd degree)"
            result.equation = "y = c3·x³ + c2·x² + c1·x + c0"
        elif model_type == "poly4":
            model = lm_models.PolynomialModel(degree=4)
            result.model_name = "Polynomial (4th degree)"
            result.equation = "y = c4·x⁴ + c3·x³ + c2·x² + c1·x + c0"
        elif model_type == "exp_decay":
            model = lm_models.ExponentialModel(prefix="")
            result.model_name = "Exponential Decay"
            result.equation = "y = amplitude · exp(-x/decay)"
        elif model_type == "exp_growth":
            # Custom exponential growth
            model = lmfit.Model(lambda x, a, k, c: a * np.exp(k * x) + c)
            result.model_name = "Exponential Growth"
            result.equation = "y = a · exp(k·x) + c"
        elif model_type == "gaussian":
            model = lm_models.GaussianModel()
            result.model_name = "Gaussian"
            result.equation = "y = (amplitude/(σ√(2π))) · exp(-(x-center)²/(2σ²))"
        elif model_type == "lorentzian":
            model = lm_models.LorentzianModel()
            result.model_name = "Lorentzian"
            result.equation = "y = (amplitude/π) · [σ / ((x-center)² + σ²)]"
        elif model_type == "sigmoid":
            model = lmfit.Model(lambda x, L, k, x0, b: L / (1 + np.exp(-k * (x - x0))) + b)
            result.model_name = "Sigmoidal (Logistic)"
            result.equation = "y = L / (1 + exp(-k·(x-x₀))) + b"
        elif model_type == "power":
            model = lm_models.PowerLawModel()
            result.model_name = "Power Law"
            result.equation = "y = amplitude · x^exponent"
        elif model_type == "logarithmic":
            model = lmfit.Model(lambda x, a, b: a * np.log(x) + b)
            result.model_name = "Logarithmic"
            result.equation = "y = a · ln(x) + b"
        elif model_type == "michaelis":
            model = lmfit.Model(lambda x, Vmax, Km: (Vmax * x) / (Km + x))
            result.model_name = "Michaelis-Menten"
            result.equation = "y = Vmax · x / (Km + x)"
        elif model_type == "hill":
            model = lmfit.Model(lambda x, Vmax, Kd, n: (Vmax * x**n) / (Kd**n + x**n))
            result.model_name = "Hill Equation"
            result.equation = "y = Vmax · xⁿ / (Kd^n + xⁿ)"
        elif model_type == "dose_response_4pl":
            model = lmfit.Model(
                lambda x, bottom, top, ec50, hill_slope:
                bottom + (top - bottom) / (1 + (ec50 / x)**hill_slope)
            )
            result.model_name = "4-Parameter Logistic (Dose-Response)"
            result.equation = "y = Bottom + (Top-Bottom) / (1 + (EC50/x)^HillSlope)"
        else:
            return FitResult(success=False, message=f"Unknown model: {model_type}")

        # Set up initial parameters with guesses
        try:
            params = model.guess(y, x=x)
        except (NotImplementedError, AttributeError):
            params = model.make_params()
            # Set reasonable initial guesses for custom models
            FittingEngine._set_initial_params(params, x, y, model_type)

        # Perform the fit
        fit_result = model.fit(y, params, x=x, weights=weights, nan_policy='omit')

        if not fit_result.success:
            return FitResult(success=False, message=fit_result.message or "Fit did not converge")

        # Extract parameters
        for name, param in fit_result.params.items():
            result.parameters.append(FitParameter(
                name=name,
                value=param.value,
                stderr=param.stderr
            ))

        # Calculate statistics
        y_pred = fit_result.best_fit
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        n = len(y)
        p = len([p for p in fit_result.params.values() if p.vary])

        result.r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        result.adj_r_squared = 1 - (1 - result.r_squared) * (n - 1) / (n - p - 1) if n > p + 1 else 0
        result.rmse = np.sqrt(ss_res / n)
        result.aic = fit_result.aic if hasattr(fit_result, 'aic') else n * np.log(ss_res / n) + 2 * p
        result.bic = fit_result.bic if hasattr(fit_result, 'bic') else n * np.log(ss_res / n) + p * np.log(n)

        # Generate fitted curve
        result.x_fit = x_fit.tolist()
        result.y_fit = fit_result.eval(x=x_fit).tolist()
        result.residuals = (y - y_pred).tolist()
        result.success = True

        return result

    @staticmethod
    def _fit_scipy(x, y, model_type, x_fit, weights) -> FitResult:
        """Fallback fitting using scipy.optimize.curve_fit."""
        result = FitResult()

        # Define model functions
        def linear(x, m, b):
            return m * x + b

        def quadratic(x, a, b, c):
            return a * x**2 + b * x + c

        def poly3(x, c3, c2, c1, c0):
            return c3 * x**3 + c2 * x**2 + c1 * x + c0

        def exp_decay(x, a, tau):
            return a * np.exp(-x / tau)

        def gaussian(x, amp, center, sigma):
            return amp * np.exp(-(x - center)**2 / (2 * sigma**2))

        # Select function
        funcs = {
            "linear": (linear, ["slope", "intercept"], "y = slope·x + intercept", "Linear"),
            "quadratic": (quadratic, ["a", "b", "c"], "y = a·x² + b·x + c", "Quadratic"),
            "poly3": (poly3, ["c3", "c2", "c1", "c0"], "y = c3·x³ + c2·x² + c1·x + c0", "Polynomial (3rd)"),
            "exp_decay": (exp_decay, ["amplitude", "decay"], "y = amplitude · exp(-x/decay)", "Exponential Decay"),
            "gaussian": (gaussian, ["amplitude", "center", "sigma"], "y = A·exp(-(x-μ)²/(2σ²))", "Gaussian"),
        }

        if model_type not in funcs:
            return FitResult(success=False, message=f"Model {model_type} not available without lmfit")

        func, param_names, equation, model_name = funcs[model_type]
        result.equation = equation
        result.model_name = model_name

        # Fit
        sigma = 1.0 / weights if weights is not None else None
        popt, pcov = curve_fit(func, x, y, sigma=sigma, maxfev=5000)
        perr = np.sqrt(np.diag(pcov))

        # Extract parameters
        for name, val, err in zip(param_names, popt, perr):
            result.parameters.append(FitParameter(name=name, value=val, stderr=err))

        # Statistics
        y_pred = func(x, *popt)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        n = len(y)
        p = len(popt)

        result.r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        result.adj_r_squared = 1 - (1 - result.r_squared) * (n - 1) / (n - p - 1) if n > p + 1 else 0
        result.rmse = np.sqrt(ss_res / n)
        result.aic = n * np.log(ss_res / n) + 2 * p
        result.bic = n * np.log(ss_res / n) + p * np.log(n)

        result.x_fit = x_fit.tolist()
        result.y_fit = func(x_fit, *popt).tolist()
        result.residuals = (y - y_pred).tolist()
        result.success = True

        return result

    @staticmethod
    def _set_initial_params(params, x, y, model_type):
        """Set reasonable initial parameter values for custom models."""
        y_range = y.max() - y.min()
        x_range = x.max() - x.min()
        x_mid = (x.max() + x.min()) / 2

        if model_type == "exp_growth":
            params["a"].set(value=y.min(), min=0)
            params["k"].set(value=0.1)
            params["c"].set(value=0)
        elif model_type == "sigmoid":
            params["L"].set(value=y_range, min=0)
            params["k"].set(value=1.0)
            params["x0"].set(value=x_mid)
            params["b"].set(value=y.min())
        elif model_type == "logarithmic":
            params["a"].set(value=y_range / np.log(x.max() / x.min()) if x.min() > 0 else 1)
            params["b"].set(value=y.min())
        elif model_type == "michaelis":
            params["Vmax"].set(value=y.max(), min=0)
            params["Km"].set(value=x_mid, min=0)
        elif model_type == "hill":
            params["Vmax"].set(value=y.max(), min=0)
            params["Kd"].set(value=x_mid, min=0)
            params["n"].set(value=1, min=0.1)
        elif model_type == "dose_response_4pl":
            params["bottom"].set(value=y.min())
            params["top"].set(value=y.max())
            params["ec50"].set(value=x_mid, min=0)
            params["hill_slope"].set(value=1)


def get_fitting_models() -> dict:
    """Return available fitting models."""
    return FITTING_MODELS
