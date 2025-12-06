import os
import time
from datetime import datetime
from PIL import ImageGrab
from typing import Optional, Any

class ScreenshotManager:
    """
    スクリーンショットの撮影と保存を管理するクラス。
    デスクトップ全体または特定のUI要素のキャプチャをサポートします。
    """

    def __init__(self, output_dir: str = "reports/screenshots"):
        """
        Args:
            output_dir (str): スクリーンショット保存先ディレクトリ。デフォルトは 'reports/screenshots'
        """
        self.output_dir = output_dir
        if not os.path.isabs(self.output_dir):
            # プロジェクトルートからの相対パスとして解決することを試みる
            # (簡易的に現在の作業ディレクトリを基準とする)
            self.output_dir = os.path.abspath(self.output_dir)
        
        os.makedirs(self.output_dir, exist_ok=True)

    def capture_screen(self, filename: str = None) -> Optional[str]:
        """
        デスクトップ全体のスクリーンショットを撮影し保存します。

        Args:
            filename (str, optional): 保存ファイル名。指定がない場合はタイムスタンプから生成。

        Returns:
            Optional[str]: 保存されたファイルの絶対パス。失敗時はNone。
        """
        filepath = self._prepare_filepath(filename, prefix="screen")
        
        try:
            # PillowのImageGrabを使用して全画面キャプチャ
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            return filepath
        except Exception as e:
            # print(f"Error capturing full screen: {e}")
            # ログ基盤が整備されていればそちらに出力すべきだが、現状は標準出力か無視
            return None

    def capture_element(self, element: Any, filename: str = None) -> Optional[str]:
        """
        指定されたUI要素(pywinauto wrapper)のスクリーンショットを撮影し保存します。

        Args:
            element (Any): pywinautoのUI要素オブジェクト (wrapper)
            filename (str, optional): 保存ファイル名。

        Returns:
            Optional[str]: 保存されたファイルの絶対パス。失敗時はNone。
        """
        filepath = self._prepare_filepath(filename, prefix="element")

        try:
            # pywinautoの要素が capture_as_image() メソッドを持っていることを期待
            if hasattr(element, 'capture_as_image'):
                image = element.capture_as_image()
                image.save(filepath)
                return filepath
            else:
                # print(f"Element does not support capture_as_image: {type(element)}")
                return None
        except Exception as e:
            # print(f"Error capturing element: {e}")
            return None

    def _prepare_filepath(self, filename: str, prefix: str = "shot") -> str:
        """
        ファイル名を正規化し、保存先のフルパスを生成します。
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{prefix}_{timestamp}.png"
        
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            filename += ".png"
            
        # ファイル名に使えない文字を置換（簡易実装）
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        return os.path.join(self.output_dir, filename)
