"""RaceData.is_good_to_firm のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import _PAST_RACE_CODE, _make_mock_di

# 正常系


@pytest.mark.parametrize(
    "baba_code, expected",
    [
        ("1", True),
        ("2", False),
        ("3", False),
        ("4", False),
    ],
)
def test_is_good_to_firm(baba_code: str, expected: bool) -> None:
    """baba_code が '1' のとき良馬場と判定される."""
    mock_di = _make_mock_di()
    race_data = RaceData(race_code=_PAST_RACE_CODE, data_interface=mock_di, baba_code=baba_code)
    assert race_data.is_good_to_firm() is expected
