# clip_to_psd への提案PR案（ローカル準備）

目的
- 変換の堅牢性向上（未定義テキスト属性や一部レイヤー構成での失敗を回避）
- 失敗時も継続可能なフォールバックと警告ログの整備

主な変更点（提案）
- テキスト属性のパース強化（`parse_layer_text_attribute`）
  - 未知/不完全なパラメータは例外を握り潰しスキップ（WARNINGログ）
  - サイズ不一致（ofs!=size）はスキップ（WARNINGログ）
- 欠落パラメータのデフォルト
  - `param_align` が無ければ左揃え(0)
  - `quad_verts` が無ければ `bbox` から矩形を仮定
  - `aspect_ratio` が無ければ 100%
  - `font` 未指定は `Sans`、`font_size` 未指定は `12pt` 相当（dpi換算）、`color` 未指定は黒
- レイヤーピクセルのフォールバック
  - packing が (1,4) 以外の場合、`--psd-empty-bitmap-data` 指定時は空ビットマップとして出力（Assertion回避）

再現と効果
- 再現（例）: `ValueError: 57`（テキスト属性）や `AssertionError`（packing型）で停止
- 効果: 上記ケースでも変換継続、PSD出力完了（WARNINGを残す）

差分
- パッチ（参考）: `docs/integrations/clip_to_psd_upstream.patch`

テスト観察
- サンプル複数（日本語テキスト多数含む）で停止せずPSD出力が可能
- `--blank-psd-preview --psd-empty-bitmap-data` の併用で高速・安定化

今後の改善余地
- 未対応packingのRLE対応
- 既定値の根拠を仕様調査で補強
- `--strict`/`--fail-on-warn` など動作方針を選べるCLIオプション

