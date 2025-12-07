# シナリオアクション仕様

`src/core/execution/actions` で登録されているアクション種別とパラメータ仕様。シナリオから `type` を指定して呼び出す想定です。

- **ターゲット指定**: `module.Class.property` 形式で `src.pages` 配下のPage Objectを解決する。Webのみ `locator_type:value` 直指定にも対応。
- **変数利用**: `context` に保存された変数はパラメータに埋め込んで利用可能。

---

## type: system
シナリオ進行の補助や環境操作を行う。

| param | 必須 | 型/デフォルト | 説明 |
| --- | --- | --- | --- |
| action | Yes | string | 動作を指定: `sleep` / `command` / `print` / `start_app` / `set_variables` |
| duration | sleep時 | number, 1.0 | 指定秒数スリープ |
| command | command時 | string | OSシェルで実行するコマンド |
| message | print時 | string | 標準出力へ表示するメッセージ |
| path | start_app時 | string | DriverFactory経由で起動するアプリのパス |
| backend | start_app時 | string, `uia` | pywinautoバックエンド |
| variables | set_variables時 | dict | コンテキストに保存するキーと値 |

---

## type: ui
デスクトップアプリのUI操作。

| param | 必須 | 型/デフォルト | 説明 |
| --- | --- | --- | --- |
| operation | Yes | string | `input` / `click` / `read` |
| target | Yes | string | `module.Class.element` 形式でUI要素を解決 |
| value | input時 | string, "" | 送信する文字列。送信前に Ctrl+A+Delete でクリア |
| regex | read時 | string, optional | 取得テキストに対して抽出する正規表現。グループ1優先 |
| save_as | read時 | string, optional | 抽出/取得した文字列をコンテキスト変数へ保存 |

動作: `input` は type_keys で入力、`click` は click_input、`read` は get_value→window_text の順で取得。

---

## type: screenshot
スクリーンショット取得。

| param | 必須 | 型/デフォルト | 説明 |
| --- | --- | --- | --- |
| filename | No | string | 付与したいファイル名。指定時 additional_name 省略なら拡張子除去で流用 |
| additional_name | No | string | テストID/テスト名に付加する識別子 |
| target | No | string | `module.Class.element` 指定で要素キャプチャ。解決失敗時は全画面 |

保存先はコンテキスト変数 `SCREENSHOTDIR`（既定 `reports/screenshots`）。ファイル名にテストID/テスト名が付与される。

---

## type: web
Seleniumによるブラウザ操作。`target` はページオブジェクト（`module.Class.element` → `(by, value)` タプル）または `locator_type:value` 直指定に対応。既定タイムアウトは10秒。

| operation | 必須パラメータ | 任意パラメータ/デフォルト | 目的 |
| --- | --- | --- | --- |
| start_browser | - | browser=`chrome`, headless=False | 新規ブラウザ起動 |
| connect_browser | - | debugger_address=`localhost:9222`, browser | 既存デバッグポートへ接続 |
| navigate | url | - | 指定URLへ遷移 |
| click | target | timeout=10 | 要素がクリック可能になるまで待ってクリック |
| input | target | value="", clear=True, timeout=10 | 要素へ入力。clear=Trueでsend_keys前にclear |
| read | target | save_as(optional), timeout=10 | 要素テキスト/値を取得し、save_as指定時は変数保存 |
| accept_alert | - | timeout=10 | アラート受諾 |
| dismiss_alert | - | timeout=10 | アラート却下 |
| wait | - | duration=1.0 | 単純待機 |
| close_browser | - | - | ドライバをクローズ |

`locator_type` は `xpath|css|id|name|class|tag|link_text|partial_link_text` をサポート。

---

## type: excel
ExcelPageヘルパー経由でExcelを操作。

| action | 必須パラメータ | 任意パラメータ/デフォルト | 目的 |
| --- | --- | --- | --- |
| start_excel | file_path | - | 指定ブックでExcel起動 |
| select_cell | cell_address **or** (row & column) | - | セル選択 |
| input_text | value | - | 現在セルに文字列入力 |
| ribbon_shortcut | shortcut | - | リボンショートカット操作 |
| save_file | - | file_path(optional) | ブック保存（パス指定で別名保存） |
| close_workbook | - | save=False | ワークブックを閉じる、必要なら保存 |
| exit_excel | - | - | Excel終了＋ページキャッシュリセット |
| handle_dialog | - | title_patterns=[], key_action=`{ESC}`, timeout=10 | 既知ダイアログを検知し指定キー送信 |

---

## type: verify
検証系アクション。`type` で検証内容を指定。

| param | 必須 | 型/デフォルト | 説明 |
| --- | --- | --- | --- |
| type | Yes | string | `exists` / `not_exists` / `clickable` / `equals` / `contains` / `not_contains` / `matches` / `file_exists` / `file_content` |
| target | depends | string | UI要素検証に使用。`exists`/`not_exists`/`clickable` では必須 |
| actual | No | any | 比較用の実値（未指定時はターゲットからテキスト取得） |
| expected | equals/file_content | any | 期待値 |
| contains | contains時 | string | 含まれるべき文字列 |
| not_contains | not_contains時 | string | 含まれてはいけない文字列（省略時 contains を流用） |
| regex | contains/not_contains/matches時 | bool/"true"/"false" | 正規表現判定を有効化 |
| pattern | matches時 | string | 全文一致判定に使うパターン（regex エイリアス） |
| text | No | string | actual が無い場合の検証対象文字列として利用 |
| path | file_exists/file_content時 | string | 対象ファイルパス |
| min_size | file_exists時 | int | バイトサイズ下限 |
| file_type | file_content時 | string, auto | `text`/`excel`。未指定時は拡張子で推定 |
| mode | file_content(text)時 | string, `exact` | `exact` など FileValidator の比較モード |
| encoding | file_content(text)時 | string, `utf-8` | テキスト読み込みエンコーディング |
| cell | file_content(excel)時 | string | 参照セル |
| sheet | file_content(excel)時 | string | シート名 |

`exists`/`not_exists`/`clickable` は UI 要素の状態を直接確認。`contains`/`not_contains` は `regex` 指定で正規表現検索、未指定で部分一致検索。`matches` は全文一致。`file_content` は text/excel を自動判別し FileValidator で確認。

---

## type: debug
デバッグ・調査用。

| param | 必須 | 型/デフォルト | 説明 |
| --- | --- | --- | --- |
| action | Yes | string | `list_desktop_windows` / `list_descendants` / `check_dialog` |
| target | list_descendants時 | string | `module.Class` または `module.Class.property`（未指定プロパティは `window`） |
| filter | list_desktop_windows/list_descendants時 | string, "" | タイトル/テキスト部分一致で絞り込み |
| control_type | list_desktop_windows/list_descendants時 | string, "" | コントロールタイプで絞り込み |
| depth | list_descendants時 | int, None | 最大表示件数（祖先数） |
| class_name | check_dialog時 | string, optional | ダイアログのクラス名（例: `#32770`） |
| title | check_dialog時 | string, optional | タイトル部分一致文字列 |
| timeout | check_dialog時 | float, 1 | 存在確認タイムアウト（秒） |

`list_desktop_windows` はトップレベルウィンドウの一覧を表示。`list_descendants` はページ要素配下の子孫要素を列挙。`check_dialog` はクラス名・タイトル条件でダイアログの有無を確認。
