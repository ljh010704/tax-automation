"""自动报税流程编排器
协调登录、填表、提交等完整报税流程。
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from automation.browser import BrowserAutomation
from automation.sites.base_adapter import BaseSiteAdapter
from automation.sites.fujian import FujianAdapter
from core.credential_store import CredentialStore


logger = logging.getLogger(__name__)


# 省份适配器注册表
ADAPTER_REGISTRY = {
    "fujian": FujianAdapter,
}


class DeclarationPackage:
    """申报数据包"""

    def __init__(self, entity_id: str, entity_name: str, province: str,
                 tax_type: str, period: str, data: dict):
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.province = province
        self.tax_type = tax_type
        self.period = period
        self.data = data
        self.created_at = datetime.now()
        self.status = "pending"
        self.result = None

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "province": self.province,
            "tax_type": self.tax_type,
            "period": self.period,
            "data": self.data,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
        }


class DeclarationManager:
    """自动报税管理器"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.adapter = None
        self.credential_store = CredentialStore()
        self.declaration_history: List[DeclarationPackage] = []
        self.log_dir = Path("data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_adapter(self, province: str) -> BaseSiteAdapter:
        """获取对应省份的适配器"""
        adapter_class = ADAPTER_REGISTRY.get(province)
        if not adapter_class:
            supported = ", ".join(ADAPTER_REGISTRY.keys())
            raise ValueError(f"不支持的省份: {province}，当前支持: {supported}")
        return adapter_class

    async def start_browser(self):
        """启动浏览器"""
        self.browser = BrowserAutomation(headless=self.headless)
        await self.browser.start()
        logger.info("浏览器已启动")

    async def stop_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.stop()
            self.browser = None
            self.adapter = None
            logger.info("浏览器已关闭")

    async def login(self, province: str, entity_id: str,
                    login_method: str = "manual"):
        """登录电子税务局
        
        Args:
            province: 省份代码
            entity_id: 实体ID
            login_method: 登录方式 - "manual", "password", "scan"
        """
        if not self.browser:
            await self.start_browser()

        adapter_class = self._get_adapter(province)
        self.adapter = adapter_class(self.browser)
        
        logger.info(f"开始登录 {province} 电子税务局, 实体: {entity_id}")
        await self.adapter.login(method=login_method)

    async def declare_vat(self, entity_id: str, entity_name: str,
                          province: str, period: str, data: dict) -> dict:
        """增值税申报
        
        Args:
            entity_id: 实体ID
            entity_name: 实体名称
            province: 省份代码
            period: 申报期间，如 "2026-Q1"
            data: 申报数据 {"sales_amount": 100000, "tax_amount": 3000}
            
        Returns:
            申报结果
        """
        package = DeclarationPackage(
            entity_id=entity_id,
            entity_name=entity_name,
            province=province,
            tax_type="vat",
            period=period,
            data=data,
        )

        try:
            if not self.adapter:
                raise Exception("请先登录")

            # 导航到增值税申报页面
            await self.adapter.navigate_to_tax_declaration("vat")

            # 填写申报表
            await self.adapter.fill_vat_declaration(data)

            # 等待用户确认
            await self.adapter.request_user_confirm_before_submit(package.to_dict())

            # 提交申报
            result = await self.adapter.submit_declaration()

            package.status = result.get("status", "unknown")
            package.result = result

        except Exception as e:
            logger.error(f"增值税申报失败: {e}")
            package.status = "error"
            package.result = {"status": "error", "message": str(e)}

        self.declaration_history.append(package)
        self._save_log(package)
        return package.to_dict()

    async def declare_iit(self, entity_id: str, entity_name: str,
                          province: str, period: str, data: dict) -> dict:
        """个人所得税（经营所得）申报"""
        package = DeclarationPackage(
            entity_id=entity_id,
            entity_name=entity_name,
            province=province,
            tax_type="iit",
            period=period,
            data=data,
        )

        try:
            if not self.adapter:
                raise Exception("请先登录")

            await self.adapter.navigate_to_tax_declaration("iit")
            await self.adapter.fill_iit_declaration(data)
            await self.adapter.request_user_confirm_before_submit(package.to_dict())
            result = await self.adapter.submit_declaration()

            package.status = result.get("status", "unknown")
            package.result = result

        except Exception as e:
            logger.error(f"个税申报失败: {e}")
            package.status = "error"
            package.result = {"status": "error", "message": str(e)}

        self.declaration_history.append(package)
        self._save_log(package)
        return package.to_dict()

    async def declare_surtax(self, entity_id: str, entity_name: str,
                             province: str, period: str, data: dict) -> dict:
        """附加税申报"""
        package = DeclarationPackage(
            entity_id=entity_id,
            entity_name=entity_name,
            province=province,
            tax_type="surtax",
            period=period,
            data=data,
        )

        try:
            if not self.adapter:
                raise Exception("请先登录")

            await self.adapter.navigate_to_tax_declaration("surtax")
            await self.adapter.fill_surtax_declaration(data)
            await self.adapter.request_user_confirm_before_submit(package.to_dict())
            result = await self.adapter.submit_declaration()

            package.status = result.get("status", "unknown")
            package.result = result

        except Exception as e:
            logger.error(f"附加税申报失败: {e}")
            package.status = "error"
            package.result = {"status": "error", "message": str(e)}

        self.declaration_history.append(package)
        self._save_log(package)
        return package.to_dict()

    async def batch_declare(self, entity_id: str, entity_name: str,
                            province: str, period: str,
                            declarations: List[dict]) -> List[dict]:
        """批量申报
        
        Args:
            declarations: 申报列表，每项包含 tax_type 和 data
            
        Returns:
            各项申报结果
        """
        results = []
        for decl in declarations:
            tax_type = decl["tax_type"]
            data = decl["data"]

            if tax_type == "vat":
                result = await self.declare_vat(
                    entity_id, entity_name, province, period, data
                )
            elif tax_type == "iit":
                result = await self.declare_iit(
                    entity_id, entity_name, province, period, data
                )
            elif tax_type == "surtax":
                result = await self.declare_surtax(
                    entity_id, entity_name, province, period, data
                )
            else:
                result = {
                    "status": "error",
                    "message": f"不支持的税种: {tax_type}"
                }

            results.append(result)

        return results

    def _save_log(self, package: DeclarationPackage):
        """保存申报日志"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"declaration_{package.entity_id}_{timestamp}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(package.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"申报日志已保存: {log_file}")
        except Exception as e:
            logger.error(f"保存申报日志失败: {e}")

    def get_history(self) -> List[dict]:
        """获取申报历史"""
        return [pkg.to_dict() for pkg in self.declaration_history]

    def get_supported_provinces(self) -> list:
        """获取支持的省份列表"""
        return list(ADAPTER_REGISTRY.keys())
