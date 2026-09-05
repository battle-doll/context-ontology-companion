# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

**P1a 開発プレビュー · [現在の公開・検証状況](release-state.json)**

明示的に共有したプロジェクトの決定・目標・制約を、出典と変更履歴とともに次の作業へ引き継ぎます。Context Ontology Companion は独立した公開プラグインとして開発中です。

`demo` は合成例、一時保存、模擬承認を使用します。別のローカル試作版には、永続ローカル保存、認証付きループバックの人による確認画面、手動設定する stdio を実装しました。ローカルの合成テストは成功しています。macOS の Codex 0.153.3 で、試験用と明記したサンプルを用いた手動設定のローカル stdio スモークテストも成功しました。公開 GitHub マーケットプレイスからのインストールと、インストール済みランタイムのスモークテストも macOS で成功しました。ホスト型 ChatGPT 連携と実際の人による承認は未検証です。universal Directory への提出は別の手続きで、まだ行っていません。本番での実データ利用と本番認証は未対応です。

[ローカルランタイムと認証付き確認ガイド（英語）](docs/LOCAL_RUNTIME.md)

認証付きローカル確認画面と手動設定の stdio はプレビューです。macOS Codex のスモークテストは模擬承認を使用しており、人による確認手順を検証したものではありません。合成データだけを使用してください。Windows ACL による保護は未検証です。

## 公開プレビューをインストール

公開プレビューは現在インストールできます。プラグイン対応の Codex CLI で完全なパッケージをインストールします。

```sh
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

新しい Codex タスクで `$manage-approved-context` を呼び出し、インストールしたパッケージの合成デモを実行するよう依頼します。実行コード・例・同梱契約が必要なので、`SKILL.md` だけをコピーせず、バンドル全体を保持してください。永続保存と人による確認の設定は、このデモとは別です。

[Windows クイックスタート](docs/WINDOWS_QUICKSTART.md) · [現在のリリース状況](release-state.json)。GitHub マーケットプレイスからのインストールと universal Directory への公開は別の状態です。以下の CI 証拠はリンク先の完了した実行結果です。その後の公開・OS 検証状況はリリース状態ファイルを参照してください。

## ローカルプレビューを実行

このリポジトリのディレクトリで Python 3.11 以降を使用します。プレビューのコマンドに追加の Python パッケージは不要です。仮想環境と Windows コマンドは OS ガイドを参照してください。

```sh
python3 --version
python3 scripts/run.py demo
python3 scripts/run.py tools
python3 scripts/check.py
```

これらはローカル開発コードを実行するコマンドです。プラグインのインストールやホストサービスの作成は行いません。例は合成データです。

## 対応 OS と検証状況

対応対象 OS は **macOS・Windows・Linux** です。ソースの移植性、実行済み OS テスト、プラグインホストの動作は別々に確認します。リンク先の CI では 3 OS × 3 Python の全 9 組み合わせが成功しました。ホストへのインストールは別途検証します。

| OS | 実行証拠 |
| --- | --- |
| macOS | CI PASS — Python 3.11・3.12・3.13（3/3） |
| Windows | CI PASS — Python 3.11・3.12・3.13（3/3）。Windows Codex ホストへのインストールは未試験 |
| Linux | CI PASS — Python 3.11・3.12・3.13（3/3）。Linux Codex ホストへのインストールは未試験 |
| プラグインホスト連携 | macOS Codex 0.153.3 のローカル stdio と公開 GitHub マーケットプレイスからのインストールは成功。Windows/Linux ホストへのインストール・ホスト型 ChatGPT・実際の人による承認は未検証 |

[CI 証拠：全 9 ジョブ成功](https://github.com/battle-doll/context-ontology-companion/actions/runs/33975562432).

[macOS / Windows / Linux ガイド](docs/ja/PLATFORMS.md)

## 製品の境界

Code・Context・Contracts は独立した製品です。利用側は Contracts プラグインをインストールせずに契約成果物を固定または同梱できます。DB や権限の共有、自動プラグイン呼び出し、既存 Code 製品の変更は意味しません。

デモとローカル確認用の試作版には合成データだけを使用します。保存された文やモデルの承認フラグは現在の操作を許可しません。ローカルアダプターは OS アカウントと管理者を信頼しており、同じ無制限のファイルアクセス権を持つプロセスから承認を隔離しません。過去の `known_at` 再構成は未対応です。

## ドキュメント

[ドキュメント一覧](docs/ja/README.md) · [構成とロードマップ](docs/ja/ARCHITECTURE_AND_ROADMAP.md) · [バージョン方針](docs/ja/VERSION_POLICY.md) · [リリースとロールバック](docs/ja/RELEASE_POLICY.md)

[セキュリティ](docs/ja/SECURITY.md) · [プライバシー](docs/ja/PRIVACY.md) · [サポート](docs/ja/SUPPORT.md) · [貢献](docs/ja/CONTRIBUTING.md) · [変更履歴](CHANGELOG.md)

[Apache-2.0 ライセンス](LICENSE)を適用します。現在の公開・検証状況は [release-state.json](release-state.json) を参照してください。
