===============================================================================
顧客提供用ZIPファイル作成手順
===============================================================================

■ 概要
このドキュメントは、togoid-lib-pythonの顧客提供用ZIPファイルを作成する手順を
説明します。

■ スクリプト
ファイル名: create_distribution.sh
場所: プロジェクトルート

■ 使用方法

1. プロジェクトルートディレクトリに移動
   $ cd /home/souta/projects/togoid-lib-python

2. スクリプトを実行
   $ ./create_distribution.sh

3. 完成
   togoid-lib-python.zip が作成されます

■ 出力ファイル

ファイル名: togoid-lib-python.zip
サイズ: 約41KB
場所: プロジェクトルート

■ ZIPに含まれるファイル

【パッケージ】
  togoid/
    ├── __init__.py
    ├── __main__.py
    ├── annotations.py
    ├── cli.py
    ├── converter.py
    └── label_converter.py

【ドキュメント】
  ├── README.md             - 使用方法、API仕様、Breaking Changes
  ├── TESTING.md            - テスト方法の詳細
  ├── QUICKSTART_UV.md      - uv使用のクイックスタート
  └── PROJECT_STRUCTURE.md  - プロジェクト構造

【テストファイル】
  ├── test_readme_examples.py  - Python APIテスト
  └── test_cli_examples.sh     - CLIテスト

【設定ファイル】
  ├── pyproject.toml  - パッケージ設定
  ├── requirements.txt - 依存関係
  └── .gitignore

■ ZIPから除外されるファイル

• 開発過程のテストファイル
  - test_customer_feedback.py
  - test_config_list_targets.py
  - test_feedback_fixes.py
  - test_route_suggestion.py

• 内部ドキュメント
  - FEEDBACK_FIX_PLAN.md
  - ROUTE_SUGGESTION_PLAN.md
  - R_IMPLEMENTATION_PLAN.md
  - CHANGELOG_SUMMARY.md
  - feedback.md

• キャッシュファイル
  - __pycache__/
  - *.pyc

■ スクリプトの動作

1. 既存のZIPファイルと一時ディレクトリをクリーンアップ
2. 配布用ディレクトリを作成
3. togoidパッケージをコピー
4. __pycache__と*.pycファイルを削除
5. ドキュメントと設定ファイルをコピー
6. 必要なテストファイル（2つのみ）をコピー
7. ZIPアーカイブを作成
8. 一時ディレクトリをクリーンアップ
9. 結果を表示

■ 注意事項

• スクリプトは set -e を使用しているため、エラーが発生すると即座に停止します
• 既存のtogoid-lib-python.zipは自動的に上書きされます
• スクリプトはプロジェクトルートから実行する必要があります

■ トラブルシューティング

Q: 実行権限エラーが出る
A: chmod +x create_distribution.sh を実行してください

Q: ZIPファイルが作成されない
A: zipコマンドがインストールされているか確認してください
   $ sudo apt-get install zip  # Debian/Ubuntu
   $ sudo yum install zip      # RHEL/CentOS

Q: ファイルが見つからないエラー
A: プロジェクトルートディレクトリで実行しているか確認してください

===============================================================================
