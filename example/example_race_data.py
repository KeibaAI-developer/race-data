"""RaceData を使ったレース情報取得のサンプルスクリプト.

DataInterface を使用して、指定したレースコードのレースデータを
取得してレース情報・出馬表・結果・過去成績フィルタリングを表示する。
"""

import argparse

import pandas as pd
from keiba_data_interface import DataInterface

from race_data.race_data import RaceData


def _show_df_head(df: pd.DataFrame, cols: list[str] | None = None, n: int = 3) -> None:
    """DataFrame の先頭 n 行を表示する."""
    if df.empty:
        print("  (データなし)")
        return
    target = df[cols] if cols is not None else df
    print(target.head(n).to_string(index=False))


def main() -> None:
    """メイン処理.

    レースコードを指定して RaceData を作成し、レース情報を表示する。
    """
    parser = argparse.ArgumentParser(description="RaceData サンプルスクリプト")
    parser.add_argument(
        "--race-code",
        default="2023112605050812",
        help="16桁レースコード（年4+月日4+競馬場2+回2+日目2+R2）",
    )
    parser.add_argument(
        "--provider",
        default="mykeibadb",
        choices=["scraping", "mykeibadb"],
        help="データプロバイダー名",
    )
    args = parser.parse_args()

    di = DataInterface(provider=args.provider)
    rd = RaceData(race_code=args.race_code, data_interface=di)
    rd.fetch_all()

    print(f"レースコード : {rd.race_code}")
    print(f"未来のレース : {rd.future_race}")
    print(f"出走頭数     : {rd.num_runners}")
    print(f"馬場コード   : {rd.baba_code}")
    print(f"新馬戦       : {rd.is_make_debut()}")
    print(f"障害         : {rd.is_steeple_chase()}")
    print(f"直線         : {rd.is_straight_race()}")
    print(f"芝           : {rd.is_turf()}")
    print(f"ダート        : {rd.is_dirt()}")
    print(f"良馬場       : {rd.is_good_to_firm()}")
    print(f"出走する馬番   : {rd.valid_horse_num}")
    print(f"出走頭数: {len(rd.valid_horse_num)}")

    print("\n【レース基本情報】")
    for col in rd.race_basic_info_df.columns:
        val = rd.race_basic_info_df[col].iloc[0]
        if pd.notna(val):
            print(f"  {col}: {val}")

    entry_display_cols = [
        col
        for col in ["馬番", "馬名", "騎手名略称", "単勝オッズ", "単勝人気順"]
        if col in rd.entry_df.columns
    ]
    print("\n【出馬表（先頭3行）】")
    _show_df_head(rd.entry_df, entry_display_cols)

    if not rd.future_race and not rd.result_df.empty:
        result_display_cols = [
            col
            for col in ["確定着順", "馬番", "馬名", "走破タイム", "後3ハロン"]
            if col in rd.result_df.columns
        ]
        print("\n【レース結果（先頭3行）】")
        _show_df_head(rd.result_df, result_display_cols)

    if rd.past_performances_dict:
        first_uma_ban = min(rd.past_performances_dict.keys())
        filtered = rd.get_filtered_past_performances(first_uma_ban)
        pp_display_cols = [
            col
            for col in ["レースコード", "競馬場コード", "確定着順", "単勝人気順"]
            if col in filtered.columns
        ]
        print(f"\n【馬番 {first_uma_ban} の過去成績（フィルタリング済み、先頭3行）】")
        _show_df_head(filtered, pp_display_cols)


if __name__ == "__main__":
    main()
