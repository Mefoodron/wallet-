import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from PIL import Image, ImageTk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database as db
from styles import *

CATEGORIES_EXPENSE = ["Еда", "Транспорт", "Жильё", "Развлечения", "Здоровье", "Одежда", "Связь", "Прочее"]
CATEGORIES_INCOME = ["Зарплата", "Фриланс", "Инвестиции", "Подарки", "Прочее"]

def format_money(val):
    if val == int(val):
        return f"{int(val):,}".replace(",", " ") + " ₽"
    else:
        return f"{val:,.2f}".replace(",", " ") + " ₽"

class WalletApp(tk.Tk):
    def __init__(self, data_file, base_path):
        super().__init__()
        self.data_file = data_file
        self.base_path = base_path
        
        self.title("Wallet")
        self.geometry("1300x800") 
        self.configure(bg=BG_MAIN)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        try:
            icon_path = os.path.join(self.base_path, "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self.expenses = []
        self.period = tk.StringVar(value="all")
        self.tx_type = tk.StringVar(value="expense")
        
        self.selected_category = tk.StringVar(value=CATEGORIES_EXPENSE[0])

        setup_styles(self)

        self._build_ui()
        self._load_and_refresh()
        
        self.bind('<Return>', lambda event: self.add_expense())

    def _build_ui(self):
        # 1. БОКОВАЯ ПАНЕЛЬ
        sidebar = tk.Frame(self, bg=BG_SIDEBAR, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Wallet", bg=BG_SIDEBAR, fg="#FFFFFF", 
                 font=("Segoe UI", 20, "bold")).pack(pady=(40, 10), padx=20, anchor="w")
                 
        tk.Label(sidebar, text="Управление финансами", bg=BG_SIDEBAR, fg=FG_LIGHT, 
                 font=("Segoe UI", 10)).pack(pady=(0, 40), padx=20, anchor="w")

        info_frame = tk.Frame(sidebar, bg="#404040", padx=15, pady=15)
        info_frame.pack(fill="x", padx=20)
        tk.Label(info_frame, text="Совет дня", bg="#404040", fg="#FFFFFF", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(info_frame, text="Записывайте расходы сразу\nпосле покупки. Так вы\nне забудете важные детали.", 
                 bg="#404040", fg=FG_LIGHT, font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=(5, 0))

        # 2. ГЛАВНАЯ ОБЛАСТЬ
        main_area = tk.Frame(self, bg=BG_MAIN)
        main_area.pack(side="right", fill="both", expand=True, padx=25, pady=25)

        # --- ВЕРХНИЕ КАРТОЧКИ ---
        cards_frame = tk.Frame(main_area, bg=BG_MAIN)
        cards_frame.pack(fill="x", pady=(0, 25))

        def create_card(parent, title, value, color):
            card = tk.Frame(parent, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=(0, 20))
            tk.Label(card, text=title, bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(15, 0))
            lbl = tk.Label(card, text=value, bg=BG_PANEL, fg=color, font=("Segoe UI", 16, "bold"))
            lbl.pack(anchor="w", padx=20, pady=(0, 15))
            return lbl

        self.card_balance = create_card(cards_frame, "Текущий баланс", "0 ₽", FG_TEXT)
        self.card_income = create_card(cards_frame, "Доходы", "0 ₽", GREEN)
        self.card_expense = create_card(cards_frame, "Расходы", "0 ₽", RED)
        self.card_forecast = create_card(cards_frame, "Прогноз (месяц)", "0 ₽", ACCENT)

        # --- ПАНЕЛЬ ДОБАВЛЕНИЯ ---
        form_frame = tk.Frame(main_area, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
        form_frame.pack(fill="x", pady=(0, 25))
        
        inner_form = tk.Frame(form_frame, bg=BG_PANEL)
        inner_form.pack(fill="x", padx=25, pady=20)

        inner_form.columnconfigure(0, weight=0)
        inner_form.columnconfigure(1, weight=0)
        inner_form.columnconfigure(2, weight=0)
        inner_form.columnconfigure(3, weight=1) # Комментарий растягивается
        inner_form.columnconfigure(4, weight=0)
        inner_form.columnconfigure(5, weight=0)

        # --- РЯД 1: ПОДПИСИ ---
        tk.Label(inner_form, text="Дата", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(10, 15), pady=(0, 5))
        tk.Label(inner_form, text="Категория", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w", padx=(10, 15), pady=(0, 5))
        tk.Label(inner_form, text="Сумма", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(10, 15), pady=(0, 5))
        tk.Label(inner_form, text="Комментарий", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9)).grid(row=0, column=3, sticky="w", padx=(10, 15), pady=(0, 5))

        # --- РЯД 2: ПОЛЯ ВВОДА (с правильным отступом) ---
        
        # 1. Дата
        self.date_frame = tk.Frame(inner_form, bg=BG_MAIN, highlightbackground=BORDER, highlightthickness=1)
        self.date_frame.grid(row=1, column=0, padx=(10, 15), sticky="nsew")
        self.entry_date = tk.Entry(self.date_frame, width=12, font=("Segoe UI", 10), bg=BG_MAIN, relief="flat", highlightthickness=0, bd=0)
        self.entry_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.entry_date.pack(fill="both", expand=True, padx=8, pady=7)

        # 2. Категория (кастомный список)
        self.cat_frame = tk.Frame(inner_form, bg=BG_MAIN, highlightbackground=BORDER, highlightthickness=1, cursor="hand2")
        self.cat_frame.grid(row=1, column=1, padx=(10, 15), sticky="nsew")
        
        self.cat_lbl = tk.Label(self.cat_frame, textvariable=self.selected_category, bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 10), anchor="w", padx=8, pady=7)
        self.cat_lbl.pack(side="left", fill="both", expand=True)
        
        self.arrow_canvas = tk.Canvas(self.cat_frame, width=12, height=12, bg=BG_MAIN, highlightthickness=0, cursor="hand2")
        self.arrow_canvas.pack(side="right", padx=10)
        self.arrow_canvas.create_line(2, 4, 6, 8, 10, 4, fill=FG_MUTED, width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)

        self.cat_frame.bind("<Button-1>", self.show_category_menu)
        self.cat_lbl.bind("<Button-1>", self.show_category_menu)
        self.arrow_canvas.bind("<Button-1>", self.show_category_menu)

        # 3. Сумма
        self.amount_frame = tk.Frame(inner_form, bg=BG_MAIN, highlightbackground=BORDER, highlightthickness=1)
        self.amount_frame.grid(row=1, column=2, padx=(10, 15), sticky="nsew")
        self.entry_amount = tk.Entry(self.amount_frame, width=12, font=("Segoe UI", 10), bg=BG_MAIN, relief="flat", highlightthickness=0, bd=0)
        self.entry_amount.pack(fill="both", expand=True, padx=8, pady=7)

        # 4. Комментарий
        self.comment_frame = tk.Frame(inner_form, bg=BG_MAIN, highlightbackground=BORDER, highlightthickness=1)
        self.comment_frame.grid(row=1, column=3, sticky="ew", padx=(10, 20))
        self.entry_comment = tk.Entry(self.comment_frame, font=("Segoe UI", 10), bg=BG_MAIN, relief="flat", highlightthickness=0, bd=0)
        self.entry_comment.pack(fill="both", expand=True, padx=8, pady=7)

        # 5. Переключатель (Расход/Доход)
        type_frame = tk.Frame(inner_form, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
        type_frame.grid(row=1, column=4, padx=(10, 20), sticky="nsew")
        
        self.lbl_type_expense = tk.Label(type_frame, text="Расход", bg=RED, fg="#FFFFFF", font=("Segoe UI", 10, "bold"), padx=20, pady=7, cursor="hand2")
        self.lbl_type_expense.pack(side="left", fill="y")
        
        self.lbl_type_income = tk.Label(type_frame, text="Доход", bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 10, "bold"), padx=20, pady=7, cursor="hand2")
        self.lbl_type_income.pack(side="left", fill="y")
        
        self.lbl_type_expense.bind("<Button-1>", lambda e: self.set_type("expense"))
        self.lbl_type_income.bind("<Button-1>", lambda e: self.set_type("income"))
        self.set_type("expense")

        # 6. Кнопка Добавить
        btn_add = tk.Button(inner_form, text="Добавить", command=self.add_expense, 
                            bg=ACCENT, fg="#FFFFFF", font=("Segoe UI", 10, "bold"), 
                            relief="flat", bd=0, cursor="hand2", padx=30, pady=7,
                            highlightbackground=BORDER, highlightthickness=1)
        btn_add.bind("<Enter>", lambda e: btn_add.config(bg="#444444"))
        btn_add.bind("<Leave>", lambda e: btn_add.config(bg=ACCENT))
        btn_add.grid(row=1, column=5, padx=(10, 0), sticky="nsew")

        # --- РАБОЧАЯ ОБЛАСТЬ ---
        workspace = tk.Frame(main_area, bg=BG_MAIN)
        workspace.pack(fill="both", expand=True)

        left_panel = tk.Frame(workspace, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 25))

        top_bar = tk.Frame(left_panel, bg=BG_PANEL)
        top_bar.pack(fill="x", padx=20, pady=20)

        self.segment_frame = tk.Frame(top_bar, bg=BG_MAIN, highlightbackground=BORDER, highlightthickness=1)
        self.segment_frame.pack(side="left")
        self.btn_period_all = tk.Label(self.segment_frame, text="Всё время", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 9, "bold"), padx=15, pady=6, cursor="hand2")
        self.btn_period_all.pack(side="left")
        self.btn_period_month = tk.Label(self.segment_frame, text="Текущий месяц", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 9, "bold"), padx=15, pady=6, cursor="hand2")
        self.btn_period_month.pack(side="left")
        self.btn_period_all.bind("<Button-1>", lambda e: self.set_period("all"))
        self.btn_period_month.bind("<Button-1>", lambda e: self.set_period("month"))
        self.update_segment_ui()

        actions_frame = tk.Frame(top_bar, bg=BG_PANEL)
        actions_frame.pack(side="right")
        btn_del = create_button(actions_frame, "Удалить", self.delete_selected, fg=FG_TEXT)
        btn_del.pack(side="left", padx=8)
        btn_save = create_button(actions_frame, "Сохранить", self.save, fg=FG_TEXT)
        btn_save.pack(side="left", padx=8)

        self.tree = ttk.Treeview(left_panel, columns=("date", "type", "category", "amount", "comment"), show="headings")
        for c, title, w in [("date", "Дата", 90), ("type", "Тип", 80), ("category", "Категория", 120), ("amount", "Сумма", 100), ("comment", "Комментарий", 200)]:
            self.tree.heading(c, text=title, anchor="w")
            self.tree.column(c, width=w, anchor="w")
        
        self.tree.tag_configure('income', foreground=GREEN)
        self.tree.tag_configure('expense', foreground=RED)
        self.tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        right_panel = tk.Frame(workspace, width=350, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        tk.Label(right_panel, text="Структура расходов", bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 12, "bold")).pack(pady=(20, 0))
        
        chart_frame = tk.Frame(right_panel, bg=BG_PANEL)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(3.5, 3.0), dpi=100)
        self.fig.patch.set_facecolor(BG_PANEL)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_category_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg=BG_PANEL, fg=FG_TEXT, 
                       activebackground="#D0D0D0", activeforeground=FG_TEXT, 
                       font=("Segoe UI", 10), bd=1, relief="solid")
        
        current_list = CATEGORIES_INCOME if self.tx_type.get() == "income" else CATEGORIES_EXPENSE
        
        for cat in current_list:
            menu.add_command(label=cat, command=lambda c=cat: self.selected_category.set(c))
            
        x = self.cat_frame.winfo_rootx()
        y = self.cat_frame.winfo_rooty() + self.cat_frame.winfo_height()
        menu.tk_popup(x, y)

    def set_type(self, tx_type):
        self.tx_type.set(tx_type)
        if tx_type == "expense":
            self.lbl_type_expense.config(bg=RED, fg="#FFFFFF")
            self.lbl_type_income.config(bg=BG_PANEL, fg=FG_TEXT)
            self.selected_category.set(CATEGORIES_EXPENSE[0])
        else:
            self.lbl_type_expense.config(bg=BG_PANEL, fg=FG_TEXT)
            self.lbl_type_income.config(bg=GREEN, fg="#FFFFFF")
            self.selected_category.set(CATEGORIES_INCOME[0])

    def set_period(self, value):
        self.period.set(value)
        self.update_segment_ui()
        self.refresh()

    def update_segment_ui(self):
        if self.period.get() == "all":
            self.btn_period_all.config(bg=ACCENT, fg="#FFFFFF")
            self.btn_period_month.config(bg=BG_MAIN, fg=FG_TEXT)
        else:
            self.btn_period_all.config(bg=BG_MAIN, fg=FG_TEXT)
            self.btn_period_month.config(bg=ACCENT, fg="#FFFFFF")

    def add_expense(self):
        date_str = self.entry_date.get().strip()
        cat = self.selected_category.get()
        amount_str = self.entry_amount.get().strip()
        comment = self.entry_comment.get().strip()
        tx_type = self.tx_type.get()

        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД")
            return
        try:
            amount = float(amount_str.replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть числом")
            return
        if amount <= 0:
            messagebox.showerror("Ошибка", "Сумма должна быть больше нуля")
            return

        self.expenses.append({"date": d, "type": tx_type, "category": cat, "amount": amount, "comment": comment})
        self.entry_amount.delete(0, tk.END)
        self.entry_comment.delete(0, tk.END)
        self.entry_amount.focus_set() 
        self.refresh()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel: return
        visible = db.filter_by_period(self.expenses, self.period.get())
        for item in sel:
            idx = self.tree.index(item)
            target = visible[idx]
            if target in self.expenses:
                self.expenses.remove(target)
        self.refresh()

    def save(self):
        try:
            db.save_expenses(self.expenses, self.data_file)
            messagebox.showinfo("Успех", "Данные сохранены!")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _load_and_refresh(self):
        try:
            self.expenses = db.load_expenses(self.data_file)
        except Exception as e:
            messagebox.showwarning("Ошибка", f"Не удалось загрузить данные: {e}")
            self.expenses = []
        self.refresh()

    def refresh(self):
        visible = db.filter_by_period(self.expenses, self.period.get())
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for e in sorted(visible, key=lambda x: x["date"], reverse=True):
            t_str = "Доход" if e["type"] == "income" else "Расход"
            tag = 'income' if e["type"] == "income" else 'expense'
            sign = "+" if e["type"] == "income" else "-"
            
            self.tree.insert("", "end", values=(
                e["date"].strftime("%d.%m.%Y"), 
                t_str, 
                e["category"], 
                f"{sign}{format_money(e['amount'])}", 
                e["comment"]
            ), tags=(tag,))

        stats = db.compute_stats(visible)
        
        balance_color = RED if stats['balance'] < 0 else FG_TEXT
        self.card_balance.config(text=format_money(stats['balance']), fg=balance_color)
        
        self.card_income.config(text=format_money(stats['income']))
        self.card_expense.config(text=format_money(stats['expense']))
        self.card_forecast.config(text=format_money(stats['forecast']))

        self.ax.clear()
        self.ax.set_facecolor(BG_PANEL)
        if stats["by_category"]:
            cats = list(stats["by_category"].keys())
            vals = list(stats["by_category"].values())
            colors = ['#95A5A6', '#7F8C8D', '#BDC3C7', '#D5DBDB', '#ABB2B9', '#566573', '#808B96', '#AAB7B8']
            
            wedges, texts, autotexts = self.ax.pie(
                vals, labels=cats, colors=colors[:len(cats)], autopct="%1.0f%%", 
                textprops={"fontsize": 9, "color": FG_TEXT},
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')
        else:
            self.ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", color=FG_MUTED)
            self.ax.set_axis_off()
        self.canvas.draw()

    def quit_app(self):
        self.destroy()
        sys.exit(0)