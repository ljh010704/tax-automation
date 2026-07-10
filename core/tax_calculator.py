"""
税额计算引擎
支持：增值税（小规模纳税人）、个人所得税（经营所得）、附加税
"""


class TaxCalculator:
    """税务计算器"""

    # 增值税小规模纳税人征收率
    VAT_RATE = 0.03
    # 小规模纳税人季度免税额度（30万）
    VAT_QUARTERLY_THRESHOLD = 300000

    # 附加税税率
    CITY_MAINTENANCE_RATE = 0.07  # 城市维护建设税 7%
    EDUCATION_SURCHARGE_RATE = 0.03  # 教育费附加 3%
    LOCAL_EDUCATION_SURCHARGE_RATE = 0.02  # 地方教育附加 2%

    # 个人所得税（经营所得）税率表 - 五级超额累进
    IIT_BRACKETS = [
        (0, 30000, 0, 0),
        (30000, 90000, 0.10, 1500),
        (90000, 300000, 0.20, 10500),
        (300000, 500000, 0.30, 40500),
        (500000, float('inf'), 0.35, 65500),
    ]

    def calculate_vat(self, quarterly_income: float, is_small_scale: bool = True) -> dict:
        """
        计算增值税（小规模纳税人）

        Args:
            quarterly_income: 季度销售额
            is_small_scale: 是否为小规模纳税人

        Returns:
            dict: 包含税额和是否免税
        """
        if not is_small_scale:
            # 一般纳税人按13%计算（简化版）
            vat = quarterly_income / 1.13 * 0.13
            return {
                "taxable_income": quarterly_income / 1.13,
                "vat": round(vat, 2),
                "is_exempt": False,
                "rate": 0.13,
            }

        # 小规模纳税人
        if quarterly_income <= self.VAT_QUARTERLY_THRESHOLD:
            return {
                "taxable_income": quarterly_income,
                "vat": 0,
                "is_exempt": True,
                "rate": self.VAT_RATE,
                "note": "季度销售额未超过30万，免征增值税",
            }
        else:
            vat = quarterly_income * self.VAT_RATE
            return {
                "taxable_income": quarterly_income,
                "vat": round(vat, 2),
                "is_exempt": False,
                "rate": self.VAT_RATE,
            }

    def calculate_surtax(self, vat_amount: float) -> dict:
        """
        计算附加税（城建税+教育费附加+地方教育附加）

        Args:
            vat_amount: 增值税税额

        Returns:
            dict: 各附加税明细
        """
        city_maintenance = vat_amount * self.CITY_MAINTENANCE_RATE
        education_surcharge = vat_amount * self.EDUCATION_SURCHARGE_RATE
        local_education = vat_amount * self.LOCAL_EDUCATION_SURCHARGE_RATE

        return {
            "city_maintenance": round(city_maintenance, 2),
            "education_surcharge": round(education_surcharge, 2),
            "local_education_surcharge": round(local_education, 2),
            "total": round(
                city_maintenance + education_surcharge + local_education, 2
            ),
        }

    def calculate_iit_business_income(
        self, annual_income: float, annual_expenses: float
    ) -> dict:
        """
        计算个人所得税（经营所得）

        Args:
            annual_income: 年度收入总额
            annual_expenses: 年度成本费用

        Returns:
            dict: 税额计算结果
        """
        # 应纳税所得额 = 收入总额 - 成本费用 - 损失
        taxable_income = max(0, annual_income - annual_expenses)

        # 适用税率和速算扣除数
        tax_rate = 0
        quick_deduction = 0
        for lower, upper, rate, deduction in self.IIT_BRACKETS:
            if lower <= taxable_income < upper:
                tax_rate = rate
                quick_deduction = deduction
                break

        # 应纳税额 = 应纳税所得额 × 税率 - 速算扣除数
        tax = taxable_income * tax_rate - quick_deduction
        tax = max(0, tax)

        # 计算季度预缴金额（按季度预缴，全年汇算清缴）
        quarterly_tax = tax / 4

        return {
            "annual_income": annual_income,
            "annual_expenses": annual_expenses,
            "taxable_income": taxable_income,
            "tax_rate": tax_rate,
            "quick_deduction": quick_deduction,
            "annual_tax": round(tax, 2),
            "quarterly_tax": round(quarterly_tax, 2),
        }

    def calculate_all_quarterly(
        self,
        quarterly_income: float,
        quarterly_expenses: float,
        quarterly_vat: float = None,
    ) -> dict:
        """
        计算季度全部税费

        Args:
            quarterly_income: 季度收入
            quarterly_expenses: 季度费用
            quarterly_vat: 季度增值税（可选，自动计算）

        Returns:
            dict: 全部税费明细
        """
        # 计算增值税
        vat_result = self.calculate_vat(quarterly_income)

        # 计算附加税
        surtax_result = self.calculate_surtax(vat_result["vat"])

        # 计算个人所得税（经营所得）- 按季度预缴
        annual_income = quarterly_income * 4
        annual_expenses = quarterly_expenses * 4
        iit_result = self.calculate_iit_business_income(annual_income, annual_expenses)

        # 季度预缴个税
        quarterly_iit = iit_result["quarterly_tax"]

        # 总税费
        total_tax = (
            vat_result["vat"] + surtax_result["total"] + quarterly_iit
        )

        return {
            "quarterly_income": quarterly_income,
            "quarterly_expenses": quarterly_expenses,
            "vat": vat_result,
            "surtax": surtax_result,
            "iit": {
                "quarterly_taxable_income": quarterly_income - quarterly_expenses,
                "quarterly_tax": quarterly_iit,
                "annual_tax": iit_result["annual_tax"],
                "tax_rate": iit_result["tax_rate"],
            },
            "total_quarterly_tax": round(total_tax, 2),
        }



    # ==================== 印花税 ====================
    STAMP_CONTRACT_RATE = 0.0003       # 购销合同 0.3‰
    STAMP_CONTRACT_RATE_SMALL = 0.00015  # 小规模纳税人减半 0.15‰
    STAMP_CAPITAL_RATE = 0.00025        # 实缴资本 0.25‰
    STAMP_CAPITAL_RATE_SMALL = 0.000125  # 小规模纳税人减半 0.125‰

    def calculate_stamp_tax(self, quarterly_income: float, paid_capital: float = 0,
                            is_small_scale: bool = True) -> dict:
        """
        印花税估算（个体工商户/个人独资企业）

        Args:
            quarterly_income: 季度销售额（用于购销合同）
            paid_capital: 实缴资本+资本公积
            is_small_scale: 是否小规模纳税人（减半征收）

        Returns:
            dict: 各税目明细
        """
        contract_rate = self.STAMP_CONTRACT_RATE_SMALL if is_small_scale else self.STAMP_CONTRACT_RATE
        capital_rate = self.STAMP_CAPITAL_RATE_SMALL if is_small_scale else self.STAMP_CAPITAL_RATE

        contract_tax = round(quarterly_income * contract_rate, 2)
        books_tax = 0  # 2018年起其他账簿免征
        capital_tax = round(paid_capital * capital_rate, 2)

        return {
            "contract": {
                "title": "购销合同",
                "rate": contract_rate,
                "amount": contract_tax,
                "note": "按季度销售额估算" + ("（小规模减半）" if is_small_scale else ""),
            },
            "books": {
                "title": "营业账簿",
                "rate": 0,
                "amount": books_tax,
                "note": "2018年起免征",
            },
            "capital": {
                "title": "实缴资本",
                "rate": capital_rate,
                "amount": capital_tax,
                "note": "按实缴资本+资本公积估算" + ("（小规模减半）" if is_small_scale else ""),
            },
            "total": round(contract_tax + books_tax + capital_tax, 2),
            "is_small_scale": is_small_scale,
        }

    # ==================== 个税年度汇算清缴 ====================
    def calculate_iit_annual_reconciliation(self, annual_income: float,
                                             annual_expenses: float,
                                             quarterly_prepaid: float) -> dict:
        """
        个人所得税（经营所得）年度汇算清缴

        Args:
            annual_income: 年度收入总额
            annual_expenses: 年度成本费用
            quarterly_prepaid: 本年度已预缴税额合计

        Returns:
            dict: 汇算结果
        """
        taxable_income = max(0, annual_income - annual_expenses)

        tax_rate = 0
        quick_deduction = 0
        for lower, upper, rate, deduction in self.IIT_BRACKETS:
            if lower <= taxable_income < upper:
                tax_rate = rate
                quick_deduction = deduction
                break

        annual_tax = max(0, taxable_income * tax_rate - quick_deduction)
        annual_tax = round(annual_tax, 2)
        diff = round(annual_tax - quarterly_prepaid, 2)

        return {
            "annual_income": annual_income,
            "annual_expenses": annual_expenses,
            "taxable_income": taxable_income,
            "tax_rate": tax_rate,
            "quick_deduction": quick_deduction,
            "annual_tax": annual_tax,
            "quarterly_prepaid": quarterly_prepaid,
            "difference": diff,
            "result": "补税" if diff > 0 else ("退税" if diff < 0 else "无差额"),
        }

    # ==================== 社保计算器 ====================
    SOCIAL_SECURITY_RATES = {
        "pension_employer": 0.16,
        "pension_individual": 0.08,
        "medical_employer": 0.08,
        "medical_individual": 0.02,
        "unemployment_employer": 0.005,
        "unemployment_individual": 0.005,
    }

    def calculate_social_security(self, monthly_base: float,
                                  city_rates: dict = None) -> dict:
        """
        社保缴费计算器（养老+医疗+失业）

        Args:
            monthly_base: 月缴费基数
            city_rates: 自定义城市费率（可选，默认全国平均）

        Returns:
            dict: 企业/个人各险种明细
        """
        rates = city_rates or self.SOCIAL_SECURITY_RATES

        pension_emp = round(monthly_base * rates.get("pension_employer", 0.16), 2)
        pension_ind = round(monthly_base * rates.get("pension_individual", 0.08), 2)
        medical_emp = round(monthly_base * rates.get("medical_employer", 0.08), 2)
        medical_ind = round(monthly_base * rates.get("medical_individual", 0.02), 2)
        unemp_emp = round(monthly_base * rates.get("unemployment_employer", 0.005), 2)
        unemp_ind = round(monthly_base * rates.get("unemployment_individual", 0.005), 2)

        employer_total = round(pension_emp + medical_emp + unemp_emp, 2)
        individual_total = round(pension_ind + medical_ind + unemp_ind, 2)

        return {
            "monthly_base": monthly_base,
            "pension": {"employer": pension_emp, "individual": pension_ind, "total": round(pension_emp + pension_ind, 2)},
            "medical": {"employer": medical_emp, "individual": medical_ind, "total": round(medical_emp + medical_ind, 2)},
            "unemployment": {"employer": unemp_emp, "individual": unemp_ind, "total": round(unemp_emp + unemp_ind, 2)},
            "employer_total": employer_total,
            "individual_total": individual_total,
            "grand_total": round(employer_total + individual_total, 2),
        }

