# Mapa Folium Interactivo

## Características principales

### Mapa Interactivo
- Visualización choropleth (colores por intensidad de datos)
- Esquema de colores YlOrRd (Amarillo-Naranja-Rojo)
- Controles de zoom y navegación

### Datos Mostrados
- **Escalas disponibles:**
  - Conteos (escala 1)
  - Tasa cruda por 10,000 habitantes (escala 2)
  - ASMR por 100,000 habitantes (escala 3)

- **Filtros aplicables:**
  - Año específico
  - Sexo (Hombres, Mujeres, Ambos)
  - Rango de edad personalizable
  - Código CIE10

### Funciones Interactivas
- **Tooltips:** Al pasar el mouse sobre un estado muestra el nombre
- **Popups:** Al hacer clic en un marcador muestra información detallada:
  - Nombre del estado
  - Año, sexo y rango de edad
  - Valor de la tasa de mortalidad
  - Código CIE10
- **Leyenda:** Muestra la escala de colores con unidades
- **Pantalla completa:** Botón para ver el mapa a pantalla completa

## Archivos Modificados

### 1. `src/funciones.py`
- **Nueva función:** `generar_mapa_folium()`
- **Actualización:** `generar_producto_consolidado()` para incluir 'mapa_folium'

### 2. `frontend/app.py`
- **Importación:** Agregada `generar_mapa_folium` a las importaciones
- **Nueva ruta:** Manejo del producto "Mapa Folium" en la función `index()`
- **Contenido:** Actualizada `determinar_contenido_mostrar()` para manejar el nuevo producto

### 3. `frontend/templates/index.html`
- **Nueva opción:** "Mapa Folium" agregado al selector de productos
- **JavaScript:** Actualizada función `mostrarCamposPorProducto()` para el nuevo producto

## Dependencias Instaladas
- `folium`: Para generar mapas interactivos
- `geopandas`: Para manejar datos geoespaciales

## Uso en la Aplicación Web

1. **Seleccionar producto:** Elegir "Mapa Folium" en el selector de tipo de producto
2. **Configurar filtros:**
   - Elegir el tipo de dato (Conteos, Tasa cruda, ASMR)
   - Seleccionar año
   - Elegir sexo
   - Configurar rango de edad
3. **Generar:** Hacer clic en "Generar" para crear el mapa
4. **Interactuar:** 
   - Hacer zoom y navegar por el mapa
   - Pasar el mouse sobre estados para ver nombres
   - Hacer clic en marcadores para información detallada

## Estructura de Datos
El mapa utiliza:
- **Archivo CSV:** `frontend/static/data/tasas_mortalidad_consolidado.csv`
- **GeoJSON:** `frontend/static/mapas/estados.geojson`
- **Agregación:** Los datos se agrupan por estado (CVE_ENT)

## Pruebas
Se incluye un script de prueba: `frontend/test_mapa_folium.py` que verifica:
- Carga correcta de datos
- Generación exitosa del mapa
- Formato válido del HTML resultante

## Ejemplo de Salida
El mapa generado incluye:
- 32 estados de México
- Colores diferenciados por intensidad de datos
- Marcadores interactivos con información detallada
- Título dinámico con filtros aplicados
- Leyenda explicativa

---

**Nota:** Este producto complementa los existentes (Line plot, Box plot, Heatmap) proporcionando una experiencia más interactiva para la visualización de datos geográficos de mortalidad.
