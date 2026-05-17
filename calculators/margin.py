""" 증거금 계산기 """

from models.kospi200 import Kospi200Model
from models.ewy import EWYModel


class MarginCalculator:
    """증거금 계산 클래스."""

    @staticmethod
    def calculate_kospi200(kospi: Kospi200Model) -> dict[str, float]:
        """미니코스피200 증거금 계산."""
        return {
            "contract_value": kospi.contract_value,
            "initial_margin": kospi.initial_margin,
            "maintenance_margin": kospi.maintenance_margin,
            "leverage": kospi.contract_value / kospi.initial_margin,
        }

    @staticmethod
    def calculate_ewy(ewy: EWYModel) -> dict[str, float]:
        """EWYUSDT 증거금 계산."""
        return {
            "contract_value_usd": ewy.contract_value_usd,
            "contract_value_krw": ewy.contract_value_krw,
            "required_margin": ewy.required_margin,
            "required_margin_10x": ewy.required_margin_10x,
            "required_margin_20x": ewy.required_margin_20x,
            "contracts": ewy.contracts,
            "leverage": float(ewy.safe_leverage),
        }

    @staticmethod
    def compare_margins(
        kospi: Kospi200Model,
        ewy: EWYModel,
    ) -> dict[str, dict[str, float]]:
        """두 계약의 증거금 비교."""
        kospi_margins = MarginCalculator.calculate_kospi200(kospi)
        ewy_margins = MarginCalculator.calculate_ewy(ewy)

        return {
            "kospi200": kospi_margins,
            "ewy": ewy_margins,
        }
