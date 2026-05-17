"""시장 데이터 조회 서비스 (MT5 + Binance).

핵심 원칙:
- 사용자가 원하는 KST 기준 시각 근처에서 MT5 KS200 15분봉을 조회한다.
- MT5가 실제로 반환한 KS200 봉의 UTC 시간을 최종 기준 시간으로 사용한다.
- Binance EWYUSDT는 그 MT5 실제 UTC 시간과 정확히 같은 15분봉만 조회한다.
- GUI에는 요청 시간이 아니라 실제 사용된 공통 시간을 표시한다.

이 방식의 이유:
- 일부 MT5 브로커/상품은 사용자가 기대한 KST 09:00 봉을 정확히 반환하지 않고,
  KST 08:45 봉만 반환할 수 있다.
- 사용자의 핵심 요구사항은 특정 시각 고정이 아니라
  KS200과 EWYUSDT가 반드시 같은 시각이어야 한다는 것이다.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, time
from typing import Optional

import MetaTrader5 as mt5
import pandas as pd
import requests

from config.settings import BROKERS

logger = logging.getLogger(__name__)

UTC = timezone.utc
KST = timezone(timedelta(hours=9), "KST")
BROKER_TZ = timezone(timedelta(hours=3), "GMT+3")

_KS200_SYMBOL = "KS200"
_BINANCE_SYMBOL = "EWYUSDT"

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/ticker/price"
_BINANCE_KLINES_URL = "https://fapi.binance.com/fapi/v1/klines"


@dataclass
class SyncedMarketData:
    """KS200 / EWYUSDT 동기화 조회 결과."""

    kospi_price: float
    ewy_price: float

    # 실제로 두 상품 조회에 사용된 공통 시간
    common_time_utc: datetime
    common_time_kst: datetime
    common_time_broker: datetime

    # 각 소스가 실제 반환한 봉 시간
    mt5_time_utc: datetime
    binance_time_utc: datetime

    # 최초 요청 기준 시간
    requested_time_utc: datetime
    requested_time_kst: datetime
    requested_time_broker: datetime

    kospi_source: str = "MT5 KS200 15m open"
    ewy_source: str = "Binance EWYUSDT 15m open"

    @property
    def is_synced(self) -> bool:
        """MT5와 Binance의 UTC 봉 시작 시간이 같은지 여부."""
        return int(self.mt5_time_utc.timestamp()) == int(
            self.binance_time_utc.timestamp()
        )

    @property
    def used_requested_exactly(self) -> bool:
        """요청한 시간과 실제 사용 시간이 같은지 여부."""
        return int(self.common_time_utc.timestamp()) == int(
            self.requested_time_utc.timestamp()
        )


def _to_utc(dt: datetime) -> datetime:
    """datetime을 UTC aware datetime으로 변환."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _connect_mt5() -> bool:
    """MT5 초기화 및 로그인."""
    broker_cfg = BROKERS.get("Zero Markets", {})

    if not broker_cfg.get("path"):
        logger.warning("Zero Markets MT5 경로가 설정되지 않았습니다.")
        return False

    if not mt5.initialize(path=broker_cfg["path"]):
        logger.warning(f"MT5 초기화 실패: {mt5.last_error()}")
        return False

    if not mt5.login(
        broker_cfg["login"],
        broker_cfg["password"],
        broker_cfg["server"],
    ):
        logger.warning(f"MT5 로그인 실패: {mt5.last_error()}")
        mt5.shutdown()
        return False

    return True


def _candidate_trading_days_kst(lookback_days: int = 14) -> list:
    """
    최근 날짜 중 KST 기준 평일 후보 목록 반환.

    한국 공휴일은 별도 캘린더를 사용하지 않고,
    실제 MT5 KS200 데이터 존재 여부로 판단한다.
    """
    today_kst = datetime.now(KST).date()
    candidates = []

    for days_back in range(1, lookback_days + 1):
        candidate = today_kst - timedelta(days=days_back)

        if candidate.weekday() < 5:
            candidates.append(candidate)

    return candidates


