"""RaceData.__post_init__ のテスト."""

from unittest.mock import MagicMock, call

import pandas as pd

from race_data.race_data import RaceData

from .conftest import (
    FUTURE_RACE_CODE,
    PAST_RACE_CODE,
    make_entry_df,
    make_mock_di,
    make_past_performances_df,
    make_race_basic_info_df,
    make_win_show_odds_df,
)

# 正常系


def test_future_race_true_for_future_code(future_race_data: RaceData) -> None:
    """未来のレースコードで future_race が True になる."""
    assert future_race_data.future_race is True


def test_future_race_false_for_past_code(past_race_data: RaceData) -> None:
    """過去のレースコードで future_race が False になる."""
    assert past_race_data.future_race is False


def test_race_basic_info_df_fetched(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """race_basic_info_df が取得される."""
    mock_di_past.get_race_basic_info.assert_called_once_with(PAST_RACE_CODE)
    assert not past_race_data.race_basic_info_df.empty


def test_entry_df_fetched_for_past_race(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """過去レースでも entry_df が取得される."""
    mock_di_past.get_entry.assert_called_once_with(PAST_RACE_CODE)
    assert not past_race_data.entry_df.empty


def test_entry_df_fetched_for_future_race(
    future_race_data: RaceData, mock_di_future: MagicMock
) -> None:
    """未来レースでも entry_df が取得される."""
    mock_di_future.get_entry.assert_called_once_with(FUTURE_RACE_CODE)
    assert not future_race_data.entry_df.empty


def test_win_show_odds_df_fetched(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """win_show_odds_df が取得される."""
    mock_di_past.get_win_show_odds.assert_called_once_with(PAST_RACE_CODE)
    assert not past_race_data.win_show_odds_df.empty


def test_result_df_fetched_for_past_race(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """過去レースで result_df が取得される."""
    mock_di_past.get_result.assert_called_once_with(PAST_RACE_CODE)
    assert not past_race_data.result_df.empty


def test_result_df_not_fetched_for_future_race(
    future_race_data: RaceData, mock_di_future: MagicMock
) -> None:
    """未来レースで result_df は取得されず空."""
    mock_di_future.get_result.assert_not_called()
    assert future_race_data.result_df.empty


def test_race_result_info_df_fetched_for_past(
    past_race_data: RaceData, mock_di_past: MagicMock
) -> None:
    """過去レースで race_result_info_df が取得される."""
    mock_di_past.get_race_result_info.assert_called_once_with(PAST_RACE_CODE)


def test_race_result_info_df_not_fetched_for_future(
    future_race_data: RaceData, mock_di_future: MagicMock
) -> None:
    """未来レースで race_result_info_df は空."""
    mock_di_future.get_race_result_info.assert_not_called()
    assert future_race_data.race_result_info_df.empty


def test_payoff_df_fetched_for_past(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """過去レースで payoff_df が取得される."""
    mock_di_past.get_payoff.assert_called_once_with(PAST_RACE_CODE)


def test_payoff_df_not_fetched_for_future(
    future_race_data: RaceData, mock_di_future: MagicMock
) -> None:
    """未来レースで payoff_df は空."""
    mock_di_future.get_payoff.assert_not_called()
    assert future_race_data.payoff_df.empty


def test_past_performances_dict_has_all_horses(past_race_data: RaceData) -> None:
    """past_performances_dict に全馬が含まれる."""
    assert set(past_race_data.past_performances_dict.keys()) == {1, 2, 3}


def test_past_performances_fetched_per_horse(
    past_race_data: RaceData, mock_di_past: MagicMock
) -> None:
    """馬ごとに get_past_performances が呼ばれる."""
    assert mock_di_past.get_past_performances.call_count == 3


def test_past_performances_excludes_future_races() -> None:
    """past_performances_dict から対象レース以降が除外される."""
    pp_with_future = make_past_performances_df(
        race_codes=["2022112605050812", "2024010105050801"],
    )
    mock_di = make_mock_di(past_performances_df=pp_with_future)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    for pp_df in race_data.past_performances_dict.values():
        assert all(pp_df["レースコード"] < PAST_RACE_CODE)


def test_num_runners_from_race_basic_info(past_race_data: RaceData) -> None:
    """num_runners が race_basic_info_df の出走頭数から取得される."""
    assert past_race_data.num_runners == 16


def test_num_runners_fallback_to_win_show_odds() -> None:
    """出走頭数が NaN の場合は win_show_odds_df の単勝人気がある頭数にフォールバック."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(shutsu_count=None),
        win_show_odds_df=make_win_show_odds_df(ninkis=[1, 2, None]),
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.num_runners == 2


def test_baba_code_auto_set_from_turf(past_race_data: RaceData) -> None:
    """芝レースで baba_code が芝馬場状態コードから自動設定される."""
    assert past_race_data.baba_code == "1"


def test_baba_code_auto_set_from_dirt() -> None:
    """ダートレースで baba_code がダート馬場状態コードから自動設定される."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(
            shiba_da="ダ",
            dart_baba_code="2",
        ),
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.baba_code == "2"


def test_baba_code_overridden_by_constructor() -> None:
    """コンストラクタ引数 baba_code で自動設定が上書きされる."""
    mock_di = make_mock_di()
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di, baba_code="3")
    assert race_data.baba_code == "3"


def test_horse_master_dict_has_all_horses(past_race_data: RaceData) -> None:
    """horse_master_dict に全馬の血統登録番号がキーとして含まれる."""
    expected_ids = set(make_entry_df()["血統登録番号"])
    assert set(past_race_data.horse_master_dict.keys()) == expected_ids


def test_horse_master_fetched_per_horse(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """馬ごとに get_horse_master が呼ばれる."""
    expected_horse_ids = list(make_entry_df()["血統登録番号"])
    assert mock_di_past.get_horse_master.call_count == len(expected_horse_ids)
    mock_di_past.get_horse_master.assert_has_calls(
        [call(horse_id) for horse_id in expected_horse_ids],
        any_order=True,
    )


def test_horse_master_dict_values_are_dataframes(past_race_data: RaceData) -> None:
    """horse_master_dict の各値が DataFrame である."""
    for df in past_race_data.horse_master_dict.values():
        assert isinstance(df, pd.DataFrame)


def test_valid_horse_num_all_valid(past_race_data: RaceData) -> None:
    """全馬が有効な場合、全馬番が昇順に含まれる."""
    assert past_race_data.valid_horse_num == [1, 2, 3]


def test_valid_horse_num_excludes_ijo_code_1() -> None:
    """異常区分コード1の馬が valid_horse_num から除外される."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["1", "0", "0"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [2, 3]


def test_valid_horse_num_excludes_ijo_code_2() -> None:
    """異常区分コード2の馬が valid_horse_num から除外される."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["0", "2", "0"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [1, 3]


def test_valid_horse_num_excludes_ijo_code_3() -> None:
    """異常区分コード3の馬が valid_horse_num から除外される."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["0", "0", "3"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [1, 2]


def test_valid_horse_num_is_sorted() -> None:
    """entry_df の馬番順に関わらず valid_horse_num が昇順に並んでいる."""
    entry_df = make_entry_df(uma_bans=[3, 1, 2], ijo_codes=["0", "0", "0"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [1, 2, 3]


def test_valid_horse_num_empty_when_all_excluded() -> None:
    """全馬が異常区分コード1,2,3の場合は空リストになる."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["1", "2", "3"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == []
