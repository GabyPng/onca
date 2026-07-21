"""
API Backend para ONCA Lite - Wrapper para funciones.py
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar todas las funciones
from funciones import (
    cargar_datos,
    filtrar_datos_consolidado,
    generar_producto_consolidado,
    generar_lineplot_html,
    generar_heatmap_plotly,
    generar_boxplot,
    generar_mapa_folium,
    filtrar_datos_nacionales,
    filtrar_datos_estatales
)

app = Flask(__name__)
CORS(app)

# Cargar datos al inicio
try:
    df_mortalidad = cargar_datos()
    print("Datos de mortalidad cargados en API")
except Exception as e:
    print(f"Error cargando datos: {e}")
    df_mortalidad = None

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del API"""
    return jsonify({
        'status': 'healthy',
        'data_loaded': df_mortalidad is not None,
        'total_rows': len(df_mortalidad) if df_mortalidad is not None else 0
    })

@app.route('/filtrar_datos', methods=['POST'])
def filtrar_datos():
    """Endpoint para filtrar datos"""
    try:
        data = request.get_json()
        
        datos_filtrados = filtrar_datos_consolidado(
            df_mortalidad,
            codigo_cie10=data.get('codigo_cie10'),
            anio_especifico=data.get('anio_especifico'),
            anio_inicio=data.get('anio_inicio'),
            anio_final=data.get('anio_final'),
            tipo_enfoque=data.get('tipo_enfoque'),
            codigo_entidad=data.get('codigo_entidad'),
            codigo_municipio=data.get('codigo_municipio'),
            tipo_sexo=data.get('tipo_sexo'),
            edad_inicio=data.get('edad_inicio'),
            edad_final=data.get('edad_final'),
            tipo_escala=data.get('tipo_escala')
        )
        
        return jsonify({
            'success': True,
            'data': datos_filtrados.to_dict('records') if datos_filtrados is not None else [],
            'total_rows': len(datos_filtrados) if datos_filtrados is not None else 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generar_mapa', methods=['POST'])
def generar_mapa():
    """Endpoint para generar mapas"""
    try:
        data = request.get_json()
        
        mapa_html = generar_mapa_folium(
            df_mortalidad,
            anio_seleccionado=data.get('anio_seleccionado', 2020),
            escala_datos=data.get('escala_datos', 2),
            id_sexo=data.get('id_sexo', 3),
            edad_inicio=data.get('edad_inicio', "00_04"),
            edad_final=data.get('edad_final', "80_84"),
            codigo_cie10=data.get('codigo_cie10', "C910"),
            codigo_estado=data.get('codigo_estado'),
            filtro_municipio=data.get('filtro_municipio', False)
        )
        
        return jsonify({
            'success': True,
            'html': mapa_html
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generar_grafico', methods=['POST'])
def generar_grafico():
    """Endpoint para generar gráficos"""
    try:
        data = request.get_json()
        tipo_grafico = data.get('tipo_grafico')
        
        if tipo_grafico == 'lineplot':
            html = generar_lineplot_html(df_mortalidad, **data.get('params', {}))
        elif tipo_grafico == 'heatmap':
            html = generar_heatmap_plotly(df_mortalidad, **data.get('params', {}))
        elif tipo_grafico == 'boxplot':
            html = generar_boxplot(df_mortalidad, **data.get('params', {}))
        else:
            return jsonify({'success': False, 'error': 'Tipo de gráfico no válido'}), 400
        
        return jsonify({
            'success': True,
            'html': html
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
