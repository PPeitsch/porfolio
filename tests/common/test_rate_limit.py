import pytest

from app.common.rate_limit import RateLimiter, get_limiter, parse_limits


def test_parse_limits():
    assert parse_limits("8/minute, 60/hour,200/days") == [
        (8, 60),
        (60, 3600),
        (200, 86400),
    ]
    assert parse_limits("5/15minute") == [(5, 900)]
    assert parse_limits("") == []


@pytest.mark.parametrize("spec", ["8", "8/week", "0/minute", "x/minute", "8/-1minute"])
def test_parse_limits_rejects_bad_specs(spec):
    with pytest.raises(ValueError):
        parse_limits(spec)


def test_limiter_counts_per_key_within_the_window():
    limiter = RateLimiter([(2, 60)])

    limiter.hit("a", now=0)
    assert limiter.retry_after("a", now=1) == 0
    limiter.hit("a", now=10)

    # Full: the first hit leaves the window at 60.
    assert limiter.retry_after("a", now=20) == 41
    assert limiter.retry_after("b", now=20) == 0
    assert limiter.retry_after("a", now=60) == 0


def test_limiter_waits_for_the_longest_full_limit():
    limiter = RateLimiter([(2, 60), (3, 3600)])
    for t in (0, 100, 200):
        limiter.hit("a", now=t)

    assert limiter.retry_after("a", now=300) == 3301


def test_limiter_drops_idle_keys(monkeypatch):
    monkeypatch.setattr("app.common.rate_limit._SWEEP_EVERY", 2)
    limiter = RateLimiter([(5, 60)])

    limiter.hit("old", now=0)
    limiter.hit("new", now=100)

    assert "old" not in limiter._hits
    assert "new" in limiter._hits


def test_get_limiter_follows_the_config(app):
    with app.app_context():
        app.config["CHAT_RATE_LIMITS"] = "1/minute"
        first = get_limiter("CHAT_RATE_LIMITS")
        assert get_limiter("CHAT_RATE_LIMITS") is first

        app.config["CHAT_RATE_LIMITS"] = "2/minute"
        assert get_limiter("CHAT_RATE_LIMITS").limits == [(2, 60)]
