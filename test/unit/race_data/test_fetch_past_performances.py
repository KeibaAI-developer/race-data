"""RaceData.fetch_past_performances のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_mock_di, make_past_performances_df

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
