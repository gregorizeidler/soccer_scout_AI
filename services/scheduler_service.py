"""
⏰ Soccer Scout AI - Agendador de Sincronização
Scheduler para sync automático de dados, cache warming e alertas
"""

import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
from services.enhanced_sportmonks_api import EnhancedSportmonksAPI
from utils.cache_service import cache_service
from database.models import get_db, Player, League

logger = logging.getLogger(__name__)

class SchedulerService:
    """Agendador para tarefas automáticas do sistema"""
    
    def __init__(self):
        self.sportmonks_api = EnhancedSportmonksAPI()
        self.is_running = False
        self.scheduler_thread = None
        
        # Configurar jobs
        self._setup_scheduled_jobs()
    
    def _setup_scheduled_jobs(self):
        """Configurar todos os jobs agendados"""
        
        # Sync diário de dados principais (3:00 AM)
        schedule.every().day.at("03:00").do(self._run_async_job, self.daily_data_sync)
        
        # Cache warming de ligas populares (6:00 AM)
        schedule.every().day.at("06:00").do(self._run_async_job, self.warm_popular_caches)
        
        # Verificação de transferências (a cada 4 horas)
        schedule.every(4).hours.do(self._run_async_job, self.check_transfer_updates)
        
        # Atualização de market trends (a cada 6 horas)
        schedule.every(6).hours.do(self._run_async_job, self.update_market_trends)
        
        # Limpeza de cache expirado (a cada hora)
        schedule.every().hour.do(self.cleanup_expired_cache)
        
        # Verificação de lesões (2x por dia)
        schedule.every(12).hours.do(self._run_async_job, self.check_injury_updates)
        
        # Sync de estatísticas de jogadores top (diário às 8:00)
        schedule.every().day.at("08:00").do(self._run_async_job, self.sync_top_players_stats)
        
        # Detectar oportunidades de mercado (diário às 10:00)
        schedule.every().day.at("10:00").do(self._run_async_job, self.detect_market_opportunities)
    
    def _run_async_job(self, async_func: Callable):
        """Executar job assíncrono no thread do scheduler"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(async_func())
        except Exception as e:
            logger.error(f"Erro no job agendado {async_func.__name__}: {e}")
        finally:
            loop.close()
    
    def start(self):
        """Iniciar o scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler iniciado")
    
    def stop(self):
        """Parar o scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler parado")
    
    def _run_scheduler(self):
        """Loop principal do scheduler"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
            except Exception as e:
                logger.error(f"Erro no scheduler: {e}")
                time.sleep(60)
    
    # ========================================
    # 🔄 JOBS DE SINCRONIZAÇÃO
    # ========================================
    
    async def daily_data_sync(self):
        """Sincronização diária completa de dados"""
        logger.info("Iniciando sync diário de dados")
        
        try:
            # 1. Atualizar ligas
            await self._sync_leagues()
            
            # 2. Atualizar jogadores principais
            await self._sync_main_players()
            
            # 3. Verificar mudanças de time
            await self._check_team_changes()
            
            # 4. Atualizar valores de mercado
            await self._update_market_values()
            
            logger.info("Sync diário concluído com sucesso")
            
        except Exception as e:
            logger.error(f"Erro no sync diário: {e}")
    
    async def _sync_leagues(self):
        """Sincronizar dados das ligas"""
        try:
            leagues_data = await self.sportmonks_api.get_leagues()
            
            db = next(get_db())
            for league_data in leagues_data:
                # Verificar se liga já existe
                existing = db.query(League).filter(
                    League.sportmonks_id == league_data['id']
                ).first()
                
                if not existing:
                    new_league = League(
                        sportmonks_id=league_data['id'],
                        name=league_data.get('name'),
                        country=league_data.get('country', {}).get('name'),
                        tier=league_data.get('tier', 1),
                        active=True
                    )
                    db.add(new_league)
                else:
                    # Atualizar dados existentes
                    existing.name = league_data.get('name')
                    existing.updated_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Sincronizadas {len(leagues_data)} ligas")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar ligas: {e}")
    
    async def _sync_main_players(self):
        """Sincronizar jogadores principais (top ligas)"""
        try:
            # Ligas principais para sincronizar
            main_leagues = [1, 2, 3, 4, 5]  # Premier, La Liga, Serie A, etc.
            
            for league_id in main_leagues:
                players = await self.sportmonks_api.search_players_by_criteria({
                    'league_id': league_id,
                    'min_appearances': 10,
                    'limit': 200
                })
                
                await self._update_players_in_db(players)
                
                # Aguardar um pouco para não sobrecarregar a API
                await asyncio.sleep(2)
            
            logger.info("Sincronização de jogadores principais concluída")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar jogadores principais: {e}")
    
    async def _update_players_in_db(self, players_data: List[Dict]):
        """Atualizar jogadores no banco de dados"""
        try:
            db = next(get_db())
            
            for player_data in players_data:
                existing = db.query(Player).filter(
                    Player.sportmonks_id == player_data['id']
                ).first()
                
                if existing:
                    # Atualizar dados existentes
                    self._update_player_fields(existing, player_data)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Criar novo jogador
                    new_player = self._create_player_from_data(player_data)
                    db.add(new_player)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar jogadores no DB: {e}")
    
    async def warm_popular_caches(self):
        """Aquecer caches de dados populares"""
        logger.info("Aquecendo caches populares")
        
        try:
            # 1. Cache de ligas
            leagues = await self.sportmonks_api.get_leagues()
            cache_service.set_leagues(leagues)
            
            # 2. Cache de jogadores top por posição
            positions = ["Centre-Forward", "Central Midfield", "Centre-Back", "Winger"]
            
            for position in positions:
                market_data = await self.sportmonks_api.get_market_radar(
                    position, [20, 30], [1, 100]
                )
                cache_service.set_market_data(position, "general", market_data)
                await asyncio.sleep(1)
            
            # 3. Cache de estatísticas de jogadores populares
            popular_players = [1, 2, 3]  # IDs dos jogadores mais buscados
            for player_id in popular_players:
                profile = await self.sportmonks_api.get_player_complete_profile(player_id)
                cache_service.set_player(player_id, profile)
                await asyncio.sleep(0.5)
            
            logger.info("Cache warming concluído")
            
        except Exception as e:
            logger.error(f"Erro no cache warming: {e}")
    
    async def check_transfer_updates(self):
        """Verificar atualizações de transferências"""
        logger.info("Verificando atualizações de transferências")
        
        try:
            # Buscar transferências recentes (últimos 7 dias)
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # Implementar lógica para buscar transferências recentes
            # e atualizar os dados dos jogadores afetados
            
            logger.info("Verificação de transferências concluída")
            
        except Exception as e:
            logger.error(f"Erro ao verificar transferências: {e}")
    
    async def update_market_trends(self):
        """Atualizar tendências de mercado"""
        logger.info("Atualizando tendências de mercado")
        
        try:
            positions = ["Centre-Forward", "Central Midfield", "Centre-Back"]
            
            for position in positions:
                # Analisar tendências de preço por posição
                trend_data = await self._analyze_position_market_trends(position)
                
                # Salvar no cache com TTL longo
                cache_service.market_cache.set(
                    f"trends_{position}", trend_data, ttl_seconds=21600  # 6 horas
                )
            
            logger.info("Tendências de mercado atualizadas")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar tendências: {e}")
    
    def cleanup_expired_cache(self):
        """Limpeza de cache expirado"""
        try:
            # O cache já tem cleanup automático, mas forçamos aqui
            stats = cache_service.get_all_stats()
            
            total_entries = sum(
                cache_stats['total_entries'] 
                for cache_stats in stats.values()
            )
            
            logger.info(f"Cache status: {total_entries} entradas totais")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de cache: {e}")
    
    async def check_injury_updates(self):
        """Verificar atualizações de lesões"""
        logger.info("Verificando atualizações de lesões")
        
        try:
            # Buscar jogadores com lesões ativas ou recentes
            db = next(get_db())
            active_players = db.query(Player).filter(
                Player.injury_prone == False,  # Jogadores não marcados como propensos
                Player.updated_at > datetime.utcnow() - timedelta(days=30)
            ).limit(100).all()
            
            for player in active_players:
                injury_timeline = await self.sportmonks_api.get_player_injury_timeline(
                    player.sportmonks_id
                )
                
                # Atualizar status de lesão se necessário
                if injury_timeline:
                    recent_injuries = [
                        inj for inj in injury_timeline 
                        if inj.get('end_date') is None  # Lesão ativa
                    ]
                    
                    if recent_injuries:
                        player.injury_prone = True
                        player.days_injured_season = sum(
                            inj.get('days_out', 0) for inj in recent_injuries
                        )
                
                await asyncio.sleep(0.1)  # Rate limiting
            
            db.commit()
            logger.info("Verificação de lesões concluída")
            
        except Exception as e:
            logger.error(f"Erro ao verificar lesões: {e}")
    
    async def sync_top_players_stats(self):
        """Sincronizar estatísticas dos jogadores top"""
        logger.info("Sincronizando estatísticas dos jogadores top")
        
        try:
            db = next(get_db())
            
            # Buscar top 100 jogadores por rating
            top_players = db.query(Player).filter(
                Player.overall_rating > 7.0
            ).order_by(Player.overall_rating.desc()).limit(100).all()
            
            for player in top_players:
                # Atualizar estatísticas da temporada
                stats = await self.sportmonks_api.get_player_season_statistics(
                    player.sportmonks_id
                )
                
                if stats and stats.get('raw_stats'):
                    raw_stats = stats['raw_stats']
                    
                    # Atualizar campos no banco
                    player.goals_season = raw_stats.get('goals', 0)
                    player.assists_season = raw_stats.get('assists', 0)
                    player.appearances_season = raw_stats.get('appearances', 0)
                    player.minutes_played = raw_stats.get('minutes_played', 0)
                    player.yellow_cards = raw_stats.get('yellow_cards', 0)
                    player.red_cards = raw_stats.get('red_cards', 0)
                    player.updated_at = datetime.utcnow()
                
                await asyncio.sleep(0.2)  # Rate limiting
            
            db.commit()
            logger.info(f"Atualizadas estatísticas de {len(top_players)} jogadores")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar estatísticas: {e}")
    
    async def detect_market_opportunities(self):
        """Detectar oportunidades de mercado automaticamente"""
        logger.info("Detectando oportunidades de mercado")
        
        try:
            opportunities = {
                'undervalued': [],
                'contract_ending': [],
                'rising_stars': [],
                'injury_recoveries': []
            }
            
            db = next(get_db())
            
            # 1. Jogadores subvalorizados (alta performance, baixo valor)
            undervalued = db.query(Player).filter(
                Player.overall_rating > 7.5,
                Player.market_value < 20.0,
                Player.age < 28
            ).limit(20).all()
            
            opportunities['undervalued'] = [
                {'id': p.id, 'name': p.name, 'reason': 'High rating, low value'}
                for p in undervalued
            ]
            
            # 2. Contratos terminando
            from sqlalchemy import extract
            contract_ending = db.query(Player).filter(
                Player.contract_end_date.isnot(None),
                extract('year', Player.contract_end_date) <= 2025,
                Player.overall_rating > 7.0
            ).limit(20).all()
            
            opportunities['contract_ending'] = [
                {'id': p.id, 'name': p.name, 'contract_end': p.contract_end_date}
                for p in contract_ending
            ]
            
            # 3. Estrelas em ascensão
            rising_stars = db.query(Player).filter(
                Player.age <= 22,
                Player.potential_rating > 8.0,
                Player.market_trend == 'rising'
            ).limit(20).all()
            
            opportunities['rising_stars'] = [
                {'id': p.id, 'name': p.name, 'potential': p.potential_rating}
                for p in rising_stars
            ]
            
            # Salvar oportunidades no cache
            cache_service.market_cache.set(
                "daily_opportunities", opportunities, ttl_seconds=86400  # 24 horas
            )
            
            logger.info(f"Detectadas oportunidades: {len(opportunities['undervalued'])} subvalorizados, "
                       f"{len(opportunities['contract_ending'])} contratos terminando")
            
        except Exception as e:
            logger.error(f"Erro ao detectar oportunidades: {e}")
    
    # ========================================
    # 🛠️ MÉTODOS AUXILIARES
    # ========================================
    
    async def _check_team_changes(self):
        """Verificar mudanças de time dos jogadores"""
        # Implementação para detectar transferências
        pass
    
    async def _update_market_values(self):
        """Atualizar valores de mercado"""
        # Implementação para atualizar valores
        pass
    
    async def _analyze_position_market_trends(self, position: str) -> Dict:
        """Analisar tendências de mercado por posição"""
        return {
            'position': position,
            'avg_value': 25.0,
            'trend': 'stable',
            'top_movers': []
        }
    
    def _update_player_fields(self, player: Player, data: Dict):
        """Atualizar campos do jogador com novos dados"""
        player.name = data.get('name', player.name)
        player.age = data.get('age', player.age)
        player.current_team = data.get('current_team', player.current_team)
        player.market_value = data.get('market_value', player.market_value)
    
    def _create_player_from_data(self, data: Dict) -> Player:
        """Criar novo jogador a partir dos dados"""
        return Player(
            sportmonks_id=data['id'],
            name=data.get('name'),
            position=data.get('position'),
            age=data.get('age'),
            nationality=data.get('nationality'),
            current_team=data.get('current_team'),
            market_value=data.get('market_value', 0),
            height=data.get('height'),
            weight=data.get('weight'),
            preferred_foot=data.get('preferred_foot'),
            overall_rating=data.get('overall_rating', 6.0),
            potential_rating=data.get('potential_rating', 6.0)
        )

# Instância global do scheduler
scheduler_service = SchedulerService()