# race-data

## 概要

`race-data` は、競馬レースの情報を一括で保持するデータクラス `RaceData` を提供する Python ライブラリです。

`keiba-data-interface` の `DataInterface` を通じてレース基本情報・出馬表・レース結果・払戻情報・各馬の過去成績を取得し、1つのインスタンスにまとめて保持します。

- **未来のレース**（予測対象）と**過去のレース**（学習データ取得）の両方に対応
- レースコードの日付から未来/過去を自動判定（同日は未来扱い）
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

`DataInterface` インスタンスと 16 桁レースコードを渡して `RaceData` をインスタンス化します。初期化と同時にすべてのデータが取得されます。

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

### 馬場状態を上書きする

過去レースの分析などで実際とは異なる馬場状態を仮定したい場合、`baba_code` を指定します。

```python
rd = RaceData(race_code=race_code, data_interface=di, baba_code="3")  # 重馬場と仮定
print(rd.is_good_to_firm())  # False
```

### 各馬の過去成績にアクセスする

`past_performances_dict` は馬番をキーとした辞書です。`get_filtered_past_performances` で機械学習に有効なデータ（中央競馬のみ、競走除外除く）に絞り込めます。

```python
# 馬番 1 の有効な過去成績を取得
filtered_df = rd.get_filtered_past_performances(1)
print(filtered_df)

# すべての馬の過去成績を処理する例
for uma_ban, pp_df in rd.past_performances_dict.items():
    filtered = rd.get_filtered_past_performances(uma_ban)
    print(f"馬番 {uma_ban}: {len(filtered)} レース")
```

### 各馬のマスタ情報にアクセスする

`horse_master_dict` は血統登録番号をキーとした辞書です。

```python
for horse_id, master_df in rd.horse_master_dict.items():
    print(f"血統登録番号 {horse_id}: {master_df['馬名'].iloc[0]}")
```

### 未来レースのオッズを更新する

レース直前に最新オッズへ更新する場合は `update_win_show_odds` を呼び出します。

```python
rd.update_win_show_odds()
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
| `result_df` | `pd.DataFrame` | レース結果（過去レースのみ。未来レースでは空） |
| `race_result_info_df` | `pd.DataFrame` | ラップタイム・コーナー通過順（過去レースのみ。未来レースでは空） |
| `payoff_df` | `pd.DataFrame` | 払戻情報（過去レースのみ。未来レースでは空） |
| `win_show_odds_df` | `pd.DataFrame` | 単複オッズ情報 |
| `past_performances_dict` | `dict[int, pd.DataFrame]` | 各馬の過去成績辞書（キー: 馬番。対象レース以前のデータのみ） |
| `horse_master_dict` | `dict[str, pd.DataFrame]` | 各馬のマスタ情報辞書（キー: 血統登録番号） |
| `num_runners` | `int` | 出走頭数（競走除外などは除く） |
| `valid_horse_num` | `list[int]` | 出走予定の馬番リスト（異常区分コードが1,2,3の馬を除外）。昇順 |


## メソッド一覧

| メソッド | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `update_win_show_odds()` | なし | `None` | `win_show_odds_df` を最新オッズで上書き |
| `is_make_debut()` | なし | `bool` | 新馬戦かどうか |
| `is_steeple_chase()` | なし | `bool` | 障害レースかどうか |
| `is_straight_race()` | なし | `bool` | 直線コースかどうか |
| `is_turf()` | なし | `bool` | 芝レースかどうか |
| `is_dirt()` | なし | `bool` | ダートレースかどうか |
| `is_good_to_firm()` | なし | `bool` | 良馬場かどうか（`baba_code == "1"`） |
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
