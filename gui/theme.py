"""
UI 主题配置 - 统一配色、响应式字体、间距
"""

import customtkinter as ctk
import math

# ===== 配色方案 =====
COLORS = {
    "primary": ["#3B82F6", "#2563EB"],
    "primary_hover": ["#2563EB", "#1D4ED8"],
    "success": ["#10B981", "#059669"],
    "success_hover": ["#059669", "#047857"],
    "warning": ["#F59E0B", "#D97706"],
    "danger": ["#EF4444", "#DC2626"],
    "danger_hover": ["#DC2626", "#B91C1C"],
    "gray": ["#6B7280", "#4B5563"],
    "gray_light": ["#F3F4F6", "#E5E7EB"],
    "bg": ["#FFFFFF", "#F9FAFB"],
    "card": ["#FFFFFF", "#FFFFFF"],
    "text": ["#111827", "#374151"],
    "text_light": ["#6B7280", "#9CA3AF"],
    "border": ["#E5E7EB", "#D1D5DB"],
    "sidebar": ["#1E293B", "#0F172A"],
    "sidebar_text": ["#FFFFFF", "#FFFFFF"],
}

# ===== 基础字体大小（基于窗口初始尺寸）=====
BASE_FONT_SIZES = {
    "h1": 20,
    "h2": 16,
    "body": 14,
    "small": 11,
    "mono": 12,
    "button": 14,
}

# ===== 间距 =====
PAD_XS = 4
PAD_SM = 8
PAD_MD = 12
PAD_LG = 16
PAD_XL = 24

# ===== 尺寸 =====
CORNER_RADIUS = 8
BUTTON_HEIGHT = 36
ENTRY_HEIGHT = 36
SIDEBAR_WIDTH = 200


class ResponsiveFont:
    """响应式字体管理器 - 基于窗口大小实时缩放字体"""

    def __init__(self, window=None):
        self._fonts = {}
        self._scale = 1.0
        self._base_sizes = dict(BASE_FONT_SIZES)
        self._window = window
        self._base_width = None
        self._initialized = False
        self._create_fonts()
        if window is not None:
            window.bind("<Configure>", self._on_configure, add="+")

    def _create_fonts(self):
        """创建 CTkFont 对象"""
        self._fonts["h1"] = ctk.CTkFont(family="Microsoft YaHei UI", weight="bold")
        self._fonts["h2"] = ctk.CTkFont(family="Microsoft YaHei UI", weight="bold")
        self._fonts["body"] = ctk.CTkFont(family="Microsoft YaHei UI")
        self._fonts["small"] = ctk.CTkFont(family="Microsoft YaHei UI")
        self._fonts["mono"] = ctk.CTkFont(family="Consolas")
        self._fonts["button"] = ctk.CTkFont(family="Microsoft YaHei UI", weight="bold")

    def get(self, name):
        """获取字体对象"""
        return self._fonts[name]

    def _on_configure(self, event):
        """窗口配置事件 - 处理首次初始化和后续缩放"""
        # 确保是顶层窗口的事件（避免子组件触发）
        if event.widget != self._window:
            return
        if not self._initialized:
            self._base_width = event.width
            self._initialized = True
            self._update_fonts(event.width)
        else:
            self._update_fonts(event.width)

    def _update_fonts(self, current_width):
        """根据当前窗口宽度更新字体大小"""
        if self._base_width and self._base_width > 0:
            scale = max(0.8, min(1.5, math.sqrt(current_width / self._base_width)))
        else:
            scale = 1.0
        self._scale = scale
        for name, font in self._fonts.items():
            base_size = self._base_sizes.get(name, 14)
            new_size = max(8, int(base_size * scale))
            font.configure(size=new_size)

    def bind_resize(self):
        """兼容接口 - 无实际操作（已在初始化时绑定）"""
        pass


# ===== 兼容旧代码的全局字体变量 =====
FONT_H1 = ("Microsoft YaHei UI", 20, "bold")
FONT_H2 = ("Microsoft YaHei UI", 16, "bold")
FONT_BODY = ("Microsoft YaHei UI", 14)
FONT_SMALL = ("Microsoft YaHei UI", 11)
FONT_MONO = ("Consolas", 12)
FONT_BUTTON = ("Microsoft YaHei UI", 14, "bold")


class Theme:
    @staticmethod
    def color(name, mode=0):
        return COLORS.get(name, ["#000000", "#000000"])[mode]

    @staticmethod
    def set_appearance(mode="light"):
        ctk.set_appearance_mode(mode)

    @staticmethod
    def set_color_theme(theme="blue"):
        ctk.set_default_color_theme(theme)


