from pywinauto import Desktop

edge = Desktop(backend="uia").window(
    class_name_re="Chrome_WidgetWin_.*",
    title_re=r".* - Microsoft\u200b Edge",
    visible_only=True
)

edge.set_focus()
edge.print_control_identifiers() 
