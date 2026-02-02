# 可能なパス提示機能の実装計画

## 要望の概要

convert を2データセット間で行い、その2データセット間がつながっていないときは、エラーメッセージに route の API で取得した可能なパスを候補として出してあげるようにする。

## 現状の問題点

### 1. エラーメッセージが不親切
現在、2つのデータセット間が直接つながっていない場合、以下のようなエラーが発生します:

```python
converter.convert(ids=['1'], route=['ncbigene', 'chebi'], format='table')
# RuntimeError: API Error: 400 Client Error: Bad Request for url: ...
```

このエラーメッセージからは:
- なぜ変換が失敗したのか分からない
- どうすれば解決できるのか分からない
- 代替手段があるのか分からない

### 2. route APIの404エラー
route APIを使用してパスを検索しようとすると、404エラーが発生することがあります:

```python
routes = converter.route(src='ncbigene', dst='ensembl_gene', max_hops=2)
# RuntimeError: API Error: 404 Client Error: Not Found
```

これは、route APIが以下の場合に404を返すことを示しています:
- パスが存在しない
- または、APIエンドポイントが異なる

## 実装方針

### アプローチ1: config_list_targets を活用した段階的提案

route APIが404を返す場合を考慮し、`config_list_targets`を使用して段階的にパスを提案します。

#### 処理フロー:

1. **convert実行でエラー発生を検知**
   - 400 Bad Request または類似のエラーをキャッチ

2. **route APIで可能なパスを検索**
   - `self.route(src, dst, max_hops=3)` を実行
   - 成功した場合: 取得したルートを提案
   - 404エラーの場合: 次のステップへ

3. **config_list_targetsで1ホップの接続を確認**
   - `self.config_list_targets(src)` を実行
   - dstが含まれているか確認
   - 含まれている場合: 直接接続を提案 `[src, dst]`
   - 含まれていない場合: 次のステップへ

4. **2ホップの可能性を探索**
   - `self.config_list_targets(src)` で中間候補を取得
   - 各中間候補について `self.config_list_targets(intermediate)` を実行
   - dstに到達できる中間データセットを見つける
   - 見つかった場合: パス `[src, intermediate, dst]` を提案

5. **エラーメッセージ生成**
   - パスが見つかった場合: 具体的なルートを提示
   - パスが見つからない場合: 接続されていないことを通知

### アプローチ2: エラーハンドリングの強化

convertメソッド内でエラーをキャッチし、より詳細なエラーメッセージを提供します。

## 実装詳細

### 1. _make_request メソッドの修正

エラー情報を保持しつつ、特定のエラー（400, 404）を判別できるようにします。

```python
def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None,
                  json_data: Optional[Dict] = None) -> Any:
    """Make HTTP request to API"""
    url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

    try:
        if method == 'GET':
            resp = requests.get(url, params=params, timeout=30)
        elif method == 'POST':
            resp = requests.post(url, json=json_data, params=params, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")

        resp.raise_for_status()

        # Try to parse as JSON, otherwise return text
        content_type = resp.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return resp.json()
        else:
            return resp.text

    except requests.exceptions.HTTPError as e:
        # Include status code in error for better handling
        error_msg = f"API Error ({e.response.status_code}): {e}"
        raise RuntimeError(error_msg) from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API Error: {e}") from e
```

### 2. convert メソッドの修正

エラーをキャッチして、可能なルートを提案するロジックを追加します。

```python
def convert(
    self,
    route: List[str],
    ids: List[str],
    format: str = 'json',
    annotate: Optional[List[Tuple[str, str]]] = None,
    filter: Optional[List[Tuple[str, str, List[str]]]] = None,
    **kwargs
) -> Any:
    """Convert IDs between databases"""
    # ... existing parameter setup ...

    try:
        # Get API response
        response = self._make_request('/convert', 'GET', params=params)

        # ... existing processing ...

    except RuntimeError as e:
        # Check if it's a connection error (400 Bad Request)
        if '400' in str(e) or 'Bad Request' in str(e):
            # Try to find alternative routes
            if len(route) == 2:
                src, dst = route
                suggested_routes = self._find_alternative_routes(src, dst)

                if suggested_routes:
                    route_strs = [' -> '.join(r) for r in suggested_routes]
                    raise RuntimeError(
                        f"No direct connection between '{src}' and '{dst}'. "
                        f"Try one of these routes instead:\n" +
                        '\n'.join(f"  - {rs}" for rs in route_strs)
                    ) from e
                else:
                    raise RuntimeError(
                        f"No connection found between '{src}' and '{dst}'. "
                        f"These datasets may not be connected in the TogoID database."
                    ) from e
        # Re-raise other errors
        raise
```

