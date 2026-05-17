"""메인 윈도우에서 사용하는 UI 패널들."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QDoubleSpinBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.constants import Kospi200 as K200Const, EWY as EWYConst


class TitlePanel(QWidget):
    """상단 타이틀 패널."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("EWYUSDT vs 미니코스피200 등가 포지션 계산기")

        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)

        title.setFont(title_font)

        layout.addWidget(title)


class PriceInputPanel(QGroupBox):
    """가격 입력 및 시세 조회 패널."""

    kospi_changed = pyqtSignal(float)
    ewy_changed = pyqtSignal(float)
    refresh_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("가격 입력", parent)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        input_layout = QVBoxLayout(self)

        price_row = QHBoxLayout()

        price_row.addWidget(QLabel("코스피200:"))

        self.kospi_input = QDoubleSpinBox()
        self.kospi_input.setRange(0, 100000)
        self.kospi_input.setDecimals(2)
        self.kospi_input.setValue(K200Const.DEFAULT_PRICE)
        price_row.addWidget(self.kospi_input)

        price_row.addWidget(QLabel("EWYUSDT:"))

        self.ewy_input = QDoubleSpinBox()
        self.ewy_input.setRange(0, 10000)
        self.ewy_input.setDecimals(4)
        self.ewy_input.setValue(EWYConst.DEFAULT_PRICE)
        price_row.addWidget(self.ewy_input)

        self.refresh_price_btn = QPushButton("🔄 시세 수동 갱신 (MT5+Binance)")
        self.refresh_price_btn.setToolTip(
            "KST 기준 특정 시각의 MT5 KS200과 Binance EWYUSDT 15분봉 시가를 동일 UTC로 조회"
        )
        self.refresh_price_btn.setFixedHeight(36)
        price_row.addWidget(self.refresh_price_btn)

        input_layout.addLayout(price_row)

        time_row = QHBoxLayout()
        time_row.setSpacing(8)

        time_title = QLabel("조회 기준:")
        time_title.setFixedWidth(75)
        time_title.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        time_row.addWidget(time_title)

        self.candle_time_label = QLabel("—")
        self.candle_time_label.setWordWrap(True)
        self.candle_time_label.setMinimumWidth(620)
        self.candle_time_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.candle_time_label.setStyleSheet(
            """
            QLabel {
                color: #1565c0;
                font-weight: bold;
                padding: 6px 10px;
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 6px;
            }
            """
        )

        time_row.addWidget(self.candle_time_label, stretch=1)

        input_layout.addLayout(time_row)

    def _connect_signals(self) -> None:
        self.kospi_input.valueChanged.connect(self.kospi_changed.emit)
        self.ewy_input.valueChanged.connect(self.ewy_changed.emit)
        self.refresh_price_btn.clicked.connect(self.refresh_requested.emit)

    def set_prices(
        self,
        kospi_price: float | None = None,
        ewy_price: float | None = None,
    ) -> None:
        """입력창 가격 업데이트."""
        if kospi_price is not None:
            self.kospi_input.blockSignals(True)
            self.kospi_input.setValue(kospi_price)
            self.kospi_input.blockSignals(False)

        if ewy_price is not None:
            self.ewy_input.blockSignals(True)
            self.ewy_input.setValue(ewy_price)
            self.ewy_input.blockSignals(False)

    def set_time_text(self, text: str) -> None:
        """조회 기준 시각 텍스트 업데이트."""
        self.candle_time_label.setText(text)

    def set_tooltips(
        self,
        kospi_tooltip: str | None = None,
        ewy_tooltip: str | None = None,
    ) -> None:
        """가격 입력칸 툴팁 업데이트."""
        if kospi_tooltip is not None:
            self.kospi_input.setToolTip(kospi_tooltip)

        if ewy_tooltip is not None:
            self.ewy_input.setToolTip(ewy_tooltip)

    def set_loading(self, loading: bool) -> None:
        """조회 버튼 로딩 상태 변경."""
        self.refresh_price_btn.setEnabled(not loading)

        if loading:
            self.refresh_price_btn.setText("⏳ MT5/Binance 조회 중...")
        else:
            self.refresh_price_btn.setText("🔄 시세 수동 갱신 (MT5+Binance)")


