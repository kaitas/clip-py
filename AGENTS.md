# Repository Guidelines

> ローカルの非公開ノートは `.local/AGENTS.md` を参照してください（Git追跡対象外）。
> PyPI公開などの作業ToDoは `.local/MyTodo.md`（[USER]/[CODEX]/[AUTO] ステータス付き）を参照。

## Project Structure & Module Organization
- Go CLI lives at repo root: `*.go` (commands in `commands.go`, entrypoint in `clip.go`).
- Tests sit alongside sources (`*_test.go`) and use fixtures in `tests/assets/`.
- Assets for docs/demos: `res/` (e.g., `res/out.gif`).
- Runtime artifacts: `.clip/` (generated), `.clipconfig` (created by `clip init`). These are ignored by Git.

## Build, Test, and Development Commands
- `make deps` — install Go deps via Glide (`glide install`).
- `make build` — build binary to `./clip`.
- `make test` — run unit tests (`go test -v`).
- Examples:
  - Build: `make build && ./clip --help`
  - Test with coverage: `go test ./... -cover`
  - Benchmarks (GIF generation): `go test -bench=. -run ^$`

## Coding Style & Naming Conventions
- Formatting: run `go fmt ./...`; prefer also `go vet ./...` locally.
- Indentation: tabs for `*.go` (8-space width). LF line endings. See `.editorconfig`.
- Naming: exported identifiers `CamelCase`; files are lowercase with underscores only when helpful (e.g., `init_clip.go`).
- Keep functions small and command logic cohesive (per-command type with `Run/Help/Synopsis`).

## Testing Guidelines
- Framework: standard library `testing` with `*_test.go` next to code (e.g., `gif_test.go`, `export_test.go`).
- Fixtures: use `tests/assets/` (no network access). Clean up temp files/dirs.
- Targets: add tests for new commands and edge cases; include table tests where reasonable.
- Commands:
  - Run all: `make test`
  - With coverage: `go test ./... -coverprofile=cover.out && go tool cover -func=cover.out`

## Commit & Pull Request Guidelines
- Commit style (from history): `[ADD]`, `[MOD]`, `[FIX]`, `[WIP]` prefix; imperative mood ("Add", "Fix").
- Keep commits focused; include rationale in body when non-trivial.
- PRs should include:
  - Clear description, linked issues, and reproduction steps.
  - CLI examples (e.g., `clip init sample.clip`, `clip show HEAD~`) and screenshots/GIFs when UX changes.
  - Notes on tests added/updated and any docs changes (README).

## Security & Configuration Tips
- `clip init` updates `.git/hooks/post-commit` in the current repo; test this in a sandbox repo.
- Prefer Git LFS for large `.clip` files; do not commit generated `.clip/`, `db/`, `tmp/`, or the `clip` binary (already in `.gitignore`).

## 作業計画（Python3 移植）
- ブランチ: `feat/py3-port` を作成済み。以後、このブランチで作業。
- ツール/環境: Python 3.11+, パッケージ管理は Poetry または Hatch、Lint/Format は Ruff+Black、テストは Pytest。
- ひな形作成: `pyproject.toml`、`src/clip_py/`、`tests/` を用意し、CLI は Typer(Click) ベースで実装。
- 機能互換: `init/export/show/gif/clean` のCLI I/Fと挙動を現行に合わせて移植。
- コア処理: `.clip` 内の SQLite 抽出（ヘッダ探索→DB抽出→`CanvasPreview` 読み取り）と GIF 生成（Pillow/imageio）をPython化。
- Gitフック: `post-commit` の更新は追記戦略とバックアップを取り、安全に適用（上書き注意）。
- テスト: 既存フィクスチャ `tests/assets/` を再利用し、単体/統合テストを整備。カバレッジ目標 80%+。
- CI: macOS で lint/format/test を実行するワークフローを追加。
- ドキュメント: `README.ja.md` を基準に Python 版の使用例を追記し、準備ができ次第 README を統一。

## 中長期計画（マンガプロジェクト・プレビューツール）
以下は、`.clip` および `.cmc` の分析結果に基づく、原作者（ネーム・セリフ担当）と作画担当者のコラボを円滑化するための中長期計画です。

### 目的
クリスタ未導入の原作者にも、進捗をほぼリアルタイムで共有し、ページ単位で的確なフィードバックを受け取れるWebダッシュボードを提供する。

### ワークフロー案
1. 作画担当者が `.cmc`（プロジェクト）と各ページの `.clip` を共有フォルダ（Dropbox/Google Drive/Git等）へ保存。
2. ツールが共有フォルダを監視し、変更時に自動処理：
   - `.cmc` をSQLiteとして読み込み、ページ順序とファイルパスを取得。
   - 各 `.clip` からサムネイルPNGを抽出。
3. Webダッシュボードを更新し、ページ順にサムネイルを表示。更新をSlack/メールで通知。
4. 原作者はブラウザで一覧・拡大表示し、ページ単位のコメント/修正指示を入力。
5. 作画担当者へ通知。どのページにどの指示が入ったかを即時把握。

### 具体機能
- 自動ページ一覧生成：`.cmc`/`.clip`解析により、順序付きサムネイル一覧を生成。
- バージョン管理・差分表示：更新前後のサムネイルを並列表示し変更点を可視化。
- コメント・修正指示：ページ単位でテキストコメントを登録。
- ステータス管理：作業中/レビュー待ち/修正中/完了などを付与し進捗を見える化。

### 限界と注意
1. 解像度の制約：抽出は低解像度サムネイルに限定。細部品質の評価には不向き。
2. テキスト抽出不可：`.clip` 内テキストレイヤのセリフ抽出は不可。必要に応じて別途JPEG等の補助出力を運用。
3. 非公式仕様リスク：将来のファイル仕様変更で動作不能となる可能性。バージョン検出とフェイルセーフ実装を検討。

### 実装メモ（技術）
- バックエンド：Python（FastAPI/Celery）で監視・抽出・画像変換。SQLite/Redis等でキュー・メタ保持。
- フロント：Next.js等でダッシュボード、コメントUI、差分ビューを提供。
- 監視：ファイル監視（watchdog）またはGitフック/CI連携。クラウド連携（Dropbox/Drive API）は段階導入。
