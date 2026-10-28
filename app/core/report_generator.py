"""
Módulo de Geração de Relatórios Técnicos (PDF e CSV)
Cria memoriais de cálculo profissionais prontos para homologação e projetos executivos.
"""

import io
import csv
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_pdf_report(
    budget_data: Dict[str, Any],
    profile_data: Optional[Dict[str, Any]] = None,
    ai_recommendation: Optional[str] = None,
    project_title: str = "Projeto de Rádio Enlace PTP"
) -> bytes:
    """
    Gera um relatório técnico em formato PDF com tabelas bem formatadas e visual de engenharia.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab não está instalado.")
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f766e')
    )
    
    elements = []
    
    # Cabeçalho
    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    elements.append(Paragraph(project_title, title_style))
    elements.append(Paragraph(f"Memorial de Cálculo de Engenharia de RF • Gerado em {now_str}", subtitle_style))
    elements.append(Spacer(1, 8))
    
    # 1. Resumo Executivo / Veredito
    b = budget_data.get("budget", {})
    inp = budget_data.get("inputs", {})
    rel = budget_data.get("reliability", {})
    fresnel = budget_data.get("fresnel", {})
    rain = budget_data.get("rain_details", {})
    
    verdict_text = b.get("verdict", "Em Análise")
    fade_margin = b.get("fade_margin_db", 0.0)
    avail_pct = rel.get("availability_percent", 99.99)
    downtime_min = rel.get("downtime_minutes_year", 0.0)
    
    summary_data = [
        ["Parâmetro Chave", "Valor Projetado", "Referência / Status"],
        ["Frequência Nominal", f"{inp.get('frequency_mhz')} MHz ({inp.get('frequency_ghz')} GHz)", f"Polarização {inp.get('polarization')}"],
        ["Distância do Enlace", f"{inp.get('distance_km')} km", "Visada Direta (LOS)"],
        ["PIRE / EIRP (TX)", f"{b.get('eirp_dbm')} dBm", "Potência Efetiva Radiada"],
        ["Nível Recebido (RSL)", f"{b.get('rsl_dbm')} dBm", f"Sensibilidade: {b.get('rx_sensitivity_dbm')} dBm"],
        ["Margem de Desvanecimento", f"{fade_margin} dB", verdict_text],
        ["Disponibilidade Anual", f"{avail_pct}%", f"{downtime_min:.1f} min/ano de queda estimada"]
    ]
    
    t_summary = Table(summary_data, colWidths=[150, 150, 220])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')])
    ]))
    
    elements.append(Paragraph("1. Resumo Executivo do Enlace", section_style))
    elements.append(t_summary)
    elements.append(Spacer(1, 12))
    
    # 2. Balanço Detalhado de Potência (Link Budget)
    elements.append(Paragraph("2. Balanço de Potência Detalhado (Link Budget)", section_style))
    
    budget_breakdown = [
        ["Estágio do Enlace", "Equação / Parâmetro", "Ganho / Perda (dB)", "Nível de Potência"],
        ["Potência do Transmissor (TX)", "Potência de Saída Conduzida", "-", f"+{inp.get('tx_power_dbm')} dBm"],
        ["Perdas em Cabos e Conectores TX", "Atenuação de linha de descida/jumper", f"-{inp.get('tx_cable_loss_db')} dB", f"+{inp.get('tx_power_dbm') - inp.get('tx_cable_loss_db'):.2f} dBm"],
        ["Ganho da Antena TX", "Antena Direcional Parabólica", f"+{inp.get('tx_antenna_gain_dbi')} dBi", f"+{b.get('eirp_dbm')} dBm (PIRE)"],
        ["Perda em Espaço Livre (FSPL)", f"ITU-R P.525 / Friis ({inp.get('distance_km')} km)", f"-{b.get('fspl_db')} dB", "-"],
        ["Atenuação por Chuva", f"ITU-R P.838 ({inp.get('rain_rate_mmh')} mm/h)", f"-{b.get('rain_loss_db')} dB", "-"],
        ["Atenuação por Gases Atmosféricos", "ITU-R P.676 (Oxigênio e Vapor)", f"-{b.get('gas_loss_db')} dB", "-"],
        ["Atenuação Total no Trajeto", "Soma de todas as atenuações", f"-{b.get('total_path_loss_db')} dB", "-"],
        ["Ganho da Antena RX", "Antena Direcional Parabólica", f"+{inp.get('rx_antenna_gain_dbi')} dBi", "-"],
        ["Perdas em Cabos e Conectores RX", "Atenuação de linha RX", f"-{inp.get('rx_cable_loss_db')} dB", "-"],
        ["Potência Recebida no Rádio (RSL)", "Sinal no LNA receptor", "-", f"{b.get('rsl_dbm')} dBm"],
        ["Sensibilidade do Receptor", "Limiar para modulação nominal", "-", f"{b.get('rx_sensitivity_dbm')} dBm"],
        ["Margem de Desvanecimento Líquida", "RSL - Sensibilidade", "-", f"+{fade_margin} dB"]
    ]
    
    t_budget = Table(budget_breakdown, colWidths=[150, 170, 100, 100])
    t_budget.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TEXTCOLOR', (-1, 3), (-1, 3), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor('#047857') if fade_margin >= 15 else colors.HexColor('#b91c1c')),
        ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold')
    ]))
    
    elements.append(t_budget)
    elements.append(Spacer(1, 12))
    
    # 3. Zonas de Fresnel e Curvatura da Terra
    elements.append(Paragraph("3. Desobstrução de Fresnel e Curvatura Terrestre", section_style))
    fresnel_data = [
        ["Parâmetro Geométrico", "Fórmula / Norma", "Valor Calculado"],
        ["Comprimento de Onda (lambda)", "c / f", f"{fresnel.get('wavelength_m')} metros"],
        ["Raio da 1ª Zona de Fresnel (meio do enlace)", "17.32 * sqrt(d1*d2 / (f*d))", f"{fresnel.get('midpoint_radius_r1_m')} metros"],
        ["Folga Mínima Recomendada (60% da 1ª Zona)", "0.6 * R1 (ITU-R P.526)", f"{fresnel.get('midpoint_clearance_60_m')} metros"],
        ["Abaulamento da Terra no ponto médio", f"(d1*d2)/(12.74*K) com K={inp.get('k_factor')}", f"{fresnel.get('earth_bulge_midpoint_m')} metros"]
    ]
    
    if profile_data:
        fresnel_data.append([
            "Folga Mínima Real no Perfil",
            "Verificação de obstáculos e relevo",
            f"{profile_data.get('min_clearance_percent')}% (Status: {'OBSTRUÍDO' if profile_data.get('is_obstructed') else 'LIVRE'})"
        ])
        
    t_fresnel = Table(fresnel_data, colWidths=[180, 190, 150])
    t_fresnel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(t_fresnel)
    elements.append(Spacer(1, 14))
    
    # 4. Parecer e Recomendações de Inteligência Artificial
    if ai_recommendation:
        elements.append(Paragraph("4. Diagnóstico e Parecer Técnico de Otimização (IA)", section_style))
        clean_text = ai_recommendation.replace("\n\n", "<br/><br/>").replace("\n", "<br/>")
        elements.append(Paragraph(clean_text, callout_style))
        elements.append(Spacer(1, 10))
        
    # Rodapé de assinatura
    elements.append(Spacer(1, 15))
    sign_text = "Memorial gerado automaticamente pelo Sistema Inteligente de Cálculo e Otimização de Rádio Enlaces."
    elements.append(Paragraph(sign_text, ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.gray)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_csv_report(
    budget_data: Dict[str, Any],
    profile_data: Optional[Dict[str, Any]] = None
) -> str:
    """Gera um arquivo CSV completo com parâmetros, balanço e perfil de elevação."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Seção 1: Cabeçalho
    writer.writerow(["# RELATORIO TECNICO DE RADIO ENLACE"])
    writer.writerow(["Data Geracao", datetime.now().isoformat()])
    writer.writerow([])
    
    # Seção 2: Entradas
    writer.writerow(["# PARAMETROS DE ENTRADA"])
    writer.writerow(["Parametro", "Valor", "Unidade"])
    inp = budget_data.get("inputs", {})
    for k, v in inp.items():
        writer.writerow([k, v, ""])
    writer.writerow([])
    
    # Seção 3: Balanço de Potência
    writer.writerow(["# BALANCO DE POTENCIA (LINK BUDGET)"])
    writer.writerow(["Variavel", "Valor", "Unidade"])
    b = budget_data.get("budget", {})
    for k, v in b.items():
        writer.writerow([k, v, "dB ou dBm"])
    writer.writerow([])
    
    # Seção 4: Confiabilidade
    writer.writerow(["# CONFIABILIDADE E DISPONIBILIDADE"])
    rel = budget_data.get("reliability", {})
    for k, v in rel.items():
        writer.writerow([k, v, ""])
    writer.writerow([])
    
    # Seção 5: Perfil de elevação ponto a ponto
    if profile_data and "points" in profile_data:
        writer.writerow(["# PERFIL DE ELEVACAO E FRESNEL"])
        writer.writerow([
            "distancia_km",
            "terreno_com_curvatura_m",
            "solo_com_obstaculos_m",
            "linha_visada_los_m",
            "fresnel_topo_m",
            "fresnel_base_m",
            "fresnel_60_base_m",
            "raio_fresnel_r1_m",
            "abaulamento_terra_m"
        ])
        for pt in profile_data["points"]:
            writer.writerow([
                pt.get("distance_km"),
                pt.get("terrain_m"),
                pt.get("ground_with_obstacles_m"),
                pt.get("los_m"),
                pt.get("fresnel_top_m"),
                pt.get("fresnel_bottom_m"),
                pt.get("fresnel_60_bottom_m"),
                pt.get("r1_radius_m"),
                pt.get("bulge_m")
            ])
            
    return output.getvalue()