class ExchangeRatePanel(QWidget):
    """환율 표시 및 갱신 패널."""

    refresh_requested = pyqtSignal()

    def __init__(self, exchange_rate: float, parent: QWidget | None = None):
        super().__init__(parent)

        self.exchange_rate = exchange_rate

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("USD/KRW 환율:"))

        self.rate_label = QLabel(f"{self.exchange_rate:.2f}")
        self.rate_label.setStyleSheet("color: blue; font-weight: bold;")

        layout.addWidget(self.rate_label)
        layout.addStretch()

        self.refresh_rate_btn = QPushButton("🔄 환율 갱신")
        layout.addWidget(self.refresh_rate_btn)

    def _connect_signals(self) -> None:
        self.refresh_rate_btn.clicked.connect(self.refresh_requested.emit)

    def set_rate(self, rate: float) -> None:
        """환율 표시 업데이트."""
        self.exchange_rate = rate
        self.rate_label.setText(f"{rate:.2f}")

    def set_loading(self, loading: bool) -> None:
        """환율 버튼 로딩 상태 변경."""
        self.refresh_rate_btn.setEnabled(not loading)

        if loading:
            self.refresh_rate_btn.setText("⏳ 환율 조회 중...")
        else:
            self.refresh_rate_btn.setText("🔄 환율 갱신")


class ContractsPanel(QGroupBox):
    """EWY 계약 수량 슬라이더 패널."""

    contracts_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__("EWY 계약 수량", parent)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        slider_layout = QHBoxLayout(self)

        self.contracts_slider = QSlider(Qt.Orientation.Horizontal)
        self.contracts_slider.setMinimum(EWYConst.MIN_CONTRACTS)
        self.contracts_slider.setMaximum(EWYConst.MAX_CONTRACTS)
        self.contracts_slider.setValue(EWYConst.DEFAULT_CONTRACTS)
        self.contracts_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.contracts_slider.setTickInterval(50)
        self.contracts_slider.setSingleStep(1)
        slider_layout.addWidget(self.contracts_slider)

        self.contracts_label = QLabel(str(EWYConst.DEFAULT_CONTRACTS))
        self.contracts_label.setStyleSheet("font-weight: bold; min-width: 30px;")
        self.contracts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slider_layout.addWidget(self.contracts_label)

    def _connect_signals(self) -> None:
        self.contracts_slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, value: int) -> None:
        self.contracts_label.setText(str(value))
        self.contracts_changed.emit(value)

    def set_value(self, value: int) -> None:
        self.contracts_slider.setValue(value)


class LeveragePanel(QGroupBox):
    """EWY 레버리지 슬라이더 패널."""

    leverage_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__("EWY 레버리지", parent)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)

        self.leverage_slider = QSlider(Qt.Orientation.Horizontal)
        self.leverage_slider.setMinimum(EWYConst.MIN_LEVERAGE)
        self.leverage_slider.setMaximum(EWYConst.MAX_LEVERAGE)
        self.leverage_slider.setValue(EWYConst.DEFAULT_LEVERAGE)
        self.leverage_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.leverage_slider.setTickInterval(1)
        self.leverage_slider.setSingleStep(1)
        layout.addWidget(self.leverage_slider)

        self.leverage_label = QLabel(f"{EWYConst.DEFAULT_LEVERAGE}x")
        self.leverage_label.setStyleSheet(
            "font-weight: bold; min-width: 45px; color: #d32f2f;"
        )
        self.leverage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.leverage_label)

    def _connect_signals(self) -> None:
        self.leverage_slider.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self, value: int) -> None:
        self.leverage_label.setText(f"{value}x")
        self.leverage_changed.emit(value)

    def set_value(self, value: int) -> None:
        self.leverage_slider.setValue(value)


class ResultGroup(QGroupBox):
    """결과 표시 공통 베이스."""

    def _add_result_row(
        self,
        label_text: str,
        parent_layout: QVBoxLayout,
        highlight: bool = False,
    ) -> QLabel:
        row_layout = QHBoxLayout()

        label = QLabel(label_text)
        label.setMinimumWidth(200)
        row_layout.addWidget(label)

        value_label = QLabel("-")

        if highlight:
            value_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        else:
            value_label.setStyleSheet("font-weight: bold;")

        row_layout.addWidget(value_label)

        parent_layout.addLayout(row_layout)

        return value_label


