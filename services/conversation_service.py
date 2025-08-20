"""
💬 Soccer Scout AI - Serviço de Persistência de Conversas
Sistema para persistir conversas do assistente IA no banco de dados
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from database.models import get_db
import uuid

Base = declarative_base()

class Conversation(Base):
    """Modelo de conversa persistida"""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    club_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String)
    context_data = Column(Text)  # JSON com contexto da conversa
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)

class ConversationMessage(Base):
    """Mensagens individuais da conversa"""
    __tablename__ = "conversation_messages"
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey('conversations.id'))
    role = Column(String)  # 'user' ou 'assistant'
    content = Column(Text)
    query_type = Column(String)  # tactical_analysis, market_analysis, etc.
    metadata = Column(Text)  # JSON com metadados
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", backref="messages")

class ConversationService:
    """Serviço de gerenciamento de conversas"""
    
    def __init__(self):
        self.max_messages_per_conversation = 100
        self.conversation_timeout_days = 30
    
    def create_conversation(self, club_id: str, user_id: str, initial_query: str) -> str:
        """Criar nova conversa"""
        
        conversation_id = str(uuid.uuid4())
        
        # Gerar título baseado na query inicial
        title = self._generate_conversation_title(initial_query)
        
        db = next(get_db())
        
        conversation = Conversation(
            id=conversation_id,
            club_id=club_id,
            user_id=user_id,
            title=title,
            context_data=json.dumps({
                'initial_query': initial_query,
                'query_count': 1,
                'topics': []
            })
        )
        
        db.add(conversation)
        db.commit()
        
        return conversation_id
    
    def add_message(
        self, 
        conversation_id: str,
        role: str,
        content: str,
        query_type: str = None,
        metadata: Dict = None
    ) -> str:
        """Adicionar mensagem à conversa"""
        
        message_id = str(uuid.uuid4())
        
        db = next(get_db())
        
        # Verificar se conversa existe
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError("Conversa não encontrada")
        
        # Criar mensagem
        message = ConversationMessage(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            query_type=query_type,
            metadata=json.dumps(metadata or {}),
            timestamp=datetime.utcnow()
        )
        
        db.add(message)
        
        # Atualizar contexto da conversa
        context = json.loads(conversation.context_data or '{}')
        context['query_count'] = context.get('query_count', 0) + 1
        context['last_query_type'] = query_type
        
        # Adicionar tópico se for novo
        if query_type and query_type not in context.get('topics', []):
            context.setdefault('topics', []).append(query_type)
        
        conversation.context_data = json.dumps(context)
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Limpar mensagens antigas se necessário
        self._cleanup_old_messages(conversation_id, db)
        
        return message_id
    
    def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """Obter histórico completo de uma conversa"""
        
        db = next(get_db())
        
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return None
        
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.timestamp.desc()).limit(limit).all()
        
        return {
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'context': json.loads(conversation.context_data or '{}'),
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat()
            },
            'messages': [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'query_type': msg.query_type,
                    'metadata': json.loads(msg.metadata or '{}'),
                    'timestamp': msg.timestamp.isoformat()
                }
                for msg in reversed(messages)  # Mais antigas primeiro
            ]
        }
    
    def get_user_conversations(
        self, 
        club_id: str, 
        user_id: str, 
        limit: int = 20
    ) -> List[Dict]:
        """Listar conversas do usuário"""
        
        db = next(get_db())
        
        conversations = db.query(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.user_id == user_id,
            Conversation.is_active == 1
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()
        
        result = []
        for conv in conversations:
            context = json.loads(conv.context_data or '{}')
            
            # Buscar última mensagem
            last_message = db.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == conv.id
            ).order_by(ConversationMessage.timestamp.desc()).first()
            
            result.append({
                'id': conv.id,
                'title': conv.title,
                'query_count': context.get('query_count', 0),
                'topics': context.get('topics', []),
                'last_message': last_message.content[:100] + '...' if last_message and len(last_message.content) > 100 else last_message.content if last_message else '',
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat()
            })
        
        return result
    
    def restore_conversation_context(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Restaurar contexto de conversa para o assistente IA"""
        
        history = self.get_conversation_history(conversation_id, limit)
        if not history:
            return []
        
        # Formatar mensagens para o assistente IA
        context_messages = []
        for message in history['messages'][-limit:]:  # Últimas N mensagens
            context_messages.append({
                'role': message['role'],
                'content': message['content'],
                'timestamp': message['timestamp'],
                'query_type': message['query_type']
            })
        
        return context_messages
    
    def search_conversations(
        self, 
        club_id: str, 
        query: str, 
        user_id: str = None
    ) -> List[Dict]:
        """Buscar conversas por conteúdo"""
        
        db = next(get_db())
        
        # Buscar em títulos e mensagens
        conversations_query = db.query(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.is_active == 1
        )
        
        if user_id:
            conversations_query = conversations_query.filter(
                Conversation.user_id == user_id
            )
        
        # Buscar por título
        title_matches = conversations_query.filter(
            Conversation.title.ilike(f'%{query}%')
        ).all()
        
        # Buscar por conteúdo de mensagens
        message_matches = db.query(ConversationMessage).join(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.is_active == 1,
            ConversationMessage.content.ilike(f'%{query}%')
        )
        
        if user_id:
            message_matches = message_matches.filter(
                Conversation.user_id == user_id
            )
        
        message_matches = message_matches.all()
        
        # Combinar resultados
        found_conversations = {}
        
        # Adicionar matches de título
        for conv in title_matches:
            found_conversations[conv.id] = {
                'conversation': conv,
                'match_type': 'title',
                'match_content': conv.title
            }
        
        # Adicionar matches de mensagens
        for msg in message_matches:
            if msg.conversation_id not in found_conversations:
                found_conversations[msg.conversation_id] = {
                    'conversation': msg.conversation,
                    'match_type': 'message',
                    'match_content': msg.content[:200] + '...' if len(msg.content) > 200 else msg.content
                }
        
        # Formatar resultado
        results = []
        for conv_data in found_conversations.values():
            conv = conv_data['conversation']
            context = json.loads(conv.context_data or '{}')
            
            results.append({
                'id': conv.id,
                'title': conv.title,
                'match_type': conv_data['match_type'],
                'match_content': conv_data['match_content'],
                'query_count': context.get('query_count', 0),
                'topics': context.get('topics', []),
                'updated_at': conv.updated_at.isoformat()
            })
        
        # Ordenar por data de atualização
        results.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return results
    
    def delete_conversation(self, conversation_id: str, user_id: str = None) -> bool:
        """Deletar conversa (soft delete)"""
        
        db = next(get_db())
        
        query = db.query(Conversation).filter(
            Conversation.id == conversation_id
        )
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        conversation = query.first()
        
        if not conversation:
            return False
        
        conversation.is_active = 0
        db.commit()
        
        return True
    
    def get_conversation_analytics(self, club_id: str) -> Dict[str, Any]:
        """Obter analytics de conversas do clube"""
        
        db = next(get_db())
        
        # Total de conversas
        total_conversations = db.query(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.is_active == 1
        ).count()
        
        # Total de mensagens
        total_messages = db.query(ConversationMessage).join(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.is_active == 1
        ).count()
        
        # Conversas por usuário
        user_conversations = {}
        conversations = db.query(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.is_active == 1
        ).all()
        
        for conv in conversations:
            user_id = conv.user_id
            user_conversations[user_id] = user_conversations.get(user_id, 0) + 1
        
        # Tipos de query mais comuns
        query_types = {}
        messages = db.query(ConversationMessage).join(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.is_active == 1,
            ConversationMessage.query_type.isnot(None)
        ).all()
        
        for msg in messages:
            query_type = msg.query_type
            query_types[query_type] = query_types.get(query_type, 0) + 1
        
        # Conversas ativas (última semana)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_conversations = db.query(Conversation).filter(
            Conversation.club_id == club_id,
            Conversation.is_active == 1,
            Conversation.updated_at >= week_ago
        ).count()
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'active_conversations_week': active_conversations,
            'avg_messages_per_conversation': total_messages / max(total_conversations, 1),
            'conversations_by_user': user_conversations,
            'popular_query_types': dict(sorted(query_types.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _generate_conversation_title(self, initial_query: str) -> str:
        """Gerar título baseado na query inicial"""
        
        # Títulos baseados em palavras-chave
        query_lower = initial_query.lower()
        
        if any(word in query_lower for word in ['centroavante', 'atacante', 'striker']):
            return "Busca por Centroavante"
        elif any(word in query_lower for word in ['zagueiro', 'defensor', 'centre-back']):
            return "Busca por Zagueiro"
        elif any(word in query_lower for word in ['meia', 'midfielder']):
            return "Busca por Meio-campista"
        elif any(word in query_lower for word in ['lateral', 'full-back']):
            return "Busca por Lateral"
        elif any(word in query_lower for word in ['goleiro', 'goalkeeper']):
            return "Busca por Goleiro"
        elif any(word in query_lower for word in ['compare', 'comparar']):
            return "Comparação de Jogadores"
        elif any(word in query_lower for word in ['tático', 'tactical', 'formação']):
            return "Análise Tática"
        elif any(word in query_lower for word in ['mercado', 'market', 'oportunidade']):
            return "Análise de Mercado"
        elif any(word in query_lower for word in ['relatório', 'report', 'scout']):
            return "Relatório de Scouting"
        else:
            # Usar as primeiras palavras da query
            words = initial_query.split()[:4]
            return ' '.join(words) + ('...' if len(initial_query.split()) > 4 else '')
    
    def _cleanup_old_messages(self, conversation_id: str, db) -> None:
        """Limpar mensagens antigas para manter performance"""
        
        message_count = db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).count()
        
        if message_count > self.max_messages_per_conversation:
            # Manter apenas as mensagens mais recentes
            old_messages = db.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == conversation_id
            ).order_by(ConversationMessage.timestamp.asc()).limit(
                message_count - self.max_messages_per_conversation
            ).all()
            
            for msg in old_messages:
                db.delete(msg)
            
            db.commit()
    
    def cleanup_expired_conversations(self) -> int:
        """Limpar conversas expiradas"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.conversation_timeout_days)
        
        db = next(get_db())
        
        expired_conversations = db.query(Conversation).filter(
            Conversation.updated_at < cutoff_date,
            Conversation.is_active == 1
        ).all()
        
        for conv in expired_conversations:
            conv.is_active = 0
        
        db.commit()
        
        return len(expired_conversations)

# Instância global do serviço
conversation_service = ConversationService()