"""RaceData.is_steeple_chase のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_mock_di, make_race_basic_info_df

# 正常系


@pytest.mark.parametrize(
    "race_shubetsu, expected",
    [
        ("障害", True),
        ("平地", False),
    ],
)
def test_is_steeple_chase(race_shubetsu: str, expected: bool) -> None:
    """レース種別で障害レースかどうかを判定できる."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(race_shubetsu=race_shubetsu)
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.is_steeple_chase() is expected
