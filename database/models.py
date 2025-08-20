from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    
    # Identificação básica
    id = Column(Integer, primary_key=True, index=True)
    sportmonks_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    full_name = Column(String)
    position = Column(String, index=True)
    secondary_position = Column(String)
    
    # Dados pessoais
    age = Column(Integer, index=True)
    birth_date = Column(Date)
    nationality = Column(String, index=True)
    second_nationality = Column(String)
    
    # Dados físicos
    height = Column(Integer)  # Em cm
    weight = Column(Integer)  # Em kg
    preferred_foot = Column(String, index=True)
    
    # Dados contratuais e financeiros
    current_team = Column(String, index=True)
    contract_end_date = Column(Date, index=True)
    market_value = Column(Float, index=True)  # Em milhões
    salary_annual = Column(Float)  # Em milhões/ano
    release_clause = Column(Float)  # Em milhões
    agent_name = Column(String)
    loan_player = Column(Boolean, default=False)
    free_agent = Column(Boolean, default=False, index=True)
    
    # Liga e competições
    league = Column(String, index=True)
    team_country = Column(String)
    champions_league = Column(Boolean, default=False)
    europa_league = Column(Boolean, default=False)
    
    # Estatísticas da temporada atual
    appearances_season = Column(Integer, default=0)
    minutes_played = Column(Integer, default=0)
    goals_season = Column(Integer, default=0, index=True)
    assists_season = Column(Integer, default=0, index=True)
    
    # Estatísticas ofensivas
    shots_per_game = Column(Float, default=0)
    shots_on_target_per_game = Column(Float, default=0)
    conversion_rate = Column(Float, default=0)
    dribbles_per_game = Column(Float, default=0)
    dribble_success_rate = Column(Float, default=0)
    
    # Estatísticas de passe
    passes_per_game = Column(Float, default=0)
    pass_accuracy = Column(Float, default=0)
    key_passes_per_game = Column(Float, default=0)
    crosses_per_game = Column(Float, default=0)
    cross_accuracy = Column(Float, default=0)
    
    # Estatísticas defensivas
    tackles_per_game = Column(Float, default=0)
    tackle_success_rate = Column(Float, default=0)
    interceptions_per_game = Column(Float, default=0)
    clearances_per_game = Column(Float, default=0)
    duels_won_per_game = Column(Float, default=0)
    duel_success_rate = Column(Float, default=0)
    
    # Jogo aéreo
    aerial_duels_per_game = Column(Float, default=0)
    aerial_duel_success_rate = Column(Float, default=0)
    headers_scored = Column(Integer, default=0)
    
    # Disciplina
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    fouls_per_game = Column(Float, default=0)
    fouls_suffered_per_game = Column(Float, default=0)
    
    # Para goleiros
    saves_per_game = Column(Float, default=0)
    save_percentage = Column(Float, default=0)
    clean_sheets = Column(Integer, default=0)
    goals_conceded = Column(Integer, default=0)
    
    # Experiência internacional
    international_caps = Column(Integer, default=0)
    international_goals = Column(Integer, default=0)
    
    # Histórico de lesões (simplificado)
    injury_prone = Column(Boolean, default=False)
    days_injured_season = Column(Integer, default=0)
    
    # Potencial e valorização
    potential_rating = Column(Float)  # 1-10
    market_trend = Column(String)  # 'rising', 'stable', 'declining'
    
    # Performance ratings
    overall_rating = Column(Float, default=0)  # 1-10
    pace = Column(Float, default=0)
    shooting = Column(Float, default=0)
    passing = Column(Float, default=0)
    dribbling = Column(Float, default=0)
    defending = Column(Float, default=0)
    physical = Column(Float, default=0)
    
    # Características especiais
    weak_foot_rating = Column(Integer, default=1)  # 1-5
    skill_moves = Column(Integer, default=1)  # 1-5
    work_rate_attack = Column(String)  # Low, Medium, High
    work_rate_defense = Column(String)  # Low, Medium, High
    
    # Meta informações
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_transfer_value = Column(Float)
    last_transfer_date = Column(Date)

class League(Base):
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True, index=True)
    sportmonks_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    country = Column(String)
    tier = Column(Integer)  # 1 = primeira divisão, 2 = segunda, etc.
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

class SearchCache(Base):
    __tablename__ = "search_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String, unique=True, index=True)
    query_text = Column(Text)
    results = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# Configurar banco de dados
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicializar banco de dados"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()