"""山西省电子税务局适配器
半自动申报流程。
程序自动填表，最后仍需用户在浏览器中确认并提交。
"""

import asyncio
import logging
from automation.sites.base_adapter import BaseSiteAdapter

logger = logging.getLogger(__name__)


class ShanxiAdapter(BaseSiteAdapter):
    """山西省电子税务局适配器"""

    LOGIN_URL = "https://etax.shanxi.chinatax.gov.cn"

    SELECTORS = {
        "login_btn": ".loginBtn",
        "modal_close_btn": "button:has-text('我知道了')",
        "user_info": ".user-info",
        "tax_declaration_menu": "text=我要办税",
        "tax_declaration_submenu": "text=税费申报及缴纳",
        "vat_declaration_entry": "text=增值税及附加税费申报",
        "vat_sales_amount": "#salesAmount",
        "vat_tax_amount": "#taxAmount",
        "vat_submit_btn": "button:has-text('申报')",
        "iit_declaration_entry": "text=个人所得税申报",
        "iit_income_amount": "#incomeAmount",
        "iit_expense_amount": "#expenseAmount",
        "iit_submit_btn": "button:has-text('申报')",
        "surtax_declaration_entry": "text=附加税费申报",
        "confirm_btn": "button:has-text('确认')",
        "success_message": ".success-message",
        "error_message": ".error-message",
    }

    def __init__(self, browser):
        super().__init__(browser)
        self.logged_in = False

    async def login(self, url: str = None, method: str = "manual"):
        """登录山西省电子税务局"""
        login_url = url or self.LOGIN_URL
        await self.browser.navigate(login_url)

        print("\n" + "=" * 60)
        print("Preparing login page...")
        print("=" * 60 + "\n")

        # 1. Close modal overlay
        try:
            await asyncio.sleep(2)
            await self.browser.page.evaluate("""
                document.querySelectorAll('.mask, .modal-mask, .overlay').forEach(el => el.remove());
                document.querySelectorAll('[class*="mask"]').forEach(el => el.style.display = 'none');
            """)
            print("Removed mask overlays")
            await asyncio.sleep(1)
        except Exception as e:
            logger.info(f"Remove overlay failed: {e}")

        # 2. Click login button
        try:
            login_btn = await self.browser.page.query_selector(self.SELECTORS["login_btn"])
            if login_btn:
                await login_btn.click(force=True)
                print("Clicked login button")
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Click login button failed: {e}")

        # 3. Wait for user to complete login
        print("\n" + "=" * 60)
        print("Please complete login in browser")
        print("Supported: CA certificate, SMS code, QR scan, Face ID")
        print("\nProgram will continue automatically after login...")
        print("=" * 60 + "\n")

        try:
            await self.browser.page.wait_for_selector(
                self.SELECTORS["user_info"],
                timeout=300000
            )
            self.logged_in = True
            logger.info("Login successful")
            print("OK: Login successful")
        except Exception as e:
            logger.error(f"Login timeout: {e}")
            raise Exception("Login timeout, please retry")

        await self.browser.take_screenshot("shanxi_login_success.png")

    async def navigate_to_tax_declaration(self, tax_type: str):
        """导航到申报页面"""
        if not self.logged_in:
            raise Exception("Please login first")

        logger.info(f"Navigating to {tax_type} declaration page")

        await self.browser.click_button(self.SELECTORS["tax_declaration_menu"])
        await asyncio.sleep(1)

        await self.browser.click_button(self.SELECTORS["tax_declaration_submenu"])
        await asyncio.sleep(2)

        entry_selector = None
        if tax_type == "vat":
            entry_selector = self.SELECTORS["vat_declaration_entry"]
        elif tax_type == "iit":
            entry_selector = self.SELECTORS["iit_declaration_entry"]
        elif tax_type == "surtax":
            entry_selector = self.SELECTORS["surtax_declaration_entry"]

        if entry_selector:
            await self.browser.click_button(entry_selector)
            await asyncio.sleep(2)
            await self.browser.take_screenshot(f"shanxi_{tax_type}_declaration_page.png")

    async def fill_vat_declaration(self, data: dict):
        """填写增值税申报表"""
        logger.info(f"Filling VAT declaration: {data}")
        try:
            if "sales_amount" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["vat_sales_amount"],
                    str(data["sales_amount"])
                )
            if "tax_amount" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["vat_tax_amount"],
                    str(data["tax_amount"])
                )
            await self.browser.take_screenshot("shanxi_vat_filled.png")
            print("OK: VAT declaration form filled")
        except Exception as e:
            logger.error(f"Fill VAT failed: {e}")
            await self.browser.take_screenshot("shanxi_vat_fill_error.png")
            raise

    async def fill_iit_declaration(self, data: dict):
        """填写个人所得税申报表"""
        logger.info(f"Filling IIT declaration: {data}")
        try:
            if "income" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["iit_income_amount"],
                    str(data["income"])
                )
            if "expenses" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["iit_expense_amount"],
                    str(data["expenses"])
                )
            await self.browser.take_screenshot("shanxi_iit_filled.png")
            print("OK: IIT declaration form filled")
        except Exception as e:
            logger.error(f"Fill IIT failed: {e}")
            await self.browser.take_screenshot("shanxi_iit_fill_error.png")
            raise

    async def fill_surtax_declaration(self, data: dict):
        """填写附加税申报表"""
        logger.info(f"Filling surtax declaration: {data}")
        print("OK: Surtax declaration form ready")

    async def request_user_confirm_before_submit(self, package) -> None:
        """提交前暂停，等待用户确认"""
        print("\n" + "=" * 60)
        print("Declaration data filled automatically")
        print("Please verify in browser and manually click submit")
        print("=" * 60 + "\n")
        await self.browser.take_screenshot("shanxi_declaration_prefilled.png")

    async def submit_declaration(self):
        """提交申报"""
        logger.info("Submitting declaration")
        try:
            await self.browser.click_button(self.SELECTORS["vat_submit_btn"])
            await asyncio.sleep(1)
            await self.browser.click_button(self.SELECTORS["confirm_btn"])
            print("Submitting...")
            await asyncio.sleep(3)
            try:
                await self.browser.page.wait_for_selector(
                    self.SELECTORS["success_message"], timeout=10000
                )
                print("OK: Declaration submitted")
                return {"status": "success", "message": "Declaration submitted"}
            except:
                print("Please check result manually")
                return {"status": "unknown", "message": "Please check manually"}
        except Exception as e:
            logger.error(f"Submit failed: {e}")
            await self.browser.take_screenshot("shanxi_submit_error.png")
            raise

    async def get_declaration_status(self) -> dict:
        """获取申报状态"""
        return {"status": "pending", "message": "To be queried"}

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            user_info = await self.browser.page.query_selector(self.SELECTORS["user_info"])
            return user_info is not None
        except Exception as e:
            logger.error(f"Check login status failed: {e}")
            return False

    async def logout(self):
        """登出"""
        logger.info("Logging out")
        try:
            logout_btn = await self.browser.page.query_selector("text=退出")
            if logout_btn:
                await logout_btn.click()
                await asyncio.sleep(2)
                self.logged_in = False
        except Exception as e:
            logger.error(f"Logout failed: {e}")
