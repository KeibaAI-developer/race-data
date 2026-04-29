"""RaceData テスト用 fixture."""

from unittest.mock import MagicMock

import pandas as pd
import pytest
from keiba_data_interface import DataInterface

from race_data.race_data import RaceData

PAST_RACE_CODE = "2023112605050812"
FUTURE_RACE_CODE = "2099010105050801"


def make_race_basic_info_df(
    shiba_da: str = "芝",
    race_shubetsu: str = "平地",
    hidari_migi: str = "左",
    kyoso_joken_code: str = "999",
    shutsu_count: int | None = 16,
    shiba_baba_code: str | None = "1",
    dart_baba_code: str | None = None,
) -> pd.DataFrame:
    """レース基本情報 DataFrame を作成する."""
    return pd.DataFrame(
        {
            "芝ダ": [shiba_da],
            "レース種別": [race_shubetsu],
            "左右": [hidari_migi],
            "競走条件コード": [kyoso_joken_code],
            "出走頭数": [shutsu_count],
            "芝馬場状態コード": [shiba_baba_code],
            "ダート馬場状態コード": [dart_baba_code],
        }
    )


def make_entry_df(
    uma_bans: list[int] | None = None,
    horse_ids: list[str] | None = None,
) -> pd.DataFrame:
    """出馬表 DataFrame を作成する."""
    if uma_bans is None:
        uma_bans = [1, 2, 3]
    if horse_ids is None:
        horse_ids = ["2019105219", "2020103656", "2021190001"]
    return pd.DataFrame({"馬番": uma_bans, "血統登録番号": horse_ids})


def make_win_show_odds_df(
    uma_bans: list[int] | None = None,
    ninkis: list[int | None] | None = None,
) -> pd.DataFrame:
    """単複オッズ DataFrame を作成する."""
    if uma_bans is None:
        uma_bans = [1, 2, 3]
    if ninkis is None:
        ninkis = [1, 2, 3]
    return pd.DataFrame({"馬番": uma_bans, "単勝人気": ninkis})


def make_past_performances_df(
    race_codes: list[str] | None = None,
    keibajo_codes: list[str] | None = None,
    ijo_codes: list[str] | None = None,
) -> pd.DataFrame:
    """過去成績 DataFrame を作成する."""
    if race_codes is None:
        race_codes = ["2022112605050812", "2021112605050812"]
    if keibajo_codes is None:
        keibajo_codes = ["05", "05"]
    if ijo_codes is None:
        ijo_codes = ["0", "0"]
    return pd.DataFrame(
        {
            "レースコード": race_codes,
            "競馬場コード": keibajo_codes,
            "異常区分コード": ijo_codes,
        }
    )


def make_mock_di(
    *,
    race_basic_info_df: pd.DataFrame | None = None,
    entry_df: pd.DataFrame | None = None,
    win_show_odds_df: pd.DataFrame | None = None,
    result_df: pd.DataFrame | None = None,
    race_result_info_df: pd.DataFrame | None = None,
    payoff_df: pd.DataFrame | None = None,
    past_performances_df: pd.DataFrame | None = None,
) -> MagicMock:
    """モック DataInterface を作成する."""
    mock = MagicMock(spec=DataInterface)
    mock.get_race_basic_info.return_value = (
        race_basic_info_df if race_basic_info_df is not None else make_race_basic_info_df()
    )
    mock.get_entry.return_value = (
        entry_df if entry_df is not None else make_entry_df()
    )
    mock.get_win_show_odds.return_value = (
        win_show_odds_df if win_show_odds_df is not None else make_win_show_odds_df()
    )
    mock.get_result.return_value = (
        result_df if result_df is not None else make_entry_df()
    )
    mock.get_race_result_info.return_value = (
        race_result_info_df if race_result_info_df is not None else pd.DataFrame()
    )
    mock.get_payoff.return_value = (
        payoff_df if payoff_df is not None else pd.DataFrame()
    )
    mock.get_past_performances.return_value = (
        past_performances_df if past_performances_df is not None else make_past_performances_df()
    )
    return mock


@pytest.fixture()
def mock_di_past() -> MagicMock:
    """過去レース用モック DataInterface."""
    return make_mock_di()


@pytest.fixture()
def mock_di_future() -> MagicMock:
    """未来レース用モック DataInterface."""
    return make_mock_di()


@pytest.fixture()
def past_race_data(mock_di_past: MagicMock) -> RaceData:
    """過去レースの RaceData インスタンス."""
    return RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di_past)


@pytest.fixture()
def future_race_data(mock_di_future: MagicMock) -> RaceData:
    """未来レースの RaceData インスタンス."""
    return RaceData(race_code=FUTURE_RACE_CODE, data_interface=mock_di_future)
