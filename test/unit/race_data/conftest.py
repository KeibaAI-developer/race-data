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
    ijo_codes: list[str] | None = None,
) -> pd.DataFrame:
    """出馬表 DataFrame を作成する."""
    if uma_bans is None:
        uma_bans = [1, 2, 3]
    if horse_ids is None:
        horse_ids = ["2019105219", "2020103656", "2021190001"]
    if ijo_codes is None:
        ijo_codes = ["0", "0", "0"]
    return pd.DataFrame({"馬番": uma_bans, "血統登録番号": horse_ids, "異常区分コード": ijo_codes})


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


def make_horse_master_df(
    horse_id: str = "2019105219",
    horse_name: str = "テストウマ",
) -> pd.DataFrame:
    """競走馬マスタ DataFrame を作成する."""
    return pd.DataFrame({"血統登録番号": [horse_id], "馬名": [horse_name]})


def make_mock_di(
    *,
    race_basic_info_df: pd.DataFrame | None = None,
    entry_df: pd.DataFrame | None = None,
    win_show_odds_df: pd.DataFrame | None = None,
    result_df: pd.DataFrame | None = None,
    race_result_info_df: pd.DataFrame | None = None,
    payoff_df: pd.DataFrame | None = None,
    past_performances_df: pd.DataFrame | None = None,
    horse_master_df: pd.DataFrame | None = None,
    past_performances_by_horse_id: dict[str, pd.DataFrame] | None = None,
    horse_master_by_horse_id: dict[str, pd.DataFrame] | None = None,
) -> MagicMock:
    """モック DataInterface を作成する."""
    mock = MagicMock(spec=DataInterface)
    mock.get_race_basic_info.return_value = (
        race_basic_info_df if race_basic_info_df is not None else make_race_basic_info_df()
    )
    mock.get_entry.return_value = entry_df if entry_df is not None else make_entry_df()
    mock.get_win_show_odds.return_value = (
        win_show_odds_df if win_show_odds_df is not None else make_win_show_odds_df()
    )
    mock.get_expected_win_show_odds.return_value = make_win_show_odds_df(ninkis=[3, 2, 1])
    mock.get_result.return_value = result_df if result_df is not None else make_entry_df()
    mock.get_race_result_info.return_value = (
        race_result_info_df if race_result_info_df is not None else pd.DataFrame()
    )
    mock.get_payoff.return_value = payoff_df if payoff_df is not None else pd.DataFrame()
    mock.get_past_performances.return_value = (
        past_performances_df if past_performances_df is not None else make_past_performances_df()
    )

    def get_past_performances_bulk(horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """指定された各馬の過去成績を返す.

        一括取得は指定した馬IDを必ずキーに含める契約である。馬ごとの過去成績が
        指定されていれば馬IDで引き、指定されていなければ
        `get_past_performances.return_value` を全馬へ返す。後者は呼び出し時点の値を
        読むため、テストが `get_past_performances.return_value` を差し替えても追随する。

        Args:
            horse_ids (list[str]): 馬ID（血統登録番号）のリスト

        Returns:
            dict[str, pd.DataFrame]: 馬ID → 過去成績
        """
        if past_performances_by_horse_id is not None:
            return {
                horse_id: past_performances_by_horse_id[horse_id].copy() for horse_id in horse_ids
            }
        return {horse_id: mock.get_past_performances.return_value.copy() for horse_id in horse_ids}

    mock.get_past_performances_bulk.side_effect = get_past_performances_bulk
    mock.get_horse_master.return_value = (
        horse_master_df if horse_master_df is not None else make_horse_master_df()
    )

    def get_horse_master_bulk(horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """指定された各馬の競走馬マスタを返す.

        一括取得は指定した馬IDを必ずキーに含める契約である。馬ごとのマスタが
        指定されていれば馬IDで引き、指定されていなければ
        `get_horse_master.return_value` を全馬へ返す。後者は呼び出し時点の値を読むため、
        テストが `get_horse_master.return_value` を差し替えても追随する。

        Args:
            horse_ids (list[str]): 馬ID（血統登録番号）のリスト

        Returns:
            dict[str, pd.DataFrame]: 馬ID → 競走馬マスタ
        """
        if horse_master_by_horse_id is not None:
            return {horse_id: horse_master_by_horse_id[horse_id].copy() for horse_id in horse_ids}
        return {horse_id: mock.get_horse_master.return_value.copy() for horse_id in horse_ids}

    mock.get_horse_master_bulk.side_effect = get_horse_master_bulk
    mock.supports_bulk = True

    def get_race_basic_info_bulk(race_codes: list[str]) -> pd.DataFrame:
        """指定レースコードのレース基本情報（1行ずつ）を返す.

        一括取得は実在したレースだけを返す契約のため、レースコード降順で返して
        呼び出し側の並べ替えを検証できるようにする。

        Args:
            race_codes (list[str]): レースコードのリスト

        Returns:
            pd.DataFrame: レースコードを持つレース基本情報
        """
        return pd.DataFrame({"レースコード": sorted(race_codes, reverse=True)})

    mock.get_race_basic_info_bulk.side_effect = get_race_basic_info_bulk
    mock.get_win_show_votes.return_value = pd.DataFrame(
        {"馬番": [1, 2, 3], "複勝票数": [300, 200, 100], "複勝票数合計": [700, 700, 700]}
    )
    mock.get_chakudosu.return_value = pd.DataFrame(
        {"馬番": [1, 2, 3], "血統登録番号": ["2019105219", "2020103656", "2021190001"]}
    )
    return mock


@pytest.fixture()
def mock_di_past() -> MagicMock:
    """過去レース用モック DataInterface."""
    return make_mock_di()


@pytest.fixture()
def mock_di_past2() -> MagicMock:
    """過去レース用モック DataInterface（比較用の別インスタンス）."""
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
def another_past_race_data(mock_di_past2: MagicMock) -> RaceData:
    """過去レースの RaceData インスタンス（比較用の別インスタンス）."""
    return RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di_past2)


@pytest.fixture()
def future_race_data(mock_di_future: MagicMock) -> RaceData:
    """未来レースの RaceData インスタンス."""
    return RaceData(race_code=FUTURE_RACE_CODE, data_interface=mock_di_future)


@pytest.fixture()
def mock_di_history() -> MagicMock:
    """アーカイブ用モック DataInterface."""
    return make_mock_di()


@pytest.fixture()
def race_data_with_history(mock_di_past: MagicMock, mock_di_history: MagicMock) -> RaceData:
    """最新情報用とアーカイブ用を分けた過去レースの RaceData インスタンス."""
    return RaceData(
        race_code=PAST_RACE_CODE, data_interface=mock_di_past, history_interface=mock_di_history
    )
