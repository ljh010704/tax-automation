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

        # 响应式字体
        self.fonts = ResponsiveFont(self.window)
        self.fonts.bind_resize()

        self._create_widgets()
        self._load_entities()

    def _create_widgets(self):
        """创建界面"""
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(2, weight=1)

        # 顶部选择主体
        top_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        top_frame.grid(row=0, column=0, columnspan=2, padx=PAD_LG, pady=PAD_MD, sticky="ew")
        ctk.CTkLabel(top_frame, text="选择主体:", font=self.fonts.get("body")).pack(side="left", padx=PAD_SM)
        self.entity_combo = ctk.CTkComboBox(top_frame, font=self.fonts.get("body"), state="readonly",
                                             command=self._on_entity_selected)
        self.entity_combo.pack(side="left", padx=PAD_SM)

        # 录入表单
        form_frame = ctk.CTkFrame(self.window, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS,
                                   border_width=1, border_color=COLORS["border"][0])
        form_frame.grid(row=1, column=0, columnspan=2, padx=PAD_LG, pady=PAD_MD, sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="类型:", font=self.fonts.get("body")).grid(row=0, column=0, padx=PAD_MD, pady=PAD_SM, sticky="w")
        self.type_combo = ctk.CTkComboBox(form_frame, values=["收入", "支出"], font=self.fonts.get("body"), state="readonly")
        self.type_combo.grid(row=0, column=1, padx=PAD_MD, pady=PAD_SM, sticky="ew")
        self.type_combo.set("收入")

        ctk.CTkLabel(form_frame, text="金额:", font=self.fonts.get("body")).grid(row=1, column=0, padx=PAD_MD, pady=PAD_SM, sticky="w")
        self.amount_entry = ctk.CTkEntry(form_frame, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.amount_entry.grid(row=1, column=1, padx=PAD_MD, pady=PAD_SM, sticky="ew")

        ctk.CTkLabel(form_frame, text="日期:", font=self.fonts.get("body")).grid(row=2, column=0, padx=PAD_MD, pady=PAD_SM, sticky="w")
        self.date_entry = ctk.CTkEntry(form_frame, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=2, column=1, padx=PAD_MD, pady=PAD_SM, sticky="ew")

        ctk.CTkLabel(form_frame, text="备注:", font=self.fonts.get("body")).grid(row=3, column=0, padx=PAD_MD, pady=PAD_SM, sticky="w")
        self.note_entry = ctk.CTkEntry(form_frame, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.note_entry.grid(row=3, column=1, padx=PAD_MD, pady=PAD_SM, sticky="ew")

        ctk.CTkButton(form_frame, text="添加记录", font=self.fonts.get("button"),
                      fg_color=COLORS["success"][0], hover_color=COLORS["success_hover"][0],
                      command=self._add_record).grid(row=4, column=0, columnspan=2, pady=PAD_MD)

        # 记录列表
        self.list_frame = ctk.CTkScrollableFrame(self.window, fg_color=COLORS["bg"][0])
        self.list_frame.grid(row=2, column=0, columnspan=2, padx=PAD_LG, pady=(0, PAD_MD), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

    def _load_entities(self):
        """加载主体到下拉框"""
        entities = self.dm.get_entities()
        if not entities:
            return
        names = [e.get("entity_name", "") for e in entities]
        self.entity_combo.configure(values=names)
        if names:
            self.entity_combo.set(names[0])
            self.current_entity_id = entities[0]["id"]

    def _on_entity_selected(self, name):
        """选中主体"""
        entities = self.dm.get_entities()
        for e in entities:
            if e.get("entity_name") == name:
                self.current_entity_id = e["id"]
                break
        self._refresh_records()

    def _add_record(self):
        """添加记录"""
        if not self.current_entity_id:
            messagebox.showwarning("提示", "请先选择经营主体")
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

        trans_type = "income" if self.type_combo.get() == "收入" else "expense"
        self.dm.add_transaction(self.current_entity_id, {
            "trans_type": trans_type,
            "amount": amount,
            "date": date_str,
            "note": self.note_entry.get().strip(),
        })
        self._refresh_records()
        if self.refresh_callback:
            self.refresh_callback()

    def _refresh_records(self):
        """刷新记录列表"""
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not self.current_entity_id:
            return
        records = self.dm.get_transactions(self.current_entity_id)
        if not records:
            ctk.CTkLabel(self.list_frame, text="暂无记录", font=self.fonts.get("body"),
                         text_color=COLORS["text_light"][0]).pack(pady=PAD_LG)
            return
        for r in records:
            row = ctk.CTkFrame(self.list_frame, fg_color=COLORS["gray_light"][0], corner_radius=CORNER_RADIUS)
            row.pack(fill="x", pady=PAD_XS)
            type_text = "收入" if r["trans_type"] == "income" else "支出"
            ctk.CTkLabel(row, text=type_text + "  " + str(r["amount"]) + "  " + r.get("date", ""),
                         font=self.fonts.get("body")).pack(side="left", padx=PAD_LG, pady=PAD_SM)
            ctk.CTkLabel(row, text=r.get("note", ""), font=self.fonts.get("small"),
                         text_color=COLORS["text_light"][0]).pack(side="right", padx=PAD_LG, pady=PAD_SM)
