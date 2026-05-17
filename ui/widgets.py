"""Qt UI 위젯들."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QDoubleSpinBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtBoundSignal

from config.constants import EWY, Kospi200, ExchangeRate


class ContractSlider(QWidget):
    """EWY 계약 수량 슬라이더."""

    value_changed: pyqtBoundSignal = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 타이틀
        title = QLabel("EWY 계약 수량")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # 슬라이더 + 값 표시
        slider_layout = QHBoxLayout()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(EWY.MIN_CONTRACTS)
        self.slider.setMaximum(EWY.MAX_CONTRACTS)
        self.slider.setValue(EWY.DEFAULT_CONTRACTS)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self._on_slider_changed)

        self.value_label = QLabel(f"{EWY.DEFAULT_CONTRACTS}")
        self.value_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumWidth(50)

        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.value_label)

        layout.addLayout(slider_layout)

        # 범위 표시
        range_label = QLabel(f"범위: {EWY.MIN_CONTRACTS} ~ {EWY.MAX_CONTRACTS}")
        range_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(range_label)

    def _on_slider_changed(self, value: int) -> None:
        self.value_label.setText(str(value))
        self.value_changed.emit(value)

    def get_value(self) -> int:
        return self.slider.value()

    def set_value(self, value: int) -> None:
        self.slider.setValue(value)


class PriceInput(QWidget):
    """가격 입력 위젯."""

    value_changed: pyqtBoundSignal = pyqtSignal(float)

    def __init__(self, label: str, default_value: float, parent: QWidget | None = None):
        super().__init__(parent)
        self._label_text = label
        self._default_value = default_value
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        label = QLabel(self._label_text)
        label.setMinimumWidth(120)
        layout.addWidget(label)

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(0, 100000)
        self.spinbox.setValue(self._default_value)
        self.spinbox.setDecimals(2)
        self.spinbox.setSingleStep(0.01)
        self.spinbox.valueChanged.connect(self._on_value_changed)

        layout.addWidget(self.spinbox)

    def _on_value_changed(self, value: float) -> None:
        self.value_changed.emit(value)

    def get_value(self) -> float:
        return self.spinbox.value()

    def set_value(self, value: float) -> None:
        self.spinbox.setValue(value)


class ExchangeRateDisplay(QWidget):
    """환율 표시 + 갱신 버튼."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        label = QLabel("USD/KRW 환율:")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self.rate_label = QLabel("1498.00")
        self.rate_label.setStyleSheet("font-size: 16px; color: blue;")
        layout.addWidget(self.rate_label)

        layout.addStretch()

        self.update_button = QLabel("🔄")
        self.update_button.setStyleSheet(
            "padding: 5px; cursor: pointer; font-size: 16px;"
        )
        self.update_button.mousePressEvent = lambda e: self._on_update_click()
        layout.addWidget(self.update_button)

    def _on_update_click(self) -> None:
        # 부모의 환율 갱신 메서드 호출
        pass

    def set_rate(self, rate: float) -> None:
        self.rate_label.setText(f"{rate:.2f}")

    def get_rate(self) -> float:
        return float(self.rate_label.text())


class ComparisonPanel(QWidget):
    """비교 결과 표시 패널."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 제목
        title = QLabel("📊 비교 결과")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # 미니코스피200 섹션
        kospi_group = QGroupBox("미니코스피200 (1계약)")
        kospi_layout = QVBoxLayout()

        self.kospi_contract_value = self._add_row("계약가치:", kospi_layout)
        self.kospi_margin = self._add_row("위탁증거금:", kospi_layout)
        self.kospi_maintenance = self._add_row("유지증거금:", kospi_layout)
        self.kospi_leverage = self._add_row("레버리지:", kospi_layout)
        self.kospi_profit = self._add_row("1포인트 손익:", kospi_layout)

        kospi_group.setLayout(kospi_layout)
        layout.addWidget(kospi_group)

        # EWYUSDT 섹션
        ewy_group = QGroupBox("EWYUSDT")
        ewy_layout = QVBoxLayout()

        self.ewy_contract_value = self._add_row("계약가치:", ewy_layout)
        self.ewy_contracts = self._add_row("계약 수량:", ewy_layout)
        self.ewy_required_margin = self._add_row("필요 증거금:", ewy_layout)
        self.ewy_profit_usd = self._add_row("1포인트 손익(USD):", ewy_layout)
        self.ewy_profit_krw = self._add_row("1포인트 손익(KRW):", ewy_layout)

        ewy_group.setLayout(ewy_layout)
        layout.addWidget(ewy_group)

        # 비교 섹션
        compare_group = QGroupBox("🎯 동일 수익 비교")
        compare_layout = QVBoxLayout()

        self.target_profit = self._add_row("목표 손익:", compare_layout)
        self.ewy_points_needed = self._add_row("EWY 필요 변동폭:", compare_layout)
        self.ewy_percent_needed = self._add_row("EWY 변동률(%):", compare_layout)

        compare_group.setLayout(compare_layout)
        layout.addWidget(compare_group)

        layout.addStretch()

    def _add_row(self, label_text: str, parent_layout: QVBoxLayout) -> QLabel:
        """행 추가 및 레이블 반환."""
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(150)
        row_layout.addWidget(label)

        value_label = QLabel("-")
        value_label.setStyleSheet("color: #333; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row_layout.addWidget(value_label)

        parent_layout.addLayout(row_layout)
        return value_label

    def update_kospi(self, data: dict) -> None:
        """미니코스피200 데이터 업데이트."""
        self.kospi_contract_value.setText(f"₩{data.get('contract_value', 0):,.0f}")
        self.kospi_margin.setText(f"₩{data.get('initial_margin', 0):,.0f}")
        self.kospi_maintenance.setText(f"₩{data.get('maintenance_margin', 0):,.0f}")
        self.kospi_leverage.setText(f"{data.get('leverage', 0):.1f}x")
        self.kospi_profit.setText(f"₩{data.get('profit_per_point', 0):,.0f}")

    def update_ewy(self, data: dict) -> None:
        """EWYUSDT 데이터 업데이트."""
        self.ewy_contract_value.setText(f"${data.get('contract_value_usd', 0):,.2f} (₩{data.get('contract_value_krw', 0):,.0f})")
        self.ewy_contracts.setText(f"{data.get('contracts', 0)} contracts")
        self.ewy_required_margin.setText(f"₩{data.get('required_margin', 0):,.0f}")
        self.ewy_profit_usd.setText(f"${data.get('profit_per_point_usd', 0):,.2f}")
        self.ewy_profit_krw.setText(f"₩{data.get('profit_per_point_krw', 0):,.0f}")

    def update_comparison(self, data: dict) -> None:
        """비교 데이터 업데이트."""
        target = data.get('target_profit', 50000)
        self.target_profit.setText(f"₩{target:,.0f}")

        ewy_points = data.get('ewy_points_needed', 0)
        ewy_price = data.get('ewy_price', 189.87)
        self.ewy_points_needed.setText(f"{ewy_points:.3f} 포인트 (${ewy_points * ewy_price:.2f})")

        percent = (ewy_points / ewy_price * 100) if ewy_price > 0 else 0
        self.ewy_percent_needed.setText(f"{percent:.2f}%")