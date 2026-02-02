# 顧客フィードバック修正計画

## 問題点の整理

### 1. converter.convertの挙動（route長が3以上のとき）
**現状の問題:**
- route長が3以上でも、sourceとtargetのIDしか出力されない（2列のみ）
- 例: `route=["ncbigene", "ensembl_gene", "ensembl_transcript"]` でも `ensembl_gene` が出力されない

**期待される動作:**
- 中間のデータセットIDも含めて全ての列を出力
- `report=full` を使用して全経路を取得

**影響範囲:**
- `format="table"`
- `format="dataframe"`

### 2. annotate指定時のDataFrameヘッダーのずれ
**現状の問題:**
```
   ncbigene ensembl_gene ensembl_transcript   ncbigene label
0         1         A1BG    ENSG00000121410  ENST00000263100
```
- アノテーション列が中間IDの位置に入り、ヘッダーがずれている
- 実際のデータ: `[source_id, annotation, intermediate_id, target_id]`
- ヘッダー: `[source, intermediate, target, annotation]`

**期待される動作:**
- ヘッダーとデータの列順序を一致させる
- アノテーション列を正しい位置に表示

### 3. format="dict"の廃止（route>=3のとき）
**理由:**
- route長が3以上のときの入れ子辞書は使いづらい
- tableとdataframeで十分

**対応:**
- route長が3以上で `format="dict"` が指定された場合はエラーを返す

### 4. label_converter.convertのlabel_types
**現状:**
- 型: `Optional[str]`（カンマ区切り文字列）
- 値: dataset.yamlの`dictionary`の値

**期待:**
- 型: `Optional[List[str]]`（リスト）
- 値: dataset.yamlの`label_type`の値

### 5. annotator.execute_queryのfilters
**現状:**
- `filters`がrequiredパラメータ

**期待:**
- `filters`をoptionalに変更（`default={}`）

## 実装計画

### ステップ1: converter.py の修正

#### 1-1. convertメソッドのreport設定を修正
**ファイル:** `togoid/converter.py`
**場所:** `convert` メソッド内のreport設定部分

**変更前:**
```python
if 'report' not in params:
    if annotate or filter:
        params['report'] = 'full'
    elif format in ('dict', 'table', 'dataframe'):
        params['report'] = 'pair'
```

**変更後:**
```python
if 'report' not in params:
    if annotate or filter or len(route) >= 3:
        params['report'] = 'full'
    elif format in ('dict', 'table', 'dataframe'):
        params['report'] = 'pair'
```

#### 1-2. dictフォーマットの廃止（route>=3）
**ファイル:** `togoid/converter.py`
**場所:** `convert` メソッド内のフォーマット処理部分

**追加コード:**
```python
# Transform based on format
if format == 'dict':
    if len(route) >= 3:
        raise ValueError(
            "format='dict' is not supported when route length >= 3. "
            "Use 'table' or 'dataframe' instead."
        )
    return self._convert_to_dict(response, route)
```

#### 1-3. _convert_to_dataframeでのヘッダー修正
**ファイル:** `togoid/converter.py`
**場所:** `_convert_to_dataframe` メソッド

**修正内容:**
- annotateがある場合、アノテーション列の挿入位置を考慮してヘッダーを生成
- データの列順序と一致するようにヘッダーを構築

**ロジック:**
1. routeから基本的な列名を取得
2. annotateがある場合、各アノテーションがどのデータセットの後に挿入されるかを計算
3. 挿入位置を考慮して正しい順序で列名を生成

### ステップ2: label_converter.py の修正

#### 2-1. label_types引数の型変更
**ファイル:** `togoid/label_converter.py`
**場所:**
- `convert` メソッドのシグネチャ
- `convert_pubdictionaries` メソッドのシグネチャ
- `convert_sparqlist` メソッドのシグネチャ

**変更:**
- `label_types: Optional[str]` → `label_types: Optional[List[str]]`
- API呼び出し時に `,`.join() で文字列化

#### 2-2. dataset configから取得する値の変更
**ファイル:** `togoid/label_converter.py`
**場所:** `convert` メソッド内のconfig取得部分

**変更前:**
```python
# Extract dictionary names from dataset config
dictionary_configs = label_resolver.get("dictionaries", [])
if dictionary_configs:
    label_types = ",".join([d["dictionary"] for d in dictionary_configs])
```

**変更後:**
```python
# Extract label_type values from dataset config
label_type_configs = label_resolver.get("label_types", [])
if label_type_configs:
    label_types = [lt["label_type"] for lt in label_type_configs]
```

### ステップ3: annotations.py の修正

#### 3-1. execute_queryメソッドのfiltersをoptionalに
**ファイル:** `togoid/annotations.py`
**場所:** `execute_query` メソッドのシグネチャ

**変更前:**
```python
def execute_query(
    self,
    dataset_name: str,
    ids: List[str],
    fields: List[str],
    filters: Dict
):
```

**変更後:**
```python
def execute_query(
    self,
    dataset_name: str,
    ids: List[str],
    fields: List[str],
    filters: Optional[Dict] = None
):
    if filters is None:
        filters = {}
```

## テスト計画

### テスト1: route長が3以上のときの出力
```python
result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
    format="table"
)
# 期待: 各行が3列（source, intermediate, target）
assert len(result[0]) == 3
```

### テスト2: annotate指定時のDataFrameヘッダー
```python
result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
    format="dataframe",
    annotate=[("ncbigene", "label")]
)
# 期待: ヘッダーとデータが一致
# ヘッダー: ['ncbigene', 'ncbigene label', 'ensembl_gene', 'ensembl_transcript']
```

### テスト3: route>=3でのdictフォーマットエラー
```python
try:
    result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
        format="dict"
    )
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "not supported when route length >= 3" in str(e)
```

### テスト4: label_types引数がリスト型
```python
label_converter = LabelConverter()
result = label_converter.convert(
    labels=["BRCA1", "TP53"],
    dataset="ncbigene",
    label_types=["symbol", "synonym"],
    taxonomy="9606"
)
```

### テスト5: filtersなしでannotator.execute_query
```python
annotator = AnnotationsConverter()
result = annotator.execute_query(
    dataset_name="ncbigene",
    ids=["672", "7157"],
    fields=["label", "gene_synonym"]
    # filtersなし
)
```

## 影響範囲

### 破壊的変更
1. **format="dict"の廃止（route>=3）**
   - route長が3以上で dict を使用しているコードはエラーになる
   - 代替: table または dataframe を使用

2. **label_types引数の型変更**
   - 文字列からリストへの変更
   - 既存コード: `label_types="symbol,synonym"`
   - 新しいコード: `label_types=["symbol", "synonym"]`

### 非破壊的変更（改善）
1. **route>=3での完全な出力**
   - 既存の動作が改善される

2. **annotate時のヘッダー修正**
   - 既存の動作が修正される

3. **filtersのoptional化**
   - 既存コードはそのまま動作
   - 新しいコードではfiltersを省略可能

## 実装順序

1. ✅ 修正計画をMarkdownファイルに保存
2. converter.py の修正
   - report設定の修正
   - dictフォーマットの廃止
   - DataFrameヘッダーの修正
3. label_converter.py の修正
   - label_types型変更
   - label_type値の使用
4. annotations.py の修正
   - filtersをoptionalに
5. テストファイルの作成・実行
6. PR作成
