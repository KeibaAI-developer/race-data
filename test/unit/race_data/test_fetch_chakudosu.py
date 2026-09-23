"""RaceData.fetch_chakudosu のテスト."""

import pytest
from keiba_data_interface.exceptions import DataNotFoundError, UnsupportedOperationError

from race_data.race_data import RaceData

# 正常系


def test_fetch_chakudosu_sets_chakudosu_df(past_race_data: RaceData) -> None:
    """fetch_chakudosu 後に chakudosu_df を参照できる."""
    di = past_race_data.history_interface

    past_race_data.fetch_chakudosu()

    di.get_chakudosu.assert_called_once_with(past_race_data.race_code)
    assert past_race_data.chakudosu_df["馬番"].tolist() == [1, 2, 3]


def test_fetch_all_fetches_chakudosu_when_supported(past_race_data: RaceData) -> None:
    """着度数に対応したプロバイダーでは fetch_all が着度数も取得する."""
    past_race_data.fetch_all()

    past_race_data.history_interface.get_chakudosu.assert_called_once_with(past_race_data.race_code)
    assert past_race_data.chakudosu_df["馬番"].tolist() == [1, 2, 3]


def test_fetch_all_skips_chakudosu_when_not_supported(past_race_data: RaceData) -> None:
    """着度数に対応しないプロバイダー（UnsupportedOperationError）では fetch_all が取得を省く."""
    past_race_data.history_interface.get_chakudosu.side_effect = UnsupportedOperationError("非対応")

    past_race_data.fetch_all()

    with pytest.raises(RuntimeError, match="Call fetch_chakudosu"):
        _ = past_race_data.chakudosu_df


def test_fetch_all_propagates_data_not_found_for_chakudosu(past_race_data: RaceData) -> None:
    """着度数のデータが無い（DataNotFoundError）場合は fetch_all がそのまま伝播させる."""
    past_race_data.history_interface.get_chakudosu.side_effect = DataNotFoundError("データなし")

    with pytest.raises(DataNotFoundError):
        past_race_data.fetch_all()


# 準正常系


def test_chakudosu_df_raises_before_fetch(past_race_data: RaceData) -> None:
    """fetch_chakudosu 前に chakudosu_df を参照すると RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_chakudosu"):
        _ = past_race_data.chakudosu_df
