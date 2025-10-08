# Clip — CLIP STUDIO PAINT 用Gitトラッキング補助ツール

## 概要
Clip は、CLIP STUDIO PAINT の `.clip` ファイルからコミットごとのプレビュー画像を抽出・閲覧し、制作過程の GIF を生成できる Go 製CLIです。大きなバイナリの取り扱いには Git LFS の利用を推奨します。

## 必要要件
- Go 1.7 以降
- Git（LFS 推奨）
- macOS 等のUnix系環境

## インストール
```sh
go get github.com/lycoris0731/clip
```

## 使い方
1) 初期化（対象の `.clip` ファイルを指定）
```sh
clip init TARGET_FILE.clip
```
`.git/hooks/post-commit` を更新し、`.clip/` ディレクトリに画像が保存されます。

2) コミット時点の画像表示
```sh
clip show HEAD~       # 直前のコミット
clip show <HASH> ...  # 複数指定も可
```

3) 制作過程の GIF 生成
```sh
clip gif [オプション]
```

4) 生成物の掃除
```sh
clip clean
```

## ビルド / テスト
```sh
make build   # ./clip を生成
make test    # 単体テスト（go test -v）
```
ベンチマーク（GIF生成）：
```sh
go test -bench=. -run ^$
```

## 注意事項
- `.clip/` と `clip` バイナリは生成物です（`.gitignore` 済み）。
- `clip init` は Git のフックを書き換えるため、まずは検証用リポジトリで試してください。

## 今後の予定（Python3 版）
本ツールをベースに、モダンな macOS 環境向け Python 3 プロジェクトへ移植予定です（作業ブランチ: `feat/py3-port`）。既存CLIと同等のサブコマンド（init/export/show/gif/clean）互換を目指します。
