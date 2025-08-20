"""
🔗 Soccer Scout AI - Serviço de Webhooks
Sistema de notificações em tempo real para eventos importantes
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import uuid
import logging
from utils.cache_service import cache_service

logger = logging.getLogger(__name__)

class WebhookEvent(Enum):
    # Shortlist events
    SHORTLIST_CREATED = "shortlist.created"
    SHORTLIST_UPDATED = "shortlist.updated"
    PLAYER_ADDED_TO_SHORTLIST = "shortlist.player.added"
    PLAYER_STATUS_CHANGED = "shortlist.player.status_changed"
    
    # Alert events  
    ALERT_CREATED = "alert.created"
    CRITICAL_ALERT = "alert.critical"
    
    # Player events
    PLAYER_TRANSFER = "player.transfer"
    PLAYER_INJURY = "player.injury"
    PLAYER_RECOVERY = "player.recovery"
    CONTRACT_EXPIRING = "player.contract_expiring"
    
    # Market events
    PRICE_DROP = "market.price_drop"
    UNDERVALUED_DETECTED = "market.undervalued"
    MARKET_OPPORTUNITY = "market.opportunity"
    
    # System events
    USER_CREATED = "user.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    DATA_SYNC_COMPLETED = "system.data_sync_completed"

@dataclass
class WebhookEndpoint:
    id: str
    club_id: str
    url: str
    events: List[WebhookEvent]
    secret: str
    is_active: bool = True
    created_at: datetime = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    failure_count: int = 0
    max_failures: int = 10

@dataclass
class WebhookDelivery:
    id: str
    endpoint_id: str
    event: WebhookEvent
    payload: Dict[str, Any]
    status: str  # pending, delivered, failed, expired
    attempts: int = 0
    max_attempts: int = 5
    created_at: datetime = None
    delivered_at: Optional[datetime] = None
    next_retry: Optional[datetime] = None

class WebhookService:
    """Serviço de webhooks para notificações em tempo real"""
    
    def __init__(self):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.is_processing = False
        self.max_concurrent_deliveries = 10
        self.retry_intervals = [60, 300, 900, 3600, 7200]  # segundos
    
    async def start_processing(self):
        """Iniciar processamento de webhooks"""
        if self.is_processing:
            return
        
        self.is_processing = True
        
        # Iniciar workers de entrega
        workers = []
        for i in range(self.max_concurrent_deliveries):
            worker = asyncio.create_task(self._delivery_worker())
            workers.append(worker)
        
        logger.info(f"Webhook service iniciado com {self.max_concurrent_deliveries} workers")
    
    async def stop_processing(self):
        """Parar processamento de webhooks"""
        self.is_processing = False
        logger.info("Webhook service parado")
    
    def register_endpoint(
        self,
        club_id: str,
        url: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None
    ) -> WebhookEndpoint:
        """Registrar novo endpoint de webhook"""
        
        endpoint_id = str(uuid.uuid4())
        webhook_secret = secret or f"whsec_{uuid.uuid4().hex}"
        
        endpoint = WebhookEndpoint(
            id=endpoint_id,
            club_id=club_id,
            url=url,
            events=events,
            secret=webhook_secret,
            created_at=datetime.now()
        )
        
        self.endpoints[endpoint_id] = endpoint
        
        logger.info(f"Webhook endpoint registrado: {url} para clube {club_id}")
        
        return endpoint
    
    def update_endpoint(
        self,
        endpoint_id: str,
        url: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Atualizar endpoint existente"""
        
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint:
            return False
        
        if url is not None:
            endpoint.url = url
        if events is not None:
            endpoint.events = events
        if is_active is not None:
            endpoint.is_active = is_active
        
        logger.info(f"Webhook endpoint atualizado: {endpoint_id}")
        
        return True
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Remover endpoint"""
        
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Webhook endpoint removido: {endpoint_id}")
            return True
        
        return False
    
    async def emit_event(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        club_id: Optional[str] = None,
        target_endpoint_ids: Optional[List[str]] = None
    ) -> List[str]:
        """Emitir evento para webhooks relevantes"""
        
        delivery_ids = []
        
        # Encontrar endpoints relevantes
        relevant_endpoints = []
        
        if target_endpoint_ids:
            # Endpoints específicos
            relevant_endpoints = [
                ep for ep_id, ep in self.endpoints.items()
                if ep_id in target_endpoint_ids and ep.is_active
            ]
        else:
            # Endpoints por evento e clube
            relevant_endpoints = [
                ep for ep in self.endpoints.values()
                if ep.is_active and event in ep.events and 
                (club_id is None or ep.club_id == club_id)
            ]
        
        # Criar deliveries
        for endpoint in relevant_endpoints:
            delivery_id = await self._create_delivery(endpoint, event, data)
            if delivery_id:
                delivery_ids.append(delivery_id)
        
        logger.info(f"Evento {event.value} emitido para {len(delivery_ids)} endpoints")
        
        return delivery_ids
    
    async def _create_delivery(
        self,
        endpoint: WebhookEndpoint,
        event: WebhookEvent,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """Criar nova delivery e adicionar à fila"""
        
        # Verificar se endpoint não falhou muito
        if endpoint.failure_count >= endpoint.max_failures:
            logger.warning(f"Endpoint {endpoint.id} desabilitado por muitas falhas")
            endpoint.is_active = False
            return None
        
        delivery_id = str(uuid.uuid4())
        
        # Preparar payload
        payload = {
            'event': event.value,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'delivery_id': delivery_id,
            'endpoint_id': endpoint.id
        }
        
        delivery = WebhookDelivery(
            id=delivery_id,
            endpoint_id=endpoint.id,
            event=event,
            payload=payload,
            status='pending',
            created_at=datetime.now()
        )
        
        self.deliveries[delivery_id] = delivery
        
        # Adicionar à fila de entrega
        await self.delivery_queue.put(delivery_id)
        
        return delivery_id
    
    async def _delivery_worker(self):
        """Worker para processar deliveries"""
        
        while self.is_processing:
            try:
                # Pegar próxima delivery da fila
                delivery_id = await asyncio.wait_for(
                    self.delivery_queue.get(),
                    timeout=1.0
                )
                
                delivery = self.deliveries.get(delivery_id)
                if not delivery:
                    continue
                
                await self._attempt_delivery(delivery)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro no delivery worker: {e}")
    
    async def _attempt_delivery(self, delivery: WebhookDelivery):
        """Tentar entregar webhook"""
        
        endpoint = self.endpoints.get(delivery.endpoint_id)
        if not endpoint or not endpoint.is_active:
            delivery.status = 'failed'
            return
        
        delivery.attempts += 1
        
        try:
            # Preparar headers
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Event': delivery.event.value,
                'X-Webhook-Delivery': delivery.id,
                'X-Webhook-Timestamp': str(int(delivery.created_at.timestamp()))
            }
            
            # Adicionar signature se tiver secret
            if endpoint.secret:
                signature = self._generate_signature(
                    json.dumps(delivery.payload, sort_keys=True),
                    endpoint.secret
                )
                headers['X-Webhook-Signature'] = f"sha256={signature}"
            
            # Fazer request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(
                    endpoint.url,
                    json=delivery.payload,
                    headers=headers
                ) as response:
                    
                    if 200 <= response.status < 300:
                        # Sucesso
                        delivery.status = 'delivered'
                        delivery.delivered_at = datetime.now()
                        endpoint.last_success = datetime.now()
                        endpoint.failure_count = 0  # Reset failure count
                        
                        logger.info(f"Webhook entregue com sucesso: {delivery.id} -> {endpoint.url}")
                        
                    else:
                        # Falha HTTP
                        await self._handle_delivery_failure(delivery, endpoint, f"HTTP {response.status}")
        
        except Exception as e:
            # Falha de conexão/timeout
            await self._handle_delivery_failure(delivery, endpoint, str(e))
    
    async def _handle_delivery_failure(
        self,
        delivery: WebhookDelivery,
        endpoint: WebhookEndpoint,
        error: str
    ):
        """Tratar falha na entrega"""
        
        endpoint.last_failure = datetime.now()
        endpoint.failure_count += 1
        
        logger.warning(f"Falha na entrega do webhook {delivery.id}: {error}")
        
        # Verificar se deve tentar novamente
        if delivery.attempts < delivery.max_attempts:
            # Agendar retry
            retry_delay = self.retry_intervals[min(delivery.attempts - 1, len(self.retry_intervals) - 1)]
            delivery.next_retry = datetime.now() + timedelta(seconds=retry_delay)
            delivery.status = 'pending'
            
            # Reagendar delivery
            await asyncio.sleep(retry_delay)
            await self.delivery_queue.put(delivery.id)
            
            logger.info(f"Webhook reagendado para retry em {retry_delay}s")
        else:
            # Máximo de tentativas atingido
            delivery.status = 'failed'
            logger.error(f"Webhook delivery falhou definitivamente: {delivery.id}")
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Gerar signature HMAC para verificação"""
        import hmac
        import hashlib
        
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_endpoint_deliveries(
        self,
        endpoint_id: str,
        limit: int = 50
    ) -> List[WebhookDelivery]:
        """Obter histórico de deliveries de um endpoint"""
        
        endpoint_deliveries = [
            delivery for delivery in self.deliveries.values()
            if delivery.endpoint_id == endpoint_id
        ]
        
        # Ordenar por data (mais recentes primeiro)
        endpoint_deliveries.sort(
            key=lambda d: d.created_at,
            reverse=True
        )
        
        return endpoint_deliveries[:limit]
    
    def get_club_endpoints(self, club_id: str) -> List[WebhookEndpoint]:
        """Obter endpoints de um clube"""
        
        return [
            endpoint for endpoint in self.endpoints.values()
            if endpoint.club_id == club_id
        ]
    
    def get_delivery_stats(self, endpoint_id: str) -> Dict[str, Any]:
        """Obter estatísticas de entrega de um endpoint"""
        
        deliveries = self.get_endpoint_deliveries(endpoint_id, 1000)
        
        total_deliveries = len(deliveries)
        successful_deliveries = len([d for d in deliveries if d.status == 'delivered'])
        failed_deliveries = len([d for d in deliveries if d.status == 'failed'])
        pending_deliveries = len([d for d in deliveries if d.status == 'pending'])
        
        success_rate = (successful_deliveries / max(total_deliveries, 1)) * 100
        
        # Deliveries por dia (últimos 7 dias)
        daily_stats = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            daily_deliveries = [
                d for d in deliveries
                if d.created_at.date() == date
            ]
            daily_stats[date.isoformat()] = len(daily_deliveries)
        
        return {
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'pending_deliveries': pending_deliveries,
            'success_rate': round(success_rate, 2),
            'daily_stats': daily_stats
        }
    
    async def retry_failed_deliveries(self, endpoint_id: Optional[str] = None) -> int:
        """Retentar deliveries que falharam"""
        
        failed_deliveries = [
            delivery for delivery in self.deliveries.values()
            if delivery.status == 'failed' and 
            (endpoint_id is None or delivery.endpoint_id == endpoint_id)
        ]
        
        retried_count = 0
        
        for delivery in failed_deliveries:
            if delivery.attempts < delivery.max_attempts:
                delivery.status = 'pending'
                delivery.attempts = 0  # Reset attempts
                await self.delivery_queue.put(delivery.id)
                retried_count += 1
        
        logger.info(f"Retriando {retried_count} deliveries falhadas")
        
        return retried_count
    
    def cleanup_old_deliveries(self, days_old: int = 30) -> int:
        """Limpar deliveries antigas"""
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        old_delivery_ids = []
        
        for delivery_id, delivery in self.deliveries.items():
            if delivery.created_at < cutoff_date and delivery.status in ['delivered', 'failed']:
                old_delivery_ids.append(delivery_id)
        
        for delivery_id in old_delivery_ids:
            del self.deliveries[delivery_id]
        
        logger.info(f"Removidas {len(old_delivery_ids)} deliveries antigas")
        
        return len(old_delivery_ids)
    
    # ========================================
    # 🎯 EVENTOS ESPECÍFICOS PRÉ-DEFINIDOS
    # ========================================
    
    async def emit_shortlist_created(self, club_id: str, shortlist_data: Dict):
        """Emitir evento de shortlist criada"""
        await self.emit_event(
            WebhookEvent.SHORTLIST_CREATED,
            shortlist_data,
            club_id
        )
    
    async def emit_player_status_changed(
        self,
        club_id: str,
        shortlist_id: str,
        player_id: int,
        old_status: str,
        new_status: str,
        notes: str = ""
    ):
        """Emitir evento de mudança de status do jogador"""
        data = {
            'shortlist_id': shortlist_id,
            'player_id': player_id,
            'old_status': old_status,
            'new_status': new_status,
            'notes': notes,
            'changed_at': datetime.now().isoformat()
        }
        
        await self.emit_event(
            WebhookEvent.PLAYER_STATUS_CHANGED,
            data,
            club_id
        )
    
    async def emit_critical_alert(self, club_id: str, alert_data: Dict):
        """Emitir alerta crítico"""
        await self.emit_event(
            WebhookEvent.CRITICAL_ALERT,
            alert_data,
            club_id
        )
    
    async def emit_market_opportunity(self, club_id: str, opportunity_data: Dict):
        """Emitir oportunidade de mercado"""
        await self.emit_event(
            WebhookEvent.MARKET_OPPORTUNITY,
            opportunity_data,
            club_id
        )
    
    async def emit_contract_expiring(self, club_id: str, player_data: Dict):
        """Emitir alerta de contrato expirando"""
        await self.emit_event(
            WebhookEvent.CONTRACT_EXPIRING,
            player_data,
            club_id
        )
    
    async def emit_data_sync_completed(self, sync_stats: Dict):
        """Emitir evento de sincronização de dados concluída"""
        await self.emit_event(
            WebhookEvent.DATA_SYNC_COMPLETED,
            sync_stats
        )

# Instância global do serviço de webhooks
webhook_service = WebhookService()

# Função para integração com outros serviços
def setup_webhook_integrations():
    """Configurar integrações com webhooks"""
    
    # Integração com serviço de alertas
    from services.alerts_service import alerts_service
    
    def on_alert_created(alert):
        """Callback para quando um alerta é criado"""
        asyncio.create_task(
            webhook_service.emit_event(
                WebhookEvent.ALERT_CREATED,
                {
                    'alert_id': alert.id,
                    'type': alert.type.value,
                    'priority': alert.priority.value,
                    'title': alert.title,
                    'message': alert.message,
                    'player_id': alert.player_id
                },
                alert.club_id
            )
        )
        
        # Se for alerta crítico, emitir evento específico
        if alert.priority.value == 'critical':
            asyncio.create_task(
                webhook_service.emit_critical_alert(
                    alert.club_id,
                    {
                        'alert_id': alert.id,
                        'title': alert.title,
                        'message': alert.message,
                        'data': alert.data
                    }
                )
            )
    
    # Registrar callback (em produção seria mais elegante)
    logger.info("Integrações de webhook configuradas")

# Executar setup
setup_webhook_integrations()