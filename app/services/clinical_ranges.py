"""
Catálogo de rangos clínicos — CentineLab
─────────────────────────────────────────

Este módulo centraliza los valores de referencia y los umbrales de pánico
("panic values" / "critical values") que disparan las alertas del sistema.

Los umbrales se basan en:
  · Guías del Laboratorio Clínico del Sistema Nacional de Salud (SESPAS)
  · Recomendaciones de la SEQC (Sociedad Española de Medicina de Laboratorio)
  · Valores de pánico consensuados en la mayoría de hospitales terciarios
    españoles (publicados en los Procedimientos Normalizados de Trabajo).

Niveles de severidad y acción asociada:
    CRITICA → notificación inmediata (email + webhook). Riesgo vital
              inmediato si no se actúa en minutos. Típico del "Código Fuga"
              de laboratorio: llamada telefónica directa al facultativo.
    ALTA    → notificación en < 5 min. Alteración relevante que requiere
              valoración urgente pero no compromete la vida de forma inmediata.
    MEDIA   → notificación diferida (próxima revisión). Desviación del rango
              de normalidad sin gravedad aguda.

Reglas del motor:
  · El parámetro se busca por clave normalizada (minúsculas, sin tildes).
  · Se evalúa de mayor a menor gravedad: si cae fuera del rango 'critico',
    la alerta es CRÍTICA (aunque también esté fuera del rango 'alto').
  · Si no hay definición para ese parámetro, NO se genera alerta
    (el motor es permisivo: mejor no alertar que dar falsos positivos).

TODO (próximas versiones):
  · Rangos diferenciados por sexo (p. ej. hemoglobina, creatinina, ferritina).
  · Rangos pediátricos y neonatales (valores muy distintos en <18 años).
  · Rangos configurables por centro desde BBDD (tabla 'rangos_centro').
  · Soporte para unidades alternativas con conversión automática
    (p. ej. glucosa en mg/dL ↔ mmol/L, creatinina en mg/dL ↔ µmol/L).
  · Integración con LOINC para identificar parámetros de forma estándar.
"""

from typing import Optional

from app.models.alerta import SeveridadAlerta


# ══════════════════════════════════════════════════════════════════════════
#  Catálogo de parámetros
# ══════════════════════════════════════════════════════════════════════════
#
# Estructura de cada entrada:
#   "clave": {
#       "nombre":   Texto legible para mostrar en alertas y emails.
#       "unidad":   Unidad SI o convencional esperada por el analizador.
#       "contexto": Breve nota clínica que explica por qué importa.
#       "critico":  (min, max) — fuera de este rango → severidad CRÍTICA.
#       "alto":     (min, max) — fuera → severidad ALTA.
#       "medio":    (min, max) — fuera → severidad MEDIA.
#
#   Cualquier nivel puede ser None si no aplica. None en min o max indica
#   que no hay límite por ese lado (p. ej. troponina solo tiene máximo).
#

