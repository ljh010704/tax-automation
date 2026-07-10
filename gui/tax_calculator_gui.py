"""
税额计算器 - customtkinter UI (Notebook 四页签)
"""

import sys
from tkinter import END

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.theme import *


class TaxCalculatorWindow:
    """税额计算器 - 四合一合规计算"""

    def __init__(self, parent, tax_calculator):
        self.calc = tax_calculator

        self.window = ctk.CTkToplevel(parent)
        self.window.title("税额计算器")
        self.window.geometry("560x600")
        self.window.grab_set()

        # Notebook
        self.notebook = ctk.CTkTabview(self.window, corner_radius=CORNER_RADIUS)
        self.notebook.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        tab1 = self.notebook.add("季度税费")
        tab2 = self.notebook.add("印花税")
        tab3 = self.notebook.add("社保计算")
        tab4 = self.notebook.add("年度汇算")
        self.notebook.set("季度税费")

        self._create_quarterly_tab(tab1)
        self._create_stamp_tab(tab2)
        self._create_social_tab(tab3)
        self._create_annual_tab(tab4)

    def _create_quarterly_tab(self, parent):
        main = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        inp = ctk.CTkFrame(main, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        inp.pack(fill="x", pady=(0, PAD_MD))

        self.q_income_var = ctk.StringVar(value="100000")
        self.q_expenses_var = ctk.StringVar(value="60000")
        self.q_taxpayer_var = ctk.StringVar(value="small_scale")

        pad = {"padx": PAD_MD, "pady": PAD_SM}
        ctk.CTkLabel(inp, text="季度收入（元）", font=FONT_BODY).grid(row=0, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.q_income_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=0, column=1, **pad)

        ctk.CTkLabel(inp, text="季度费用（元）", font=FONT_BODY).grid(row=1, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.q_expenses_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=1, column=1, **pad)

        ctk.CTkLabel(inp, text="纳税人类型", font=FONT_BODY).grid(row=2, column=0, sticky="w", **pad)
        ctk.CTkComboBox(inp, variable=self.q_taxpayer_var, values=["small_scale", "general"],
                        width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=2, column=1, **pad)

        ctk.CTkButton(main, text="计算税额", height=BUTTON_HEIGHT, font=FONT_BUTTON,
                       corner_radius=CORNER_RADIUS, command=self._calc_quarterly).pack(pady=PAD_MD)

        self.q_result = ctk.CTkTextbox(main, height=200, font=FONT_MONO, corner_radius=CORNER_RADIUS)
        self.q_result.pack(fill="both", expand=True)

    def _calc_quarterly(self):
        from core.tax_calculator import format_currency
        try:
            income = float(self.q_income_var.get())
            expenses = float(self.q_expenses_var.get())
        except ValueError:
            return

        is_small = self.q_taxpayer_var.get() == "small_scale"
        vat = self.calc.calculate_vat(income, is_small)
        surtax = self.calc.calculate_surtax(vat["vat"])
        ai = income * 4
        ae = expenses * 4
        iit = self.calc.calculate_iit_business_income(ai, ae)
        total = vat["vat"] + surtax["total"] + iit["quarterly_tax"]

        text = "=== 季度税费 ===\n\n"
        text += "收入: " + format_currency(income) + "  费用: " + format_currency(expenses) + "\n\n"
        text += "[增值税]\n"
        if vat["is_exempt"]:
            text += "  免征 (季度未超30万)\n"
        else:
            text += "  税额: " + format_currency(vat["vat"]) + "\n"
        text += "\n[附加税]\n"
        text += "  城建税: " + format_currency(surtax["city_maintenance"]) + "\n"
        text += "  教育费附加: " + format_currency(surtax["education_surcharge"]) + "\n"
        text += "  地方教育附加: " + format_currency(surtax["local_education_surcharge"]) + "\n"
        text += "  附加税合计: " + format_currency(surtax["total"]) + "\n"
        text += "\n[个人所得税(经营所得)]\n"
        text += "  应纳税所得额: " + format_currency(iit["taxable_income"]) + "\n"
        text += "  适用税率: " + str(iit["tax_rate"]*100) + "%\n"
        text += "  年度应纳税额: " + format_currency(iit["annual_tax"]) + "\n"
        text += "  季度预缴: " + format_currency(iit["quarterly_tax"]) + "\n\n"
        text += "---\n  季度税费合计: " + format_currency(total)
        self.q_result.delete("1.0", "end")
        self.q_result.insert("1.0", text)

    def _create_stamp_tab(self, parent):
        main = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        inp = ctk.CTkFrame(main, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        inp.pack(fill="x", pady=(0, PAD_MD))

        self.s_income_var = ctk.StringVar(value="100000")
        self.s_capital_var = ctk.StringVar(value="0")
        self.s_small_var = ctk.StringVar(value="yes")

        pad = {"padx": PAD_MD, "pady": PAD_SM}
        ctk.CTkLabel(inp, text="季度收入（元）", font=FONT_BODY).grid(row=0, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.s_income_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=0, column=1, **pad)

        ctk.CTkLabel(inp, text="实缴资本（元）", font=FONT_BODY).grid(row=1, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.s_capital_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=1, column=1, **pad)

        ctk.CTkButton(main, text="计算印花税", height=BUTTON_HEIGHT, font=FONT_BUTTON,
                       corner_radius=CORNER_RADIUS, command=self._calc_stamp).pack(pady=PAD_MD)

        self.s_result = ctk.CTkTextbox(main, height=200, font=FONT_MONO, corner_radius=CORNER_RADIUS)
        self.s_result.pack(fill="both", expand=True)

    def _calc_stamp(self):
        from core.tax_calculator import format_currency
        try:
            income = float(self.s_income_var.get())
            capital = float(self.s_capital_var.get())
        except ValueError:
            return

        is_small = self.s_small_var.get() == "yes"
        r = self.calc.calculate_stamp_tax(income, capital, is_small)

        text = "=== 印花税估算 ===\n\n"
        for key in ["contract", "books", "capital"]:
            item = r[key]
            text += "[" + item["title"] + "]\n"
            text += "  税额: " + format_currency(item["amount"]) + " (" + item["note"] + ")\n\n"
        text += "---\n  印花税合计: " + format_currency(r["total"])
        self.s_result.delete("1.0", "end")
        self.s_result.insert("1.0", text)

    def _create_social_tab(self, parent):
        main = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        inp = ctk.CTkFrame(main, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        inp.pack(fill="x", pady=(0, PAD_MD))

        self.ss_base_var = ctk.StringVar(value="5000")

        pad = {"padx": PAD_MD, "pady": PAD_SM}
        ctk.CTkLabel(inp, text="月缴费基数（元）", font=FONT_BODY).grid(row=0, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.ss_base_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=0, column=1, **pad)
        ctk.CTkLabel(inp, text="按全国平均费率计算", font=FONT_SMALL, text_color=COLORS["text_light"][0]).grid(row=1, column=0, columnspan=2, sticky="w", padx=PAD_MD)

        ctk.CTkButton(main, text="计算社保", height=BUTTON_HEIGHT, font=FONT_BUTTON,
                       corner_radius=CORNER_RADIUS, command=self._calc_social).pack(pady=PAD_MD)

        self.ss_result = ctk.CTkTextbox(main, height=200, font=FONT_MONO, corner_radius=CORNER_RADIUS)
        self.ss_result.pack(fill="both", expand=True)

    def _calc_social(self):
        from core.tax_calculator import format_currency
        try:
            base = float(self.ss_base_var.get())
        except ValueError:
            return

        r = self.calc.calculate_social_security(base)

        text = "=== 社保缴费计算 ===\n\n"
        text += "月缴费基数: " + format_currency(r["monthly_base"]) + "\n\n"
        text += "[养老保险]\n  企业: " + format_currency(r["pension"]["employer"]) + "  个人: " + format_currency(r["pension"]["individual"]) + "\n"
        text += "[医疗保险]\n  企业: " + format_currency(r["medical"]["employer"]) + "  个人: " + format_currency(r["medical"]["individual"]) + "\n"
        text += "[失业保险]\n  企业: " + format_currency(r["unemployment"]["employer"]) + "  个人: " + format_currency(r["unemployment"]["individual"]) + "\n\n"
        text += "---\n  企业承担: " + format_currency(r["employer_total"]) + "\n"
        text += "  个人承担: " + format_currency(r["individual_total"]) + "\n"
        text += "  当月总缴费: " + format_currency(r["grand_total"])
        self.ss_result.delete("1.0", "end")
        self.ss_result.insert("1.0", text)

    def _create_annual_tab(self, parent):
        main = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        inp = ctk.CTkFrame(main, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        inp.pack(fill="x", pady=(0, PAD_MD))

        self.a_income_var = ctk.StringVar(value="400000")
        self.a_expenses_var = ctk.StringVar(value="240000")
        self.a_prepaid_var = ctk.StringVar(value="10000")

        pad = {"padx": PAD_MD, "pady": PAD_SM}
        ctk.CTkLabel(inp, text="年度收入（元）", font=FONT_BODY).grid(row=0, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.a_income_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=0, column=1, **pad)

        ctk.CTkLabel(inp, text="年度费用（元）", font=FONT_BODY).grid(row=1, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.a_expenses_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=1, column=1, **pad)

        ctk.CTkLabel(inp, text="已预缴税额（元）", font=FONT_BODY).grid(row=2, column=0, sticky="w", **pad)
        ctk.CTkEntry(inp, textvariable=self.a_prepaid_var, width=180, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=2, column=1, **pad)

        ctk.CTkButton(main, text="计算汇算清缴", height=BUTTON_HEIGHT, font=FONT_BUTTON,
                       corner_radius=CORNER_RADIUS, command=self._calc_annual).pack(pady=PAD_MD)

        self.a_result = ctk.CTkTextbox(main, height=200, font=FONT_MONO, corner_radius=CORNER_RADIUS)
        self.a_result.pack(fill="both", expand=True)

    def _calc_annual(self):
        from core.tax_calculator import format_currency
        try:
            income = float(self.a_income_var.get())
            expenses = float(self.a_expenses_var.get())
            prepaid = float(self.a_prepaid_var.get())
        except ValueError:
            return

        r = self.calc.calculate_iit_annual_reconciliation(income, expenses, prepaid)

        text = "=== 个税汇算清缴 ===\n\n"
        text += "年度收入: " + format_currency(r["annual_income"]) + "\n"
        text += "年度费用: " + format_currency(r["annual_expenses"]) + "\n"
        text += "应纳税所得额: " + format_currency(r["taxable_income"]) + "\n"
        text += "适用税率: " + str(r["tax_rate"]*100) + "%\n"
        text += "速算扣除数: " + str(r["quick_deduction"]) + "\n"
        text += "年度应纳税额: " + format_currency(r["annual_tax"]) + "\n"
        text += "已预缴税额: " + format_currency(r["quarterly_prepaid"]) + "\n\n"
        text += "---\n"
        diff = r["difference"]
        if diff > 0:
            text += "应补缴: " + format_currency(diff)
        elif diff < 0:
            text += "应退税: " + format_currency(abs(diff))
        else:
            text += "无差额"
        self.a_result.delete("1.0", "end")
        self.a_result.insert("1.0", text)
