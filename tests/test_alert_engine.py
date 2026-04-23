"""
Tests del motor de alertas y del catálogo de rangos clínicos.

Son los tests más importantes del proyecto: validan que los umbrales
coinciden con los valores de pánico consensuados en laboratorio clínico.
"""

from app.models.alerta import SeveridadAlerta
from app.services.clinical_ranges import (
    CLINICAL_RANGES,
    evaluar_resultado,
    generar_mensaje_alerta,
)


# ── Potasio ────────────────────────────────────────────────────────────────

def test_potasio_critico_alto():
    """K⁺ > 6.5 → riesgo de fibrilación ventricular → CRÍTICA."""
    assert evaluar_resultado("potasio", 7.0) == SeveridadAlerta.critica


def test_potasio_critico_bajo():
    """K⁺ < 2.5 → parálisis muscular, arritmia → CRÍTICA."""
    assert evaluar_resultado("potasio", 2.0) == SeveridadAlerta.critica


def test_potasio_alto_no_critico():
    """K⁺ = 5.8 → fuera del rango 'alto' pero no 'crítico' → ALTA."""
    assert evaluar_resultado("potasio", 5.8) == SeveridadAlerta.alta


def test_potasio_normal():
    assert evaluar_resultado("potasio", 4.0) is None


# ── Glucosa ────────────────────────────────────────────────────────────────

def test_glucosa_hiperglucemia_critica():
    """>500 → sospechar cetoacidosis o coma hiperosmolar."""
    assert evaluar_resultado("glucosa", 550) == SeveridadAlerta.critica


def test_glucosa_hipoglucemia_critica():
    """<40 → riesgo de daño neurológico."""
    assert evaluar_resultado("glucosa", 30) == SeveridadAlerta.critica


def test_glucosa_normal():
    assert evaluar_resultado("glucosa", 95) is None


# ── Troponina (solo límite superior) ──────────────────────────────────────

def test_troponina_elevada():
    assert evaluar_resultado("troponina_i", 0.5) == SeveridadAlerta.critica


def test_troponina_normal():
    assert evaluar_resultado("troponina_i", 0.05) is None


# ── INR ────────────────────────────────────────────────────────────────────

def test_inr_critico():
    """INR > 5 → riesgo hemorrágico alto."""
    assert evaluar_resultado("inr", 5.5) == SeveridadAlerta.critica


def test_inr_terapeutico():
    """INR 2.5 está dentro del rango terapéutico típico → sin alerta."""
    assert evaluar_resultado("inr", 2.5) is None


# ── pH arterial (rango con dos extremos) ──────────────────────────────────

def test_ph_acidosis_grave():
    assert evaluar_resultado("ph_arterial", 7.15) == SeveridadAlerta.critica


def test_ph_alcalosis_grave():
    assert evaluar_resultado("ph_arterial", 7.65) == SeveridadAlerta.critica


def test_ph_normal():
    assert evaluar_resultado("ph_arterial", 7.40) is None


# ── Hemoglobina ───────────────────────────────────────────────────────────

def test_hemoglobina_critica_baja():
    """Hb < 7 → indicación transfusional."""
    assert evaluar_resultado("hemoglobina", 6.5) == SeveridadAlerta.critica


# ── Parámetro desconocido ─────────────────────────────────────────────────

def test_parametro_no_catalogado():
    """Valor de un parámetro que no existe en el catálogo → sin alerta."""
    assert evaluar_resultado("parametro_inventado", 9999) is None


# ── Generación de mensaje ─────────────────────────────────────────────────

def test_mensaje_incluye_nombre_y_valor():
    msg = generar_mensaje_alerta("potasio", 7.0, SeveridadAlerta.critica)
    assert "Potasio" in msg
    assert "7.0" in msg


def test_mensaje_incluye_paciente():
    msg = generar_mensaje_alerta(
        "glucosa", 600, SeveridadAlerta.critica,
        nombre_paciente="García, Ana",
    )
    assert "García, Ana" in msg


def test_mensaje_etiqueta_severidad():
    assert "[CRITICA]" in generar_mensaje_alerta("potasio", 7.0, SeveridadAlerta.critica)
    assert "[ALTA]"    in generar_mensaje_alerta("potasio", 5.8, SeveridadAlerta.alta)


# ── Catálogo ──────────────────────────────────────────────────────────────

def test_catalogo_entradas_validas():
    """Verifica que todas las entradas del catálogo tienen los campos mínimos."""
    for clave, definicion in CLINICAL_RANGES.items():
        assert definicion.get("nombre"), f"Parámetro '{clave}' sin nombre."
        assert "unidad" in definicion,   f"Parámetro '{clave}' sin unidad."
        tiene_rango = any(
            definicion.get(nivel) for nivel in ("critico", "alto", "medio")
        )
        assert tiene_rango, f"Parámetro '{clave}' sin ningún rango definido."
