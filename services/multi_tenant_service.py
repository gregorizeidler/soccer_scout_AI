"""
🏢 Soccer Scout AI - Serviço Multi-Tenant
Sistema de autenticação, autorização e isolamento por clube
"""

import jwt
import bcrypt
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import secrets
import logging
from config import settings

logger = logging.getLogger(__name__)

class UserRole(Enum):
    ADMIN = "admin"              # Administrador do sistema
    DIRECTOR = "director"        # Diretor do clube (acesso total)
    SCOUT_MANAGER = "scout_manager"  # Gerente de scouts
    SCOUT = "scout"              # Scout (acesso limitado)
    ANALYST = "analyst"          # Analista (só visualização)
    VIEWER = "viewer"            # Visualização básica

class Permission(Enum):
    # Shortlists
    CREATE_SHORTLIST = "create_shortlist"
    EDIT_SHORTLIST = "edit_shortlist"
    DELETE_SHORTLIST = "delete_shortlist"
    VIEW_SHORTLIST = "view_shortlist"
    
    # Players
    VIEW_PLAYER_DETAILS = "view_player_details"
    VIEW_ADVANCED_STATS = "view_advanced_stats"
    ACCESS_MARKET_DATA = "access_market_data"
    VIEW_CONTRACT_INFO = "view_contract_info"
    
    # Reports
    GENERATE_REPORTS = "generate_reports"
    EXPORT_REPORTS = "export_reports"
    
    # Settings
    MANAGE_USERS = "manage_users"
    CONFIGURE_ALERTS = "configure_alerts"
    ACCESS_ADMIN_PANEL = "access_admin_panel"
    
    # API
    API_ACCESS = "api_access"
    BULK_OPERATIONS = "bulk_operations"

@dataclass
class User:
    id: str
    email: str
    name: str
    club_id: str
    role: UserRole
    permissions: List[Permission]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    preferences: Dict[str, Any] = None

@dataclass
class Club:
    id: str
    name: str
    country: str
    tier: int  # 1 = elite, 2 = professional, 3 = semi-pro
    subscription_plan: str  # basic, professional, enterprise
    max_users: int
    features: List[str]
    created_at: datetime
    is_active: bool = True

