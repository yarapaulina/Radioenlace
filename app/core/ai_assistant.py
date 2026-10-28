"""
Assistente de Inteligência Artificial Especialista em Rádio Enlaces e Telecomunicações.
Integra motor especialista heurístico local + API do Google Gemini (gemini-3.8-flash).
"""

import os
from typing import Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def generate_local_heuristic_analysis(
    budget_data: Dict[str, Any],
    profile_data: Optional[Dict[str, Any]] = None,
    user_query: Optional[str] = None
) -> str:
    """
    Gera um relatório técnico analítico detalhado operando 100% offline,
    atuando como um Engenheiro Sênior de Telecomunicações / RF.
    """
    b = budget_data.get("budget", {})
    inp = budget_data.get("inputs", {})
    rel = budget_data.get("reliability", {})
    fresnel = budget_data.get("fresnel", {})
    rain = budget_data.get("rain_details", {})
    
    freq_ghz = inp.get("frequency_ghz", 5.8)
    dist_km = inp.get("distance_km", 10.0)
    margin = b.get("fade_margin_db", 0.0)
    rsl = b.get("rsl_dbm", -70.0)
    eirp = b.get("eirp_dbm", 30.0)
    avail = rel.get("availability_percent", 99.99)
    downtime_min = rel.get("downtime_minutes_year", 0.0)
    
    lines = []
    lines.append("### 📡 Parecer Técnico do Especialista em Rádio Enlace (IA Local)\n")
    lines.append(f"**Cenário Analisado:** Enlace PTP de **{dist_km} km** operando em **{freq_ghz} GHz**.\n")
    
    # Diagnóstico da Margem de Desvanecimento
    if margin >= 25.0:
        lines.append(f"- **Margem de Desvanecimento Excelente ({margin:.1f} dB):** O enlace possui robustez de sobra contra eventos de desvanecimento por multi-percurso e intempéries climáticas.")
    elif margin >= 15.0:
        lines.append(f"- **Margem de Desvanecimento Adequada ({margin:.1f} dB):** Enlace operacional satisfatório. Recomendado monitorar variações sazonais de temperatura e umidade.")
    elif margin >= 10.0:
        lines.append(f"- **Margem de Desvanecimento no Limite ({margin:.1f} dB):** Risco moderado de degradação da modulação (QAM drop) durante variações atmosféricas ou chuvas moderadas.")
    else:
        lines.append(f"- **⚠️ Margem de Desvanecimento Crítica ({margin:.1f} dB):** O enlace está muito vulnerável a quedas. É mandatório elevar os ganhos de antena ou a potência.")

    # Diagnóstico de Potência Recebida (RSL)
    sens = b.get("rx_sensitivity_dbm", -75.0)
    lines.append(f"- **Potência Recebida (RSL = {rsl:.1f} dBm vs. Sensibilidade = {sens:.1f} dBm):**")
    if rsl > -45.0:
        lines.append("  - *Alerta de Saturação:* RSL muito elevado (> -45 dBm). Risco de saturar o LNA (baixo ruído) do receptor. Considere reduzir a potência do TX se o enlace for de curto alcance.")
    elif rsl < -75.0:
        lines.append("  - *Sinal Fraco:* RSL próximo do piso de sensibilidade. O rádio precisará descer para esquemas de modulação de baixa ordem (BPSK/QPSK), diminuindo a vazão de dados (throughput).")
    else:
        lines.append("  - *Nível Nominal:* Faixa de operação ideal para modulações elevadas (64-QAM a 1024-QAM).")

    # Diagnóstico de Fresnel e Relevo
    if profile_data:
        clearance = profile_data.get("min_clearance_percent", 100.0)
        is_obs = profile_data.get("is_obstructed", False)
        if is_obs or clearance < 60.0:
            lines.append(f"- **⚠️ Obstrução de Linha de Visada (Folga mínima: {clearance:.1f}% da 1ª Zona de Fresnel):**")
            lines.append(f"  - O elipsóide de Fresnel está invadido em ponto intermediário. O efeito gume de faca (knife-edge) causará perda adicional por difração de 6 a 20 dB. Elevação de torres é indispensável.")
        else:
            lines.append(f"- **Visada Óptica e Elipsóide de Fresnel Livres:** Folga mínima de {clearance:.1f}% mantida ao longo de todo o trajeto, respeitando a regra dos 60% da ITU-R.")
            
    # Diagnóstico de Chuva e Frequência
    if freq_ghz >= 10.0:
        rain_loss = rain.get("attenuation_rain_db", 0.0)
        lines.append(f"- **Impacto de Chuva em Frequências Altas ({freq_ghz} GHz):**")
        lines.append(f"  - Atenuação específica de chuva estimada em **{rain_loss:.1f} dB**. Recomenda-se ativar **ACM (Modulação e Codificação Adaptativa)** para manter o enlace ativo mesmo sob precipitação torrencial.")
        if inp.get("polarization") == "H":
            lines.append("  - *Dica:* A polarização Vertical (V) apresenta ~20% menos atenuação em relação à Horizontal (H) na chuva.")
    else:
        lines.append(f"- **Frequência Sub-10GHz ({freq_ghz} GHz):** A atenuação por chuva é negligenciável ({rain.get('attenuation_rain_db', 0.0):.1f} dB). As principais preocupações são visada, ruído de fundo e multi-percurso.")

    # Confiabilidade
    lines.append(f"- **Disponibilidade Estimada: {avail:.4f}%** (Indisponibilidade média projetada: **{downtime_min:.1f} minutos/ano**).")
    
    # Resposta à pergunta do usuário se fornecida
    if user_query:
        lines.append(f"\n**Comentário sobre sua pergunta ('{user_query}'):**")
        lines.append("Com base nos parâmetros atuais de rádio frequência calculados, este enlace atende aos requisitos técnicos primários desde que seguidas as recomendações de infraestrutura física e alinhamento fino das antenas com analisador de espectro.")

    return "\n".join(lines)


