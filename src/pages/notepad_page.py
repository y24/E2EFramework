from src.pages.base_page import BasePage

class NotepadPage(BasePage):
    def __init__(self):
        # Notepad title: "Untitled - Notepad" or "無題 - メモ帳"
        # Support both English and Japanese
        super().__init__(title_re=".*(Notepad|メモ帳).*")

    @property
    def window(self):
        # Override to use Desktop scope because modern Notepad app launching behavior
        # often detaches from the initial process handle tracked by Application().
        from pywinauto import Desktop
        return Desktop(backend='uia').window(title_re=self.title_re, found_index=0)

    @property
    def editor(self):
        # Modern Notepad (Win11) often uses 'Document' control type for the main text area.
        # It might also be nested.
        # Let's try to find a child that is 'Document' or 'Edit'.
        
        # Strategy 1: Look for 'Document' (Modern)
        doc = self.window.child_window(control_type="Document")
        if doc.exists(timeout=1):
            return doc
            
        # Strategy 2: Look for 'Edit' (Classic)
        edit = self.window.child_window(control_type="Edit")
        return edit

    @property
    def menu_bar(self):
         return self.window.child_window(control_type="MenuBar")

    @property
    def file_menu(self):
        # "File" menu. In Japanese "ファイル".
        # Modern Notepad might put this in a different place or style, but standard UIA often finds it by name.
        # Try finding by title "File" or "ファイル"
        return self.window.child_window(title_re=".*(File|ファイル).*", control_type="MenuItem")

    @property
    def exit_menu_item(self):
        # "Exit" menu item. In Japanese "終了".
        # This usually appears after clicking "File".
        # It is often a child of the Menu or the Window (depending on UIA tree structure after expansion).
        # We can try to find it under the window (assuming it pops up as a context menu or similar)
        return self.window.child_window(title_re=".*(Exit|終了).*", control_type="MenuItem")
