"""RaceData.fetch_votes のテスト."""

import pytest
from keiba_data_interface.exceptions import DataNotFoundError, UnsupportedOperationError

from race_data.race_data import RaceData

# 正常系


def test_fetch_votes_sets_win_show_votes_df(past_race_data: RaceData) -> None:
    """fetch_votes 後に win_show_votes_df を参照できる."""
    di = past_race_data.data_interface

    past_race_data.fetch_votes()

    di.get_win_show_votes.assert_called_once_with(past_race_data.race_code)
    assert past_race_data.win_show_votes_df["馬番"].tolist() == [1, 2, 3]


def test_fetch_all_fetches_votes_when_supported(past_race_data: RaceData) -> None:
    """票数に対応したプロバイダーでは fetch_all が票数も取得する."""
    past_race_data.fetch_all()

    past_race_data.data_interface.get_win_show_votes.assert_called_once_with(
        past_race_data.race_code
    )
    assert past_race_data.win_show_votes_df["馬番"].tolist() == [1, 2, 3]


def test_fetch_all_skips_votes_when_not_supported(past_race_data: RaceData) -> None:
    """票数に対応しないプロバイダー（UnsupportedOperationError）では fetch_all が取得を省く."""
    past_race_data.data_interface.get_win_show_votes.side_effect = UnsupportedOperationError(
        "非対応"
    )

    past_race_data.fetch_all()

    with pytest.raises(RuntimeError, match="Call fetch_votes"):
        _ = past_race_data.win_show_votes_df


def test_fetch_all_propagates_data_not_found_for_votes(past_race_data: RaceData) -> None:
    """票数のデータが無い（DataNotFoundError）場合は fetch_all がそのまま伝播させる."""
    past_race_data.data_interface.get_win_show_votes.side_effect = DataNotFoundError("データなし")

    with pytest.raises(DataNotFoundError):
        past_race_data.fetch_all()


# 準正常系


def test_win_show_votes_df_raises_before_fetch(past_race_data: RaceData) -> None:
    """fetch_votes 前に win_show_votes_df を参照すると RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_votes"):
        _ = past_race_data.win_show_votes_df
