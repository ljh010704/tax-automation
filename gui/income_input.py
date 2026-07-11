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

        # 响应式字体
        self.fonts = ResponsiveFont(self.window)
        # fonts initialized

        self._create_widgets()
        self._load_entities()

    def _create_widgets(self):
        """创建界面"""
        self.window.grid_columnconfigure(1, weight=1)

        form_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        form_frame.grid(row=0, column=0, padx=PAD_LG, pady=PAD_LG, sticky="nsew")
        form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="选择主体:", font=self.fonts.get("body")).grid(row=0, column=0, padx=PAD_SM, pady=PAD_MD, sticky="w")
        self.entity_combo = ctk.CTkComboBox(form_frame, font=self.fonts.get("body"), state="readonly")
        self.entity_combo.grid(row=0, column=1, padx=PAD_SM, pady=PAD_MD, sticky="ew")

        ctk.CTkLabel(form_frame, text="收入金额:", font=self.fonts.get("body")).grid(row=1, column=0, padx=PAD_SM, pady=PAD_MD, sticky="w")
        self.amount_entry = ctk.CTkEntry(form_frame, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.amount_entry.grid(row=1, column=1, padx=PAD_SM, pady=PAD_MD, sticky="ew")

        ctk.CTkLabel(form_frame, text="日期:", font=self.fonts.get("body")).grid(row=2, column=0, padx=PAD_SM, pady=PAD_MD, sticky="w")
        self.date_entry = ctk.CTkEntry(form_frame, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=2, column=1, padx=PAD_SM, pady=PAD_MD, sticky="ew")

        ctk.CTkLabel(form_frame, text="备注:", font=self.fonts.get("body")).grid(row=3, column=0, padx=PAD_SM, pady=PAD_MD, sticky="w")
        self.note_entry = ctk.CTkEntry(form_frame, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.note_entry.grid(row=3, column=1, padx=PAD_SM, pady=PAD_MD, sticky="ew")

        ctk.CTkButton(form_frame, text="录入", font=self.fonts.get("button"),
                      fg_color=COLORS["success"][0], hover_color=COLORS["success_hover"][0],
                      command=self._submit).grid(row=4, column=0, columnspan=2, pady=PAD_XL)

    def _load_entities(self):
        """加载主体"""
        entities = self.dm.get_entities()
        if not entities:
            return
        names = [e.get("entity_name", "") for e in entities]
        self.entity_combo.configure(values=names)
        if names:
            self.entity_combo.set(names[0])

    def _submit(self):
        """提交"""
        name = self.entity_combo.get()
        entities = self.dm.get_entities()
        entity_id = None
        for e in entities:
            if e.get("entity_name") == name:
                entity_id = e["id"]
                break
        if not entity_id:
            messagebox.showwarning("提示", "请先添加经营主体")
            return
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入有效金额")
            return
        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("提示", "日期格式应为 YYYY-MM-DD")
            return

        self.dm.add_transaction(entity_id, {
            "trans_type": "income",
            "amount": amount,
            "date": date_str,
            "note": self.note_entry.get().strip(),
        })
        messagebox.showinfo("成功", "收入录入成功")
        if self.refresh_callback:
            self.refresh_callback()
        self.window.destroy()