def query_gemini_rf_expert(
    budget_data: Dict[str, Any],
    profile_data: Optional[Dict[str, Any]],
    user_query: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executa consulta com o modelo Gemini 3.8 Flash para engenharia de telecomunicações.
    Se não houver API key ou biblioteca, reverte graciosamente para o motor analítico local.
    """
    resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
    
    if not resolved_key or not GENAI_AVAILABLE:
        analysis = generate_local_heuristic_analysis(budget_data, profile_data, user_query)
        return {
            "source": "local_ai_engine",
            "model": "Motor Especialista Heurístico RF (Offline)",
            "response": analysis,
            "has_gemini_key": bool(resolved_key)
        }
        
    try:
        client = genai.Client(api_key=resolved_key)
        
        system_prompt = (
            "Você é um Engenheiro Sênior de Telecomunicações e Especialista em Rádio Enlaces Ponto a Ponto (PTP/PTMP), "
            "com profundo domínio das recomendações da ITU-R (P.530, P.838, P.676, P.526), resoluções da ANATEL "
            "(como Resolução 680, limites de PIRE, canais de 5 GHz, 11 GHz, 18 GHz, 24 GHz, 80 GHz E-Band) "
            "e práticas de infraestrutura física (torres estaiadas, autoportantes, alinhamento de parábolas, ACM, RSSI). "
            "Seja direto, técnico, didático e forneça respostas práticas, com cálculos explicados e recomendações claras."
        )
        
        b = budget_data.get("budget", {})
        inp = budget_data.get("inputs", {})
        rel = budget_data.get("reliability", {})
        fresnel = budget_data.get("fresnel", {})
        rain = budget_data.get("rain_details", {})
        
        context_summary = f"""
Dados Atuais do Rádio Enlace:
- Frequência: {inp.get('frequency_mhz')} MHz ({inp.get('frequency_ghz')} GHz), Polarização: {inp.get('polarization')}
- Distância: {inp.get('distance_km')} km
- Potência TX: {inp.get('tx_power_dbm')} dBm | Perdas Cabo TX: {inp.get('tx_cable_loss_db')} dB | Ganho Antena TX: {inp.get('tx_antenna_gain_dbi')} dBi
- PIRE / EIRP: {b.get('eirp_dbm')} dBm
- Perda no Espaço Livre (FSPL): {b.get('fspl_db')} dB
- Atenuação por Chuva: {rain.get('attenuation_rain_db')} dB (Taxa: {inp.get('rain_rate_mmh')} mm/h)
- Atenuação por Gases Atmosféricos: {b.get('gas_loss_db')} dB
- Perda Total no Percurso: {b.get('total_path_loss_db')} dB
- Ganho Antena RX: {inp.get('rx_antenna_gain_dbi')} dBi | Perdas Cabo RX: {inp.get('rx_cable_loss_db')} dB
- Potência Recebida (RSL): {b.get('rsl_dbm')} dBm vs. Sensibilidade: {b.get('rx_sensitivity_dbm')} dBm
- Margem de Desvanecimento: {b.get('fade_margin_db')} dB
- Raio 1ª Zona de Fresnel (ponto médio): {fresnel.get('midpoint_radius_r1_m')} m (Folga 60%: {fresnel.get('midpoint_clearance_60_m')} m)
- Abaulamento da Terra (K={inp.get('k_factor')}): {fresnel.get('earth_bulge_midpoint_m')} m
- Disponibilidade Anual: {rel.get('availability_percent')}% (Queda anual: {rel.get('downtime_minutes_year')} minutos)
"""
        if profile_data:
            context_summary += f"""
- Perfil de Visada: Obstruído: {profile_data.get('is_obstructed')} | Folga Mínima de Fresnel: {profile_data.get('min_clearance_percent')}%
"""
            
        full_prompt = f"{context_summary}\n\nPergunta/Solicitação do Engenheiro:\n{user_query or 'Por favor, avalie a viabilidade técnica geral deste rádio enlace e aponte os principais pontos de otimização e riscos.'}"
        
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3
            )
        )
        
        return {
            "source": "gemini_api",
            "model": "Google Gemini 3.8 Flash",
            "response": response.text,
            "has_gemini_key": True
        }
    except Exception as e:
        # Fallback seguro para o motor local caso haja erro na chamada da API
        local_resp = generate_local_heuristic_analysis(budget_data, profile_data, user_query)
        return {
            "source": "local_fallback",
            "model": "Motor Especialista Heurístico RF (Fallback)",
            "response": f"*(Nota: Ocorreu um problema ao conectar com a API Gemini: {str(e)}. Apresentando diagnóstico gerado pelo motor especialista local:)*\n\n{local_resp}",
            "has_gemini_key": bool(resolved_key)
        }
