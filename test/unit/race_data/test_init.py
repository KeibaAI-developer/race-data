"""RaceData の初期化のテスト."""

from unittest.mock import MagicMock

from race_data.race_data import RaceData

from .conftest import (
    FUTURE_RACE_CODE,
    PAST_RACE_CODE,
    make_entry_df,
    make_mock_di,
    make_race_basic_info_df,
)

# 正常系


def test_future_race_true_for_future_code(future_race_data: RaceData) -> None:
    """未来のレースコードで future_race が True になる."""
    assert future_race_data.future_race is True


def test_future_race_false_for_past_code(past_race_data: RaceData) -> None:
    """過去のレースコードで future_race が False になる."""
    assert past_race_data.future_race is False


def test_race_basic_info_df_fetched(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """race_basic_info_df が取得される."""
    mock_di_past.get_race_basic_info.assert_called_once_with(PAST_RACE_CODE)
    assert not past_race_data.race_basic_info_df.empty


def test_entry_df_fetched_for_past_race(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """過去レースでも entry_df が取得される."""
    mock_di_past.get_entry.assert_called_once_with(PAST_RACE_CODE)
    assert not past_race_data.entry_df.empty


def test_entry_df_fetched_for_future_race(
    future_race_data: RaceData, mock_di_future: MagicMock
) -> None:
    """未来レースでも entry_df が取得される."""
    mock_di_future.get_entry.assert_called_once_with(FUTURE_RACE_CODE)
    assert not future_race_data.entry_df.empty


def test_lazy_data_not_fetched_on_init(past_race_data: RaceData, mock_di_past: MagicMock) -> None:
    """初期化時に遅延データが取得されない."""
    mock_di_past.get_win_show_odds.assert_not_called()
    mock_di_past.get_result.assert_not_called()
    mock_di_past.get_race_result_info.assert_not_called()
    mock_di_past.get_payoff.assert_not_called()
    mock_di_past.get_past_performances.assert_not_called()
    mock_di_past.get_horse_master.assert_not_called()
    mock_di_past.get_chakudosu.assert_not_called()


def test_num_runners_from_race_basic_info(past_race_data: RaceData) -> None:
    """num_runners が race_basic_info_df の出走頭数から取得される."""
    assert past_race_data.num_runners == 16


def test_num_runners_zero_when_race_basic_info_missing() -> None:
    """出走頭数が NaN の場合は init 後 num_runners が0になる."""
    mock_di = make_mock_di(race_basic_info_df=make_race_basic_info_df(shutsu_count=None))
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.num_runners == 0


def test_baba_code_auto_set_from_turf(past_race_data: RaceData) -> None:
    """芝レースで baba_code が芝馬場状態コードから自動設定される."""
    assert past_race_data.baba_code == "1"


def test_baba_code_auto_set_from_dirt() -> None:
    """ダートレースで baba_code がダート馬場状態コードから自動設定される."""
    mock_di = make_mock_di(
        race_basic_info_df=make_race_basic_info_df(
            shiba_da="ダ",
            dart_baba_code="2",
        ),
    )
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.baba_code == "2"


def test_baba_code_overridden_by_constructor() -> None:
    """コンストラクタ引数 baba_code で自動設定が上書きされる."""
    mock_di = make_mock_di()
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di, baba_code="3")
    assert race_data.baba_code == "3"


def test_valid_horse_num_all_valid(past_race_data: RaceData) -> None:
    """全馬が有効な場合、全馬番が昇順に含まれる."""
    assert past_race_data.valid_horse_num == [1, 2, 3]


def test_valid_horse_num_excludes_ijo_code_1() -> None:
    """異常区分コード1の馬が valid_horse_num から除外される."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["1", "0", "0"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [2, 3]


def test_valid_horse_num_excludes_ijo_code_2() -> None:
    """異常区分コード2の馬が valid_horse_num から除外される."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["0", "2", "0"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [1, 3]


def test_valid_horse_num_excludes_ijo_code_3() -> None:
    """異常区分コード3の馬が valid_horse_num から除外される."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["0", "0", "3"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [1, 2]


def test_valid_horse_num_is_sorted() -> None:
    """entry_df の馬番順に関わらず valid_horse_num が昇順に並んでいる."""
    entry_df = make_entry_df(uma_bans=[3, 1, 2], ijo_codes=["0", "0", "0"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == [1, 2, 3]


def test_valid_horse_num_empty_when_all_excluded() -> None:
    """全馬が異常区分コード1,2,3の場合は空リストになる."""
    entry_df = make_entry_df(uma_bans=[1, 2, 3], ijo_codes=["1", "2", "3"])
    mock_di = make_mock_di(entry_df=entry_df)
    race_data = RaceData(race_code=PAST_RACE_CODE, data_interface=mock_di)
    assert race_data.valid_horse_num == []
