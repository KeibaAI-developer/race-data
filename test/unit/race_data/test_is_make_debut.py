"""RaceData.is_make_debut のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_mock_di, make_race_basic_info_df

# 正常系


@pytest.mark.parametrize(
    "kyoso_joken_code, expected",
    [
        ("701", True),
        ("999", False),
        ("001", False),
    ],
)
def test_is_make_debut(kyoso_joken_code: str, expected: bool) -> None:
    """競走条件コードで新馬戦かどうかを判定できる."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(kyoso_joken_code=kyoso_joken_code)
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.is_make_debut() is expected
