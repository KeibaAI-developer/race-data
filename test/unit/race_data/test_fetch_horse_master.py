"""RaceData.fetch_horse_master のテスト."""

import pandas as pd
import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_entry_df, make_horse_master_df, make_mock_di

# 正常系


def test_fetch_horse_master_sets_dict(past_race_data: RaceData) -> None:
    """fetch_horse_master 後に horse_master_dict を参照できる."""
    past_race_data.fetch_horse_master()
    expected_ids = set(make_entry_df()["血統登録番号"])
    assert set(past_race_data.horse_master_dict.keys()) == expected_ids


def test_fetch_horse_master_fetches_all_horses_at_once(past_race_data: RaceData) -> None:
    """fetch_horse_master が全出走馬ぶんを1回でまとめて取得する.

    馬ごとに取得すると頭数ぶんの往復と変換が積み上がる。
    """
    di = past_race_data.data_interface

    past_race_data.fetch_horse_master()

    di.get_horse_master_bulk.assert_called_once()
    di.get_horse_master.assert_not_called()


def test_fetch_horse_master_passes_unique_horse_ids(past_race_data: RaceData) -> None:
    """fetch_horse_master が重複を除いた血統登録番号を渡す."""
    di = past_race_data.data_interface
    expected_horse_ids = list(make_entry_df()["血統登録番号"])

    past_race_data.fetch_horse_master()

    passed = di.get_horse_master_bulk.call_args.args[0]
    assert passed == expected_horse_ids


def test_fetch_horse_master_maps_each_horse_to_its_own_master() -> None:
    """馬IDとマスタの対応が入れ替わらない.

    カラム構成・dtype・行順・indexまで含めて一致することを検証する。
    """
    horse_ids = list(make_entry_df()["血統登録番号"])
    by_horse_id = {
        horse_id: make_horse_master_df(horse_id=horse_id, horse_name=f"テスト馬{index}")
        for index, horse_id in enumerate(horse_ids)
    }
    mock_di = make_mock_di(horse_master_by_horse_id=by_horse_id)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)

    race_data.fetch_horse_master()

    result = race_data.horse_master_dict
    assert list(result) == horse_ids
    for horse_id in horse_ids:
        pd.testing.assert_frame_equal(result[horse_id], by_horse_id[horse_id])


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
