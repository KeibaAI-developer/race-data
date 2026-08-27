# race-data

## 概要

`race-data` は、競馬レースの情報を一括で保持するデータクラス `RaceData` を提供する Python ライブラリです。

`keiba-data-interface` の `DataInterface` を通じてレース基本情報・出馬表・レース結果・払戻情報・各馬の過去成績を取得し、1つのインスタンスにまとめて保持します。

- **未来のレース**（予測対象）と**過去のレース**（学習データ取得）の両方に対応
- レースコードの日付から未来/過去を自動判定（同日は未来扱い）
- 初期化時は確定データ（レース基本情報・出馬表）のみ取得し、結果・オッズ・過去成績・馬マスタは `fetch_*()` で明示的に取得する遅延取得設計
- 馬場状態・レース種別・コース形状の判定メソッドを提供
- 過去成績の機械学習向けフィルタリングをサポート


## 動作要件

- Python 3.12以上


## 依存パッケージ

- `pandas>=2.0.0`
- `keiba-data-interface`（PyPI非公開、後述のインストール手順を参照）


## インストール

```bash
pip install -e "/path/to/race-data"
```

`keiba-data-interface` は `pyproject.toml` で Git URL 依存関係として宣言されているため、上記コマンド一つで自動的にインストールされます。

ネットワーク制限などで GitHub にアクセスできない場合は、事前に手動でインストールしてください。

```bash
git clone https://github.com/KeibaAI-developer/keiba-data-interface
pip install -e ./keiba-data-interface
pip install -e "/path/to/race-data"
```


## セットアップ

データ取得には `keiba-data-interface` の `DataInterface` を使用します。使用するプロバイダー（`scraping` / `mykeibadb`）に応じたセットアップが必要です。

