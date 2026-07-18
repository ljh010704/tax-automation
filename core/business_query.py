"""企业信息查询模块
    }
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

    CITY_PROVINCE_MAP = {
        "南宁": "广西壮族自治区", "柳州": "广西壮族自治区", "桂林": "广西壮族自治区",
        "梧州": "广西壮族自治区", "北海": "广西壮族自治区", "崇左": "广西壮族自治区",
        "来宾": "广西壮族自治区", "贺州": "广西壮族自治区", "玉林": "广西壮族自治区",
        "百色": "广西壮族自治区", "钦州": "广西壮族自治区", "河池": "广西壮族自治区",
        "防城港": "广西壮族自治区", "贵港": "广西壮族自治区",
        "广州": "广东省", "深圳": "广东省", "东莞": "广东省", "佛山": "广东省",
        "珠海": "广东省", "惠州": "广东省", "中山": "广东省", "江门": "广东省",
        "湛江": "广东省", "肇庆": "广东省", "汕头": "广东省", "韶关": "广东省",
        "梅州": "广东省", "汕尾": "广东省", "河源": "广东省", "阳江": "广东省",
        "清远": "广东省", "潮州": "广东省", "揭阳": "广东省", "云浮": "广东省",
        "茂名": "广东省",
        "济南": "山东省", "青岛": "山东省", "烟台": "山东省", "潍坊": "山东省",
        "淄博": "山东省", "临沂": "山东省", "济宁": "山东省", "泰安": "山东省",
        "威海": "山东省", "日照": "山东省", "滨州": "山东省", "德州": "山东省",
        "聊城": "山东省", "菏泽": "山东省", "枣庄": "山东省", "东营": "山东省",
        "合肥": "安徽省", "芜湖": "安徽省", "蚌埠": "安徽省", "淮南": "安徽省",
        "马鞍山": "安徽省", "安庆": "安徽省", "阜阳": "安徽省", "亳州": "安徽省",
        "宿州": "安徽省", "滁州": "安徽省", "六安": "安徽省", "宣城": "安徽省",
        "铜陵": "安徽省", "池州": "安徽省", "黄山": "安徽省",
        "福州": "福建省", "厦门": "福建省", "泉州": "福建省", "漳州": "福建省",
        "莆田": "福建省", "龙岩": "福建省", "三明": "福建省", "南平": "福建省",
        "宁德": "福建省",
        "杭州": "浙江省", "宁波": "浙江省", "温州": "浙江省", "嘉兴": "浙江省",
        "湖州": "浙江省", "绍兴": "浙江省", "金华": "浙江省", "衢州": "浙江省",
        "台州": "浙江省", "丽水": "浙江省", "舟山": "浙江省",
        "南京": "江苏省", "苏州": "江苏省", "无锡": "江苏省", "常州": "江苏省",
        "徐州": "江苏省", "南通": "江苏省", "扬州": "江苏省", "镇江": "江苏省",
        "盐城": "江苏省", "淮安": "江苏省", "连云港": "江苏省", "泰州": "江苏省",
        "宿迁": "江苏省",
        "石家庄": "河北省", "唐山": "河北省", "秦皇岛": "河北省",
        "邯郸": "河北省", "邢台": "河北省", "保定": "河北省", "张家口": "河北省",
        "承德": "河北省", "沧州": "河北省", "廊坊": "河北省", "衡水": "河北省",
        "太原": "山西省", "大同": "山西省", "阳泉": "山西省", "长治": "山西省",
        "晋城": "山西省", "朔州": "山西省", "晋中": "山西省", "运城": "山西省",
        "忻州": "山西省", "临汾": "山西省", "吕梁": "山西省",
        "沈阳": "辽宁省", "大连": "辽宁省", "鞍山": "辽宁省", "抚顺": "辽宁省",
        "本溪": "辽宁省", "丹东": "辽宁省", "锦州": "辽宁省", "营口": "辽宁省", "阜新": "辽宁省",
        "辽阳": "辽宁省", "盘锦": "辽宁省", "铁岭": "辽宁省", "朝阳": "辽宁省",
        "葫芦岛": "辽宁省",
        "长春": "吉林省", "吉林市": "吉林省", "四平": "吉林省", "辽源": "吉林省",
        "通化": "吉林省", "白山": "吉林省", "松原": "吉林省", "白城": "吉林省",
        "延边": "吉林省",
        "哈尔滨": "黑龙江省", "齐齐哈尔": "黑龙江省", "大庆": "黑龙江省",
        "鸡西": "黑龙江省", "鹤岗": "黑龙江省", "双鸭山": "黑龙江省",
        "伊春": "黑龙江省", "七台河": "黑龙江省", "牡丹江": "黑龙江省",
        "黑河": "黑龙江省", "绥化": "黑龙江省", "佳木斯": "黑龙江省",
        "郑州": "河南省", "洛阳": "河南省", "开封": "河南省", "安阳": "河南省",
        "新乡": "河南省", "许昌": "河南省", "平顶山": "河南省", "信阳": "河南省",
        "南阳": "河南省", "焦作": "河南省", "濮阳": "河南省", "漯河": "河南省",
        "三门峡": "河南省", "周口": "河南省", "驻马店": "河南省", "商丘": "河南省",
        "鹤壁": "河南省", "济源": "河南省",
        "武汉": "湖北省", "黄石": "湖北省", "十堰": "湖北省", "宜昌": "湖北省",
        "襄阳": "湖北省", "鄂州": "湖北省", "荆门": "湖北省", "孝感": "湖北省",
        "荆州": "湖北省", "黄冈": "湖北省", "咸宁": "湖北省", "随州": "湖北省",
        "仙桃": "湖北省", "天门": "湖北省", "潜江": "湖北省",
        "长沙": "湖南省", "株洲": "湖南省", "湘潭": "湖南省", "衡阳": "湖南省",
        "邵阳": "湖南省", "岳阳": "湖南省", "常德": "湖南省", "益阳": "湖南省",
        "郴州": "湖南省", "永州": "湖南省", "怀化": "湖南省", "娄底": "湖南省",
        "张家界": "湖南省",
        "南昌": "江西省", "九江": "江西省", "景德镇": "江西省", "萍乡": "江西省",
        "新余": "江西省", "鹰潭": "江西省", "赣州": "江西省", "吉安": "江西省",
        "宜春": "江西省", "抚州": "江西省", "上饶": "江西省",
        "成都": "四川省", "绵阳": "四川省", "德阳": "四川省", "宜宾": "四川省",
        "自贡": "四川省", "乐山": "四川省", "泸州": "四川省", "南充": "四川省",
        "广元": "四川省", "遂宁": "四川省", "内江": "四川省", "眉山": "四川省",
        "广安": "四川省", "达州": "四川省", "雅安": "四川省", "巴中": "四川省",
        "资阳": "四川省", "攀枝花": "四川省",
        "贵阳": "贵州省", "遵义": "贵州省", "六盘水": "贵州省", "安顺": "贵州省",
        "毕节": "贵州省", "铜仁": "贵州省", "黔南": "贵州省", "黔东南": "贵州省",
        "黔西南": "贵州省",
        "昆明": "云南省", "曲靖": "云南省", "玉溪": "云南省", "保山": "云南省",
        "昭通": "云南省", "丽江": "云南省", "普洱": "云南省", "临沧": "云南省",
        "大理": "云南省", "红河": "云南省", "德宏": "云南省", "怒江": "云南省",
        "迪庆": "云南省", "楚雄": "云南省", "文山": "云南省", "西双版纳": "云南省",
        "西安": "陕西省", "铜川": "陕西省", "宝鸡": "陕西省", "咸阳": "陕西省",
        "渭南": "陕西省", "延安": "陕西省", "汉中": "陕西省", "榆林": "陕西省",
        "安康": "陕西省", "商洛": "陕西省",
        "兰州": "甘肃省", "嘉峪关": "甘肃省", "金昌": "甘肃省", "白银": "甘肃省",
        "天水": "甘肃省", "武威": "甘肃省", "张掖": "甘肃省", "平凉": "甘肃省",
        "酒泉": "甘肃省", "庆阳": "甘肃省", "定西": "甘肃省", "陇南": "甘肃省",
        "金昌": "甘肃省",
        "西宁": "青海省", "海东": "青海省", "海北": "青海省", "黄南": "青海省",
        "海南": "青海省", "果洛": "青海省", "玉树": "青海省", "海西": "青海省",
        "银川": "宁夏回族自治区", "石嘴山": "宁夏回族自治区", "吴忠": "宁夏回族自治区",
        "固原": "宁夏回族自治区", "中卫": "宁夏回族自治区",
        "拉萨": "西藏自治区", "日喀则": "西藏自治区", "昌都": "西藏自治区",
        "林芝": "西藏自治区", "山南": "西藏自治区", "那曲": "西藏自治区",
        "阿里": "西藏自治区",
        "乌鲁木齐": "新疆维吾尔自治区", "克拉玛依": "新疆维吾尔自治区",
        "吐鲁番": "新疆维吾尔自治区", "哈密": "新疆维吾尔自治区",
        "南宁": "广西壮族自治区",
    }
    
    """企业信息自动查询（保存登录状态）"""

    TIANYANCHA_URL = "https://www.tianyancha.com"
    USER_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "browser_data")

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.headless = False

    async def start(self, save_login: bool = True):
        """鍚姩娴忚鍣?"""
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()

        # Detect if running on server (no display)
        import platform
        is_linux = platform.system() == "Linux"
        headless = is_linux or os.environ.get("PLAYWRIGHT_HEADLESS", "0") == "1"
        self.headless = headless

        # Chrome paths for different OS
        chrome_paths = []
        if platform.system() == "Windows":
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            ]
        elif platform.system() == "Linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
            ]

        chrome_path = None
        for p in chrome_paths:
            if os.path.exists(p):
                chrome_path = p
                break

        os.makedirs(self.USER_DATA_DIR, exist_ok=True)

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
        if not headless:
            launch_args.append("--start-maximized")

        try:
            if chrome_path:
                print(f"浣跨敤绯荤粺 Chrome: {chrome_path} (headless={headless})")
                self.browser = await self.playwright.chromium.launch(
                    headless=headless,
                    executable_path=chrome_path,
                    args=launch_args,
                )
            else:
                print("鏈壘鍒扮郴蘎Chrome锛屼娇鐢?Playwright 鑷甫娴忚鍣")

                self.browser = await self.playwright.chromium.launch(
                    headless=headless,
                    args=launch_args,
                )

            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            self.page = await self.context.new_page()
            await self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        except Exception as e:
            print(f"鍚姩娴忚鍣ㄥけ璐? {e}")
            raise


    async def stop(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
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
                if self.headless:
                    return None  # Headless mode cannot login
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
                        await self.page.goto(href, wait_until="commit", timeout=60000)
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

        # city-to-province fallback
        if not result.get("province") and result.get("city"):
            city_short = result["city"][:-1] if result["city"].endswith("市") else result["city"]
            if city_short in self.CITY_PROVINCE_MAP:
                result["province"] = self.CITY_PROVINCE_MAP[city_short]

        # 城市反查省份后备方案
        if not result.get("province") and result.get("city"):
            city_short = result["city"][:-1] if result["city"].endswith(chr(24066)) else result["city"]
            if self.CITY_PROVINCE_MAP.get(city_short):
                result["province"] = self.CITY_PROVINCE_MAP[city_short]

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

    return asyncio.run(_run_query())


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


def debug_query(credit_code: str):
    """调试查询：返回详细步骤信息"""
    import asyncio
    steps = []

    async def _run():
        from playwright.async_api import async_playwright
        import platform

        is_linux = platform.system() == "Linux"
        headless = is_linux or os.environ.get("PLAYWRIGHT_HEADLESS", "0") == "1"
        steps.append(f"OS: {platform.system()}, headless: {headless}")

        playwright = await async_playwright().start()

        chrome_paths = []
        if platform.system() == "Linux":
            chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium", "/snap/bin/chrome"]
        chrome_path = None
        for p in chrome_paths:
            if os.path.exists(p):
                chrome_path = p
                break

        user_data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "browser_data")
        os.makedirs(user_data_dir, exist_ok=True)

        args = ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]

        if chrome_path:
            steps.append(f"Chrome: {chrome_path}")
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir, headless=headless, executable_path=chrome_path,
                viewport={"width": 1280, "height": 800}, args=args)
        else:
            steps.append("Chrome: Playwright bundled")
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir, headless=headless,
                viewport={"width": 1280, "height": 800}, args=args)

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        search_url = f"https://www.tianyancha.com/search?key={credit_code}"
        steps.append(f"Navigating to: {search_url}")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        current_url = page.url
        steps.append(f"Current URL: {current_url}")

        is_login = any(kw in current_url.lower() for kw in ["/login", "/register", "login?", "register?"])
        steps.append(f"Is login page: {is_login}")

        if is_login and headless:
            steps.append("BLOCKED: Login required in headless mode")
            await context.close()
            await playwright.stop()
            return steps

        # Get page content summary
        content_text = await page.content()
        steps.append(f"Page content length: {len(content_text)}")

        # Check for anti-bot
        if "验证码" in content_text or "captcha" in content_text.lower():
            steps.append("BLOCKED: CAPTCHA/verification detected")
            await context.close()
            await playwright.stop()
            return steps

        # Check for company links
        links = await page.query_selector_all('a[href*="/company/"]')
        steps.append(f"Company links found: {len(links)}")

        # Try to get title
        title = await page.title()
        steps.append(f"Page title: {title}")

        # Take screenshot
        screenshot_path = os.path.join(os.path.dirname(__file__), "..", "debug_screenshot.png")
        await page.screenshot(path=screenshot_path)
        steps.append(f"Screenshot saved: {screenshot_path}")

        await context.close()
        await playwright.stop()
        return steps

    return asyncio.run(_run())
