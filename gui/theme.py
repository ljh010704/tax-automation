"""
UI 主题配置 - 统一配色、字体、间距
"""

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

# ===== 字体层级 =====
FONT_H1 = ("Microsoft YaHei UI", 18, "bold")
FONT_H2 = ("Microsoft YaHei UI", 14, "bold")
FONT_BODY = ("Microsoft YaHei UI", 11)
FONT_SMALL = ("Microsoft YaHei UI", 9)
FONT_MONO = ("Consolas", 10)
FONT_BUTTON = ("Microsoft YaHei UI", 11, "bold")

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

# ===== 组件常量 =====
class Theme:
    @staticmethod
    def color(name, mode=0):
        """获取颜色，mode=0 浅色, mode=1 深色"""
        return COLORS.get(name, ["#000000", "#000000"])[mode]

    @staticmethod
    def set_appearance(mode="light"):
        """设置全局主题: 'light', 'dark', 'system'"""
        import customtkinter as ctk
        ctk.set_appearance_mode(mode)

    @staticmethod
    def set_color_theme(theme="blue"):
        """设置颜色主题"""
        import customtkinter as ctk
        ctk.set_default_color_theme(theme)
