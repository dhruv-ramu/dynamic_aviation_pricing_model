"""Willingness-to-pay sampling by traveler segment."""

from __future__ import annotations

import numpy as np

from airline_rm.entities.passenger_segment import PassengerSegment
from airline_rm.types import SimulationConfig


def _lognormal_mu_sigma_from_mean_std(mean_usd: float, std_usd: float) -> tuple[float, float]:
    """Map interpretable dollar mean/std to NumPy lognormal parameters.

    If :math:`X \\sim \\text{LogNormal}(\\mu, \\sigma_{log})` in NumPy's parameterization
    (``rng.lognormal(mu, sigma_log)`` draws :math:`\\exp(\\mu + \\sigma_{log} Z)` with
    standard normal :math:`Z`), then

    .. math::

        \\mathbb{E}[X] = \\exp\\Big(\\mu + \\tfrac{1}{2}\\sigma_{log}^2\\Big),

        \\mathrm{Var}(X) = \\mathbb{E}[X]^2\\,(e^{\\sigma_{log}^2} - 1).

    Solving for a target mean :math:`m` and standard deviation :math:`s` in **dollar space**:

    .. math::

        \\sigma_{log}^2 = \\ln\\!\\Big(1 + \\Big(\\frac{s}{m}\\Big)^2\\Big),\\quad
        \\mu = \\ln m - \\tfrac{1}{2}\\sigma_{log}^2.

    For :math:`s=0`, we collapse to a degenerate lognormal with negligible spread
    (``sigma_log`` set to a tiny positive value).
    """

    if mean_usd <= 0:
        raise ValueError("WTP mean must be positive")
    if std_usd < 0:
        raise ValueError("WTP sigma (std dev in USD) must be non-negative")
    if std_usd == 0.0:
        return float(np.log(mean_usd)), 1e-9

    sigma_log_sq = float(np.log1p((std_usd / mean_usd) ** 2))
    sigma_log = float(np.sqrt(sigma_log_sq))
    mu = float(np.log(mean_usd) - 0.5 * sigma_log_sq)
    return mu, sigma_log


class WTPModel:
    """Independent lognormal WTP draws by segment (means/stds in USD)."""

    __slots__ = (
        "_leisure_mean",
        "_leisure_std",
        "_business_mean",
        "_business_std",
        "_leisure_params",
        "_business_params",
    )

    def __init__(
        self,
        leisure_wtp_mean: float,
        leisure_wtp_sigma: float,
        business_wtp_mean: float,
        business_wtp_sigma: float,
    ) -> None:
        self._leisure_mean = float(leisure_wtp_mean)
        self._leisure_std = float(leisure_wtp_sigma)
        self._business_mean = float(business_wtp_mean)
        self._business_std = float(business_wtp_sigma)

        self._leisure_params = _lognormal_mu_sigma_from_mean_std(self._leisure_mean, self._leisure_std)
        self._business_params = _lognormal_mu_sigma_from_mean_std(
            self._business_mean, self._business_std
        )

    def sample_wtp(self, segment: PassengerSegment, rng: np.random.Generator) -> float:
        """Draw a positive WTP (USD) for ``segment``."""

        if segment is PassengerSegment.LEISURE:
            mu, sigma_log = self._leisure_params
        elif segment is PassengerSegment.BUSINESS:
            mu, sigma_log = self._business_params
        else:
            raise TypeError(f"Unsupported segment: {segment!r}")

        return float(rng.lognormal(mu, sigma_log))

    @classmethod
    def from_simulation_config(cls, config: SimulationConfig) -> WTPModel:
        """Instantiate WTP distributions from configuration."""

        return cls(
            leisure_wtp_mean=config.leisure_wtp_mean,
            leisure_wtp_sigma=config.leisure_wtp_sigma,
            business_wtp_mean=config.business_wtp_mean,
            business_wtp_sigma=config.business_wtp_sigma,
        )
