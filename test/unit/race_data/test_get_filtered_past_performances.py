"""RaceData.get_filtered_past_performances のテスト."""

import pytest

from race_data.race_data import RaceData

from .conftest import _PAST_RACE_CODE, _make_mock_di, _make_past_performances_df

# 正常系


def test_filters_out_non_central(past_race_data: RaceData) -> None:
    """地方競馬（競馬場コード '00'）は除外される."""
    past_race_data.past_performances_dict[1] = _make_past_performances_df(
        keibajo_codes=["05", "00"],
    )
    result = past_race_data.get_filtered_past_performances(1)
    assert len(result) == 1
    assert result["競馬場コード"].iloc[0] == "05"


def test_filters_out_scratched(past_race_data: RaceData) -> None:
    """出走取消（異常区分コード '1'）は除外される."""
    past_race_data.past_performances_dict[1] = _make_past_performances_df(
        ijo_codes=["0", "1"],
    )
    result = past_race_data.get_filtered_past_performances(1)
    assert len(result) == 1
    assert result["異常区分コード"].iloc[0] == "0"


def test_filters_out_excluded_by_starters(past_race_data: RaceData) -> None:
    """発走除外（異常区分コード '2'）は除外される."""
    past_race_data.past_performances_dict[1] = _make_past_performances_df(
        ijo_codes=["0", "2"],
    )
    result = past_race_data.get_filtered_past_performances(1)
    assert len(result) == 1


def test_filters_out_excluded_by_stewards(past_race_data: RaceData) -> None:
    """競走除外（異常区分コード '3'）は除外される."""
    past_race_data.past_performances_dict[1] = _make_past_performances_df(
        ijo_codes=["0", "3"],
    )
    result = past_race_data.get_filtered_past_performances(1)
    assert len(result) == 1


def test_keeps_normal_and_fall_to_finish(past_race_data: RaceData) -> None:
    """正常（'0'）と競走中止（'4'）は残る."""
    past_race_data.past_performances_dict[1] = _make_past_performances_df(
        ijo_codes=["0", "4"],
    )
    result = past_race_data.get_filtered_past_performances(1)
    assert len(result) == 2


def test_all_central_codes_accepted() -> None:
    """中央競馬の全競馬場コード（'01' 〜 '10'）が通過する."""
    central_codes = [f"{i:02d}" for i in range(1, 11)]
    mock_di = _make_mock_di(
        past_performances_df=_make_past_performances_df(
            race_codes=[f"202301010{i:02d}0101" for i in range(1, 11)],
            keibajo_codes=central_codes,
            ijo_codes=["0"] * 10,
        )
    )
    race_data = RaceData(race_code=_PAST_RACE_CODE, data_interface=mock_di)
    result = race_data.get_filtered_past_performances(1)
    assert len(result) == 10


def test_index_is_reset(past_race_data: RaceData) -> None:
    """フィルタリング後のインデックスがリセットされる."""
    past_race_data.past_performances_dict[1] = _make_past_performances_df(
        ijo_codes=["1", "0"],
    )
    result = past_race_data.get_filtered_past_performances(1)
    assert list(result.index) == [0]


# 準正常系


def test_raises_key_error_for_unknown_uma_ban(past_race_data: RaceData) -> None:
    """存在しない馬番を指定すると KeyError が発生する."""
    with pytest.raises(KeyError):
        past_race_data.get_filtered_past_performances(99)
