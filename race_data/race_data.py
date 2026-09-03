"""レース情報の型定義."""

import datetime
import logging
from zoneinfo import ZoneInfo

import pandas as pd
from keiba_data_interface import DataInterface
from keiba_data_interface.exceptions import DataNotFoundError, UnsupportedOperationError
from keiba_data_interface.schema import RACE_BASIC_INFO_COLUMNS
from keiba_domain import (
    CENTRAL_KEIBAJO_CODES,
    Baba,
    Direction,
    RaceShubetsu,
    TurfDirt,
    baba_from_code,
)

_EXCLUDE_IJO_CODES: frozenset[str] = frozenset({"1", "2", "3"})


JST = ZoneInfo("Asia/Tokyo")


def today_jst(now: datetime.datetime | None = None) -> datetime.date:
    """日本時間の今日の日付を返す.

    レースの開催日は日本時間で決まるため、実行環境のタイムゾーンに依らず日本時間で判定する。

    Args:
        now (datetime.datetime | None): 現在時刻（タイムゾーン付き）。省略時は現在時刻

    Returns:
        datetime.date: 日本時間での今日
    """
    current = datetime.datetime.now(tz=JST) if now is None else now
    return current.astimezone(JST).date()


class RaceData:
    """指定したレースの情報を格納するクラス.

    未来のレースと過去のレースいずれにも対応する。
    データ取得には keiba-data-interface の DataInterface を使用する。取得先は 2 つに分かれ、
    対象レースの情報（レース基本情報・出馬表・オッズ・票数・結果系）は data_interface から、
    過去成績・過去走のレース基本情報・競走馬マスタ・着度数は history_interface から取得する。
    history_interface を省略すると data_interface を両方に使う。
    history_interface・baba_code・logger はキーワード専用引数で、位置引数での取り違えを防ぐ。

    Attributes:
        race_code (str): 16桁レースコード（年(4)+月日(4)+競馬場(2)+回(2)+日目(2)+R(2)）
        data_interface (DataInterface): 対象レースの情報の取得先（最新情報用）
        history_interface (DataInterface): 過去情報の取得先（アーカイブ用）。
            省略時は data_interface
        baba_code (str): 馬場状態コード。"1"(良), "2"(稍), "3"(重), "4"(不) のいずれか。
            省略時は race_basic_info_df から自動設定
        future_race (bool): 未来のレースかどうか
        race_basic_info_df (pd.DataFrame): レース基本情報（1行）
        entry_df (pd.DataFrame): 出馬表（常に取得）
        result_df (pd.DataFrame): レース結果。fetch_race_result または fetch_result 後に参照可能
        race_result_info_df (pd.DataFrame): ラップタイム・コーナー通過順。
            fetch_race_result_info または fetch_result 後に参照可能
        payoff_df (pd.DataFrame): 払戻情報。fetch_payoff または fetch_result 後に参照可能
        win_show_odds_df (pd.DataFrame): 単複オッズ情報。fetch_odds 後に参照可能
        win_show_odds_is_expected (bool): win_show_odds_df が発売前の予想オッズなら True
        win_show_votes_df (pd.DataFrame): 単複票数情報。fetch_votes 後に参照可能
            （fetch_all は票数に対応したプロバイダーでのみ取得する）
        past_performances_dict (dict[int, pd.DataFrame]): 各馬の過去成績辞書。
            fetch_past_performances 後に参照可能
        past_race_basic_info_df (pd.DataFrame): 全出走馬の過去走のレース基本情報。
            fetch_past_race_basic_info 後に参照可能
        horse_master_dict (dict[str, pd.DataFrame]): 各馬のマスタ情報辞書。
            fetch_horse_master 後に参照可能
        chakudosu_df (pd.DataFrame): 出走別着度数。fetch_chakudosu 後に参照可能
            （fetch_all は着度数に対応したプロバイダーでのみ取得する）
        num_runners (int): 出走頭数（競走除外などは除く）。レース基本情報の出走頭数が取得できない
            場合は valid_horse_num の数
        valid_horse_num (list[int]): 出走予定の馬番リスト（異常区分コードが1,2,3の馬を除く）。昇順
        logger (logging.Logger): ロガー。省略時は __name__ のロガー
    """

    def __init__(
        self,
        race_code: str,
        data_interface: DataInterface,
        *,
        history_interface: DataInterface | None = None,
        baba_code: str = "",
        logger: logging.Logger | None = None,
    ) -> None:
        self.race_code = race_code
        self.data_interface = data_interface
        self.history_interface = data_interface if history_interface is None else history_interface
        self.baba_code = baba_code
        self.logger = logger or logging.getLogger(__name__)
        self.win_show_odds_is_expected = False
        self._result_df: pd.DataFrame | None = None
        self._race_result_info_df: pd.DataFrame | None = None
        self._payoff_df: pd.DataFrame | None = None
        self._win_show_odds_df: pd.DataFrame | None = None
        self._win_show_votes_df: pd.DataFrame | None = None
        self._past_performances_dict: dict[int, pd.DataFrame] | None = None
        self._past_race_basic_info_df: pd.DataFrame | None = None
        self._horse_master_dict: dict[str, pd.DataFrame] | None = None
        self._chakudosu_df: pd.DataFrame | None = None
        self.future_race = self._is_future_race()
        self.race_basic_info_df = self.data_interface.get_race_basic_info(self.race_code)
        self.entry_df = self.data_interface.get_entry(self.race_code)
        self.valid_horse_num = self._build_valid_horse_num()
        self.num_runners = self._calculate_num_runners()
        if not self.baba_code:
            self.baba_code = self._get_baba_code()

    def fetch_race_result(self) -> None:
        """レース結果を取得する."""
        self._result_df = self.data_interface.get_result(self.race_code)

    def fetch_race_result_info(self) -> None:
        """ラップタイム・コーナー通過順を取得する."""
        self._race_result_info_df = self.data_interface.get_race_result_info(self.race_code)

    def fetch_payoff(self) -> None:
        """払戻情報を取得する."""
        self._payoff_df = self.data_interface.get_payoff(self.race_code)

    def fetch_result(self) -> None:
        """結果系データをまとめて取得する.

        レース結果・ラップタイム/コーナー通過順・払戻情報の3つを取得する。
        scrapingプロバイダーではこれらが同じページにあるため、個別に取得するより
        まとめて取得するほうが効率がよい。

        一部しか使わない場合は fetch_race_result / fetch_race_result_info /
        fetch_payoff を個別に呼ぶ。

        取得済みであっても取り直す。取得済みを理由に省略すると、値が変わりうる
        データを再取得できなくなるため。
        """
        self.fetch_race_result()
        self.fetch_race_result_info()
        self.fetch_payoff()

    def fetch_odds(self) -> None:
        """単複オッズを取得する.

        現在のオッズが無く（DataNotFoundError）レース日が今日より後なら、馬券発売前と判断して
        予想オッズ（get_expected_win_show_odds）を使い、win_show_odds_is_expected を True にする。
        レース日が今日以前にオッズが無いのは取得元の異常なので例外のままにする。

        Raises:
            DataNotFoundError: レース日が今日以前でオッズが無い場合、または発売前で
                予想オッズも無い場合
            UnsupportedOperationError: 発売前で、予想オッズに対応していないプロバイダーの場合
        """
        try:
            self._win_show_odds_df = self.data_interface.get_win_show_odds(self.race_code)
        except DataNotFoundError:
            if not self._is_before_race_day():
                raise
            self.logger.info("発売前のため予想オッズを使います: race_code=%s", self.race_code)
            self._win_show_odds_df = self.data_interface.get_expected_win_show_odds(self.race_code)
            self.win_show_odds_is_expected = True
            return
        self.win_show_odds_is_expected = False

    def fetch_votes(self) -> None:
        """単勝・複勝の票数を取得する.

        複勝支持率を票数から求めるために使う。

        Raises:
            DataNotFoundError: 該当レースの票数が存在しない場合
            UnsupportedOperationError: 票数に対応していないプロバイダー（scraping）の場合
        """
        self._win_show_votes_df = self.data_interface.get_win_show_votes(self.race_code)

    def fetch_past_performances(self) -> None:
        """各馬の過去成績辞書を取得する.

        過去走のレース基本情報（past_race_basic_info_df）は過去成績から組み立てるため、
        再取得時は未取得状態へ戻す。古い過去成績に基づく値が残らないようにする。
        """
        self._past_performances_dict = self._build_past_performances_dict()
        self._past_race_basic_info_df = None

    def fetch_past_race_basic_info(self) -> None:
        """全出走馬の過去走のレース基本情報を一括取得する.

        valid_horse_num の各馬の過去成績（get_filtered_past_performances）からレースコードを
        重複なく集め、history_interface の get_race_basic_info_bulk を1回だけ呼ぶ。
        fetch_past_performances() の実行後に呼ぶこと。

        複数の特徴量ライブラリが同じ取得を必要とするため、RaceData が1回だけ取得して保持する。

        Raises:
            RuntimeError: fetch_past_performances が未実行の場合
            UnsupportedOperationError: history_interface のプロバイダーが一括取得に
                対応していない場合（scraping）
        """
        self._past_race_basic_info_df = self._build_past_race_basic_info_df()

    def fetch_horse_master(self) -> None:
        """各馬のマスタ情報辞書を取得する."""
        self._horse_master_dict = self._build_horse_master_dict()

    def fetch_chakudosu(self) -> None:
        """出走別着度数を history_interface から取得する.

        Raises:
            DataNotFoundError: 該当レースの着度数が存在しない場合
            UnsupportedOperationError: 着度数に対応していないプロバイダー（scraping）の場合
        """
        self._chakudosu_df = self.history_interface.get_chakudosu(self.race_code)

    def fetch_all(self) -> None:
        """遅延取得対象をすべて取得する.

        プロバイダーが対応していない操作（UnsupportedOperationError。scraping の単複票数・
        過去走のレース基本情報の一括取得・着度数）は取得せず、該当属性の参照時に
        RuntimeError になる。
        データが存在しない場合（DataNotFoundError）はそのまま伝播する。
        """
        if not self.future_race:
            self.fetch_result()
        else:
            self._result_df = pd.DataFrame()
            self._race_result_info_df = pd.DataFrame()
            self._payoff_df = pd.DataFrame()
        self.fetch_odds()
        try:
            self.fetch_votes()
        except UnsupportedOperationError:
            pass
        self.fetch_past_performances()
        try:
            self.fetch_past_race_basic_info()
        except UnsupportedOperationError:
            pass
        self.fetch_horse_master()
        try:
            self.fetch_chakudosu()
        except UnsupportedOperationError:
            pass

    @property
    def result_df(self) -> pd.DataFrame:
        """レース結果を返す.

        Raises:
            RuntimeError: fetch_race_result も fetch_result も未実行の場合
        """
        if self._result_df is None:
            raise RuntimeError(
                "result_df is not fetched. Call fetch_race_result() or fetch_result() first."
            )
        return self._result_df

    @property
    def race_result_info_df(self) -> pd.DataFrame:
        """ラップタイム・コーナー通過順を返す.

        Raises:
            RuntimeError: fetch_race_result_info も fetch_result も未実行の場合
        """
        if self._race_result_info_df is None:
            raise RuntimeError(
                "race_result_info_df is not fetched. "
                "Call fetch_race_result_info() or fetch_result() first."
            )
        return self._race_result_info_df

    @property
    def payoff_df(self) -> pd.DataFrame:
        """払戻情報を返す.

        Raises:
            RuntimeError: fetch_payoff も fetch_result も未実行の場合
        """
        if self._payoff_df is None:
            raise RuntimeError(
                "payoff_df is not fetched. Call fetch_payoff() or fetch_result() first."
            )
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
    def win_show_votes_df(self) -> pd.DataFrame:
        """単複票数情報を返す.

        Raises:
            RuntimeError: fetch_votes が未実行の場合
        """
        if self._win_show_votes_df is None:
            raise RuntimeError("win_show_votes_df is not fetched. Call fetch_votes() first.")
        return self._win_show_votes_df

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
    def past_race_basic_info_df(self) -> pd.DataFrame:
        """全出走馬の過去走のレース基本情報を返す.

        RACE_BASIC_INFO_COLUMNS のカラムを持ち、レースコード昇順。存在しないレース
        （一括取得で返らなかったレースコード）の行は含めない。

        Raises:
            RuntimeError: fetch_past_race_basic_info が未実行の場合
        """
        if self._past_race_basic_info_df is None:
            raise RuntimeError(
                "past_race_basic_info_df is not fetched. Call fetch_past_race_basic_info() first."
            )
        return self._past_race_basic_info_df

    @property
    def horse_master_dict(self) -> dict[str, pd.DataFrame]:
        """各馬のマスタ情報辞書を返す.

        Raises:
            RuntimeError: fetch_horse_master が未実行の場合
        """
        if self._horse_master_dict is None:
            raise RuntimeError("horse_master_dict is not fetched. Call fetch_horse_master() first.")
        return self._horse_master_dict

    @property
    def chakudosu_df(self) -> pd.DataFrame:
        """出走別着度数を返す.

        Raises:
            RuntimeError: fetch_chakudosu が未実行の場合
        """
        if self._chakudosu_df is None:
            raise RuntimeError("chakudosu_df is not fetched. Call fetch_chakudosu() first.")
        return self._chakudosu_df

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
        return str(self.race_basic_info_df["レース種別"].iloc[0]) == RaceShubetsu.SHOGAI

    def is_straight_race(self) -> bool:
        """直線コースかどうかを判定する.

        Returns:
            bool: 直線コースなら True
        """
        return str(self.race_basic_info_df["左右"].iloc[0]) == Direction.STRAIGHT

    def is_turf(self) -> bool:
        """芝レースかどうかを判定する.

        Returns:
            bool: 芝レースなら True
        """
        return str(self.race_basic_info_df["芝ダ"].iloc[0]) == TurfDirt.TURF

    def is_dirt(self) -> bool:
        """ダートレースかどうかを判定する.

        Returns:
            bool: ダートレースなら True
        """
        return str(self.race_basic_info_df["芝ダ"].iloc[0]) == TurfDirt.DIRT

    def is_good_to_firm(self) -> bool:
        """良馬場かどうかを判定する.

        Returns:
            bool: 良馬場なら True

        Raises:
            KeibaDomainError: baba_code が "0"〜"4" のいずれでもない場合（馬場状態コードが
                未取得で空文字の場合を含む）
        """
        return baba_from_code(self.baba_code) == Baba.GOOD

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
            pp_df["競馬場コード"].isin(CENTRAL_KEIBAJO_CODES)
            & ~pp_df["異常区分コード"].isin(_EXCLUDE_IJO_CODES)
        ]
        return filtered.reset_index(drop=True)

    def _calculate_num_runners(self) -> int:
        """出走頭数を計算する.

        race_basic_info_df の「出走頭数」から取得する。取得できない（scraping など）場合は
        出馬表の出走予定馬（valid_horse_num）の数を使う。
        """
        shutsu_val = self.race_basic_info_df["出走頭数"].iloc[0]
        if pd.notna(shutsu_val):
            return int(shutsu_val)
        return len(self.valid_horse_num)

    def _build_valid_horse_num(self) -> list[int]:
        """出走予定の馬番リストを構築する.

        entry_df の異常区分コードが "1", "2", "3" の馬を除いた馬番を昇順で返す。
        """
        valid = self.entry_df[~self.entry_df["異常区分コード"].isin(_EXCLUDE_IJO_CODES)]
        return sorted(valid["馬番"].tolist())

    def _build_past_performances_dict(self) -> dict[int, pd.DataFrame]:
        """entry_df の各馬の過去成績辞書を構築する.

        出走馬ごとに取得すると頭数ぶんのクエリが発行される。umagoto_race_johoの主キーは
        (レースコード, 血統登録番号) であり、血統登録番号だけで絞り込むと主キーの前方一致に
        ならずインデックスを頭から走査するため、1頭あたり約276msかかる。まとめて取得する。

        今レースより前のレースへの絞り込みは、取得後に馬ごとへ当てる。一括取得の時点で
        絞り込まないのは、同じ馬が別のRaceDataから参照されたときにレースコードの違いで
        結果が変わってしまうため。

        Returns:
            dict[int, pd.DataFrame]: 馬番 → 今レースより前の過去成績。
                キーはentry_dfの馬番昇順
        """
        sorted_entry = self.entry_df.sort_values("馬番").reset_index(drop=True)
        horse_ids = [str(row["血統登録番号"]) for _, row in sorted_entry.iterrows()]
        pp_by_horse_id = self.history_interface.get_past_performances_bulk(horse_ids)
        return {
            int(row["馬番"]): self._filter_past_races(pp_by_horse_id[str(row["血統登録番号"])])
            for _, row in sorted_entry.iterrows()
        }

    def _filter_past_races(self, pp_df: pd.DataFrame) -> pd.DataFrame:
        """過去成績を今レースより前のレースだけに絞り込む.

        Args:
            pp_df (pd.DataFrame): 1頭分の過去成績

        Returns:
            pd.DataFrame: 今レースより前のレースだけを残した過去成績
        """
        return pp_df[pp_df["レースコード"] < self.race_code].reset_index(drop=True)

    def _build_past_race_basic_info_df(self) -> pd.DataFrame:
        """全出走馬の過去走のレース基本情報を組み立てる.

        Returns:
            pd.DataFrame: 過去走のレース基本情報（RACE_BASIC_INFO_COLUMNS、レースコード昇順）。
                過去走が1件も無ければ0行
        """
        race_codes: list[str] = []
        seen: set[str] = set()
        for uma_ban in self.valid_horse_num:
            for race_code in self.get_filtered_past_performances(uma_ban)["レースコード"]:
                code = str(race_code)
                if code not in seen:
                    seen.add(code)
                    race_codes.append(code)
        if not race_codes:
            return pd.DataFrame(columns=RACE_BASIC_INFO_COLUMNS)
        df = self.history_interface.get_race_basic_info_bulk(race_codes)
        return df.sort_values("レースコード").reset_index(drop=True)

    def _build_horse_master_dict(self) -> dict[str, pd.DataFrame]:
        """entry_df の各馬のマスタ情報辞書を構築する.

        出走馬ごとに取得すると頭数ぶんの往復と変換が積み上がる。まとめて取得する。

        一括取得の戻り値をそのまま返さず、要求した馬IDで組み立て直す。キーの集合と
        並びを取得側の実装に委ねないため。

        Returns:
            dict[str, pd.DataFrame]: 馬ID（血統登録番号）→ 競走馬マスタ（1行）。
                キーはentry_dfの出現順で重複を除いたもの
        """
        horse_ids = [str(horse_id) for horse_id in self.entry_df["血統登録番号"].unique()]
        horse_master_by_horse_id = self.history_interface.get_horse_master_bulk(horse_ids)
        return {horse_id: horse_master_by_horse_id[horse_id] for horse_id in horse_ids}

    def _get_baba_code(self) -> str:
        """race_basic_info_df から馬場状態コードを取得する."""
        if self.is_turf():
            code = self.race_basic_info_df["芝馬場状態コード"].iloc[0]
        else:
            code = self.race_basic_info_df["ダート馬場状態コード"].iloc[0]
        if pd.notna(code):
            return str(code)
        return ""

    def _is_before_race_day(self) -> bool:
        """レース日が今日（日本時間）より後かどうか（当日は含まない）."""
        return self.race_code[:8] > today_jst().strftime("%Y%m%d")

    def _is_future_race(self) -> bool:
        """race_code の日付と現在日付を比較して未来のレースかどうか判定する.

        Returns:
            bool: 同日を含む未来のレースなら True
        """
        race_date_str = self.race_code[:8]
        today_str = today_jst().strftime("%Y%m%d")
        return race_date_str >= today_str
