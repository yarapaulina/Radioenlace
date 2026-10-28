"""
Modelos de Dados Pydantic para a Aplicação de Rádio Enlace.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ObstacleItem(BaseModel):
    distance_km: float = Field(..., ge=0, description="Distância do obstáculo a partir do TX em km")
    height_m: float = Field(..., ge=0, description="Altura do obstáculo acima do solo em metros")
    description: Optional[str] = Field("Obstáculo", description="Descrição (ex: Morro, Prédio, Árvores)")


class RadioLinkRequest(BaseModel):
    # Frequência e Geometria
    frequency_mhz: float = Field(5800.0, gt=0, description="Frequência de operação em MHz (ex: 5800 para 5.8 GHz, 11000 para 11 GHz)")
    distance_km: float = Field(10.0, gt=0, description="Distância entre as estações em km")
    
    # Coordenadas Geográficas (Estilo LINKPlanner)
    site_a_name: Optional[str] = Field("Estação A (TX)", description="Nome ou ID do Site A")
    site_a_lat: Optional[float] = Field(-23.5505, description="Latitude do Site A (graus decimais)")
    site_a_lon: Optional[float] = Field(-46.6333, description="Longitude do Site A (graus decimais)")
    
    site_b_name: Optional[str] = Field("Estação B (RX)", description="Nome ou ID do Site B")
    site_b_lat: Optional[float] = Field(-23.6300, description="Latitude do Site B (graus decimais)")
    site_b_lon: Optional[float] = Field(-46.7200, description="Longitude do Site B (graus decimais)")
    
    # Transmissor (TX)
    tx_power_dbm: float = Field(20.0, description="Potência do rádio transmissor em dBm")
    tx_cable_loss_db: float = Field(1.5, ge=0, description="Perdas de cabos e conectores no TX em dB")
    tx_antenna_gain_dbi: float = Field(25.0, ge=0, description="Ganho da antena transmissora em dBi")
    tx_tower_height_m: float = Field(20.0, ge=0, description="Altura da torre transmissora em metros")
    tx_terrain_altitude_m: float = Field(50.0, description="Altitude do terreno no TX em metros (nível do mar)")
    
    # Receptor (RX)
    rx_antenna_gain_dbi: float = Field(25.0, ge=0, description="Ganho da antena receptora em dBi")
    rx_cable_loss_db: float = Field(1.5, ge=0, description="Perdas de cabos e conectores no RX em dB")
    rx_sensitivity_dbm: float = Field(-75.0, description="Sensibilidade do receptor em dBm (ex: -75 dBm)")
    rx_tower_height_m: float = Field(20.0, ge=0, description="Altura da torre receptora em metros")
    rx_terrain_altitude_m: float = Field(80.0, description="Altitude do terreno no RX em metros (nível do mar)")
    
    # Perdas adicionais
    misc_losses_db: float = Field(0.0, ge=0, description="Perdas adicionais diversas em dB")
    
    # Parâmetros Ambientais e Clima
    k_factor: float = Field(1.33333, gt=0, description="Fator K de refração da Terra (4/3 = 1.333 padrão)")
    rain_rate_mmh: float = Field(42.0, ge=0, description="Taxa de precipitação pluviométrica R0.01 em mm/h")
    polarization: str = Field("H", description="Polarização da onda: 'H' (Horizontal) ou 'V' (Vertical)")
    enable_rain: bool = Field(True, description="Incluir atenuação por chuva nos cálculos")
    enable_gas: bool = Field(True, description="Incluir atenuação por gases atmosféricos")
    
    # Obstruções ao longo do trajeto
    obstacles: List[ObstacleItem] = Field(default_factory=list, description="Lista de obstáculos no perfil do enlace")
    
    # Amostras de altitude de terreno real DEM (SRTM)
    terrain_elevations: Optional[List[float]] = Field(None, description="Amostras de altitude real de terreno coletadas via DEM/SRTM")


class ElevationProfileRequest(BaseModel):
    lat1: float = Field(..., description="Latitude do Site A")
    lon1: float = Field(..., description="Longitude do Site A")
    lat2: float = Field(..., description="Latitude do Site B")
    lon2: float = Field(..., description="Longitude do Site B")
    num_points: int = Field(50, ge=10, le=200, description="Número de pontos a amostrar ao longo do trajeto")


class OptimizationRequest(BaseModel):
    link_params: RadioLinkRequest
    target_fade_margin_db: float = Field(25.0, description="Margem de desvanecimento desejada em dB (ex: 20 a 30 dB)")
    target_availability_pct: float = Field(99.999, description="Disponibilidade anual desejada em % (ex: 99.999% '5 noves')")


class AIQueryRequest(BaseModel):
    link_params: RadioLinkRequest
    user_query: Optional[str] = Field(None, description="Pergunta ou dúvida específica do usuário")
    api_key: Optional[str] = Field(None, description="Chave da API Gemini (opcional)")
