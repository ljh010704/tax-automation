"""
UI 主题配置 - 统一配色、响应式字体、间距
"""

import customtkinter as ctk

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

# ===== 基础字体大小（参考窗口宽度 1020px） =====
BASE_WIDTH = 1020
BASE_FONT_SIZES = {
    "h1": 18,
    "h2": 14,
    "body": 11,
    "small": 9,
    "mono": 10,
    "button": 11,
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
    """响应式字体管理器 - 根据窗口大小自动缩放字体"""

    def __init__(self, root):
        self.root = root
        self._fonts = {}
        self._scale = 1.0
        self._base_sizes = dict(BASE_FONT_SIZES)
        self._last_scale = -1
        self._create_fonts()
        self._update_fonts()

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

    def bind_resize(self):
        """绑定窗口大小变化事件"""
        self.root.bind("<Configure>", self._on_resize, add="+")

    def _on_resize(self, event):
        """窗口大小变化时更新字体"""
        if event.widget is not self.root:
            return
        width = event.width
        if width <= 1:
            return
        new_scale = max(0.7, min(1.5, width / BASE_WIDTH))
        if abs(new_scale - self._last_scale) < 0.02:
            return
        self._last_scale = new_scale
        self._scale = new_scale
        self._update_fonts()

    def _update_fonts(self):
        """更新所有字体大小"""
        for name, font in self._fonts.items():
            base_size = self._base_sizes.get(name, 11)
            new_size = max(8, int(base_size * self._scale))
            font.configure(size=new_size)


# ===== 兼容旧代码的全局字体变量 =====
FONT_H1 = ("Microsoft YaHei UI", 18, "bold")
FONT_H2 = ("Microsoft YaHei UI", 14, "bold")
FONT_BODY = ("Microsoft YaHei UI", 11)
FONT_SMALL = ("Microsoft YaHei UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_BUTTON = ("Microsoft YaHei UI", 11, "bold")


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
