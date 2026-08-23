"""RaceData.fetch_past_performances のテスト."""

import pandas as pd
import pytest

from race_data.race_data import RaceData

from .conftest import (
    PAST_RACE_CODE,
    make_entry_df,
    make_mock_di,
    make_past_performances_df,
)

# 正常系


def test_fetch_past_performances_sets_dict(past_race_data: RaceData) -> None:
    """fetch_past_performances 後に past_performances_dict を参照できる."""
    past_race_data.fetch_past_performances()
    assert set(past_race_data.past_performances_dict.keys()) == {1, 2, 3}


def test_fetch_past_performances_fetches_all_horses_at_once(past_race_data: RaceData) -> None:
    """fetch_past_performances が全出走馬ぶんを1回でまとめて取得する.

    馬ごとに取得すると頭数ぶんのクエリが発行される。血統登録番号だけの絞り込みは
    主キーの前方一致にならず、1頭あたり約276msかかる。
    """
    di = past_race_data.data_interface

    past_race_data.fetch_past_performances()

    di.get_past_performances_bulk.assert_called_once()
    di.get_past_performances.assert_not_called()


def test_fetch_past_performances_passes_all_horse_ids(past_race_data: RaceData) -> None:
    """fetch_past_performances が全出走馬の血統登録番号を渡す."""
    di = past_race_data.data_interface
    expected = [str(horse_id) for horse_id in past_race_data.entry_df["血統登録番号"]]

    past_race_data.fetch_past_performances()

    passed = di.get_past_performances_bulk.call_args.args[0]
    assert sorted(passed) == sorted(expected)


def test_fetch_past_performances_maps_each_horse_to_its_own_uma_ban() -> None:
    """馬番と過去成績の対応が入れ替わらない.

    一括取得は馬IDをキーに返すため、馬番との対応づけを誤ると別の馬の過去成績が
    入る。カラム構成・dtype・行順・indexまで含めて一致することを検証する。
    """
    horse_ids = ["2019105219", "2020103656", "2021190001"]
    entry_df = make_entry_df(uma_bans=[1, 2, 3], horse_ids=horse_ids)
    # 馬ごとに異なる過去成績を用意する（レースコードの下2桁で見分ける）
    by_horse_id = {
        horse_id: make_past_performances_df(
            race_codes=[f"20221126050508{index}1", f"20211126050508{index}1"],
        )
        for index, horse_id in enumerate(horse_ids)
    }
    mock_di = make_mock_di(entry_df=entry_df, past_performances_by_horse_id=by_horse_id)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)

    race_data.fetch_past_performances()

    result = race_data.past_performances_dict
    assert list(result) == [1, 2, 3]
    for uma_ban, horse_id in zip([1, 2, 3], horse_ids, strict=True):
        expected = by_horse_id[horse_id].reset_index(drop=True)
        pd.testing.assert_frame_equal(result[uma_ban], expected)


def test_fetch_past_performances_excludes_future_races() -> None:
    """対象レース以降の過去成績が除外される."""
    pp_with_future = make_past_performances_df(
        race_codes=["2022112605050812", "2024010105050801"],
    )
    mock_di = make_mock_di(past_performances_df=pp_with_future)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)

    race_data.fetch_past_performances()

    for pp_df in race_data.past_performances_dict.values():
        assert all(pp_df["レースコード"] < PAST_RACE_CODE)


# 準正常系


def test_past_performances_dict_raises_before_fetch(past_race_data: RaceData) -> None:
    """fetch_past_performances 前に past_performances_dict 参照で RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_past_performances"):
        _ = past_race_data.past_performances_dict
