# clip_to_psd 取り込みと需要分析

## 概要
- サブモジュール: `third_party/clip_to_psd`（元リポジトリ: https://github.com/dobrokot/clip_to_psd ）
- 目的: `.clip` → `.psd` 変換ツールの検証・連携検討（将来的にCLI統合/プラグイン化）

## 使い方（概要）
```sh
python clip_to_psd.py input.clip -o output.psd
```
- 依存: Python 3。Pillow は任意（PSDプレビューやPNG書き出し時に推奨）。

## 需要の初期指標（GitHub 公開メタ）
- Stars: 37
- Forks: 3
- Open Issues: 1
- Watchers(subscribers): 1
- Default Branch: main
- Last Push: 2024-07-05T23:32:42Z
- Created: 2024-06-22T18:32:48Z
- License: MIT

所見:
- 公開から日が浅いがスターは一定あり、関心は存在。PSD出力のニーズはプロの現場/校了連携で高い傾向。
- Pillow任意/単体動作という特性は、導入障壁が低く評価。

リスク/限界:
- Vector/トーン/フレーム等の未対応領域あり（README記載）。CSP仕様更新による互換性リスク。
- PSDでの高度機能はCSPへ再読み込み不可な場合がある（Photoshop前提機能）。

次アクション（提案）
- 互換テスト: `tests/assets/sample.clip` での最小変換とPSDの基本プロパティ検査。
- CLI連携: `clip-py` に `convert psd` サブコマンドを用意し、サブモジュールを呼び出す薄いラッパを実装。
- フィードバック収集: Issue/Discussions にアンケート（用途、頻度、失敗ケース）。
- 将来: pip 配布/エントリポイント統合、最小限の互換層・例外処理追加。

