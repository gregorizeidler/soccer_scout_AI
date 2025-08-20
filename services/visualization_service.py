"""
📈 Soccer Scout AI - Serviço de Visualizações
Sistema para gerar heatmaps, shot maps, gráficos radar e outras visualizações
"""

import matplotlib
matplotlib.use('Agg')  # Backend não-interativo
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import io
import base64
from datetime import datetime
import json
import os
from pathlib import Path

class VisualizationService:
    """Serviço de geração de visualizações para dados de futebol"""
    
    def __init__(self):
        # Configurar estilo
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
        # Diretório para salvar visualizações
        self.viz_dir = Path("static/visualizations")
        self.viz_dir.mkdir(parents=True, exist_ok=True)
        
        # Cores padrão
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'accent': '#F18F01',
            'success': '#C73E1D',
            'field_green': '#4CAF50',
            'field_lines': '#FFFFFF'
        }
    
    def generate_player_radar(
        self, 
        player_data: Dict[str, Any], 
        comparison_player: Dict[str, Any] = None
    ) -> str:
        """Gerar gráfico radar de atributos do jogador"""
        
        # Atributos para o radar
        attributes = ['Pace', 'Shooting', 'Passing', 'Dribbling', 'Defending', 'Physical']
        
        # Valores do jogador principal
        player_values = [
            player_data.get('pace', 6),
            player_data.get('shooting', 6), 
            player_data.get('passing', 6),
            player_data.get('dribbling', 6),
            player_data.get('defending', 6),
            player_data.get('physical', 6)
        ]
        
        # Configurar o gráfico
        angles = np.linspace(0, 2 * np.pi, len(attributes), endpoint=False).tolist()
        angles += angles[:1]  # Fechar o círculo
        player_values += player_values[:1]
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Plotar jogador principal
        ax.plot(angles, player_values, 'o-', linewidth=2, label=player_data.get('name', 'Player 1'), color=self.colors['primary'])
        ax.fill(angles, player_values, alpha=0.25, color=self.colors['primary'])
        
        # Plotar jogador de comparação se fornecido
        if comparison_player:
            comparison_values = [
                comparison_player.get('pace', 6),
                comparison_player.get('shooting', 6),
                comparison_player.get('passing', 6),
                comparison_player.get('dribbling', 6),
                comparison_player.get('defending', 6),
                comparison_player.get('physical', 6)
            ]
            comparison_values += comparison_values[:1]
            
            ax.plot(angles, comparison_values, 'o-', linewidth=2, label=comparison_player.get('name', 'Player 2'), color=self.colors['secondary'])
            ax.fill(angles, comparison_values, alpha=0.25, color=self.colors['secondary'])
        
        # Configurar labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(attributes, fontsize=12)
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=10)
        ax.grid(True)
        
        # Título e legenda
        title = f"Radar Chart: {player_data.get('name', 'Player')}"
        if comparison_player:
            title += f" vs {comparison_player.get('name', 'Player 2')}"
        
        plt.title(title, size=16, fontweight='bold', pad=20)
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        # Salvar e retornar
        filename = f"radar_{player_data.get('id', 'unknown')}_{int(datetime.now().timestamp())}.png"
        filepath = self.viz_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"/static/visualizations/{filename}"
    
    def generate_performance_trend(self, player_stats: List[Dict]) -> str:
        """Gerar gráfico de tendência de performance"""
        
        if not player_stats:
            return None
        
        # Preparar dados
        dates = [stat.get('date', datetime.now()) for stat in player_stats]
        goals = [stat.get('goals', 0) for stat in player_stats]
        assists = [stat.get('assists', 0) for stat in player_stats]
        ratings = [stat.get('rating', 6.0) for stat in player_stats]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Gráfico 1: Gols e Assistências
        ax1.plot(dates, goals, marker='o', label='Goals', color=self.colors['primary'], linewidth=2)
        ax1.plot(dates, assists, marker='s', label='Assists', color=self.colors['secondary'], linewidth=2)
        ax1.set_ylabel('Goals / Assists', fontsize=12)
        ax1.set_title('Performance Trend - Goals & Assists', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Rating médio
        ax2.plot(dates, ratings, marker='D', label='Rating', color=self.colors['accent'], linewidth=2)
        ax2.set_ylabel('Average Rating', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_title('Performance Trend - Match Ratings', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 10)
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar e retornar
        filename = f"trend_{int(datetime.now().timestamp())}.png"
        filepath = self.viz_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"/static/visualizations/{filename}"
    
    def generate_position_heatmap(self, position_data: Dict[str, float]) -> str:
        """Gerar heatmap de posições do jogador no campo"""
        
        # Criar campo de futebol
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Dimensões do campo (simplificado)
        field_length = 105
        field_width = 68
        
        # Desenhar campo
        ax.set_xlim(0, field_length)
        ax.set_ylim(0, field_width)
        ax.set_aspect('equal')
        ax.set_facecolor(self.colors['field_green'])
        
        # Linhas do campo
        # Linha lateral
        ax.plot([0, field_length], [0, 0], color=self.colors['field_lines'], linewidth=2)
        ax.plot([0, field_length], [field_width, field_width], color=self.colors['field_lines'], linewidth=2)
        ax.plot([0, 0], [0, field_width], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length, field_length], [0, field_width], color=self.colors['field_lines'], linewidth=2)
        
        # Linha central
        ax.plot([field_length/2, field_length/2], [0, field_width], color=self.colors['field_lines'], linewidth=2)
        
        # Círculo central
        circle = plt.Circle((field_length/2, field_width/2), 9.15, fill=False, color=self.colors['field_lines'], linewidth=2)
        ax.add_patch(circle)
        
        # Áreas
        # Área esquerda
        ax.plot([0, 16.5], [13.84, 13.84], color=self.colors['field_lines'], linewidth=2)
        ax.plot([0, 16.5], [54.16, 54.16], color=self.colors['field_lines'], linewidth=2)
        ax.plot([16.5, 16.5], [13.84, 54.16], color=self.colors['field_lines'], linewidth=2)
        
        # Área direita  
        ax.plot([field_length, field_length-16.5], [13.84, 13.84], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length, field_length-16.5], [54.16, 54.16], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length-16.5, field_length-16.5], [13.84, 54.16], color=self.colors['field_lines'], linewidth=2)
        
        # Gerar dados de heatmap baseado nas zonas
        x = np.linspace(5, field_length-5, 10)
        y = np.linspace(5, field_width-5, 7)
        X, Y = np.meshgrid(x, y)
        
        # Intensidade baseada nas zonas de ação
        zones = np.zeros((7, 10))
        
        # Mapear position_data para zonas
        zones[3, 2] = position_data.get('defensive_third', 20)  # Defesa
        zones[3, 5] = position_data.get('middle_third', 40)     # Meio
        zones[3, 8] = position_data.get('attacking_third', 30)  # Ataque
        zones[1, 5] = position_data.get('left_flank', 25)       # Esquerda
        zones[5, 5] = position_data.get('right_flank', 25)      # Direita
        zones[3, 9] = position_data.get('penalty_area', 15)     # Área
        
        # Aplicar blur para suavizar
        from scipy.ndimage import gaussian_filter
        zones = gaussian_filter(zones, sigma=0.8)
        
        # Plotar heatmap
        im = ax.contourf(X, Y, zones, levels=20, alpha=0.6, cmap='Reds')
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.6)
        cbar.set_label('Activity Intensity', rotation=270, labelpad=15)
        
        # Títulos
        ax.set_title('Player Position Heatmap', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Salvar e retornar
        filename = f"heatmap_{int(datetime.now().timestamp())}.png"
        filepath = self.viz_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"/static/visualizations/{filename}"
    
    def generate_shot_map(self, shot_data: List[Dict]) -> str:
        """Gerar mapa de finalizações"""
        
        if not shot_data:
            return None
        
        # Criar campo
        fig, ax = plt.subplots(figsize=(12, 8))
        
        field_length = 105
        field_width = 68
        
        # Focar na metade ofensiva
        ax.set_xlim(52.5, field_length)
        ax.set_ylim(0, field_width)
        ax.set_aspect('equal')
        ax.set_facecolor(self.colors['field_green'])
        
        # Desenhar metade ofensiva do campo
        # Linhas
        ax.plot([52.5, field_length], [0, 0], color=self.colors['field_lines'], linewidth=2)
        ax.plot([52.5, field_length], [field_width, field_width], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length, field_length], [0, field_width], color=self.colors['field_lines'], linewidth=2)
        ax.plot([52.5, 52.5], [0, field_width], color=self.colors['field_lines'], linewidth=2)
        
        # Área
        ax.plot([field_length, field_length-16.5], [13.84, 13.84], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length, field_length-16.5], [54.16, 54.16], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length-16.5, field_length-16.5], [13.84, 54.16], color=self.colors['field_lines'], linewidth=2)
        
        # Área pequena
        ax.plot([field_length, field_length-5.5], [24.84, 24.84], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length, field_length-5.5], [43.16, 43.16], color=self.colors['field_lines'], linewidth=2)
        ax.plot([field_length-5.5, field_length-5.5], [24.84, 43.16], color=self.colors['field_lines'], linewidth=2)
        
        # Gol
        ax.plot([field_length, field_length], [30.34, 37.66], color=self.colors['field_lines'], linewidth=4)
        
        # Plotar chutes
        for shot in shot_data:
            x = shot.get('x', 80)
            y = shot.get('y', 34)
            outcome = shot.get('outcome', 'miss')  # goal, save, miss, block
            
            if outcome == 'goal':
                ax.scatter(x, y, c='red', s=100, marker='o', alpha=0.8, edgecolors='darkred', linewidth=2)
            elif outcome == 'save':
                ax.scatter(x, y, c='orange', s=80, marker='s', alpha=0.7, edgecolors='darkorange')
            elif outcome == 'block':
                ax.scatter(x, y, c='blue', s=60, marker='^', alpha=0.6, edgecolors='darkblue')
            else:  # miss
                ax.scatter(x, y, c='gray', s=40, marker='x', alpha=0.5)
        
        # Legenda
        goal_marker = plt.scatter([], [], c='red', s=100, marker='o', alpha=0.8, edgecolors='darkred', linewidth=2)
        save_marker = plt.scatter([], [], c='orange', s=80, marker='s', alpha=0.7, edgecolors='darkorange')
        block_marker = plt.scatter([], [], c='blue', s=60, marker='^', alpha=0.6, edgecolors='darkblue')
        miss_marker = plt.scatter([], [], c='gray', s=40, marker='x', alpha=0.5)
        
        ax.legend([goal_marker, save_marker, block_marker, miss_marker], 
                 ['Goal', 'Saved', 'Blocked', 'Missed'], 
                 loc='upper left')
        
        ax.set_title('Shot Map', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Salvar e retornar
        filename = f"shotmap_{int(datetime.now().timestamp())}.png"
        filepath = self.viz_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"/static/visualizations/{filename}"
    
    def generate_market_comparison_chart(self, players: List[Dict]) -> str:
        """Gerar gráfico de comparação de mercado (valor vs qualidade)"""
        
        if len(players) < 2:
            return None
        
        # Extrair dados
        names = [p.get('name', f'Player {i}') for i, p in enumerate(players)]
        market_values = [p.get('market_value', 0) for p in players]
        ratings = [p.get('overall_rating', 6) for p in players]
        ages = [p.get('age', 25) for p in players]
        
        # Criar scatter plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Bubble chart (tamanho = idade)
        sizes = [(30 - age) * 20 for age in ages]  # Jogadores mais novos = bolhas maiores
        
        scatter = ax.scatter(ratings, market_values, s=sizes, alpha=0.6, 
                           c=range(len(players)), cmap='viridis', edgecolors='black', linewidth=1)
        
        # Adicionar nomes
        for i, name in enumerate(names):
            ax.annotate(name, (ratings[i], market_values[i]), 
                       xytext=(5, 5), textcoords='offset points', 
                       fontsize=10, fontweight='bold')
        
        # Configurar gráfico
        ax.set_xlabel('Overall Rating', fontsize=12, fontweight='bold')
        ax.set_ylabel('Market Value (€M)', fontsize=12, fontweight='bold')
        ax.set_title('Market Value vs Quality Comparison', fontsize=16, fontweight='bold', pad=20)
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        # Linha de valor ideal (simplificado)
        x_line = np.linspace(min(ratings), max(ratings), 100)
        y_line = (x_line - 5) ** 2 * 2  # Valor cresce exponencialmente com rating
        ax.plot(x_line, y_line, '--', alpha=0.5, color='red', label='Expected Value Line')
        
        ax.legend()
        
        # Colorbar para idades
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Player Index', rotation=270, labelpad=15)
        
        # Salvar e retornar
        filename = f"market_comparison_{int(datetime.now().timestamp())}.png"
        filepath = self.viz_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"/static/visualizations/{filename}"
    
    def generate_stats_comparison_bars(self, players: List[Dict], stats: List[str]) -> str:
        """Gerar gráfico de barras comparativo de estatísticas"""
        
        if not players or not stats:
            return None
        
        # Preparar dados
        player_names = [p.get('name', f'Player {i}')[:15] for i, p in enumerate(players)]
        
        # Criar subplot para cada estatística
        n_stats = len(stats)
        fig, axes = plt.subplots(n_stats, 1, figsize=(12, 4*n_stats))
        
        if n_stats == 1:
            axes = [axes]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(players)))
        
        for i, stat in enumerate(stats):
            values = [p.get(stat, 0) for p in players]
            
            bars = axes[i].bar(player_names, values, color=colors, alpha=0.7, edgecolor='black')
            
            # Adicionar valores nas barras
            for bar, value in zip(bars, values):
                height = bar.get_height()
                axes[i].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
            
            axes[i].set_title(f'{stat.replace("_", " ").title()}', fontsize=14, fontweight='bold')
            axes[i].set_ylabel('Value', fontsize=12)
            axes[i].grid(True, alpha=0.3, axis='y')
            
            # Rotacionar nomes se necessário
            if len(max(player_names, key=len)) > 10:
                axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Salvar e retornar
        filename = f"stats_comparison_{int(datetime.now().timestamp())}.png"
        filepath = self.viz_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"/static/visualizations/{filename}"
    
    def generate_age_value_distribution(self, players: List[Dict], position: str) -> str:
        """Gerar distribuição idade vs valor para uma posição"""
        
        if not players:
            return None
        
        # Filtrar por posição se especificado
        if position and position != 'All':
            players = [p for p in players if p.get('position', '').lower() == position.lower()]
        
        ages = [p.get('age', 25) for p in players]
        values = [p.get('market_value', 0) for p in players]
        
        # Criar scatter plot com densidade
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Scatter plot principal
        ax1.scatter(ages, values, alpha=0.6, c=self.colors['primary'], s=50, edgecolors='black', linewidth=0.5)
        ax1.set_xlabel('Age', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Market Value (€M)', fontsize=12, fontweight='bold')
        ax1.set_title(f'Age vs Market Value Distribution - {position}', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Adicionar linha de tendência
        if len(ages) > 1:
            z = np.polyfit(ages, values, 2)  # Polynomial de grau 2
            p = np.poly1d(z)
            x_trend = np.linspace(min(ages), max(ages), 100)
            ax1.plot(x_trend, p(x_trend), "r--", alpha=0.8, linewidth=2, label='Trend Line')
            ax1.legend()
        
        # Histogram de idades
        ax2.hist(ages, bins=15, alpha=0.7, color=self.colors['secondary'], edgecolor='black')
        ax2.set_xlabel('Age', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Number of Players', fontsize=12, fontweight='bold')
        ax2.set_title(f'Age Distribution - {position}', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Salvar e retornar
        filename = f"age_value_dist_{position.lower()}_{int(datetime.now().timestamp())}.png"
        filepath = self.viz_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"/static/visualizations/{filename}"
    
    def cleanup_old_visualizations(self, days_old: int = 7) -> int:
        """Limpar visualizações antigas"""
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
        deleted_count = 0
        
        for file_path in self.viz_dir.glob("*.png"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except OSError:
                    continue
        
        return deleted_count
    
    def get_visualization_url(self, viz_path: str) -> str:
        """Obter URL completa da visualização"""
        if viz_path.startswith('/static/'):
            return viz_path
        return f"/static/visualizations/{viz_path}"

# Instância global do serviço
visualization_service = VisualizationService()