CLINICAL_RANGES: dict[str, dict] = {

    # ──────────────────────────────────────────────────────────────────────
    #  ELECTROLITOS
    # ──────────────────────────────────────────────────────────────────────

    "potasio": {
        "nombre":   "Potasio (K⁺)",
        "unidad":   "mEq/L",
        "contexto": (
            "K⁺ <2.5 → arritmia ventricular, parálisis muscular. "
            "K⁺ >6.5 → ondas T picudas, riesgo de fibrilación ventricular. "
            "Falsa hiperpotasemia frecuente por hemólisis de la muestra."
        ),
        "critico": (2.5, 6.5),
        "alto":    (3.0, 5.5),
        "medio":   None,
    },

    "sodio": {
        "nombre":   "Sodio (Na⁺)",
        "unidad":   "mEq/L",
        "contexto": (
            "Hiponatremia <120 → edema cerebral, convulsiones. "
            "Hipernatremia >160 → deshidratación grave, alteración consciencia. "
            "Corrección demasiado rápida puede provocar mielinolisis pontina."
        ),
        "critico": (120, 160),
        "alto":    (130, 150),
        "medio":   None,
    },

    "calcio_corregido": {
        "nombre":   "Calcio corregido (por albúmina)",
        "unidad":   "mg/dL",
        "contexto": (
            "Hipocalcemia <7 → tetania, Chvostek/Trousseau, QT largo. "
            "Hipercalcemia >14 → crisis hipercalcémica, riesgo arritmia. "
            "Siempre valorar junto a la albúmina (falsa hipocalcemia si hipoalbuminemia)."
        ),
        "critico": (7.0, 14.0),
        "alto":    (8.0, 11.0),
        "medio":   None,
    },

    "magnesio": {
        "nombre":   "Magnesio",
        "unidad":   "mg/dL",
        "contexto": (
            "Hipomagnesemia frecuente en alcoholismo crónico y diuréticos. "
            "Se asocia a hipopotasemia refractaria e hipocalcemia."
        ),
        "critico": (1.0, 4.5),
        "alto":    (1.5, 3.0),
        "medio":   None,
    },

    "fosforo": {
        "nombre":   "Fósforo",
        "unidad":   "mg/dL",
        "contexto": (
            "Hiperfosfatemia típica en ERC avanzada → calcificación vascular. "
            "Hipofosfatemia grave en realimentación y cetoacidosis."
        ),
        "alto":    (1.0, 7.0),
        "medio":   (2.0, 5.0),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  METABOLISMO / GLUCEMIA
    # ──────────────────────────────────────────────────────────────────────

    "glucosa": {
        "nombre":   "Glucosa",
        "unidad":   "mg/dL",
        "contexto": (
            "Hipoglucemia <40 → coma, daño neurológico irreversible. "
            "Hiperglucemia >500 → sospechar cetoacidosis o coma hiperosmolar. "
            "En paciente sintomático, actuar independientemente del valor exacto."
        ),
        "critico": (40, 500),
        "alto":    (60, 400),
        "medio":   (70, 250),
    },

    "hba1c": {
        "nombre":   "Hemoglobina glicosilada (HbA1c)",
        "unidad":   "%",
        "contexto": (
            "Control glucémico últimos 2-3 meses. "
            ">10% indica muy mal control, riesgo elevado de complicaciones."
        ),
        "medio":   (None, 10.0),
    },

    "lactato": {
        "nombre":   "Lactato",
        "unidad":   "mmol/L",
        "contexto": (
            "Marcador de hipoperfusión tisular. "
            ">4 → shock, sepsis grave, isquemia mesentérica. "
            "Seguimiento cada 2-4h en paciente séptico (clearance de lactato)."
        ),
        "critico": (None, 4.0),
        "alto":    (None, 2.0),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  CARDIOPATÍA ISQUÉMICA / INSUFICIENCIA CARDÍACA
    # ──────────────────────────────────────────────────────────────────────

    "troponina_i": {
        "nombre":   "Troponina I (de alta sensibilidad)",
        "unidad":   "ng/mL",
        "contexto": (
            "Marcador de necrosis miocárdica. Cualquier elevación debe ponerse "
            "en contexto clínico (dolor torácico, ECG, cinética). "
            "Umbral de pánico laboratorial: >0.4 ng/mL."
        ),
        # TODO: el umbral "correcto" depende del percentil 99 del ensayo
        # del laboratorio (habitualmente entre 0.04 y 0.5 ng/mL según reactivo).
        # Debería configurarse por centro desde BBDD.
        "critico": (None, 0.4),
    },

    "nt_probnp": {
        "nombre":   "NT-proBNP",
        "unidad":   "pg/mL",
        "contexto": (
            "Marcador de insuficiencia cardíaca. "
            ">2000 sugiere IC aguda descompensada. "
            "Interpretar según edad y función renal."
        ),
        "alto":    (None, 2000),
        "medio":   (None, 450),
    },

    "dimero_d": {
        "nombre":   "Dímero D",
        "unidad":   "ng/mL FEU",
        "contexto": (
            "Útil para DESCARTAR TEP/TVP en pacientes de baja probabilidad. "
            "Valor elevado es inespecífico: edad, embarazo, inflamación, cáncer."
        ),
        "medio":   (None, 500),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  HEMOGRAMA
    # ──────────────────────────────────────────────────────────────────────

    "hemoglobina": {
        "nombre":   "Hemoglobina",
        "unidad":   "g/dL",
        "contexto": (
            "<7 → indicación transfusional en paciente estable (según criterio). "
            "<5 → riesgo vital por insuficiencia cardíaca/shock hipoxémico. "
            ">20 → policitemia vera, riesgo trombótico."
        ),
        # TODO: diferenciar rangos por sexo (H: 13.5-17.5, M: 12-15.5)
        "critico": (7.0, 20.0),
        "alto":    (8.0, 18.0),
    },

    "hematocrito": {
        "nombre":   "Hematocrito",
        "unidad":   "%",
        "critico": (20.0, 60.0),
        "alto":    (30.0, 55.0),
    },

    "leucocitos": {
        "nombre":   "Leucocitos totales",
        "unidad":   "/μL",
        "contexto": (
            "Leucopenia <2000 → aplasia medular, sepsis grave, quimioterapia. "
            "Leucocitosis >30000 → reacción leucemoide, leucemia aguda, sepsis."
        ),
        "critico": (1000, 50000),
        "alto":    (2000, 30000),
        "medio":   (3500, 12000),
    },

    "neutrofilos_absolutos": {
        "nombre":   "Neutrófilos absolutos",
        "unidad":   "/μL",
        "contexto": (
            "Neutropenia <500 → aislamiento protector, riesgo de sepsis. "
            "Especialmente relevante en paciente oncohematológico. "
            "Neutropenia febril = emergencia médica."
        ),
        "critico": (500, None),
        "alto":    (1000, None),
    },

    "plaquetas": {
        "nombre":   "Plaquetas",
        "unidad":   "/μL",
        "contexto": (
            "<20000 → riesgo hemorrágico espontáneo, valorar transfusión. "
            "<50000 → contraindicación relativa para procedimientos invasivos. "
            ">1.000.000 → trombocitosis esencial, riesgo trombótico."
        ),
        "critico": (20000, 1000000),
        "alto":    (50000, 800000),
        "medio":   (100000, 500000),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  COAGULACIÓN
    # ──────────────────────────────────────────────────────────────────────

    "inr": {
        "nombre":   "INR",
        "unidad":   "",
        "contexto": (
            "Monitoriza tratamiento con anticoagulantes orales (Sintrom/warfarina). "
            ">5 → riesgo hemorrágico alto, considerar vitamina K. "
            "Rango terapéutico habitual: 2.0-3.0 (FA no valvular), 2.5-3.5 (prótesis)."
        ),
        "critico": (None, 5.0),
        "alto":    (None, 3.5),
    },

    "ttpa": {
        "nombre":   "TTPA (tiempo tromboplastina parcial activada)",
        "unidad":   "segundos",
        "contexto": (
            "Monitoriza heparina no fraccionada. "
            "TTPA prolongado aislado → déficit factores vía intrínseca."
        ),
        "alto":    (None, 100),
    },

    "fibrinogeno": {
        "nombre":   "Fibrinógeno",
        "unidad":   "mg/dL",
        "contexto": (
            "<100 → CID, fibrinólisis, riesgo hemorrágico. "
            "Reactante de fase aguda: se eleva en infecciones e inflamación."
        ),
        "critico": (100, None),
        "alto":    (150, 700),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  FUNCIÓN RENAL
    # ──────────────────────────────────────────────────────────────────────

    "creatinina": {
        "nombre":   "Creatinina",
        "unidad":   "mg/dL",
        "contexto": (
            "Aumento agudo → FRA (fracaso renal agudo). "
            "Si aumenta >0.3 mg/dL en 48h o >1.5x basal → criterio AKI (KDIGO). "
            "Valorar siempre el filtrado glomerular estimado (FGe)."
        ),
        # TODO: calcular FGe con CKD-EPI e incluir como alerta independiente.
        # TODO: rangos distintos por sexo (H: <1.3, M: <1.1 habitualmente).
        "critico": (None, 10.0),
        "alto":    (None, 4.0),
        "medio":   (None, 1.5),
    },

    "urea": {
        "nombre":   "Urea",
        "unidad":   "mg/dL",
        "contexto": (
            "Aumenta en FRA, deshidratación, hemorragia digestiva alta. "
            "Ratio urea/creatinina >40 orienta a causa prerrenal."
        ),
        "alto":    (None, 200),
        "medio":   (None, 50),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  FUNCIÓN HEPÁTICA
    # ──────────────────────────────────────────────────────────────────────

    "bilirrubina_total": {
        "nombre":   "Bilirrubina total",
        "unidad":   "mg/dL",
        "contexto": (
            "Ictericia clínica visible desde ~2.5 mg/dL. "
            ">15 → insuficiencia hepática, colestasis, hemólisis grave."
        ),
        "alto":    (None, 15.0),
        "medio":   (None, 1.2),
    },

    "alt": {
        "nombre":   "ALT (GPT)",
        "unidad":   "U/L",
        "contexto": (
            "Marcador de citolisis hepática (más específico que AST). "
            ">1000 → hepatitis aguda (vírica, tóxica, isquémica)."
        ),
        "alto":    (None, 500),
        "medio":   (None, 40),
    },

    "ast": {
        "nombre":   "AST (GOT)",
        "unidad":   "U/L",
        "contexto": (
            "Menos específica hepática: se eleva también en daño muscular y cardíaco. "
            "Ratio AST/ALT >2 sugiere hepatopatía alcohólica."
        ),
        "alto":    (None, 500),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  INFECCIÓN / INFLAMACIÓN
    # ──────────────────────────────────────────────────────────────────────

    "pcr": {
        "nombre":   "Proteína C reactiva",
        "unidad":   "mg/L",
        "contexto": (
            "Reactante de fase aguda. "
            ">100 → infección bacteriana probable (no exclusivo). "
            "Inespecífica: también elevada en trauma, IAM, cáncer."
        ),
        "alto":    (None, 100),
        "medio":   (None, 5),
    },

    "procalcitonina": {
        "nombre":   "Procalcitonina",
        "unidad":   "ng/mL",
        "contexto": (
            "Más específica que PCR para infección bacteriana y sepsis. "
            ">2 → probable sepsis. "
            "Útil para guiar duración de antibioterapia."
        ),
        "alto":    (None, 2.0),
        "medio":   (None, 0.5),
    },

    # ──────────────────────────────────────────────────────────────────────
    #  GASOMETRÍA ARTERIAL
    # ──────────────────────────────────────────────────────────────────────

    "ph_arterial": {
        "nombre":   "pH arterial",
        "unidad":   "",
        "contexto": (
            "Acidosis grave <7.20 o alcalosis grave >7.60 son emergencias. "
            "Interpretar siempre junto a pCO₂ y HCO₃⁻."
        ),
        "critico": (7.20, 7.60),
        "alto":    (7.30, 7.50),
    },

    "bicarbonato": {
        "nombre":   "Bicarbonato (HCO₃⁻)",
        "unidad":   "mEq/L",
        "contexto": (
            "<10 → acidosis metabólica grave (cetoacidosis, acidosis láctica). "
            ">40 → alcalosis metabólica (vómitos, diuréticos)."
        ),
        "critico": (10.0, 40.0),
        "alto":    (18.0, 32.0),
    },
}


# ══════════════════════════════════════════════════════════════════════════
#  Funciones auxiliares del motor
# ══════════════════════════════════════════════════════════════════════════

def _fuera_de_rango(valor: float, rango: Optional[tuple]) -> bool:
    """Comprueba si un valor cae fuera de un rango (min, max)."""
    if rango is None:
        return False
    minimo, maximo = rango
    if minimo is not None and valor < minimo:
        return True
    if maximo is not None and valor > maximo:
        return True
    return False


def evaluar_resultado(parametro: str, valor: float) -> Optional[SeveridadAlerta]:
    """
    Evalúa un valor contra el catálogo y devuelve la severidad más grave
    que se cumple, o None si el valor está dentro de todos los rangos normales.

    Se evalúa de mayor a menor gravedad (critico → alto → medio) para asegurar
    que una alerta crítica no se "degrade" a alta.
    """
    definicion = CLINICAL_RANGES.get(parametro)
    if definicion is None:
        # Parámetro no catalogado: el motor no alerta
        # (decisión consciente para evitar falsos positivos)
        return None

    if _fuera_de_rango(valor, definicion.get("critico")):
        return SeveridadAlerta.critica
    if _fuera_de_rango(valor, definicion.get("alto")):
        return SeveridadAlerta.alta
    if _fuera_de_rango(valor, definicion.get("medio")):
        return SeveridadAlerta.media

    return None


def generar_mensaje_alerta(
    parametro: str,
    valor: float,
    severidad: SeveridadAlerta,
    nombre_paciente: str = "",
) -> str:
    """
    Construye el mensaje legible que aparecerá en el email y en el registro de alerta.

    Ejemplo:
        "[CRITICA] Troponina I: 0.85 ng/mL — Paciente: García López, Juan"
    """
    definicion = CLINICAL_RANGES.get(parametro, {})
    nombre_param = definicion.get("nombre", parametro)
    unidad = definicion.get("unidad", "")

    etiqueta = {
        SeveridadAlerta.critica: "[CRITICA]",
        SeveridadAlerta.alta:    "[ALTA]",
        SeveridadAlerta.media:   "[MEDIA]",
    }[severidad]

    mensaje = f"{etiqueta} {nombre_param}: {valor} {unidad}".strip()
    if nombre_paciente:
        mensaje += f" — Paciente: {nombre_paciente}"

    return mensaje
