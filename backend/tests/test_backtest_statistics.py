from app.backtesting.statistics import (
    annualization_factor,
    downside_deviation,
    max_drawdown,
    mean,
    monte_carlo_drawdown_distribution,
    monte_carlo_shuffle,
    stdev,
)


def test_mean_empty_is_zero():
    assert mean([]) == 0.0


def test_mean_basic():
    assert mean([1.0, 2.0, 3.0]) == 2.0


def test_stdev_fewer_than_two_is_zero():
    assert stdev([]) == 0.0
    assert stdev([5.0]) == 0.0


def test_stdev_basic():
    assert stdev([1.0, 1.0, 1.0]) == 0.0
    assert stdev([1.0, 2.0, 3.0]) > 0.0


def test_downside_deviation_ignores_upside():
    # All returns above target -> no downside at all
    assert downside_deviation([1.0, 2.0, 3.0], target=0.0) == 0.0


def test_downside_deviation_only_uses_below_target():
    values = [-5.0, -3.0, 10.0, 20.0]
    dd = downside_deviation(values, target=0.0)
    assert dd > 0.0


def test_max_drawdown_no_drawdown_on_monotonic_increase():
    dd_pct, dd_dollar, peak_idx, trough_idx = max_drawdown([100.0, 110.0, 120.0, 130.0])
    assert dd_pct == 0.0
    assert dd_dollar == 0.0


def test_max_drawdown_finds_largest_drop():
    balances = [100.0, 120.0, 90.0, 95.0, 150.0, 100.0]
    dd_pct, dd_dollar, peak_idx, trough_idx = max_drawdown(balances)
    # Largest drawdown: 150 -> 100 = 33.3%, vs 120 -> 90 = 25%
    assert peak_idx == 4
    assert trough_idx == 5
    assert abs(dd_pct - (50.0 / 150.0 * 100.0)) < 1e-9
    assert dd_dollar == 50.0


def test_max_drawdown_empty_is_zero():
    assert max_drawdown([]) == (0.0, 0.0, 0, 0)


def test_annualization_factor_zero_trades_per_year_is_zero():
    assert annualization_factor(0) == 0.0


def test_annualization_factor_positive():
    assert annualization_factor(365) > 0.0


def test_monte_carlo_shuffle_preserves_values_only_reorders():
    pnls = [10.0, -5.0, 20.0, -15.0, 3.0]
    simulations = monte_carlo_shuffle(pnls, n_simulations=10, seed=1)

    assert len(simulations) == 10
    for sim in simulations:
        assert sorted(sim) == sorted(pnls)
        assert sum(sim) == sum(pnls)


def test_monte_carlo_shuffle_deterministic_given_seed():
    pnls = [10.0, -5.0, 20.0, -15.0, 3.0, 7.0, -2.0]
    first = monte_carlo_shuffle(pnls, n_simulations=5, seed=42)
    second = monte_carlo_shuffle(pnls, n_simulations=5, seed=42)
    assert first == second


def test_monte_carlo_shuffle_different_seeds_can_differ():
    pnls = [10.0, -5.0, 20.0, -15.0, 3.0, 7.0, -2.0, 1.0]
    a = monte_carlo_shuffle(pnls, n_simulations=5, seed=1)
    b = monte_carlo_shuffle(pnls, n_simulations=5, seed=2)
    assert a != b


def test_monte_carlo_drawdown_distribution_length_and_bounds():
    pnls = [100.0, -50.0, 30.0, -20.0, 60.0]
    dd_distribution = monte_carlo_drawdown_distribution(pnls, initial_balance=1000.0, n_simulations=25, seed=7)
    assert len(dd_distribution) == 25
    assert all(dd >= 0.0 for dd in dd_distribution)
