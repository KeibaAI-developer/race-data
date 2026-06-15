"""RaceData.fetch_horse_master のテスト."""

from unittest.mock import call

import pandas as pd
import pytest

from race_data.race_data import RaceData

from .conftest import make_entry_df

# 正常系


def test_fetch_horse_master_sets_dict(past_race_data: RaceData) -> None:
    """fetch_horse_master 後に horse_master_dict を参照できる."""
    past_race_data.fetch_horse_master()
    expected_ids = set(make_entry_df()["血統登録番号"])
    assert set(past_race_data.horse_master_dict.keys()) == expected_ids


def test_fetch_horse_master_calls_interface_per_horse(past_race_data: RaceData) -> None:
    """fetch_horse_master が馬ごとに get_horse_master を呼ぶ."""
    di = past_race_data.data_interface
    expected_horse_ids = list(make_entry_df()["血統登録番号"])

    past_race_data.fetch_horse_master()

    assert di.get_horse_master.call_count == len(expected_horse_ids)
    di.get_horse_master.assert_has_calls(
        [call(horse_id) for horse_id in expected_horse_ids],
        any_order=True,
    )


def test_fetch_horse_master_values_are_dataframes(past_race_data: RaceData) -> None:
    """horse_master_dict の各値が DataFrame である."""
    past_race_data.fetch_horse_master()
    for df in past_race_data.horse_master_dict.values():
        assert isinstance(df, pd.DataFrame)


# 準正常系


def test_horse_master_dict_raises_before_fetch(past_race_data: RaceData) -> None:
    """fetch_horse_master 前に horse_master_dict 参照で RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_horse_master"):
        _ = past_race_data.horse_master_dict
