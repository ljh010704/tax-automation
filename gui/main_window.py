"""
税务记账助手 - 主窗口 (customtkinter 现代 UI)
"""

import sys
import os
import threading
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui.theme import *
from core.data_manager import DataManager
from core.tax_calculator import TaxCalculator, format_currency
from core.declaration_runner import DeclarationRunner
from gui.entity_manager import EntityManagerWindow
from gui.income_input import IncomeInputWindow
from gui.tax_calculator_gui import TaxCalculatorWindow
from gui.bookkeeping import BookkeepingWindow

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MainWindow:
    """主窗口 - 现代侧边栏布局"""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("税务记账助手")
        self.root.geometry("1020x680")
        self.root.minsize(800, 500)

        # 响应式字体管理器
        self.fonts = ResponsiveFont(self.root)

        self.dm = DataManager()
        self.calc = TaxCalculator()
        self.runner = DeclarationRunner(self.dm, self.calc)

        self._id_map = {}
        self._create_layout()
        self.fonts.bind_resize()

    def _create_layout(self):
        """创建主布局：左侧边栏 + 右侧内容"""
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # === 侧边栏 ===
        sidebar = ctk.CTkFrame(self.root, width=SIDEBAR_WIDTH, corner_radius=0, fg_color=COLORS["sidebar"][0])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(4, weight=1)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=PAD_LG, pady=PAD_XL, sticky="ew")
        ctk.CTkLabel(logo_frame, text="税务记账助手", font=self.fonts.get("h1"), text_color=COLORS["sidebar_text"][0]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="v1.0 智能报税", font=self.fonts.get("small"), text_color=COLORS["text_light"][0]).pack(anchor="w")

        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.grid(row=1, column=0, padx=PAD_MD, pady=PAD_LG, sticky="ew")

        nav_items = [
            ("首页概览", self._refresh_all),
            ("经营管理主体", self._open_entity_manager),
            ("记账", self._open_bookkeeping),
            ("快速收入录入", self._open_income_input),
            ("税额计算器", self._open_tax_calculator),
        ]
        self.nav_buttons = {}
        for text, cmd in nav_items:
            btn = ctk.CTkButton(
                nav_frame, text=text, font=self.fonts.get("body"),
                fg_color="transparent", hover_color=COLORS["primary"][1],
                text_color=COLORS["sidebar_text"][0], anchor="w",
                height=40, corner_radius=CORNER_RADIUS,
                command=cmd
            )
            btn.pack(fill="x", pady=PAD_XS)
            self.nav_buttons[text] = btn

        # === 底部工具按钮 ===
        tool_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        tool_frame.grid(row=5, column=0, padx=PAD_MD, pady=PAD_LG, sticky="ew")

        ctk.CTkButton(
            tool_frame, text="开始申报", font=self.fonts.get("button"),
            fg_color=COLORS["success"][0], hover_color=COLORS["success_hover"][0],
            height=BUTTON_HEIGHT, corner_radius=CORNER_RADIUS,
            command=self._start_declaration
        ).pack(fill="x", pady=PAD_XS)

        ctk.CTkButton(
            tool_frame, text="使用说明", font=self.fonts.get("body"),
            fg_color="transparent", hover_color=COLORS["gray"][0],
            text_color=COLORS["sidebar_text"][0], border_width=1, border_color=COLORS["gray"][0],
            height=36, corner_radius=CORNER_RADIUS,
            command=self._show_usage
        ).pack(fill="x", pady=PAD_XS)

        # === 主内容区 ===
        self.content = ctk.CTkScrollableFrame(self.root, fg_color=COLORS["bg"][0])
        self.content.grid(row=0, column=1, sticky="nsew", padx=PAD_XL, pady=PAD_XL)
        self.content.grid_columnconfigure(0, weight=1)

        self._build_home()

    def _build_home(self):
        """构建首页内容"""
        for w in self.content.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", pady=(0, PAD_LG))
        ctk.CTkLabel(header, text="首页概览", font=self.fonts.get("h1"), text_color=COLORS["text"][0]).pack(side="left")
        date_str = datetime.now().strftime("%Y年%m月%d日")
        ctk.CTkLabel(header, text=date_str, font=self.fonts.get("body"), text_color=COLORS["text_light"][0]).pack(side="right")

        # === 数据卡片 ===
        cards_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, PAD_LG))
        for i in range(3):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="card")

        stats = [
            ("经营主体", str(len(self.dm.get_entities())), COLORS["primary"][0]),
            ("本月收入", format_currency(self._get_monthly_income()), COLORS["success"][0]),
            ("本月支出", format_currency(self._get_monthly_expense()), COLORS["warning"][0]),
        ]
        for i, (title, value, color) in enumerate(stats):
            card = ctk.CTkFrame(cards_frame, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS,
                                border_width=1, border_color=COLORS["border"][0])
            card.grid(row=0, column=i, padx=PAD_SM, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=self.fonts.get("small"), text_color=COLORS["text_light"][0]).pack(anchor="w", padx=PAD_LG, pady=(PAD_MD, 0))
            ctk.CTkLabel(card, text=value, font=self.fonts.get("h1"), text_color=color).pack(anchor="w", padx=PAD_LG, pady=(PAD_XS, PAD_MD))

        # === 经营主体列表 ===
        list_frame = ctk.CTkFrame(self.content, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS,
                                   border_width=1, border_color=COLORS["border"][0])
        list_frame.pack(fill="both", expand=True, pady=(0, PAD_LG))
        list_frame.grid_columnconfigure(0, weight=1)

        list_header = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=PAD_LG, pady=PAD_MD)
        ctk.CTkLabel(list_header, text="经营主体", font=self.fonts.get("h2"), text_color=COLORS["text"][0]).pack(side="left")

        self.entity_list_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        self.entity_list_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_MD))
        self.entity_list_frame.grid_columnconfigure(0, weight=1)

        self._refresh_entity_list()

        # === 合规日历 + 年报数据 ===
        bottom_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        bottom_frame.pack(fill="x")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        cal_card = ctk.CTkFrame(bottom_frame, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS,
                                border_width=1, border_color=COLORS["border"][0])
        cal_card.grid(row=0, column=0, padx=(0, PAD_SM), sticky="nsew")
        ctk.CTkLabel(cal_card, text="合规日历", font=self.fonts.get("h2"), text_color=COLORS["text"][0]).pack(anchor="w", padx=PAD_LG, pady=PAD_MD)
        self.cal_text = ctk.CTkTextbox(cal_card, font=self.fonts.get("body"), height=120, fg_color="transparent", border_width=0)
        self.cal_text.pack(fill="x", padx=PAD_LG, pady=(0, PAD_MD))
        self._update_calendar()

        report_card = ctk.CTkFrame(bottom_frame, fg_color=COLORS["card"][0], corner_radius=CORNER_RADIUS,
                                    border_width=1, border_color=COLORS["border"][0])
        report_card.grid(row=0, column=1, padx=(PAD_SM, 0), sticky="nsew")
        ctk.CTkLabel(report_card, text="年报汇总", font=self.fonts.get("h2"), text_color=COLORS["text"][0]).pack(anchor="w", padx=PAD_LG, pady=PAD_MD)
        self.report_text = ctk.CTkTextbox(report_card, font=self.fonts.get("body"), height=120, fg_color="transparent", border_width=0)
        self.report_text.pack(fill="x", padx=PAD_LG, pady=(0, PAD_MD))
        self._update_report()

    def _get_monthly_income(self):
        total = 0
        now = datetime.now()
        for e in self.dm.get_entities():
            try:
                records = self.dm.get_transactions(e["id"], year=now.year, month=now.month)
                for r in records:
                    if r["trans_type"] == "income":
                        total += r["amount"]
            except Exception:
                pass
        return total

    def _get_monthly_expense(self):
        total = 0
        now = datetime.now()
        for e in self.dm.get_entities():
            try:
                records = self.dm.get_transactions(e["id"], year=now.year, month=now.month)
                for r in records:
                    if r["trans_type"] == "expense":
                        total += r["amount"]
            except Exception:
                pass
        return total

    def _refresh_all(self):
        self._build_home()

    def _refresh_entity_list(self):
        """刷新主体列表"""
        for w in self.entity_list_frame.winfo_children():
            w.destroy()

        entities = self.dm.get_entities()
        if not entities:
            ctk.CTkLabel(self.entity_list_frame, text="暂无经营主体，请先添加", font=self.fonts.get("body"),
                         text_color=COLORS["text_light"][0]).pack(pady=PAD_LG)
            return

        taxpayer_map = {"small_scale": "小规模", "general": "一般纳税人"}

        for idx, entity in enumerate(entities, 1):
            row = ctk.CTkFrame(self.entity_list_frame, fg_color=COLORS["gray_light"][0], corner_radius=CORNER_RADIUS)
            row.pack(fill="x", pady=PAD_XS)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text=str(idx) + ". " + entity.get("entity_name", ""),
                         font=self.fonts.get("body"), text_color=COLORS["text"][0]).grid(row=0, column=0, sticky="w", padx=PAD_LG, pady=(PAD_SM, 0))
            ctk.CTkLabel(row, text=entity.get("credit_code", "") + "  " + entity.get("province", ""),
                         font=self.fonts.get("small"), text_color=COLORS["text_light"][0]).grid(row=1, column=0, sticky="w", padx=PAD_LG, pady=(0, PAD_SM))

            type_label = ctk.CTkLabel(row, text=taxpayer_map.get(entity.get("taxpayer_type", "small_scale"), ""),
                                      font=self.fonts.get("small"), width=70, height=22, corner_radius=6,
                                      fg_color=COLORS["gray_light"][0], text_color=COLORS["gray"][0])
            type_label.grid(row=0, column=1, rowspan=2, padx=PAD_SM)

            self._id_map[str(idx)] = entity["id"]

    def _update_calendar(self):
        """更新合规日历"""
        if not hasattr(self, 'cal_text'):
            return
        now = datetime.now()
        month = now.month
        quarter = (month - 1) // 3 + 1
        text = "【每月】社保代扣 / 记账\n"
        text += "【第" + str(quarter) + "季度】增值税 / 附加税 / 个税预缴\n"
        text += "【年度】个税汇算清缴(3.31前) / 工商年报(6.30前)"
        self.cal_text.delete("1.0", "end")
        self.cal_text.insert("1.0", text)

    def _update_report(self):
        """更新年报数据"""
        if not hasattr(self, 'report_text'):
            return
        year = datetime.now().year - 1
        entities = self.dm.get_entities()
        total_income = 0
        for e in entities:
            try:
                records = self.dm.get_transactions(e["id"], year=year)
                for r in records:
                    if r["trans_type"] == "income":
                        total_income += r["amount"]
            except Exception:
                pass
        text = "  主体数量: " + str(len(entities)) + " 家\n"
        text += "  年度收入: " + format_currency(total_income)
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", text)

    def _start_declaration(self):
        """开始申报"""
        entities = self.dm.get_entities()
        if not entities:
            messagebox.showwarning("提示", "请先添加经营主体")
            return
        entity_id = entities[0]["id"]

        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1

        try:
            package = self.runner.build_declaration_package(entity_id, year, quarter)
        except Exception as e:
            messagebox.showerror("错误", "生成数据失败: " + str(e))
            return

        if not package.login_url:
            messagebox.showwarning("提示", "未配置电子税务局地址")
            return

        msg = "主体: " + package.entity_name + "\n" + str(year) + "年第" + str(quarter) + "季度\n"
        msg += "增值税: " + format_currency(package.items[0]["amount"]) + "\n"
        msg += "附加税: " + format_currency(package.items[1]["amount"]) + "\n"
        msg += "个税: " + format_currency(package.items[2]["amount"])
        if not messagebox.askyesno("确认申报", msg):
            return

        def run_in_thread():
            try:
                import asyncio
                from automation.sites.shanxi import ShanxiAdapter
                from automation.browser import BrowserAutomation
                async def _run():
                    browser = BrowserAutomation()
                    await browser.start()
                    try:
                        adapter = ShanxiAdapter(browser)
                        return await self.runner.run_semi_auto(package, adapter)
                    finally:
                        await browser.stop()
                result = asyncio.run(_run())
                self.root.after(0, lambda: messagebox.showinfo("结果", result.get("message", "完成")))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))

        threading.Thread(target=run_in_thread, daemon=True).start()

    def _open_entity_manager(self):
        EntityManagerWindow(self.root, self.dm, self._refresh_entity_list)

    def _open_income_input(self):
        IncomeInputWindow(self.root, self.dm, self._refresh_all)

    def _open_bookkeeping(self):
        BookkeepingWindow(self.root, self.dm, self._refresh_all)

    def _open_tax_calculator(self):
        TaxCalculatorWindow(self.root, self.calc)

    def _show_usage(self):
        messagebox.showinfo("使用说明",
            "1. 添加经营主体\n2. 录入收支\n3. 点击开始申报\n4. 确认后提交")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
