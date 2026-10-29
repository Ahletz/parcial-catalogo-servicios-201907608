FROM python:3.13-slim-bookworm@sha256:5024f48ba9441d4b13a95d3945abc6365538e3a31109833367a1923523c6efed

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src:/app
WORKDIR /app/src
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --index-url https://pypi.org/simple -r /app/requirements.txt
RUN useradd --uid 1000 --create-home app
RUN install -d -o app -g app /app/staticfiles /app/privado/adjuntos
COPY src /app/src
COPY tests /app/tests
COPY scripts /app/scripts
COPY data/CatalogoServicios.xlsx /app/data/CatalogoServicios.xlsx
COPY ENUNCIADO.md /fuentes/ENUNCIADO.md
COPY data/CatalogoServicios.xlsx /fuentes/CatalogoServicios.xlsx
USER app
# Solo configuración sintética de build; collectstatic no necesita conexión BD.
RUN DJANGO_SECRET_KEY=publica-sintetica-solo-build DB_NAME=build DB_USER=build python manage.py collectstatic --noinput
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--access-logfile", "/dev/null"]
