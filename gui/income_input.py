"""
快速收入录入窗口 - customtkinter UI
"""

import sys
import os
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.theme import *


class IncomeInputWindow:
    """快速收入录入窗口"""

    def __init__(self, parent, data_manager, refresh_callback=None):
        self.dm = data_manager
        self.refresh_callback = refresh_callback

        self.window = ctk.CTkToplevel(parent)
        self.window.title("快速收入录入")
        self.window.geometry("480x380")
        self.window.grab_set()

        self._create_widgets()
        self._load_entities()

    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        # 选择主体
        sel_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        sel_frame.pack(fill="x", pady=(0, PAD_LG))

        ctk.CTkLabel(sel_frame, text="经营主体:", font=FONT_BODY).pack(side="left")
        self.entity_var = ctk.StringVar()
        self.entity_combo = ctk.CTkComboBox(sel_frame, variable=self.entity_var, width=220,
                                              command=self._on_entity_change)
        self.entity_combo.pack(side="left", padx=PAD_MD)

        ctk.CTkLabel(sel_frame, text="年份:", font=FONT_BODY).pack(side="left")
        self.year_var = ctk.StringVar(value=str(datetime.now().year))
        years = [str(y) for y in range(datetime.now().year, datetime.now().year - 3, -1)]
        ctk.CTkComboBox(sel_frame, variable=self.year_var, values=years, width=70).pack(side="left", padx=PAD_SM)

        ctk.CTkLabel(sel_frame, text="季度:", font=FONT_BODY).pack(side="left", padx=(PAD_SM, 0))
        self.quarter_var = ctk.StringVar(value=str((datetime.now().month - 1) // 3 + 1))
        ctk.CTkComboBox(sel_frame, variable=self.quarter_var, values=["1", "2", "3", "4"], width=50).pack(side="left", padx=PAD_SM)

        # 输入区
        input_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        input_frame.pack(fill="x", pady=(0, PAD_LG))

        pad = {"padx": PAD_MD, "pady": PAD_MD}
        ctk.CTkLabel(input_frame, text="季度收入（元）", font=FONT_BODY).grid(row=0, column=0, sticky="w", **pad)
        self.income_var = ctk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.income_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=0, column=1, **pad)

        ctk.CTkLabel(input_frame, text="季度费用（元）", font=FONT_BODY).grid(row=1, column=0, sticky="w", **pad)
        self.expenses_var = ctk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.expenses_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=1, column=1, **pad)

        ctk.CTkLabel(input_frame, text="备注", font=FONT_BODY).grid(row=2, column=0, sticky="w", **pad)
        self.notes_var = ctk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.notes_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=2, column=1, **pad)

        # 税额预览
        self.preview_label = ctk.CTkLabel(main_frame, text="", font=FONT_BODY, text_color=COLORS["success"][0])
        self.preview_label.pack(pady=PAD_MD)

        # 按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(btn_frame, text="保存", width=100, height=BUTTON_HEIGHT,
                       font=FONT_BUTTON, corner_radius=CORNER_RADIUS,
                       fg_color=COLORS["success"][0], command=self._save).pack(side="left", padx=PAD_SM)
        ctk.CTkButton(btn_frame, text="加载已有数据", width=120, height=BUTTON_HEIGHT,
                       font=FONT_BODY, corner_radius=CORNER_RADIUS,
                       command=self._load_existing).pack(side="left", padx=PAD_SM)

    def _load_entities(self):
        entities = self.dm.get_entities()
        if entities:
            self.entity_map = {e["name"]: e["id"] for e in entities}
            self.entity_combo.configure(values=list(self.entity_map.keys()))
            first = list(self.entity_map.keys())[0]
            self.entity_var.set(first)
            self.current_entity_id = self.entity_map[first]

    def _on_entity_change(self, choice):
        self.current_entity_id = self.entity_map.get(choice)

    def _load_existing(self):
        if not self.current_entity_id:
            return
        record = self.dm.get_income(self.current_entity_id, int(self.year_var.get()), int(self.quarter_var.get()))
        if record:
            self.income_var.set(str(record.get("income", "")))
            self.expenses_var.set(str(record.get("expenses", "")))
            self.notes_var.set(record.get("notes", ""))

    def _save(self):
        if not self.current_entity_id:
            messagebox.showwarning("提示", "请先选择经营主体")
            return
        try:
            income = float(self.income_var.get() or 0)
            expenses = float(self.expenses_var.get() or 0)
        except ValueError:
            messagebox.showwarning("提示", "请输入合法数字")
            return

        self.dm.save_income(self.current_entity_id, int(self.year_var.get()), int(self.quarter_var.get()),
                            income, expenses, self.notes_var.get())
        if self.refresh_callback:
            self.refresh_callback()
        messagebox.showinfo("提示", "已保存")
        self.window.destroy()
