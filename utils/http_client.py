"""
🔄 Soccer Scout AI - Cliente HTTP Resiliente
Cliente robusto com retries, exponential backoff, jitter e tratamento de rate limits
"""

import time
import random
import asyncio
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)

class ResilientHTTPClient:
    """
    Cliente HTTP resiliente com:
    - Timeouts configuráveis
    - Retries com exponential backoff + jitter
    - Tratamento específico para 429 (Rate Limit) e 5xx
    - Circuit breaker simples
    - Telemetria básica
    """

    def __init__(
        self,
        default_timeout_seconds: float = 10.0,
        max_retries: int = 5,
        backoff_base_seconds: float = 0.5,
        backoff_cap_seconds: float = 8.0,
        circuit_breaker_threshold: int = 5
    ) -> None:
        self.default_timeout_seconds = default_timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.backoff_cap_seconds = backoff_cap_seconds
        
        # Circuit breaker simples
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.consecutive_failures = 0
        self.circuit_open = False
        self.last_failure_time = 0
        self.circuit_reset_timeout = 60  # segundos
        
        # Telemetria
        self.request_count = 0
        self.error_count = 0
        self.rate_limit_count = 0
        
        # Configurar sessão com pool de conexões
        self.session = requests.Session()
        
        # Configurar retry strategy para urllib3
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=backoff_base_seconds,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _is_circuit_open(self) -> bool:
        """Verificar se circuit breaker está aberto"""
        if not self.circuit_open:
            return False
        
        # Tentar resetar depois do timeout
        if time.time() - self.last_failure_time > self.circuit_reset_timeout:
            self.circuit_open = False
            self.consecutive_failures = 0
            logger.info("Circuit breaker reset")
            return False
        
        return True

    def _record_failure(self) -> None:
        """Registrar falha e atualizar circuit breaker"""
        self.consecutive_failures += 1
        self.error_count += 1
        self.last_failure_time = time.time()
        
        if self.consecutive_failures >= self.circuit_breaker_threshold:
            self.circuit_open = True
            logger.warning(f"Circuit breaker opened after {self.consecutive_failures} failures")

    def _record_success(self) -> None:
        """Registrar sucesso e resetar contador"""
        self.consecutive_failures = 0
        if self.circuit_open:
            self.circuit_open = False
            logger.info("Circuit breaker closed after successful request")

    def _sleep_with_backoff(self, attempt_index: int, retry_after_header: Optional[str] = None) -> None:
        """Sleep com exponential backoff + jitter"""
        if retry_after_header:
            try:
                sleep_seconds = float(retry_after_header)
                sleep_time = min(sleep_seconds, self.backoff_cap_seconds)
                logger.info(f"Rate limited, sleeping for {sleep_time}s (from Retry-After header)")
                time.sleep(sleep_time)
                return
            except (ValueError, TypeError):
                pass

        # Exponential backoff with jitter
        base_delay = min(self.backoff_base_seconds * (2 ** attempt_index), self.backoff_cap_seconds)
        jitter = random.uniform(0, self.backoff_base_seconds)
        sleep_time = base_delay + jitter
        
        logger.info(f"Retrying in {sleep_time:.2f}s (attempt {attempt_index + 1})")
        time.sleep(sleep_time)

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[float] = None,
    ) -> requests.Response:
        """GET request com retry logic"""
        
        # Check circuit breaker
        if self._is_circuit_open():
            raise Exception("Circuit breaker is open, requests blocked")
        
        timeout = timeout_seconds or self.default_timeout_seconds
        self.request_count += 1
        
        last_exc: Optional[Exception] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1})")
                response = self.session.get(
                    url, 
                    headers=headers, 
                    params=params, 
                    timeout=timeout
                )

                # Success
                if 200 <= response.status_code < 300:
                    self._record_success()
                    return response

                # Rate limiting
                if response.status_code == 429:
                    self.rate_limit_count += 1
                    if attempt < self.max_retries:
                        self._sleep_with_backoff(attempt, response.headers.get("Retry-After"))
                        continue

                # Server errors - retry
                if response.status_code in (500, 502, 503, 504):
                    if attempt < self.max_retries:
                        self._sleep_with_backoff(attempt)
                        continue

                # Client errors - don't retry
                if 400 <= response.status_code < 500:
                    self._record_failure()
                    response.raise_for_status()
                    return response

                # Other errors
                response.raise_for_status()
                return response

            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                logger.warning(f"Network error on attempt {attempt + 1}: {exc}")
                if attempt < self.max_retries:
                    self._sleep_with_backoff(attempt)
                    continue
                self._record_failure()
                raise
            
            except requests.RequestException as exc:
                last_exc = exc
                logger.error(f"Request error on attempt {attempt + 1}: {exc}")
                if attempt < self.max_retries:
                    self._sleep_with_backoff(attempt)
                    continue
                self._record_failure()
                raise

        self._record_failure()
        if last_exc:
            raise last_exc
        raise RuntimeError("HTTP request failed without exception context")

    async def get_async(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[float] = None,
    ) -> requests.Response:
        """GET request assíncrono"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.get(url, headers, params, timeout_seconds)
        )

    def get_telemetry(self) -> Dict[str, Any]:
        """Obter métricas do cliente"""
        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "rate_limits": self.rate_limit_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "consecutive_failures": self.consecutive_failures,
            "circuit_open": self.circuit_open
        }