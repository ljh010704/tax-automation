"""申报执行器（1.0 半自动）
职责：组装申报数据包 -> 调用站点适配器填表 -> 停在用户确认 -> 提交并记录结果。
当前仅支持半自动流程：程序自动填表，最后仍由用户确认提交。
"""

from __future__ import annotations

import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Optional


@dataclass
class DeclarationItem:
    tax_type: str
    title: str
    amount: float
    detail: Dict


@dataclass
class DeclarationPackage:
    entity_id: int
    entity_name: str
    credit_code: str
    province: str
    city: str
    login_url: str
    year: int
    quarter: int
    generated_at: str
    items: list


class DeclarationRunner:
    """半自动申报运行器（1.0）"""

    def __init__(self, data_manager, tax_calculator):
        self.dm = data_manager
        self.calc = tax_calculator

    def build_declaration_package(self, entity_id: int, year: int, quarter: int) -> DeclarationPackage:
        entity = self.dm.get_entity(entity_id)
        if not entity:
            raise ValueError("未找到经营主体")

        summary = self.dm.get_quarterly_summary(entity_id, year, quarter)
        result = self.calc.calculate_all_quarterly(summary["income"], summary["expense"])

        items = [
            DeclarationItem(
                tax_type="vat",
                title="增值税",
                amount=result["vat"]["vat"],
                detail=result["vat"],
            ),
            DeclarationItem(
                tax_type="surtax",
                title="附加税",
                amount=result["surtax"]["total"],
                detail=result["surtax"],
            ),
            DeclarationItem(
                tax_type="iit",
                title="个人所得税（经营所得）",
                amount=result["iit"]["quarterly_tax"],
                detail=result["iit"],
            ),
        ]

        return DeclarationPackage(
            entity_id=entity["id"],
            entity_name=entity["name"],
            credit_code=entity["credit_code"],
            province=entity.get("province", ""),
            city=entity.get("city", ""),
            login_url=entity.get("login_url", ""),
            year=year,
            quarter=quarter,
            generated_at=datetime.now().isoformat(timespec="seconds"),
            items=[asdict(i) for i in items],
        )

    async def run_semi_auto(self, package: DeclarationPackage, adapter) -> Dict:
        url = package.login_url
        if not url:
            return {
                "status": "failed",
                "reason": "login_url_missing",
                "message": "未配置电子税务局地址，请先在经营主体中填写登录地址。",
            }

        await adapter.login(url)

        if package.items[0]["amount"] > 0 or package.items[1]["amount"] > 0 or package.items[2]["amount"] > 0:
            await adapter.navigate_to_tax_declaration("vat")

        await adapter.fill_vat_declaration({
            "sales_amount": 0,
            "tax_amount": package.items[0]["amount"],
            "package": package.items[0],
        })

        await adapter.fill_surtax_declaration({
            "tax_amount": package.items[1]["amount"],
            "package": package.items[1],
        })

        await adapter.fill_iit_declaration({
            "income": 0,
            "expenses": 0,
            "package": package.items[2],
        })

        await adapter.request_user_confirm_before_submit(package)

        return {
            "status": "waiting_user_confirm",
            "message": "已自动填表，等待用户在界面/浏览器中确认提交。",
            "package_summary": {
                "entity": package.entity_name,
                "year": package.year,
                "quarter": package.quarter,
                "vat": package.items[0]["amount"],
                "surtax": package.items[1]["amount"],
                "iit": package.items[2]["amount"],
            },
        }
