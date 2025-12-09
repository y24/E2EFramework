# ページオブジェクト階層化 設計案

## 現状
- ページオブジェクトは `src/pages` 直下にフラット配置。
- 各アクション/条件のターゲット解決は `module.Class.member` の3段固定で `importlib.import_module(f"src.pages.{module}")` を実行。
  - 対象: `UIAction` / `VerifyAction` / `ConditionEvaluator` / `WebAction` / `ScreenshotAction` / `DebugAction`。
- `ExcelAction` は `from src.pages.excel_page import ExcelPage` で静的 import。
- シナリオ例は `notepad_page.NotepadPage.editor` などフラット前提。

## 課題
- サブフォルダ化（例: `desktop/notepad_page.py` や `web/alert_sample_page.py`）をすると、ターゲットに含まれるドット数が増え、既存パーサーが破綻する。
- 静的 import の `ExcelAction` はファイル移動で確実に壊れる。

## 目標
- `src/pages` 配下をサブパッケージ化しても動作するターゲット解決を提供。
- 既存のフラット指定との後方互換を維持。
- ターゲット解決ロジックを一元化し、重複実装を排除。

## 仕様案
1. **ターゲット形式の拡張**
   - 形式: `<module_path>.<Class>.<member>`（ドット3つ以上を許容）。
   - 解析: `parts = target.split('.')`; `module_path = '.'.join(parts[0:-2])`; `class_name = parts[-2]`; `member_name = parts[-1]`。
   - 既存の `notepad_page.NotepadPage.editor` も `module_path=notepad_page` でそのまま動作。
   - `DebugAction list_descendants` は従来通り `module.Class`（member 省略時は `window`）も許容。

2. **Resolver ユーティリティの追加 (`src/utils/page_resolver.py`)**
   - `parse_target(target: str, default_member: str|None=None) -> ParsedTarget`（dataclass: module_path/class/member）。
   - `load_page_instance(parsed) -> object`: `importlib.import_module(f"src.pages.{parsed.module_path}")` でクラス取得しインスタンス生成。
   - `resolve_member(target: str, default_member: str|None=None)`: 上記2つを束ねてメンバー取得。存在/AttributeError/ImportError を説明的に raise。
   - (Web用) `resolve_locator_tuple(member)`: `(type, value)` 形式チェックと By 変換ヘルパ。

3. **各所の呼び出しを Resolver に置き換え**
   - `ConditionEvaluator._resolve_element`
   - `UIAction` ターゲット解決
   - `VerifyAction._resolve_target`
   - `WebAction._resolve_target`（直接ロケーター形式 `xpath:...` などは現状維持、ページ指定のみ resolver へ）
   - `ScreenshotAction`（要素キャプチャ解決）
   - `DebugAction._list_descendants`（default_member=`window` を渡す）

4. **ページ配置例**
```
src/pages/
  __init__.py
  base_page.py
  base_web_page.py
  desktop/
    __init__.py
    notepad_page.py
    flexible_renamer.py
    excel_page.py
  web/
    __init__.py
    alert_sample_page.py
```

5. **ExcelAction の対応**
- `ExcelPage` をサブフォルダに移す場合、静的 import をやめ resolver ベースでロードするか、新パスに更新。
- シナリオで Excel のターゲットを使う場合、`desktop.excel_page.ExcelPage.<member>` 形式に変更可能（旧形式も後方互換）。

6. **移行指針**
- 既存シナリオ/ターゲットは変更なしで動作させる（後方互換）。
- サブフォルダを使うページから順次ターゲットを `desktop.xxx.Class.member` / `web.xxx.Class.member` に更新。
- ドキュメント（action/target 記法リファレンス）に新形式を追記。

7. **テスト案**
- `page_resolver` のユニットテスト: フラットとネストのパース/インポート成功、存在しないモジュール/クラス/メンバーの例外メッセージ確認。
- Web ロケーター tuple のバリデーションテスト。
- 簡易シナリオ実行またはモックで各アクションのターゲット解決が resolver 経由で呼ばれることを確認。
