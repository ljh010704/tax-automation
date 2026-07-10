"""经营管理主体窗口"""

import tkinter as tk
from tkinter import ttk, messagebox


class EntityManagerWindow:
    """经营管理主体窗口"""

    def __init__(self, parent, data_manager, refresh_callback=None):
        self.dm = data_manager
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)
        self.window.title("经营管理主体管理")
        self.window.geometry("700x500")
        self.window.transient(parent)
        self.window.grab_set()

        self._create_widgets()
        self._refresh_list()

    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="添加主体", command=self._add_entity).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑主体", command=self._edit_entity).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除主体", command=self._delete_entity).pack(side=tk.LEFT, padx=5)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "credit_code", "entity_type", "taxpayer_type", "legal_rep", "biz_status", "tax_status", "province")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        self.tree.heading("id", text="序号")
        self.tree.heading("name", text="名称")
        self.tree.heading("credit_code", text="统一社会信用代码")
        self.tree.heading("entity_type", text="主体类型")
        self.tree.heading("taxpayer_type", text="纳税人类型")
        self.tree.heading("legal_rep", text="法人")
        self.tree.heading("biz_status", text="企业状态")
        self.tree.heading("tax_status", text="纳税人状态")
        self.tree.heading("province", text="省份")

        self.tree.column("id", width=35, minwidth=35)
        self.tree.column("name", width=220, minwidth=150)
        self.tree.column("credit_code", width=160, minwidth=100)
        self.tree.column("entity_type", width=80, minwidth=60)
        self.tree.column("taxpayer_type", width=100, minwidth=80)
        self.tree.column("legal_rep", width=70, minwidth=50)
        self.tree.column("biz_status", width=70, minwidth=50)
        self.tree.column("tax_status", width=90, minwidth=60)
        self.tree.column("province", width=80, minwidth=50)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar_h.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)

    def _refresh_list(self):
        """刷新列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._id_map = {}

        taxpayer_map = {"small_scale": "小规模纳税人", "general": "一般纳税人"}

        entities = self.dm.get_entities()
        for idx, entity in enumerate(entities, start=1):
            taxpayer_type = entity.get("taxpayer_type", "")
            item_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    idx,
                    entity["name"],
                    entity["credit_code"],
                    entity["entity_type"],
                    taxpayer_map.get(taxpayer_type, taxpayer_type),
                    entity.get("legal_representative", ""),
                    entity.get("business_status", "正常"),
                    entity.get("taxpayer_status", "正常"),
                    entity.get("province", ""),
                ),
            )
            self._id_map[item_id] = entity["id"]

    def _add_entity(self):
        """添加经营主体"""
        EntityEditDialog(self.window, self.dm, callback=self._on_edit_done)

    def _edit_entity(self):
        """编辑经营主体"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个经营主体")
            return

        entity_id = self._id_map.get(selected[0], self.tree.item(selected[0])["values"][0])
        entity = self.dm.get_entity(entity_id)
        if entity:
            EntityEditDialog(self.window, self.dm, entity=entity, callback=self._on_edit_done)

    def _delete_entity(self):
        """删除经营主体"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个经营主体")
            return

        entity_id = self._id_map.get(selected[0], self.tree.item(selected[0])["values"][0])
        entity_name = self.tree.item(selected[0])["values"][1]

        if messagebox.askyesno("确认", f"确定要删除经营主体 '{entity_name}' 吗？"):
            self.dm.delete_entity(entity_id)
            self._refresh_list()
            if self.refresh_callback:
                self.refresh_callback()

    def _on_edit_done(self):
        """编辑完成回调"""
        self._refresh_list()
        if self.refresh_callback:
            self.refresh_callback()


class EntityEditDialog:
    """经营主体编辑对话框"""

    def __init__(self, parent, data_manager, entity=None, callback=None):
        self.dm = data_manager
        self.entity = entity
        self.callback = callback

        self.window = tk.Toplevel(parent)
        self.window.title("编辑经营主体" if entity else "添加经营主体")
        self.window.geometry("580x520")
        self.window.transient(parent)
        self.window.grab_set()

        self._create_widgets()

        if entity:
            self._load_entity(entity)

    def _create_widgets(self):
        """创建编辑表单"""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        ttk.Label(main_frame, text="企业名称 *").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=row, column=1, columnspan=2, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="统一社会信用代码 *").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.credit_code_var = tk.StringVar()
        credit_entry = ttk.Entry(main_frame, textvariable=self.credit_code_var, width=25)
        credit_entry.grid(row=row, column=1, pady=5, sticky=tk.W)
        ttk.Button(main_frame, text="查询企业信息", command=self._query_business_info).grid(row=row, column=2, padx=5, pady=5)
        ttk.Button(main_frame, text="重新登录天眼查", command=self._clear_login).grid(row=row, column=3, padx=5, pady=5)

        row += 1
        ttk.Label(main_frame, text="主体类型").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.entity_type_var = tk.StringVar(value="个体工商户")
        entity_type_combo = ttk.Combobox(main_frame, textvariable=self.entity_type_var, width=15, state="readonly")
        entity_type_combo["values"] = ["个体工商户", "有限公司", "个人独资企业", "合伙企业"]
        entity_type_combo.grid(row=row, column=1, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="纳税人类型").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.taxpayer_type_var = tk.StringVar(value="小规模纳税人")
        self.taxpayer_type_map = {"小规模纳税人": "small_scale", "一般纳税人": "general"}
        taxpayer_combo = ttk.Combobox(main_frame, textvariable=self.taxpayer_type_var, width=15, state="readonly")
        taxpayer_combo["values"] = list(self.taxpayer_type_map.keys())
        taxpayer_combo.grid(row=row, column=1, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="法定代表人").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.legal_rep_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.legal_rep_var, width=20).grid(row=row, column=1, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="企业状态").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.biz_status_var = tk.StringVar(value="正常")
        ttk.Combobox(main_frame, textvariable=self.biz_status_var, values=["正常", "注销", "吊销"], width=10, state="readonly").grid(row=row, column=1, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="纳税人状态").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.tax_status_var = tk.StringVar(value="正常")
        ttk.Combobox(main_frame, textvariable=self.tax_status_var, values=["正常", "非正常", "注销"], width=10, state="readonly").grid(row=row, column=1, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="省份").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.province_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.province_var, width=15).grid(row=row, column=1, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="城市").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.city_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.city_var, width=15).grid(row=row, column=1, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="主管税务机关").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.tax_authority_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.tax_authority_var, width=30).grid(row=row, column=1, columnspan=2, pady=5, sticky=tk.W)

        row += 1
        ttk.Label(main_frame, text="电子税务局").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.login_url_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.login_url_var, width=40).grid(row=row, column=1, columnspan=2, pady=5, sticky=tk.W)

        row += 1
        ttk.Button(main_frame, text="保存", command=self._save).grid(row=row, column=1, pady=15, sticky=tk.W)

    def _load_entity(self, entity):
        """加载已有经营主体数据"""
        self.name_var.set(entity.get("name", ""))
        self.credit_code_var.set(entity.get("credit_code", ""))

        entity_type = entity.get("entity_type", "")
        if entity_type:
            self.entity_type_var.set(entity_type)

        taxpayer_type = entity.get("taxpayer_type", "small_scale")
        reverse_map = {v: k for k, v in self.taxpayer_type_map.items()}
        self.taxpayer_type_var.set(reverse_map.get(taxpayer_type, "小规模纳税人"))

        self.legal_rep_var.set(entity.get("legal_representative", ""))
        self.biz_status_var.set(entity.get("business_status", "正常"))
        self.tax_status_var.set(entity.get("taxpayer_status", "正常"))
        self.province_var.set(entity.get("province", ""))
        self.city_var.set(entity.get("city", ""))
        self.tax_authority_var.set(entity.get("tax_authority", ""))
        self.login_url_var.set(entity.get("login_url", ""))

    def _query_business_info(self):
        """查询企业信息（半自动）"""
        credit_code = self.credit_code_var.get().strip()
        if not credit_code:
            messagebox.showwarning("提示", "请先输入统一社会信用代码")
            return

        if len(credit_code) != 18:
            messagebox.showwarning("提示", "统一社会信用代码应为18位")
            return

        messagebox.showinfo(
            "开始查询",
            "即将打开浏览器访问天眼查查询企业信息\n\n"
            "首次使用需要登录天眼查（微信/手机号均可）\n"
            "登录后状态会自动保存，以后不用再登录\n\n"
            "程序会自动提取以下信息：\n"
            "- 企业名称\n"
            "- 法定代表人\n"
            "- 经营状态\n"
            "- 省份、城市\n"
            "- 主管税务机关\n"
            "- 电子税务局网址\n\n"
            "请等待浏览器打开...",
        )

        import threading

        def run_query():
            import asyncio
            from core.business_query import BusinessQuery

            async def _query():
                query = BusinessQuery()
                try:
                    await query.start()
                    result = await query.query(credit_code)
                    return result
                finally:
                    await query.stop()

            return asyncio.run(_query())

        def callback(result):
            if result:
                filled = []
                if result.get("name"):
                    self.name_var.set(result["name"])
                    filled.append("企业名称")
                if result.get("legal_representative"):
                    self.legal_rep_var.set(result["legal_representative"])
                    filled.append("法定代表人")
                if result.get("business_status"):
                    self.biz_status_var.set(result["business_status"])
                    filled.append("企业状态")
                if result.get("entity_type"):
                    self.entity_type_var.set(result["entity_type"])
                    filled.append("主体类型")
                if result.get("province"):
                    self.province_var.set(result["province"])
                    filled.append("省份")
                if result.get("city"):
                    self.city_var.set(result["city"])
                    filled.append("城市")
                if result.get("tax_authority"):
                    self.tax_authority_var.set(result["tax_authority"])
                    filled.append("主管税务机关")
                if result.get("login_url"):
                    self.login_url_var.set(result["login_url"])
                    filled.append("电子税务局")

                if filled:
                    messagebox.showinfo("查询完成", f"已自动填充：{', '.join(filled)}\n请检查信息是否正确")
                else:
                    failure_reason = result.get("failure_reason", "extract_failed")
                    hint = {
                        "extract_failed": "页面结构变化或未登录，信息提取失败，请手动核对。",
                        "timeout": "查询超时，请检查网络后重试，或手动填写。",
                        "captcha_or_risk_control": "疑似触发验证码或风控，请先在浏览器中完成验证后再试。",
                        "login_required": "天眼查登录已过期，请在弹出的浏览器中重新登录，登录后系统会自动重试查询。",
                        "unexpected_error": "查询过程出错，请检查网络或手动填写。",
                    }.get(failure_reason, "未能自动提取信息，请手动填写。")
                    messagebox.showwarning("查询提示", hint)
            else:
                messagebox.showwarning("查询提示", "查询失败，请检查网络后重试，或先手动填写。")

        def run_in_thread():
            try:
                result = run_query()
                self.window.after(0, lambda: callback(result))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.window.after(0, lambda: messagebox.showerror("查询失败", f"查询过程出错，请稍后重试。\n错误信息: {e}"))

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    def _clear_login(self):
        """清除天眼查登录数据，下次查询时需重新登录"""
        from tkinter import messagebox
        result = messagebox.askyesno(
            "重新登录天眼查",
            "清除后下次查询会重新弹出登录窗口，是否继续？"
        )
        if not result:
            return

        import os
        import shutil
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "browser_data")
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir, ignore_errors=True)
        messagebox.showinfo("已清除", "登录数据已清除。下次点击查询企业信息时，会弹出登录窗口。")

    def _save(self):
        """保存数据"""
        name = self.name_var.get().strip()
        credit_code = self.credit_code_var.get().strip()

        if not name:
            messagebox.showwarning("提示", "请输入名称")
            return
        if not credit_code:
            messagebox.showwarning("提示", "请输入统一社会信用代码")
            return

        entity = {
            "name": name,
            "credit_code": credit_code,
            "entity_type": self.entity_type_var.get(),
            "taxpayer_type": self.taxpayer_type_map.get(self.taxpayer_type_var.get(), "small_scale"),
            "legal_representative": self.legal_rep_var.get().strip(),
            "business_status": self.biz_status_var.get(),
            "taxpayer_status": self.tax_status_var.get(),
            "province": self.province_var.get().strip(),
            "city": self.city_var.get().strip(),
            "tax_authority": self.tax_authority_var.get().strip(),
            "login_url": self.login_url_var.get().strip(),
        }

        try:
            if self.entity:
                self.dm.update_entity(self.entity["id"], entity)
            else:
                self.dm.add_entity(entity)
            self.window.destroy()
            if self.callback:
                self.callback()
        except Exception as e:
            messagebox.showerror("保存失败", f"保存过程出错，请检查输入后重试。\n错误信息: {e}")


