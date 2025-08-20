"""
🚨 Soccer Scout AI - Serviço de Alertas Inteligentes
Sistema de alertas automáticos para oportunidades de mercado, mudanças de status e eventos
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from sqlalchemy.orm import Session
from database.models import get_db, Player, League
from services.enhanced_sportmonks_api import EnhancedSportmonksAPI
from utils.cache_service import cache_service

logger = logging.getLogger(__name__)

class AlertType(Enum):
    CONTRACT_ENDING = "contract_ending"
    FREE_AGENT = "free_agent" 
    PRICE_DROP = "price_drop"
    PERFORMANCE_SURGE = "performance_surge"
    INJURY_RECOVERY = "injury_recovery"
    TRANSFER_RUMOR = "transfer_rumor"
    UNDERVALUED_PLAYER = "undervalued_player"
    RISING_STAR = "rising_star"
    LOAN_OPPORTUNITY = "loan_opportunity"
    RELEASE_CLAUSE = "release_clause"

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    id: str
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    player_id: Optional[int]
    club_id: str
    data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime]
    is_read: bool = False
    is_acted_upon: bool = False

class AlertsService:
    """Serviço de alertas inteligentes para clubes"""
    
    def __init__(self):
        self.sportmonks_api = EnhancedSportmonksAPI()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_subscribers: Dict[str, List[Callable]] = {}  # club_id -> callbacks
        self.monitoring_rules: Dict[str, Dict] = {}  # club_id -> rules
    
    async def setup_club_monitoring(self, club_id: str, monitoring_config: Dict) -> None:
        """Configurar monitoramento personalizado para um clube"""
        
        self.monitoring_rules[club_id] = {
            'positions_of_interest': monitoring_config.get('positions', []),
            'max_age': monitoring_config.get('max_age', 30),
            'max_budget': monitoring_config.get('max_budget', 50),
            'min_rating': monitoring_config.get('min_rating', 7.0),
            'preferred_leagues': monitoring_config.get('leagues', []),
            'exclude_injury_prone': monitoring_config.get('exclude_injury_prone', True),
            'contract_alert_months': monitoring_config.get('contract_alert_months', 6),
            'performance_threshold': monitoring_config.get('performance_threshold', 0.8),
            'value_drop_threshold': monitoring_config.get('value_drop_threshold', 0.15)
        }
        
        logger.info(f"Configurado monitoramento para clube {club_id}")
    
    def subscribe_to_alerts(self, club_id: str, callback: Callable[[Alert], None]) -> None:
        """Inscrever callback para receber alertas de um clube"""
        if club_id not in self.alert_subscribers:
            self.alert_subscribers[club_id] = []
        
        self.alert_subscribers[club_id].append(callback)
    
    async def run_monitoring_cycle(self) -> None:
        """Executar ciclo completo de monitoramento para todos os clubes"""
        
        logger.info("Iniciando ciclo de monitoramento de alertas")
        
        for club_id, rules in self.monitoring_rules.items():
            try:
                await self._monitor_club_opportunities(club_id, rules)
            except Exception as e:
                logger.error(f"Erro no monitoramento do clube {club_id}: {e}")
        
        logger.info("Ciclo de monitoramento concluído")
    
    async def _monitor_club_opportunities(self, club_id: str, rules: Dict) -> None:
        """Monitorar oportunidades para um clube específico"""
        
        # 1. Verificar contratos terminando
        await self._check_contract_endings(club_id, rules)
        
        # 2. Detectar quedas de preço
        await self._check_price_drops(club_id, rules)
        
        # 3. Monitorar performance surges
        await self._check_performance_surges(club_id, rules)
        
        # 4. Verificar jogadores subvalorizados
        await self._check_undervalued_players(club_id, rules)
        
        # 5. Detectar estrelas em ascensão
        await self._check_rising_stars(club_id, rules)
        
        # 6. Monitorar oportunidades de empréstimo
        await self._check_loan_opportunities(club_id, rules)
        
        # 7. Alertas de cláusulas de rescisão
        await self._check_release_clauses(club_id, rules)
        
        # 8. Recuperações de lesões
        await self._check_injury_recoveries(club_id, rules)
    
    async def _check_contract_endings(self, club_id: str, rules: Dict) -> None:
        """Verificar contratos terminando em breve"""
        
        try:
            alert_months = rules.get('contract_alert_months', 6)
            cutoff_date = date.today() + timedelta(days=30 * alert_months)
            
            db = next(get_db())
            
            # Buscar jogadores com contrato terminando
            ending_contracts = db.query(Player).filter(
                Player.contract_end_date.isnot(None),
                Player.contract_end_date <= cutoff_date,
                Player.overall_rating >= rules.get('min_rating', 7.0),
                Player.age <= rules.get('max_age', 30),
                Player.market_value <= rules.get('max_budget', 50)
            )
            
            # Filtrar por posições de interesse
            if rules.get('positions_of_interest'):
                ending_contracts = ending_contracts.filter(
                    Player.position.in_(rules['positions_of_interest'])
                )
            
            players = ending_contracts.limit(20).all()
            
            for player in players:
                if player.contract_end_date:
                    months_left = (player.contract_end_date - date.today()).days // 30
                    
                    priority = AlertPriority.HIGH if months_left <= 3 else AlertPriority.MEDIUM
                    
                    alert = Alert(
                        id=f"contract_{player.id}_{club_id}",
                        type=AlertType.CONTRACT_ENDING,
                        priority=priority,
                        title=f"Contrato terminando: {player.name}",
                        message=f"{player.name} ({player.position}) - Contrato termina em {months_left} meses. "
                               f"Valor: €{player.market_value}M, Rating: {player.overall_rating}/10",
                        player_id=player.id,
                        club_id=club_id,
                        data={
                            'months_remaining': months_left,
                            'market_value': player.market_value,
                            'position': player.position,
                            'age': player.age,
                            'current_team': player.current_team
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=30)
                    )
                    
                    await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar contratos terminando: {e}")
    
    async def _check_price_drops(self, club_id: str, rules: Dict) -> None:
        """Detectar quedas significativas de preço"""
        
        try:
            drop_threshold = rules.get('value_drop_threshold', 0.15)  # 15%
            
            # Buscar jogadores com histórico de valor
            db = next(get_db())
            
            potential_drops = db.query(Player).filter(
                Player.last_transfer_value.isnot(None),
                Player.market_value.isnot(None),
                Player.overall_rating >= rules.get('min_rating', 7.0)
            ).limit(50).all()
            
            for player in potential_drops:
                if player.last_transfer_value and player.market_value:
                    price_change = (player.market_value - player.last_transfer_value) / player.last_transfer_value
                    
                    if price_change <= -drop_threshold:  # Queda significativa
                        alert = Alert(
                            id=f"price_drop_{player.id}_{club_id}",
                            type=AlertType.PRICE_DROP,
                            priority=AlertPriority.MEDIUM,
                            title=f"Queda de preço: {player.name}",
                            message=f"{player.name} teve queda de {abs(price_change)*100:.1f}% no valor. "
                                   f"De €{player.last_transfer_value}M para €{player.market_value}M",
                            player_id=player.id,
                            club_id=club_id,
                            data={
                                'price_change_percent': price_change * 100,
                                'old_value': player.last_transfer_value,
                                'new_value': player.market_value,
                                'potential_bargain': True
                            },
                            created_at=datetime.now(),
                            expires_at=datetime.now() + timedelta(days=7)
                        )
                        
                        await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar quedas de preço: {e}")
    
    async def _check_performance_surges(self, club_id: str, rules: Dict) -> None:
        """Monitorar surtos de performance"""
        
        try:
            performance_threshold = rules.get('performance_threshold', 0.8)
            
            db = next(get_db())
            
            # Buscar jogadores com alta performance recente
            high_performers = db.query(Player).filter(
                Player.goals_season >= 15,  # Muitos gols
                Player.age <= rules.get('max_age', 28),
                Player.market_value <= rules.get('max_budget', 50)
            ).limit(20).all()
            
            for player in high_performers:
                # Calcular performance score baseado em gols + assists + rating
                performance_score = (
                    (player.goals_season or 0) * 0.4 + 
                    (player.assists_season or 0) * 0.3 + 
                    (player.overall_rating or 6) * 0.3
                )
                
                if performance_score >= performance_threshold * 10:
                    alert = Alert(
                        id=f"performance_{player.id}_{club_id}",
                        type=AlertType.PERFORMANCE_SURGE,
                        priority=AlertPriority.HIGH,
                        title=f"Performance excepcional: {player.name}",
                        message=f"{player.name} está em excelente forma: {player.goals_season}G + "
                               f"{player.assists_season}A em {player.appearances_season} jogos",
                        player_id=player.id,
                        club_id=club_id,
                        data={
                            'goals': player.goals_season,
                            'assists': player.assists_season,
                            'appearances': player.appearances_season,
                            'performance_score': performance_score,
                            'form_trend': 'excellent'
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=14)
                    )
                    
                    await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar surtos de performance: {e}")
    
    async def _check_undervalued_players(self, club_id: str, rules: Dict) -> None:
        """Detectar jogadores subvalorizados"""
        
        try:
            db = next(get_db())
            
            # Buscar jogadores com alto rating mas baixo valor
            undervalued = db.query(Player).filter(
                Player.overall_rating >= 8.0,
                Player.market_value <= 15.0,  # Menos de 15M
                Player.age <= rules.get('max_age', 28)
            )
            
            if rules.get('positions_of_interest'):
                undervalued = undervalued.filter(
                    Player.position.in_(rules['positions_of_interest'])
                )
            
            players = undervalued.limit(10).all()
            
            for player in players:
                # Calcular ratio valor/qualidade
                value_quality_ratio = player.market_value / max(player.overall_rating, 1)
                
                if value_quality_ratio < 2.0:  # Menos de 2M por ponto de rating
                    alert = Alert(
                        id=f"undervalued_{player.id}_{club_id}",
                        type=AlertType.UNDERVALUED_PLAYER,
                        priority=AlertPriority.HIGH,
                        title=f"Oportunidade: {player.name}",
                        message=f"{player.name} - Rating {player.overall_rating}/10 por apenas €{player.market_value}M. "
                               f"Excelente custo-benefício!",
                        player_id=player.id,
                        club_id=club_id,
                        data={
                            'value_quality_ratio': value_quality_ratio,
                            'market_value': player.market_value,
                            'overall_rating': player.overall_rating,
                            'opportunity_type': 'undervalued'
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=21)
                    )
                    
                    await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar jogadores subvalorizados: {e}")
    
    async def _check_rising_stars(self, club_id: str, rules: Dict) -> None:
        """Detectar estrelas em ascensão"""
        
        try:
            db = next(get_db())
            
            # Buscar jogadores jovens com alto potencial
            rising_stars = db.query(Player).filter(
                Player.age <= 22,
                Player.potential_rating >= 8.5,
                Player.market_trend == 'rising',
                Player.market_value <= rules.get('max_budget', 50)
            ).limit(15).all()
            
            for player in rising_stars:
                potential_growth = player.potential_rating - player.overall_rating
                
                if potential_growth >= 1.5:  # Grande margem de crescimento
                    alert = Alert(
                        id=f"rising_star_{player.id}_{club_id}",
                        type=AlertType.RISING_STAR,
                        priority=AlertPriority.MEDIUM,
                        title=f"Estrela em ascensão: {player.name}",
                        message=f"{player.name} ({player.age} anos) - Potencial {player.potential_rating}/10, "
                               f"atual {player.overall_rating}/10. Margem de crescimento: +{potential_growth:.1f}",
                        player_id=player.id,
                        club_id=club_id,
                        data={
                            'potential_rating': player.potential_rating,
                            'current_rating': player.overall_rating,
                            'growth_potential': potential_growth,
                            'market_trend': player.market_trend,
                            'investment_type': 'future_star'
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=30)
                    )
                    
                    await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar estrelas em ascensão: {e}")
    
    async def _check_loan_opportunities(self, club_id: str, rules: Dict) -> None:
        """Verificar oportunidades de empréstimo"""
        
        try:
            db = next(get_db())
            
            # Buscar jogadores disponíveis para empréstimo
            loan_candidates = db.query(Player).filter(
                Player.loan_player == True,
                Player.age <= rules.get('max_age', 25),
                Player.overall_rating >= rules.get('min_rating', 7.0)
            ).limit(10).all()
            
            for player in loan_candidates:
                alert = Alert(
                    id=f"loan_{player.id}_{club_id}",
                    type=AlertType.LOAN_OPPORTUNITY,
                    priority=AlertPriority.MEDIUM,
                    title=f"Empréstimo disponível: {player.name}",
                    message=f"{player.name} ({player.position}) disponível para empréstimo. "
                           f"Rating: {player.overall_rating}/10, Idade: {player.age}",
                    player_id=player.id,
                    club_id=club_id,
                    data={
                        'loan_type': 'available',
                        'parent_club': player.current_team,
                        'position': player.position,
                        'rating': player.overall_rating
                    },
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=14)
                )
                
                await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar oportunidades de empréstimo: {e}")
    
    async def _check_release_clauses(self, club_id: str, rules: Dict) -> None:
        """Alertas sobre cláusulas de rescisão acessíveis"""
        
        try:
            max_budget = rules.get('max_budget', 50)
            
            db = next(get_db())
            
            # Buscar jogadores com cláusula dentro do orçamento
            affordable_clauses = db.query(Player).filter(
                Player.release_clause.isnot(None),
                Player.release_clause <= max_budget,
                Player.overall_rating >= rules.get('min_rating', 7.5)
            ).limit(10).all()
            
            for player in affordable_clauses:
                if player.release_clause < player.market_value * 0.9:  # Cláusula abaixo do valor de mercado
                    alert = Alert(
                        id=f"release_clause_{player.id}_{club_id}",
                        type=AlertType.RELEASE_CLAUSE,
                        priority=AlertPriority.HIGH,
                        title=f"Cláusula acessível: {player.name}",
                        message=f"{player.name} tem cláusula de €{player.release_clause}M "
                               f"(valor de mercado: €{player.market_value}M)",
                        player_id=player.id,
                        club_id=club_id,
                        data={
                            'release_clause': player.release_clause,
                            'market_value': player.market_value,
                            'savings': player.market_value - player.release_clause,
                            'opportunity_type': 'release_clause'
                        },
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=7)
                    )
                    
                    await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar cláusulas de rescisão: {e}")
    
    async def _check_injury_recoveries(self, club_id: str, rules: Dict) -> None:
        """Monitorar recuperações de lesões importantes"""
        
        try:
            db = next(get_db())
            
            # Buscar jogadores que estavam lesionados mas podem estar voltando
            recovery_candidates = db.query(Player).filter(
                Player.days_injured_season > 30,  # Esteve lesionado por mais de 30 dias
                Player.overall_rating >= 8.0,    # Alta qualidade
                Player.age <= 30
            ).limit(15).all()
            
            for player in recovery_candidates:
                # Simular verificação de status de lesão atual
                # Em produção, verificaria via API se ainda está lesionado
                
                alert = Alert(
                    id=f"injury_recovery_{player.id}_{club_id}",
                    type=AlertType.INJURY_RECOVERY,
                    priority=AlertPriority.MEDIUM,
                    title=f"Recuperação de lesão: {player.name}",
                    message=f"{player.name} pode estar retornando de lesão. "
                           f"Oportunidade para negociar com desconto.",
                    player_id=player.id,
                    club_id=club_id,
                    data={
                        'days_injured': player.days_injured_season,
                        'pre_injury_rating': player.overall_rating,
                        'opportunity_type': 'post_injury_discount'
                    },
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(days=10)
                )
                
                await self._send_alert(alert)
        
        except Exception as e:
            logger.error(f"Erro ao verificar recuperações de lesões: {e}")
    
    async def _send_alert(self, alert: Alert) -> None:
        """Enviar alerta para os subscribers do clube"""
        
        # Verificar se já existe alerta similar recente
        existing_key = f"{alert.type.value}_{alert.player_id}_{alert.club_id}"
        
        if existing_key in self.active_alerts:
            existing_alert = self.active_alerts[existing_key]
            # Se o alerta é muito recente (menos de 24h), não enviar duplicata
            if (datetime.now() - existing_alert.created_at).total_seconds() < 86400:
                return
        
        # Salvar alerta
        self.active_alerts[alert.id] = alert
        
        # Enviar para subscribers
        if alert.club_id in self.alert_subscribers:
            for callback in self.alert_subscribers[alert.club_id]:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Erro ao enviar alerta via callback: {e}")
        
        logger.info(f"Alerta enviado: {alert.title} para clube {alert.club_id}")
    
    async def get_club_alerts(
        self, 
        club_id: str, 
        alert_type: Optional[AlertType] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Alert]:
        """Obter alertas de um clube"""
        
        alerts = [
            alert for alert in self.active_alerts.values() 
            if alert.club_id == club_id
        ]
        
        if alert_type:
            alerts = [alert for alert in alerts if alert.type == alert_type]
        
        if unread_only:
            alerts = [alert for alert in alerts if not alert.is_read]
        
        # Ordenar por prioridade e data
        priority_order = {AlertPriority.CRITICAL: 4, AlertPriority.HIGH: 3, AlertPriority.MEDIUM: 2, AlertPriority.LOW: 1}
        alerts.sort(
            key=lambda x: (priority_order[x.priority], x.created_at),
            reverse=True
        )
        
        return alerts[:limit]
    
    async def mark_alert_as_read(self, alert_id: str) -> bool:
        """Marcar alerta como lido"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].is_read = True
            return True
        return False
    
    async def mark_alert_as_acted_upon(self, alert_id: str) -> bool:
        """Marcar alerta como ação tomada"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].is_acted_upon = True
            return True
        return False
    
    async def cleanup_expired_alerts(self) -> int:
        """Limpar alertas expirados"""
        now = datetime.now()
        expired_ids = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.expires_at and now > alert.expires_at:
                expired_ids.append(alert_id)
        
        for alert_id in expired_ids:
            del self.active_alerts[alert_id]
        
        logger.info(f"Removidos {len(expired_ids)} alertas expirados")
        return len(expired_ids)
    
    def get_alert_stats(self, club_id: str) -> Dict[str, Any]:
        """Obter estatísticas de alertas do clube"""
        
        club_alerts = [a for a in self.active_alerts.values() if a.club_id == club_id]
        
        total_alerts = len(club_alerts)
        unread_alerts = len([a for a in club_alerts if not a.is_read])
        high_priority = len([a for a in club_alerts if a.priority == AlertPriority.HIGH])
        
        type_breakdown = {}
        for alert in club_alerts:
            alert_type = alert.type.value
            type_breakdown[alert_type] = type_breakdown.get(alert_type, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'unread_alerts': unread_alerts,
            'high_priority_alerts': high_priority,
            'alert_types': type_breakdown,
            'last_updated': datetime.now().isoformat()
        }

# Instância global do serviço de alertas
alerts_service = AlertsService()