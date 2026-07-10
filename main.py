"""税务记账助手 - 主程序入口"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from gui.main_window import MainWindow


def main():
    """主函数"""
    print("正在启动税务记账助手...")
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
