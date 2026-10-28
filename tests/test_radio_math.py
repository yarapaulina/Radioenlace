"""
Testes Unitários e de Integração para a Aplicação RadioLink Pro
"""

import pytest
from app.core.radio_math import (
    calculate_wavelength,
    calculate_fspl,
    calculate_eirp,
    calculate_fresnel_radius,
    calculate_fresnel_midpoint_radius,
    calculate_earth_bulge,
    calculate_rain_attenuation,
    calculate_atmospheric_gas_attenuation,
    calculate_availability_and_reliability,
    generate_link_elevation_profile,
    compute_complete_link_budget
)
from app.core.optimizer import optimize_radio_link
from app.core.report_generator import generate_pdf_report, generate_csv_report
from fastapi.testclient import TestClient
from app.main import app


def test_calculate_wavelength():
    wl_5ghz = calculate_wavelength(5800.0)
    assert 0.05 < wl_5ghz < 0.055
    wl_10ghz = calculate_wavelength(10000.0)
    assert round(wl_10ghz, 4) == 0.03


def test_calculate_fspl():
    # 10 km a 5800 MHz: ~127.7 dB
    fspl = calculate_fspl(10.0, 5800.0)
    assert 127.0 < fspl < 128.5
    
    # 1 km a 1000 MHz: 32.44 + 20*log10(1) + 20*log10(1000) = 32.44 + 0 + 60 = 92.44 dB
    fspl_1km = calculate_fspl(1.0, 1000.0)
    assert round(fspl_1km, 2) == 92.44


def test_calculate_eirp():
    # Tx Power 20 dBm, Cabo 1.5 dB, Antena 25 dBi => 43.5 dBm
    eirp = calculate_eirp(20.0, 1.5, 25.0)
    assert eirp == 43.5


def test_calculate_fresnel_and_bulge():
    r1_mid = calculate_fresnel_midpoint_radius(10.0, 5800.0)
    assert 10.0 < r1_mid < 13.0
    
    bulge = calculate_earth_bulge(5.0, 10.0, 1.33333)
    assert 1.2 < bulge < 1.6


def test_complete_link_budget():
    params = {
        "frequency_mhz": 5800.0,
        "distance_km": 10.0,
        "tx_power_dbm": 20.0,
        "tx_cable_loss_db": 1.5,
        "tx_antenna_gain_dbi": 25.0,
        "rx_antenna_gain_dbi": 25.0,
        "rx_cable_loss_db": 1.5,
        "rx_sensitivity_dbm": -75.0,
        "misc_losses_db": 0.0,
        "k_factor": 1.33333,
        "rain_rate_mmh": 42.0,
        "polarization": "H",
        "enable_rain": True,
        "enable_gas": True
    }
    result = compute_complete_link_budget(params)
    assert "budget" in result
    assert "reliability" in result
    assert "fresnel" in result
    
    b = result["budget"]
    # RSL deve ser aproximadamente: 43.5 - 127.7 - 0.2 + 25 - 1.5 = ~ -60.9 dBm
    assert -70.0 < b["rsl_dbm"] < -55.0
    # Margem deve ser RSL - (-75) = ~ 14.1 dB
    assert 10.0 < b["fade_margin_db"] < 25.0
    assert result["reliability"]["availability_percent"] > 99.0


def test_optimizer():
    params = {
        "frequency_mhz": 5800.0,
        "distance_km": 15.0,
        "tx_power_dbm": 18.0,
        "tx_cable_loss_db": 1.5,
        "tx_antenna_gain_dbi": 22.0,
        "tx_tower_height_m": 12.0,
        "tx_terrain_altitude_m": 20.0,
        "rx_antenna_gain_dbi": 22.0,
        "rx_cable_loss_db": 1.5,
        "rx_sensitivity_dbm": -75.0,
        "rx_tower_height_m": 12.0,
        "rx_terrain_altitude_m": 25.0,
        "k_factor": 1.33333,
        "rain_rate_mmh": 42.0,
        "polarization": "H",
        "enable_rain": True,
        "enable_gas": True
    }
    opt = optimize_radio_link(params, target_fade_margin_db=25.0, target_availability_pct=99.999)
    assert opt["optimized_summary"]["fade_margin_db"] > opt["original_summary"]["fade_margin_db"]
    assert len(opt["recommendations"]["action_items"]) > 0