def format_currency(amount: float) -> str:
    """格式化金额显示"""
    return f"¥{amount:,.2f}"


def print_tax_summary(result: dict):
    """打印税费汇总"""
    print("=" * 50)
    print("季度税费计算汇总")
    print("=" * 50)
    print(f"季度收入: {format_currency(result['quarterly_income'])}")
    print(f"季度费用: {format_currency(result['quarterly_expenses'])}")
    print("-" * 50)

    vat = result["vat"]
    if vat["is_exempt"]:
        print(f"增值税: {format_currency(0)} (免征)")
    else:
        print(f"增值税: {format_currency(vat['vat'])} (税率: {vat['rate']*100}%)")

    surtax = result["surtax"]
    print(f"城建税: {format_currency(surtax['city_maintenance'])}")
    print(f"教育费附加: {format_currency(surtax['education_surcharge'])}")
    print(f"地方教育附加: {format_currency(surtax['local_education_surcharge'])}")
    print(f"附加税合计: {format_currency(surtax['total'])}")

    iit = result["iit"]
    print(f"个人所得税(经营所得): {format_currency(iit['quarterly_tax'])}")
    print(f"  适用税率: {iit['tax_rate']*100}%")
    print("-" * 50)
    print(f"季度应缴税费合计: {format_currency(result['total_quarterly_tax'])}")
    print("=" * 50)


if __name__ == "__main__":
    # 测试计算
    calc = TaxCalculator()

    # 测试：季度收入10万，费用6万
    result = calc.calculate_all_quarterly(
        quarterly_income=100000, quarterly_expenses=60000
    )
    print_tax_summary(result)

    print("\n")

    # 测试：季度收入35万（超过免税额度）
    result2 = calc.calculate_all_quarterly(
        quarterly_income=350000, quarterly_expenses=200000
    )
    print_tax_summary(result2)
