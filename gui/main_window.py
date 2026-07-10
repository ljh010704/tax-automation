"""税务记账助手 - 主窗口"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import threading
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.data_manager import DataManager
from core.tax_calculator import TaxCalculator, format_currency
from core.declaration_runner import DeclarationRunner
from gui.entity_manager import EntityManagerWindow
from gui.income_input import IncomeInputWindow
from gui.tax_calculator_gui import TaxCalculatorWindow
from gui.bookkeeping import BookkeepingWindow


class MainWindow:
    """主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("税务记账助手")
        self.root.geometry("960x640")
        self.root.minsize(860, 540)

        self.dm = DataManager()
        self.calc = TaxCalculator()
        self.runner = DeclarationRunner(self.dm, self.calc)

        self._create_menu()
        self._create_main_layout()
        self._update_status_bar()

    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出数据", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        manage_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="管理", menu=manage_menu)
        manage_menu.add_command(label="经营管理主体", command=self._open_entity_manager)
        manage_menu.add_command(label="记账", command=self._open_bookkeeping)
        manage_menu.add_command(label="快速收入录入", command=self._open_income_input)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="税额计算器", command=self._open_tax_calculator)
        tools_menu.add_command(label="社保计算器", command=self._open_social_security)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_usage)
        help_menu.add_command(label="关于", command=self._show_about)

    def _create_main_layout(self):
        """创建主界面布局"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        quick_frame = ttk.LabelFrame(main_frame, text="快速操作", padding=10)
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(quick_frame, text="记账", command=self._open_bookkeeping).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="经营管理主体", command=self._open_entity_manager).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="快速收入录入", command=self._open_income_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="税额计算", command=self._open_tax_calculator).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="开始申报", command=self._start_declaration).pack(side=tk.LEFT, padx=5)

        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        entity_frame = ttk.LabelFrame(middle_frame, text="经营管理主体列表", padding=10)
        entity_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        columns = ("id", "name", "credit_code", "entity_type", "taxpayer_type", "legal_rep", "biz_status", "province")
        self.entity_tree = ttk.Treeview(entity_frame, columns=columns, show="headings", height=8)

        self.entity_tree.heading("id", text="序号")
        self.entity_tree.heading("name", text="名称")
        self.entity_tree.heading("credit_code", text="统一社会信用代码")
        self.entity_tree.heading("entity_type", text="类型")
        self.entity_tree.heading("taxpayer_type", text="纳税人")
        self.entity_tree.heading("legal_rep", text="法人")
        self.entity_tree.heading("biz_status", text="状态")
        self.entity_tree.heading("province", text="省份")

        self.entity_tree.column("id", width=35, minwidth=35)
        self.entity_tree.column("name", width=200, minwidth=120)
        self.entity_tree.column("credit_code", width=150, minwidth=100)
        self.entity_tree.column("entity_type", width=70, minwidth=50)
        self.entity_tree.column("taxpayer_type", width=80, minwidth=50)
        self.entity_tree.column("legal_rep", width=60, minwidth=40)
        self.entity_tree.column("biz_status", width=60, minwidth=40)
        self.entity_tree.column("province", width=80, minwidth=50)

        scrollbar = ttk.Scrollbar(entity_frame, orient=tk.VERTICAL, command=self.entity_tree.yview)
        self.entity_tree.configure(yscrollcommand=scrollbar.set)
        self.entity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        right_frame = ttk.Frame(middle_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        reminder_frame = ttk.LabelFrame(right_frame, text="申报提醒", padding=10)
        reminder_frame.pack(fill=tk.X, pady=(0, 10))

        self.reminder_text = tk.Text(reminder_frame, height=8, width=36, state=tk.DISABLED)
        self.reminder_text.pack(fill=tk.X)

        overview_frame = ttk.LabelFrame(right_frame, text="当前季度申报概览", padding=10)
        overview_frame.pack(fill=tk.BOTH, expand=True)

        self.overview_text = tk.Text(overview_frame, height=8, width=36, state=tk.DISABLED)
        self.overview_text.pack(fill=tk.BOTH, expand=True)

        self._refresh_entity_list()
        self._update_reminder()
        self._update_overview()

    def _refresh_entity_list(self):
        """刷新经营管理主体列表"""
        for item in self.entity_tree.get_children():
            self.entity_tree.delete(item)
        self._entity_id_map = {}

        taxpayer_map = {"small_scale": "小规模", "general": "一般"}

        entities = self.dm.get_entities()
        for idx, entity in enumerate(entities, start=1):
            item_id = self.entity_tree.insert(
                "",
                tk.END,
                values=(
                    idx,
                    entity["name"],
                    entity.get("credit_code", ""),
                    entity.get("entity_type", ""),
                    taxpayer_map.get(entity.get("taxpayer_type", ""), ""),
                    entity.get("legal_representative", ""),
                    entity.get("business_status", "正常"),
                    entity.get("province", ""),
                ),
            )
            self._entity_id_map[item_id] = entity["id"]

    def _update_reminder(self):
        """更新合规日历"""
        now = datetime.now()
        month = now.month
        quarter = (month - 1) // 3 + 1
    
        self.reminder_text.config(state=tk.NORMAL)
        self.reminder_text.delete(1.0, tk.END)
        self.reminder_text.insert(tk.END, "合规日历")
        self.reminder_text.insert(tk.END, "\\n月度：社保/记账")
        self.reminder_text.insert(tk.END, f"\\nQ{quarter}：增值税/附加税/个税预缴")
        self.reminder_text.insert(tk.END, "\\n年度：个税汇算(3.31前)/工商年报(6.30前)")
        self.reminder_text.config(state=tk.DISABLED)

    def _update_overview(self):
        """更新申报概览"""
        self.overview_text.config(state=tk.NORMAL)
        self.overview_text.delete(1.0, tk.END)

        entities = self.dm.get_entities()
        if not entities:
            self.overview_text.insert(tk.END, "暂无经营主体，请先添加经营主体。")
            self.overview_text.config(state=tk.DISABLED)
            return

        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1

        self.overview_text.insert(tk.END, f"当前: {year}年 第{quarter}季度\n经营主体: {len(entities)}个\n")
        self.overview_text.insert(tk.END, "—" * 28 + "\n")

        total_tax = 0
        for entity in entities:
            summary = self.dm.get_quarterly_summary(entity["id"], year, quarter)
            if summary["income"] > 0:
                result = self.calc.calculate_all_quarterly(summary["income"], summary["expense"])
                tax = result["total_quarterly_tax"]
                total_tax += tax
                self.overview_text.insert(tk.END, f"{entity['name'][:10]}: {format_currency(tax)}\n")
            else:
                self.overview_text.insert(tk.END, f"{entity['name'][:10]}: 未记账\n")

        self.overview_text.insert(tk.END, "—" * 28 + "\n")
        self.overview_text.insert(tk.END, f"本季度税费: {format_currency(total_tax)}\n")

        self.overview_text.config(state=tk.DISABLED)

    def _update_status_bar(self):
        """更新状态栏"""
        pass

    def _get_selected_entity_id(self):
        selected = self.entity_tree.selection()
        if not selected:
            return None
        return self._entity_id_map.get(selected[0], self.entity_tree.item(selected[0])["values"][0])

    def _start_declaration(self):
        """开始申报（1.0 半自动）"""
        entity_id = self._get_selected_entity_id()
        if not entity_id:
            messagebox.showwarning("提示", "请先在左侧选择一个经营主体。")
            return

        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1

        try:
            package = self.runner.build_declaration_package(entity_id, year, quarter)
        except Exception as e:
            messagebox.showerror("申报准备失败", f"生成申报数据包失败：{e}")
            return

        if not package.login_url:
            messagebox.showwarning("提示", "该主体未配置电子税务局地址，请先在经营管理主体中补充 login_url。")
            return

        confirm_text = (
            f"即将开始 1.0 半自动申报流程：\n\n"
            f"主体：{package.entity_name}\n"
            f"时间：{package.year}年 第{package.quarter}季度\n"
            f"增值税：{format_currency(package.items[0]['amount'])}\n"
            f"附加税：{format_currency(package.items[1]['amount'])}\n"
            f"个人所得税：{format_currency(package.items[2]['amount'])}\n\n"
            f"程序会自动打开浏览器并填表，最后仍由你确认提交。是否继续？"
        )
        if not messagebox.askyesno("确认开始申报", confirm_text):
            return

        messagebox.showinfo("开始申报", "即将打开浏览器并登录电子税务局，请准备好登录方式。")

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
                        result = await self.runner.run_semi_auto(package, adapter)
                        return result
                    finally:
                        await browser.stop()

                result = asyncio.run(_run())
                self.root.after(0, lambda: messagebox.showinfo("申报结果", f"{result.get('message', '流程结束')}"))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: messagebox.showerror("申报失败", f"申报过程出错：{e}"))

        threading.Thread(target=run_in_thread, daemon=True).start()

    def _open_entity_manager(self):
        """打开经营管理主体窗口"""
        EntityManagerWindow(self.root, self.dm, self._refresh_entity_list)

    def _open_income_input(self):
        """打开收入数据录入窗口"""
        IncomeInputWindow(self.root, self.dm, self._update_overview)

    def _open_bookkeeping(self):
        """打开记账窗口"""
        BookkeepingWindow(self.root, self.dm, self._update_overview)

    def _open_tax_calculator(self):
        """打开税额计算器"""
        TaxCalculatorWindow(self.root, self.calc)

    def _open_social_security(self):
        """打开社保计算器"""
        from gui.tax_calculator_gui import TaxCalculatorWindow
        win = TaxCalculatorWindow(self.root, self.calc)
        try:
            notebook = win.window.children.get('!notebook')
            if notebook:
                notebook.select(2)
        except Exception:
            pass

    def _export_data(self):
        """导出数据"""
        messagebox.showinfo("提示", "导出功能暂未开放，后续版本会支持数据导出。")

    def _get_annual_report_data(self):
        """汇总年报数据（供工商年报填报参考）"""
        year = datetime.now().year - 1  # 年报填报上年数据

        entities = self.dm.get_entities()
        total_income = 0
        entity_count = len(entities)

        for entity in entities:
            # 获取年度收入汇总
            try:
                records = self.dm.get_transactions(entity["id"], year=year)
                for r in records:
                    if r["trans_type"] == "income":
                        total_income += r["amount"]
            except Exception:
                pass

        return {
            "year": year,
            "entity_count": entity_count,
            "total_income": round(total_income, 2),
        }

    def _show_usage(self):
        """显示使用说明"""
        messagebox.showinfo(
            "使用说明",
            "1. 先在【经营管理主体】中添加主体，并配置电子税务局地址。\n"
            "2. 优先通过【记账】录入收入和支出。\n"
            "3. 在左侧选中主体后，点击【开始申报】。\n"
            "4. 程序会自动准备申报数据、打开浏览器并填表。\n"
            "5. 最终由你确认后，再提交申报。\n",
        )

    def _show_about(self):
        """显示关于信息"""
        messagebox.showinfo(
            "关于",
            "税务记账助手 v1.0\n\n"
            "功能：\n"
            "- 经营主体管理\n"
            "- 记账与收入录入\n"
            "- 税额自动计算\n"
            "- 企业信息查询辅助\n"
            "- 1.0 半自动申报流程\n\n"
            "支持税种：\n"
            "- 增值税（小规模纳税人）\n"
            "- 个人所得税（经营所得）\n"
            "- 附加税\n- 印花税计算\n- 社保计算器\n- 个税年度汇算清缴\n\n"
            "说明：当前版本支持半自动申报，程序可自动填表，最终由用户确认提交。",
        )

    def run(self):
        """运行主窗口"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
