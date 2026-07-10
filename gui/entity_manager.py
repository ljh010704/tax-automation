"""
经营管理主体窗口 - customtkinter UI
"""

import sys
import os
from tkinter import messagebox

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.theme import *


class EntityManagerWindow:
    """经营管理主体窗口"""

    def __init__(self, parent, data_manager, refresh_callback=None):
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self._id_map = {}

        self.window = ctk.CTkToplevel(parent)
        self.window.title("经营管理主体管理")
        self.window.geometry("720x520")
        self.window.grab_set()

        # 响应式字体
        self.fonts = ResponsiveFont(self.window)
        self.fonts.bind_resize()

        self._create_widgets()
        self._refresh_list()

    def _create_widgets(self):
        """创建界面组件"""
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)

        # 顶部按钮栏
        btn_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        btn_frame.grid(row=0, column=0, padx=PAD_LG, pady=PAD_MD, sticky="ew")

        ctk.CTkButton(btn_frame, text="新增主体", font=self.fonts.get("button"),
                      fg_color=COLORS["primary"][0], hover_color=COLORS["primary_hover"][0],
                      command=self._add_entity).pack(side="left", padx=PAD_XS)
        ctk.CTkButton(btn_frame, text="删除选中", font=self.fonts.get("button"),
                      fg_color=COLORS["danger"][0], hover_color=COLORS["danger_hover"][0],
                      command=self._delete_selected).pack(side="left", padx=PAD_XS)

        # 列表区域
        self.list_frame = ctk.CTkScrollableFrame(self.window, fg_color=COLORS["bg"][0])
        self.list_frame.grid(row=1, column=0, padx=PAD_LG, pady=(0, PAD_MD), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

    def _refresh_list(self):
        """刷新列表"""
        for w in self.list_frame.winfo_children():
            w.destroy()

        entities = self.dm.get_entities()
        if not entities:
            ctk.CTkLabel(self.list_frame, text="暂无经营主体", font=self.fonts.get("body"),
                         text_color=COLORS["text_light"][0]).pack(pady=PAD_XL)
            return

        for idx, entity in enumerate(entities, 1):
            row = ctk.CTkFrame(self.list_frame, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS,
                                border_width=1, border_color=COLORS["border"][0])
            row.pack(fill="x", pady=PAD_XS)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text=str(idx) + ". " + entity.get("entity_name", ""),
                         font=self.fonts.get("body"), text_color=COLORS["text"][0]).grid(row=0, column=0, sticky="w", padx=PAD_LG, pady=(PAD_SM, 0))
            ctk.CTkLabel(row, text=entity.get("credit_code", ""),
                         font=self.fonts.get("small"), text_color=COLORS["text_light"][0]).grid(row=1, column=0, sticky="w", padx=PAD_LG, pady=(0, PAD_SM))

            self._id_map[str(idx)] = entity["id"]

    def _add_entity(self):
        """新增主体 - 弹出表单"""
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("新增经营主体")
        dialog.geometry("480x420")
        dialog.grab_set()

        dialog_fonts = ResponsiveFont(dialog)
        dialog_fonts.bind_resize()

        form_frame = ctk.CTkScrollableFrame(dialog, fg_color=COLORS["bg"][0])
        form_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)
        form_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("entity_name", "企业名称"),
            ("credit_code", "统一社会信用代码"),
            ("legal_rep", "法定代表人"),
            ("entity_type", "主体类型"),
            ("province", "省份"),
            ("city", "城市"),
            ("address", "经营地址"),
            ("tax_authority", "主管税务机关"),
            ("taxpayer_type", "纳税人类型"),
            ("tax_url", "电子税务局网址"),
        ]
        entries = {}
        for i, (key, label) in enumerate(fields):
            ctk.CTkLabel(form_frame, text=label + ":", font=dialog_fonts.get("body")).grid(row=i, column=0, sticky="w", pady=PAD_SM, padx=PAD_SM)
            entry = ctk.CTkEntry(form_frame, font=dialog_fonts.get("body"), height=ENTRY_HEIGHT)
            entry.grid(row=i, column=1, sticky="ew", pady=PAD_SM, padx=PAD_SM)
            entries[key] = entry

        def save():
            data = {}
            for key, entry in entries.items():
                val = entry.get().strip()
                if not val:
                    messagebox.showwarning("提示", "请填写完整信息")
                    return
                data[key] = val
            self.dm.add_entity(data)
            self._refresh_list()
            if self.refresh_callback:
                self.refresh_callback()
            dialog.destroy()

        ctk.CTkButton(form_frame, text="保存", font=dialog_fonts.get("button"),
                      fg_color=COLORS["success"][0], hover_color=COLORS["success_hover"][0],
                      command=save).grid(row=len(fields), column=0, columnspan=2, pady=PAD_LG)

    def _delete_selected(self):
        """删除选中的主体"""
        # 简化：删除最后一个
        entities = self.dm.get_entities()
        if not entities:
            messagebox.showinfo("提示", "没有可删除的主体")
            return
        if not messagebox.askyesno("确认", "确定要删除 [" + entities[-1].get("entity_name", "") + "] 吗？"):
            return
        self.dm.delete_entity(entities[-1]["id"])
        self._refresh_list()
        if self.refresh_callback:
            self.refresh_callback()
