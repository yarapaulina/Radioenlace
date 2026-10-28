"""
Módulo de Otimização Inteligente para Rádio Enlaces
Aplica algoritmos de otimização multiobjetivo e raciocínio de engenharia de RF
para dimensionar antenas, torres, potências e frequências ideais.
"""

import math
from typing import Dict, Any, List, Optional
from app.core.radio_math import (
    compute_complete_link_budget,
    generate_link_elevation_profile,
    calculate_earth_bulge,
    calculate_fresnel_radius
)


# Diâmetros comerciais típicos de antenas parabólicas e ganhos aproximados por faixa de frequência
ANTENNA_CATALOG = [
    {"diameter_m": 0.3, "name": "Antena Disco 0.3m (1 ft)", "g_5ghz": 22.0, "g_11ghz": 29.0, "g_18ghz": 33.0, "g_24ghz": 35.0},
    {"diameter_m": 0.6, "name": "Antena Disco 0.6m (2 ft)", "g_5ghz": 28.0, "g_11ghz": 35.0, "g_18ghz": 39.0, "g_24ghz": 41.0},
    {"diameter_m": 0.9, "name": "Antena Disco 0.9m (3 ft)", "g_5ghz": 31.0, "g_11ghz": 38.0, "g_18ghz": 42.0, "g_24ghz": 44.5},
    {"diameter_m": 1.2, "name": "Antena Disco 1.2m (4 ft)", "g_5ghz": 34.0, "g_11ghz": 41.0, "g_18ghz": 45.0, "g_24ghz": 47.0},
    {"diameter_m": 1.8, "name": "Antena Disco 1.8m (6 ft)", "g_5ghz": 37.0, "g_11ghz": 44.0, "g_18ghz": 48.0, "g_24ghz": 50.5},
]


def estimate_antenna_gain_for_freq(diameter_m: float, freq_mhz: float, efficiency: float = 0.55) -> float:
    """Calcula ganho teórico de antena parabólica em dBi: G = 10*log10( eta * (pi * D / lambda)^2 )"""
    f_ghz = freq_mhz / 1000.0
    wavelength = 0.3 / f_ghz
    gain_linear = efficiency * math.pow((math.pi * diameter_m) / wavelength, 2)
    return round(10.0 * math.log10(max(1.0, gain_linear)), 1)


def optimize_radio_link(
    params: Dict[str, Any],
    target_fade_margin_db: float = 25.0,
    target_availability_pct: float = 99.999,
    obstacles: Optional[List[Dict[str, float]]] = None
) -> Dict[str, Any]:
    """
    Executa a otimização algorítmica completa do projeto de rádio enlace.
    Retorna diagnóstico profundo, parâmetros otimizados e plano de ação técnico.
    """
    original_results = compute_complete_link_budget(params)
    original_budget = original_results["budget"]
    original_margin = original_budget["fade_margin_db"]
    original_availability = original_results["reliability"]["availability_percent"]
    
    distance_km = float(params.get("distance_km", 10.0))
    frequency_mhz = float(params.get("frequency_mhz", 5800.0))
    tx_tower_h = float(params.get("tx_tower_height_m", 15.0))
    rx_tower_h = float(params.get("rx_tower_height_m", 15.0))
    tx_alt = float(params.get("tx_terrain_altitude_m", 0.0))
    rx_alt = float(params.get("rx_terrain_altitude_m", 0.0))
    k_factor = float(params.get("k_factor", 4.0 / 3.0))
    
    # 1. Análise de Obstrução de Fresnel e Altura de Torres
    profile = generate_link_elevation_profile(
        distance_km=distance_km,
        frequency_mhz=frequency_mhz,
        tx_tower_height_m=tx_tower_h,
        rx_tower_height_m=rx_tower_h,
        tx_terrain_altitude_m=tx_alt,
        rx_terrain_altitude_m=rx_alt,
        k_factor=k_factor,
        obstacles=obstacles or []
    )
    
    tower_adjust_needed = False
    recommended_tx_tower = tx_tower_h
    recommended_rx_tower = rx_tower_h
    obstruction_notes = []
    
    if profile["is_obstructed"] or profile["min_clearance_percent"] < 60.0:
        tower_adjust_needed = True
        worst = profile.get("worst_point")
        deficiency_m = 0.0
        if worst:
            # Quanto falta para atingir 60% do raio de Fresnel
            r1 = worst["fresnel_r1_m"]
            clearance_m = worst["clearance_m"]
            target_clearance_m = 0.6 * r1
            deficiency_m = max(0.0, target_clearance_m - clearance_m)
            
        # Adicionar margem de segurança de 2 a 3 metros
        additional_height = math.ceil(deficiency_m + 3.0)
        # Distribuir elevação entre as duas torres ou na mais baixa
        if recommended_tx_tower <= recommended_rx_tower:
            recommended_tx_tower += additional_height
        else:
            recommended_rx_tower += additional_height
            
        obstruction_notes.append(
            f"Obstrução crítica detectada (folga de apenas {profile['min_clearance_percent']}% da 1ª Zona de Fresnel). "
            f"Recomenda-se elevar a infraestrutura em pelo menos +{additional_height}m para garantir 100% de visada limpa."
        )
    else:
        obstruction_notes.append("Linha de visada (LOS) e Zona de Fresnel de 60% totalmente livres de obstrução.")

    # 2. Otimização de Margem de Desvanecimento e Ganho de Antenas
    margin_deficit = target_fade_margin_db - original_margin
    optimized_params = dict(params)
    actions = []
    
    current_tx_gain = float(params.get("tx_antenna_gain_dbi", 25.0))
    current_rx_gain = float(params.get("rx_antenna_gain_dbi", 25.0))
    current_tx_power = float(params.get("tx_power_dbm", 20.0))
    
    opt_tx_gain = current_tx_gain
    opt_rx_gain = current_rx_gain
    opt_tx_power = current_tx_power
    
    if margin_deficit > 0:
        # Precisamos de mais ganho ou potência
        gain_needed_each = margin_deficit / 2.0
        
        # Testar se podemos aumentar antenas
        candidate_gain = current_tx_gain + math.ceil(gain_needed_each)
        if candidate_gain <= 38.0:
            opt_tx_gain = candidate_gain
            opt_rx_gain = candidate_gain
            actions.append(f"Substituir antenas de {current_tx_gain:.0f} dBi por modelos de maior ganho (~{opt_tx_gain:.0f} dBi) para ganho mútuo de +{2*(opt_tx_gain - current_tx_gain):.1f} dB.")
        else:
            opt_tx_gain = 38.0
            opt_rx_gain = 38.0
            remaining_deficit = target_fade_margin_db - (original_margin + (38.0 - current_tx_gain) + (38.0 - current_rx_gain))
            if remaining_deficit > 0 and opt_tx_power < 27.0:
                power_increase = min(27.0 - opt_tx_power, math.ceil(remaining_deficit))
                opt_tx_power += power_increase
                actions.append(f"Ajustar potência de transmissão para {opt_tx_power:.1f} dBm (+{power_increase:.1f} dBm) para complementar o link budget.")
    elif margin_deficit < -10.0 and opt_tx_power > 14.0:
        # Enlace superdimensionado - podemos reduzir potência para economizar e reduzir ruído
        surplus = abs(margin_deficit) - 5.0
        reduction = min(surplus, opt_tx_power - 14.0)
        opt_tx_power -= reduction
        actions.append(f"Reduzir potência do transmissor em -{reduction:.1f} dBm (para {opt_tx_power:.1f} dBm) para reduzir interferência co-canal e evitar saturação do receptor.")
    else:
        actions.append("Ganho de antenas e potência de transmissão já estão próximos do ponto de equilíbrio ideal.")

    # 3. Consideração de Polarização em Frequências Altas
    polarization = str(params.get("polarization", "H")).upper()
    if frequency_mhz >= 10000.0 and polarization == "H":
        actions.append("Para enlaces acima de 10 GHz com taxas tropicais de chuva, recomenda-se utilizar polarização Vertical (V), que sofre menor atenuação específica por chuva (~15% a 25% menos perda).")

    # Atualizar parâmetros otimizados
    optimized_params["tx_antenna_gain_dbi"] = opt_tx_gain
    optimized_params["rx_antenna_gain_dbi"] = opt_rx_gain
    optimized_params["tx_power_dbm"] = opt_tx_power
    optimized_params["tx_tower_height_m"] = recommended_tx_tower
    optimized_params["rx_tower_height_m"] = recommended_rx_tower
    if frequency_mhz >= 10000.0:
        optimized_params["polarization"] = "V"
        
    optimized_results = compute_complete_link_budget(optimized_params)
    optimized_profile = generate_link_elevation_profile(
        distance_km=distance_km,
        frequency_mhz=frequency_mhz,
        tx_tower_height_m=recommended_tx_tower,
        rx_tower_height_m=recommended_rx_tower,
        tx_terrain_altitude_m=tx_alt,
        rx_terrain_altitude_m=rx_alt,
        k_factor=k_factor,
        obstacles=obstacles or []
    )
    
    # Avaliação de conformidade regulatória (ex: EIRP ANATEL)
    opt_eirp = optimized_results["budget"]["eirp_dbm"]
    anatel_status = "Conforme"
    if frequency_mhz >= 5150 and frequency_mhz <= 5850:
        if opt_eirp > 36.0:
            anatel_status = f"Atenção: PIRE de {opt_eirp:.1f} dBm excede o limite comum de 36 dBm (Res. 680 da ANATEL para 5.8 GHz). Em enlaces ponto-a-ponto autorizados, a potência conduzida deve ser ajustada caso a antena supere 6 dBi (regra 1:1 ou 3:1 de back-off)."
        else:
            anatel_status = f"Excelente: PIRE de {opt_eirp:.1f} dBm está dentro das diretrizes operacionais de 5 GHz."
    else:
        anatel_status = f"Enlace em banda licenciada ({frequency_mhz/1000.0:.1f} GHz). Requer coordenação de frequências e outorga técnica junto à ANATEL."

    return {
        "original_summary": {
            "fade_margin_db": original_margin,
            "availability_percent": original_availability,
            "rsl_dbm": original_budget["rsl_dbm"],
            "eirp_dbm": original_budget["eirp_dbm"],
            "downtime_minutes_year": original_results["reliability"]["downtime_minutes_year"],
            "min_clearance_percent": profile["min_clearance_percent"],
            "is_obstructed": profile["is_obstructed"]
        },
        "optimized_summary": {
            "fade_margin_db": optimized_results["budget"]["fade_margin_db"],
            "availability_percent": optimized_results["reliability"]["availability_percent"],
            "rsl_dbm": optimized_results["budget"]["rsl_dbm"],
            "eirp_dbm": optimized_results["budget"]["eirp_dbm"],
            "downtime_minutes_year": optimized_results["reliability"]["downtime_minutes_year"],
            "min_clearance_percent": optimized_profile["min_clearance_percent"],
            "is_obstructed": optimized_profile["is_obstructed"]
        },
        "recommendations": {
            "tx_antenna_gain_dbi": opt_tx_gain,
            "rx_antenna_gain_dbi": opt_rx_gain,
            "tx_power_dbm": opt_tx_power,
            "tx_tower_height_m": recommended_tx_tower,
            "rx_tower_height_m": recommended_rx_tower,
            "polarization": optimized_params.get("polarization", "H"),
            "action_items": actions,
            "obstruction_notes": obstruction_notes,
            "anatel_compliance": anatel_status
        },
        "optimized_params": optimized_params
    }
