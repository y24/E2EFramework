# Excelページオブジェクト化（excel_automation_helper 廃止）設計案

## 現状
- Excel 操作は `ExcelAutomationHelper` が pywinauto の操作や DriverFactory 連携、復旧ファイル削除を一手に持つ。
- `ExcelPage` は helper の薄いラッパーで、ページオブジェクトの枠組み（BasePage 相当の責務分担）と乖離。
- `ExcelAction` は helper 前提で実装され、他のアクションのようなターゲット解決やページメソッド呼び出しの統一感がない。
- helper がアプリ/ウィンドウ状態をキャッシュしており、DriverFactory と二重管理になっている。

## 目標
- Excel も他ページ同様に「ページオブジェクト上のメソッド」を直接呼ぶ構造に統一し、helper への依存を排除する。
- シナリオ/アクション側のインターフェース（`params.action` や引数キー）は後方互換を維持。
- ウィンドウ活性化や復旧ファイル削除などの共通処理は ExcelPage 内部の責務として集約し、状態管理を DriverFactory に寄せる。

## 改修方針
1. **ExcelPage の責務拡張**  
   - DriverFactory 経由でアプリ/ウィンドウを取得し、ウィンドウ活性化・存在確認・復旧ファイル削除を内部で完結させる。  
   - send_keys ベースの操作（セル選択、テキスト入力、リボンショートカット、保存、終了など）を ExcelPage の公開メソッドとして提供。
   - helper で保持していた一時状態（`copied_files` やキャッシュ）は ExcelPage のクラス変数/インスタンス変数に移行し、必要最低限にする。

2. **公開 API の整理（ExcelPage）**  
   - `start(file_path=None)`：DriverFactory.start_excel を呼び出し、ウィンドウ取得と初期化を実施。  
   - `activate_window(max_retries=3, retry_delay=1.0)` / `_ensure_active(operation_name)`：操作前にフォーカスを取る。  
   - `select_cell(row=None, column=None, cell_address=None)`：ExcelConfig からアドレス生成。  
   - `input_text(text)`、`execute_ribbon_shortcut(shortcut_key)`、`save(file_path=None)`、`close_workbook(save=False)`、`quit()`、`handle_dialog(title_patterns, key_action='{ESC}', timeout=10)`。  
   - `_cleanup_recovery_files()`：復旧ファイル削除ロジックを private として保持。  
   - `reset()`：DriverFactory.close_excel とキャッシュクリア。

3. **ExcelAction の呼び出し置き換え**  
   - helper 取得を廃止し、ExcelPage インスタンスのメソッドへ直接ディスパッチ。  
   - params のキー/意味は現行を踏襲し、戻り値や例外メッセージのみ整形。  
   - アプリ終了後の `reset()` 呼び出しは ExcelPage 側の新 API を利用。

4. **構成整理**  
   - `src/utils/excel_automation_helper.py` を削除し、必要ロジックを ExcelPage に移植。  
   - `ExcelConfig` は現行のまま活用（タイミング・ショートカット・セル計算の入口として利用）。  
   - ドキュメント/サンプルシナリオは action 名とパラメータが変わらないため更新不要だが、実装方針の差分を README か planning ノートに記載する。

## 実装ステップ案
1. ExcelPage をリライト：DriverFactory 依存を直接持ち、各操作メソッドと活性化/クリーンアップの内部ヘルパーを実装。  
2. ExcelAction を ExcelPage メソッド呼び出しに差し替え（例：`page.select_cell(...)`）。  
3. helper 削除に伴う import の掃除と、不要メンバーの除去。  
4. 例外メッセージ/ログの統一（他アクションと同程度の表現に合わせる）。  
5. 影響範囲の軽いテスト（ユニットレベルは pywinauto をモックし、シナリオ実行系は手動または CI スキップでの smoke を検討）。

## 影響範囲と後方互換
- シナリオ定義（params.action や引数名）は不変。内部実装のみ変更。  
- DriverFactory の Excel ライフサイクル API は既存を利用するため、他利用箇所（あれば）への影響は限定的。  
- ExcelPage をインポートして helper を期待する内部呼び出しは存在しない前提だが、念のため `ExcelPage.helper` を削除する際はリポジトリ全体の参照を確認。

## テスト観点
- 単体：ExcelPage メソッドが DriverFactory/send_keys を正しく呼ぶかをモックで確認（開始/活性化/セル選択/保存/終了）。  
- 例外系：ウィンドウ非取得時の挙動、無効セル指定時の ValueError、ダイアログ未検出時の戻り値。  
- シナリオサンプル：`SAMPLE-004_excel.json` を使った手動 E2E 確認（Excel 実機起動が必要なため自動化はオプション）。

## リスク・検討事項
- send_keys に依存するためフォーカスロスに弱い。活性化ロジックのリトライ値は `ExcelConfig.TIMING` を活用し、必要なら可変にする。  
- helper 削除後に共通化しづらいロジック（復旧ファイル削除など）が単一クラスにまとまるため、将来の再利用が必要なら Utility 切り出しを再検討。  
- DriverFactory と ExcelPage のキャッシュ整合性を壊さないよう、リセット時に双方の参照を必ずクリアする。
