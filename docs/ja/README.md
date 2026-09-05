# Context Ontology Companion — ドキュメント

[English](../README.md) | [한국어](../ko/README.md) | [日本語](README.md) | [简体中文](../zh-CN/README.md) | [Русский](../ru/README.md)

まずローカルプレビューと制限を確認してください。Context の番号付き設計文書は長期計画であり、現在のランタイム対応を拡大するものではありません。

- [ローカルプレビューを実行](../../README.ja.md)
- [macOS / Windows / Linux ガイド](PLATFORMS.md)
- [構成とロードマップ](ARCHITECTURE_AND_ROADMAP.md)
- [バージョン方針](VERSION_POLICY.md)
- [リリースとロールバック](RELEASE_POLICY.md)
- [セキュリティ](SECURITY.md)
- [プライバシー](PRIVACY.md)
- [サポート](SUPPORT.md)
- [貢献](CONTRIBUTING.md)
- [変更履歴](../../CHANGELOG.md)
- [Apache-2.0](../../LICENSE)

`demo` は合成例、一時保存、模擬承認を使用します。別のローカル試作版には、永続ローカル保存、認証付きループバックの人による確認画面、手動設定する stdio を実装しました。ローカルの合成テストは成功しています。実データの利用、本番認証、実際の ChatGPT/Codex ホスト連携は未対応です。

Code・Context・Contracts は独立した製品です。利用側は Contracts プラグインをインストールせずに契約成果物を固定または同梱できます。DB や権限の共有、自動プラグイン呼び出し、既存 Code 製品の変更は意味しません。

認証付きローカル確認画面と手動設定の stdio は実装済みプレビューであり、実際のホスト連携とは別です。合成データだけを使用してください。Windows ACL による保護は未検証です。

[ローカルランタイムと認証付き確認ガイド（英語）](../LOCAL_RUNTIME.md)
