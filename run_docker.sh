#!/bin/bash
# Script para ejecutar ONCA Lite con Docker Compose
echo "Iniciando ONCA Lite "

# Construir y ejecutar los contenedores
docker compose up --build -d

echo "Contenedores iniciados!"
echo ""
echo " URLs disponibles:"
echo "   Frontend: http://alpha.tamps.cinvestav.mx:8085"
echo "   Backend API: http://alpha.tamps.cinvestav.mx:8084"
echo "   Health Check: http://alpha.tamps.cinvestav.mx:8084/health"
echo ""
echo "Comandos útiles:"
echo "   Ver logs: docker compose logs -f"
echo "   Parar servicios: docker compose down"
echo "   Reiniciar: docker compose restart"
