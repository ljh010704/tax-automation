"""税额计算器窗口 - 四合一合规计算"""

import tkinter as tk
from tkinter import ttk, messagebox


class TaxCalculatorWindow:
    """税额计算器窗口（Notebook 四页签）"""

    def __init__(self, parent, tax_calculator):
        self.calc = tax_calculator

        self.window = tk.Toplevel(parent)
        self.window.title("税额计算器")
        self.window.geometry("580x620")
        self.window.transient(parent)
        self.window.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """创建 Notebook 界面"""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 四个页签
        tab1 = ttk.Frame(notebook, padding=10)
        tab2 = ttk.Frame(notebook, padding=10)
        tab3 = ttk.Frame(notebook, padding=10)
        tab4 = ttk.Frame(notebook, padding=10)

        notebook.add(tab1, text="季度税费")
        notebook.add(tab2, text="印花税")
        notebook.add(tab3, text="社保计算")
        notebook.add(tab4, text="年度汇算")

        self._create_quarterly_tab(tab1)
        self._create_stamp_tab(tab2)
        self._create_social_security_tab(tab3)
        self._create_annual_tab(tab4)

    # ==================== 页签1：季度税费 ====================
    def _create_quarterly_tab(self, parent):
        from core.tax_calculator import format_currency

        input_frame = ttk.LabelFrame(parent, text="输入数据", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="季度收入（元）").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.q_income_var = tk.StringVar(value="100000")
        ttk.Entry(input_frame, textvariable=self.q_income_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="季度费用（元）").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.q_expenses_var = tk.StringVar(value="60000")
        ttk.Entry(input_frame, textvariable=self.q_expenses_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="纳税人类型").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.q_taxpayer_var = tk.StringVar(value="small_scale")
        ttk.Radiobutton(input_frame, text="小规模纳税人", variable=self.q_taxpayer_var, value="small_scale").grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(input_frame, text="一般纳税人", variable=self.q_taxpayer_var, value="general").grid(row=2, column=2, sticky=tk.W, padx=5)

        ttk.Button(parent, text="计算税额", command=self._calculate_quarterly).pack(pady=10)

        result_frame = ttk.LabelFrame(parent, text="计算结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.q_result_text = tk.Text(result_frame, height=14, state=tk.DISABLED, font=("Consolas", 9))
        self.q_result_text.pack(fill=tk.BOTH, expand=True)

    def _calculate_quarterly(self):
        from core.tax_calculator import format_currency
        try:
            income = float(self.q_income_var.get())
            expenses = float(self.q_expenses_var.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入合法数字金额")
            return

        is_small = self.q_taxpayer_var.get() == "small_scale"
        vat = self.calc.calculate_vat(income, is_small)
        surtax = self.calc.calculate_surtax(vat["vat"])
        annual_income = income * 4
        annual_expenses = expenses * 4
        iit = self.calc.calculate_iit_business_income(annual_income, annual_expenses)
        total_tax = vat["vat"] + surtax["total"] + iit["quarterly_tax"]

        self.q_result_text.config(state=tk.NORMAL)
        self.q_result_text.delete(1.0, tk.END)
        self.q_result_text.insert(tk.END, "=" * 48 + "\n")
        self.q_result_text.insert(tk.END, "        季度税费计算结果\n")
        self.q_result_text.insert(tk.END, "=" * 48 + "\n\n")
        self.q_result_text.insert(tk.END, f"  季度收入:     {format_currency(income)}\n")
        self.q_result_text.insert(tk.END, f"  季度费用:     {format_currency(expenses)}\n")
        self.q_result_text.insert(tk.END, "-" * 48 + "\n\n")
        self.q_result_text.insert(tk.END, "【增值税】\n")
        if vat["is_exempt"]:
            self.q_result_text.insert(tk.END, f"  税额: {format_currency(0)} (免征)\n")
            self.q_result_text.insert(tk.END, f"  说明: 季度销售额未超过30万，免征增值税\n\n")
        else:
            self.q_result_text.insert(tk.END, f"  税额: {format_currency(vat['vat'])} (税率: {vat['rate']*100}%)\n\n")
        self.q_result_text.insert(tk.END, "【附加税】\n")
        self.q_result_text.insert(tk.END, f"  城市维护建设税: {format_currency(surtax['city_maintenance'])}\n")
        self.q_result_text.insert(tk.END, f"  教育费附加:     {format_currency(surtax['education_surcharge'])}\n")
        self.q_result_text.insert(tk.END, f"  地方教育附加:   {format_currency(surtax['local_education_surcharge'])}\n")
        self.q_result_text.insert(tk.END, f"  附加税合计:     {format_currency(surtax['total'])}\n\n")
        self.q_result_text.insert(tk.END, "【个人所得税（经营所得）】\n")
        self.q_result_text.insert(tk.END, f"  年度应纳税所得额: {format_currency(iit['taxable_income'])}\n")
        self.q_result_text.insert(tk.END, f"  适用税率:         {iit['tax_rate']*100}%\n")
        self.q_result_text.insert(tk.END, f"  年度应纳税额:     {format_currency(iit['annual_tax'])}\n")
        self.q_result_text.insert(tk.END, f"  季度预缴税额:     {format_currency(iit['quarterly_tax'])}\n\n")
        self.q_result_text.insert(tk.END, "-" * 48 + "\n")
        self.q_result_text.insert(tk.END, f"  季度应缴税费合计: {format_currency(total_tax)}\n")
        self.q_result_text.insert(tk.END, "=" * 48 + "\n")
        self.q_result_text.config(state=tk.DISABLED)

    # ==================== 页签2：印花税 ====================
    def _create_stamp_tab(self, parent):
        input_frame = ttk.LabelFrame(parent, text="输入数据", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="季度收入（元）").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.s_income_var = tk.StringVar(value="100000")
        ttk.Entry(input_frame, textvariable=self.s_income_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="实缴资本（元）").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.s_capital_var = tk.StringVar(value="0")
        ttk.Entry(input_frame, textvariable=self.s_capital_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="纳税人类型").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.s_taxpayer_var = tk.StringVar(value="small_scale")
        ttk.Radiobutton(input_frame, text="小规模纳税人", variable=self.s_taxpayer_var, value="small_scale").grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(input_frame, text="一般纳税人", variable=self.s_taxpayer_var, value="general").grid(row=2, column=2, sticky=tk.W, padx=5)

        ttk.Button(parent, text="计算印花税", command=self._calculate_stamp).pack(pady=10)

        result_frame = ttk.LabelFrame(parent, text="计算结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.s_result_text = tk.Text(result_frame, height=14, state=tk.DISABLED, font=("Consolas", 9))
        self.s_result_text.pack(fill=tk.BOTH, expand=True)

    def _calculate_stamp(self):
        from core.tax_calculator import format_currency
        try:
            income = float(self.s_income_var.get())
            capital = float(self.s_capital_var.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入合法数字金额")
            return

        is_small = self.s_taxpayer_var.get() == "small_scale"
        result = self.calc.calculate_stamp_tax(income, capital, is_small)

        self.s_result_text.config(state=tk.NORMAL)
        self.s_result_text.delete(1.0, tk.END)
        self.s_result_text.insert(tk.END, "=" * 48 + "\n")
        self.s_result_text.insert(tk.END, "          印花税估算\n")
        self.s_result_text.insert(tk.END, "=" * 48 + "\n\n")

        for item_key in ["contract", "books", "capital"]:
            item = result[item_key]
            self.s_result_text.insert(tk.END, f"【{item['title']}】\n")
            if item['rate'] > 0:
                self.s_result_text.insert(tk.END, f"  计税依据: {format_currency(income if item_key == 'contract' else capital)}\n")
                self.s_result_text.insert(tk.END, f"  税率: {item['rate']*10000/100:.4f}‰\n")
            self.s_result_text.insert(tk.END, f"  税额: {format_currency(item['amount'])} ({item['note']})\n\n")

        self.s_result_text.insert(tk.END, "-" * 48 + "\n")
        self.s_result_text.insert(tk.END, f"  印花税合计: {format_currency(result['total'])}\n")
        self.s_result_text.insert(tk.END, "=" * 48 + "\n")
        self.s_result_text.config(state=tk.DISABLED)

    # ==================== 页签3：社保计算 ====================
    def _create_social_security_tab(self, parent):
        input_frame = ttk.LabelFrame(parent, text="输入数据", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="月缴费基数（元）").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ss_base_var = tk.StringVar(value="5000")
        ttk.Entry(input_frame, textvariable=self.ss_base_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="说明: 按全国平均费率计算").grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5)

        ttk.Button(parent, text="计算社保", command=self._calculate_ss).pack(pady=10)

        result_frame = ttk.LabelFrame(parent, text="计算结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.ss_result_text = tk.Text(result_frame, height=14, state=tk.DISABLED, font=("Consolas", 9))
        self.ss_result_text.pack(fill=tk.BOTH, expand=True)

    def _calculate_ss(self):
        from core.tax_calculator import format_currency
        try:
            base = float(self.ss_base_var.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入合法数字金额")
            return

        result = self.calc.calculate_social_security(base)

        self.ss_result_text.config(state=tk.NORMAL)
        self.ss_result_text.delete(1.0, tk.END)
        self.ss_result_text.insert(tk.END, "=" * 48 + "\n")
        self.ss_result_text.insert(tk.END, "          社保缴费计算\n")
        self.ss_result_text.insert(tk.END, "=" * 48 + "\n\n")
        self.ss_result_text.insert(tk.END, f"  月缴费基数: {format_currency(result['monthly_base'])}\n\n")

        for name, label in [("pension", "养老保险"), ("medical", "医疗保险"), ("unemployment", "失业保险")]:
            item = result[name]
            self.ss_result_text.insert(tk.END, f"【{label}】\n")
            self.ss_result_text.insert(tk.END, f"  企业: {format_currency(item['employer'])}  个人: {format_currency(item['individual'])}  小计: {format_currency(item['total'])}\n\n")

        self.ss_result_text.insert(tk.END, "-" * 48 + "\n")
        self.ss_result_text.insert(tk.END, f"  企业承担合计: {format_currency(result['employer_total'])}\n")
        self.ss_result_text.insert(tk.END, f"  个人承担合计: {format_currency(result['individual_total'])}\n")
        self.ss_result_text.insert(tk.END, f"  当月总缴费:   {format_currency(result['grand_total'])}\n")
        self.ss_result_text.insert(tk.END, "=" * 48 + "\n")
        self.ss_result_text.config(state=tk.DISABLED)

    # ==================== 页签4：年度汇算 ====================
    def _create_annual_tab(self, parent):
        input_frame = ttk.LabelFrame(parent, text="输入数据", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="年度收入（元）").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.a_income_var = tk.StringVar(value="400000")
        ttk.Entry(input_frame, textvariable=self.a_income_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="年度费用（元）").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.a_expenses_var = tk.StringVar(value="240000")
        ttk.Entry(input_frame, textvariable=self.a_expenses_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="已预缴税额（元）").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.a_prepaid_var = tk.StringVar(value="10000")
        ttk.Entry(input_frame, textvariable=self.a_prepaid_var, width=20).grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(parent, text="计算汇算清缴", command=self._calculate_annual).pack(pady=10)

        result_frame = ttk.LabelFrame(parent, text="计算结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.a_result_text = tk.Text(result_frame, height=14, state=tk.DISABLED, font=("Consolas", 9))
        self.a_result_text.pack(fill=tk.BOTH, expand=True)

    def _calculate_annual(self):
        from core.tax_calculator import format_currency
        try:
            income = float(self.a_income_var.get())
            expenses = float(self.a_expenses_var.get())
            prepaid = float(self.a_prepaid_var.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入合法数字金额")
            return

        result = self.calc.calculate_iit_annual_reconciliation(income, expenses, prepaid)

        self.a_result_text.config(state=tk.NORMAL)
        self.a_result_text.delete(1.0, tk.END)
        self.a_result_text.insert(tk.END, "=" * 48 + "\n")
        self.a_result_text.insert(tk.END, "    个人所得税（经营所得）年度汇算清缴\n")
        self.a_result_text.insert(tk.END, "=" * 48 + "\n\n")
        self.a_result_text.insert(tk.END, f"  年度收入总额:     {format_currency(result['annual_income'])}\n")
        self.a_result_text.insert(tk.END, f"  年度成本费用:     {format_currency(result['annual_expenses'])}\n")
        self.a_result_text.insert(tk.END, f"  应纳税所得额:     {format_currency(result['taxable_income'])}\n")
        self.a_result_text.insert(tk.END, f"  适用税率:         {result['tax_rate']*100}%\n")
        self.a_result_text.insert(tk.END, f"  速算扣除数:       {result['quick_deduction']}\n")
        self.a_result_text.insert(tk.END, f"  年度应纳税额:     {format_currency(result['annual_tax'])}\n")
        self.a_result_text.insert(tk.END, f"  已预缴税额合计:   {format_currency(result['quarterly_prepaid'])}\n\n")
        self.a_result_text.insert(tk.END, "-" * 48 + "\n")

        diff = result['difference']
        if diff > 0:
            self.a_result_text.insert(tk.END, f"  ★ 应补缴税额:   {format_currency(diff)}\n")
        elif diff < 0:
            self.a_result_text.insert(tk.END, f"  ★ 应申请退税:   {format_currency(abs(diff))}\n")
        else:
            self.a_result_text.insert(tk.END, f"  ★ 无需补退税\n")

        self.a_result_text.insert(tk.END, "=" * 48 + "\n")
        self.a_result_text.insert(tk.END, "  汇算清缴截止日期: 次年3月31日前\n")
        self.a_result_text.insert(tk.END, "=" * 48 + "\n")
        self.a_result_text.config(state=tk.DISABLED)
