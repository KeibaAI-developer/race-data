"""RaceData.is_straight_race のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_mock_di, make_race_basic_info_df

# 正常系


@pytest.mark.parametrize(
    "hidari_migi, expected",
    [
        ("直", True),
        ("左", False),
        ("右", False),
    ],
)
def test_is_straight_race(hidari_migi: str, expected: bool) -> None:
    """左右で直線コースかどうかを判定できる."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(hidari_migi=hidari_migi)
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.is_straight_race() is expected
