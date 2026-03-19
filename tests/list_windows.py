
import pygetwindow as gw
import win32gui

def list_all_windows():
    print("--- Listing All Visible Windows ---")
    windows = gw.getAllWindows()
    for w in windows:
        if w.title:
            try:
                class_name = win32gui.GetClassName(w._hWnd)
                print(f"Title: {w.title} | Class: {class_name} | HWND: {w._hWnd}")
            except:
                print(f"Title: {w.title} | HWND: {w._hWnd}")

if __name__ == "__main__":
    list_all_windows()
