"""电子税务局适配器基类
用于 1.0 半自动申报流程。
"""


class BaseSiteAdapter:
    """电子税务局适配器基类"""

    def __init__(self, browser):
        self.browser = browser

    async def login(self, url: str):
        """登录电子税务局"""
        raise NotImplementedError

    async def navigate_to_tax_declaration(self, tax_type: str):
        """导航到申报页面"""
        raise NotImplementedError

    async def fill_vat_declaration(self, data: dict):
        """填写增值税申报表"""
        raise NotImplementedError

    async def fill_iit_declaration(self, data: dict):
        """填写个人所得税（经营所得）申报表"""
        raise NotImplementedError

    async def fill_surtax_declaration(self, data: dict):
        """填写附加税申报表"""
        raise NotImplementedError

    async def request_user_confirm_before_submit(self, package) -> None:
        """提交前暂停，等待用户确认"""
        raise NotImplementedError

    async def submit_declaration(self):
        """提交申报"""
        raise NotImplementedError

    async def get_declaration_status(self) -> dict:
        """获取申报状态"""
        raise NotImplementedError
