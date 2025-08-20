from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

from config import settings
from services.sportmonks_api import SportmonksAPI
from services.enhanced_sportmonks_api import EnhancedSportmonksAPI
from services.openai_service import OpenAIService
from services.player_service import PlayerService
from services.club_services import ClubScoutingService, PlayerComparisonService
from services.advanced_filters import AdvancedPlayerFilters, ClubSpecificFilters
from services.shortlist_service import ShortlistService
from services.alerts_service import alerts_service, Alert, AlertType, AlertPriority
from services.multi_tenant_service import multi_tenant_service, UserRole, Permission
from services.conversation_service import conversation_service
from services.visualization_service import visualization_service
from services.scheduler_service import scheduler_service
from utils.cache_service import cache_service
from database.models import init_db

# Novos serviços de IA avançada
from ai_services.tactical_analyzer import TacticalAnalyzer
from ai_services.performance_predictor import PerformancePredictor
from ai_services.report_generator import ReportGenerator
from ai_services.intelligent_assistant import IntelligentAssistant

app = FastAPI(
    title="Soccer Scout AI",
    description="Sistema de scouting de futebol integrado com IA para consultas inteligentes sobre jogadores",
    version="1.0.0"
)

# Inicializar serviços básicos
sportmonks_api = SportmonksAPI()
enhanced_sportmonks_api = EnhancedSportmonksAPI()
openai_service = OpenAIService()
player_service = PlayerService(sportmonks_api, openai_service)

# Inicializar serviços de IA avançada
tactical_analyzer = TacticalAnalyzer()
performance_predictor = PerformancePredictor()
report_generator = ReportGenerator()
intelligent_assistant = IntelligentAssistant()

# Inicializar serviços específicos para clubes
club_scouting = ClubScoutingService()
player_comparison = PlayerComparisonService()
advanced_filters = AdvancedPlayerFilters()
club_filters = ClubSpecificFilters()
shortlist_service = ShortlistService()

# Inicializar scheduler
scheduler_service.start()

# Templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    players: list
    explanation: str
    query_processed: str

# Novos modelos para IA avançada
class TacticalAnalysisRequest(BaseModel):
    player_id: int
    tactical_system: str

class PerformancePredictionRequest(BaseModel):
    player_id: int
    timeframe: str = "6_months"

class TeamAnalysisRequest(BaseModel):
    player_ids: list[int]
    team_name: str = "Equipe Alvo"

class IntelligentQueryRequest(BaseModel):
    query: str
    context: dict = None

class ReportRequest(BaseModel):
    player_id: int
    detailed: bool = True

class ComparisonRequest(BaseModel):
    player_ids: list[int]

# ========================================
# 🎯 NOVOS MODELOS PARA CLUBES
# ========================================

class ClubSearchRequest(BaseModel):
    query: str
    club_context: Optional[Dict[str, Any]] = None
    max_results: Optional[int] = 20

class AdvancedFiltersRequest(BaseModel):
    filters: Dict[str, Any]
    limit: Optional[int] = 20

class MarketAnalysisRequest(BaseModel):
    position: Optional[str] = None
    max_value: Optional[float] = None
    league: Optional[str] = None

class ClubComparisonRequest(BaseModel):
    player_ids: List[int]
    comparison_type: Optional[str] = "complete"  # complete, tactical, financial

class ScoutingReportRequest(BaseModel):
    player_id: int
    club_context: Optional[Dict[str, Any]] = None
    detailed: Optional[bool] = True

class ClubNeedRequest(BaseModel):
    tactical_system: str
    position_needed: str
    max_budget: Optional[float] = None
    max_age: Optional[int] = None
    must_have_characteristics: Optional[List[str]] = []
    preferred_characteristics: Optional[List[str]] = []

@app.on_event("startup")
async def startup_event():
    """Inicializar banco de dados na inicialização"""
    init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página inicial com interface do chatbot"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/scout", response_model=QueryResponse)
