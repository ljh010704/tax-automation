"""企业信息查询模块
通过天眼查查询企业信息（登录状态保存）
"""

import re
import asyncio
import os
import shutil
from typing import Optional, Dict


def _is_login_page(url: str) -> bool:
    """判断 URL 是否是登录/注册页面"""
    url_lower = url.lower()
    return any(kw in url_lower for kw in [
        "/login", "/register", "/userLogin",
        "login?", "register?",
    ])


class BusinessQuery:
    """企业信息自动查询（保存登录状态）"""

    TIANYANCHA_URL = "https://www.tianyancha.com"
    USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "browser_data")

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def start(self, save_login: bool = True):
        """启动浏览器"""
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()

        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ]

        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break

        os.makedirs(self.USER_DATA_DIR, exist_ok=True)

        launch_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ]

        if chrome_path:
            print(f"使用系统 Chrome: {chrome_path}")
            self.context = await self.playwright.chromium.launch_persistent_context(
                self.USER_DATA_DIR,
                headless=False,
                executable_path=chrome_path,
                viewport={"width": 1280, "height": 800},
                args=launch_args,
            )
        else:
            print("未找到系统 Chrome，使用 Playwright 自带浏览器")
            self.context = await self.playwright.chromium.launch_persistent_context(
                self.USER_DATA_DIR,
                headless=False,
                viewport={"width": 1280, "height": 800},
                args=launch_args,
            )

        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

    async def stop(self):
        """关闭浏览器（登录状态会自动保存）"""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    async def query(self, credit_code: str) -> Optional[Dict]:
        """通过天眼查查询企业信息"""
        result = {
            "credit_code": credit_code,
            "name": "",
            "legal_representative": "",
            "business_status": "正常",
            "taxpayer_status": "正常",
            "province": "",
            "city": "",
            "address": "",
            "tax_authority": "",
            "login_url": "",
        }

        print(f"正在查询企业信息: {credit_code}")

        try:
            search_url = f"https://www.tianyancha.com/search?key={credit_code}"
            print("正在打开天眼查...")
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(5000)

            current_url = self.page.url

            # 仅通过 URL 路径判断是否在登录页
            if _is_login_page(current_url):
                print("\n需要登录天眼查，请在浏览器中完成登录...")
                await self.page.screenshot(path=os.path.join(os.path.dirname(__file__), "..", "login_waiting.png"))

                for i in range(180):
                    await self.page.wait_for_timeout(1000)
                    current_url = self.page.url
                    if not _is_login_page(current_url):
                        print("登录成功!")
                        await self.page.wait_for_timeout(3000)
                        break
                    if i % 30 == 0 and i > 0:
                        print(f"已等待 {i} 秒，请在浏览器中完成登录...")

                # 登录成功后重新搜索
                await self.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await self.page.wait_for_timeout(5000)

            await self.page.screenshot(path=os.path.join(os.path.dirname(__file__), "..", "search_result.png"))
            print("搜索结果已截图保存")

            # 再次检查：如果跳转到了登录页
            if _is_login_page(current_url):
                result["failure_reason"] = "login_required"
                print("\n页面仍处于登录状态，请先登录后再试。")
                return result

            # 检查验证码
            content = await self.page.content()
            if any(keyword in content for keyword in ["验证码", "captcha", "请完成安全验证", "滑块验证"]):
                result["failure_reason"] = "captcha_or_risk_control"
                print("\n疑似触发验证码或风控，请先在浏览器中完成验证。")
                return result

            # 如果搜索直接跳转到详情页，直接提取
            if "/company/" in self.page.url:
                print("搜索直接跳转到详情页，直接提取...")
                result = await self._extract_from_detail_page(credit_code)
                if result.get("province"):
                    if result.get("county") and "省" not in result.get("county", "") and result["county"] != result.get("province", ""):
                        result["tax_authority"] = f"国家税务总局{result['county']}税务局"
                    elif result.get("city"):
                        result["tax_authority"] = f"国家税务总局{result['city']}税务局"
                    else:
                        prov_short = result["province"].replace("省", "").replace("市", "").replace("自治区", "")
                        result["tax_authority"] = f"国家税务总局{prov_short}税务局"
                    result["login_url"] = self._get_tax_bureau_url(result["province"], result.get("city", ""))
                return result

            # 【核心改动】点击搜索结果中的第一个公司链接，进入详情页
            print("正在查找搜索结果中的公司链接...")
            
            # 等待搜索结果加载
            try:
                await self.page.wait_for_selector('a[href*="/company/"]', timeout=10000)
            except Exception:
                print("未找到公司链接，尝试其他选择器...")
            
            # 尝试多种选择器找到公司链接
            company_link = None
            selectors = [
                'a[href*="/company/"]',
                'a[class*="name"]',
                'a[class*="company"]',
                '.result-list a',
                '.search-result a',
            ]
            
            for selector in selectors:
                try:
                    company_link = await self.page.query_selector(selector)
                    if company_link:
                        print(f"找到公司链接，选择器: {selector}")
                        break
                except Exception:
                    continue
            
            if company_link:
                # 点击进入详情页
                print("正在进入公司详情页...")
                try:
                    # 提取链接href，以备直接导航
                    href = await company_link.get_attribute('href') or ''
                    if href and href.startswith('/'):
                        href = 'https://www.tianyancha.com' + href

                    await company_link.click()
                    await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                    await self.page.wait_for_timeout(3000)

                    # 验证是否真正进入了详情页，否则直接导航
                    if "/company/" not in self.page.url and href:
                        print(f"点击未能跳转，直接导航: {href}")
                        await self.page.goto(href, wait_until="domcontentloaded", timeout=30000)
                        await self.page.wait_for_timeout(3000)

                    await self.page.screenshot(path=os.path.join(os.path.dirname(__file__), "..", "company_detail.png"))
                    print("公司详情页已截图保存")
                    
                    # 从详情页提取信息
                    result = await self._extract_from_detail_page(credit_code)
                except Exception as e:
                    print(f"点击公司链接失败: {e}")
                    result["failure_reason"] = "click_failed"
            else:
                print("未找到公司链接，尝试从当前页面提取...")
                # 降级：从搜索结果页提取
                result = self._extract_from_search_page(content, credit_code)

            # 如果提取失败，设置失败原因
            if not result.get("name"):
                if not result.get("failure_reason"):
                    result["failure_reason"] = "extract_failed"
                print("\n未能自动提取，请查看浏览器中的搜索结果")
            else:
                # 提取成功，生成税务信息
                if result.get("province"):
                    if result.get("county") and "省" not in result.get("county", "") and result["county"] != result.get("province", ""):
                        result["tax_authority"] = f"国家税务总局{result['county']}税务局"
                    elif result.get("city"):
                        result["tax_authority"] = f"国家税务总局{result['city']}税务局"
                    else:
                        prov_short = result["province"].replace("省", "").replace("市", "").replace("自治区", "")
                        result["tax_authority"] = f"国家税务总局{prov_short}税务局"
                    result["login_url"] = self._get_tax_bureau_url(result["province"], result.get("city", ""))

            return result

        except asyncio.TimeoutError:
            result["failure_reason"] = "timeout"
            print("查询超时，请检查网络或稍后重试")
            return result
        except Exception as e:
            result["failure_reason"] = "unexpected_error"
            print(f"查询出错: {e}")
            import traceback
            traceback.print_exc()
            return result
    async def _extract_from_detail_page(self, credit_code: str) -> Dict:
        """从公司详情页提取企业信息（使用 inner_text 获取渲染后的文本）"""
        result = {
            "credit_code": credit_code,
            "name": "",
            "legal_representative": "",
            "entity_type": "",
            "business_status": "正常",
            "taxpayer_status": "正常",
            "province": "",
            "city": "",
            "county": "",
            "address": "",
        }

        print("正在从详情页提取信息...")

        # 等待页面主要内容加载
        try:
            await self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await self.page.wait_for_timeout(2000)

        # 向下滚动以加载更多信息（地址等在页面下方）
        try:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(2000)
        except Exception:
            pass

        # 【核心修复】使用 inner_text 获取渲染后的纯文本，而非 page.content() 返回的原始 HTML
        # 天眼查是 JS SPA，page.content() 返回的 HTML 不包含动态渲染的文本
        try:
            text = await self.page.inner_text("body")
        except Exception:
            text = ""

        if not text:
            print("  警告: 无法获取页面文本内容")
            return result

        # 将连续空白压缩为空格，便于正则匹配
        clean = re.sub(r"\s+", " ", text)

        # 1. 提取企业名称
        #    天眼查详情页顶部 h1 标签显示公司全称
        name_selectors = [
            "h1",
            ".company-name",
            ".header-name",
            '[class*="companyName"]',
        ]
        for selector in name_selectors:
            try:
                elems = await self.page.query_selector_all(selector)
                for elem in elems:
                    t = await elem.text_content()
                    if t and len(t.strip()) > 4 and len(t.strip()) < 80:
                        result["name"] = t.strip()
                        result["name"] = re.sub(
                            r"(存续|在业|开业|注销|吊销|迁出|停业|清算)$", "",
                            result["name"]
                        ).strip()
                        print(f"  企业名称: {result['name']}")
                        break
                if result["name"]:
                    break
            except Exception:
                continue

        # 2. 提取法定代表人/投资人
        #    个人独资企业无法人代表，以投资人代替
        m = re.search(r"法定代表人\s*[：:]\s*([\u4e00-\u9fa5]{2,6})", clean)
        if m:
            result["legal_representative"] = m.group(1).strip()
            print(f"  法定代表人: {result['legal_representative']}")
        else:
            m = re.search(r"投资人\s*[：:]?\s*([\u4e00-\u9fa5]{2,6})", clean)
            if m:
                result["legal_representative"] = m.group(1).strip()
                print(f"  投资人: {result['legal_representative']}")
        if not result.get("legal_representative"):
            m = re.search(r"经营者\s*[：:]?\s*([\u4e00-\u9fa5]{2,6})", clean)
            if m:
                result["legal_representative"] = m.group(1).strip()
                print(f"  经营者: {result['legal_representative']}")
        # 3. 提取经营状态
        status_patterns = [
            r"经营状态\s+(?:[：:]\s*)?(存续|在业|开业|注销|吊销|迁出|停业|清算)",
            r"登记状态\s+(?:[：:]\s*)?([^\s，,；;。]+)",
            r"企业状态\s+(?:[：:]\s*)?([^\s，,；;。]+)",
        ]
        for pattern in status_patterns:
            match = re.search(pattern, clean)
            if match:
                status = match.group(1).strip()
                if "存续" in status or "在业" in status or "开业" in status:
                    result["business_status"] = "正常"
                elif "注销" in status:
                    result["business_status"] = "注销"
                elif "吊销" in status:
                    result["business_status"] = "吊销"
                else:
                    result["business_status"] = status
                print(f"  经营状态: {result['business_status']}")
                break

        # 4. 提取主体类型
        entity_type_map = {
            "个体工商户": r"个体工商户",
            "有限公司": r"(?:有限责任公司|股份有限公司|有限公司)",
            "个人独资企业": r"个人独资企业",
            "合伙企业": r"(?:普通合伙|有限合伙|合伙企业)",
        }
        for etype, pattern in entity_type_map.items():
            if re.search(pattern, result["name"]):
                result["entity_type"] = etype
                print(f"  主体类型: {result['entity_type']}")
                break

        # 兜底：从页面"企业类型"字段提取
        if not result.get("entity_type"):
            et_match = re.search(r"企业类型\s*(?:[：:]|\t)\s*([^\t\n]+)", text)
            if et_match:
                et_text = et_match.group(1).strip()
                for etype, pattern in entity_type_map.items():
                    if re.search(pattern, et_text):
                        result["entity_type"] = etype
                        print(f"  主体类型(字段): {result['entity_type']}")
                        break

        # 5. 提取地址和省市（地址通常在页面下方）
        addr_patterns = [
            r"注册地址[：:\s]\s*(.+)",
            r"通讯地址[：:\s]\s*(.+)",
            r"(?:详细地址|地\s*址)[：:\s]\s*(.+)",
            r"(?:住所|经营场所)[：:\s]\s*(.+)",
        ]
        for pattern in addr_patterns:
            match = re.search(pattern, text)
            if match:
                address = match.group(1).strip()
                address = re.sub(r"(附近公司|附近企业|地图|关注|集群登记).*", "", address)
                if len(address) > 5:
                    result["address"] = address
                    print(f"  地址: {result['address']}")
                    self._extract_province_city(address, result)
                    break

        # 6. 如果地址里没提取到省市，尝试从企业名称或所属地区推断
        if not result["province"] and result["name"]:
            self._extract_province_city(result["name"], result)

        if not result["province"]:
            region_match = re.search(r"(?:所属地区|所在地区|地区|登记机关)\s*[：:]\s*([\u4e00-\u9fa5]+(?:省|市|自治区))", clean)
            if region_match:
                self._extract_province_city(region_match.group(1), result)
        # 7. 如果仍未提取到城市，从页面全文匹配"位于XX省XX市"
        if not result.get("city"):
            desc_match = re.search(r"位于[\u4e00-\u9fa5]*?(?:省|自治区)([\u4e00-\u9fa5]{2,4})市", clean)
            if desc_match:
                result["city"] = desc_match.group(1) + "市"
        # 7b. 兜底：从企业名称前的所在地或"位于"描述中提取
        if not result.get("city"):
            for m in re.finditer(r"位于([\u4e00-\u9fa5]{2,4})市", clean):
                c = m.group(1) + "市"
                if result.get("province") and result["province"].replace("省", "").replace("自治区", "").replace("市", "") not in c:
                    result["city"] = c
                    break

        # 提取区/县（用于主管税务机关）
        if not result.get("address"):
            pass
        else:
            county_match = re.search(r'([^\s\u7701]{2,4})县', result["address"])
            if county_match:
                result["county"] = county_match.group(1) + "县"
            elif result.get("city"):
                result["county"] = result["city"]

        print(f"  省份: {result['province'] or '未提取到'}")
        print(f"  城市: {result['city'] or '未提取到'}")

        return result

    def _extract_from_search_page(self, content: str, credit_code: str) -> Dict:
        """从搜索结果页提取企业信息（降级方案）"""
        result = {
            "credit_code": credit_code,
            "name": "",
            "legal_representative": "",
            "business_status": "正常",
            "taxpayer_status": "正常",
            "province": "",
            "city": "",
            "address": "",
        }

        print("尝试从搜索结果页提取...")

        # 清理 HTML 标签
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        clean_content = re.sub(r'\s+', ' ', clean_content)

        # 提取企业名称
        name_match = re.search(r'([\u4e00-\u9fa5（()）]{4,50}(?:有限公司|股份有限公司|合伙企业|个人独资企业|企业|中心|事务所|工作室))', clean_content)
        if name_match:
            result["name"] = name_match.group(1).strip()
            print(f"  企业名称: {result['name']}")

        # 提取经营状态
        status_match = re.search(r'经营状态\s*[：:]\s*([^\s，,<>]+)', clean_content)
        if status_match:
            status = status_match.group(1).strip()
            if '存续' in status or '在业' in status or '开业' in status:
                result["business_status"] = "正常"
            elif '注销' in status:
                result["business_status"] = "注销"
            elif '吊销' in status:
                result["business_status"] = "吊销"
            else:
                result["business_status"] = status
            print(f"  经营状态: {result['business_status']}")

        return result

    def _extract_province_city(self, text: str, result: Dict):
        """从文本中提取省和市"""
        provinces = {
            "北京市": "北京", "天津市": "天津", "上海市": "上海", "重庆市": "重庆",
            "河北省": "河北", "山西省": "山西", "辽宁省": "辽宁", "吉林省": "吉林",
            "黑龙江省": "黑龙江", "江苏省": "江苏", "浙江省": "浙江",
            "安徽省": "安徽", "福建省": "福建", "江西省": "江西", "山东省": "山东",
            "河南省": "河南", "湖北省": "湖北", "湖南省": "湖南", "广东省": "广东",
            "海南省": "海南", "四川省": "四川", "贵州省": "贵州", "云南省": "云南",
            "陕西省": "陕西", "甘肃省": "甘肃", "青海省": "青海", "台湾省": "台湾",
            "内蒙古自治区": "内蒙古", "广西壮族自治区": "广西",
            "西藏自治区": "西藏", "宁夏回族自治区": "宁夏",
            "新疆维吾尔自治区": "新疆",
        }

        for full_name, short_name in provinces.items():
            if full_name in text:
                result["province"] = full_name
                break

        text_without_province = text
        for full_name in provinces.keys():
            text_without_province = text_without_province.replace(full_name, '')

        city_match = re.search(r'([\u4e00-\u9fa5]{2,4})市', text_without_province)
        if city_match:
            city_name = city_match.group(1)
            if len(city_name) >= 2 and '省' not in city_name:
                result["city"] = city_name + "市"

        if result.get("province") in ["北京市", "天津市", "上海市", "重庆市"]:
            result["city"] = result["province"]

    def _get_tax_bureau_url(self, province: str, city: str) -> str:
        """根据省市生成电子税务局 URL"""
        tax_urls = {
            "北京": "https://etax.beijing.chinatax.gov.cn",
            "天津": "https://etax.tianjin.chinatax.gov.cn",
            "上海": "https://etax.shanghai.chinatax.gov.cn",
            "重庆": "https://etax.chongqing.chinatax.gov.cn",
            "河北": "https://etax.hebei.chinatax.gov.cn",
            "山西": "https://etax.shanxi.chinatax.gov.cn",
            "辽宁": "https://etax.liaoning.chinatax.gov.cn",
            "吉林": "https://etax.jilin.chinatax.gov.cn",
            "黑龙江": "https://etax.heilongjiang.chinatax.gov.cn",
            "江苏": "https://etax.jiangsu.chinatax.gov.cn",
            "浙江": "https://etax.zhejiang.chinatax.gov.cn",
            "安徽": "https://etax.anhui.chinatax.gov.cn",
            "福建": "https://etax.fujian.chinatax.gov.cn",
            "江西": "https://etax.jiangxi.chinatax.gov.cn",
            "山东": "https://etax.shandong.chinatax.gov.cn",
            "河南": "https://etax.henan.chinatax.gov.cn",
            "湖北": "https://etax.hubei.chinatax.gov.cn",
            "湖南": "https://etax.hunan.chinatax.gov.cn",
            "广东": "https://etax.guangdong.chinatax.gov.cn",
            "海南": "https://etax.hainan.chinatax.gov.cn",
            "四川": "https://etax.sichuan.chinatax.gov.cn",
            "贵州": "https://etax.guizhou.chinatax.gov.cn",
            "云南": "https://etax.yunnan.chinatax.gov.cn",
            "陕西": "https://etax.shaanxi.chinatax.gov.cn",
            "甘肃": "https://etax.gansu.chinatax.gov.cn",
            "内蒙古": "https://etax.neimenggu.chinatax.gov.cn",
            "广西": "https://etax.guangxi.chinatax.gov.cn",
            "西藏": "https://etax.xizang.chinatax.gov.cn",
            "宁夏": "https://etax.ningxia.chinatax.gov.cn",
            "新疆": "https://etax.xinjiang.chinatax.gov.cn",
            "青海": "https://etax.qinghai.chinatax.gov.cn",
        }

        prov = province.replace("省", "").replace("市", "").replace("自治区", "")
        return tax_urls.get(prov, "")


def clear_browser_data():
    """清除浏览器登录数据，下次查询时需要重新登录"""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "browser_data")
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)
        print("浏览器登录数据已清除，下次查询需要重新登录天眼查")
        return True
    return False


def query_business_info_sync(credit_code: str, callback=None):
    """同步方式调用查询（在 GUI 中使用）"""

    async def _run_query():
        query = BusinessQuery()
        try:
            await query.start()
            result = await query.query(credit_code)
            if callback:
                callback(result)
            return result
        finally:
            await query.stop()

    asyncio.run(_run_query())


class BusinessQueryOffline:
    """离线辅助工具"""

    @staticmethod
    def validate_credit_code(credit_code: str) -> bool:
        """验证统一社会信用代码格式"""
        if not credit_code:
            return False
        credit_code = credit_code.strip()
        if len(credit_code) != 18:
            return False
        pattern = r'^[0-9A-Z]{18}$'
        return bool(re.match(pattern, credit_code))