def test_reports_generation():
    params = {
        "frequency_mhz": 5800.0,
        "distance_km": 10.0,
        "tx_power_dbm": 20.0,
        "tx_cable_loss_db": 1.5,
        "tx_antenna_gain_dbi": 25.0,
        "rx_antenna_gain_dbi": 25.0,
        "rx_cable_loss_db": 1.5,
        "rx_sensitivity_dbm": -75.0,
        "misc_losses_db": 0.0,
        "k_factor": 1.33333,
        "rain_rate_mmh": 42.0,
        "polarization": "H",
        "enable_rain": True,
        "enable_gas": True
    }
    budget = compute_complete_link_budget(params)
    profile = generate_link_elevation_profile(
        distance_km=10.0,
        frequency_mhz=5800.0,
        tx_tower_height_m=20.0,
        rx_tower_height_m=20.0
    )
    
    # PDF
    pdf_bytes = generate_pdf_report(budget, profile, "Recomendações de teste")
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b'%PDF')
    
    # CSV
    csv_str = generate_csv_report(budget, profile)
    assert "PARAMETROS DE ENTRADA" in csv_str
    assert "BALANCO DE POTENCIA" in csv_str


def test_fastapi_endpoints():
    client = TestClient(app)
    
    # Home
    resp = client.get("/")
    assert resp.status_code == 200
    assert "RadioLink Pro" in resp.text  # build React ou página de aviso
    
    # Presets
    resp_presets = client.get("/api/presets")
    assert resp_presets.status_code == 200
    assert len(resp_presets.json()) >= 4
    
    # Calculate
    calc_payload = {
        "frequency_mhz": 5800.0,
        "distance_km": 10.0,
        "tx_power_dbm": 20.0,
        "tx_cable_loss_db": 1.5,
        "tx_antenna_gain_dbi": 25.0,
        "tx_tower_height_m": 20.0,
        "tx_terrain_altitude_m": 50.0,
        "rx_antenna_gain_dbi": 25.0,
        "rx_cable_loss_db": 1.5,
        "rx_sensitivity_dbm": -75.0,
        "rx_tower_height_m": 20.0,
        "rx_terrain_altitude_m": 80.0,
        "misc_losses_db": 0.0,
        "k_factor": 1.33333,
        "rain_rate_mmh": 42.0,
        "polarization": "H",
        "enable_rain": True,
        "enable_gas": True,
        "obstacles": []
    }
    resp_calc = client.post("/api/calculate", json=calc_payload)
    assert resp_calc.status_code == 200
    data = resp_calc.json()
    assert "budget_data" in data
    assert "profile_data" in data
    
    # Optimize
    resp_opt = client.post("/api/optimize", json={
        "link_params": calc_payload,
        "target_fade_margin_db": 25.0,
        "target_availability_pct": 99.999
    })
    assert resp_opt.status_code == 200
    assert "recommendations" in resp_opt.json()
    
    # AI Consulting
    resp_ai = client.post("/api/ai-consulting", json={
        "link_params": calc_payload,
        "user_query": "Avalie a margem de desvanecimento deste link."
    })
    assert resp_ai.status_code == 200
    assert "response" in resp_ai.json()
    
    # Export PDF
    resp_pdf = client.post("/api/export/pdf", json=calc_payload)
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    
    # Export CSV
    resp_csv = client.post("/api/export/csv", json=calc_payload)
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]

    # Elevation Profile (LINKPlanner style)
    resp_elev = client.post("/api/elevation-profile", json={
        "lat1": -23.5615,
        "lon1": -46.6559,
        "lat2": -23.4285,
        "lon2": -46.6200,
        "num_points": 20
    })
    assert resp_elev.status_code == 200
    elev_data = resp_elev.json()
    assert "elevations_m" in elev_data
    assert len(elev_data["elevations_m"]) == 21
    assert elev_data["distance_km"] > 0
    assert "bearing_ab_deg" in elev_data

    # Geocode
    resp_geo = client.post("/api/geocode", json={"query": "Sao Paulo"})
    assert resp_geo.status_code == 200
    assert "results" in resp_geo.json()
