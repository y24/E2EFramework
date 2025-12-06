from src.pages.base_page import BasePage

class FlexibleRenamerPage(BasePage):
    def __init__(self):
        # Title usually matches "Flexible Renamer"
        super().__init__(title_re=".*Flexible Renamer.*")

    @property
    def rename_button(self):
        # "Rename(R)" button.
        # In Win32, buttons are often found by title (text) or class "Button".
        return self.window.child_window(title="リネーム(&R)", class_name="Button")

    @property
    def dialog(self):
        # The main dialog that pops up. Title is also "Flexible Renamer" usually.
        # It's better to search for a window that is NOT the main window if possible,
        # but often it's just a top-level window or a child.
        # Assuming it's a child or a separate top-level window.
        # Using app.window() again might be safer for top-level dialogs.
        return self.app.window(title="Flexible Renamer", class_name="#32770")

    @property
    def dialog_text(self):
        # The text "対象となるファイルがありません"
        # usually Static control
        return self.dialog.child_window(title="対象となるファイルがありません", class_name="Static")

    @property
    def ok_button(self):
        # OK button on the dialog
        return self.dialog.child_window(title="OK", class_name="Button")
