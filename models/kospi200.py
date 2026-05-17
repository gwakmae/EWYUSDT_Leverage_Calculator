"""미니코스피200 선물 모델."""

from dataclasses import dataclass, field

from config.constants import Kospi200 as Const


@dataclass
class Kospi200Model:
    """미니코스피200 선물 계약 모델."""

    price: float = Const.DEFAULT_PRICE

    @property
    def contract_value(self) -> float:
        """계약가치 (KRW)."""
        return self.price * Const.CONTRACT_MULTIPLIER

    @property
    def initial_margin(self) -> float:
        """위탁증거금 (KRW)."""
        return self.contract_value * (Const.INITIAL_MARGIN_RATE / 100)

    @property
    def maintenance_margin(self) -> float:
        """유지증거금 (KRW)."""
        return self.contract_value * (Const.MAINTENANCE_MARGIN_RATE / 100)

    @property
    def profit_per_point(self) -> float:
        """1포인트 변동 시 손익 (KRW)."""
        return Const.CONTRACT_MULTIPLIER

    def update_price(self, new_price: float) -> None:
        """가격 업데이트."""
        self.price = new_price