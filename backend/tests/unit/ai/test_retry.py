import pytest

from app.ai.errors import AIProviderError, AIResponseError, AITransientError
from app.ai.retry import retry_call


class _Counter:
    """A callable that fails a set number of times, then returns a value."""

    def __init__(self, fail_times: int, exc: Exception, value: str = "ok") -> None:
        self.fail_times = fail_times
        self.exc = exc
        self.value = value
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc
        return self.value


def _no_sleep(_: float) -> None:
    return None


class TestRetrySuccess:
    def test_returns_immediately_on_success(self) -> None:
        fn = _Counter(fail_times=0, exc=AITransientError("x"))
        assert retry_call(fn, sleep=_no_sleep) == "ok"
        assert fn.calls == 1

    def test_retries_transient_then_succeeds(self) -> None:
        fn = _Counter(fail_times=2, exc=AITransientError("temp"))
        assert retry_call(fn, max_attempts=3, sleep=_no_sleep) == "ok"
        assert fn.calls == 3


class TestRetryExhaustion:
    def test_raises_after_exhausting_attempts(self) -> None:
        fn = _Counter(fail_times=5, exc=AITransientError("temp"))
        with pytest.raises(AITransientError):
            retry_call(fn, max_attempts=3, sleep=_no_sleep)
        assert fn.calls == 3

    def test_sleeps_between_attempts_only(self) -> None:
        delays: list[float] = []
        fn = _Counter(fail_times=5, exc=AITransientError("temp"))
        with pytest.raises(AITransientError):
            retry_call(fn, max_attempts=3, sleep=delays.append)
        # 3 attempts -> 2 sleeps.
        assert len(delays) == 2


class TestRetryNonTransient:
    def test_does_not_retry_non_transient_provider_error(self) -> None:
        fn = _Counter(fail_times=5, exc=AIProviderError("auth"))
        with pytest.raises(AIProviderError):
            retry_call(fn, max_attempts=3, sleep=_no_sleep)
        assert fn.calls == 1

    def test_does_not_retry_response_error(self) -> None:
        fn = _Counter(fail_times=5, exc=AIResponseError("bad json"))
        with pytest.raises(AIResponseError):
            retry_call(fn, max_attempts=3, sleep=_no_sleep)
        assert fn.calls == 1


class TestBackoff:
    def test_exponential_growth_without_jitter(self) -> None:
        delays: list[float] = []
        fn = _Counter(fail_times=5, exc=AITransientError("temp"))
        with pytest.raises(AITransientError):
            retry_call(
                fn,
                max_attempts=4,
                base_delay=1.0,
                jitter=False,
                sleep=delays.append,
            )
        # base_delay * 2**n: 1, 2, 4
        assert delays == [1.0, 2.0, 4.0]

    def test_delay_capped_at_max(self) -> None:
        delays: list[float] = []
        fn = _Counter(fail_times=9, exc=AITransientError("temp"))
        with pytest.raises(AITransientError):
            retry_call(
                fn,
                max_attempts=5,
                base_delay=10.0,
                max_delay=15.0,
                jitter=False,
                sleep=delays.append,
            )
        assert all(d <= 15.0 for d in delays)
