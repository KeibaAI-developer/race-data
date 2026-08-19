"""RaceData.fetch_past_performances のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE, make_mock_di, make_past_performances_df

# 正常系


def test_fetch_past_performances_sets_dict(past_race_data: RaceData) -> None:
    """fetch_past_performances 後に past_performances_dict を参照できる."""
    past_race_data.fetch_past_performances()
    assert set(past_race_data.past_performances_dict.keys()) == {1, 2, 3}


def test_fetch_past_performances_calls_interface_per_horse(past_race_data: RaceData) -> None:
    """fetch_past_performances が馬ごとに get_past_performances を呼ぶ."""
    di = past_race_data.data_interface
    past_race_data.fetch_past_performances()
    assert di.get_past_performances.call_count == 3


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
