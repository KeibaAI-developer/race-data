"""RaceData.fetch_odds のテスト."""

import logging

import pandas as pd
import pytest
from keiba_data_interface.exceptions import DataNotFoundError, UnsupportedOperationError

from race_data.race_data import RaceData, today_jst

from .conftest import FUTURE_RACE_CODE, PAST_RACE_CODE, make_mock_di, make_win_show_odds_df

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


def test_fetch_odds_keeps_num_runners(past_race_data: RaceData) -> None:
    """fetch_odds は num_runners を書き換えない."""
    before = past_race_data.num_runners
    past_race_data.fetch_odds()
    assert past_race_data.num_runners == before


def test_fetch_odds_uses_expected_odds_before_race_day(caplog: pytest.LogCaptureFixture) -> None:
    """レース日より前で現在のオッズが無ければ、発売前として予想オッズを使う."""
    mock_di = make_mock_di()
    mock_di.get_win_show_odds.side_effect = DataNotFoundError("発売前")
    expected_df = make_win_show_odds_df(ninkis=[2, 1, 3])
    mock_di.get_expected_win_show_odds.return_value = expected_df
    race_data = RaceData(race_code=FUTURE_RACE_CODE, data_interface=mock_di)

    with caplog.at_level(logging.INFO):
        race_data.fetch_odds()

    pd.testing.assert_frame_equal(race_data.win_show_odds_df, expected_df)
    assert race_data.win_show_odds_is_expected is True
    mock_di.get_expected_win_show_odds.assert_called_once_with(FUTURE_RACE_CODE)
    assert "予想オッズ" in caplog.text


def test_fetch_odds_resets_expected_flag_when_current_odds_available() -> None:
    """現在のオッズが取れれば win_show_odds_is_expected は False に戻る."""
    mock_di = make_mock_di()
    mock_di.get_win_show_odds.side_effect = [DataNotFoundError("発売前"), make_win_show_odds_df()]
    race_data = RaceData(race_code=FUTURE_RACE_CODE, data_interface=mock_di)

    race_data.fetch_odds()
    assert race_data.win_show_odds_is_expected is True
    race_data.fetch_odds()
    assert race_data.win_show_odds_is_expected is False


# 準正常系


def test_win_show_odds_df_raises_before_fetch(past_race_data: RaceData) -> None:
    """fetch_odds 前に win_show_odds_df 参照で RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_odds"):
        _ = past_race_data.win_show_odds_df


def test_fetch_odds_raises_on_race_day_without_odds(caplog: pytest.LogCaptureFixture) -> None:
    """レース当日にオッズが無ければ予想オッズに切り替えず、ログを出して DataNotFoundError."""
    today_race_code = today_jst().strftime("%Y%m%d") + "05050801"
    mock_di = make_mock_di()
    mock_di.get_win_show_odds.side_effect = DataNotFoundError("取得元の異常")
    race_data = RaceData(race_code=today_race_code, data_interface=mock_di)

    with caplog.at_level(logging.ERROR), pytest.raises(DataNotFoundError):
        race_data.fetch_odds()
    mock_di.get_expected_win_show_odds.assert_not_called()
    assert "単複オッズを取得できません" in caplog.text


def test_fetch_odds_raises_for_past_race_without_odds(past_race_data: RaceData) -> None:
    """過去レースでオッズが無ければ DataNotFoundError."""
    past_race_data.data_interface.get_win_show_odds.side_effect = DataNotFoundError("なし")

    with pytest.raises(DataNotFoundError):
        past_race_data.fetch_odds()


def test_fetch_odds_propagates_expected_odds_error(caplog: pytest.LogCaptureFixture) -> None:
    """発売前で予想オッズも取れなければその例外をそのまま送出する."""
    mock_di = make_mock_di()
    mock_di.get_win_show_odds.side_effect = DataNotFoundError("発売前")
    mock_di.get_expected_win_show_odds.side_effect = UnsupportedOperationError("非対応")
    race_data = RaceData(race_code=FUTURE_RACE_CODE, data_interface=mock_di)

    with caplog.at_level(logging.ERROR), pytest.raises(UnsupportedOperationError):
        race_data.fetch_odds()
    assert "予想オッズを取得できません" in caplog.text