def fetch_ks200_m15_open_near_utc(
    target_utc: datetime,
    tolerance_minutes: int = 30,
) -> tuple[Optional[float], Optional[datetime]]:
    """
    MT5에서 target_utc 근처의 KS200 15분봉 시가를 조회한다.

    중요:
    - 정확히 target_utc와 일치하는 봉이 있으면 그 봉을 사용한다.
    - 정확히 일치하는 봉이 없으면 MT5가 실제 반환한 봉 중 target_utc에 가장 가까운 봉을 사용한다.
    - 최종 Binance 조회는 여기서 반환된 MT5 실제 봉 시간으로 한다.

    반환:
        price, mt5_actual_candle_time_utc
    """
    target_utc = _to_utc(target_utc)

    if not _connect_mt5():
        return None, None

    try:
        date_from = target_utc - timedelta(minutes=tolerance_minutes)
        date_to = target_utc + timedelta(minutes=tolerance_minutes)

        rates = mt5.copy_rates_range(
            _KS200_SYMBOL,
            mt5.TIMEFRAME_M15,
            date_from,
            date_to,
        )

        if rates is None or len(rates) == 0:
            logger.warning(
                "KS200 MT5 데이터 없음 | "
                f"target UTC={target_utc} | "
                f"range={date_from} ~ {date_to}"
            )
            return None, None

        df = pd.DataFrame(rates)
        df["time_utc"] = pd.to_datetime(df["time"], unit="s", utc=True)

        target_ts = int(target_utc.timestamp())

        df["diff_sec"] = (df["time"].astype(int) - target_ts).abs()
        df = df.sort_values(["diff_sec", "time"])

        row = df.iloc[0]

        price = float(row["open"])
        mt5_time_utc = row["time_utc"].to_pydatetime()

        exact_match = int(mt5_time_utc.timestamp()) == target_ts

        available_times = [
            x.strftime("%Y-%m-%d %H:%M:%S UTC")
            for x in df["time_utc"].dt.to_pydatetime()
        ]

        if exact_match:
            logger.info(
                "KS200 정확 시각 조회 성공 | "
                f"open={price} | "
                f"UTC={mt5_time_utc} | "
                f"KST={mt5_time_utc.astimezone(KST)} | "
                f"Broker={mt5_time_utc.astimezone(BROKER_TZ)}"
            )
        else:
            logger.warning(
                "KS200 요청 시각과 정확히 일치하는 봉 없음. "
                "MT5가 반환한 가장 가까운 실제 봉을 사용합니다 | "
                f"requested UTC={target_utc} | "
                f"used UTC={mt5_time_utc} | "
                f"used KST={mt5_time_utc.astimezone(KST)} | "
                f"used Broker={mt5_time_utc.astimezone(BROKER_TZ)} | "
                f"available={available_times}"
            )

        return price, mt5_time_utc

    except Exception as e:
        logger.warning(f"KS200 MT5 근접 시각 조회 실패: {e}")
        return None, None

    finally:
        mt5.shutdown()


def fetch_ewyusdt_m15_open_at_utc(
    target_utc: datetime,
) -> tuple[Optional[float], Optional[datetime]]:
    """
    Binance에서 target_utc와 정확히 같은 시작 시간의 EWYUSDT 15분봉 시가를 조회한다.

    반환:
        price, binance_candle_time_utc
    """
    target_utc = _to_utc(target_utc)

    start_ms = int(target_utc.timestamp() * 1000)
    end_ms = start_ms + 15 * 60 * 1000

    try:
        params = {
            "symbol": _BINANCE_SYMBOL,
            "interval": "15m",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1,
        }

        resp = requests.get(
            _BINANCE_KLINES_URL,
            headers=_HEADERS,
            params=params,
            timeout=10,
        )
        resp.raise_for_status()

        data = resp.json()

        if not data:
            logger.warning(f"EWYUSDT Binance 데이터 없음 | target UTC={target_utc}")
            return None, None

        returned_open_ms = int(data[0][0])

        if returned_open_ms != start_ms:
            returned_utc = datetime.fromtimestamp(returned_open_ms / 1000, tz=UTC)

            logger.warning(
                "EWYUSDT Binance 시간이 target UTC와 불일치 | "
                f"target UTC={target_utc} | returned UTC={returned_utc}"
            )
            return None, None

        price = float(data[0][1])
        binance_time_utc = datetime.fromtimestamp(returned_open_ms / 1000, tz=UTC)

        logger.info(
            "EWYUSDT 정확 시각 조회 성공 | "
            f"open={price} | "
            f"UTC={binance_time_utc} | "
            f"KST={binance_time_utc.astimezone(KST)}"
        )

        return price, binance_time_utc

    except Exception as e:
        logger.warning(f"EWYUSDT Binance 정확 시각 조회 실패: {e}")
        return None, None


def fetch_synced_prices_at_kst(
    hour: int = 9,
    minute: int = 0,
    lookback_days: int = 14,
    mt5_tolerance_minutes: int = 30,
) -> Optional[SyncedMarketData]:
    """
    최근 실제 거래 가능했던 날짜의 KST 기준 특정 시각 근처에서
    KS200 / EWYUSDT 15분봉 시가를 동기화 조회한다.

    핵심:
    - KST hour:minute은 '요청 기준 시각'이다.
    - MT5가 정확히 그 시각 봉을 주면 그대로 사용한다.
    - MT5가 그 시각 봉을 안 주면, 근처에서 실제 반환한 KS200 봉 시간을 사용한다.
    - Binance는 반드시 MT5가 실제 반환한 UTC 시간으로 조회한다.

    보장:
        MT5 KS200 actual candle UTC == Binance EWYUSDT candle UTC
    """

    candidates = _candidate_trading_days_kst(lookback_days=lookback_days)

    if not candidates:
        logger.warning("조회 가능한 KST 평일 후보가 없습니다.")
        return None

    for trading_day in candidates:
        requested_kst = datetime.combine(
            trading_day,
            time(hour=hour, minute=minute),
            tzinfo=KST,
        )

        requested_utc = requested_kst.astimezone(UTC)
        requested_broker = requested_kst.astimezone(BROKER_TZ)

        logger.info(
            "동기화 조회 요청 기준 생성 | "
            f"Requested KST={requested_kst} | "
            f"Requested UTC={requested_utc} | "
            f"Requested Broker={requested_broker}"
        )

        kospi_price, mt5_time_utc = fetch_ks200_m15_open_near_utc(
            requested_utc,
            tolerance_minutes=mt5_tolerance_minutes,
        )

        if kospi_price is None or mt5_time_utc is None:
            logger.warning(
                "해당 날짜 KS200 조회 실패. 이전 거래일 후보로 재시도 | "
                f"requested KST={requested_kst} | requested UTC={requested_utc}"
            )
            continue

        # 여기서부터가 핵심:
        # Binance는 요청 시간(requested_utc)이 아니라
        # MT5가 실제 반환한 시간(mt5_time_utc)으로 조회한다.
        actual_common_utc = mt5_time_utc.astimezone(UTC)
        actual_common_kst = actual_common_utc.astimezone(KST)
        actual_common_broker = actual_common_utc.astimezone(BROKER_TZ)

        ewy_price, binance_time_utc = fetch_ewyusdt_m15_open_at_utc(
            actual_common_utc
        )

        if ewy_price is None or binance_time_utc is None:
            logger.warning(
                "해당 날짜 EWYUSDT 조회 실패. 이전 거래일 후보로 재시도 | "
                f"MT5 actual UTC={actual_common_utc} | "
                f"MT5 actual KST={actual_common_kst}"
            )
            continue

        if int(mt5_time_utc.timestamp()) != int(binance_time_utc.timestamp()):
            logger.warning(
                "동기화 실패: MT5와 Binance UTC가 다름 | "
                f"MT5 UTC={mt5_time_utc} | "
                f"Binance UTC={binance_time_utc}"
            )
            continue

        result = SyncedMarketData(
            kospi_price=kospi_price,
            ewy_price=ewy_price,
            common_time_utc=actual_common_utc,
            common_time_kst=actual_common_kst,
            common_time_broker=actual_common_broker,
            mt5_time_utc=mt5_time_utc,
            binance_time_utc=binance_time_utc,
            requested_time_utc=requested_utc,
            requested_time_kst=requested_kst,
            requested_time_broker=requested_broker,
        )

        logger.info(
            "동기화 조회 최종 성공 | "
            f"Requested KST={result.requested_time_kst} | "
            f"Used KST={result.common_time_kst} | "
            f"Used UTC={result.common_time_utc} | "
            f"Used Broker={result.common_time_broker} | "
            f"KS200={result.kospi_price} | "
            f"EWYUSDT={result.ewy_price} | "
            f"is_synced={result.is_synced} | "
            f"used_requested_exactly={result.used_requested_exactly}"
        )

        return result

    logger.warning(
        f"최근 {lookback_days}일 내 KST {hour:02d}:{minute:02d} 근처 기준 "
        "동기화 가능한 KS200/EWYUSDT 데이터를 찾지 못했습니다."
    )
    return None


def fetch_ewyusdt_current_binance() -> Optional[float]:
    """Binance USDS-M 선물 API에서 EWYUSDT 현재가 조회."""
    try:
        params = {"symbol": _BINANCE_SYMBOL}

        resp = requests.get(
            _BINANCE_FUTURES_URL,
            headers=_HEADERS,
            params=params,
            timeout=10,
        )
        resp.raise_for_status()

        data = resp.json()
        price = float(data.get("price", 0))

        if price > 0:
            logger.info(f"EWYUSDT 현재가: {price}")
            return price

        logger.warning("EWYUSDT 응답에서 유효한 price 값 없음")

    except Exception as e:
        logger.warning(f"EWYUSDT 현재가 조회 실패: {e}")

    return None
