"""
记账窗口 - customtkinter UI
"""

import sys
import os
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.theme import *


class BookkeepingWindow:
    """记账窗口"""

    def __init__(self, parent, data_manager, refresh_callback=None):
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.current_entity_id = None
        self._id_map = {}

        self.window = ctk.CTkToplevel(parent)
        self.window.title("记账")
        self.window.geometry("750x600")
        self.window.grab_set()

        self._create_widgets()
        self._load_entities()

    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        # 顶部选择
        top_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, PAD_MD))

        ctk.CTkLabel(top_frame, text="经营主体:", font=FONT_BODY).pack(side="left", padx=(0, PAD_SM))
        self.entity_var = ctk.StringVar()
        self.entity_combo = ctk.CTkComboBox(top_frame, variable=self.entity_var, width=200,
                                              command=self._on_entity_change)
        self.entity_combo.pack(side="left", padx=(0, PAD_LG))

        ctk.CTkLabel(top_frame, text="年份:", font=FONT_BODY).pack(side="left", padx=(0, PAD_SM))
        self.year_var = ctk.StringVar(value=str(datetime.now().year))
        years = [str(y) for y in range(datetime.now().year, datetime.now().year - 3, -1)]
        ctk.CTkComboBox(top_frame, variable=self.year_var, values=years, width=80).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkLabel(top_frame, text="月份:", font=FONT_BODY).pack(side="left", padx=(0, PAD_SM))
        self.month_var = ctk.StringVar(value="全部")
        months = ["全部"] + [str(m) for m in range(1, 13)]
        ctk.CTkComboBox(top_frame, variable=self.month_var, values=months, width=70).pack(side="left")

        ctk.CTkButton(top_frame, text="刷新", width=60, height=30, corner_radius=CORNER_RADIUS,
                       command=self._refresh_list).pack(side="left", padx=PAD_MD)

        # 添加记录
        add_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        add_frame.grid(row=1, column=0, sticky="ew", pady=(0, PAD_MD))

        self.trans_date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.trans_type_var = ctk.StringVar(value="income")
        self.category_var = ctk.StringVar(value="营业收入")
        self.amount_var = ctk.StringVar()
        self.desc_var = ctk.StringVar()

        row1 = ctk.CTkFrame(add_frame, fg_color="transparent")
        row1.pack(fill="x", padx=PAD_MD, pady=PAD_MD)
        ctk.CTkLabel(row1, text="日期:", font=FONT_SMALL).pack(side="left")
        ctk.CTkEntry(row1, textvariable=self.trans_date_var, width=100, height=32, corner_radius=6).pack(side="left", padx=PAD_XS)
        ctk.CTkLabel(row1, text="类型:", font=FONT_SMALL).pack(side="left", padx=(PAD_MD, 0))
        ctk.CTkComboBox(row1, variable=self.trans_type_var, width=80, height=32,
                        values=["income", "expense"], corner_radius=6).pack(side="left", padx=PAD_XS)
        ctk.CTkLabel(row1, text="分类:", font=FONT_SMALL).pack(side="left", padx=(PAD_MD, 0))
        ctk.CTkEntry(row1, textvariable=self.category_var, width=100, height=32, corner_radius=6).pack(side="left", padx=PAD_XS)
        ctk.CTkLabel(row1, text="金额:", font=FONT_SMALL).pack(side="left", padx=(PAD_MD, 0))
        ctk.CTkEntry(row1, textvariable=self.amount_var, width=90, height=32, corner_radius=6).pack(side="left", padx=PAD_XS)
        ctk.CTkLabel(row1, text="备注:", font=FONT_SMALL).pack(side="left", padx=(PAD_MD, 0))
        ctk.CTkEntry(row1, textvariable=self.desc_var, width=100, height=32, corner_radius=6).pack(side="left", padx=PAD_XS)

        ctk.CTkButton(add_frame, text="+ 添加记录", width=100, height=32,
                       corner_radius=CORNER_RADIUS, font=FONT_SMALL,
                       fg_color=COLORS["primary"][0], command=self._add_record).pack(anchor="e", padx=PAD_MD, pady=(0, PAD_MD))

        # 记录列表
        self.list_frame = ctk.CTkScrollableFrame(main_frame, fg_color=COLORS["card"][0],
                                                  corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        self.list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, PAD_MD))
        self.list_frame.grid_columnconfigure(1, weight=1)

        # 底部汇总
        self.summary_text = ctk.CTkTextbox(main_frame, height=60, font=FONT_SMALL, corner_radius=CORNER_RADIUS)
        self.summary_text.grid(row=3, column=0, sticky="ew")

    def _load_entities(self):
        entities = self.dm.get_entities()
        if entities:
            self.entity_map = {e["name"]: e["id"] for e in entities}
            self.entity_combo.configure(values=list(self.entity_map.keys()))
            first = list(self.entity_map.keys())[0]
            self.entity_var.set(first)
            self.current_entity_id = self.entity_map[first]
            self._refresh_list()

    def _on_entity_change(self, choice):
        self.current_entity_id = self.entity_map.get(choice)
        self._refresh_list()

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self._id_map = {}
        if not self.current_entity_id:
            return

        year_str = self.year_var.get()
        month_str = self.month_var.get()
        year = int(year_str) if year_str else None
        month = int(month_str) if month_str != "全部" else None

        records = self.dm.get_transactions(self.current_entity_id, year, month)
        for idx, r in enumerate(records, start=1):
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1, padx=PAD_XS)
            row.grid_columnconfigure(2, weight=1)
            ctk.CTkLabel(row, text=str(idx), font=FONT_SMALL, width=35, text_color=COLORS["text_light"][0]).grid(row=0, column=0)
            ctk.CTkLabel(row, text=r["trans_date"], font=FONT_SMALL, width=80).grid(row=0, column=1, padx=PAD_XS)
            type_text = "收入" if r["trans_type"] == "income" else "支出"
            ctk.CTkLabel(row, text=type_text, font=FONT_SMALL, width=40).grid(row=0, column=2, padx=PAD_XS)
            ctk.CTkLabel(row, text=r["category"], font=FONT_SMALL, width=80).grid(row=0, column=3, padx=PAD_XS)
            ctk.CTkLabel(row, text="¥" + f"{r['amount']:,.2f}", font=FONT_SMALL, width=80, anchor="e").grid(row=0, column=4, padx=PAD_XS)
            self._id_map[str(idx)] = r["id"]

    def _add_record(self):
        if not self.current_entity_id:
            messagebox.showwarning("提示", "请先选择经营主体")
            return
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入合法金额")
            return

        self.dm.add_transaction(
            self.current_entity_id,
            self.trans_date_var.get(),
            self.trans_type_var.get(),
            self.category_var.get(),
            amount,
            self.desc_var.get()
        )
        self.amount_var.set("")
        self.desc_var.set("")
        self._refresh_list()
        if self.refresh_callback:
            self.refresh_callback()
