"""RaceData.fetch_past_race_basic_info のテスト."""

import pandas as pd
import pytest
from keiba_data_interface.exceptions import DataNotFoundError, UnsupportedOperationError
from keiba_data_interface.schema import RACE_BASIC_INFO_COLUMNS

from race_data.race_data import RaceData

from .conftest import (
    PAST_RACE_CODE,
    make_entry_df,
    make_mock_di,
    make_past_performances_df,
)


def _empty_past_performances_df() -> pd.DataFrame:
    """過去走が無い馬の過去成績（0行、文字列カラム）を作成する."""
    return pd.DataFrame({
        "レースコード": pd.Series([], dtype="object"),
        "競馬場コード": pd.Series([], dtype="object"),
        "異常区分コード": pd.Series([], dtype="object"),
    })


# 正常系


def test_fetch_past_race_basic_info_collects_unique_race_codes_in_one_call() -> None:
    """全出走馬の過去走のレースコードを重複なく集めて一括取得を1回だけ呼ぶ."""
    horse_ids = ["2019105219", "2020103656", "2021190001"]
    codes_a = ["2022112605050812", "2021112605050812"]
    codes_b = ["2022112605050812", "2020112605050812"]
    by_horse_id = {
        horse_ids[0]: make_past_performances_df(race_codes=codes_a),
        horse_ids[1]: make_past_performances_df(race_codes=codes_b),
        horse_ids[2]: _empty_past_performances_df(),
    }
    mock_di = make_mock_di(
        entry_df=make_entry_df(horse_ids=horse_ids), past_performances_by_horse_id=by_horse_id
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    race_data.fetch_past_performances()

    race_data.fetch_past_race_basic_info()

    mock_di.get_race_basic_info_bulk.assert_called_once()
    passed = mock_di.get_race_basic_info_bulk.call_args.args[0]
    assert passed == ["2022112605050812", "2021112605050812", "2020112605050812"]


def test_past_race_basic_info_df_is_sorted_by_race_code(past_race_data: RaceData) -> None:
    """past_race_basic_info_df はレースコード昇順で返る（取得側の並びに依存しない）."""
    past_race_data.fetch_past_performances()

    past_race_data.fetch_past_race_basic_info()

    codes = past_race_data.past_race_basic_info_df["レースコード"].tolist()
    assert codes == sorted(codes)
    assert codes == ["2021112605050812", "2022112605050812"]


def test_excluded_past_races_are_not_collected() -> None:
    """get_filtered_past_performances で除かれる過去走（地方・除外）のレースコードは集めない."""
    pp_df = make_past_performances_df(
        race_codes=["2022112605050812", "2022110130010101", "2022100105050801"],
        keibajo_codes=["05", "30", "05"],
        ijo_codes=["0", "0", "1"],
    )
    mock_di = make_mock_di(past_performances_df=pp_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    race_data.fetch_past_performances()

    race_data.fetch_past_race_basic_info()

    passed = mock_di.get_race_basic_info_bulk.call_args.args[0]
    assert passed == ["2022112605050812"]


def test_no_past_races_returns_empty_frame_without_fetching() -> None:
    """過去走が1件も無ければ一括取得を呼ばず、スキーマカラム付きの0行を返す."""
    mock_di = make_mock_di(past_performances_df=_empty_past_performances_df())
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    race_data.fetch_past_performances()

    race_data.fetch_past_race_basic_info()

    mock_di.get_race_basic_info_bulk.assert_not_called()
    df = race_data.past_race_basic_info_df
    assert df.empty
    assert list(df.columns) == RACE_BASIC_INFO_COLUMNS


def test_fetch_all_fetches_past_race_basic_info_when_bulk_supported(
    past_race_data: RaceData,
) -> None:
    """一括取得に対応したプロバイダーでは fetch_all が past_race_basic_info_df も取得する."""
    past_race_data.fetch_all()

    assert isinstance(past_race_data.past_race_basic_info_df, pd.DataFrame)


def test_fetch_all_skips_past_race_basic_info_when_bulk_not_supported() -> None:
    """一括取得に対応しないプロバイダーでは fetch_all は取得を省き、参照時に RuntimeError になる."""
    mock_di = make_mock_di()
    mock_di.get_race_basic_info_bulk.side_effect = UnsupportedOperationError("非対応")
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)

    race_data.fetch_all()

    with pytest.raises(RuntimeError, match="Call fetch_past_race_basic_info"):
        _ = race_data.past_race_basic_info_df


def test_fetch_all_propagates_data_not_found() -> None:
    """一括取得でデータが無い（DataNotFoundError）場合は fetch_all がそのまま伝播させる."""
    mock_di = make_mock_di()
    mock_di.get_race_basic_info_bulk.side_effect = DataNotFoundError("データなし")
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)

    with pytest.raises(DataNotFoundError):
        race_data.fetch_all()


# 準正常系


def test_fetch_before_past_performances_raises(past_race_data: RaceData) -> None:
    """fetch_past_performances 前に呼ぶと RuntimeError が発生する."""
    with pytest.raises(RuntimeError, match="Call fetch_past_performances"):
        past_race_data.fetch_past_race_basic_info()


def test_property_before_fetch_raises(past_race_data: RaceData) -> None:
    """fetch_past_race_basic_info 前に past_race_basic_info_df を参照すると RuntimeError."""
    with pytest.raises(RuntimeError, match="Call fetch_past_race_basic_info"):
        _ = past_race_data.past_race_basic_info_df


def test_refetching_past_performances_resets_past_race_basic_info(
    past_race_data: RaceData,
) -> None:
    """fetch_past_performances を再実行すると past_race_basic_info_df は未取得状態に戻る.

    過去成績から組み立てた値が、更新後の過去成績と食い違ったまま残らないようにする。
    """
    past_race_data.fetch_past_performances()
    past_race_data.fetch_past_race_basic_info()

    past_race_data.fetch_past_performances()

    with pytest.raises(RuntimeError, match="Call fetch_past_race_basic_info"):
        _ = past_race_data.past_race_basic_info_df
