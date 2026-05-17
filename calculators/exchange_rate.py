"""환율 조회 서비스."""

import logging
from typing import Optional

import requests

from config.constants import ExchangeRate as Const

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """환율 조회 서비스."""

    def __init__(self):
        self._cached_rate: Optional[float] = None
        self._last_fetch: Optional[float] = None

    def fetch_rate(self, force: bool = False) -> float:
        """서울외국환중개 API에서 환율 조회."""
        import time

        # 60초 이내 재조회 방지 (캐시)
        if not force and self._last_fetch:
            if time.time() - self._last_fetch < 60:
                return self._cached_rate or Const.DEFAULT_RATE

        try:
            response = requests.get(Const.API_URL, timeout=10)
            response.encoding = "utf-8"
            response.raise_for_status()

            # HTML 파싱 - USD 환율 추출
            rate = self._parse_html(response.text)
            if rate:
                self._cached_rate = rate
                self._last_fetch = time.time()
                logger.info(f"환율 조회 성공: {rate}")
                return rate

        except requests.RequestException as e:
            logger.warning(f"환율 API 조회 실패: {e}, 기본값 사용")

        return self._cached_rate or Const.DEFAULT_RATE

    def _parse_html(self, html: str) -> Optional[float]:
        """HTML에서 USD/KRW 환율 파싱."""
        import re

        # 간단한 패턴 매칭 - 실제 사이트 구조에 맞게 조정 필요
        # 예: <td>미국 달러 (USD)</td><td>1,498.50</td>
        patterns = [
            r"미국\s*달러.*?([0-9,]+(?:\.[0-9]+)?)",
            r"USD.*?([0-9,]+(?:\.[0-9]+)?)",
            r">\s*([0-9]{3,4}\.[0-9]{2})\s*<",
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                rate_str = match.group(1).replace(",", "")
                try:
                    return float(rate_str)
                except ValueError:
                    continue

        return None

    @property
    def current_rate(self) -> float:
        """현재 환율 (캐시된 값)."""
        return self._cached_rate or Const.DEFAULT_RATE

    @property
    def last_updated(self) -> Optional[float]:
        """마지막 업데이트 시간."""
        return self._last_fetch


# Singleton instance
_exchange_service: Optional[ExchangeRateService] = None


def get_exchange_service() -> ExchangeRateService:
    """환율 서비스 싱글톤 인스턴스 반환."""
    global _exchange_service
    if _exchange_service is None:
        _exchange_service = ExchangeRateService()
    return _exchange_service