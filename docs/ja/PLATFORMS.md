# macOS / Windows / Linux ガイド

対象 OS は macOS・Windows・Linux、必要な Python は 3.11 以降です。各 OS の実行証拠は、コードレビューや CI 行列の設定とは分けて記録します。

| OS | 実行証拠 |
| --- | --- |
| macOS | ローカル Python 3.12.14 合成テスト成功 |
| Windows | `not_run` — CI 設定済み、実行待ち |
| Linux | `not_run` — CI 設定済み、実行待ち |
| プラグインホスト連携 | 保留 — ホスト E2E・ディレクトリ公開未確認 |

仮想環境の作成前に Python のバージョンを確認します。3.11 未満なら、インストール済みの 3.11 以降を選択してください。有効化スクリプトは不要で、環境内の Python を直接呼び出します。

## macOS と Linux

```sh
python3 --version
python3 -m venv .venv
.venv/bin/python scripts/run.py demo
.venv/bin/python scripts/run.py tools
.venv/bin/python scripts/check.py
```

## Windows PowerShell

```powershell
py -3 --version
py -3 -m venv .venv
.venv\Scripts\python.exe scripts/run.py demo
.venv\Scripts\python.exe scripts/run.py tools
.venv\Scripts\python.exe scripts/check.py
```

主要な例には専用シェルインストーラー、Docker、Node.js、管理者権限、API キー、ネットワークサービスは不要です。Python の用意とプラグインホストの対応は別の前提条件です。Linux CLI の動作は Linux デスクトップホストの対応を証明しません。

これらはローカル開発コードを実行するコマンドです。プラグインのインストールやホストサービスの作成は行いません。例は合成データです。

[ドキュメント一覧](README.md)

認証付きローカル確認画面と手動設定の stdio は実装済みプレビューであり、実際のホスト連携とは別です。合成データだけを使用してください。Windows ACL による保護は未検証です。

[ローカルランタイムと認証付き確認ガイド（英語）](../LOCAL_RUNTIME.md)
