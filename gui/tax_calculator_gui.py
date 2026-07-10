"""
税额计算器 - customtkinter UI (Notebook 四页签)
"""

import sys
import os
from tkinter import END

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.theme import *
from core.tax_calculator import TaxCalculator, format_currency


class TaxCalculatorWindow:
    """税额计算器 - 四合一合规计算"""

    def __init__(self, parent, tax_calculator):
        self.calc = tax_calculator

        self.window = ctk.CTkToplevel(parent)
        self.window.title("税额计算器")
        self.window.geometry("560x600")
        self.window.grab_set()

        # 响应式字体
        self.fonts = ResponsiveFont(self.window)
        self.fonts.bind_resize()

        # Notebook
        self.notebook = ctk.CTkTabview(self.window, corner_radius=CORNER_RADIUS)
        self.notebook.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        self.notebook.add("季度税费")
        self.notebook.add("印花税")
        self.notebook.add("社保计算")
        self.notebook.add("年度汇算")

        self._build_quarterly_tab(self.notebook.tab("季度税费"))
        self._build_stamp_tab(self.notebook.tab("印花税"))
        self._build_social_tab(self.notebook.tab("社保计算"))
        self._build_annual_tab(self.notebook.tab("年度汇算"))

    def _build_quarterly_tab(self, tab):
        """季度税费计算"""
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="季度收入:", font=self.fonts.get("body")).grid(row=0, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.q_income = ctk.CTkEntry(tab, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.q_income.grid(row=0, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkLabel(tab, text="纳税人类型:", font=self.fonts.get("body")).grid(row=1, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.q_type = ctk.CTkComboBox(tab, values=["小规模纳税人", "一般纳税人"], font=self.fonts.get("body"), state="readonly")
        self.q_type.set("小规模纳税人")
        self.q_type.grid(row=1, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkButton(tab, text="计算", font=self.fonts.get("button"),
                      fg_color=COLORS["primary"][0], hover_color=COLORS["primary_hover"][0],
                      command=self._calc_quarterly).grid(row=2, column=0, columnspan=2, pady=PAD_LG)

        self.q_result = ctk.CTkTextbox(tab, font=self.fonts.get("mono"), height=280)
        self.q_result.grid(row=3, column=0, columnspan=2, padx=PAD_MD, pady=PAD_MD, sticky="nsew")

    def _calc_quarterly(self):
        try:
            income = float(self.q_income.get())
        except ValueError:
            self.q_result.delete("1.0", END)
            self.q_result.insert("1.0", "请输入有效金额")
            return
        is_small = self.q_type.get() == "小规模纳税人"
        result = self.calc.calculate_quarterly_vat(income, is_small)
        text = "增值税: " + format_currency(result["vat"]) + "\n"
        text += "附加税: " + format_currency(result["surcharge"]) + "\n"
        text += "个税预缴: " + format_currency(result["iit"]) + "\n"
        text += "合计: " + format_currency(result["total"])
        self.q_result.delete("1.0", END)
        self.q_result.insert("1.0", text)

    def _build_stamp_tab(self, tab):
        """印花税计算"""
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="季度收入:", font=self.fonts.get("body")).grid(row=0, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.s_income = ctk.CTkEntry(tab, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.s_income.grid(row=0, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkLabel(tab, text="实缴资本:", font=self.fonts.get("body")).grid(row=1, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.s_capital = ctk.CTkEntry(tab, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.s_capital.insert(0, "0")
        self.s_capital.grid(row=1, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkButton(tab, text="计算", font=self.fonts.get("button"),
                      fg_color=COLORS["primary"][0], hover_color=COLORS["primary_hover"][0],
                      command=self._calc_stamp).grid(row=2, column=0, columnspan=2, pady=PAD_LG)

        self.s_result = ctk.CTkTextbox(tab, font=self.fonts.get("mono"), height=280)
        self.s_result.grid(row=3, column=0, columnspan=2, padx=PAD_MD, pady=PAD_MD, sticky="nsew")

    def _calc_stamp(self):
        try:
            income = float(self.s_income.get())
            capital = float(self.s_capital.get())
        except ValueError:
            self.s_result.delete("1.0", END)
            self.s_result.insert("1.0", "请输入有效金额")
            return
        result = self.calc.calculate_stamp_tax(income, capital)
        text = "购销合同: " + format_currency(result["sales_contract"]) + "\n"
        text += "营业账簿: " + format_currency(result["account_book"]) + "\n"
        text += "实缴资本: " + format_currency(result["paid_capital"]) + "\n"
        text += "合计: " + format_currency(result["total"])
        self.s_result.delete("1.0", END)
        self.s_result.insert("1.0", text)

    def _build_social_tab(self, tab):
        """社保计算"""
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="月缴费基数:", font=self.fonts.get("body")).grid(row=0, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.so_base = ctk.CTkEntry(tab, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.so_base.grid(row=0, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkButton(tab, text="计算", font=self.fonts.get("button"),
                      fg_color=COLORS["primary"][0], hover_color=COLORS["primary_hover"][0],
                      command=self._calc_social).grid(row=1, column=0, columnspan=2, pady=PAD_LG)

        self.so_result = ctk.CTkTextbox(tab, font=self.fonts.get("mono"), height=280)
        self.so_result.grid(row=2, column=0, columnspan=2, padx=PAD_MD, pady=PAD_MD, sticky="nsew")

    def _calc_social(self):
        try:
            base = float(self.so_base.get())
        except ValueError:
            self.so_result.delete("1.0", END)
            self.so_result.insert("1.0", "请输入有效金额")
            return
        result = self.calc.calculate_social_security(base)
        text = "企业承担: " + format_currency(result["employer"]) + "\n"
        text += "个人承担: " + format_currency(result["employee"]) + "\n"
        text += "合计: " + format_currency(result["total"])
        self.so_result.delete("1.0", END)
        self.so_result.insert("1.0", text)

    def _build_annual_tab(self, tab):
        """年度汇算"""
        tab.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab, text="年度收入:", font=self.fonts.get("body")).grid(row=0, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.a_income = ctk.CTkEntry(tab, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.a_income.grid(row=0, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkLabel(tab, text="年度费用:", font=self.fonts.get("body")).grid(row=1, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.a_expense = ctk.CTkEntry(tab, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.a_expense.insert(0, "0")
        self.a_expense.grid(row=1, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkLabel(tab, text="已预缴税额:", font=self.fonts.get("body")).grid(row=2, column=0, padx=PAD_MD, pady=PAD_MD, sticky="w")
        self.a_prepaid = ctk.CTkEntry(tab, font=self.fonts.get("body"), height=ENTRY_HEIGHT)
        self.a_prepaid.insert(0, "0")
        self.a_prepaid.grid(row=2, column=1, padx=PAD_MD, pady=PAD_MD, sticky="ew")

        ctk.CTkButton(tab, text="计算", font=self.fonts.get("button"),
                      fg_color=COLORS["primary"][0], hover_color=COLORS["primary_hover"][0],
                      command=self._calc_annual).grid(row=3, column=0, columnspan=2, pady=PAD_LG)

        self.a_result = ctk.CTkTextbox(tab, font=self.fonts.get("mono"), height=220)
        self.a_result.grid(row=4, column=0, columnspan=2, padx=PAD_MD, pady=PAD_MD, sticky="nsew")

    def _calc_annual(self):
        try:
            income = float(self.a_income.get())
            expense = float(self.a_expense.get())
            prepaid = float(self.a_prepaid.get())
        except ValueError:
            self.a_result.delete("1.0", END)
            self.a_result.insert("1.0", "请输入有效金额")
            return
        result = self.calc.calculate_iit_annual_reconciliation(income, expense, prepaid)
        text = "年度所得: " + format_currency(result["annual_income"]) + "\n"
        text += "已预缴: " + format_currency(result["prepaid"]) + "\n"
        text += "应纳税额: " + format_currency(result["tax_due"]) + "\n"
        text += "应补(退): " + format_currency(result["refund_or_owed"])
        self.a_result.delete("1.0", END)
        self.a_result.insert("1.0", text)
