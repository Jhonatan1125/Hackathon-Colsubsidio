"""Risk policy configuration.

PD tier boundaries, LGD constant, and amount reduction rules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    """Risk thresholds and loss parameters."""

    pd_low_risk: float = 0.10
    pd_high_risk: float = 0.20
    lgd: float = 0.45
    amount_reduction_factor: float = 0.50
    min_ev_threshold: float = 0.0


RISK = RiskConfig()
