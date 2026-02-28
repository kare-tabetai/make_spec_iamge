# CLAUDE.md

このドキュメントはclaude codeが参照する様の基本指示ファイルです。
プロジェクト固有の情報は記載されていません。

## ドキュメントについて

- Docs/spec.mdが仕様書です

## 開発環境

このプロジェクトはdevcontainer上に構築されています。
実装時は、bypassPermissionsを使用して自動で処理をする想定です。

- claude code
- Git
- vscode
- devcontainer
- python3
- uv

## 基本命令

- plan時に不明な部分、曖昧な部分があれば、積極的に質問してください。
- 自分が暴走していると判断した場合は動作を停止してください
- タスクの推敲進捗メモをDocs/Steering/フォルダ内に都度生成するようにしてください
