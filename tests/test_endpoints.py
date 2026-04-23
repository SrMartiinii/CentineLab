"""
Tests de integración de los endpoints REST.
"""

from fastapi import status


# ── Sanitarios ─────────────────────────────────────────────────────────────

def test_crear_sanitario(client):
    r = client.post("/api/v1/sanitarios/", json={
        "nombre":  "María",
        "apellidos": "Fernández",
        "codigo_profesional": "ENF-100",
        "email":   "maria@hospital.example.com",
        "rol":     "enfermero",
    })
    assert r.status_code == 201
    assert r.json()["codigo_profesional"] == "ENF-100"


def test_crear_sanitario_duplicado(client):
    payload = {
        "nombre": "Pedro",
        "apellidos": "López",
        "codigo_profesional": "ENF-200",
        "email": "pedro@hospital.example.com",
        "rol": "enfermero",
    }
    client.post("/api/v1/sanitarios/", json=payload)
    r = client.post("/api/v1/sanitarios/", json=payload)
    assert r.status_code == 409


def test_desactivar_sanitario(client, enfermero):
    r = client.delete(f"/api/v1/sanitarios/{enfermero.id}")
    assert r.status_code == status.HTTP_204_NO_CONTENT

    detalle = client.get(f"/api/v1/sanitarios/{enfermero.id}")
    assert detalle.json()["activo"] is False


# ── Pacientes ──────────────────────────────────────────────────────────────

def test_crear_paciente(client):
    r = client.post("/api/v1/pacientes/", json={
        "nombre": "Luis",
        "apellidos": "García",
        "nhc": "NHC-001",
        "fecha_nacimiento": "1975-03-20",
    })
    assert r.status_code == 201


def test_nhc_duplicado(client, paciente):
    r = client.post("/api/v1/pacientes/", json={
        "nombre": "Otro",
        "apellidos": "Paciente",
        "nhc": paciente.nhc,
        "fecha_nacimiento": "1990-01-01",
    })
    assert r.status_code == 409


def test_buscar_por_nhc(client, paciente):
    r = client.get(f"/api/v1/pacientes/nhc/{paciente.nhc}")
    assert r.status_code == 200
    assert r.json()["id"] == paciente.id


# ── Peticiones ─────────────────────────────────────────────────────────────

def test_crear_peticion(client, paciente, enfermero, medico):
    r = client.post("/api/v1/peticiones/", json={
        "barcode": "PET-BC-001",
        "motivo": "Control anual",
        "paciente_id": paciente.id,
        "enfermero_id": enfermero.id,
        "medico_id": medico.id,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["estado"] == "pendiente"
    assert data["enfermero"]["id"] == enfermero.id


def test_rol_incorrecto(client, paciente, enfermero, medico):
    """Asignar un médico en la posición de enfermero debe dar 400."""
    r = client.post("/api/v1/peticiones/", json={
        "barcode": "PET-BC-002",
        "paciente_id": paciente.id,
        "enfermero_id": medico.id,     # rol incorrecto
        "medico_id":    enfermero.id,  # rol incorrecto
    })
    assert r.status_code == 400


def test_actualizar_estado(client, peticion):
    r = client.patch(f"/api/v1/peticiones/{peticion.id}", json={"estado": "extraida"})
    assert r.status_code == 200
    assert r.json()["estado"] == "extraida"


# ── Flujo completo de resultado y alerta (lo más importante) ──────────────

def test_resultado_normal_no_genera_alerta(client, muestra):
    r = client.post("/api/v1/resultados/", json={
        "parametro": "potasio",
        "valor": 4.2,
        "unidad": "mEq/L",
        "muestra_id": muestra.id,
    })
    assert r.status_code == 201
    assert r.json()["alerta"] is None


def test_potasio_critico_genera_alerta(client, muestra):
    """K⁺ = 7.5 → alerta CRÍTICA."""
    r = client.post("/api/v1/resultados/", json={
        "parametro": "potasio",
        "valor": 7.5,
        "unidad": "mEq/L",
        "muestra_id": muestra.id,
    })
    assert r.status_code == 201
    alerta = r.json()["alerta"]
    assert alerta is not None
    assert alerta["severidad"] == "critica"


def test_glucosa_critica(client, muestra):
    """Glucosa = 600 mg/dL → alerta crítica."""
    r = client.post("/api/v1/resultados/", json={
        "parametro": "glucosa",
        "valor": 600.0,
        "unidad": "mg/dL",
        "muestra_id": muestra.id,
    })
    assert r.status_code == 201
    assert r.json()["alerta"]["severidad"] == "critica"


def test_valor_negativo_rechazado(client, muestra):
    r = client.post("/api/v1/resultados/", json={
        "parametro": "glucosa",
        "valor": -10.0,
        "unidad": "mg/dL",
        "muestra_id": muestra.id,
    })
    assert r.status_code == 422


def test_listar_alertas(client, muestra):
    client.post("/api/v1/resultados/", json={
        "parametro": "troponina_i",
        "valor": 1.0,
        "unidad": "ng/mL",
        "muestra_id": muestra.id,
    })
    r = client.get("/api/v1/alertas/")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


# ── Endpoints básicos ──────────────────────────────────────────────────────

def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_raiz(client):
    assert "CentineLab" in client.get("/").json()["app"]
