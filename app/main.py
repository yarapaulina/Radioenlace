"""
Servidor FastAPI para Aplicação de Cálculo, Dimensionamento e Otimização com IA de Rádio Enlaces.
"""

import os
import urllib.request
import urllib.parse
import json
from pydantic import BaseModel, Field
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.models import RadioLinkRequest, OptimizationRequest, AIQueryRequest, ElevationProfileRequest
from app.core.radio_math import (
    compute_complete_link_budget,
    generate_link_elevation_profile,
    fetch_elevation_profile,
    calculate_haversine_distance,
    calculate_bearing,
    calculate_tilt_angle
)
from app.core.optimizer import optimize_radio_link
from app.core.ai_assistant import query_gemini_rf_expert
from app.core.report_generator import generate_pdf_report, generate_csv_report


app = FastAPI(
    title="RadioLink Pro - Sistema de Cálculo e Otimização de Rádio Enlace com IA",
    description="Calculadora profissional de balanço de potência, zonas de Fresnel, confiabilidade ITU-R e otimização por Inteligência Artificial.",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build de produção do frontend React (gerado por `npm run build` em frontend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")


# Presets típicos da indústria de Telecomunicações com coordenadas geográficas reais
PRESETS = [
    {
        "id": "wifi_5ghz_15km",
        "name": "5.8 GHz ISP Rural/Urbano (15 km)",
        "description": "Enlace clássico de provedor em faixa não licenciada (5.8 GHz) com antenas parabólicas de 30 dBi.",
        "params": {
            "frequency_mhz": 5800.0,
            "distance_km": 15.0,
            "site_a_name": "Torre Bela Vista (São Paulo)",
            "site_a_lat": -23.5615,
            "site_a_lon": -46.6559,
            "site_b_name": "Torre Osasco Centro",
            "site_b_lat": -23.5329,
            "site_b_lon": -46.7916,
            "tx_power_dbm": 22.0,
            "tx_cable_loss_db": 1.5,
            "tx_antenna_gain_dbi": 30.0,
            "tx_tower_height_m": 25.0,
            "tx_terrain_altitude_m": 780.0,
            "rx_antenna_gain_dbi": 30.0,
            "rx_cable_loss_db": 1.5,
            "rx_sensitivity_dbm": -74.0,
            "rx_tower_height_m": 20.0,
            "rx_terrain_altitude_m": 760.0,
            "misc_losses_db": 0.5,
            "k_factor": 1.33333,
            "rain_rate_mmh": 42.0,
            "polarization": "H",
            "enable_rain": True,
            "enable_gas": True,
            "obstacles": [{"distance_km": 7.5, "height_m": 12.0, "description": "Vegetação de copa alta / Morro intermediário"}]
        }
    },
    {
        "id": "backhaul_11ghz_8km",
        "name": "11 GHz Backhaul Corporativo (8 km)",
        "description": "Enlace micro-ondas licenciado de média distância para interconexão de torres com alta disponibilidade.",
        "params": {
            "frequency_mhz": 11000.0,
            "distance_km": 8.0,
            "site_a_name": "Serra do Curral (Belo Horizonte)",
            "site_a_lat": -19.9575,
            "site_a_lon": -43.9312,
            "site_b_name": "Torre Distrito Industrial (Betim)",
            "site_b_lat": -19.9678,
            "site_b_lon": -44.0090,
            "tx_power_dbm": 24.0,
            "tx_cable_loss_db": 1.0,
            "tx_antenna_gain_dbi": 35.0,
            "tx_tower_height_m": 30.0,
            "tx_terrain_altitude_m": 1100.0,
            "rx_antenna_gain_dbi": 35.0,
            "rx_cable_loss_db": 1.0,
            "rx_sensitivity_dbm": -71.0,
            "rx_tower_height_m": 30.0,
            "rx_terrain_altitude_m": 850.0,
            "misc_losses_db": 0.5,
            "k_factor": 1.33333,
            "rain_rate_mmh": 60.0,
            "polarization": "V",
            "enable_rain": True,
            "enable_gas": True,
            "obstacles": []
        }
    },
    {
        "id": "high_cap_18ghz_4km",
        "name": "18 GHz Alta Capacidade Metropolitano (4 km)",
        "description": "Enlace de alta vazão para operadoras e data centers com antenas compactas de 0.6m.",
        "params": {
            "frequency_mhz": 18000.0,
            "distance_km": 4.0,
            "site_a_name": "Morro do Sumaré (Rio de Janeiro)",
            "site_a_lat": -22.9519,
            "site_a_lon": -43.2105,
            "site_b_name": "Torre Icaraí (Niterói)",
            "site_b_lat": -22.9050,
            "site_b_lon": -43.1120,
            "tx_power_dbm": 18.0,
            "tx_cable_loss_db": 0.5,
            "tx_antenna_gain_dbi": 39.0,
            "tx_tower_height_m": 25.0,
            "tx_terrain_altitude_m": 420.0,
            "rx_antenna_gain_dbi": 39.0,
            "rx_cable_loss_db": 0.5,
            "rx_sensitivity_dbm": -68.0,
            "rx_tower_height_m": 25.0,
            "rx_terrain_altitude_m": 25.0,
            "misc_losses_db": 0.0,
            "k_factor": 1.33333,
            "rain_rate_mmh": 50.0,
            "polarization": "V",
            "enable_rain": True,
            "enable_gas": True,
            "obstacles": [{"distance_km": 2.0, "height_m": 18.0, "description": "Edifício comercial"}]
        }
    },
    {
        "id": "eband_80ghz_1_5km",
        "name": "80 GHz E-Band Multi-Gigabit (1.5 km)",
        "description": "Enlace de altíssima taxa (10 Gbps) em ondas milimétricas para interconexão urbana ponto a ponto.",
        "params": {
            "frequency_mhz": 80000.0,
            "distance_km": 1.5,
            "site_a_name": "Data Center Centro (Curitiba)",
            "site_a_lat": -25.4284,
            "site_a_lon": -49.2733,
            "site_b_name": "POP Batel",
            "site_b_lat": -25.4390,
            "site_b_lon": -49.2840,
            "tx_power_dbm": 16.0,
            "tx_cable_loss_db": 0.0,
            "tx_antenna_gain_dbi": 43.0,
            "tx_tower_height_m": 20.0,
            "tx_terrain_altitude_m": 920.0,
            "rx_antenna_gain_dbi": 43.0,
            "rx_cable_loss_db": 0.0,
            "rx_sensitivity_dbm": -60.0,
            "rx_tower_height_m": 20.0,
            "rx_terrain_altitude_m": 915.0,
            "misc_losses_db": 0.0,
            "k_factor": 1.33333,
            "rain_rate_mmh": 65.0,
            "polarization": "V",
            "enable_rain": True,
            "enable_gas": True,
            "obstacles": []
        }
    }
]


@app.get("/api/presets")
async def get_presets():
    """Retorna os cenários de rádio enlace predefinidos."""
    return PRESETS


@app.post("/api/elevation-profile")
async def get_elevation_profile(req: ElevationProfileRequest):
    """
    Obtém o perfil de elevação do terreno real ao longo do arco geodésico (DEM SRTM / Open-Meteo),
    calcula a distância real em km, azimute de apontamento e cotas do terreno das estações.
    """
    profile = fetch_elevation_profile(req.lat1, req.lon1, req.lat2, req.lon2, req.num_points)
    return profile


class GeocodeRequest(BaseModel):
    query: str = Field(..., description="Nome da cidade, bairro ou endereço para busca")


@app.post("/api/geocode")
async def geocode_location(req: GeocodeRequest):
    """
    Geocodificação simples de endereços via Nominatim OpenStreetMap com fallback.
    """
    q = req.query.strip()
    encoded = urllib.parse.quote(q)
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded}&limit=5"
    try:
        http_req = urllib.request.Request(url, headers={"User-Agent": "RadioLinkPro-App/1.0"})
        with urllib.request.urlopen(http_req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for item in data:
                results.append({
                    "display_name": item.get("display_name"),
                    "lat": float(item.get("lat")),
                    "lon": float(item.get("lon"))
                })
            return {"results": results}
    except Exception:
        # Fallback para coordenadas de capitais brasileiras comuns se a rede falhar
        capitais = {
            "sao paulo": (-23.5505, -46.6333),
            "rio de janeiro": (-22.9068, -43.1729),
            "belo horizonte": (-19.9167, -43.9345),
            "brasilia": (-15.7975, -47.8919),
            "curitiba": (-25.4284, -49.2733),
            "porto alegre": (-30.0346, -51.2177),
            "salvador": (-12.9777, -38.5016),
            "fortaleza": (-3.7172, -38.5433),
            "recife": (-8.0476, -34.8770),
            "florianopolis": (-27.5954, -48.5480)
        }
        clean = q.lower()
        for k, coords in capitais.items():
            if k in clean:
                return {"results": [{"display_name": f"{k.title()}, Brasil", "lat": coords[0], "lon": coords[1]}]}
        return {"results": []}


@app.post("/api/calculate")
async def calculate_link(req: RadioLinkRequest):
    """
    Endpoint principal para cálculo simultâneo de:
    - Balanço de Potência (Link Budget)
    - Zonas de Fresnel e Perfil de Terreno com Curvatura
    - Atenuação por Chuva (ITU-R P.838) e Gases (ITU-R P.676)
    - Confiabilidade e Tempo de Queda Anual
    - Relevo real DEM caso fornecido
    """
    params_dict = req.model_dump()
    obstacles_dict = [obs.model_dump() for obs in req.obstacles]
    
    # Se foram passadas coordenadas do Site A e Site B, calcula azimute e tilt
    bearing_ab = None
    bearing_ba = None
    tilt_ab = None
    if req.site_a_lat is not None and req.site_a_lon is not None and req.site_b_lat is not None and req.site_b_lon is not None:
        bearing_ab = calculate_bearing(req.site_a_lat, req.site_a_lon, req.site_b_lat, req.site_b_lon)
        bearing_ba = calculate_bearing(req.site_b_lat, req.site_b_lon, req.site_a_lat, req.site_a_lon)
        tilt_ab = calculate_tilt_angle(
            req.distance_km,
            req.tx_terrain_altitude_m,
            req.tx_tower_height_m,
            req.rx_terrain_altitude_m,
            req.rx_tower_height_m
        )
    
    # 1. Balanço de Potência
    budget_result = compute_complete_link_budget(params_dict)
    
    # 2. Perfil de Elevação e Linha de Visada (usando terrain_elevations real se presente)
    profile_result = generate_link_elevation_profile(
        distance_km=req.distance_km,
        frequency_mhz=req.frequency_mhz,
        tx_tower_height_m=req.tx_tower_height_m,
        rx_tower_height_m=req.rx_tower_height_m,
        tx_terrain_altitude_m=req.tx_terrain_altitude_m,
        rx_terrain_altitude_m=req.rx_terrain_altitude_m,
        k_factor=req.k_factor,
        obstacles=obstacles_dict,
        terrain_elevations=req.terrain_elevations
    )
    
    return {
        "budget_data": budget_result,
        "profile_data": profile_result,
        "geodesic": {
            "bearing_ab_deg": bearing_ab,
            "bearing_ba_deg": bearing_ba,
            "tilt_ab_deg": tilt_ab
        }
    }


@app.post("/api/optimize")
async def optimize_link(req: OptimizationRequest):
    """
    Endpoint para otimização com Inteligência Artificial:
    Dimensiona antenas, potências, elevação de torres e polarização ideais.
    """
    params_dict = req.link_params.model_dump()
    obstacles_dict = [obs.model_dump() for obs in req.link_params.obstacles]
    
    optimization_result = optimize_radio_link(
        params=params_dict,
        target_fade_margin_db=req.target_fade_margin_db,
        target_availability_pct=req.target_availability_pct,
        obstacles=obstacles_dict
    )
    
    return optimization_result


@app.post("/api/ai-consulting")
async def ai_consulting(req: AIQueryRequest):
    """
    Endpoint para consultoria técnica de RF com Inteligência Artificial.
    Usa Google Gemini 3.8 Flash com fallback seguro para motor especialista heurístico.
    """
    params_dict = req.link_params.model_dump()
    obstacles_dict = [obs.model_dump() for obs in req.link_params.obstacles]
    
    budget_result = compute_complete_link_budget(params_dict)
    profile_result = generate_link_elevation_profile(
        distance_km=req.link_params.distance_km,
        frequency_mhz=req.link_params.frequency_mhz,
        tx_tower_height_m=req.link_params.tx_tower_height_m,
        rx_tower_height_m=req.link_params.rx_tower_height_m,
        tx_terrain_altitude_m=req.link_params.tx_terrain_altitude_m,
        rx_terrain_altitude_m=req.link_params.rx_terrain_altitude_m,
        k_factor=req.link_params.k_factor,
        obstacles=obstacles_dict
    )
    
    consulting_result = query_gemini_rf_expert(
        budget_data=budget_result,
        profile_data=profile_result,
        user_query=req.user_query or "Gere uma análise técnica detalhada da viabilidade deste enlace.",
        api_key=req.api_key
    )
    
    return consulting_result


@app.post("/api/export/pdf")
async def export_pdf(req: RadioLinkRequest):
    """Gera e faz download do memorial descritivo de cálculo em PDF."""
    params_dict = req.model_dump()
    obstacles_dict = [obs.model_dump() for obs in req.obstacles]
    
    budget_result = compute_complete_link_budget(params_dict)
    profile_result = generate_link_elevation_profile(
        distance_km=req.distance_km,
        frequency_mhz=req.frequency_mhz,
        tx_tower_height_m=req.tx_tower_height_m,
        rx_tower_height_m=req.rx_tower_height_m,
        tx_terrain_altitude_m=req.tx_terrain_altitude_m,
        rx_terrain_altitude_m=req.rx_terrain_altitude_m,
        k_factor=req.k_factor,
        obstacles=obstacles_dict
    )
    
    pdf_bytes = generate_pdf_report(
        budget_data=budget_result,
        profile_data=profile_result,
        ai_recommendation=f"Veredito do Projeto: {budget_result['budget']['verdict']}. Margem de desvanecimento de {budget_result['budget']['fade_margin_db']} dB e disponibilidade projetada de {budget_result['reliability']['availability_percent']}%.",
        project_title="Memorial Técnico de Rádio Enlace"
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=memorial_radio_enlace.pdf"}
    )


@app.post("/api/export/csv")
async def export_csv(req: RadioLinkRequest):
    """Exporta todas as métricas e pontos do perfil em formato CSV."""
    params_dict = req.model_dump()
    obstacles_dict = [obs.model_dump() for obs in req.obstacles]
    
    budget_result = compute_complete_link_budget(params_dict)
    profile_result = generate_link_elevation_profile(
        distance_km=req.distance_km,
        frequency_mhz=req.frequency_mhz,
        tx_tower_height_m=req.tx_tower_height_m,
        rx_tower_height_m=req.rx_tower_height_m,
        tx_terrain_altitude_m=req.tx_terrain_altitude_m,
        rx_terrain_altitude_m=req.rx_terrain_altitude_m,
        k_factor=req.k_factor,
        obstacles=obstacles_dict
    )
    
    csv_text = generate_csv_report(budget_result, profile_result)
    
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dados_radio_enlace.csv"}
    )


# O frontend React é montado por último para que as rotas /api/* tenham prioridade.
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/", response_class=HTMLResponse)
    async def frontend_not_built():
        return (
            "<h1>RadioLink Pro — API ativa</h1>"
            "<p>O frontend React ainda não foi compilado. Execute <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>, "
            "ou use o servidor de desenvolvimento com <code>npm run dev</code> (http://localhost:5173).</p>"
        )
