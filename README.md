# dds-pdf-ingest

TP Desarrollo de Software · UTN San Rafael · 2026.
Equipo: Tomás Caratti y Felipe Mora.

Base inicial ejecutable; las mejoras y experimentos se siguen en issues.
[Inicio, contratos, ejecución y reparto de tareas](https://github.com/TomiCaratti13/dds-pdf-platform).
[Issues](https://github.com/TomiCaratti13/dds-pdf-ingest/issues).

La etapa 1 original se conserva en
[proyecto-software](https://github.com/felipemorarodrigo11-web/proyecto-software).

[Tablero del equipo](https://github.com/users/TomiCaratti13/projects/3) · [Reparto y dependencias](https://github.com/TomiCaratti13/dds-pdf-platform/blob/main/docs/team-plan.md)

## Desarrollo local

`uv sync --locked` y `uv run --frozen python -m pytest -q`.
Crear el directorio de DB_PATH si se usa disco. Copiar .env.example a .env y ajustar URLs locales.
Iniciar con `uv run --frozen python -m uvicorn app.main:app --port 8001`. Swagger en /docs.
