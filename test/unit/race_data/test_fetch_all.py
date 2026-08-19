"""RaceData.fetch_all のテスト."""

from race_data.race_data import RaceData

# 正常系


def test_fetch_all_fetches_all_lazy_data_for_past_race(past_race_data: RaceData) -> None:
    """過去レースでは全遅延データを取得する."""
    past_race_data.fetch_all()

    assert not past_race_data.result_df.empty
    assert past_race_data.race_result_info_df is not None
    assert past_race_data.payoff_df is not None
    assert not past_race_data.win_show_odds_df.empty
    assert past_race_data.past_performances_dict
    assert past_race_data.horse_master_dict


def test_fetch_all_skips_result_for_future_race(future_race_data: RaceData) -> None:
    """未来レースでは結果系を取得しない."""
    di = future_race_data.data_interface

    future_race_data.fetch_all()

    di.get_result.assert_not_called()
    di.get_race_result_info.assert_not_called()
    di.get_payoff.assert_not_called()
    assert not future_race_data.win_show_odds_df.empty
    assert future_race_data.past_performances_dict
    assert future_race_data.horse_master_dict
