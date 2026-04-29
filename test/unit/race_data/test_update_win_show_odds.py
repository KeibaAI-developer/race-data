"""RaceData.update_win_show_odds のテスト."""

import pandas as pd

from race_data.race_data import RaceData

from .conftest import make_win_show_odds_df

# 正常系


def test_update_win_show_odds_overwrites_df(past_race_data: RaceData) -> None:
    """update_win_show_odds を呼ぶと win_show_odds_df が上書きされる."""
    new_odds_df = make_win_show_odds_df(ninkis=[3, 1, 2])
    di = past_race_data.data_interface
    di.get_win_show_odds.return_value = new_odds_df
    past_race_data.update_win_show_odds()
    pd.testing.assert_frame_equal(past_race_data.win_show_odds_df, new_odds_df)


def test_update_win_show_odds_calls_interface(past_race_data: RaceData) -> None:
    """update_win_show_odds が DataInterface.get_win_show_odds を呼ぶ."""
    di = past_race_data.data_interface
    call_count_before = di.get_win_show_odds.call_count
    past_race_data.update_win_show_odds()
    assert di.get_win_show_odds.call_count == call_count_before + 1
