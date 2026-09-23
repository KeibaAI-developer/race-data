"""RaceData の data_interface と history_interface の使い分けのテスト."""

from unittest.mock import MagicMock

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE

# 正常系


def test_history_interface_defaults_to_data_interface(past_race_data: RaceData) -> None:
    """history_interface を省略すると data_interface と同じインスタンスになる."""
    assert past_race_data.history_interface is past_race_data.data_interface


def test_history_interface_is_kept_when_given(
    race_data_with_history: RaceData, mock_di_past: MagicMock, mock_di_history: MagicMock
) -> None:
    """history_interface を指定すると data_interface とは別に保持される."""
    assert race_data_with_history.data_interface is mock_di_past
    assert race_data_with_history.history_interface is mock_di_history


def test_init_uses_data_interface_for_target_race(
    race_data_with_history: RaceData, mock_di_past: MagicMock, mock_di_history: MagicMock
) -> None:
    """レース基本情報と出馬表は data_interface から取得し history_interface は使わない."""
    mock_di_past.get_race_basic_info.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_entry.assert_called_once_with(PAST_RACE_CODE)
    mock_di_history.get_race_basic_info.assert_not_called()
    mock_di_history.get_entry.assert_not_called()


def test_target_race_fetches_use_data_interface(
    race_data_with_history: RaceData, mock_di_past: MagicMock, mock_di_history: MagicMock
) -> None:
    """結果系・オッズ・票数は data_interface から取得する."""
    race_data_with_history.fetch_result()
    race_data_with_history.fetch_odds()
    race_data_with_history.fetch_votes()

    mock_di_past.get_result.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_race_result_info.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_payoff.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_win_show_odds.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_win_show_votes.assert_called_once_with(PAST_RACE_CODE)
    mock_di_history.get_result.assert_not_called()
    mock_di_history.get_race_result_info.assert_not_called()
    mock_di_history.get_payoff.assert_not_called()
    mock_di_history.get_win_show_odds.assert_not_called()
    mock_di_history.get_win_show_votes.assert_not_called()


def test_history_fetches_use_history_interface(
    race_data_with_history: RaceData, mock_di_past: MagicMock, mock_di_history: MagicMock
) -> None:
    """過去成績・過去走のレース基本情報・競走馬マスタ・着度数は history_interface から取得する."""
    race_data_with_history.fetch_past_performances()
    race_data_with_history.fetch_past_race_basic_info()
    race_data_with_history.fetch_horse_master()
    race_data_with_history.fetch_chakudosu()

    mock_di_history.get_past_performances_bulk.assert_called_once()
    mock_di_history.get_race_basic_info_bulk.assert_called_once()
    mock_di_history.get_horse_master_bulk.assert_called_once()
    mock_di_history.get_chakudosu.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_past_performances_bulk.assert_not_called()
    mock_di_past.get_race_basic_info_bulk.assert_not_called()
    mock_di_past.get_horse_master_bulk.assert_not_called()
    mock_di_past.get_chakudosu.assert_not_called()


def test_fetch_all_splits_calls_between_interfaces(
    race_data_with_history: RaceData, mock_di_past: MagicMock, mock_di_history: MagicMock
) -> None:
    """fetch_all でも対象レースの情報と過去情報で取得先が分かれる."""
    race_data_with_history.fetch_all()

    mock_di_past.get_result.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_win_show_odds.assert_called_once_with(PAST_RACE_CODE)
    mock_di_past.get_win_show_votes.assert_called_once_with(PAST_RACE_CODE)
    mock_di_history.get_past_performances_bulk.assert_called_once()
    mock_di_history.get_race_basic_info_bulk.assert_called_once()
    mock_di_history.get_horse_master_bulk.assert_called_once()
    mock_di_history.get_chakudosu.assert_called_once_with(PAST_RACE_CODE)
    mock_di_history.get_result.assert_not_called()
    mock_di_history.get_win_show_odds.assert_not_called()
    mock_di_past.get_past_performances_bulk.assert_not_called()
    mock_di_past.get_chakudosu.assert_not_called()
