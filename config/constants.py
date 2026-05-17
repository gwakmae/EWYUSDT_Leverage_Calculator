"""Trading constants and configuration."""


class Kospi200:
    """미니코스피200 선물 계약 상수."""

    # 계약 승수: 1포인트 = 50,000원
    CONTRACT_MULTIPLIER: int = 50_000

    # 증거금률 (%)
    INITIAL_MARGIN_RATE: float = 19.200
    MAINTENANCE_MARGIN_RATE: float = 12.800

    # 기본값
    DEFAULT_PRICE: float = 1240.10


class EWY:
    """EWYUSDT 계약 상수."""

    CONTRACT_VALUE_USD: float = 1.0

    MIN_CONTRACTS: int = 1
    MAX_CONTRACTS: int = 500
    DEFAULT_CONTRACTS: int = 1

    # 레버리지
    MIN_LEVERAGE: int = 1
    MAX_LEVERAGE: int = 20
    DEFAULT_LEVERAGE: int = 10

    DEFAULT_PRICE: float = 189.87


class ExchangeRate:
    """환율 관련 상수."""

    API_URL: str = "http://www.smbs.biz/ExRate/StdExRate.jsp"
    DEFAULT_RATE: float = 1498.0

    MIN_LEVERAGE: float = 1.0
    MAX_LEVERAGE: float = 20.0
    DEFAULT_LEVERAGE: float = 1.0
