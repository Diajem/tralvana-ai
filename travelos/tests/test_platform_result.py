import pytest

from travelos.shared.result import Error, Result


def test_ok_result_exposes_value_and_is_truthy():
    result = Result.ok({"trip_id": "trip-1"})

    assert result.success is True
    assert result.value == {"trip_id": "trip-1"}
    assert result.error is None
    assert bool(result) is True
    assert result.unwrap() == {"trip_id": "trip-1"}


def test_failed_result_preserves_structured_error_and_is_falsy():
    result = Result.fail(
        "PROVIDER_UNAVAILABLE",
        "No provider answered",
        provider="example",
    )

    assert result.success is False
    assert result.value is None
    assert result.error == Error(
        code="PROVIDER_UNAVAILABLE",
        message="No provider answered",
        details={"provider": "example"},
    )
    assert str(result.error) == "[PROVIDER_UNAVAILABLE] No provider answered"
    assert bool(result) is False


def test_unwrap_rejects_failed_result():
    with pytest.raises(
        ValueError,
        match=r"Result is not ok: \[NOT_FOUND\] Trip missing",
    ):
        Result.fail("NOT_FOUND", "Trip missing").unwrap()


def test_unwrap_rejects_success_without_a_value():
    result = Result(success=True, value=None, error=None)

    with pytest.raises(ValueError, match="Result is not ok"):
        result.unwrap()
