"""RaceDataの結果系データを個別に取得するメソッドのテスト.

fetch_result は結果・ラップタイム/コーナー通過順・払戻の3つをまとめて取得する。
一部しか使わない呼び出し側が不要な取得を避けられるよう、個別に取得できる。
"""

import pytest

from race_data.race_data import RaceData

from .conftest import PAST_RACE_CODE


# 正常系
def test_fetch_race_result_sets_result_df(past_race_data: RaceData) -> None:
    """fetch_race_result 後に result_df を参照できる."""
    past_race_data.fetch_race_result()

    assert not past_race_data.result_df.empty


def test_fetch_race_result_info_sets_race_result_info_df(past_race_data: RaceData) -> None:
    """fetch_race_result_info 後に race_result_info_df を参照できる."""
    past_race_data.fetch_race_result_info()

    assert past_race_data.race_result_info_df is not None


def test_fetch_payoff_sets_payoff_df(past_race_data: RaceData) -> None:
    """fetch_payoff 後に payoff_df を参照できる."""
    past_race_data.fetch_payoff()

    assert past_race_data.payoff_df is not None


@pytest.mark.parametrize(
    "method_name, called, not_called",
    [
        ("fetch_race_result", "get_result", ["get_race_result_info", "get_payoff"]),
        (
            "fetch_race_result_info",
            "get_race_result_info",
            ["get_result", "get_payoff"],
        ),
        ("fetch_payoff", "get_payoff", ["get_result", "get_race_result_info"]),
    ],
)
def test_individual_fetch_calls_only_its_own_interface_method(
    past_race_data: RaceData,
    method_name: str,
    called: str,
    not_called: list[str],
) -> None:
    """個別取得メソッドが対応する取得だけを行う.

    不要な取得を避けることが個別取得を用意した目的であるため、他の取得を
    呼ばないことを固定する。
    """
    di = past_race_data.data_interface

    getattr(past_race_data, method_name)()

    getattr(di, called).assert_called_once_with(PAST_RACE_CODE)
    for name in not_called:
        getattr(di, name).assert_not_called()


def test_fetch_result_matches_individual_fetches(
    past_race_data: RaceData, another_past_race_data: RaceData
) -> None:
    """fetch_result の結果が個別に3回呼んだ場合と一致する."""
    past_race_data.fetch_result()
    another_past_race_data.fetch_race_result()
    another_past_race_data.fetch_race_result_info()
    another_past_race_data.fetch_payoff()

    assert past_race_data.result_df.equals(another_past_race_data.result_df)
    assert past_race_data.race_result_info_df.equals(
        another_past_race_data.race_result_info_df
    )
    assert past_race_data.payoff_df.equals(another_past_race_data.payoff_df)


def test_fetch_result_refetches_after_individual_fetch(past_race_data: RaceData) -> None:
    """個別取得のあとに fetch_result を呼ぶと取り直す.

    取得済みを理由に省略すると、値が変わりうるデータを再取得できなくなる。
    """
    di = past_race_data.data_interface
    past_race_data.fetch_race_result()
    past_race_data.fetch_result()

    assert di.get_result.call_count == 2


# 準正常系
def test_other_properties_stay_unfetched_after_individual_fetch(
    past_race_data: RaceData,
) -> None:
    """個別取得しても、取得していないプロパティは未取得のままである."""
    past_race_data.fetch_race_result()

    with pytest.raises(RuntimeError, match="Call fetch_payoff"):
        _ = past_race_data.payoff_df
    with pytest.raises(RuntimeError, match="Call fetch_race_result_info"):
        _ = past_race_data.race_result_info_df
