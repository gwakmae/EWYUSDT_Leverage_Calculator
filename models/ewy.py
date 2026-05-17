"""EWYUSDT 선물 모델."""

from dataclasses import dataclass

from config.constants import EWY as Const


@dataclass
class EWYModel:
    """EWYUSDT 계약 모델."""

    price_usd: float = Const.DEFAULT_PRICE
    contracts: int = Const.DEFAULT_CONTRACTS
    exchange_rate: float = 1498.0  # KRW per USD
    leverage: int = Const.DEFAULT_LEVERAGE

    @property
    def contract_value_usd(self) -> float:
        """계약가치 (USD)."""
        return self.price_usd * Const.CONTRACT_VALUE_USD * self.contracts

    @property
    def contract_value_krw(self) -> float:
        """계약가치 (KRW)."""
        return self.contract_value_usd * self.exchange_rate

    @property
    def safe_leverage(self) -> int:
        """유효 레버리지."""
        return max(Const.MIN_LEVERAGE, min(Const.MAX_LEVERAGE, int(self.leverage)))

    @property
    def required_margin(self) -> float:
        """현재 레버리지 기준 필요 증거금 (KRW)."""
        return self.required_margin_at_leverage(self.safe_leverage)

    @property
    def required_margin_10x(self) -> float:
        """10배 레버리지 기준 필요 증거금 (KRW)."""
        return self.required_margin_at_leverage(10)

    @property
    def required_margin_20x(self) -> float:
        """20배 레버리지 기준 필요 증거금 (KRW)."""
        return self.required_margin_at_leverage(20)

    @property
    def profit_per_point_usd(self) -> float:
        """1포인트 변동 시 손익 (USD)."""
        return Const.CONTRACT_VALUE_USD * self.contracts

    @property
    def profit_per_point_krw(self) -> float:
        """1포인트 변동 시 손익 (KRW)."""
        return self.profit_per_point_usd * self.exchange_rate

    def required_margin_at_leverage(self, leverage: int | float) -> float:
        """특정 레버리지 기준 필요 증거금."""
        lev = max(Const.MIN_LEVERAGE, min(Const.MAX_LEVERAGE, float(leverage)))

        if lev <= 0:
            return self.contract_value_krw

        return self.contract_value_krw / lev

    def points_for_target_profit(self, target_krw: float) -> float:
        """목표 손익(KRW)을 위한 필요 변동폭 (EWY 포인트)."""
        return target_krw / self.exchange_rate / self.contracts

    def update_price(self, new_price: float) -> None:
        """가격 업데이트."""
        self.price_usd = new_price

    def update_contracts(self, new_contracts: int) -> None:
        """계약 수량 업데이트."""
        self.contracts = max(
            Const.MIN_CONTRACTS,
            min(Const.MAX_CONTRACTS, new_contracts),
        )

    def update_exchange_rate(self, rate: float) -> None:
        """환율 업데이트."""
        self.exchange_rate = rate

    def update_leverage(self, leverage: int) -> None:
        """레버리지 업데이트."""
        self.leverage = max(
            Const.MIN_LEVERAGE,
            min(Const.MAX_LEVERAGE, leverage),
        )
