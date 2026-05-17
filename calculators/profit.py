"""손익 계산기."""

from models.kospi200 import Kospi200Model
from models.ewy import EWYModel
from config.constants import Kospi200 as K200Const


class ProfitCalculator:
    """손익 및 등가 포지션 계산기."""

    @staticmethod
    def calculate_kospi200(kospi: Kospi200Model) -> dict[str, float]:
        """미니코스피200 손익 계산."""
        return {
            "profit_per_point": kospi.profit_per_point,
            "price": kospi.price,
        }

    @staticmethod
    def calculate_ewy(ewy: EWYModel) -> dict[str, float]:
        """EWYUSDT 손익 계산."""
        return {
            "profit_per_point_usd": ewy.profit_per_point_usd,
            "profit_per_point_krw": ewy.profit_per_point_krw,
            "contracts": ewy.contracts,
            "exchange_rate": ewy.exchange_rate,
        }

    @staticmethod
    def calculate_equivalent_position(
        kospi_price: float,
        ewy_price: float,
        contracts: int,
        exchange_rate: float,
    ) -> dict[str, float]:
        """
        코스피200 1포인트 움직임에 대한 EWYUSDT 등가 포지션 계산.
        실시간 가격 비율을 기반으로 정확한 변동폭과 필요 계약 수를 산출합니다.
        """
        if ewy_price <= 0 or exchange_rate <= 0:
            return {
                "price_ratio": 0.0,
                "ewy_move_per_kospi_1pt": 0.0,
                "pnl_per_contract_usd": 0.0,
                "pnl_per_contract_krw": 0.0,
                "contracts_needed_for_50k": 0.0,
                "current_pnl_krw": 0.0,
            }

        # 1. 실시간 가격 비율 (KOSPI ÷ EWY)
        price_ratio = kospi_price / ewy_price

        # 2. 코스피 1포인트 변동 시 EWY 변동폭
        ewy_move_per_kospi_1pt = 1.0 / price_ratio

        # 3. EWY 1계약당 해당 변동 시 손익 (EWY 계약승수 $1 기준)
        pnl_per_contract_usd = ewy_move_per_kospi_1pt * 1.0
        pnl_per_contract_krw = pnl_per_contract_usd * exchange_rate

        # 4. 미니코스피 1포인트 손익(5만원) 대비 등가 계약 수
        target_pnl_krw = K200Const.CONTRACT_MULTIPLIER  # 50,000
        contracts_needed = target_pnl_krw / pnl_per_contract_krw

        # 5. 현재 계약 수로 코스피 1pt 변동 시 예상 손익
        current_pnl_krw = pnl_per_contract_krw * contracts

        return {
            "price_ratio": price_ratio,
            "ewy_move_per_kospi_1pt": ewy_move_per_kospi_1pt,
            "pnl_per_contract_usd": pnl_per_contract_usd,
            "pnl_per_contract_krw": pnl_per_contract_krw,
            "contracts_needed_for_50k": contracts_needed,
            "current_pnl_krw": current_pnl_krw,
        }

    @staticmethod
    def compare_profits(
        kospi: Kospi200Model,
        ewy: EWYModel,
        target_profit: float = 50_000,
    ) -> dict[str, dict[str, float]]:
        """두 계약의 손익 비교."""
        kospi_profit = ProfitCalculator.calculate_kospi200(kospi)
        ewy_profit = ProfitCalculator.calculate_ewy(ewy)

        equivalent = ProfitCalculator.calculate_equivalent_position(
            kospi.price, ewy.price_usd, ewy.contracts, ewy.exchange_rate
        )

        return {
            "kospi200": kospi_profit,
            "ewy": ewy_profit,
            "equivalent": equivalent,
        }