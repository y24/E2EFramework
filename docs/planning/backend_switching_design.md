# UIA/Win32 バックエンド切り替え設計メモ

## 現状整理
- SystemAction の `start_app` だけが backend を受け取り DriverFactory に単一 `_app` / `_backend` として保持しているが、 `_backend` は他の場所で参照されていない。
- `connect_app` は DriverFactory に存在するがシナリオから呼び出す手段がなく、既存プロセスへの接続や backend 併用ができない。
- BasePage は DriverFactory.get_app() を呼ぶのみで、Desktop / Application を backend ごとに切り替える仕組みがない。
- NotepadPage / DebugAction / Condition などは `Desktop(backend='uia')` をハードコードしており、win32 指定時はここだけ UIA を見に行く。
- シナリオ JSON は start_app の params.backend 以外に backend や app を指定する場所がなく、同一アプリ内での切替や複数ハンドル併用ができない。

## 目標
- 同一アプリに対して uia / win32 を場面に応じて切り替えられること。
- 既存シナリオとの後方互換性を保つこと。
- 切替の責務をドライバ層で吸収し、Page / Action からは簡潔に利用できること。

## 設計概要
1) DriverFactory の拡張
- `_apps: Dict[alias][backend]` と `_active_backend: Dict[alias]` を持ち、複数ハンドルを並行保持。
- `start_app(path, backend='uia', alias='default', **kwargs)` / `connect_app(alias, backend, **kwargs)` で各バックエンドに接続し、プロセス ID や起動コマンドを記録。
- `switch_backend(alias, backend, attach_running=True)` を追加。attach=True の場合は既存プロセス (PID/タイトル/パス) をもとに別バックエンドで connect、無ければ start する。
- `get_app(alias='default', backend=None)` と `get_desktop(backend=None)` で明示 backend もしくは active_backend を返す。
- Excel 用管理は現行のまま分離。
2) Context / App エイリアス管理
- `CURRENT_APP_ALIAS` と `CURRENT_BACKEND` を Context.variables に格納。SystemAction で開始/切替時に更新し、未指定時のデフォルトとして利用。
3) Page 層の対応
- BasePage に `alias='default'`, `backend=None` を受け取るよう変更し、DriverFactory から正しい App / Backend を取得する。
- Desktop 検索を行う箇所は `DriverFactory.get_desktop(backend or active_backend)` を使用。NotepadPage のような固定 `backend='uia'` 指定を排除。
- バックエンド差分がある要素は `locators = {'uia': {...}, 'win32': {...}}` のように持ち、Page 側で backend に応じて切り替える。
4) Action 層の対応
- SystemAction: 既存 start_app に alias / remember_pid を追加し、新規 `switch_backend`, `connect_app` を実装。backend / app_alias を Context に反映。
- UI / Verify / Condition / Screenshot / DebugAction: `app_alias` と `backend` (任意) を params で受け、ターゲット解決時に BasePage へ渡す、もしくは Context の CURRENT_* を利用。指定が無ければ従来どおり default+uia。
5) シナリオスキーマ拡張
- 各 step に `app_alias` / `backend` を任意指定可とする。SystemAction の start_app で alias を登録し、以降の step は backend を省略すれば現在の active_backend を使用。
- 新規 `switch_backend` を追加し、同一プロセスに win32 で再接続する等の用途に使う。

## シナリオ例（新仕様案）
```json
{
  "id": "SAMPLE-011",
  "name": "UIA/Win32切替デモ",
  "steps": [
    {
      "type": "system",
      "name": "アプリをUIAで起動",
      "params": {
        "action": "start_app",
        "path": "C:/Program Files/FooApp/foo.exe",
        "backend": "uia",
        "app_alias": "foo"
      }
    },
    {
      "type": "ui",
      "name": "UIAでリストに入力",
      "params": {
        "operation": "input",
        "target": "foo_page.FooPage.search_box",
        "value": "abc",
        "app_alias": "foo",
        "backend": "uia"
      }
    },
    {
      "type": "system",
      "name": "win32へ切替（同一プロセスに接続）",
      "params": {
        "action": "switch_backend",
        "backend": "win32",
        "app_alias": "foo",
        "attach_running": true,
        "process_name": "foo.exe"
      }
    },
    {
      "type": "ui",
      "name": "win32でレガシーグリッド操作",
      "params": {
        "operation": "click",
        "target": "foo_page.FooPage.legacy_grid",
        "app_alias": "foo",
        "backend": "win32"
      }
    },
    {
      "type": "verify",
      "name": "結果表示はUIAで確認",
      "params": {
        "type": "contains",
        "target": "foo_page.FooPage.result_text",
        "contains": "Completed",
        "app_alias": "foo",
        "backend": "uia"
      }
    }
  ]
}
```

## 既存影響と移行
- backend / app_alias 未指定の既存シナリオは `alias='default'`, `backend='uia'` で従来動作。
- Notepad 等の Page で UIA 固定ロジックを外す必要があるが、ロケータは共通で流用できる想定。
- 切替失敗時の例外メッセージにプロセス情報を含め、デバッグ容易にする。

## 実装・検証タスク
- DriverFactory リファクタリングと単体テスト（start / connect / switch の組み合わせ）。
- BasePage と既存 Page の backend 対応リファクタ（Desktop 利用箇所の差し替え）。
- Action / Condition / Screenshot での app_alias / backend 受け渡し実装と回帰テスト。
- サンプルシナリオ・ドキュメントの更新と、win32/UIA 混在の小さな E2E デモの追加。
