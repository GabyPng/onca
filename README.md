# onca_lite

## Instalar las dependencias
pip install -r requirements.txt 

## Archivos requeridos
static/data/**tasas_mortalidad_consolidado.csv** <br>
static/mapas/**municipios.geojson** <br>
static/mapas/**estados.geojson**

## Todo está aqui temporalmente
https://estanciasdelfin2025.slack.com/archives/C0991384Y9F/p1755809602432649

## Iniciar el programa de manera local / debbug
cd frontend 
python3 app.py

Link Funcionakl
http://localhost:8085/

## Borrar el proceso
Si el puerto se ocupa:
lsof -i :5001
copiar ID del proceso
kill <PID>

## Version de Docker
Docker version 28.1.1, build 4eba377
Docker Compose version v2.35.1

## Importante usar los comandos recomendados 
Los ocmandos son originalmente soportados para Docker Compose V2, por lo que puede dar problemas si se utilizan otros

**Importante estar dentro de la carpeta onca_lite** <br>
##
docker compose up --build -d

## Inicia todos los servicios
docker compose up -d 

## Detener y eliminar los servicios
docker compose down -d 

## Reiniciar
docker compose restart

## Ver logs
docker compose logs -f
docker compose logs backend
docker compose logs frontend

## Aplicacion
Frontend http://localhost:8085/
Backend http://localhost:8084/

## Acceso externo (no funcional)
Frontend http://alpha.tamps.cinvestav.mx:8085
Backend http://alpha.tamps.cinvestav.mx:8085

docker-composee.yml -- Estam definidos cada servicio con su imagen, puertos en una variable oculta en .env


