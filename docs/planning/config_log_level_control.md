# config.ini ログレベル制御設計

## 背景
- 現在のログレベルは pytest.ini の log_cli_level=INFO と conftest.py の FileHandler(DEBUG) に固定で、環境や実行者が変更できない。
- 実行環境によって詳細ログ(デバッグ用途)を出したい/抑制したいニーズ。
- config/config.ini を唯一の実行時設定ポイントとして集約したい。

## 目標
- config/config.ini からログレベルを指定し、ランログファイルとコンソール出力の双方に反映できる。
- 環境(--env)ごとに指定が可能で、未指定時は既定値（INFO）で従来挙動を維持。
- 無効値が指定された場合は安全な既定値へフォールバックし、警告ログに残す。

## 現状整理
- ログ初期化は tests/conftest.py の session fixture で実施。reports/<run>/run_<run>.log に FileHandler(DEBUG) を追加、root logger レベルは未指定（デフォルト WARNING）。
- pytest.ini が log_cli=true / log_cli_level=INFO を持つため、コンソールは INFO 固定。
- config/config.ini にはログ関連キーがなく、Context.load_config は DEFAULT と --env セクションのみを variables に展開。

## 仕様案
- config/config.ini に [LOGGING] セクションを追加。
  - Level: root logger の基準レベル。省略時は INFO。
  - FileLevel: run ログファイルのハンドラーレベル。省略時は Level を使用。
  - ConsoleLevel: コンソール出力（pytest log_cli ハンドラー）用レベル。省略時は Level を使用。
  - 値は DEBUG/INFO/WARNING/ERROR/CRITICAL（大文字小文字問わず）か数値(10/20/...)を許容。
- 環境別上書き:
  - LOGGING.<ENV> セクション（例: [LOGGING.STAGING]）を認識し、[LOGGING] をベースに該当 env のキーで上書き。
  - 上書き対象キーが無ければ [LOGGING] または既定値を利用。
- 無効値は WARNING を残して既定値にフォールバック。設定が無い場合も既定値。

### 設定例
`ini
[LOGGING]
Level = INFO
FileLevel = DEBUG
ConsoleLevel = WARNING

[LOGGING.STAGING]
Level = DEBUG        ; ステージングのみ詳細
ConsoleLevel = INFO  ; コンソールは冗長すぎないよう抑制
`

## 実装方針
- 新規 src/utils/logging_config.py を追加し、設定読み込みとレベル解決を担当。
  - esolve_level(value, default) -> int で文字列/数値を logging レベルに変換し、無効時は default を返しつつ logging.warning を出す。
  - load_from_context(context, env) で [LOGGING] + [LOGGING.<ENV>] をマージし、{"root": lvl, "file": lvl, "console": lvl} を返す。
- 	ests/conftest.py
  - Context.load_config 後に logging_config.load_from_context(context, env) を呼び、レベルを決定。
  - root logger に setLevel(root_level) を設定（最小レベルでフィルタリング）。ファイルハンドラー生成時に setLevel(file_level) を適用。
  - pytest のコンソール出力も設定値に合わせるため、config.option.log_cli_level を ConsoleLevel に書き換え（文字列表現へ）。
  - フレームワークが追加した FileHandler を識別する属性を付け、再実行時の重複追加を防止。
  - 決定したレベルを Context.variables に LOGGING.LEVEL / LOGGING.FILELEVEL / LOGGING.CONSOLELEVEL として格納し、他モジュールが参照できるようにする。
- 既存コードへの影響は conftest.py 以外には発生しない想定。ランログパスやフォーマットは変更しない。

## 移行・後方互換
- config.ini に [LOGGING] を追加しない場合は INFO 相当で動作し、現行と同等の出力量を維持。
- pytest.ini の log_cli_level より config.ini が優先される（実行時に上書き）。既存 pytest.ini はそのまま残す。
- 既存シナリオやアクションコードは変更不要。

## テスト観点
- [LOGGING] Level=ERROR 指定時に run ログ/コンソールへ ERROR 以上のみ出ること。
- FileLevel=DEBUG, ConsoleLevel=INFO でファイルに DEBUG が残りつつコンソールには出ないこと。
- env=STAGING 実行時に [LOGGING.STAGING] が反映され、DEFAULT 実行時は [LOGGING] のみ使われること。
- 無効なレベル文字列（例: TRACE）が指定された場合に WARNING をログへ出し、既定値で動作すること。
- 複数セッション連続実行で FileHandler が二重に追加されないこと（ログ重複しないこと）。
