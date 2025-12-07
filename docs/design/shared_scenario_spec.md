# 共有シナリオ（Shared Scenario）設計仕様書

## 1. 概要
ログイン処理や初期設定など、複数のテストシナリオで共通して利用される手順を「共有シナリオ」として定義し、他のシナリオから参照・再利用可能にする機能を実装する。

## 2. ディレクトリ構成
プロジェクトルート直下に `scenarios_shared` フォルダを作成し、そこに共有シナリオ（.json）を格納する。

```
ProjectRoot/
  ├── scenarios/          # 通常のテストシナリオ
  │   └── test/
  │       └── login_test.json
  └── scenarios_shared/   # 共有シナリオ
      └── common/
          └── login.json
```

## 3. シナリオ定義 (JSON仕様)

### 3.1 共有シナリオファイル
通常のシナリオファイルと同じフォーマット（JSON）を使用する。
ただし、`steps` 配列のみが必須となり、`id` や `tags` は任意（参照時は無視される想定でも良いが、管理上あると望ましい）。

**例: scenarios_shared/common/login.json**
```json
{
  "name": "共通ログイン処理",
  "steps": [
    {
      "name": "ユーザーID入力",
      "type": "ui",
      "params": {
        "target": "login_page.user_input",
        "value": "${login_user}"
      }
    },
    {
      "name": "パスワード入力",
      "type": "ui",
      "params": {
        "target": "login_page.password_input",
        "value": "${login_password}"
      }
    },
    {
      "name": "ログインボタン押下",
      "type": "ui",
      "params": {
        "operation": "click",
        "target": "login_page.login_button"
      }
    }
  ]
}
```

### 3.2 参照側シナリオでの記述
`steps` 内で、`type: "run_scenario"` (または `include_scenario`) を指定することで、共有シナリオを呼び出す。

**パラメータ仕様**
*   `type`: `"run_scenario"` (仮)
*   `params`:
    *   `path`: `scenarios_shared` フォルダからの相対パス (例: `common/login.json`)
    *   `args`: (オプション) 共有シナリオ内で使用する変数をオーバーライド・設定するための辞書

**例: scenarios/test/my_test.json**
```json
{
  "id": "TEST-001",
  "name": "ログイン後機能確認",
  "steps": [
    {
      "name": "アプリ起動",
      "type": "system",
      "params": { "action": "start_app", ... }
    },
    {
      "name": "管理者としてログイン",
      "type": "run_scenario",
      "params": {
        "path": "common/login.json",
        "args": {
          "login_user": "admin",
          "login_password": "password123"
        }
      }
    },
    {
      "name": "後続の検証処理",
      "type": "verify",
      ...
    }
  ]
}
```

## 4. 実装方式

### 4.1 読み込み時の展開 (Macro Expansion)
`ScenarioLoader` がシナリオを読み込む際、`type: "run_scenario"` を検知したら、対象の JSON を読み込み、その `steps` を展開して元のステップと置き換える方式を採用する。

**メリット:**
*   実行エンジン (`Runner`) の変更が最小限で済む（フラットなステップリストとして扱える）。
*   入れ子（共有シナリオが別の共有シナリオを呼ぶ）にも対応しやすい。

**デメリット:**
*   実行ログ上で、どの共有シナリオ内のステップか分かりにくくなる可能性がある（対策: ステップ名にプレフィックスを付ける、あるいは `_source` 属性を付与してログ出力時に表示する）。

### 4.2 変数の扱い (`args` パラメータ)
展開時に変数をどう渡すかが課題となる。
単純な展開（`Macro Expansion`）の場合、変数は `Context` 上のグローバル変数として扱われることが多い。

**提案方式:**
`run_scenario` ステップに `args` が指定されている場合、**展開されるステップの前**に「変数をセットするステップ」を自動挿入する。

展開イメージ:
```json
[
  // 自動挿入された変数セットステップ
  {
    "name": "Set arguments for login.json",
    "type": "system", // または internal
    "params": {
      "action": "set_variables",
      "variables": { "login_user": "admin", ... }
    }
  },
  // login.json から展開されたステップ
  { "name": "ユーザーID入力", ... },
  { "name": "パスワード入力", ... },
  ...
]
```

※ 変数のスコープについては、現状の `Context` がフラットであれば、上書きされる。実行後に元の値に戻すなどの「ローカルスコープ」的な挙動は複雑になるため、当面は**グローバル変数の上書き**として扱う。

## 5. 実装ステップ

1.  **シナリオローダーの改修 (`src/core/scenario_loader.py`)**
    *   `_expand_scenarios(steps)` メソッドを追加し、再帰的に `run_scenario` を処理する。
    *   `scenarios_shared` フォルダのパスを解決できるようにする。

2.  **実行コンテキスト/システムアクションの拡張**
    *   変数を動的にセットするための仕組みが必要であれば追加する（現状の `Context` に変数セット機能があればそれを利用）。

3.  **検証**
    *   `scenarios_shared/sample_shared.json` を作成。
    *   それを呼び出す `scenarios/test/shared_test.json` を作成し、正しく動作確認。
