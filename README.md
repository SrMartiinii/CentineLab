# CentineLab

> Sistema backend de vigilancia clínica inteligente. Detecta valores críticos
> en analíticas de sangre y notifica automáticamente al personal sanitario
> asignado al paciente.

![status](https://img.shields.io/badge/status-en_desarrollo-yellow)
![python](https://img.shields.io/badge/python-3.12-blue)
![fastapi](https://img.shields.io/badge/FastAPI-0.115-009688)
[![tests](https://github.com/SrMartiinii/CentineLab/actions/workflows/tests.yml/badge.svg)](https://github.com/SrMartiinii/CentineLab/actions/workflows/tests.yml)

---

## El problema

En la mayoría de centros sanitarios, cuando un analizador de laboratorio
detecta un valor crítico (p. ej. un potasio de 7.5 mEq/L), el circuito
habitual pasa por:

1. El técnico del laboratorio ve la alarma del analizador.
2. Busca en el LIS qué médico firmó la petición.
3. Llama por teléfono al busca o al servicio.
4. El médico debe localizar al paciente y valorar.

Ese circuito **depende por completo de una persona disponible en el lab** y
de que el contacto del facultativo esté al día. En guardias, noches o fines
de semana, se traduce en **minutos u horas de retraso** en situaciones donde
el tiempo es crítico: hiperpotasemia severa, hipoglucemia, troponinas
positivas, neutropenia febril, INR disparado…

## La propuesta

CentineLab automatiza la trazabilidad y la comunicación de valores de pánico:

1. La petición se genera con un código de barras que identifica paciente +
   enfermero + médico responsables.
2. Cuando llega un resultado al sistema (idealmente desde el middleware del
   analizador), el motor lo evalúa contra los umbrales clínicos.
3. Si está fuera de rango, se crea una alerta y se notifica por **email**
   y **webhook** al enfermero y al médico asignados, **con trazabilidad
   completa** (qué se envió, cuándo, a quién, si llegó).

No pretende sustituir al criterio clínico: pretende garantizar que **la
alerta llega**, sin depender de si el técnico tuvo tiempo de llamar.

## Arquitectura

```
┌──────────────┐   ┌─────────────────┐   ┌──────────────┐
│  Petición    │   │                 │   │ Email SMTP   │
│ (barcode)    │──►│                 │──►│ (enfermero   │
└──────────────┘   │                 │   │  + médico)   │
                   │    FastAPI      │   └──────────────┘
┌──────────────┐   │   + motor de    │
│ Resultado    │──►│     alertas     │   ┌──────────────┐
│ analítico    │   │                 │──►│ Webhook      │
└──────────────┘   │                 │   │ Slack/Teams  │
                   └────────┬────────┘   └──────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ SQLAlchemy ORM  │
                   │ SQLite / PG     │
                   └─────────────────┘
```

**Modelos:** `Paciente`, `Sanitario`, `Peticion`, `Muestra`, `Resultado`,
`Alerta`.

**Motor clínico:** `app/services/clinical_ranges.py` contiene el catálogo
de ~25 parámetros con sus umbrales crítico/alto/medio y una nota de
contexto clínico por cada uno.

## Stack

| Capa           | Tecnología                    |
| -------------- | ----------------------------- |
| API REST       | FastAPI                       |
| Validación     | Pydantic v2                   |
| ORM            | SQLAlchemy 2.x                |
| BBDD (dev)     | SQLite                        |
| BBDD (prod)    | PostgreSQL                    |
| Notificaciones | SMTP + Webhooks (httpx)       |
| Testing        | pytest + TestClient           |
| Despliegue     | Docker + docker-compose       |

## Arrancar en local

```bash
# 1. Clonar y entrar
git clone https://github.com/<tu-usuario>/centinelab.git
cd centinelab

# 2. Entorno virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env

# 5. Arrancar la API
uvicorn app.main:app --reload
```

Documentación interactiva en: `http://localhost:8000/docs`

### Con Docker

```bash
docker-compose up --build
```

## Flujo mínimo de prueba

```bash
# 1. Crear enfermero y médico
curl -X POST http://localhost:8000/api/v1/sanitarios/ \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Ana","apellidos":"García","codigo_profesional":"ENF-1",
       "email":"ana@test.com","rol":"enfermero"}'

# 2. Crear paciente
# 3. Crear petición vinculando paciente + enfermero + médico
# 4. Registrar muestra
# 5. POSTear un resultado con valor crítico
#    → se crea la alerta y se intenta notificar
```

Ver [`docs/ejemplos.http`](./docs/ejemplos.http) para una secuencia completa.
*(pendiente de subir)*

## Tests

```bash
pytest
```

Cobertura actual centrada en:

- Evaluación de los umbrales clínicos (parámetro por parámetro).
- Flujo completo HTTP: crear recurso → registrar resultado → verificar
  que la alerta aparece en la respuesta y en `GET /alertas`.

## Estado del proyecto

| Fase                                                     | Estado        |
| -------------------------------------------------------- | ------------- |
| Diseño de arquitectura y modelos                         | ✅ Hecho      |
| Motor de alertas + notificaciones (email / webhook)      | ✅ Hecho      |
| Suite de tests y documentación OpenAPI                   | 🟡 En curso   |
| Migraciones Alembic + despliegue PostgreSQL              | 🟡 En curso   |
| Autenticación JWT                                        | ⚪ Pendiente  |
| Integración HL7 v2 / FHIR para recepción de resultados   | ⚪ Pendiente  |
| Cola asíncrona para notificaciones (Celery/RQ)           | ⚪ Pendiente  |
| Rangos pediátricos y diferenciados por sexo              | ⚪ Pendiente  |
| Escalado automático de alertas sin confirmar             | ⚪ Pendiente  |
| Panel web de auditoría (frontend)                        | ⚪ Pendiente  |

## Decisiones de diseño comentadas

Algunas decisiones que merecen mención explícita:

- **Motor permisivo ante parámetros desconocidos.** Si llega un resultado
  con un `parametro` que no existe en el catálogo, no se genera alerta.
  Preferible falso negativo a falso positivo: una alerta espuria genera
  "alert fatigue" y hace que el personal deje de leerlas.
- **Soft-delete de sanitarios.** Un sanitario no se borra, se marca
  `activo=False`. Así se preserva la integridad referencial con peticiones
  y alertas históricas (auditoría).
- **La alerta se persiste antes de notificar.** Si falla el SMTP, la
  alerta queda en BBDD con `notificado=False` y un admin puede reintentar.
  El sistema nunca "pierde" una alerta silenciosamente.
- **Los umbrales viven en código, no en BBDD.** Decisión temporal para la
  v0.2. Para un despliegue real deben ser configurables por centro
  (ver TODO en `clinical_ranges.py`).

## Limitaciones conocidas (honestidad)

- No hay autenticación todavía — no debe exponerse a internet como está.
- Las notificaciones son síncronas: un SMTP lento bloquea la respuesta
  HTTP del endpoint de resultados.
- No hay migraciones con Alembic — el esquema se crea con
  `Base.metadata.create_all` al arrancar, suficiente para desarrollo.
- No se gestiona la diferenciación de rangos por sexo, edad o
  embarazo, que sí afecta en clínica real.

Todos estos puntos están marcados como `TODO` en el código.

## Contexto del autor

Proyecto personal construido para mi portfolio de **healthtech**. Combina:

- Experiencia real en el ámbito sanitario (gestión de circuitos clínicos,
  trazabilidad de muestras, familiaridad con valores de pánico).
- Conocimientos de desarrollo (FastAPI, SQLAlchemy, Docker) adquiridos
  durante el ciclo DAM y ampliados en este proyecto.

El diseño clínico se basa en prácticas reales de laboratorio; el código
Python es mi terreno de aprendizaje — los `TODO` reflejan dónde sé que
hay trabajo pendiente para llegar a producción.

## Licencia

MIT — úsalo, fórkalo, rómpelo.
