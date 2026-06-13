"""RaceData.fetch_odds のテスト."""

import pandas as pd
import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_mock_di, make_race_basic_info_df, make_win_show_odds_df

# 正常系


def test_fetch_odds_sets_win_show_odds_df(past_race_data: RaceData) -> None:
    """fetch_odds 後に win_show_odds_df を参照できる."""
    past_race_data.fetch_odds()
    assert not past_race_data.win_show_odds_df.empty


def test_fetch_odds_calls_interface(past_race_data: RaceData) -> None:
    """fetch_odds が DataInterface.get_win_show_odds を呼ぶ."""
    di = past_race_data.data_interface
    past_race_data.fetch_odds()
    di.get_win_show_odds.assert_called_once_with(PAST_RACE_CODE)


def test_fetch_odds_overwrites_df(past_race_data: RaceData) -> None:
    """fetch_odds を再実行すると win_show_odds_df が上書きされる."""
    first_odds_df = make_win_show_odds_df(ninkis=[1, 2, 3])
    second_odds_df = make_win_show_odds_df(ninkis=[3, 1, 2])
    di = past_race_data.data_interface
    di.get_win_show_odds.side_effect = [first_odds_df, second_odds_df]

    past_race_data.fetch_odds()
    past_race_data.fetch_odds()

    pd.testing.assert_frame_equal(past_race_data.win_show_odds_df, second_odds_df)


def test_fetch_odds_complements_num_runners_when_missing() -> None:
    """出走頭数が未確定の場合は単勝人気がある頭数で補完される."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(shutsu_count=None),
        win_show_odds_df=make_win_show_odds_df(ninkis=[1, 2, None]),
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)

    assert race_data.num_runners == 0
    race_data.fetch_odds()
    assert race_data.num_runners == 2


def test_fetch_odds_updates_num_runners_when_race_basic_info_missing() -> None:
    """出走頭数が未確定の場合は fetch_odds のたびに num_runners が更新される."""
    first_odds_df = make_win_show_odds_df(ninkis=[1, 2, None])
    second_odds_df = make_win_show_odds_df(ninkis=[1, None, None])
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(shutsu_count=None),
        win_show_odds_df=first_odds_df,
    )
    mock_di.get_win_show_odds.side_effect = [first_odds_df, second_odds_df]
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)

    race_data.fetch_odds()
    assert race_data.num_runners == 2
    race_data.fetch_odds()
    assert race_data.num_runners == 1


# 準正常系


def test_win_show_odds_df_raises_before_fetch(past_race_data: RaceData) -> None:
    """fetch_odds 前に win_show_odds_df 参照で RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_odds"):
        _ = past_race_data.win_show_odds_df
