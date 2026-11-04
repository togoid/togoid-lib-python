# TODO: togoid-api PR #149 (`?prefix`) 対応 —【改訂版：prefix付き出力を受け入れる】

## 確定方針

- **convert結果にprefix（CURIE）が付くのを歓迎**。APIデフォルト（paramなし＝整形あり）をそのまま流す。
- label2id（label_converter）は **スコープ外・生IDのまま**（PubDictionaries/SPARQList経由で`?prefix`対象外）。
- get_ortholog は **内部照合は生ID／最終出力はprefix付き**。
- 重要な制約：PR#149は**まだ本番未デプロイ**（devホストのみ、PRはOpen）。よって本改修は
  **デプロイ前（生ID返却）でも後（prefix返却）でも正しく動く**こと（＝下記ヘルパーが生IDでは no-op）を必須要件とする。

## 設計の核心：`_local_id()` ヘルパー1つに集約

prefix付きだと壊れるのは「**IDを文字列一致キーとして使い回す**」箇所のみ。そこだけ
CURIE `PREFIX:localid` から**local ID（生ID）を取り出して照合**する。表示するIDは素通し（prefix付きのまま）。

```
def _local_id(id):
    # CURIE の prefix を剥がして DB 生ID を返す。prefix無しIDやNoneはそのまま。
    # 例: "GO:0005634" -> "0005634" / "ENSG000..." -> そのまま / None -> None
    # APIの整形は "PREFIX:%s" 形式なので最初の ':' で分割。URI("//"含む)は対象外。
```
→ 生ID入力（デプロイ前）では `:` を含まず **完全な no-op**。デプロイ後のみ剥がす。前方・後方両対応。

## 実装タスク

- [ ] 1. `converter.py` に `_local_id()` を追加（None安全・`//`ガード・最初の`:`で分割）
- [ ] 2. `_add_annotations`（最重要）
  - GRASPへ渡すID集合を `_local_id(str(row[idx]))` で生IDに正規化（converter.py:147付近）
  - filter突合・annotate列挿入のルックアップキーも `_local_id(...)` に（converter.py:186, 213付近）
  - GRASPは生IDキーで返す（現行動作から実証済み）ため、両側が生IDで一致する
- [ ] 3. `get_ortholog`
  - `intermediate_to_sources` / `intermediate_to_targets` / `target_to_taxonomy` の**キーを `_local_id(...)` に統一**（converter.py:822-830, 857-862, 879-889）
  - taxonomy判定を `_local_id(taxonomy_id) in {_local_id(t) for t in target_taxids}` に（888）
  - **表示値（source/intermediate/target/taxonomy）は素通し（prefix付きのまま）**＝最終出力prefix付き
  - 内部convert呼び出しはデフォルトのまま（prefix付き）でよい。照合はlocal_idで吸収
- [ ] 4. （堅牢性）`AnnotationsConverter.execute_query` の入口でも入力IDを `_local_id` 正規化
  - ユーザーがconvert出力のprefix付きIDをそのまま貼っても動くように
- [ ] 5. （任意・opt-out）`convert()` に `prefix: bool = True` を追加
  - True（既定）→ param送らず＝API整形あり／False → `prefix=no` 送信で生ID
  - 「生IDが欲しい」利用者への逃げ道。必須ではないが低コスト
- [ ] 6. テスト `test_round6.py`
  - `_local_id` の単体（prefix有/無/None/URI）
  - `_add_annotations`：prefix付き行＋生IDキーGRASP応答（mock）でジョインが成立すること
  - `get_ortholog`：prefix付き中間ID（mock convert）で照合・taxonomy判定が通ること
  - デプロイ前相当（生ID）でも全て通ること（no-op回帰）
- [ ] 7. dev ホスト（`https://api.togoid.dbcls.jp.il3c.com`）で実地確認
  - convert が prefix付きを返すこと、annotate/filter が壊れないこと
- [ ] 8. ドキュメント
  - README：convert出力例をprefix付きへ更新（25箇所）、prefix挙動を明記、label2idは生IDと注記
  - `test_readme_examples.py`(8) / `test_round5.py`(2) の期待値更新
  - CHANGELOG_SUMMARY.md 第6弾、`tasks/lessons.md` に教訓追記

## 変更不要（確認済み）

- `_convert_to_dict/table/dataframe`、CLI表示、count/search/lookup：文字列素通しでprefixの恩恵のみ
- 入力側：APIのregexがprefix入力を吸収するため変更不要

## 検証（Verification Before Done）

- 新旧テスト全通過（生ID/prefix付き両方でジョインが成立）
- dev ホストで実サーバー確認
- 「シニアが承認するか？」：`_local_id`が生IDでno-op＝デプロイ非依存で安全、表示は素直にprefix付き

## Review（実装後）

**実装完了・検証済み。**

- `togoid/_ids.py` 新設：`local_id()`（CURIEから生ID抽出。生ID/None/URIはno-op）
- `converter.py`：`_local_id` を共有ヘルパーに委譲／`_add_annotations` のGRASP問い合わせ・ジョインを生ID正規化／`get_ortholog` の3照合マップ+taxonomy判定を生IDキー化（表示はprefix付き保持）／`convert(prefix=True)` 追加（False→`prefix=no`）
- `annotations.py`：`execute_query` がprefix付き入力を受理（生IDで問い合わせ、元IDでキーして返す）
- `cli.py`：`convert --raw` フラグ追加
- `test_round6.py` 新設：5ケース全PASS（`_local_id`／annotationジョイン／ortholog／execute_query／prefix opt-out。mockで生ID・prefix両方を網羅）

**検証結果（証拠）**
- `test_round6.py`：5/5 PASS
- `test_round5.py`（既存・本番ライブAPI）：6/6 PASS（回帰なし）
- devホスト（PR#149）実地：default→`ORPHA:217124/GO:0005737`、`prefix=False`→生ID。annotate も prefix付き出力でラベル付与成立（ジョイン成立）
- 本番ホスト（生ID）実地：annotate ラベル付与成立（後方互換OK）
- → `local_id` の no-op 設計により**デプロイ時期に非依存で正しい**ことを実サーバーで確認

**スコープ判断メモ**
- README の既存25例は本番が今も生IDを返すため据え置き、別途「ID Prefixes (CURIE format)」節で挙動とopt-outを明記（現行ユーザーに正確）。
- label2id は生IDのまま（別サービス経由・スコープ外）。
