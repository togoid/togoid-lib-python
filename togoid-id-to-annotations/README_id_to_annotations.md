# id_to_annotations.py の使い方

## 概要

`id_to_annotations.py` は TogoID の ID→ラベル・アノテーション変換機能をコマンドラインから利用できるようにした Python スクリプトです。TogoID 設定 API からデータセットのアノテーション定義を取得し、GRASP GraphQL エンドポイントを用いて ID に対応するラベルやメタデータを取得します。

## 事前準備

1. Python 3.9 以上を用意します。
2. 依存関係をインストールします。

   ```bash
   pip install -r requirements.txt
   ```

3. ネットワークから以下のエンドポイントへアクセスできる必要があります。
   - TogoID API: `https://api.togoid.dbcls.jp`
   - GRASP GraphQL: `https://dx.dbcls.jp/grasp-dev-togoid`

   環境に応じてエンドポイントを変更したい場合は、環境変数 `TOGOID_API_ENDPOINT` と `TOGOID_GRASP_ENDPOINT` を設定するか、後述のオプションで上書きします。

## 基本操作

### 利用可能なアノテーション項目の確認

```bash
python id_to_annotations.py --dataset ncbigene --list-fields
```

指定したデータセットで取得できるフィールド名やリスト型の値を表示します。

### ラベルやメタデータの取得

```bash
python id_to_annotations.py --dataset ncbigene --ids 672 7157 \
  --field gene_synonym --field full_name --include-label
```

複数の ID をまとめて問い合わせ、指定したフィールド（同義語や正式名称など）を取得します。`--include-label` を付けると GraphQL が提供する標準の `label` フィールドも結果に含めます。

### フィルタリング

```bash
python id_to_annotations.py --dataset ncbigene --ids 672 7157 \
  --field type_of_gene --filter type_of_gene=protein-coding
```

`--filter` オプションで特定の値に一致する行のみを抽出できます。複数値を指定すると `,` 区切りで OR 条件になります。

### 出力形式の選択

- 表形式（タブ区切り・既定値）

  ```bash
  python id_to_annotations.py --dataset ncbigene --ids 672 --field gene_synonym
  ```

- CSV 形式

  ```bash
  python id_to_annotations.py --dataset ncbigene --ids 672 \
    --field gene_synonym --format csv --output result.csv
  ```

- JSON 形式

  ```bash
  python id_to_annotations.py --dataset ncbigene --ids 672 \
    --field gene_synonym --format json
  ```

リスト型フィールドを 1 行にまとめたい場合は `--compact` を付けます。デフォルトでは直積展開され、複数の値がある項目は複数行に分解されます。

### ID の一括入力

`--ids` で直接指定するほか、`--ids-file` で 1 行 1 ID のテキストファイルを読み込めます。

```bash
python id_to_annotations.py --dataset ncbigene --ids-file ids.txt --field full_name
```

## 主なオプション一覧

| オプション | 説明 |
| ---------- | ---- |
| `--dataset` | 参照するデータセットキー（必須） |
| `--ids` / `--ids-file` | 変換対象 ID を指定。両方指定した場合は併合されます |
| `--field` | 取得したいアノテーションフィールドを複数指定可能 |
| `--include-label` | GraphQL の `label` フィールドを結果に含める |
| `--filter` | `フィールド=値1,値2` 形式でフィルタ条件を指定 |
| `--compact` | リスト型の値を 1 セルにまとめる |
| `--format` | `table`(既定) / `csv` / `json` を選択 |
| `--delimiter` | `table` または `csv` の区切り文字を変更 |
| `--output` | 出力ファイルパスを指定。未指定の場合は標準出力に表示 |
| `--api-endpoint`, `--graphql-endpoint` | それぞれのエンドポイント URL を明示的に指定 |
| `--timeout` | HTTP タイムアウト秒数を指定 |
| `--verbose` | 進行ログを標準エラーに出力 |

## トラブルシューティング

- DNS やファイアウォールの設定によりエンドポイントへ接続できない場合があります。`--verbose` を付けてリクエスト先を確認し、プロキシ設定が必要な場合は Python の `requests` で利用できる環境変数（`HTTP_PROXY` など）を設定してください。
- 指定したフィールド名が存在しない場合はエラーになります。まず `--list-fields` で利用可能な項目を確認してください。

## ライセンス

プロジェクト全体のライセンスに従います。詳細はリポジトリのルートにあるライセンス情報を参照してください。
