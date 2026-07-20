"""自动报税窗口"""

import sys
import os
import asyncio
import threading
from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.theme import *
from core.data_manager import DataManager
from core.tax_calculator import TaxCalculator, format_currency
from core.credential_store import CredentialStore
from automation.declaration_manager import DeclarationManager


class AutoDeclarationWindow(ctk.CTkToplevel):
    """自动报税窗口"""

    def __init__(self, parent, data_manager: DataManager, tax_calculator: TaxCalculator):
        super().__init__(parent)
        self.title("自动报税")
        self.geometry("900x700")
        self.resizable(True, True)

        self.dm = data_manager
        self.calc = tax_calculator
        self.credential_store = CredentialStore()
        self.declaration_manager = None

        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        # 主容器
        main_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg"][0])
        main_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        # 标题
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, PAD_LG))
        ctk.CTkLabel(
            title_frame, text="自动报税",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"][0]
        ).pack(side="left")

        # === 步骤1: 选择经营主体 ===
        step1_frame = ctk.CTkFrame(main_frame)
        step1_frame.pack(fill="x", pady=(0, PAD_MD))
        
        ctk.CTkLabel(
            step1_frame, text="步骤1: 选择经营主体",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"][0]
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        entity_frame = ctk.CTkFrame(step1_frame, fg_color="transparent")
        entity_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        self.entity_var = ctk.StringVar()
        entities = self.dm.get_entities()
        entity_names = [f"{e['name']} ({e.get('province', '未知')})" for e in entities]
        
        if entity_names:
            self.entity_combo = ctk.CTkComboBox(
                entity_frame, values=entity_names,
                variable=self.entity_var, width=400
            )
            self.entity_combo.pack(side="left", padx=(0, PAD_SM))
            self.entity_combo.set(entity_names[0])
        else:
            ctk.CTkLabel(
                entity_frame, text="暂无经营主体，请先添加",
                text_color=COLORS["error"][0]
            ).pack(side="left")

        # === 步骤2: 选择省份和登录方式 ===
        step2_frame = ctk.CTkFrame(main_frame)
        step2_frame.pack(fill="x", pady=(0, PAD_MD))
        
        ctk.CTkLabel(
            step2_frame, text="步骤2: 登录电子税务局",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"][0]
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        login_frame = ctk.CTkFrame(step2_frame, fg_color="transparent")
        login_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        ctk.CTkLabel(login_frame, text="省份:").pack(side="left", padx=(0, PAD_XS))
        self.province_var = ctk.StringVar(value="fujian")
        province_combo = ctk.CTkComboBox(
            login_frame, values=["fujian"],
            variable=self.province_var, width=120
        )
        province_combo.pack(side="left", padx=(0, PAD_MD))

        ctk.CTkLabel(login_frame, text="登录方式:").pack(side="left", padx=(0, PAD_XS))
        self.login_method_var = ctk.StringVar(value="manual")
        login_combo = ctk.CTkComboBox(
            login_frame, values=["manual", "scan"],
            variable=self.login_method_var, width=120
        )
        login_combo.pack(side="left", padx=(0, PAD_MD))

        self.login_btn = ctk.CTkButton(
            login_frame, text="登录", width=100,
            command=self._on_login
        )
        self.login_btn.pack(side="left")

        self.login_status_label = ctk.CTkLabel(
            login_frame, text="未登录",
            text_color=COLORS["text_light"][0]
        )
        self.login_status_label.pack(side="left", padx=PAD_MD)

        # === 步骤3: 选择申报税种 ===
        step3_frame = ctk.CTkFrame(main_frame)
        step3_frame.pack(fill="x", pady=(0, PAD_MD))
        
        ctk.CTkLabel(
            step3_frame, text="步骤3: 选择申报税种",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"][0]
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        tax_type_frame = ctk.CTkFrame(step3_frame, fg_color="transparent")
        tax_type_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        self.vat_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            tax_type_frame, text="增值税",
            variable=self.vat_var
        ).pack(side="left", padx=(0, PAD_MD))

        self.iit_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            tax_type_frame, text="个人所得税",
            variable=self.iit_var
        ).pack(side="left", padx=(0, PAD_MD))

        self.surtax_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            tax_type_frame, text="附加税",
            variable=self.surtax_var
        ).pack(side="left", padx=(0, PAD_MD))

        # 申报期间
        period_frame = ctk.CTkFrame(step3_frame, fg_color="transparent")
        period_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        ctk.CTkLabel(period_frame, text="申报期间:").pack(side="left", padx=(0, PAD_XS))
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        self.period_var = ctk.StringVar(value=f"{now.year}-Q{quarter}")
        period_entry = ctk.CTkEntry(
            period_frame, textvariable=self.period_var, width=150
        )
        period_entry.pack(side="left")

        # === 步骤4: 申报数据预览 ===
        step4_frame = ctk.CTkFrame(main_frame)
        step4_frame.pack(fill="x", pady=(0, PAD_MD))
        
        ctk.CTkLabel(
            step4_frame, text="步骤4: 申报数据预览",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"][0]
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        self.data_text = ctk.CTkTextbox(
            step4_frame, height=200, width=800
        )
        self.data_text.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        # 刷新数据按钮
        refresh_btn = ctk.CTkButton(
            step4_frame, text="刷新数据", width=120,
            command=self._refresh_data
        )
        refresh_btn.pack(anchor="e", padx=PAD_LG, pady=(0, PAD_LG))

        # === 步骤5: 开始申报 ===
        step5_frame = ctk.CTkFrame(main_frame)
        step5_frame.pack(fill="x", pady=(0, PAD_MD))
        
        ctk.CTkLabel(
            step5_frame, text="步骤5: 开始申报",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text"][0]
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_SM))

        btn_frame = ctk.CTkFrame(step5_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        self.declare_btn = ctk.CTkButton(
            btn_frame, text="开始自动申报", width=150,
            fg_color=COLORS["success"][0],
            hover_color=COLORS["success_hover"][0],
            command=self._on_declare
        )
        self.declare_btn.pack(side="left", padx=(0, PAD_SM))

        self.status_label = ctk.CTkLabel(
            btn_frame, text="就绪",
            text_color=COLORS["text_light"][0]
        )
        self.status_label.pack(side="left", padx=PAD_MD)

        # 初始刷新数据
        self._refresh_data()

    def _refresh_data(self):
        """刷新申报数据预览"""
        if not self.entity_var.get():
            return

        # 解析实体名称获取ID
        entity_name = self.entity_var.get()
        entities = self.dm.get_entities()
        entity = None
        for e in entities:
            display_name = f"{e['name']} ({e.get('province', '未知')})"
            if display_name == entity_name:
                entity = e
                break

        if not entity:
            return

        # 解析申报期间
        period = self.period_var.get()
        try:
            year, quarter_str = period.split("-Q")
            year = int(year)
            quarter = int(quarter_str)
        except:
            self.data_text.delete("1.0", "end")
            self.data_text.insert("1.0", "申报期间格式错误，应为: 2026-Q1")
            return

        # 计算税额
        text = f"经营主体: {entity['name']}\n"
        text += f"申报期间: {year}年第{quarter}季度\n"
        text += "=" * 50 + "\n\n"

        # 获取记账数据
        try:
            records = self.dm.get_transactions(entity["id"], year=year)
            quarter_records = [r for r in records if (int(r["month"]) - 1) // 3 + 1 == quarter]
            
            total_income = sum(r["amount"] for r in quarter_records if r["trans_type"] == "income")
            total_expense = sum(r["amount"] for r in quarter_records if r["trans_type"] == "expense")
            
            text += f"季度收入: {format_currency(total_income)}\n"
            text += f"季度费用: {format_currency(total_expense)}\n"
            text += f"应纳税所得额: {format_currency(total_income - total_expense)}\n\n"

            # 计算税额
            if self.vat_var.get():
                vat = self.calc.calculate_vat(total_income, entity.get("taxpayer_type", "small_scale"))
                text += f"增值税: {format_currency(vat)}\n"

            if self.surtax_var.get():
                surtax = self.calc.calculate_surtax(vat)
                text += f"附加税: {format_currency(surtax)}\n"

            if self.iit_var.get():
                taxable_income = total_income - total_expense
                iit = self.calc.calculate_iit_business(taxable_income)
                text += f"个人所得税: {format_currency(iit)}\n"

        except Exception as e:
            text += f"计算失败: {str(e)}\n"

        self.data_text.delete("1.0", "end")
        self.data_text.insert("1.0", text)

    def _on_login(self):
        """登录按钮点击"""
        province = self.province_var.get()
        login_method = self.login_method_var.get()

        self.login_status_label.configure(text="登录中...", text_color=COLORS["warning"][0])
        self.login_btn.configure(state="disabled")

        def do_login():
            try:
                async def _login():
                    dm = DeclarationManager(headless=False)
                    await dm.start_browser()
                    await dm.login(province, "temp", login_method)
                    return dm

                self.declaration_manager = asyncio.run(_login())
                self.login_status_label.configure(text="已登录", text_color=COLORS["success"][0])
            except Exception as e:
                self.login_status_label.configure(text="登录失败", text_color=COLORS["error"][0])
                self.after(0, lambda: messagebox.showerror("登录失败", str(e)))
            finally:
                self.login_btn.configure(state="normal")

        threading.Thread(target=do_login, daemon=True).start()

    def _on_declare(self):
        """开始申报"""
        if not self.declaration_manager:
            messagebox.showwarning("提示", "请先登录电子税务局")
            return

        if not self.entity_var.get():
            messagebox.showwarning("提示", "请选择经营主体")
            return

        # 解析实体
        entity_name = self.entity_var.get()
        entities = self.dm.get_entities()
        entity = None
        for e in entities:
            display_name = f"{e['name']} ({e.get('province', '未知')})"
            if display_name == entity_name:
                entity = e
                break

        if not entity:
            return

        # 解析期间
        period = self.period_var.get()
        try:
            year, quarter_str = period.split("-Q")
            year = int(year)
            quarter = int(quarter_str)
        except:
            messagebox.showerror("错误", "申报期间格式错误")
            return

        # 获取数据
        records = self.dm.get_transactions(entity["id"], year=year)
        quarter_records = [r for r in records if (int(r["month"]) - 1) // 3 + 1 == quarter]
        total_income = sum(r["amount"] for r in quarter_records if r["trans_type"] == "income")
        total_expense = sum(r["amount"] for r in quarter_records if r["trans_type"] == "expense")

        self.status_label.configure(text="申报中...", text_color=COLORS["warning"][0])
        self.declare_btn.configure(state="disabled")

        def do_declare():
            try:
                results = []
                dm = self.declaration_manager

                if self.vat_var.get():
                    vat = self.calc.calculate_vat(total_income, entity.get("taxpayer_type", "small_scale"))
                    result = asyncio.run(dm.declare_vat(
                        entity["id"], entity["name"], "fujian", period,
                        {"sales_amount": total_income, "tax_amount": vat}
                    ))
                    results.append(("增值税", result))

                if self.iit_var.get():
                    taxable_income = total_income - total_expense
                    iit = self.calc.calculate_iit_business(taxable_income)
                    result = asyncio.run(dm.declare_iit(
                        entity["id"], entity["name"], "fujian", period,
                        {"income": total_income, "expenses": total_expense}
                    ))
                    results.append(("个人所得税", result))

                if self.surtax_var.get():
                    vat = self.calc.calculate_vat(total_income, entity.get("taxpayer_type", "small_scale"))
                    surtax = self.calc.calculate_surtax(vat)
                    result = asyncio.run(dm.declare_surtax(
                        entity["id"], entity["name"], "fujian", period,
                        {"vat_amount": vat}
                    ))
                    results.append(("附加税", result))

                # 显示结果
                msg = "申报完成\n\n"
                for tax_type, result in results:
                    status = result.get("status", "unknown")
                    status_text = "成功" if status == "success" else "失败" if status == "error" else "待确认"
                    msg += f"{tax_type}: {status_text}\n"

                self.after(0, lambda: messagebox.showinfo("申报结果", msg))
                self.status_label.configure(text="申报完成", text_color=COLORS["success"][0])

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("申报失败", str(e)))
                self.status_label.configure(text="申报失败", text_color=COLORS["error"][0])
            finally:
                self.declare_btn.configure(state="normal")

        threading.Thread(target=do_declare, daemon=True).start()
