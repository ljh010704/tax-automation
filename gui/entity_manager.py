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

        self._create_widgets()
        self._refresh_list()

    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        # 按钮行
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkButton(btn_frame, text="+ 添加主体", width=100, height=BUTTON_HEIGHT,
                       font=FONT_BUTTON, corner_radius=CORNER_RADIUS,
                       fg_color=COLORS["primary"][0], hover_color=COLORS["primary_hover"][0],
                       command=self._add_entity).pack(side="left", padx=(0, PAD_SM))
        ctk.CTkButton(btn_frame, text="编辑", width=80, height=BUTTON_HEIGHT,
                       font=FONT_BODY, corner_radius=CORNER_RADIUS,
                       command=self._edit_entity).pack(side="left", padx=PAD_XS)
        ctk.CTkButton(btn_frame, text="删除", width=80, height=BUTTON_HEIGHT,
                       font=FONT_BODY, corner_radius=CORNER_RADIUS,
                       fg_color=COLORS["danger"][0], hover_color=COLORS["danger_hover"][0],
                       command=self._delete_entity).pack(side="left", padx=PAD_XS)

        # 列表标题
        header_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["gray_light"][0], corner_radius=CORNER_RADIUS)
        header_frame.pack(fill="x", pady=(0, PAD_XS))
        headers = [("序号", 40), ("名称", 180), ("信用代码", 150), ("类型", 70), ("法人", 60), ("状态", 60), ("省份", 70)]
        for idx, (text, width) in enumerate(headers):
            ctk.CTkLabel(header_frame, text=text, font=FONT_SMALL, width=width,
                         text_color=COLORS["text_light"][0]).grid(row=0, column=idx, padx=PAD_XS, pady=PAD_SM)

        # 列表区域
        self.list_frame = ctk.CTkScrollableFrame(main_frame, fg_color=COLORS["card"][0],
                                                  corner_radius=CORNER_RADIUS, border_width=1, border_color=COLORS["border"][0])
        self.list_frame.pack(fill="both", expand=True)
        self.list_frame.grid_columnconfigure(1, weight=1)

    def _refresh_list(self):
        """刷新列表"""
        for w in self.list_frame.winfo_children():
            w.destroy()
        self._id_map = {}

        entities = self.dm.get_entities()
        taxpayer_map = {"small_scale": "小规模", "general": "一般纳税人"}
        status_colors = {"正常": COLORS["success"][0], "注销": COLORS["warning"][0], "吊销": COLORS["danger"][0]}

        for idx, entity in enumerate(entities, start=1):
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=PAD_XS, padx=PAD_XS)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=str(idx), font=FONT_SMALL, width=40, height=28,
                         corner_radius=14, fg_color=COLORS["primary"][0], text_color="white").grid(row=0, column=0, padx=(0, PAD_SM))

            name_frame = ctk.CTkFrame(row, fg_color="transparent")
            name_frame.grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(name_frame, text=entity["name"], font=FONT_BODY, text_color=COLORS["text"][0]).pack(side="left")

            ctk.CTkLabel(row, text=entity.get("credit_code", ""), font=FONT_SMALL,
                         width=150, text_color=COLORS["text_light"][0]).grid(row=0, column=2, padx=PAD_XS)

            ctk.CTkLabel(row, text=entity.get("entity_type", ""), font=FONT_SMALL,
                         width=70, text_color=COLORS["text"][0]).grid(row=0, column=3, padx=PAD_XS)

            ctk.CTkLabel(row, text=entity.get("legal_representative", ""), font=FONT_SMALL,
                         width=60, text_color=COLORS["text"][0]).grid(row=0, column=4, padx=PAD_XS)

            status = entity.get("business_status", "正常")
            sc = status_colors.get(status, COLORS["gray"][0])
            ctk.CTkLabel(row, text=status, font=FONT_SMALL, width=50, height=22,
                         corner_radius=6, fg_color=sc, text_color="white").grid(row=0, column=5, padx=PAD_XS)

            ctk.CTkLabel(row, text=entity.get("province", ""), font=FONT_SMALL,
                         width=70, text_color=COLORS["text"][0]).grid(row=0, column=6, padx=PAD_XS)

            self._id_map[str(idx)] = entity["id"]

    def _get_selected_entity(self):
        """获取选中的主体信息 - 简化:返回列表第一个或指定"""
        entities = self.dm.get_entities()
        return entities[0] if entities else None

    def _add_entity(self):
        """添加经营主体"""
        EntityEditDialog(self.window, self.dm, callback=self._on_edit_done)

    def _edit_entity(self):
        """编辑经营主体"""
        entity = self._get_selected_entity()
        if not entity:
            messagebox.showwarning("提示", "请先添加经营主体")
            return
        EntityEditDialog(self.window, self.dm, entity=entity, callback=self._on_edit_done)

    def _delete_entity(self):
        """删除经营主体"""
        entity = self._get_selected_entity()
        if not entity:
            messagebox.showwarning("提示", "请先添加经营主体")
            return
        if messagebox.askyesno("确认删除", "确定要删除【" + entity["name"] + "】吗？"):
            try:
                self.dm.delete_entity(entity["id"])
                self._refresh_list()
                if self.refresh_callback:
                    self.refresh_callback()
                messagebox.showinfo("提示", "已删除")
            except Exception as e:
                messagebox.showerror("错误", "删除失败: " + str(e))

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

        self.window = ctk.CTkToplevel(parent)
        self.window.title("编辑经营主体" if entity else "添加经营主体")
        self.window.geometry("520x500")
        self.window.grab_set()

        self._create_widgets()
        if entity:
            self._load_entity(entity)

    def _create_widgets(self):
        """创建编辑表单"""
        main_frame = ctk.CTkScrollableFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        self.name_var = ctk.StringVar()
        self.credit_code_var = ctk.StringVar()
        self.entity_type_var = ctk.StringVar(value="个体工商户")
        self.taxpayer_type_var = ctk.StringVar(value="小规模纳税人")
        self.legal_rep_var = ctk.StringVar()
        self.biz_status_var = ctk.StringVar(value="正常")
        self.tax_status_var = ctk.StringVar(value="正常")
        self.province_var = ctk.StringVar()
        self.city_var = ctk.StringVar()
        self.tax_authority_var = ctk.StringVar()
        self.login_url_var = ctk.StringVar()
        self.taxpayer_type_map = {"小规模纳税人": "small_scale", "一般纳税人": "general"}

        row = 0
        self._add_field(main_frame, "企业名称 *", row, self.name_var, 40)
        row += 1
        code_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        code_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=PAD_SM)
        code_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(code_frame, text="统一社会信用代码 *", font=FONT_BODY, width=140, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(code_frame, textvariable=self.credit_code_var, width=200, height=ENTRY_HEIGHT,
                     corner_radius=CORNER_RADIUS).grid(row=0, column=1, padx=PAD_SM)
        ctk.CTkButton(code_frame, text="查询", width=70, height=ENTRY_HEIGHT,
                       corner_radius=CORNER_RADIUS, font=FONT_SMALL,
                       command=self._query_business_info).grid(row=0, column=2, padx=PAD_XS)
        row += 1
        self._add_combo(main_frame, "主体类型", row, self.entity_type_var,
                        ["个体工商户", "有限公司", "个人独资企业", "合伙企业"])
        row += 1
        self._add_combo(main_frame, "纳税人类型", row, self.taxpayer_type_var,
                        ["小规模纳税人", "一般纳税人"])
        row += 1
        self._add_field(main_frame, "法定代表人", row, self.legal_rep_var, 20)
        row += 1
        self._add_combo(main_frame, "企业状态", row, self.biz_status_var, ["正常", "注销", "吊销"])
        row += 1
        self._add_combo(main_frame, "纳税人状态", row, self.tax_status_var, ["正常", "非正常", "注销"])
        row += 1
        self._add_field(main_frame, "省份", row, self.province_var, 15)
        row += 1
        self._add_field(main_frame, "城市", row, self.city_var, 15)
        row += 1
        self._add_field(main_frame, "主管税务机关", row, self.tax_authority_var, 30)
        row += 1
        self._add_field(main_frame, "电子税务局", row, self.login_url_var, 40)
        row += 1

        # 保存按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, pady=PAD_LG)
        ctk.CTkButton(btn_frame, text="保存", width=120, height=BUTTON_HEIGHT,
                       font=FONT_BUTTON, corner_radius=CORNER_RADIUS,
                       fg_color=COLORS["success"][0], hover_color=COLORS["success_hover"][0],
                       command=self._save).pack()

    def _add_field(self, parent, label, row, var, width):
        """添加输入字段"""
        parent.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(parent, text=label, font=FONT_BODY, width=140, anchor="w").grid(row=row, column=0, sticky="w", pady=PAD_SM)
        ctk.CTkEntry(parent, textvariable=var, width=250, height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS).grid(row=row, column=1, sticky="w", padx=PAD_SM, pady=PAD_SM)

    def _add_combo(self, parent, label, row, var, values):
        """添加下拉选择"""
        parent.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(parent, text=label, font=FONT_BODY, width=140, anchor="w").grid(row=row, column=0, sticky="w", pady=PAD_SM)
        ctk.CTkComboBox(parent, variable=var, values=values, width=180, height=ENTRY_HEIGHT,
                        corner_radius=CORNER_RADIUS).grid(row=row, column=1, sticky="w", padx=PAD_SM, pady=PAD_SM)

    def _load_entity(self, entity):
        """加载已有经营主体数据"""
        self.name_var.set(entity.get("name", ""))
        self.credit_code_var.set(entity.get("credit_code", ""))
        et = entity.get("entity_type", "")
        if et:
            self.entity_type_var.set(et)
        tt = entity.get("taxpayer_type", "small_scale")
        rev = {v: k for k, v in self.taxpayer_type_map.items()}
        self.taxpayer_type_var.set(rev.get(tt, "小规模纳税人"))
        self.legal_rep_var.set(entity.get("legal_representative", ""))
        self.biz_status_var.set(entity.get("business_status", "正常"))
        self.tax_status_var.set(entity.get("taxpayer_status", "正常"))
        self.province_var.set(entity.get("province", ""))
        self.city_var.set(entity.get("city", ""))
        self.tax_authority_var.set(entity.get("tax_authority", ""))
        self.login_url_var.set(entity.get("login_url", ""))

    def _save(self):
        """保存数据"""
        name = self.name_var.get().strip()
        credit_code = self.credit_code_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入企业名称")
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
            messagebox.showerror("保存失败", "出错: " + str(e))

    def _query_business_info(self):
        """查询企业信息"""
        credit_code = self.credit_code_var.get().strip()
        if not credit_code:
            messagebox.showwarning("提示", "请先输入统一社会信用代码")
            return
        if len(credit_code) != 18:
            messagebox.showwarning("提示", "统一社会信用代码应为18位")
            return

        messagebox.showinfo("开始查询", "即将打开浏览器访问天眼查查询企业信息\n\n首次使用需要登录天眼查\n登录后状态会自动保存")

        def run_query():
            import asyncio
            from core.business_query import BusinessQuery

            async def _query():
                query = BusinessQuery()
                try:
                    await query.start()
                    return await query.query(credit_code)
                finally:
                    await query.stop()

            def callback(result):
                if result:
                    filled = []
                    if result.get("name"):
                        self.name_var.set(result["name"])
                        filled.append("企业名称")
                    if result.get("legal_representative"):
                        self.legal_rep_var.set(result["legal_representative"])
                        filled.append("法定代表人/经营者")
                    if result.get("business_status"):
                        st = result["business_status"]
                        if st == "正常":
                            self.biz_status_var.set("正常")
                        elif st == "注销":
                            self.biz_status_var.set("注销")
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
                        messagebox.showinfo("查询完成", "已自动填充: " + ", ".join(filled))
                    else:
                        messagebox.showwarning("提示", "未能提取信息，请手动填写")

            import threading
            def thread_fn():
                result = asyncio.run(_query())
                self.window.after(0, lambda: callback(result))
            threading.Thread(target=thread_fn, daemon=True).start()

        run_query()
