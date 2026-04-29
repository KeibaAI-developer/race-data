"""RaceData.is_turf のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import _PAST_RACE_CODE, _make_mock_di, _make_race_basic_info_df

# 正常系


@pytest.mark.parametrize(
    "shiba_da, expected",
    [
        ("芝", True),
        ("ダ", False),
    ],
)
def test_is_turf(shiba_da: str, expected: bool) -> None:
    """芝ダで芝レースかどうかを判定できる."""
    mock_di = _make_mock_di(
        race_basic_info_df=_make_race_basic_info_df(shiba_da=shiba_da)
    )
    race_data = RaceData(race_code=_PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.is_turf() is expected
