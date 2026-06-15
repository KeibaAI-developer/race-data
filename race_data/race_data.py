"""レース情報の型定義."""

import datetime
from dataclasses import dataclass, field

import pandas as pd
from keiba_data_interface import DataInterface

_CENTRAL_KEIBAJO_CODES: frozenset[str] = frozenset(f"{i:02d}" for i in range(1, 11))
_EXCLUDE_IJO_CODES: frozenset[str] = frozenset({"1", "2", "3"})


@dataclass
class RaceData:
    """指定したレースの情報を格納するデータクラス.

    未来のレースと過去のレースいずれにも対応する。
    データ取得には keiba-data-interface の DataInterface を使用する。

    Attributes:
        race_code (str): 16桁レースコード（年(4)+月日(4)+競馬場(2)+回(2)+日目(2)+R(2)）
        data_interface (DataInterface): データ取得インターフェース
        baba_code (str): 馬場状態コード。"1"(良), "2"(稍), "3"(重), "4"(不) のいずれか。
            省略時は race_basic_info_df から自動設定
        future_race (bool): 未来のレースかどうか
        race_basic_info_df (pd.DataFrame): レース基本情報（1行）
        entry_df (pd.DataFrame): 出馬表（常に取得）
        result_df (pd.DataFrame): レース結果。fetch_result 後に参照可能
        race_result_info_df (pd.DataFrame): ラップタイム・コーナー通過順。fetch_result 後に参照可能
        payoff_df (pd.DataFrame): 払戻情報。fetch_result 後に参照可能
        win_show_odds_df (pd.DataFrame): 単複オッズ情報。fetch_odds 後に参照可能
        past_performances_dict (dict[int, pd.DataFrame]): 各馬の過去成績辞書。fetch_past_performances 後に参照可能
        horse_master_dict (dict[str, pd.DataFrame]): 各馬のマスタ情報辞書。fetch_horse_master 後に参照可能
        num_runners (int): 出走頭数（競走除外などは除く）
        valid_horse_num (list[int]): 出走予定の馬番リスト（異常区分コードが1,2,3の馬を除く）。昇順
    """

    race_code: str
    data_interface: DataInterface = field(repr=False)
    baba_code: str = ""
    future_race: bool = field(init=False, default=False)
    race_basic_info_df: pd.DataFrame = field(init=False, default_factory=pd.DataFrame)
    entry_df: pd.DataFrame = field(init=False, default_factory=pd.DataFrame)
    num_runners: int = field(init=False, default=0)
    valid_horse_num: list[int] = field(init=False, default_factory=list)
    _result_df: pd.DataFrame | None = field(init=False, default=None)
    _race_result_info_df: pd.DataFrame | None = field(init=False, default=None)
    _payoff_df: pd.DataFrame | None = field(init=False, default=None)
    _win_show_odds_df: pd.DataFrame | None = field(init=False, default=None)
    _past_performances_dict: dict[int, pd.DataFrame] | None = field(init=False, default=None)
    _horse_master_dict: dict[str, pd.DataFrame] | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """データを初期化する."""
        self.future_race = self._is_future_race()
        self.race_basic_info_df = self.data_interface.get_race_basic_info(self.race_code)
        self.entry_df = self.data_interface.get_entry(self.race_code)
        self.num_runners = self._calculate_num_runners()
        self.valid_horse_num = self._build_valid_horse_num()
        if not self.baba_code:
            self.baba_code = self._get_baba_code()

    def fetch_result(self) -> None:
        """結果系データを取得する."""
        self._result_df = self.data_interface.get_result(self.race_code)
        self._race_result_info_df = self.data_interface.get_race_result_info(self.race_code)
        self._payoff_df = self.data_interface.get_payoff(self.race_code)

    def fetch_odds(self) -> None:
        """単複オッズを取得する."""
        self._win_show_odds_df = self.data_interface.get_win_show_odds(self.race_code)
        if pd.isna(self.race_basic_info_df["出走頭数"].iloc[0]):
            self.num_runners = int(self._win_show_odds_df["単勝人気"].notna().sum())

    def fetch_past_performances(self) -> None:
        """各馬の過去成績辞書を取得する."""
        self._past_performances_dict = self._build_past_performances_dict()

    def fetch_horse_master(self) -> None:
        """各馬のマスタ情報辞書を取得する."""
        self._horse_master_dict = self._build_horse_master_dict()

    def fetch_all(self) -> None:
        """遅延取得対象をすべて取得する."""
        if not self.future_race:
            self.fetch_result()
        else:
            self._result_df = pd.DataFrame()
            self._race_result_info_df = pd.DataFrame()
            self._payoff_df = pd.DataFrame()
        self.fetch_odds()
        self.fetch_past_performances()
        self.fetch_horse_master()

    @property
    def result_df(self) -> pd.DataFrame:
        """レース結果を返す.

        Raises:
            RuntimeError: fetch_result が未実行の場合
        """
        if self._result_df is None:
            raise RuntimeError("result_df is not fetched. Call fetch_result() first.")
        return self._result_df

    @property
    def race_result_info_df(self) -> pd.DataFrame:
        """ラップタイム・コーナー通過順を返す.

        Raises:
            RuntimeError: fetch_result が未実行の場合
        """
        if self._race_result_info_df is None:
            raise RuntimeError("race_result_info_df is not fetched. Call fetch_result() first.")
        return self._race_result_info_df

    @property
    def payoff_df(self) -> pd.DataFrame:
        """払戻情報を返す.

        Raises:
            RuntimeError: fetch_result が未実行の場合
        """
        if self._payoff_df is None:
            raise RuntimeError("payoff_df is not fetched. Call fetch_result() first.")
        return self._payoff_df

    @property
    def win_show_odds_df(self) -> pd.DataFrame:
        """単複オッズ情報を返す.

        Raises:
            RuntimeError: fetch_odds が未実行の場合
        """
        if self._win_show_odds_df is None:
            raise RuntimeError("win_show_odds_df is not fetched. Call fetch_odds() first.")
        return self._win_show_odds_df

    @property
    def past_performances_dict(self) -> dict[int, pd.DataFrame]:
        """各馬の過去成績辞書を返す.

        Raises:
            RuntimeError: fetch_past_performances が未実行の場合
        """
        if self._past_performances_dict is None:
            raise RuntimeError(
                "past_performances_dict is not fetched. Call fetch_past_performances() first."
            )
        return self._past_performances_dict

    @property
    def horse_master_dict(self) -> dict[str, pd.DataFrame]:
        """各馬のマスタ情報辞書を返す.

        Raises:
            RuntimeError: fetch_horse_master が未実行の場合
        """
        if self._horse_master_dict is None:
            raise RuntimeError("horse_master_dict is not fetched. Call fetch_horse_master() first.")
        return self._horse_master_dict

    def is_make_debut(self) -> bool:
        """新馬戦かどうかを判定する.

        Returns:
            bool: 新馬戦なら True
        """
        return str(self.race_basic_info_df["競走条件コード"].iloc[0]) == "701"

    def is_steeple_chase(self) -> bool:
        """障害レースかどうかを判定する.

        Returns:
            bool: 障害レースなら True
        """
        return str(self.race_basic_info_df["レース種別"].iloc[0]) == "障害"

    def is_straight_race(self) -> bool:
        """直線コースかどうかを判定する.

        Returns:
            bool: 直線コースなら True
        """
        return str(self.race_basic_info_df["左右"].iloc[0]) == "直"

    def is_turf(self) -> bool:
        """芝レースかどうかを判定する.

        Returns:
            bool: 芝レースなら True
        """
        return str(self.race_basic_info_df["芝ダ"].iloc[0]) == "芝"

    def is_dirt(self) -> bool:
        """ダートレースかどうかを判定する.

        Returns:
            bool: ダートレースなら True
        """
        return str(self.race_basic_info_df["芝ダ"].iloc[0]) == "ダ"

    def is_good_to_firm(self) -> bool:
        """良馬場かどうかを判定する.

        Returns:
            bool: 良馬場なら True
        """
        return self.baba_code == "1"

    def get_filtered_past_performances(self, uma_ban: int) -> pd.DataFrame:
        """指定馬番の過去成績から機械学習に有効なデータのみを抽出する.

        フィルタリング条件:
        - 中央競馬のみ（競馬場コードが "01" から "10"）
        - 競走除外を除く（異常区分コードが "1", "2", "3" でない）

        Args:
            uma_ban (int): 馬番

        Returns:
            pd.DataFrame: フィルタリング済みの過去成績

        Raises:
            RuntimeError: fetch_past_performances が未実行の場合
            KeyError: 指定馬番が past_performances_dict に存在しない場合
        """
        pp_df = self.past_performances_dict[uma_ban]
        filtered = pp_df[
            pp_df["競馬場コード"].isin(_CENTRAL_KEIBAJO_CODES)
            & ~pp_df["異常区分コード"].isin(_EXCLUDE_IJO_CODES)
        ]
        return filtered.reset_index(drop=True)

    def _calculate_num_runners(self) -> int:
        """出走頭数を計算する.

        race_basic_info_df の「出走頭数」から取得する。NaN の場合は0を返す。
        """
        shutsu_val = self.race_basic_info_df["出走頭数"].iloc[0]
        if pd.notna(shutsu_val):
            return int(shutsu_val)
        return 0

    def _build_valid_horse_num(self) -> list[int]:
        """出走予定の馬番リストを構築する.

        entry_df の異常区分コードが "1", "2", "3" の馬を除いた馬番を昇順で返す。
        """
        valid = self.entry_df[~self.entry_df["異常区分コード"].isin(_EXCLUDE_IJO_CODES)]
        return sorted(valid["馬番"].tolist())

    def _build_past_performances_dict(self) -> dict[int, pd.DataFrame]:
        """entry_df の各馬の過去成績辞書を構築する."""
        sorted_entry = self.entry_df.sort_values("馬番").reset_index(drop=True)
        past_performances: dict[int, pd.DataFrame] = {}
        for _, row in sorted_entry.iterrows():
            horse_id = str(row["血統登録番号"])
            uma_ban = int(row["馬番"])
            pp_df = self.data_interface.get_past_performances(horse_id)
            pp_df = pp_df[pp_df["レースコード"] < self.race_code].reset_index(drop=True)
            past_performances[uma_ban] = pp_df
        return past_performances

    def _build_horse_master_dict(self) -> dict[str, pd.DataFrame]:
        """entry_df の各馬のマスタ情報辞書を構築する."""
        horse_master: dict[str, pd.DataFrame] = {}
        for horse_id in self.entry_df["血統登録番号"].unique():
            horse_id_str = str(horse_id)
            horse_master[horse_id_str] = self.data_interface.get_horse_master(horse_id_str)
        return horse_master

    def _get_baba_code(self) -> str:
        """race_basic_info_df から馬場状態コードを取得する."""
        if self.is_turf():
            code = self.race_basic_info_df["芝馬場状態コード"].iloc[0]
        else:
            code = self.race_basic_info_df["ダート馬場状態コード"].iloc[0]
        if pd.notna(code):
            return str(code)
        return ""

    def _is_future_race(self) -> bool:
        """race_code の日付と現在日付を比較して未来のレースかどうか判定する.

        Returns:
            bool: 同日を含む未来のレースなら True
        """
        race_date_str = self.race_code[:8]
        today_str = datetime.date.today().strftime("%Y%m%d")
        return race_date_str >= today_str
