"""EWYUSDT vs 미니코스피200 레버리지 계산기."""

import sys
import logging

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

logging.basicConfig(level=logging.INFO)


def main() -> int:
    """메인 함수."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())