### 3. _find_alternative_routes メソッドの追加

可能なルートを探索する新しいメソッドを追加します。

```python
def _find_alternative_routes(
    self,
    src: str,
    dst: str,
    max_hops: int = 3
) -> List[List[str]]:
    """
    Find alternative routes between two datasets

    Args:
        src: Source dataset name
        dst: Destination dataset name
        max_hops: Maximum number of hops to search

    Returns:
        List of routes (each route is a list of dataset names)
    """
    routes = []

    # Try route API first
    try:
        api_routes = self.route(src, dst, max_hops=max_hops)
        if api_routes:
            return api_routes
    except RuntimeError:
        # Route API failed (404 or other error), fall back to manual search
        pass

    # Manual search using config_list_targets

    # Check direct connection (1 hop)
    targets_from_src = self.config_list_targets(src)
    if dst in targets_from_src:
        routes.append([src, dst])
        return routes

    # Check 2-hop connections
    if max_hops >= 2:
        for intermediate in targets_from_src:
            targets_from_intermediate = self.config_list_targets(intermediate)
            if dst in targets_from_intermediate:
                routes.append([src, intermediate, dst])

        if routes:
            return routes

    # Check 3-hop connections
    if max_hops >= 3:
        for intermediate1 in targets_from_src:
            targets_from_intermediate1 = self.config_list_targets(intermediate1)
            for intermediate2 in targets_from_intermediate1:
                if intermediate2 == src:  # Avoid loops
                    continue
                targets_from_intermediate2 = self.config_list_targets(intermediate2)
                if dst in targets_from_intermediate2:
                    routes.append([src, intermediate1, intermediate2, dst])

        if routes:
            return routes

    return routes
```

## テスト計画

### テストケース1: 直接接続が存在しない場合（1ホップで到達可能）

```python
# ncbigene と ensembl_gene は直接接続されている（仮定）
try:
    converter.convert(ids=['1'], route=['ncbigene', 'ensembl_gene'], format='table')
    # 成功する場合、テスト失敗
except RuntimeError as e:
    # エラーメッセージに候補ルートが含まれることを確認
    assert 'Try one of these routes' in str(e)
    assert 'ncbigene -> ensembl_gene' in str(e)
```

### テストケース2: 2ホップで到達可能な場合

```python
# ncbigene -> ensembl_protein -> uniprot などのパス
try:
    converter.convert(ids=['1'], route=['ncbigene', 'some_disconnected_dataset'], format='table')
except RuntimeError as e:
    # 2ホップのルートが提案されることを確認
    assert 'ncbigene -> ' in str(e)
```

### テストケース3: 接続が存在しない場合

```python
# 完全に接続されていないデータセット
try:
    converter.convert(ids=['1'], route=['ncbigene', 'nonexistent_dataset'], format='table')
except RuntimeError as e:
    # 接続されていないことが通知されることを確認
    assert 'No connection found' in str(e)
```

## 考慮事項

### パフォーマンス
- `config_list_targets`の呼び出し回数が多くなる可能性
- キャッシュ機構の導入を検討（特に2-3ホップ探索時）

### エラーメッセージの見やすさ
- ルート提案は最大5件程度に制限
- 最短パスを優先的に表示

### route APIとの整合性
- route APIが利用可能な場合は優先的に使用
- 404エラー時のみフォールバック

## 実装順序

1. ✅ 実装計画をMarkdownファイルに保存
2. `_make_request`メソッドの修正（ステータスコード情報の保持）
3. `_find_alternative_routes`メソッドの実装
4. `convert`メソッドのエラーハンドリング追加
5. テストファイルの作成・実行
6. PR作成

## 破壊的変更

なし。エラーメッセージの改善のみで、既存の動作は変更されません。
