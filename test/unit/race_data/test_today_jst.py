"""today_jst のテスト."""

import datetime
from zoneinfo import ZoneInfo

from race_data.race_data import JST, today_jst


# 正常系
def test_today_jst_uses_japan_date_for_utc_time() -> None:
    """UTC では前日でも日本時間では翌日になる時刻は、日本時間の日付を返す."""
    now = datetime.datetime(2026, 9, 5, 23, 30, tzinfo=ZoneInfo("UTC"))  # JST 9/6 08:30
    assert today_jst(now) == datetime.date(2026, 9, 6)


def test_today_jst_keeps_japan_date_for_jst_time() -> None:
    """日本時間の時刻はそのままの日付を返す."""
    now = datetime.datetime(2026, 9, 5, 8, 30, tzinfo=JST)
    assert today_jst(now) == datetime.date(2026, 9, 5)


def test_today_jst_without_argument_is_japan_today() -> None:
    """引数を省略すると日本時間の今日を返す."""
    assert today_jst() == datetime.datetime.now(tz=JST).date()