async def scout_players(query_request: QueryRequest):
    """
    Endpoint principal para consultas de scouting
    
    Exemplos de consultas:
    - "Quero um meia direita até 50 milhões que fez mais de 10 gols"
    - "Mostre zagueiros jovens com bom passe"
    - "Atacantes rapidos e baratos para a Premier League"
    """
    try:
        result = await player_service.process_scout_query(query_request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leagues")
async def get_leagues():
    """Listar ligas disponíveis"""
    try:
        leagues = await sportmonks_api.get_leagues()
        return {"leagues": leagues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions():
    """Listar posições disponíveis"""
    positions = [
        "Goalkeeper", "Centre-Back", "Left-Back", "Right-Back",
        "Defensive Midfield", "Central Midfield", "Attacking Midfield",
        "Left Winger", "Right Winger", "Centre-Forward", "Second Striker"
    ]
    return {"positions": positions}

@app.get("/api/player/{player_id}")
async def get_player_details(player_id: int):
    """Obter detalhes completos de um jogador"""
    try:
        player = await sportmonks_api.get_player_details(player_id)
        return {"player": player}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Player not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# ========================================
# 🧠 ENDPOINTS DE IA AVANÇADA
# ========================================

@app.post("/api/ai/intelligent-query")
async def intelligent_query(request: IntelligentQueryRequest):
    """
    Processamento inteligente de consultas com IA avançada
    
    Exemplos:
    - "Qual a melhor formação para contra-ataques rápidos?"
    - "Compare Mbappé com Haaland em termos táticos"
    - "Analise o mercado de laterais-direitos jovens"
    """
    try:
        result = await intelligent_assistant.process_advanced_query(
            request.query, 
            request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/tactical-analysis")
async def tactical_analysis(request: TacticalAnalysisRequest):
    """Análise tática avançada de adequação jogador-sistema"""
    try:
        # Buscar dados do jogador
        player = await sportmonks_api.get_player_details(request.player_id)
        
        # Análise tática
        analysis = await tactical_analyzer.analyze_player_tactical_fit(
            player, request.tactical_system
        )
        
        return {
            "player": player,
            "tactical_system": request.tactical_system,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/performance-prediction")
async def performance_prediction(request: PerformancePredictionRequest):
    """Predição de performance futura usando IA"""
    try:
        # Buscar dados do jogador
        player = await sportmonks_api.get_player_details(request.player_id)
        
        # Predição de performance
        prediction = await performance_predictor.predict_player_future_performance(
            player, request.timeframe
        )
        
        return {
            "player": player,
            "timeframe": request.timeframe,
            "prediction": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/scouting-report")
async def generate_scouting_report(request: ReportRequest):
    """Gerar relatório completo de scouting com IA"""
    try:
        # Buscar dados do jogador
        player = await sportmonks_api.get_player_details(request.player_id)
        
        # Gerar relatório
        report = await report_generator.generate_player_scouting_report(
            player, request.detailed
        )
        
        return {
            "player": player,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/team-analysis")
async def team_analysis(request: TeamAnalysisRequest):
    """Análise completa de equipe com IA"""
    try:
        # Buscar dados dos jogadores
        players = []
        for player_id in request.player_ids:
            player = await sportmonks_api.get_player_details(player_id)
            players.append(player)
        
        # Análise da equipe
        analysis = await report_generator.generate_team_analysis_report(
            players, request.team_name
        )
        
        return {
            "team_name": request.team_name,
            "players": players,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/compare-players")
async def compare_players(request: ComparisonRequest):
    """Comparação avançada entre jogadores"""
    try:
        # Buscar dados dos jogadores
        players = []
        for player_id in request.player_ids:
            player = await sportmonks_api.get_player_details(player_id)
            players.append(player)
        
        # Comparação de trajetórias
        comparison = await performance_predictor.compare_player_trajectories(players)
        
        return {
            "players": players,
            "comparison": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/formation-optimizer")
async def formation_optimizer(request: TeamAnalysisRequest):
    """Otimizador de formação com IA"""
    try:
        # Buscar dados dos jogadores
        players = []
        for player_id in request.player_ids:
            player = await sportmonks_api.get_player_details(player_id)
            players.append(player)
        
        # Testar diferentes sistemas
        systems = ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2"]
        comparison = await tactical_analyzer.compare_tactical_systems(players, systems)
        
        return {
            "team_name": request.team_name,
            "players": players,
            "system_comparison": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/market-trends/{position}")
async def market_trends(position: str, league: str = None):
    """Análise de tendências de mercado por posição"""
    try:
        trends = await performance_predictor.predict_market_trends(position, league)
        return {
            "position": position,
            "league": league,
            "trends": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/conversation-history")
async def get_conversation_history():
    """Obter histórico da conversa com IA"""
    try:
        summary = await intelligent_assistant.get_conversation_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/clear-conversation")
async def clear_conversation():
    """Limpar histórico da conversa"""
    try:
        intelligent_assistant.clear_conversation()
        return {"message": "Conversa limpa com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/smart-suggestions")
async def get_smart_suggestions():
    """Obter sugestões inteligentes baseadas no contexto"""
    try:
        suggestions = await intelligent_assistant.get_smart_suggestions()
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# ⚽ ENDPOINTS ESPECÍFICOS PARA CLUBES
# ========================================

@app.post("/api/club/intelligent-search")
async def club_intelligent_search(request: ClubSearchRequest):
    """
    🎯 Busca inteligente específica para clubes
    
    Exemplos:
    - "Preciso de um centroavante até 25 anos, rápido, que faça muitos gols para meu 4-5-1"
    - "Busco um lateral-esquerdo que cruze bem, até 30M, para sistema ofensivo"
    - "Quero um zagueiro alto, experiente, bom no jogo aéreo, até 15M"
    """
    try:
        result = await club_scouting.intelligent_player_search(
            request.query, 
            request.club_context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/club/advanced-filters")
async def advanced_filters_search(request: AdvancedFiltersRequest):
    """
    🔍 Sistema de filtros ultra avançado
    
    Suporta todos os filtros possíveis:
    - Contratuais, financeiros, performance, características físicas, etc.
    """
    try:
        players = await advanced_filters.advanced_player_search(request.filters)
        return {
            "filters_applied": request.filters,
            "players_found": players,
            "total_count": len(players)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/club/compare-players")
async def club_compare_players(request: ClubComparisonRequest):
    """
    ⚖️ Comparação avançada entre jogadores para clubes
    
    Tipos de comparação:
    - complete: Comparação completa em todas as áreas
    - tactical: Foco em aspectos táticos 
    - financial: Foco em aspectos financeiros e contratuais
    """
    try:
        result = await club_scouting.compare_players(
            request.player_ids, 
            request.comparison_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/club/market-opportunities")
async def market_opportunities(request: MarketAnalysisRequest):
    """
    💰 Análise de oportunidades no mercado
    
    Identifica:
    - Agentes livres
    - Contratos terminando
    - Jogadores subvalorizados
    - Oportunidades de empréstimo
    - Estrelas em ascensão
    """
    try:
        opportunities = await club_scouting.market_opportunities(
            request.position, 
            request.max_value
        )
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/club/free-agents")
async def get_free_agents(
    position: Optional[str] = None,
    max_value: Optional[float] = None,
    min_rating: Optional[float] = 6.5
):
    """
    🆓 Lista de agentes livres disponíveis
    """
    try:
        filters = {
            'free_agents': True,
            'overall_rating_min': min_rating
        }
        if position:
            filters['position'] = [position]
        if max_value:
            filters['market_value_max'] = max_value
        
        players = await advanced_filters.advanced_player_search(filters)
        return {
            "free_agents": players,
            "total_count": len(players),
            "filters_applied": filters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/club/young-prospects")
async def get_young_prospects(
    max_age: Optional[int] = 21,
    max_value: Optional[float] = None,
    min_potential: Optional[float] = 7.5
):
    """
    🌟 Jovens promessas com alto potencial
    """
    try:
        filters = {
            'age_max': max_age,
            'potential_rating_min': min_potential,
            'market_trend': 'rising',
            'minutes_min': 300  # Alguma experiência
        }
        if max_value:
            filters['market_value_max'] = max_value
        
        players = await advanced_filters.advanced_player_search(filters)
        return {
            "young_prospects": players,
            "total_count": len(players),
            "criteria": {
                "max_age": max_age,
                "min_potential": min_potential,
                "max_value": max_value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# 🔐 ENDPOINTS DE AUTENTICAÇÃO
# ========================================

@app.post("/api/auth/login")
async def login(email: str, password: str):
    """Login de usuário"""
    token = multi_tenant_service.authenticate_user(email, password)
    if not token:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def get_current_user(authorization: str = None):
    """Obter dados do usuário atual"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = authorization.split(" ")[1]
    user_context = multi_tenant_service.get_user_context(token)
    
    if not user_context:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    return user_context

# ========================================
# 📋 ENDPOINTS DE SHORTLISTS
# ========================================

@app.post("/api/shortlists")
async def create_shortlist(
    name: str,
    position: str, 
    criteria: Dict[str, Any],
    authorization: str = None
):
    """Criar nova shortlist"""
    # Verificar autenticação
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = authorization.split(" ")[1]
    token_data = multi_tenant_service.verify_token(token)
    
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Verificar permissão
    if not multi_tenant_service.check_permission(token_data, Permission.CREATE_SHORTLIST):
        raise HTTPException(status_code=403, detail="Sem permissão para criar shortlists")
    
    shortlist = await shortlist_service.create_shortlist(
        club_id=token_data['club_id'],
        name=name,
        position=position,
        criteria=criteria,
        user_id=token_data['user_id']
    )
    
    return shortlist

@app.post("/api/shortlists/{shortlist_id}/players/{player_id}/status")
async def update_player_status(
    shortlist_id: str,
    player_id: int,
    new_status: str,
    notes: str = "",
    priority: str = None,
    authorization: str = None
):
    """Atualizar status de jogador na shortlist"""
    # Verificar autenticação e permissão
    token = authorization.split(" ")[1] if authorization and authorization.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token_data = multi_tenant_service.verify_token(token)
    if not token_data or not multi_tenant_service.check_permission(token_data, Permission.EDIT_SHORTLIST):
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    success = await shortlist_service.update_player_status(
        shortlist_id, player_id, new_status, notes, priority
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Shortlist ou jogador não encontrado")
    
    return {"message": "Status atualizado com sucesso"}

@app.post("/api/players/{player_id}/dossier")
async def generate_player_dossier(
    player_id: int,
    club_context: Dict = None,
    authorization: str = None
):
    """Gerar dossiê completo de jogador"""
    token = authorization.split(" ")[1] if authorization and authorization.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token_data = multi_tenant_service.verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    dossier = await shortlist_service.generate_player_dossier(player_id, club_context)
    return dossier

# ========================================
# 🚨 ENDPOINTS DE ALERTAS
# ========================================

@app.get("/api/alerts")
async def get_club_alerts(
    alert_type: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
    authorization: str = None
):
    """Obter alertas do clube"""
    token = authorization.split(" ")[1] if authorization and authorization.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token_data = multi_tenant_service.verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    alert_type_enum = AlertType(alert_type) if alert_type else None
    alerts = await alerts_service.get_club_alerts(
        token_data['club_id'], alert_type_enum, unread_only, limit
    )
    
    return {"alerts": [
        {
            "id": alert.id,
            "type": alert.type.value,
            "priority": alert.priority.value,
            "title": alert.title,
            "message": alert.message,
            "player_id": alert.player_id,
            "data": alert.data,
            "created_at": alert.created_at.isoformat(),
            "is_read": alert.is_read
        }
        for alert in alerts
    ]}

@app.post("/api/alerts/{alert_id}/read")
async def mark_alert_as_read(alert_id: str):
    """Marcar alerta como lido"""
    success = await alerts_service.mark_alert_as_read(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    return {"message": "Alerta marcado como lido"}

# ========================================
# 💬 ENDPOINTS DE CONVERSAS
# ========================================

@app.post("/api/conversations")
async def create_conversation(
    initial_query: str,
    authorization: str = None
):
    """Criar nova conversa"""
    token = authorization.split(" ")[1] if authorization and authorization.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token_data = multi_tenant_service.verify_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    conversation_id = conversation_service.create_conversation(
        token_data['club_id'], token_data['user_id'], initial_query
    )
    
    return {"conversation_id": conversation_id}

@app.get("/api/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """Obter histórico de conversa"""
    history = conversation_service.get_conversation_history(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    return history

# ========================================
# 📊 ENDPOINTS DE VISUALIZAÇÕES
# ========================================

@app.post("/api/visualizations/radar")
async def generate_player_radar(
    player_data: Dict[str, Any],
    comparison_player: Optional[Dict[str, Any]] = None
):
    """Gerar gráfico radar de jogador"""
    viz_url = visualization_service.generate_player_radar(player_data, comparison_player)
    return {"visualization_url": viz_url}

@app.post("/api/visualizations/heatmap")
async def generate_position_heatmap(position_data: Dict[str, float]):
    """Gerar heatmap de posições"""
    viz_url = visualization_service.generate_position_heatmap(position_data)
    return {"visualization_url": viz_url}

@app.post("/api/visualizations/market-comparison")
async def generate_market_comparison(players: List[Dict]):
    """Gerar comparação de mercado"""
    viz_url = visualization_service.generate_market_comparison_chart(players)
    return {"visualization_url": viz_url}

# ========================================
# 📈 ENDPOINTS DE ANALYTICS E CACHE
# ========================================

@app.get("/api/system/cache-stats")
async def get_cache_stats():
    """Obter estatísticas do cache"""
    return cache_service.get_all_stats()

@app.get("/api/system/health")
async def health_check():
    """Health check completo do sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache_stats": cache_service.get_all_stats(),
        "scheduler_running": scheduler_service.is_running,
        "services": {
            "sportmonks_api": "active",
            "openai_service": "active", 
            "alerts_service": "active",
            "multi_tenant": "active"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )