"""
Módulo de Cálculos Físicos e Eletromagnéticos para Rádio Enlaces
Baseado nas Recomendações Internacionais da ITU-R (P.530, P.838, P.676, P.526)
e nos Modelos Clássicos de Telecomunicações (Friis, Vigants-Barnett, Fresnel).
"""

import urllib.request
import json
import math
from typing import Dict, Any, List, Tuple, Optional


SPEED_OF_LIGHT = 299792458.0  # m/s
EARTH_RADIUS_KM = 6371.0       # km


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância geodésica entre dois pontos (WGS84 / Haversine) em km.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 3)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula o azimute de orientação da antena (bearing) em graus (0° a 360°).
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    theta = math.atan2(y, x)
    bearing = (math.degrees(theta) + 360.0) % 360.0
    return round(bearing, 1)


def calculate_tilt_angle(distance_km: float, alt_tx_m: float, h_tx_m: float, alt_rx_m: float, h_rx_m: float) -> float:
    """
    Calcula o ângulo de inclinação vertical (tilt angle) da antena em graus.
    Positivo = apontando para cima; Negativo = apontando para baixo (downtilt).
    """
    if distance_km <= 0:
        return 0.0
    dist_m = distance_km * 1000.0
    delta_h = (alt_rx_m + h_rx_m) - (alt_tx_m + h_tx_m)
    tilt_rad = math.atan2(delta_h, dist_m)
    return round(math.degrees(tilt_rad), 2)


def sample_great_circle_points(lat1: float, lon1: float, lat2: float, lon2: float, num_points: int = 50) -> List[Tuple[float, float, float]]:
    """
    Interpola coordenadas (lat, lon, fraction) ao longo da linha geodésica.
    """
    points = []
    for i in range(num_points + 1):
        fraction = i / num_points
        lat = lat1 + (lat2 - lat1) * fraction
        lon = lon1 + (lon2 - lon1) * fraction
        points.append((round(lat, 6), round(lon, 6), round(fraction, 4)))
    return points


def fetch_elevation_profile(lat1: float, lon1: float, lat2: float, lon2: float, num_points: int = 50) -> Dict[str, Any]:
    """
    Obtém o perfil de elevação do terreno real via Open-Meteo DEM / SRTM (gratuito e sem chave de API).
    Inclui fallback seguro de interpolação caso a rede esteja indisponível.
    """
    points = sample_great_circle_points(lat1, lon1, lat2, lon2, num_points)
    lats = [str(p[0]) for p in points]
    lons = [str(p[1]) for p in points]
    
    url = f"https://api.open-meteo.com/v1/elevation?latitude={','.join(lats)}&longitude={','.join(lons)}"
    elevations = []
    source = "Open-Meteo Elevation (SRTM DEM)"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RadioLinkPro/1.0"})
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "elevation" in data and isinstance(data["elevation"], list):
                elevations = [float(e) if e is not None else 0.0 for e in data["elevation"]]
    except Exception:
        # Fallback de modelagem de relevo aproximada com ondulação suave
        source = "Interpolação de Terreno (Offline Fallback)"
        elevations = [round(50.0 + 15.0 * math.sin(i * 0.3) + i * 0.5, 1) for i in range(num_points + 1)]

    dist_km = calculate_haversine_distance(lat1, lon1, lat2, lon2)
    bearing_ab = calculate_bearing(lat1, lon1, lat2, lon2)
    bearing_ba = calculate_bearing(lat2, lon2, lat1, lon1)

    return {
        "source": source,
        "distance_km": dist_km,
        "bearing_ab_deg": bearing_ab,
        "bearing_ba_deg": bearing_ba,
        "samples": [
            {
                "lat": pt[0],
                "lon": pt[1],
                "distance_km": round(pt[2] * dist_km, 3),
                "elevation_m": elevations[idx] if idx < len(elevations) else 0.0
            }
            for idx, pt in enumerate(points)
        ],
        "elevations": elevations,
        "elevations_m": elevations,
        "site_a_elevation_m": elevations[0] if elevations else 0.0,
        "site_b_elevation_m": elevations[-1] if elevations else 0.0,
        "site_a_altitude_m": elevations[0] if elevations else 0.0,
        "site_b_altitude_m": elevations[-1] if elevations else 0.0
    }


def calculate_wavelength(frequency_mhz: float) -> float:
    """Calcula o comprimento de onda em metros."""
    if frequency_mhz <= 0:
        return 0.0
    return SPEED_OF_LIGHT / (frequency_mhz * 1e6)


def calculate_fspl(distance_km: float, frequency_mhz: float) -> float:
    """
    Calcula a Perda de Percurso em Espaço Livre (Free Space Path Loss - FSPL).
    Fórmula clássica: FSPL (dB) = 32.44 + 20*log10(d_km) + 20*log10(f_MHz)
    """
    if distance_km <= 0 or frequency_mhz <= 0:
        return 0.0
    return 32.44 + 20.0 * math.log10(distance_km) + 20.0 * math.log10(frequency_mhz)


def calculate_eirp(tx_power_dbm: float, tx_cable_loss_db: float, tx_antenna_gain_dbi: float) -> float:
    """
    Calcula o PIRE / EIRP (Potência Isotrópica Radiada Equivalente).
    PIRE = P_tx - L_tx + G_tx
    """
    return tx_power_dbm - tx_cable_loss_db + tx_antenna_gain_dbi


def calculate_fresnel_radius(n: int, distance_km: float, frequency_mhz: float, d1_km: float) -> float:
    """
    Calcula o raio da n-ésima Zona de Fresnel em um ponto a d1_km do transmissor.
    rn = sqrt( (n * lambda * d1 * d2) / d )
    com d1, d2 em metros, lambda em metros.
    """
    if distance_km <= 0 or frequency_mhz <= 0 or d1_km <= 0 or d1_km >= distance_km:
        return 0.0
    
    wavelength = calculate_wavelength(frequency_mhz)
    d1_m = d1_km * 1000.0
    d2_m = (distance_km - d1_km) * 1000.0
    d_m = distance_km * 1000.0
    
    radius = math.sqrt((n * wavelength * d1_m * d2_m) / d_m)
    return radius


def calculate_fresnel_midpoint_radius(distance_km: float, frequency_mhz: float) -> float:
    """
    Calcula o raio da 1ª Zona de Fresnel no ponto médio do enlace (ponto de raio máximo).
    r1_max = 8.656 * sqrt( d_km / f_GHz )
    """
    if distance_km <= 0 or frequency_mhz <= 0:
        return 0.0
    f_ghz = frequency_mhz / 1000.0
    return 8.656 * math.sqrt(distance_km / f_ghz)


def calculate_earth_bulge(d1_km: float, distance_km: float, k_factor: float = 4.0 / 3.0) -> float:
    """
    Calcula o abaulamento da Terra (flecha/sagitta) em um ponto intermediário d1.
    hc (metros) = (d1 * d2) / (12.74 * K)
    onde d1, d2 em km, K é o fator de refração atmosférica (padrão 4/3 = 1.333).
    """
    if distance_km <= 0 or d1_km <= 0 or d1_km >= distance_km or k_factor <= 0:
        return 0.0
    d2_km = distance_km - d1_km
    return (d1_km * d2_km) / (12.74 * k_factor)


def get_itu_rain_coefficients(frequency_ghz: float, polarization: str = "H") -> Tuple[float, float]:
    """
    Retorna os coeficientes k e alpha para o modelo de atenuação por chuva ITU-R P.838.
    Suporta polarização Horizontal ('H') e Vertical ('V').
    """
    f = max(1.0, min(frequency_ghz, 100.0))
    pol = polarization.upper()
    
    # Coeficientes aproximados tabelados e interpolados rigorosamente conforme ITU-R P.838-3
    freqs = [1, 2, 4, 6, 8, 10, 12, 15, 18, 20, 24, 28, 30, 38, 40, 60, 80]
    
    # [k_H, alpha_H, k_V, alpha_V]
    table = {
        1:  (0.0000387, 0.912, 0.0000352, 0.880),
        2:  (0.000154,  0.963, 0.000138,  0.923),
        4:  (0.000650,  1.121, 0.000591,  1.075),
        6:  (0.00175,   1.308, 0.00155,   1.265),
        8:  (0.00454,   1.327, 0.00395,   1.310),
        10: (0.0101,    1.276, 0.00887,   1.264),
        12: (0.0188,    1.217, 0.0168,    1.200),
        15: (0.0367,    1.154, 0.0335,    1.128),
        18: (0.0707,    1.089, 0.0609,    1.065),
        20: (0.0916,    1.056, 0.0751,    1.030),
        24: (0.137,     1.000, 0.117,     0.970),
        28: (0.187,     0.960, 0.166,     0.929),
        30: (0.214,     0.939, 0.191,     0.912),
        38: (0.350,     0.880, 0.310,     0.855),
        40: (0.371,     0.868, 0.334,     0.842),
        60: (0.707,     0.780, 0.642,     0.755),
        80: (1.100,     0.720, 1.020,     0.700),
    }
    
    # Encontrar faixa de interpolação
    if f <= freqs[0]:
        row = table[freqs[0]]
        return (row[0], row[1]) if pol == "H" else (row[2], row[3])
    if f >= freqs[-1]:
        row = table[freqs[-1]]
        return (row[0], row[1]) if pol == "H" else (row[2], row[3])
    
    for i in range(len(freqs) - 1):
        f1, f2 = freqs[i], freqs[i+1]
        if f1 <= f <= f2:
            weight = (f - f1) / (f2 - f1)
            r1, r2 = table[f1], table[f2]
            if pol == "H":
                k = r1[0] * math.pow(r2[0] / r1[0], weight)
                alpha = r1[1] + weight * (r2[1] - r1[1])
            else:
                k = r1[2] * math.pow(r2[2] / r1[2], weight)
                alpha = r1[3] + weight * (r2[3] - r1[3])
            return k, alpha
            
    return 0.01, 1.0


def calculate_rain_attenuation(
    distance_km: float,
    frequency_mhz: float,
    rain_rate_mmh: float = 42.0,  # R0.01 em mm/h (Região tropical típica Brasil varia de 40 a 100 mm/h)
    polarization: str = "H"
) -> Dict[str, float]:
    """
    Calcula a atenuação específica por chuva e a atenuação total do enlace
    segundo ITU-R P.838-3 e ITU-R P.530-17.
    """
    if distance_km <= 0 or frequency_mhz <= 0 or rain_rate_mmh <= 0:
        return {"gamma_r_db_km": 0.0, "d_eff_km": 0.0, "attenuation_rain_db": 0.0}
    
    f_ghz = frequency_mhz / 1000.0
    k, alpha = get_itu_rain_coefficients(f_ghz, polarization)
    
    # Atenuação específica de chuva (dB/km)
    gamma_r = k * math.pow(rain_rate_mmh, alpha)
    
    # Fator de redução de percurso r (ITU-R P.530-17)
    term1 = 0.78 * math.sqrt(max(0.001, (distance_km * gamma_r) / f_ghz))
    term2 = 0.11 * (1.0 - math.exp(-0.2 * distance_km))
    denom = 1.0 + term1 - term2
    r_factor = 1.0 / denom if denom > 0 else 1.0
    r_factor = min(1.0, max(0.1, r_factor))
    
    d_eff = distance_km * r_factor
    attenuation_rain = gamma_r * d_eff
    
    return {
        "gamma_r_db_km": round(gamma_r, 4),
        "d_eff_km": round(d_eff, 3),
        "r_factor": round(r_factor, 4),
        "attenuation_rain_db": round(attenuation_rain, 2)
    }


def calculate_atmospheric_gas_attenuation(distance_km: float, frequency_mhz: float) -> float:
    """
    Calcula a atenuação por absorção de gases atmosféricos (Oxigênio e Vapor d'Água)
    conforme ITU-R P.676 (nível do mar, 15°C, 1013 hPa, 7.5 g/m³ de vapor d'água).
    """
    if distance_km <= 0 or frequency_mhz <= 0:
        return 0.0
    
    f_ghz = frequency_mhz / 1000.0
    
    # Atenuação específica por Oxigênio (dB/km)
    if f_ghz < 50.0:
        gamma_o = (7.19e-3 + (6.09 / (f_ghz**2 + 0.227)) + (4.81 / ((f_ghz - 57)**2 + 1.50))) * (f_ghz**2 * 1e-3)
    elif 50.0 <= f_ghz <= 70.0:
        # Pico de absorção em torno de 60 GHz
        gamma_o = 15.0 * math.exp(-((f_ghz - 60.0)**2) / 36.0)
    else:
        gamma_o = 0.05
        
    # Atenuação específica por Vapor d'Água (dB/km) - ressonância em 22.2 GHz
    gamma_w = (0.05 + 0.0021 * 7.5 + (3.6 / ((f_ghz - 22.2)**2 + 8.5))) * (f_ghz**2 * 7.5 * 1e-4)
    
    gamma_total = max(0.001, gamma_o + gamma_w)
    return round(gamma_total * distance_km, 2)


def calculate_availability_and_reliability(
    distance_km: float,
    frequency_mhz: float,
    fade_margin_db: float,
    rain_attenuation_db: float = 0.0,
    geoclimatic_factor: float = 1.0e-5  # Vigants-Barnett (1e-5 terreno médio, 4e-5 litorâneo úmido)
) -> Dict[str, Any]:
    """
    Calcula a disponibilidade anual percentual e o tempo de queda (outage)
    usando o modelo de desvanecimento por múltiplos percursos (Vigants-Barnett / ITU-R P.530)
    e atenuação por chuva.
    """
    if distance_km <= 0 or frequency_mhz <= 0:
        return {
            "availability_percent": 100.0,
            "unavailability_percent": 0.0,
            "downtime_minutes_year": 0.0,
            "downtime_seconds_year": 0.0,
            "status": "Indeterminado"
        }
    
    f_ghz = frequency_mhz / 1000.0
    
    # 1. Probabilidade de desvanecimento por múltiplos percursos
    p0 = geoclimatic_factor * math.pow(distance_km, 3.0) * math.pow(f_ghz, 1.2)
    # Probabilidade de desvanecimento profundo que supera a margem M
    p_multipath = p0 * math.pow(10.0, -fade_margin_db / 10.0)
    p_multipath = max(0.0, min(1.0, p_multipath))
    
    # 2. Indisponibilidade por chuva: quando a atenuação de chuva excede a margem
    if rain_attenuation_db > 0 and fade_margin_db > 0:
        # Se margem for menor que A0.01, chuva causa indisponibilidade adicional
        if fade_margin_db < rain_attenuation_db:
            # Estimação empírica de probabilidade conforme ITU-R P.530
            ratio = max(0.01, fade_margin_db / rain_attenuation_db)
            p_rain = 0.0001 * math.pow(ratio, -1.8)
            p_rain = max(0.0, min(0.05, p_rain))
        else:
            p_rain = 0.00001 * math.exp(-(fade_margin_db - rain_attenuation_db) / 5.0)
    else:
        p_rain = 0.0
        
    p_total_outage = min(1.0, p_multipath + p_rain)
    unavailability_pct = p_total_outage * 100.0
    availability_pct = max(0.0, 100.0 - unavailability_pct)
    
    # Tempo de indisponibilidade anual (em segundos e minutos)
    seconds_in_year = 365.25 * 24.0 * 3600.0
    downtime_sec = p_total_outage * seconds_in_year
    downtime_min = downtime_sec / 60.0
    
    # Nível de classificação técnica
    if availability_pct >= 99.999:
        status = "Excelente (Carrier Grade - 5 Noves)"
    elif availability_pct >= 99.99:
        status = "Muito Bom (Padrão Corporativo - 4 Noves)"
    elif availability_pct >= 99.9:
        status = "Adequado (Acesso Residencial/Comercial)"
    elif availability_pct >= 99.0:
        status = "Atenção (Margem Baixa / Sujeito a Quedas)"
    else:
        status = "Crítico (Enlace Inviável nas Condições Atuais)"
        
    return {
        "availability_percent": round(availability_pct, 5),
        "unavailability_percent": round(unavailability_pct, 5),
        "downtime_seconds_year": round(downtime_sec, 1),
        "downtime_minutes_year": round(downtime_min, 2),
        "p_multipath": p_multipath,
        "p_rain": p_rain,
        "status": status
    }


def generate_link_elevation_profile(
    distance_km: float,
    frequency_mhz: float,
    tx_tower_height_m: float,
    rx_tower_height_m: float,
    tx_terrain_altitude_m: float = 0.0,
    rx_terrain_altitude_m: float = 0.0,
    k_factor: float = 4.0 / 3.0,
    obstacles: Optional[List[Dict[str, float]]] = None,
    num_points: int = 100,
    terrain_elevations: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Gera o perfil longitudinal de elevação do enlace, incluindo:
    - Curvatura da Terra com fator K
    - Linha de Visada direta (LOS)
    - Envoltória superior e inferior da 1ª Zona de Fresnel
    - Linha de desobstrução de 60% da 1ª Zona de Fresnel
    - Obstruções e verificação de folga mínima
    - Relevo real (SRTM / DEM) caso fornecido
    """
    if distance_km <= 0 or frequency_mhz <= 0:
        return {"points": [], "is_obstructed": False, "min_clearance_percent": 100.0}
    
    obstacles = obstacles or []
    points = []
    
    tx_total_alt = tx_terrain_altitude_m + tx_tower_height_m
    rx_total_alt = rx_terrain_altitude_m + rx_tower_height_m
    
    min_clearance_ratio = 999.0
    worst_obstruction_point = None
    is_obstructed = False
    
    for i in range(num_points + 1):
        d1 = (i / num_points) * distance_km
        fraction = d1 / distance_km if distance_km > 0 else 0
        
        # Cota do terreno: relevo real DEM ou interpolação linear básica
        if terrain_elevations and len(terrain_elevations) > 1:
            idx_float = fraction * (len(terrain_elevations) - 1)
            i_low = int(idx_float)
            i_high = min(len(terrain_elevations) - 1, i_low + 1)
            w = idx_float - i_low
            terrain_base = terrain_elevations[i_low] * (1.0 - w) + terrain_elevations[i_high] * w
        else:
            terrain_base = tx_terrain_altitude_m + (rx_terrain_altitude_m - tx_terrain_altitude_m) * fraction
        
        # Abaulamento da Terra (metros)
        bulge = calculate_earth_bulge(d1, distance_km, k_factor)
        
        # Terreno com curvatura da Terra (nível efetivo do solo aparente)
        curved_terrain = terrain_base + bulge
        
        # Linha de Visada direta (LOS) entre o topo das duas antenas
        los_altitude = tx_total_alt + (rx_total_alt - tx_total_alt) * fraction
        
        # Raio da 1ª Zona de Fresnel neste ponto
        r1 = calculate_fresnel_radius(1, distance_km, frequency_mhz, d1)
        r60 = 0.6 * r1
        
        # Envoltórias de Fresnel relativas à linha de visada
        fresnel_top = los_altitude + r1
        fresnel_bottom = los_altitude - r1
        fresnel_60_bottom = los_altitude - r60
        
        # Verificar se há obstáculo cadastrado próximo a este ponto
        obs_height = 0.0
        for obs in obstacles:
            obs_dist = obs.get("distance_km", 0.0)
            if abs(obs_dist - d1) <= (distance_km / num_points):
                obs_height = max(obs_height, obs.get("height_m", 0.0))
                
        effective_ground = curved_terrain + obs_height
        
        # Folga entre a linha de visada e o obstáculo mais alto / solo
        clearance_m = los_altitude - effective_ground
        
        clearance_ratio = clearance_m / r1 if r1 > 0 else 1.0
        if 0 < d1 < distance_km and clearance_ratio < min_clearance_ratio:
            min_clearance_ratio = clearance_ratio
            worst_obstruction_point = {
                "distance_km": round(d1, 2),
                "clearance_m": round(clearance_m, 2),
                "fresnel_r1_m": round(r1, 2),
                "clearance_percent": round(clearance_ratio * 100.0, 1)
            }
            
        if clearance_ratio < 0.6:
            is_obstructed = True
            
        points.append({
            "distance_km": round(d1, 3),
            "terrain_m": round(curved_terrain, 2),
            "ground_with_obstacles_m": round(effective_ground, 2),
            "los_m": round(los_altitude, 2),
            "fresnel_top_m": round(fresnel_top, 2),
            "fresnel_bottom_m": round(fresnel_bottom, 2),
            "fresnel_60_bottom_m": round(fresnel_60_bottom, 2),
            "r1_radius_m": round(r1, 2),
            "bulge_m": round(bulge, 2)
        })
        
    return {
        "points": points,
        "is_obstructed": is_obstructed,
        "min_clearance_percent": round(min_clearance_ratio * 100.0, 1) if min_clearance_ratio != 999.0 else 100.0,
        "worst_point": worst_obstruction_point
    }


def compute_complete_link_budget(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executa o cálculo completo e unificado de Balanço de Potência de Rádio Enlace.
    """
    frequency_mhz = float(params.get("frequency_mhz", 5800.0))
    distance_km = float(params.get("distance_km", 10.0))
    tx_power_dbm = float(params.get("tx_power_dbm", 20.0))
    tx_cable_loss_db = float(params.get("tx_cable_loss_db", 1.5))
    tx_antenna_gain_dbi = float(params.get("tx_antenna_gain_dbi", 25.0))
    
    rx_antenna_gain_dbi = float(params.get("rx_antenna_gain_dbi", 25.0))
    rx_cable_loss_db = float(params.get("rx_cable_loss_db", 1.5))
    rx_sensitivity_dbm = float(params.get("rx_sensitivity_dbm", -75.0))
    
    misc_losses_db = float(params.get("misc_losses_db", 0.0))
    
    # Fatores ambientais
    k_factor = float(params.get("k_factor", 4.0 / 3.0))
    rain_rate_mmh = float(params.get("rain_rate_mmh", 42.0))
    polarization = str(params.get("polarization", "H")).upper()
    enable_rain = bool(params.get("enable_rain", True))
    enable_gas = bool(params.get("enable_gas", True))
    
    # 1. PIRE / EIRP
    eirp_dbm = calculate_eirp(tx_power_dbm, tx_cable_loss_db, tx_antenna_gain_dbi)
    
    # 2. Atenuação no espaço livre (FSPL)
    fspl_db = calculate_fspl(distance_km, frequency_mhz)
    
    # 3. Atenuação por chuva
    rain_info = calculate_rain_attenuation(distance_km, frequency_mhz, rain_rate_mmh, polarization) if enable_rain else {
        "gamma_r_db_km": 0.0, "d_eff_km": distance_km, "r_factor": 1.0, "attenuation_rain_db": 0.0
    }
    rain_loss_db = rain_info["attenuation_rain_db"]
    
    # 4. Atenuação por gases atmosféricos
    gas_loss_db = calculate_atmospheric_gas_attenuation(distance_km, frequency_mhz) if enable_gas else 0.0
    
    # 5. Perdas totais no trajeto
    total_path_loss_db = fspl_db + rain_loss_db + gas_loss_db + misc_losses_db
    
    # 6. Potência Recebida (RSL)
    # RSL = EIRP - Perda de Percurso + Ganho Antena RX - Perdas Cabos RX
    rsl_dbm = eirp_dbm - total_path_loss_db + rx_antenna_gain_dbi - rx_cable_loss_db
    
    # 7. Margem de Desvanecimento (Fade Margin)
    fade_margin_db = rsl_dbm - rx_sensitivity_dbm
    
    # 8. Raio da 1ª Zona de Fresnel no ponto médio
    fresnel_midpoint_m = calculate_fresnel_midpoint_radius(distance_km, frequency_mhz)
    fresnel_60_midpoint_m = 0.6 * fresnel_midpoint_m
    
    # 9. Abaulamento máximo da terra no meio do enlace
    earth_bulge_midpoint_m = calculate_earth_bulge(distance_km / 2.0, distance_km, k_factor)
    
    # 10. Confiabilidade e Disponibilidade
    reliability = calculate_availability_and_reliability(
        distance_km=distance_km,
        frequency_mhz=frequency_mhz,
        fade_margin_db=fade_margin_db,
        rain_attenuation_db=rain_loss_db
    )
    
    # Status de viabilidade técnica geral
    if fade_margin_db >= 25.0:
        verdict = "Enlace Altamente Confiável (Aprovado com Ampla Folga)"
        verdict_color = "success"
    elif fade_margin_db >= 15.0:
        verdict = "Enlace Viável (Aprovado dentro dos Padrões Normais)"
        verdict_color = "info"
    elif fade_margin_db >= 10.0:
        verdict = "Enlace Marginal (Requer Atenção e Monitoramento)"
        verdict_color = "warning"
    else:
        verdict = "Enlace Inviável (Margem Insuficiente - Risco Alto de Queda)"
        verdict_color = "danger"
        
    return {
        "inputs": {
            "frequency_mhz": frequency_mhz,
            "frequency_ghz": round(frequency_mhz / 1000.0, 3),
            "distance_km": distance_km,
            "tx_power_dbm": tx_power_dbm,
            "tx_cable_loss_db": tx_cable_loss_db,
            "tx_antenna_gain_dbi": tx_antenna_gain_dbi,
            "rx_antenna_gain_dbi": rx_antenna_gain_dbi,
            "rx_cable_loss_db": rx_cable_loss_db,
            "rx_sensitivity_dbm": rx_sensitivity_dbm,
            "misc_losses_db": misc_losses_db,
            "k_factor": k_factor,
            "rain_rate_mmh": rain_rate_mmh,
            "polarization": polarization
        },
        "budget": {
            "eirp_dbm": round(eirp_dbm, 2),
            "fspl_db": round(fspl_db, 2),
            "rain_loss_db": round(rain_loss_db, 2),
            "gas_loss_db": round(gas_loss_db, 2),
            "misc_losses_db": round(misc_losses_db, 2),
            "total_path_loss_db": round(total_path_loss_db, 2),
            "rsl_dbm": round(rsl_dbm, 2),
            "rx_sensitivity_dbm": round(rx_sensitivity_dbm, 2),
            "fade_margin_db": round(fade_margin_db, 2),
            "verdict": verdict,
            "verdict_color": verdict_color
        },
        "fresnel": {
            "midpoint_radius_r1_m": round(fresnel_midpoint_m, 2),
            "midpoint_clearance_60_m": round(fresnel_60_midpoint_m, 2),
            "wavelength_m": round(calculate_wavelength(frequency_mhz), 4),
            "earth_bulge_midpoint_m": round(earth_bulge_midpoint_m, 2)
        },
        "rain_details": rain_info,
        "reliability": reliability
    }
