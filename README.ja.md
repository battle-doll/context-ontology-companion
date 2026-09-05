# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

選択したプロジェクトの決定、要件、制約をローカルに保存し、出典や変更履歴とともに検索できます。プロジェクトの変化に応じて記録を更新・撤回・削除し、必要なコンテキストをほかのツール向けにエクスポートできます。

macOS、Windows、Linux と Python 3.11 以降に対応しています。API キーやリモートサービスは不要です。

## インストール

```text
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

スキル、サーバー、スキーマを含むプラグイン全体をインストールしてください。インストール後、プロジェクトで新しい Codex タスクを開くと、インストールしたスキルを利用できます。

## プロジェクトに接続

対象プロジェクトの新しい Codex タスクで、次のように依頼します。

```text
$manage-approved-context
現在のプロジェクトに、このプラグインのローカル MCP 接続を設定してください。
```

設定後、同じプロジェクトで新しいタスクを開くと MCP ツールを利用できます。直接実行するコマンド、インストール先の確認方法、OS 別の手順は [ローカル MCP 設定](docs/LOCAL_MCP.md) と [Windows クイックスタート](docs/WINDOWS_QUICKSTART.md) を参照してください。

## 現在の作業に適用

```text
$apply-context-ontology
Context Ontology Companionをここに適用し、関連するプロジェクトの制約を取得して現在の作業を続けてください。
```

適用範囲は現在の会話です。実際のMCPまたは同梱CLIを確認し、完全に一致する保存済み情報は再取得して利用します。保存・修正は明示的な依頼に限り、類似・矛盾する記録は対象の選択を待ちます。CodeとContractsは任意であり、他製品のインストールや有効化は行いません。

## 使い方

保存したい決定を具体的に伝えます。

```text
$manage-approved-context
このプロジェクトの要件として、macOS、Windows、Linux をサポートすることを保存してください。
このメッセージを出典にしてください。
```

後のタスクで検索できます。

```text
$manage-approved-context
このプロジェクトがサポートする OS を検索し、出典とともに表示してください。
```

選択した記録の更新・削除、変更履歴の表示、コンテキストのエクスポートも依頼できます。MCP 接続なしで使える CLI コマンドは [ローカル利用ガイド](docs/LOCAL_USE.md) にあります。

データはリポジトリの外にローカル OS アカウントで保存され、プロジェクトのパスごとに分かれます。保存するのは選択した内容だけで、会話全体は自動収集しません。保存された決定はコンテキストであり、後の操作を実行する権限にはなりません。認証情報や機密性の高い個人情報は保存しないでください。クラウド上だけで動くホストには、ローカルランタイムへの別途接続が必要です。

## アップデート

```text
codex plugin marketplace upgrade context-ontology-preview
codex plugin add context-ontology-companion@context-ontology-preview
```

アップデート後、プロジェクトで新しい Codex タスクを開き、更新されたスキルを読み込んでください。そのタスクで上記の接続設定を再度依頼し、さらに新しいタスクを開くと、更新された MCP 接続を利用できます。

## ヘルプ

[ドキュメント](docs/ja/README.md) · [サポート](SUPPORT.md) · [プライバシー](PRIVACY.md) · [セキュリティ](SECURITY.md) · [変更履歴](CHANGELOG.md)

[Apache-2.0](LICENSE) ライセンスで提供しています。