class KospiResultPanel(ResultGroup):
    """미니코스피200 결과 패널."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("📊 미니코스피200 (1계약)", parent)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.value_label = self._add_result_row("계약가치:", layout)
        self.margin_label = self._add_result_row("위탁증거금:", layout)
        self.maint_label = self._add_result_row("유지증거금:", layout)
        self.lever_label = self._add_result_row("레버리지:", layout)
        self.profit_label = self._add_result_row(
            "1포인트 손익:",
            layout,
            highlight=True,
        )

    def update_result(self, data: dict[str, float], profit_per_point: float) -> None:
        self.value_label.setText(f"{data['contract_value']:,.0f} KRW")
        self.margin_label.setText(f"{data['initial_margin']:,.0f} KRW")
        self.maint_label.setText(f"{data['maintenance_margin']:,.0f} KRW")
        self.lever_label.setText(f"{data['leverage']:.1f}x")
        self.profit_label.setText(f"{profit_per_point:,.0f} KRW")


class EWYResultPanel(ResultGroup):
    """EWYUSDT 결과 패널."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("📊 EWYUSDT", parent)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.contracts_label = self._add_result_row("계약 수량:", layout)
        self.leverage_label = self._add_result_row("현재 레버리지:", layout)
        self.value_label = self._add_result_row("계약가치:", layout)

        self.margin_label = self._add_result_row(
            "필요 증거금:",
            layout,
            highlight=True,
        )
        self.margin_10x_label = self._add_result_row(
            "10배 레버리지 증거금:",
            layout,
        )
        self.margin_20x_label = self._add_result_row(
            "20배 레버리지 증거금:",
            layout,
        )

        self.profit_usd_label = self._add_result_row("EWY $1 변동 시 USD:", layout)
        self.profit_krw_label = self._add_result_row(
            "EWY $1 변동 시 KRW:",
            layout,
            highlight=True,
        )

    def update_result(
        self,
        margin_data: dict[str, float],
        profit_data: dict[str, float],
    ) -> None:
        leverage = margin_data["leverage"]

        self.contracts_label.setText(f"{margin_data['contracts']} contracts")
        self.leverage_label.setText(f"{leverage:.0f}x")

        self.value_label.setText(
            f"${margin_data['contract_value_usd']:,.2f} "
            f"({margin_data['contract_value_krw']:,.0f} KRW)"
        )

        self.margin_label.setText(
            f"{margin_data['required_margin']:,.0f} KRW "
            f"({leverage:.0f}x 기준)"
        )
        self.margin_10x_label.setText(
            f"{margin_data['required_margin_10x']:,.0f} KRW"
        )
        self.margin_20x_label.setText(
            f"{margin_data['required_margin_20x']:,.0f} KRW"
        )

        self.profit_usd_label.setText(f"${profit_data['profit_per_point_usd']:.2f}")
        self.profit_krw_label.setText(
            f"{profit_data['profit_per_point_krw']:,.0f} KRW"
        )


class EquivalentPositionPanel(ResultGroup):
    """코스피200 1포인트 등가 EWY 포지션 패널."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("🎯 코스피200 1포인트 등가 EWY 포지션", parent)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.ratio_label = self._add_result_row("KOSPI / EWY 가격 비율:", layout)
        self.ewy_move_label = self._add_result_row(
            "코스피 1pt ↔ EWY 변동폭:",
            layout,
            highlight=True,
        )
        self.pnl_per_contract_label = self._add_result_row(
            "EWY 1계약당 원화 손익:",
            layout,
        )
        self.contracts_needed_label = self._add_result_row(
            "5만원 등가 필요 계약 수:",
            layout,
            highlight=True,
        )
        self.current_pnl_label = self._add_result_row(
            "현재 계약 시 코스피 1pt 손익:",
            layout,
        )

    def update_result(self, data: dict[str, float]) -> None:
        self.ratio_label.setText(f"{data['price_ratio']:.4f}")
        self.ewy_move_label.setText(f"{data['ewy_move_per_kospi_1pt']:.5f} pt")
        self.pnl_per_contract_label.setText(
            f"{data['pnl_per_contract_krw']:,.0f} KRW"
        )
        self.contracts_needed_label.setText(
            f"{data['contracts_needed_for_50k']:.1f} contracts"
        )
        self.current_pnl_label.setText(f"{data['current_pnl_krw']:,.0f} KRW")
