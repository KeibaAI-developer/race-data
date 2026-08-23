"""RaceData.fetch_result のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE

# 正常系


def test_fetch_result_sets_result_df(past_race_data: RaceData) -> None:
    """fetch_result 後に result_df を参照できる."""
    past_race_data.fetch_result()
    assert not past_race_data.result_df.empty


def test_fetch_result_sets_race_result_info_df(past_race_data: RaceData) -> None:
    """fetch_result 後に race_result_info_df を参照できる."""
    past_race_data.fetch_result()
    assert past_race_data.race_result_info_df is not None


def test_fetch_result_sets_payoff_df(past_race_data: RaceData) -> None:
    """fetch_result 後に payoff_df を参照できる."""
    past_race_data.fetch_result()
    assert past_race_data.payoff_df is not None


def test_fetch_result_calls_interface(past_race_data: RaceData) -> None:
    """fetch_result が結果系取得メソッドを呼ぶ."""
    di = past_race_data.data_interface
    past_race_data.fetch_result()
    di.get_result.assert_called_once_with(PAST_RACE_CODE)
    di.get_race_result_info.assert_called_once_with(PAST_RACE_CODE)
    di.get_payoff.assert_called_once_with(PAST_RACE_CODE)


# 準正常系


def test_result_df_raises_before_fetch(past_race_data: RaceData) -> None:
    """取得前に result_df 参照で RuntimeError が発生する.

    個別取得と一括取得のどちらを呼べばよいかがメッセージから分かること。
    """
    with pytest.raises(RuntimeError, match="Call fetch_race_result\\(\\) or fetch_result"):
        _ = past_race_data.result_df


def test_race_result_info_df_raises_before_fetch(past_race_data: RaceData) -> None:
    """取得前に race_result_info_df 参照で RuntimeError が発生する."""
    with pytest.raises(
        RuntimeError, match="Call fetch_race_result_info\\(\\) or fetch_result"
    ):
        _ = past_race_data.race_result_info_df


def test_payoff_df_raises_before_fetch(past_race_data: RaceData) -> None:
    """取得前に payoff_df 参照で RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_payoff\\(\\) or fetch_result"):
        _ = past_race_data.payoff_df
