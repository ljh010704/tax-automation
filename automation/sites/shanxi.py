"""山西省电子税务局适配器
1.0 版本：半自动申报流程。
程序自动填表，最后仍需用户在浏览器中确认并提交。
"""

from automation.sites.base_adapter import BaseSiteAdapter


class ShanxiAdapter(BaseSiteAdapter):
    """山西省电子税务局适配器（1.0 半自动）"""

    LOGIN_URL = "https://etax.shanxi.chinatax.gov.cn"

    async def login(self, url: str = None):
        """登录山西省电子税务局"""
        login_url = url or self.LOGIN_URL
        await self.browser.navigate(login_url)

        print("请在浏览器中完成登录（支持CA证书/短信验证/人脸识别）")
        print("登录完成后程序将继续...")

        await self.browser.wait_for_login(timeout=300)

    async def navigate_to_tax_declaration(self, tax_type: str):
        """导航到申报页面"""
        menu_selectors = {
            "vat": "增值税申报",
            "iit": "个人所得税申报",
            "surtax": "附加税申报",
        }

        menu_text = menu_selectors.get(tax_type)
        if menu_text:
            print(f"导航到{menu_text}页面...")

    async def fill_vat_declaration(self, data: dict):
        """填写增值税申报表"""
        print("填写增值税申报表...")

        if "sales_amount" in data:
            await self.browser.fill_form_field(
                "#salesAmount",
                str(data["sales_amount"]),
            )

        if "tax_amount" in data:
            await self.browser.fill_form_field(
                "#taxAmount",
                str(data["tax_amount"]),
            )

    async def fill_iit_declaration(self, data: dict):
        """填写个人所得税（经营所得）申报表"""
        print("填写个人所得税申报表...")

        if "income" in data:
            await self.browser.fill_form_field(
                "#incomeAmount",
                str(data["income"]),
            )

        if "expenses" in data:
            await self.browser.fill_form_field(
                "#expenseAmount",
                str(data["expenses"]),
            )

    async def fill_surtax_declaration(self, data: dict):
        """填写附加税申报表"""
        print("填写附加税申报表...")

    async def request_user_confirm_before_submit(self, package) -> None:
        """提交前暂停，等待用户确认"""
        print("已自动填表完成，请在浏览器中核对申报信息。")
        print("确认无误后，请手动点击提交按钮完成申报。")
        await self.browser.take_screenshot("tax-automation/declaration_prefilled.png")

    async def submit_declaration(self):
        """提交申报"""
        print("提交申报...")
        await self.browser.click_button("#submitBtn")

        print("等待提交结果...")

    async def get_declaration_status(self) -> dict:
        """获取申报状态"""
        return {"status": "pending", "message": "待提交"}
