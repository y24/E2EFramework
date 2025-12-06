# AIエージェント向けシナリオ実装ガイドライン

このドキュメントは、AIエージェントに新規シナリオの実装を依頼する際の作業方針と、AIエージェント自身が参照すべき実装ルールをまとめたものです。

## 1. 概要
本E2Eフレームワークは、JSON形式のシナリオファイルと、PythonによるPage Object Model (POM) を組み合わせたアーキテクチャを採用しています。
AIエージェントは、既存のPage Objectを再利用するか、必要に応じて新規作成し、JSONシナリオを構築します。

## 2. 実装フロー
新しいシナリオを実装する場合、以下の手順で進めてください。

1.  **要件の理解**: どのような操作を行い、何を検証するかを明確にします。
2.  **既存リソースの確認**:
    *   対象アプリケーションのPage Objectが `src/pages/` に存在するか確認します。
    *   必要なアクション（クリック、入力、検証など）がフレームワークでサポートされているか確認します。
3.  **Page Objectの実装/修正 (必要な場合)**:
    *   新しい画面や要素を操作する場合は、該当するPage Objectクラスにプロパティを追加します。
    *   要素の特定には `pywinauto` のセレクタ（`title_re`, `control_type` 等）を使用します。
4.  **シナリオファイルの作成**:
    *   `scenarios/` 配下の適切なディレクトリにJSONファイルを作成します。
    *   `steps` 配下に操作手順を記述します。
5.  **実行と検証**:
    *   `pytest` を使用してシナリオを実行し、動作を確認します。

## 3. Page Objectの実装ルール
*   **配置場所**: `src/pages/`
*   **親クラス**: `src.pages.base_page.BasePage` (Win32アプリ) または `src.pages.base_web_page.BaseWebPage` (Webアプリ) を継承します。
*   **要素定義**: `@property` デコレータを使用し、操作対象の UI 要素を返します。
    *   要素が見つからない場合のハンドリング（`exists(timeout=1)` 等）も考慮すると堅牢になります。

```python
# src/pages/notepad_page.py の例
from src.pages.base_page import BasePage

class NotepadPage(BasePage):
    def __init__(self):
        super().__init__(title_re=".*(Notepad|メモ帳).*")

    @property
    def editor(self):
        # 編集エリアの取得
        return self.window.child_window(control_type="Edit")
```

## 4. シナリオファイルの記述ルール
*   **フォーマット**: JSON
*   **基本構造**:
    *   `name`: シナリオ名
    *   `description`: 説明
    *   `steps`: アクションのリスト
*   **アクションタイプ**:
    *   `ui`: UI操作 (click, input, verify 等)
    *   `system`: システム操作 (exec, sleep 等)

```json
{
  "name": "メモ帳テスト",
  "steps": [
    {
      "step_id": 1,
      "type": "system",
      "action": "exec",
      "path": "notepad.exe"
    },
    {
      "step_id": 2,
      "type": "ui",
      "target": "notepad_page.NotepadPage.editor",
      "action": "input",
      "value": "Hello World"
    }
  ]
}
```

## 5. 条件分岐 (Advanced)
特定の要素が存在する場合のみステップを実行する等の制御が可能です。

*   **condition**: ステップに `condition` ブロックを追加します。
*   **type**: `element_exists` や `variable` が使用可能です。

```json
{
  "step_id": 3,
  "type": "ui",
  "target": "notepad_page.NotepadPage.save_button",
  "action": "click",
  "condition": {
    "type": "element_exists",
    "target": "notepad_page.NotepadPage.save_button",
    "expected": true,
    "timeout": 2
  }
}
```

## 6. AIエージェントへの依頼プロンプト例
AIエージェントに実装を依頼する際は、以下のテンプレートを活用してください。

```markdown
# 依頼内容
E2Eテストシナリオの新規作成をお願いします。

# テスト対象
*   アプリ: [アプリ名/パス]
*   操作内容:
    1.  アプリを起動する
    2.  [メニュー名] を開く
    3.  [ボタン名] をクリックする
    4.  [メッセージ] が表示されることを確認する

# 実装要件
1.  既存の `src/pages/` を確認し、Page Objectが不足している場合は追加・修正してください。
2.  シナリオファイルは `scenarios/test/[識別子].json` として作成してください。
3.  検証ステップ (`verify`) を必ず含めてください。
4.  実装後、実行コマンドと期待される結果を提示してください。

# 参考ファイル
*   Page Object例: src/pages/notepad_page.py
*   シナリオ例: scenarios/sample/SAMPLE-001_notepad.json
```
