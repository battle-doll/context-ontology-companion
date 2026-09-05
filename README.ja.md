# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

選択したプロジェクトの決定、要件、制約をローカルに保存し、出典や変更履歴とともに検索できます。プロジェクトの変化に応じて記録を更新・撤回・削除し、必要なコンテキストをほかのツール向けにエクスポートできます。

macOS、Windows、Linux と Python 3.11 以降に対応しています。API キーやリモートサービスは不要です。

## インストール

```text
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

スキル、サーバー、スキーマを含むプラグイン全体をインストールしてください。

## プロジェクトに接続

Codex で対象のプロジェクトを開き、次のように依頼します。

```text
$manage-approved-context
現在のプロジェクトに、このプラグインのローカル MCP 接続を設定してください。
```

設定後、同じプロジェクトで新しいタスクを開くと MCP ツールを利用できます。直接実行するコマンド、インストール先の確認方法、OS 別の手順は [ローカル MCP 設定](docs/LOCAL_MCP.md) と [Windows クイックスタート](docs/WINDOWS_QUICKSTART.md) を参照してください。

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

アップデート後は上記の接続設定を再度依頼し、新しいタスクを開いてインストール済みの新バージョンを利用してください。

## ヘルプ

[ドキュメント](docs/ja/README.md) · [サポート](SUPPORT.md) · [プライバシー](PRIVACY.md) · [セキュリティ](SECURITY.md) · [変更履歴](CHANGELOG.md)

[Apache-2.0](LICENSE) ライセンスで提供しています。
