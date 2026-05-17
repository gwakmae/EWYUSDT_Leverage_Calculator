"""메인 윈도우 - PyQt6."""

import logging
import threading

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot

from config.constants import Kospi200 as K200Const, EWY as EWYConst
from calculators.profit import ProfitCalculator
from calculators.margin import MarginCalculator
from calculators.exchange_rate import get_exchange_service
from services.market_data import fetch_synced_prices_at_kst
from models.kospi200 import Kospi200Model
from models.ewy import EWYModel

from ui.panels import (
    TitlePanel,
    PriceInputPanel,
    ExchangeRatePanel,
    ContractsPanel,
    KospiResultPanel,
    EWYResultPanel,
    EquivalentPositionPanel,
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """메인 윈도우.

    역할:
    - 전체 UI 패널 배치
    - 사용자 입력 이벤트 연결
    - 백그라운드 시세/환율 조회
    - 계산 결과를 패널에 전달
    """

    # 백그라운드 스레드 -> 메인 스레드 UI 업데이트용 시그널
    # kospi_price, ewy_price, kospi_ok, ewy_ok, candle_time_str
    fetch_completed = pyqtSignal(float, float, bool, bool, str)

    # 환율 조회 완료 시그널
    rate_completed = pyqtSignal(float)

    def __init__(self):
        super().__init__()

        self.exchange_service = get_exchange_service()
        self.exchange_rate = self.exchange_service.fetch_rate()

        self.kospi_price = K200Const.DEFAULT_PRICE
        self.ewy_price = EWYConst.DEFAULT_PRICE
        self.contracts = EWYConst.DEFAULT_CONTRACTS

        self._setup_ui()
        self._connect_signals()
        self._update_display()

        # 환율 자동 갱신 타이머, 5분
        self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._on_refresh_rate)
        self._rate_timer.start(300000)

    def _setup_ui(self) -> None:
        """UI 구성."""
        self.setWindowTitle("EWYUSDT vs 미니코스피200 등가 포지션 계산기")
        self.setMinimumWidth(900)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)

        self.title_panel = TitlePanel()
        main_layout.addWidget(self.title_panel)

        self.price_panel = PriceInputPanel()
        main_layout.addWidget(self.price_panel)

        self.exchange_rate_panel = ExchangeRatePanel(self.exchange_rate)
        main_layout.addWidget(self.exchange_rate_panel)

        self.contracts_panel = ContractsPanel()
        main_layout.addWidget(self.contracts_panel)

        self.kospi_result_panel = KospiResultPanel()
        main_layout.addWidget(self.kospi_result_panel)

        self.ewy_result_panel = EWYResultPanel()
        main_layout.addWidget(self.ewy_result_panel)

        self.equivalent_panel = EquivalentPositionPanel()
        main_layout.addWidget(self.equivalent_panel)

        main_layout.addStretch()

    def _connect_signals(self) -> None:
        """시그널 연결."""
        self.price_panel.kospi_changed.connect(self._on_kospi_changed)
        self.price_panel.ewy_changed.connect(self._on_ewy_changed)
        self.price_panel.refresh_requested.connect(self._on_refresh_prices)

        self.exchange_rate_panel.refresh_requested.connect(self._on_refresh_rate)

        self.contracts_panel.contracts_changed.connect(self._on_contracts_changed)

        self.fetch_completed.connect(self._update_ui_from_fetch)
        self.rate_completed.connect(self._update_rate_from_fetch)

    def _on_kospi_changed(self, value: float) -> None:
        self.kospi_price = value
        self._update_display()

    def _on_ewy_changed(self, value: float) -> None:
        self.ewy_price = value
        self._update_display()

    def _on_contracts_changed(self, value: int) -> None:
        self.contracts = value
        self._update_display()

    def _on_refresh_rate(self) -> None:
        """환율 갱신."""
        self.exchange_rate_panel.set_loading(True)

        def fetch():
            try:
                rate = self.exchange_service.fetch_rate(force=True)
                self.rate_completed.emit(rate)

            except Exception as e:
                logger.exception(f"환율 조회 중 예외 발생: {e}")
                self.rate_completed.emit(self.exchange_rate)

        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(float)
    def _update_rate_from_fetch(self, rate: float) -> None:
        """환율 조회 결과를 UI에 반영."""
        self.exchange_rate = rate
        self.exchange_rate_panel.set_rate(rate)
        self.exchange_rate_panel.set_loading(False)
        self._update_display()

    def _on_refresh_prices(self) -> None:
        """시세 수동 갱신.

        현재 기준:
        - 최근 실제 거래 가능일의 KST 09:00 15분봉 시가
        - MT5 KS200과 Binance EWYUSDT를 같은 UTC open time으로 조회
        - 두 UTC 시간이 같을 때만 성공 처리
        """
        self.price_panel.set_loading(True)

        def fetch():
            try:
                # 기준 시각 설정
                # 09:00 KST를 사용
                # 08:45 KST를 원하면 hour=8, minute=45로 변경
                result = fetch_synced_prices_at_kst(hour=8, minute=45)

                if result is None:
                    self.fetch_completed.emit(
                        self.kospi_price,
                        self.ewy_price,
                        False,
                        False,
                        "동기화 조회 실패",
                    )
                    return

                time_str = (
                    f"✅ 동기화 완료\n"
                    f"기준: {result.common_time_kst.strftime('%Y-%m-%d %H:%M')} KST 15분봉 시가\n"
                    f"UTC {result.common_time_utc.strftime('%Y-%m-%d %H:%M')} | "
                    f"브로커 {result.common_time_broker.strftime('%H:%M')} GMT+3"
                )


                self.fetch_completed.emit(
                    result.kospi_price,
                    result.ewy_price,
                    True,
                    True,
                    time_str,
                )

            except Exception as e:
                logger.exception(f"시세 동기화 조회 중 예외 발생: {e}")

                self.fetch_completed.emit(
                    self.kospi_price,
                    self.ewy_price,
                    False,
                    False,
                    f"조회 실패: {e}",
                )

        threading.Thread(target=fetch, daemon=True).start()

    @pyqtSlot(float, float, bool, bool, str)
    def _update_ui_from_fetch(
        self,
        kospi_price: float,
        ewy_price: float,
        kospi_ok: bool,
        ewy_ok: bool,
        time_str: str,
    ) -> None:
        """API/MT5에서 가져온 시세로 UI 업데이트."""
        self.price_panel.set_time_text(time_str)

        kospi_tooltip = None
        ewy_tooltip = None

        if kospi_ok:
            self.kospi_price = kospi_price
            kospi_tooltip = f"MT5 Zero Markets KS200 | {time_str}"

        if ewy_ok:
            self.ewy_price = ewy_price
            ewy_tooltip = f"Binance Futures EWYUSDT | {time_str}"

        self.price_panel.set_prices(
            kospi_price=self.kospi_price if kospi_ok else None,
            ewy_price=self.ewy_price if ewy_ok else None,
        )

        self.price_panel.set_tooltips(
            kospi_tooltip=kospi_tooltip,
            ewy_tooltip=ewy_tooltip,
        )

        self.price_panel.set_loading(False)
        self._update_display()

    def _update_display(self) -> None:
        """계산 결과를 각 결과 패널에 반영."""
        kospi_model = Kospi200Model(price=self.kospi_price)

        ewy_model = EWYModel(
            price_usd=self.ewy_price,
            contracts=self.contracts,
            exchange_rate=self.exchange_rate,
        )

        # 미니코스피200
        kospi_margin = MarginCalculator.calculate_kospi200(kospi_model)

        self.kospi_result_panel.update_result(
            kospi_margin,
            kospi_model.profit_per_point,
        )

        # EWYUSDT
        ewy_margin = MarginCalculator.calculate_ewy(ewy_model)
        ewy_profit = ProfitCalculator.calculate_ewy(ewy_model)

        self.ewy_result_panel.update_result(ewy_margin, ewy_profit)

        # 등가 포지션
        equivalent = ProfitCalculator.calculate_equivalent_position(
            self.kospi_price,
            self.ewy_price,
            self.contracts,
            self.exchange_rate,
        )

        self.equivalent_panel.update_result(equivalent)