詳細は [keiba-data-interface の README](https://github.com/KeibaAI-developer/keiba-data-interface/blob/main/README.md) を参照してください。


## 使い方

### 基本的な使い方

`DataInterface` インスタンスと 16 桁レースコードを渡して `RaceData` をインスタンス化します。初期化時にはレース基本情報・出馬表など確定データのみが取得されます。

```python
from keiba_data_interface import DataInterface
from race_data import RaceData

di = DataInterface("mykeibadb")
race_code = "2023112605050812"
rd = RaceData(race_code=race_code, data_interface=di)

print(rd.future_race)   # False（過去のレース）
print(rd.num_runners)   # 出走頭数
print(rd.baba_code)     # "1"（良馬場）

print(rd.is_turf())          # True（芝レース）
print(rd.is_good_to_firm())  # True（良馬場）
```

### 遅延データを取得する

`result_df` / `race_result_info_df` / `payoff_df` / `win_show_odds_df` / `win_show_votes_df` / `past_performances_dict` / `past_race_basic_info_df` / `horse_master_dict` は初期化時には取得されません。各 `fetch_*()` を呼び出した後にのみ参照できます。未取得の状態でアクセスすると `RuntimeError` が発生します。

```python
rd = RaceData(race_code=race_code, data_interface=di)

try:
    rd.result_df
except RuntimeError as exc:
    print(exc)  # result_df is not fetched. Call fetch_race_result() or fetch_result() first.

rd.fetch_result()             # result_df / race_result_info_df / payoff_df を取得
rd.fetch_odds()                # win_show_odds_df を取得
rd.fetch_votes()               # win_show_votes_df を取得（mykeibadb のみ）
rd.fetch_past_performances()   # past_performances_dict を取得
rd.fetch_past_race_basic_info() # past_race_basic_info_df を取得（fetch_past_performances の後）
rd.fetch_horse_master()        # horse_master_dict を取得

print(rd.result_df)
print(rd.win_show_odds_df)
```

すべての遅延データをまとめて取得するには `fetch_all()` を使用します。未来レースでは結果系（`result_df` / `race_result_info_df` / `payoff_df`）は取得されず空の `DataFrame` になります。
`win_show_votes_df` と `past_race_basic_info_df` は対応したプロバイダー（mykeibadb）でのみ `fetch_all()` で取得されます。対応していないプロバイダー（scraping。`UnsupportedOperationError`）では取得せず、参照時に `RuntimeError` になります。

### 過去走のレース基本情報

過去成績（`past_performances_dict`）には芝ダ・距離・馬場状態など過去走のレース条件が含まれません。全出走馬の過去走のレース基本情報を `fetch_past_race_basic_info()` で1回にまとめて取得し、`past_race_basic_info_df`（レースコード昇順）から参照します。特徴量ライブラリはこれを使い、`get_race_basic_info_bulk` を直接呼びません。

```python
rd.fetch_past_performances()
rd.fetch_past_race_basic_info()
info_by_race_code = rd.past_race_basic_info_df.set_index("レースコード")
```


### 結果系データを個別に取得する

`fetch_result()` は結果・ラップタイム/コーナー通過順・払戻の3つをまとめて取得します。一部しか使わない場合は個別に取得できます。

```python
rd.fetch_race_result()        # result_df のみ取得
rd.fetch_race_result_info()   # race_result_info_df のみ取得
rd.fetch_payoff()             # payoff_df のみ取得
```

`scraping` プロバイダーではこれら3つが**同じページ**にあるため、3つとも必要な場合は `fetch_result()` でまとめて取得するほうが効率的です。一部しか使わない場合や `mykeibadb` プロバイダーでは、個別に取得することで不要な取得を避けられます。

取得済みであっても取り直します。取得済みを理由に省略すると、値が変わりうるデータを再取得できなくなるためです。

```python
rd.fetch_all()
```

### 馬場状態を上書きする

過去レースの分析などで実際とは異なる馬場状態を仮定したい場合、`baba_code` を指定します。

```python
rd = RaceData(race_code=race_code, data_interface=di, baba_code="3")  # 重馬場と仮定
print(rd.is_good_to_firm())  # False
```

### 各馬の過去成績にアクセスする

`past_performances_dict` は馬番をキーとした辞書です。`fetch_past_performances()` で取得した後に参照できます。`get_filtered_past_performances` で機械学習に有効なデータ（中央競馬のみ、競走除外除く）に絞り込めます。

```python
rd.fetch_past_performances()

# 馬番 1 の有効な過去成績を取得
filtered_df = rd.get_filtered_past_performances(1)
print(filtered_df)

# すべての馬の過去成績を処理する例
for uma_ban, pp_df in rd.past_performances_dict.items():
    filtered = rd.get_filtered_past_performances(uma_ban)
    print(f"馬番 {uma_ban}: {len(filtered)} レース")
```

### 各馬のマスタ情報にアクセスする

`horse_master_dict` は血統登録番号をキーとした辞書です。`fetch_horse_master()` で取得した後に参照できます。

```python
rd.fetch_horse_master()

for horse_id, master_df in rd.horse_master_dict.items():
    print(f"血統登録番号 {horse_id}: {master_df['馬名'].iloc[0]}")
```

### 未来レースのオッズを更新する

レース直前に最新オッズへ更新する場合は `fetch_odds()` を再度呼び出します。

```python
rd.fetch_odds()
print(rd.win_show_odds_df)
```

### 複数レースで DataInterface を共有する

`DataInterface` はコンストラクタ引数として受け取るため、複数の `RaceData` インスタンスで共有できます。

```python
di = DataInterface("mykeibadb")

race_data_list = [
    RaceData(race_code=code, data_interface=di)
    for code in ["2023112605050811", "2023112605050812"]
]
```


## 属性一覧

| 属性名 | 型 | 説明 |
|---|---|---|
| `race_code` | `str` | 16桁レースコード（年(4)+月日(4)+競馬場(2)+回(2)+日目(2)+R(2)） |
| `baba_code` | `str` | 馬場状態コード。`"1"`(良), `"2"`(稍), `"3"`(重), `"4"`(不)。省略時は自動設定 |
| `future_race` | `bool` | 未来のレースかどうか（レース日 ≥ 実行日なら `True`） |
| `race_basic_info_df` | `pd.DataFrame` | レース基本情報（1行） |
| `entry_df` | `pd.DataFrame` | 出馬表（常に取得） |
| `result_df` | `pd.DataFrame` | レース結果。`fetch_race_result()` または `fetch_result()` 後に参照可能（未取得時は `RuntimeError`）。未来レースでは `fetch_all()` 後に空 |
| `race_result_info_df` | `pd.DataFrame` | ラップタイム・コーナー通過順。`fetch_race_result_info()` または `fetch_result()` 後に参照可能（未取得時は `RuntimeError`）。未来レースでは `fetch_all()` 後に空 |
| `payoff_df` | `pd.DataFrame` | 払戻情報。`fetch_payoff()` または `fetch_result()` 後に参照可能（未取得時は `RuntimeError`）。未来レースでは `fetch_all()` 後に空 |
| `win_show_odds_df` | `pd.DataFrame` | 単複オッズ情報。`fetch_odds()` 後に参照可能（未取得時は `RuntimeError`） |
| `win_show_votes_df` | `pd.DataFrame` | 単複票数情報（`WIN_SHOW_VOTES_COLUMNS`、馬番順）。`fetch_votes()` 後に参照可能（未取得時は `RuntimeError`） |
| `past_performances_dict` | `dict[int, pd.DataFrame]` | 各馬の過去成績辞書（キー: 馬番。対象レース以前のデータのみ）。`fetch_past_performances()` 後に参照可能（未取得時は `RuntimeError`） |
| `past_race_basic_info_df` | `pd.DataFrame` | 全出走馬の過去走のレース基本情報（`RACE_BASIC_INFO_COLUMNS`、レースコード昇順）。`fetch_past_race_basic_info()` 後に参照可能（未取得時は `RuntimeError`） |
| `horse_master_dict` | `dict[str, pd.DataFrame]` | 各馬のマスタ情報辞書（キー: 血統登録番号）。`fetch_horse_master()` 後に参照可能（未取得時は `RuntimeError`） |
| `num_runners` | `int` | 出走頭数（競走除外などは除く）。`race_basic_info_df` の出走頭数が欠損している場合、初期化時は `0` となり `fetch_odds()` 後に単勝人気の件数から補完される |
| `valid_horse_num` | `list[int]` | 出走予定の馬番リスト（異常区分コードが1,2,3の馬を除外）。昇順 |


## メソッド一覧

| メソッド | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `fetch_race_result()` | なし | `None` | `result_df` を取得 |
| `fetch_race_result_info()` | なし | `None` | `race_result_info_df` を取得 |
| `fetch_payoff()` | なし | `None` | `payoff_df` を取得 |
| `fetch_result()` | なし | `None` | `result_df` / `race_result_info_df` / `payoff_df` をまとめて取得 |
| `fetch_odds()` | なし | `None` | `win_show_odds_df` を取得（再取得も可）。出走頭数欠損時は `num_runners` を補完 |
| `fetch_votes()` | なし | `None` | `win_show_votes_df` を取得。票数に対応していないプロバイダー（scraping）は `UnsupportedOperationError` |
| `fetch_past_performances()` | なし | `None` | `past_performances_dict` を取得 |
| `fetch_past_race_basic_info()` | なし | `None` | `past_race_basic_info_df` を取得（`fetch_past_performances()` の後に呼ぶ。scraping プロバイダーは `UnsupportedOperationError`） |
| `fetch_horse_master()` | なし | `None` | `horse_master_dict` を取得 |
| `fetch_all()` | なし | `None` | 上記すべてを取得。未来レースでは結果系は空 `DataFrame` になる。プロバイダーが対応していない操作（`UnsupportedOperationError`）は取得を省く |
| `is_make_debut()` | なし | `bool` | 新馬戦かどうか |
| `is_steeple_chase()` | なし | `bool` | 障害レースかどうか |
| `is_straight_race()` | なし | `bool` | 直線コースかどうか |
| `is_turf()` | なし | `bool` | 芝レースかどうか |
| `is_dirt()` | なし | `bool` | ダートレースかどうか |
| `is_good_to_firm()` | なし | `bool` | 良馬場かどうか。`baba_code` が `"0"`〜`"4"` のいずれでもない場合（空文字を含む）は `KeibaDomainError` を送出 |
| `get_filtered_past_performances(uma_ban)` | 馬番（int） | `pd.DataFrame` | 機械学習に有効な過去成績を抽出 |

### `get_filtered_past_performances` のフィルタリング条件

- 中央競馬のみ（競馬場コードが `"01"` 〜 `"10"`）
- 競走除外を除く（出走取消・発走除外・競走除外は除外）


## サンプルコード

[example/example_race_data.py](example/example_race_data.py) に実行可能なサンプルスクリプトがあります。

```bash
# mykeibadb プロバイダーで実行（デフォルト）
python example/example_race_data.py --race-code 2023112605050812

# scraping プロバイダーで実行
python example/example_race_data.py --race-code 2023112605050812 --provider scraping
```

サンプルスクリプトはレース基本情報・出馬表・レース結果・過去成績（フィルタリング済み）を順に表示します。
