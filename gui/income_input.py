"""收入数据录入窗口"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class IncomeInputWindow:
    """收入数据录入窗口"""

    def __init__(self, parent, data_manager, refresh_callback=None):
        self.dm = data_manager
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)
        self.window.title("收入数据录入")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()

        self._create_widgets()
        self._load_entities()

    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        select_frame = ttk.LabelFrame(main_frame, text="选择申报主体和时间", padding=10)
        select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(select_frame, text="经营主体:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.entity_var = tk.StringVar()
        self.entity_combo = ttk.Combobox(select_frame, textvariable=self.entity_var, width=30, state="readonly")
        self.entity_combo.grid(row=0, column=1, padx=5)
        self.entity_combo.bind("<<ComboboxSelected>>", self._on_entity_change)

        ttk.Label(select_frame, text="年份:").grid(row=0, column=2, padx=5)
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        year_combo = ttk.Combobox(select_frame, textvariable=self.year_var, width=8, state="readonly")
        year_combo["values"] = [str(y) for y in range(2020, 2030)]
        year_combo.grid(row=0, column=3, padx=5)

        ttk.Label(select_frame, text="季度:").grid(row=0, column=4, padx=5)
        current_quarter = (datetime.now().month - 1) // 3 + 1
        self.quarter_var = tk.StringVar(value=str(current_quarter))
        quarter_combo = ttk.Combobox(select_frame, textvariable=self.quarter_var, width=5, state="readonly")
        quarter_combo["values"] = ["1", "2", "3", "4"]
        quarter_combo.grid(row=0, column=5, padx=5)
        quarter_combo.bind("<<ComboboxSelected>>", self._on_quarter_change)

        data_frame = ttk.LabelFrame(main_frame, text="收入数据", padding=10)
        data_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(data_frame, text="季度收入（元）").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.income_var = tk.StringVar(value="0")
        ttk.Entry(data_frame, textvariable=self.income_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(data_frame, text="季度费用（元）").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.expenses_var = tk.StringVar(value="0")
        ttk.Entry(data_frame, textvariable=self.expenses_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(data_frame, text="备注").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.notes_var = tk.StringVar()
        ttk.Entry(data_frame, textvariable=self.notes_var, width=40).grid(row=2, column=1, padx=5, pady=5)

        preview_frame = ttk.LabelFrame(main_frame, text="税额预览", padding=10)
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.preview_text = tk.Text(preview_frame, height=6, state=tk.DISABLED)
        self.preview_text.pack(fill=tk.X)

        self.income_var.trace_add("write", lambda *args: self._update_preview())
        self.expenses_var.trace_add("write", lambda *args: self._update_preview())

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="加载已有数据", command=self._load_existing).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

    def _load_entities(self):
        """加载经营主体列表"""
        entities = self.dm.get_entities()
        if not entities:
            messagebox.showwarning("提示", "请先添加经营主体")
            return

        entity_names = [e["name"] for e in entities]
        self.entity_combo["values"] = entity_names
        self.entities = {e["name"]: e for e in entities}
        self.entity_combo.current(0)
        self._on_entity_change()

    def _on_entity_change(self, event=None):
        """主体选择变化"""
        self._load_existing()
        self._update_preview()

    def _on_quarter_change(self, event=None):
        """季度选择变化"""
        self._load_existing()
        self._update_preview()

    def _load_existing(self):
        """加载已有数据"""
        entity_name = self.entity_var.get()
        if not entity_name or entity_name not in self.entities:
            return

        entity = self.entities[entity_name]
        year = int(self.year_var.get())
        quarter = int(self.quarter_var.get())

        income = self.dm.get_income(entity["id"], year, quarter)
        if income:
            self.income_var.set(str(income["income"]))
            self.expenses_var.set(str(income.get("expenses", income.get("expense", 0))))
            self.notes_var.set(income.get("notes", ""))
        else:
            self.income_var.set("0")
            self.expenses_var.set("0")
            self.notes_var.set("")

    def _update_preview(self):
        """更新税额预览"""
        from core.tax_calculator import TaxCalculator, format_currency

        calc = TaxCalculator()

        try:
            income = float(self.income_var.get() or 0)
            expenses = float(self.expenses_var.get() or 0)
        except ValueError:
            return

        result = calc.calculate_all_quarterly(income, expenses)

        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)

        if income == 0:
            self.preview_text.insert(tk.END, "请输入收入数据查看税额预览。")
        else:
            vat = result["vat"]
            if vat["is_exempt"]:
                self.preview_text.insert(tk.END, "增值税: 免征 (季度收入未超过30万)\n")
            else:
                self.preview_text.insert(tk.END, f"增值税: {format_currency(vat['vat'])}\n")

            self.preview_text.insert(tk.END, f"附加税: {format_currency(result['surtax']['total'])}\n")
            self.preview_text.insert(tk.END, f"个人所得税(经营所得): {format_currency(result['iit']['quarterly_tax'])}\n")
            self.preview_text.insert(tk.END, "—" * 40 + "\n")
            self.preview_text.insert(tk.END, f"季度应缴税费合计: {format_currency(result['total_quarterly_tax'])}\n")

        self.preview_text.config(state=tk.DISABLED)

    def _save(self):
        """保存数据"""
        entity_name = self.entity_var.get()
        if not entity_name or entity_name not in self.entities:
            messagebox.showwarning("提示", "请选择经营主体")
            return

        try:
            income = float(self.income_var.get() or 0)
            expenses = float(self.expenses_var.get() or 0)
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的金额")
            return

        entity = self.entities[entity_name]
        year = int(self.year_var.get())
        quarter = int(self.quarter_var.get())
        notes = self.notes_var.get().strip()

        self.dm.save_income(entity["id"], year, quarter, income, expenses, notes)
        messagebox.showinfo("成功", "收入数据已保存")

        if self.refresh_callback:
            self.refresh_callback()