class MultiTenantService:
    """Serviço de multi-tenancy e controle de acesso"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY or secrets.token_urlsafe(32)
        self.token_expiry_hours = 24
        
        # Role permissions mapping
        self.role_permissions = {
            UserRole.ADMIN: list(Permission),  # Admin tem todas as permissões
            
            UserRole.DIRECTOR: [
                Permission.CREATE_SHORTLIST, Permission.EDIT_SHORTLIST, Permission.DELETE_SHORTLIST,
                Permission.VIEW_SHORTLIST, Permission.VIEW_PLAYER_DETAILS, Permission.VIEW_ADVANCED_STATS,
                Permission.ACCESS_MARKET_DATA, Permission.VIEW_CONTRACT_INFO, Permission.GENERATE_REPORTS,
                Permission.EXPORT_REPORTS, Permission.MANAGE_USERS, Permission.CONFIGURE_ALERTS,
                Permission.API_ACCESS, Permission.BULK_OPERATIONS
            ],
            
            UserRole.SCOUT_MANAGER: [
                Permission.CREATE_SHORTLIST, Permission.EDIT_SHORTLIST, Permission.VIEW_SHORTLIST,
                Permission.VIEW_PLAYER_DETAILS, Permission.VIEW_ADVANCED_STATS, Permission.ACCESS_MARKET_DATA,
                Permission.VIEW_CONTRACT_INFO, Permission.GENERATE_REPORTS, Permission.EXPORT_REPORTS,
                Permission.CONFIGURE_ALERTS, Permission.API_ACCESS
            ],
            
            UserRole.SCOUT: [
                Permission.CREATE_SHORTLIST, Permission.EDIT_SHORTLIST, Permission.VIEW_SHORTLIST,
                Permission.VIEW_PLAYER_DETAILS, Permission.VIEW_ADVANCED_STATS, Permission.ACCESS_MARKET_DATA,
                Permission.GENERATE_REPORTS, Permission.API_ACCESS
            ],
            
            UserRole.ANALYST: [
                Permission.VIEW_SHORTLIST, Permission.VIEW_PLAYER_DETAILS, Permission.VIEW_ADVANCED_STATS,
                Permission.ACCESS_MARKET_DATA, Permission.GENERATE_REPORTS
            ],
            
            UserRole.VIEWER: [
                Permission.VIEW_SHORTLIST, Permission.VIEW_PLAYER_DETAILS
            ]
        }
        
        # Subscription features
        self.subscription_features = {
            'basic': [
                'player_search', 'basic_stats', 'shortlists', 'basic_reports'
            ],
            'professional': [
                'player_search', 'basic_stats', 'advanced_stats', 'shortlists', 
                'detailed_reports', 'market_analysis', 'alerts', 'api_access'
            ],
            'enterprise': [
                'player_search', 'basic_stats', 'advanced_stats', 'shortlists',
                'detailed_reports', 'market_analysis', 'alerts', 'api_access',
                'custom_integrations', 'priority_support', 'advanced_ai'
            ]
        }
        
        # Mock databases (em produção seria banco de dados real)
        self.users: Dict[str, User] = {}
        self.clubs: Dict[str, Club] = {}
        self.sessions: Dict[str, Dict] = {}
    
    def create_club(
        self,
        name: str,
        country: str,
        tier: int,
        subscription_plan: str = 'basic'
    ) -> Club:
        """Criar novo clube"""
        
        club_id = secrets.token_urlsafe(16)
        
        club = Club(
            id=club_id,
            name=name,
            country=country,
            tier=tier,
            subscription_plan=subscription_plan,
            max_users=self._get_max_users_for_plan(subscription_plan),
            features=self.subscription_features[subscription_plan],
            created_at=datetime.now()
        )
        
        self.clubs[club_id] = club
        logger.info(f"Clube criado: {name} ({club_id})")
        
        return club
    
    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        club_id: str,
        role: UserRole
    ) -> Optional[User]:
        """Criar novo usuário"""
        
        # Verificar se clube existe
        if club_id not in self.clubs:
            raise ValueError("Clube não encontrado")
        
        club = self.clubs[club_id]
        
        # Verificar limite de usuários
        club_users = [u for u in self.users.values() if u.club_id == club_id and u.is_active]
        if len(club_users) >= club.max_users:
            raise ValueError("Limite de usuários atingido para este plano")
        
        # Verificar se email já existe
        if any(u.email == email for u in self.users.values()):
            raise ValueError("Email já cadastrado")
        
        user_id = secrets.token_urlsafe(16)
        hashed_password = self._hash_password(password)
        
        user = User(
            id=user_id,
            email=email,
            name=name,
            club_id=club_id,
            role=role,
            permissions=self.role_permissions[role],
            created_at=datetime.now(),
            preferences={}
        )
        
        self.users[user_id] = user
        
        # Salvar senha hasheada separadamente (em produção seria no DB)
        self.sessions[f"pwd_{user_id}"] = {'password': hashed_password}
        
        logger.info(f"Usuário criado: {email} para clube {club_id}")
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Autenticar usuário e retornar token JWT"""
        
        # Encontrar usuário pelo email
        user = None
        for u in self.users.values():
            if u.email == email and u.is_active:
                user = u
                break
        
        if not user:
            return None
        
        # Verificar senha
        stored_password = self.sessions.get(f"pwd_{user.id}", {}).get('password')
        if not stored_password or not self._verify_password(password, stored_password):
            return None
        
        # Verificar se clube está ativo
        club = self.clubs.get(user.club_id)
        if not club or not club.is_active:
            return None
        
        # Gerar token JWT
        token_payload = {
            'user_id': user.id,
            'email': user.email,
            'club_id': user.club_id,
            'role': user.role.value,
            'permissions': [p.value for p in user.permissions],
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(token_payload, self.secret_key, algorithm='HS256')
        
        # Atualizar último login
        user.last_login = datetime.now()
        
        logger.info(f"Usuário autenticado: {email}")
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verificar e decodificar token JWT"""
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Verificar se usuário ainda existe e está ativo
            user = self.users.get(payload['user_id'])
            if not user or not user.is_active:
                return None
            
            # Verificar se clube ainda está ativo
            club = self.clubs.get(user.club_id)
            if not club or not club.is_active:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token inválido")
            return None
    
    def check_permission(self, user_token: Dict, required_permission: Permission) -> bool:
        """Verificar se usuário tem permissão específica"""
        
        user_permissions = [Permission(p) for p in user_token.get('permissions', [])]
        return required_permission in user_permissions
    
    def check_feature_access(self, club_id: str, feature: str) -> bool:
        """Verificar se clube tem acesso a uma funcionalidade"""
        
        club = self.clubs.get(club_id)
        if not club:
            return False
        
        return feature in club.features
    
    def get_user_context(self, token: str) -> Optional[Dict]:
        """Obter contexto completo do usuário"""
        
        token_data = self.verify_token(token)
        if not token_data:
            return None
        
        user = self.users.get(token_data['user_id'])
        club = self.clubs.get(token_data['club_id'])
        
        if not user or not club:
            return None
        
        return {
            'user': asdict(user),
            'club': asdict(club),
            'permissions': [p.value for p in user.permissions],
            'features': club.features,
            'subscription_plan': club.subscription_plan
        }
    
    def get_club_users(self, club_id: str, requester_token: Dict) -> List[User]:
        """Listar usuários do clube (apenas para roles autorizadas)"""
        
        # Verificar se usuário pode gerenciar usuários
        if not self.check_permission(requester_token, Permission.MANAGE_USERS):
            raise PermissionError("Sem permissão para listar usuários")
        
        # Verificar se é do mesmo clube
        if requester_token['club_id'] != club_id:
            raise PermissionError("Acesso negado para este clube")
        
        club_users = [u for u in self.users.values() if u.club_id == club_id]
        return club_users
    
    def update_user_role(
        self,
        target_user_id: str,
        new_role: UserRole,
        requester_token: Dict
    ) -> bool:
        """Atualizar role de usuário"""
        
        # Verificar permissão
        if not self.check_permission(requester_token, Permission.MANAGE_USERS):
            raise PermissionError("Sem permissão para alterar usuários")
        
        target_user = self.users.get(target_user_id)
        if not target_user:
            return False
        
        # Verificar se é do mesmo clube
        if target_user.club_id != requester_token['club_id']:
            raise PermissionError("Usuário não pertence ao mesmo clube")
        
        # Atualizar role e permissões
        target_user.role = new_role
        target_user.permissions = self.role_permissions[new_role]
        
        logger.info(f"Role atualizada para usuário {target_user_id}: {new_role.value}")
        
        return True
    
    def deactivate_user(self, user_id: str, requester_token: Dict) -> bool:
        """Desativar usuário"""
        
        if not self.check_permission(requester_token, Permission.MANAGE_USERS):
            raise PermissionError("Sem permissão para desativar usuários")
        
        user = self.users.get(user_id)
        if not user or user.club_id != requester_token['club_id']:
            return False
        
        user.is_active = False
        logger.info(f"Usuário desativado: {user_id}")
        
        return True
    
    def upgrade_subscription(self, club_id: str, new_plan: str) -> bool:
        """Atualizar plano de assinatura"""
        
        if new_plan not in self.subscription_features:
            return False
        
        club = self.clubs.get(club_id)
        if not club:
            return False
        
        club.subscription_plan = new_plan
        club.features = self.subscription_features[new_plan]
        club.max_users = self._get_max_users_for_plan(new_plan)
        
        logger.info(f"Plano atualizado para clube {club_id}: {new_plan}")
        
        return True
    
    def audit_log(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Dict = None
    ) -> None:
        """Registrar ação para auditoria"""
        
        # Em produção, salvaria no banco de dados
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details or {}
        }
        
        logger.info(f"Audit: {audit_entry}")
    
    def get_subscription_limits(self, club_id: str) -> Dict:
        """Obter limites da assinatura"""
        
        club = self.clubs.get(club_id)
        if not club:
            return {}
        
        plan_limits = {
            'basic': {
                'max_shortlists': 5,
                'max_players_per_shortlist': 25,
                'api_calls_per_day': 100,
                'reports_per_month': 10
            },
            'professional': {
                'max_shortlists': 20,
                'max_players_per_shortlist': 50,
                'api_calls_per_day': 1000,
                'reports_per_month': 50
            },
            'enterprise': {
                'max_shortlists': -1,  # Ilimitado
                'max_players_per_shortlist': 100,
                'api_calls_per_day': 5000,
                'reports_per_month': -1  # Ilimitado
            }
        }
        
        return plan_limits.get(club.subscription_plan, plan_limits['basic'])
    
    # Métodos privados
    def _hash_password(self, password: str) -> str:
        """Hash da senha usando bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verificar senha"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _get_max_users_for_plan(self, plan: str) -> int:
        """Obter limite de usuários por plano"""
        limits = {
            'basic': 3,
            'professional': 10,
            'enterprise': 25
        }
        return limits.get(plan, 3)
    
    def create_api_key(self, user_id: str, name: str) -> str:
        """Criar API key para usuário"""
        
        user = self.users.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Gerar API key
        api_key = f"sks_{secrets.token_urlsafe(32)}"
        
        # Salvar metadados da API key
        self.sessions[f"api_{api_key}"] = {
            'user_id': user_id,
            'club_id': user.club_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        logger.info(f"API key criada para usuário {user_id}: {name}")
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict]:
        """Verificar API key"""
        
        key_data = self.sessions.get(f"api_{api_key}")
        if not key_data or not key_data.get('is_active'):
            return None
        
        user = self.users.get(key_data['user_id'])
        club = self.clubs.get(key_data['club_id'])
        
        if not user or not user.is_active or not club or not club.is_active:
            return None
        
        return {
            'user_id': user.id,
            'club_id': user.club_id,
            'role': user.role.value,
            'permissions': [p.value for p in user.permissions]
        }

# Instância global do serviço multi-tenant
multi_tenant_service = MultiTenantService()

# Criar dados de exemplo
def setup_demo_data():
    """Criar dados de demonstração"""
    try:
        # Criar clube de exemplo
        demo_club = multi_tenant_service.create_club(
            name="Demo Football Club",
            country="Brazil", 
            tier=1,
            subscription_plan="professional"
        )
        
        # Criar usuário administrador
        admin_user = multi_tenant_service.create_user(
            email="admin@demo.com",
            password="admin123",
            name="Admin Demo",
            club_id=demo_club.id,
            role=UserRole.DIRECTOR
        )
        
        # Criar scout
        scout_user = multi_tenant_service.create_user(
            email="scout@demo.com", 
            password="scout123",
            name="Scout Demo",
            club_id=demo_club.id,
            role=UserRole.SCOUT
        )
        
        logger.info("Dados de demonstração criados")
        logger.info(f"Clube: {demo_club.id}")
        logger.info(f"Admin: admin@demo.com / admin123")
        logger.info(f"Scout: scout@demo.com / scout123")
        
    except Exception as e:
        logger.error(f"Erro ao criar dados demo: {e}")

# Executar setup de demonstração
setup_demo_data()