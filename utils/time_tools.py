"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — TIME ENGINE                           ║
║         Consciência temporal — sessões, calendário, timing                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple


class TimeEngine:
    """
    Motor temporal da ASI — sabe QUANDO o mercado é favorável.
    O timing é metade da batalha: mesmo um sinal perfeito fracassa
    se executado na sessão errada ou às vésperas de um FOMC.
    """

    # ═══════════════════════════════════════════════════════════
    #  SESSÕES DE MERCADO (UTC)
    # ═══════════════════════════════════════════════════════════
    SESSIONS = {
        "ASIA":           {"start": (0, 0),   "end": (8, 0)},
        "EUROPE":         {"start": (7, 0),   "end": (16, 0)},
        "US":             {"start": (13, 0),  "end": (22, 0)},
        "OVERLAP_EU_US":  {"start": (13, 0),  "end": (16, 0)},
        "LONDON_OPEN":    {"start": (7, 0),   "end": (8, 0)},
        "NY_OPEN":        {"start": (13, 0),  "end": (14, 0)},
        "LONDON_CLOSE":   {"start": (15, 0),  "end": (16, 0)},
    }

    # Períodos de alta/baixa liquidez para BTC
    HIGH_LIQUIDITY_WINDOWS = [
        "OVERLAP_EU_US",  # Maior liquidez global
        "NY_OPEN",        # Abertura de NY — momentum forte
        "LONDON_OPEN",    # Abertura de Londres
    ]

    LOW_LIQUIDITY_WINDOWS = [
        ("WEEKEND", None),  # Fim de semana — liquidez muito baixa
        ("LATE_ASIA", {"start": (4, 0), "end": (7, 0)}),  # Madrugada asiática
    ]

    @staticmethod
    def now_utc() -> datetime:
        """Hora atual em UTC."""
        return datetime.now(timezone.utc)

    @staticmethod
    def now_broker(broker_offset_hours: int = 2) -> datetime:
        """Hora atual no timezone do broker (padrão: UTC+2 para muitos brokers MT5)."""
        return datetime.now(timezone(timedelta(hours=broker_offset_hours)))

    @classmethod
    def current_session(cls) -> list:
        """
        Retorna lista de sessões ativas no momento.
        BTC opera 24/7, mas liquidez varia drasticamente.
        """
        now = cls.now_utc()
        hour = now.hour
        minute = now.minute
        current_time = (hour, minute)

        active = []
        for name, times in cls.SESSIONS.items():
            start = times["start"]
            end = times["end"]

            if start <= current_time < end:
                active.append(name)

        return active if active else ["OFF_HOURS"]

    @classmethod
    def is_high_liquidity(cls) -> bool:
        """Estamos em janela de alta liquidez?"""
        current = cls.current_session()
        return any(s in cls.HIGH_LIQUIDITY_WINDOWS for s in current)

    @classmethod
    def is_weekend(cls) -> bool:
        """É fim de semana? (BTC opera mas liquidez é muito menor)."""
        return cls.now_utc().weekday() >= 5

    @classmethod
    def session_info(cls) -> dict:
        """Informação completa da sessão atual."""
        now = cls.now_utc()
        sessions = cls.current_session()

        return {
            "utc_time": now.isoformat(),
            "hour_utc": now.hour,
            "day_of_week": now.strftime("%A"),
            "active_sessions": sessions,
            "is_high_liquidity": cls.is_high_liquidity(),
            "is_weekend": cls.is_weekend(),
            "trading_favorability": cls._calculate_favorability(sessions, now),
        }

    @classmethod
    def _calculate_favorability(cls, sessions: list, now: datetime) -> float:
        """
        Score de favorabilidade de trading [0.0 - 1.0].
        1.0 = condições ideais
        0.0 = pior momento possível
        """
        score = 0.5  # Base

        # Overlap EU/US é o melhor momento
        if "OVERLAP_EU_US" in sessions:
            score += 0.3
        elif "US" in sessions:
            score += 0.2
        elif "EUROPE" in sessions:
            score += 0.15
        elif "ASIA" in sessions:
            score += 0.05

        # Aberturas de sessão = volatilidade útil
        if "NY_OPEN" in sessions or "LONDON_OPEN" in sessions:
            score += 0.1

        # Weekend = penalidade menor para permitir Sniper de movimentos reais
        if cls.is_weekend():
            score -= 0.15  # Reduzido de 0.3 para 0.15

        # Madrugada = penalidade
        hour = now.hour
        if 2 <= hour <= 6:
            score -= 0.15

        return max(0.0, min(1.0, score))

    # ═══════════════════════════════════════════════════════════
    #  CALENDÁRIO DE EVENTOS MACRO
    # ═══════════════════════════════════════════════════════════
    # Eventos de alto impacto recorrentes (serão complementados pelo macro_scraper)
    HIGH_IMPACT_EVENTS = [
        "FOMC",           # Federal Open Market Committee
        "CPI",            # Consumer Price Index
        "NFP",            # Non-Farm Payrolls
        "GDP",            # Gross Domestic Product
        "PCE",            # Personal Consumption Expenditures
        "UNEMPLOYMENT",   # Unemployment Claims
        "RETAIL_SALES",   # Retail Sales
        "PPI",            # Producer Price Index
    ]

    @classmethod
    def minutes_to_next_candle(cls, timeframe_minutes: int) -> int:
        """Minutos até o próximo candle fechar no timeframe dado."""
        now = cls.now_utc()
        total_minutes = now.hour * 60 + now.minute
        remainder = total_minutes % timeframe_minutes
        return timeframe_minutes - remainder

    @classmethod
    def is_candle_fresh(cls, timeframe_minutes: int,
                        max_age_seconds: int = 5) -> bool:
        """
        O candle acabou de fechar? (Útil para timing de decisão)
        Retorna True se estamos nos primeiros `max_age_seconds` do novo candle.
        """
        now = cls.now_utc()
        total_seconds = now.hour * 3600 + now.minute * 60 + now.second
        tf_seconds = timeframe_minutes * 60
        elapsed = total_seconds % tf_seconds
        return elapsed < max_age_seconds

    # ═══════════════════════════════════════════════════════════
    #  TIMING DE PERFORMANCE
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def elapsed_ms(start_time: datetime) -> float:
        """Milissegundos desde start_time."""
        delta = datetime.now(timezone.utc) - start_time
        return delta.total_seconds() * 1000

    @staticmethod
    def timestamp_ms() -> int:
        """Timestamp atual em milissegundos."""
        return int(datetime.now(timezone.utc).timestamp() * 1000)
