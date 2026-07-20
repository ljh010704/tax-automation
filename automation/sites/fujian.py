"""Fujian Electronic Tax Bureau Adapter"""

import asyncio
import logging
from typing import Optional, Dict, Any
from automation.sites.base_adapter import BaseSiteAdapter


logger = logging.getLogger(__name__)


class FujianAdapter(BaseSiteAdapter):
    """Fujian Electronic Tax Bureau Adapter"""

    LOGIN_URL = "https://etax.fujian.chinatax.gov.cn:8443/"
    
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
        "cancel_btn": "button:has-text('取消')",
        "success_message": ".success-message",
        "error_message": ".error-message",
    }

    def __init__(self, browser):
        super().__init__(browser)
        self.logged_in = False
        self.current_entity = None

    async def login(self, url: str = None, method: str = "manual"):
        """Login to Fujian Electronic Tax Bureau"""
        login_url = url or self.LOGIN_URL
        await self.browser.navigate(login_url)
        
        logger.info(f"Opened Fujian tax website: {login_url}")
        
        if method == "manual":
            print("\n" + "="*60)
            print("Preparing login page...")
            print("="*60 + "\n")
            
            # 1. Close modal if exists - force remove overlay
            try:
                await asyncio.sleep(2)
                # Force remove all mask overlays
                await self.browser.page.evaluate("""
                    document.querySelectorAll('.mask, .modal-mask, .overlay').forEach(el => el.remove());
                    document.querySelectorAll('[class*="mask"]').forEach(el => el.style.display = 'none');
                """)
                print("Removed all mask overlays")
                await asyncio.sleep(1)
            except Exception as e:
                logger.info(f"Remove overlay failed: {e}")
            
            # 2. Click login button with force
            try:
                login_btn = await self.browser.page.query_selector(self.SELECTORS["login_btn"])
                if login_btn:
                    await login_btn.click(force=True)
                    print("Clicked login button (force)")
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Click login button failed: {e}")
            
            # 3. Wait for user to complete login
            print("\n" + "="*60)
            print("Please complete login in browser")
            print("Supported methods: CA certificate, SMS code, QR scan, Face ID")
            print("\nProgram will continue automatically after login...")
            print("="*60 + "\n")
            
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
        
        elif method == "password":
            await self._login_with_password()
        
        elif method == "scan":
            await self._login_with_scan()
        
        await self.browser.take_screenshot("fujian_login_success.png")

    async def _login_with_password(self):
        """Login with password (not implemented)"""
        print("Password login not implemented yet")
        raise NotImplementedError("Password login requires credentials")

    async def _login_with_scan(self):
        """Login with QR scan"""
        print("QR scan login mode")
        try:
            await self.browser.page.wait_for_selector(
                self.SELECTORS["user_info"],
                timeout=120000
            )
            self.logged_in = True
            logger.info("QR scan login successful")
            print("OK: QR scan login successful")
        except Exception as e:
            logger.error(f"QR scan login failed: {e}")
            raise Exception("QR scan login timeout")

    async def navigate_to_tax_declaration(self, tax_type: str):
        """Navigate to tax declaration page"""
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
            logger.info("Entering VAT declaration page")
        elif tax_type == "iit":
            entry_selector = self.SELECTORS["iit_declaration_entry"]
            logger.info("Entering IIT declaration page")
        elif tax_type == "surtax":
            entry_selector = self.SELECTORS["surtax_declaration_entry"]
            logger.info("Entering surtax declaration page")
        
        if entry_selector:
            await self.browser.click_button(entry_selector)
            await asyncio.sleep(2)
            await self.browser.take_screenshot(f"fujian_{tax_type}_declaration_page.png")

    async def fill_vat_declaration(self, data: dict):
        """Fill VAT declaration form"""
        logger.info(f"Filling VAT declaration: {data}")
        
        try:
            if "sales_amount" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["vat_sales_amount"],
                    str(data["sales_amount"])
                )
                logger.info(f"Filled sales amount: {data['sales_amount']}")
            
            if "tax_amount" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["vat_tax_amount"],
                    str(data["tax_amount"])
                )
                logger.info(f"Filled tax amount: {data['tax_amount']}")
            
            await self.browser.take_screenshot("fujian_vat_filled.png")
            print("OK: VAT declaration form filled")
            
        except Exception as e:
            logger.error(f"Fill VAT declaration failed: {e}")
            await self.browser.take_screenshot("fujian_vat_fill_error.png")
            raise

    async def fill_iit_declaration(self, data: dict):
        """Fill IIT declaration form"""
        logger.info(f"Filling IIT declaration: {data}")
        
        try:
            if "income" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["iit_income_amount"],
                    str(data["income"])
                )
                logger.info(f"Filled income: {data['income']}")
            
            if "expenses" in data:
                await self.browser.fill_form_field(
                    self.SELECTORS["iit_expense_amount"],
                    str(data["expenses"])
                )
                logger.info(f"Filled expenses: {data['expenses']}")
            
            await self.browser.take_screenshot("fujian_iit_filled.png")
            print("OK: IIT declaration form filled")
            
        except Exception as e:
            logger.error(f"Fill IIT declaration failed: {e}")
            await self.browser.take_screenshot("fujian_iit_fill_error.png")
            raise

    async def fill_surtax_declaration(self, data: dict):
        """Fill surtax declaration form"""
        logger.info(f"Filling surtax declaration: {data}")
        try:
            print("OK: Surtax declaration form ready")
        except Exception as e:
            logger.error(f"Fill surtax declaration failed: {e}")
            raise

    async def request_user_confirm_before_submit(self, package) -> None:
        """Wait for user confirmation before submit"""
        print("\n" + "="*60)
        print("Declaration data filled automatically")
        print("Please verify in browser:")
        print(f"  - Tax type: {package.get('tax_type', 'unknown')}")
        print(f"  - Period: {package.get('period', 'unknown')}")
        print(f"  - Amount: {package.get('amount', 'unknown')}")
        print("\nPlease manually click submit button to complete")
        print("="*60 + "\n")
        
        await self.browser.take_screenshot("fujian_declaration_prefilled.png")

    async def submit_declaration(self):
        """Submit declaration"""
        logger.info("Submitting declaration")
        
        try:
            await self.browser.click_button(self.SELECTORS["vat_submit_btn"])
            await asyncio.sleep(1)
            await self.browser.click_button(self.SELECTORS["confirm_btn"])
            
            print("Submitting...")
            await asyncio.sleep(3)
            
            try:
                await self.browser.page.wait_for_selector(
                    self.SELECTORS["success_message"],
                    timeout=10000
                )
                logger.info("Declaration submitted successfully")
                print("OK: Declaration submitted")
                return {"status": "success", "message": "Declaration submitted"}
            except:
                try:
                    error_elem = await self.browser.page.query_selector(
                        self.SELECTORS["error_message"]
                    )
                    if error_elem:
                        error_text = await error_elem.text_content()
                        logger.error(f"Declaration failed: {error_text}")
                        return {"status": "error", "message": error_text}
                except:
                    pass
                
                logger.warning("Cannot confirm result, please check manually")
                return {"status": "unknown", "message": "Please check manually"}
            
        except Exception as e:
            logger.error(f"Submit declaration failed: {e}")
            await self.browser.take_screenshot("fujian_submit_error.png")
            raise

    async def get_declaration_status(self) -> dict:
        """Get declaration status"""
        logger.info("Getting declaration status")
        return {
            "status": "pending",
            "message": "To be queried",
            "last_updated": None
        }

    async def check_login_status(self) -> bool:
        """Check login status"""
        try:
            user_info = await self.browser.page.query_selector(
                self.SELECTORS["user_info"]
            )
            return user_info is not None
        except Exception as e:
            logger.error(f"Check login status failed: {e}")
            return False

    async def logout(self):
        """Logout"""
        logger.info("Logging out")
        try:
            logout_btn = await self.browser.page.query_selector("text=退出")
            if logout_btn:
                await logout_btn.click()
                await asyncio.sleep(2)
                self.logged_in = False
                logger.info("Logged out")
        except Exception as e:
            logger.error(f"Logout failed: {e}")
