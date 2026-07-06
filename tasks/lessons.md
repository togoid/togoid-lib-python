# Lessons (togoid-lib-python)

## 第5弾フィードバック (2026-05-25) からの教訓

### L1. 欠損値の sentinel は **出力フォーマットに合わせて使い分け** る

**発生**: `converter.convert(format="dataframe")` で欠損セルが文字列 `"None"`、`format="table"` でも `'None'`、`label_converter.convert` では空文字列 `""` と、関数とフォーマットによってバラバラだった。原因は `_convert_to_table` の `str(elem)` で `None` を強制的に文字列化していたこと。

**ルール**:
- **dataframe** → `pd.NA` (object dtype を維持して `df.where(df.notna(), pd.NA)` で正規化)
- **table / list of list** → Python の `None`
- DataFrame に渡す前のリスト段階では `None` を保持し、`str()` で固めない (固めると元情報が失われ DataFrame で `pd.NA` に戻せなくなる)

**注意点**:
- `pd.NA` は `==` / `!=` で結果が NA になり、`bool()` で `TypeError: boolean value of NA is ambiguous` を投げる。テストで `pd.NA` を判定するときは `x is pd.NA` か `pd.isna(x)` を使う。両者を `and` で繋ぐ簡易判定は壊れる。

---

### L2. 大規模リスト ID/labels は GET の URL に乗せず、form-encoded POST にする

**発生**: 6478 件の `ncbigene` ID を `converter.convert` に渡したら HTTP 494 で失敗。GET クエリ文字列に全 ID を並べていたのが原因。

**ルール**: ID やラベルのような **「件数が呼び出し側次第」のパラメータ** は原則 form-encoded POST で送る (`requests.post(url, data=params)`)。短い場合の効率より長い場合の robustness を優先。

**注意点**:
- SPARQList は JSON POST 非対応 (500 エラー) なので、`json=` ではなく `data=` を使う。form-encoded POST で統一しておくと TogoID API / PubDictionaries / SPARQList すべて動く。
- `_make_request` は `form_data` / `json_data` を引数で分岐させ、POST のときに `params` を URL クエリに付けないようにする (混ぜると body と URL の両方に乗ってしまう)。

---

## 第6弾フィードバック (2026-07-06): API `?prefix` (CURIE整形) 対応からの教訓

### L3. API のデフォルト出力変更は「IDを一致キーに再利用している箇所」を静かに壊す

**発生**: togoid-api PR #149 で `/convert` がデフォルトでプレフィックス付きID (`GO:0005634`) を返すようになった。ライブラリは convert 出力IDを**文字列一致キー**として再利用している箇所があり、そこが壊れる:
- `_add_annotations`: convert結果IDを GRASP GraphQL の**生IDキー**と突合 → prefix付きだと全ミス → annotate列が空・filterが全行除外 (サイレント破壊)
- `get_ortholog`: 中間ID/target/taxonomy を3回の convert 間で文字列照合。特に `taxonomy_id in target_taxids` は prefix付き `taxon:10090` と生 `10090` が不一致
- `AnnotationsConverter.execute_query`: ユーザーが convert 出力の prefix付きIDを貼るとGRASPが引けない

**ルール**: **表示用ID (prefix付き)** と **照合用キー (生ID/local ID)** を分離する。IDを辞書キーや `in` 比較に使うときは必ず生IDに正規化してから照合し、表示・出力には元のprefix付きを使う。共通ヘルパー `togoid/_ids.py::local_id()` に一本化 (CURIE `PREFIX:%s` を最初の `:` で分割。prefix無し/None/URIはそのまま)。

**注意点**:
- `local_id()` は**生IDに対して no-op** になるよう設計する。こうすると API デプロイ前 (生ID返却) でも後 (prefix付き) でも同じコードが正しく動き、デプロイ時期に依存しない。これが「場当たり的でない」正解。
- 検証は mock だけでなく **dev ホスト (`api.togoid.dbcls.jp.il3c.com`) と本番の両方**で実地確認する。今回 annotate のジョインが prefix付き出力でも生成されることを実サーバーで確認した。

### L4. 「効率化できるはず」という前提は鵜呑みにせず、コードで裏取りする

**発生**: ユーザーは「API変更でライブラリの処理が効率化/不要になる」と見込んでいたが、実際にはライブラリに手作業prefix付与処理は**存在しなかった** (PR #149が触るのは API 側の同名 `togoid/` パッケージ)。効率化ではなく「デフォルト挙動変更への追従」が本質だった。

**ルール**: ユーザーの見立て (「〜が不要になるはず」等) は、grep/コード精読で**該当処理の実在を確認してから**同意・着手する。無い場合は率直に指摘し、本当の論点 (今回は互換性リスク) を提示する。

**注意点**: togoid-api と togoid-lib-python は**どちらも `togoid/` パッケージ名**を持つ。PR差分の `togoid/config.py` 等は API 側であってこのクライアントではない、という混同に注意。
