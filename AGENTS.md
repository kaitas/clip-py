# Repository Guidelines

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
