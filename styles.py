import tkinter as tk
from tkinter import ttk

# --- Цветовая палитра ---
BG_MAIN = "#F5F5F5"        
BG_SIDEBAR = "#333333"     
BG_PANEL = "#FFFFFF"       
FG_TEXT = "#222222"        
FG_MUTED = "#888888"       
FG_LIGHT = "#DDDDDD"       
ACCENT = "#555555"         
GREEN = "#27AE60"          
RED = "#C0392B"            
BORDER = "#E0E0E0"         

def create_button(parent, text, command, bg=BG_PANEL, fg=FG_TEXT, is_dark=False):
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                    font=("Segoe UI", 10, "bold"), relief="flat", bd=0, cursor="hand2",
                    padx=15, pady=6, highlightbackground=BORDER, highlightthickness=1)
    
    if is_dark:
        btn.config(bg=ACCENT, fg="#FFFFFF")
        btn.bind("<Enter>", lambda e: btn.config(bg="#444444"))
        btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT))
    else:
        btn.bind("<Enter>", lambda e: btn.config(bg="#E8E8E8"))
        btn.bind("<Leave>", lambda e: btn.config(bg=BG_PANEL))
    return btn

def setup_styles(root):
    """Глобальная настройка стилей. Передаем root, чтобы применить настройки к списку."""
    style = ttk.Style()
    style.theme_use("clam")
    
    # Настройка выпадающего списка (самого поля)
    style.configure("TCombobox", 
                    fieldbackground=BG_PANEL, 
                    background=BG_PANEL,
                    foreground=FG_TEXT, 
                    arrowcolor=FG_TEXT, 
                    bordercolor=BORDER,
                    lightcolor=BORDER, 
                    darkcolor=BORDER, 
                    padding=5)
    
    # Убираем синюю рамку при клике
    style.map('TCombobox', fieldbackground=[('readonly', BG_PANEL)],
              selectbackground=[('readonly', BG_PANEL)],
              selectforeground=[('readonly', FG_TEXT)])

    # Настройка выпадающего СПИСКА (самих элементов)
    root.option_add('*TCombobox*Listbox.background', BG_PANEL)
    root.option_add('*TCombobox*Listbox.foreground', FG_TEXT)
    root.option_add('*TCombobox*Listbox.selectBackground', "#D0D0D0") 
    root.option_add('*TCombobox*Listbox.selectForeground', FG_TEXT)
    root.option_add('*TCombobox*Listbox.font', ("Segoe UI", 10)) # Единый шрифт

    # Настройка таблицы
    style.configure("Treeview", 
                    background=BG_PANEL, 
                    foreground=FG_TEXT, 
                    rowheight=35, 
                    fieldbackground=BG_PANEL, 
                    borderwidth=0, 
                    font=("Segoe UI", 10))
    
    style.configure("Treeview.Heading", 
                    background=BG_MAIN, 
                    foreground=FG_MUTED, 
                    font=("Segoe UI", 10, "bold"), 
                    borderwidth=0, 
                    padding=5)
    
    style.map("Treeview", 
              background=[("selected", "#E0E0E0")], 
              foreground=[("selected", FG_TEXT)])