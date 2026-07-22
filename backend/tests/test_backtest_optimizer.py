import pytest

from app.backtesting.optimizer import (
    DEFAULT_PARAMETER_SPACE,
    Optimizer,
    ParameterSpace,
    ParameterSpec,
)


def test_parameter_spec_rejects_min_greater_than_max():
    with pytest.raises(ValueError, match="min_value must be <= max_value"):
        ParameterSpec("x", min_value=10.0, max_value=1.0, step=1.0)


def test_parameter_spec_rejects_non_positive_step():
    with pytest.raises(ValueError, match="step must be positive"):
        ParameterSpec("x", min_value=0.0, max_value=1.0, step=0.0)


def test_parameter_space_grid_size():
    space = ParameterSpace(parameters=(ParameterSpec("a", 0.0, 1.0, 0.5), ParameterSpec("b", 0.0, 2.0, 1.0)))
    # a: 0.0, 0.5, 1.0 -> 3 steps; b: 0.0, 1.0, 2.0 -> 3 steps
    assert space.grid_size() == 9


def test_default_parameter_space_covers_the_spec_named_targets():
    names = {p.name for p in DEFAULT_PARAMETER_SPACE.parameters}
    assert "min_confidence_for_action" in names
    assert "stop_atr_multiplier" in names
    assert any(name.startswith("factor_weight_") for name in names)
    assert any(name.startswith("tp") for name in names)


def test_optimizer_run_is_not_implemented_yet():
    optimizer = Optimizer(DEFAULT_PARAMETER_SPACE, objective=lambda result: result.risk.sharpe_ratio)
    with pytest.raises(NotImplementedError):
        optimizer.run()
