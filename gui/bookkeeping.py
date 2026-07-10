"""记账窗口"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from core.tax_calculator import TaxCalculator, format_currency


INCOME_CATEGORIES = [
    "销售收入",
    "服务收入",
    "其他收入",
]

EXPENSE_CATEGORIES = [
    "进货成本",
    "房租",
    "水电费",
    "快递费",
    "包装材料",
    "平台扣点",
    "员工工资",
    "办公用品",
    "维修费",
    "其他支出",
]


class BookkeepingWindow:
    """记账窗口"""

    def __init__(self, parent, data_manager, refresh_callback=None):
        self.dm = data_manager
        self.calc = TaxCalculator()
        self.refresh_callback = refresh_callback
        self.current_entity_id = None

        self.window = tk.Toplevel(parent)
        self.window.title("记账")
        self.window.geometry("900x600")
        self.window.minsize(800, 500)
        self.window.transient(parent)
        self.window.grab_set()

        self._create_widgets()
        self._load_entities()

    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="经营主体:").pack(side=tk.LEFT, padx=(0, 5))
        self.entity_var = tk.StringVar()
        self.entity_combo = ttk.Combobox(top_frame, textvariable=self.entity_var, width=25, state="readonly")
        self.entity_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.entity_combo.bind("<<ComboboxSelected>>", self._on_entity_change)

        ttk.Label(top_frame, text="年份:").pack(side=tk.LEFT, padx=(0, 5))
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        year_combo = ttk.Combobox(top_frame, textvariable=self.year_var, width=8, state="readonly")
        year_combo["values"] = [str(y) for y in range(2020, 2030)]
        year_combo.pack(side=tk.LEFT, padx=(0, 20))
        year_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        ttk.Label(top_frame, text="月份:").pack(side=tk.LEFT, padx=(0, 5))
        self.month_var = tk.StringVar(value="全部")
        month_values = ["全部"] + [str(m) for m in range(1, 13)]
        month_combo = ttk.Combobox(top_frame, textvariable=self.month_var, width=8, values=month_values, state="readonly")
        month_combo.pack(side=tk.LEFT)
        month_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        left_frame = ttk.LabelFrame(mid_frame, text="添加记录", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(left_frame, text="日期:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(left_frame, textvariable=self.date_var, width=15).grid(row=0, column=1, pady=5, sticky=tk.W)

        ttk.Label(left_frame, text="类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="income")
        type_frame = ttk.Frame(left_frame)
        type_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(type_frame, text="收入", variable=self.type_var, value="income", command=self._on_type_change).pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="支出", variable=self.type_var, value="expense", command=self._on_type_change).pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(left_frame, text="分类:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value="销售收入")
        self.category_combo = ttk.Combobox(left_frame, textvariable=self.category_var, width=18, state="readonly")
        self.category_combo["values"] = INCOME_CATEGORIES
        self.category_combo.grid(row=2, column=1, sticky=tk.W, pady=5)

        ttk.Label(left_frame, text="金额(元):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.amount_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=5)

        ttk.Label(left_frame, text="备注:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.desc_var, width=30).grid(row=4, column=1, sticky=tk.W, pady=5)

        ttk.Button(left_frame, text="添加记录", command=self._add_transaction).grid(row=5, column=1, pady=15, sticky=tk.W)

        right_frame = ttk.LabelFrame(mid_frame, text="季度汇总（自动算税）", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.summary_text = tk.Text(right_frame, height=15, state=tk.DISABLED, font=("Consolas", 9))
        self.summary_text.pack(fill=tk.BOTH, expand=True)

        bottom_frame = ttk.LabelFrame(main_frame, text="记账记录", padding=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="删除选中记录", command=self._delete_selected).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="刷新", command=self._refresh_list).pack(side=tk.LEFT, padx=10)

        columns = ("id", "date", "type", "category", "amount", "description")
        self.tree = ttk.Treeview(bottom_frame, columns=columns, show="headings", height=8)

        self.tree.heading("id", text="序号")
        self.tree.heading("date", text="日期")
        self.tree.heading("type", text="类型")
        self.tree.heading("category", text="分类")
        self.tree.heading("amount", text="金额")
        self.tree.heading("description", text="备注")

        self.tree.column("id", width=40)
        self.tree.column("date", width=100)
        self.tree.column("type", width=60)
        self.tree.column("category", width=100)
        self.tree.column("amount", width=100)
        self.tree.column("description", width=150)

        scrollbar = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_entities(self):
        """加载经营主体"""
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
        """主体切换"""
        entity_name = self.entity_var.get()
        if entity_name and entity_name in self.entities:
            self.current_entity_id = self.entities[entity_name]["id"]
            self._refresh_list()
            self._update_summary()

    def _on_type_change(self):
        """收支类型切换"""
        if self.type_var.get() == "income":
            self.category_combo["values"] = INCOME_CATEGORIES
            self.category_var.set("销售收入")
        else:
            self.category_combo["values"] = EXPENSE_CATEGORIES
            self.category_var.set("进货成本")

    def _on_filter_change(self, event=None):
        """筛选条件变化"""
        self._refresh_list()
        self._update_summary()

    def _add_transaction(self):
        """添加记账记录"""
        if not self.current_entity_id:
            messagebox.showwarning("提示", "请先选择经营主体")
            return

        trans_date = self.date_var.get().strip()
        try:
            datetime.strptime(trans_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("提示", "日期格式错误，请使用 YYYY-MM-DD 格式")
            return

        amount_str = self.amount_var.get().strip()
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的金额（大于0）")
            return

        trans_type = self.type_var.get()
        category = self.category_var.get()
        description = self.desc_var.get().strip()

        self.dm.add_transaction(self.current_entity_id, trans_date, trans_type, category, amount, description)

        self.amount_var.set("")
        self.desc_var.set("")

        self._refresh_list()
        self._update_summary()

        type_text = "收入" if trans_type == "income" else "支出"
        messagebox.showinfo("成功", f"已添加{type_text}记录: {category} ¥{amount:,.2f}")

    def _refresh_list(self):
        """刷新记录列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.current_entity_id:
            return

        year_str = self.year_var.get()
        month_str = self.month_var.get()

        year = int(year_str) if year_str else None
        month = int(month_str) if month_str and month_str != "全部" else None

        records = self.dm.get_transactions(self.current_entity_id, year, month)

        self._trans_id_map = {}
        for idx, r in enumerate(records, start=1):
            type_text = "收入" if r["trans_type"] == "income" else "支出"
            item_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    idx,
                    r["trans_date"],
                    type_text,
                    r["category"],
                    f"¥{r['amount']:,.2f}",
                    r.get("description", ""),
                ),
            )
            self._trans_id_map[item_id] = r["id"]

    def _update_summary(self):
        """更新汇总统计（含自动算税）"""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)

        if not self.current_entity_id:
            self.summary_text.insert(tk.END, "请先选择经营主体")
            self.summary_text.config(state=tk.DISABLED)
            return

        year_str = self.year_var.get()
        year = int(year_str) if year_str else datetime.now().year

        entity = self.dm.get_entity(self.current_entity_id)
        is_small_scale = entity.get("taxpayer_type", "small_scale") == "small_scale"

        self.summary_text.insert(tk.END, f"  {year}年度汇总（自动算税）\n")
        self.summary_text.insert(tk.END, "=" * 45 + "\n\n")

        total_income = 0
        total_expense = 0
        total_tax = 0

        for q in range(1, 5):
            summary = self.dm.get_quarterly_summary(self.current_entity_id, year, q)
            total_income += summary["income"]
            total_expense += summary["expense"]

            if summary["income"] > 0 or summary["expense"] > 0:
                tax_result = self.calc.calculate_all_quarterly(summary["income"], summary["expense"])
                total_tax += tax_result["total_quarterly_tax"]

                self.summary_text.insert(tk.END, f"  第{q}季度:\n")
                self.summary_text.insert(tk.END, f"    收入: ¥{summary['income']:>12,.2f}\n")
                self.summary_text.insert(tk.END, f"    支出: ¥{summary['expense']:>12,.2f}\n")
                self.summary_text.insert(tk.END, f"    净利: ¥{summary['profit']:>12,.2f}\n")
                self.summary_text.insert(tk.END, f"    ——— 应缴税费 ———\n")

                vat = tax_result["vat"]
                if vat["is_exempt"]:
                    self.summary_text.insert(tk.END, "    增值税: 免征\n")
                else:
                    self.summary_text.insert(tk.END, f"    增值税: ¥{vat['vat']:>10,.2f}\n")

                self.summary_text.insert(tk.END, f"    附加税: ¥{tax_result['surtax']['total']:>10,.2f}\n")
                self.summary_text.insert(tk.END, f"    个税:   ¥{tax_result['iit']['quarterly_tax']:>10,.2f}\n")
                self.summary_text.insert(tk.END, f"    小计:   ¥{tax_result['total_quarterly_tax']:>10,.2f}\n\n")

        self.summary_text.insert(tk.END, "-" * 45 + "\n")
        self.summary_text.insert(tk.END, "  全年合计:\n")
        self.summary_text.insert(tk.END, f"    总收入: ¥{total_income:>10,.2f}\n")
        self.summary_text.insert(tk.END, f"    总支出: ¥{total_expense:>10,.2f}\n")
        self.summary_text.insert(tk.END, f"    净利润: ¥{total_income - total_expense:>10,.2f}\n")
        self.summary_text.insert(tk.END, f"    ———————————————————\n")
        self.summary_text.insert(tk.END, f"    全年应缴税费: ¥{total_tax:>10,.2f}\n")
        self.summary_text.insert(tk.END, f"    税后净收入: ¥{total_income - total_expense - total_tax:>10,.2f}\n")

        self.summary_text.config(state=tk.DISABLED)

    def _delete_selected(self):
        """删除选中记录"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的记录")
            return

        if messagebox.askyesno("确认", "确定要删除选中的记录吗？"):
            for item in selected:
                trans_id = self.tree.item(item)["values"][0]
                self.dm.delete_transaction(trans_id)
            self._refresh_list()
            self._update_summary()
