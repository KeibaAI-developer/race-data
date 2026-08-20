"""RaceData.is_good_to_firm のテスト."""

import pytest
from keiba_domain import KeibaDomainError

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_mock_di, make_race_basic_info_df

# 正常系


@pytest.mark.parametrize(
    "baba_code, expected",
    [
        ("0", False),
        ("1", True),
        ("2", False),
        ("3", False),
        ("4", False),
    ],
)
def test_is_good_to_firm(baba_code: str, expected: bool) -> None:
    """baba_code が '1' のとき良馬場、'0'（未設定）を含む他のコードでは False になる."""
    mock_di = make_mock_di()
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di, baba_code=baba_code)
    assert race_data.is_good_to_firm() is expected


# 準正常系


def test_is_good_to_firm_with_invalid_baba_code() -> None:
    """baba_code が '0'〜'4' のいずれでもない場合 KeibaDomainError が送出される."""
    mock_di = make_mock_di()
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di, baba_code="9")
    with pytest.raises(KeibaDomainError):
        race_data.is_good_to_firm()


def test_is_good_to_firm_with_empty_baba_code() -> None:
    """馬場状態コードが未取得（空文字）の場合 KeibaDomainError が送出される."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(shiba_baba_code=None)
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.baba_code == ""
    with pytest.raises(KeibaDomainError):
        race_data.is_good_to_firm()
