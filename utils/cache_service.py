"""
💾 Soccer Scout AI - Serviço de Cache
Cache inteligente com TTL, invalidação e telemetria
"""

import json
import time
import hashlib
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import threading

class InMemoryCache:
    """Cache em memória com TTL e telemetria"""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        
        # Telemetria
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.evictions = 0
    
    def _is_expired(self, entry: Dict) -> bool:
        """Verificar se entrada está expirada"""
        return time.time() > entry.get('expires_at', 0)
    
    def _cleanup_expired(self) -> None:
        """Limpar entradas expiradas"""
        expired_keys = []
        for key, entry in self._cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self.evictions += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache"""
        with self._lock:
            self._cleanup_expired()
            
            entry = self._cache.get(key)
            if entry is None or self._is_expired(entry):
                self.misses += 1
                return None
            
            self.hits += 1
            return entry['value']
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Definir valor no cache"""
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = time.time() + ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            self.sets += 1
    
    def delete(self, key: str) -> bool:
        """Deletar entrada do cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Limpar todo o cache"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / max(total_requests, 1)
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'sets': self.sets,
                'evictions': self.evictions,
                'hit_rate': hit_rate,
                'total_entries': len(self._cache),
                'total_requests': total_requests
            }

class SmartCache:
    """Cache inteligente para dados de futebol"""
    
    def __init__(self):
        # Diferentes TTLs para diferentes tipos de dados
        self.player_cache = InMemoryCache(default_ttl_seconds=1800)  # 30 min
        self.stats_cache = InMemoryCache(default_ttl_seconds=3600)   # 1 hora
        self.market_cache = InMemoryCache(default_ttl_seconds=7200)  # 2 horas
        self.league_cache = InMemoryCache(default_ttl_seconds=86400) # 24 horas
        self.search_cache = InMemoryCache(default_ttl_seconds=900)   # 15 min
    
    def _make_key(self, prefix: str, *args) -> str:
        """Criar chave de cache determinística"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    # Player cache methods
    def get_player(self, player_id: int) -> Optional[Dict]:
        return self.player_cache.get(self._make_key("player", player_id))
    
    def set_player(self, player_id: int, data: Dict) -> None:
        self.player_cache.set(self._make_key("player", player_id), data)
    
    # Stats cache methods
    def get_player_stats(self, player_id: int, season: str) -> Optional[Dict]:
        return self.stats_cache.get(self._make_key("stats", player_id, season))
    
    def set_player_stats(self, player_id: int, season: str, data: Dict) -> None:
        self.stats_cache.set(self._make_key("stats", player_id, season), data)
    
    # Market cache methods
    def get_market_data(self, position: str, league: str) -> Optional[List]:
        return self.market_cache.get(self._make_key("market", position, league))
    
    def set_market_data(self, position: str, league: str, data: List) -> None:
        self.market_cache.set(self._make_key("market", position, league), data)
    
    # League cache methods
    def get_leagues(self) -> Optional[List]:
        return self.league_cache.get("leagues_all")
    
    def set_leagues(self, data: List) -> None:
        self.league_cache.set("leagues_all", data)
    
    # Search cache methods
    def get_search_results(self, query_hash: str) -> Optional[Dict]:
        return self.search_cache.get(self._make_key("search", query_hash))
    
    def set_search_results(self, query_hash: str, data: Dict) -> None:
        self.search_cache.set(self._make_key("search", query_hash), data)
    
    def invalidate_player(self, player_id: int) -> None:
        """Invalidar cache de um jogador específico"""
        self.player_cache.delete(self._make_key("player", player_id))
        # Também invalidar stats relacionadas
        # (Em implementação real, seria mais sofisticado)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Obter estatísticas de todos os caches"""
        return {
            'player_cache': self.player_cache.get_stats(),
            'stats_cache': self.stats_cache.get_stats(),
            'market_cache': self.market_cache.get_stats(),
            'league_cache': self.league_cache.get_stats(),
            'search_cache': self.search_cache.get_stats()
        }

# Instância global do cache
cache_service = SmartCache()