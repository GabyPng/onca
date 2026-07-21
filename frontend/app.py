from flask import Flask, render_template, request, send_file, jsonify
import plotly.graph_objects as go
import plotly.offline as pyo
import pandas as pd
import os
import sys

# Agregar el directorio src al path para importar las funciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from funciones import (
        cargar_datos,
        filtrar_datos_consolidado,
        generar_producto_consolidado,
        generar_lineplot_html,
        generar_heatmap_plotly,
        generar_boxplot,
        generar_mapa_folium
    )
    # Cargar datos una vez al inicio
    df_mortalidad = cargar_datos()
    FUNCIONES_DISPONIBLES = True
    print("Datos de mortalidad cargados exitosamente")
    print("Nuevas funciones refactorizadas disponibles")
except ImportError as e:
    print(f"No se pudieron importar las funciones reales: {e}")
    FUNCIONES_DISPONIBLES = False
    df_mortalidad = None
except Exception as e:
    print(f"Error cargando datos: {e}")
    FUNCIONES_DISPONIBLES = False
    df_mortalidad = None

app = Flask(__name__)

# Funciones auxiliares para mapear parámetros
def mapear_sexo(sexo):
    """Mapea los valores de sexo del frontend al backend"""
    mapeo = {
        'hombres': 1,
        'mujeres': 2,
        'ambos': 3
    }
    return mapeo.get(sexo, 3)  # Por defecto ambos

def mapear_escala(tipo_dato):
    """Mapea el tipo de dato a escala"""
    # CORREGIDO: Los valores de escala en el CSV son:
    # 1 = conteos (no escalado)
    # 2 = tasa_cruda (por 10,000)
    # 3 = asmr (tasa estandarizada por 100,000)
    mapeo = {
        'conteos': 1,      # Conteos absolutos
        'tasa_cruda': 2,   # Tasa cruda por 10,000
        'asmr': 3          # ASMR por 100,000
    }
    return mapeo.get(tipo_dato, 2)  # Por defecto tasa_cruda

def mapear_edad(edad_num):
    """Mapea edad numérica a formato de rango"""
    try:
        edad = int(edad_num)
        if edad == 0:
            return '00_04'
        elif edad <= 85:
            inicio = (edad // 5) * 5
            fin = inicio + 4
            return f"{inicio:02d}_{fin:02d}"
        else:
            # Para edades mayores a 85, usar el último rango válido
            return '85_89'
    except:
        return '00_04'  # Por defecto

def mapear_edad_boxplot(edad_num):
    """Mapea edad numérica a formato de rango específico para boxplot"""
    try:
        edad = int(edad_num)
        # Los valores del template son: 04, 09, 14, 19, etc. (finales de rango)
        if edad <= 4:
            return '00_04'
        elif edad <= 9:
            return '05_09'
        elif edad <= 14:
            return '10_14'
        elif edad <= 19:
            return '15_19'
        elif edad <= 24:
            return '20_24'
        elif edad <= 29:
            return '25_29'
        elif edad <= 34:
            return '30_34'
        elif edad <= 39:
            return '35_39'
        elif edad <= 44:
            return '40_44'
        elif edad <= 49:
            return '45_49'
        elif edad <= 54:
            return '50_54'
        elif edad <= 59:
            return '55_59'
        elif edad <= 64:
            return '60_64'
        elif edad <= 69:
            return '65_69'
        elif edad <= 74:
            return '70_74'
        elif edad <= 79:
            return '75_79'
        elif edad <= 84:
            return '80_84'
        elif edad == 125:  # Valor especial por defecto  
            return '>85'  # Usar formato correcto para boxplot
        else:
            return '>85'  # Para cualquier valor mayor
    except:
        return '00_04'  # Por defecto

def generar_csv_datos(tipo_dato, anio=None, sexo=None):
    """Genera un archivo CSV con datos dummy que reflejan los filtros aplicados"""
    try:
        os.makedirs('static/data', exist_ok=True)
        
        # Generar datos diferentes según los filtros
        estados = ['Tamaulipas', 'Veracruz', 'Yucatán', 'Chiapas', 'Oaxaca']
        
        # Modificar valores según tipo de dato
        if tipo_dato == 'conteos':
            valores = [400, 600, 200, 800, 300]
        elif tipo_dato == 'tasa_cruda':
            valores = [0.4, 0.6, 0.2, 0.8, 0.3]
        else:  # asmr
            valores = [0.35, 0.55, 0.18, 0.75, 0.28]
        
        # Modificar según año (simulando cambios temporales)
        if anio:
            factor_anio = 1 + (int(anio) - 2020) * 0.1
            valores = [v * factor_anio for v in valores]
        
        # Modificar según sexo
        if sexo == 'hombres':
            valores = [v * 1.2 for v in valores]  # Valores más altos para hombres
        elif sexo == 'mujeres':
            valores = [v * 0.8 for v in valores]  # Valores más bajos para mujeres
        
        df = pd.DataFrame({
            'Estado': estados,
            'Valor': [round(v, 3) for v in valores],
            'Tipo': [tipo_dato] * 5,
            'Año': [anio or 2020] * 5,
            'Sexo': [sexo or 'ambos'] * 5
        })
        df.to_csv('static/data/resultados.csv', index=False)
        print(f"CSV generado con {len(df)} registros - Filtros aplicados: Tipo={tipo_dato}, Año={anio}, Sexo={sexo}")
        return True
    except Exception as e:
        print(f"Error generando CSV: {e}")
        return False

def determinar_contenido_mostrar(producto, tipo_dato, anio=None, anio_ini=None, anio_fin=None, sexo='ambos'):
    """Determina qué contenido mostrar según los parámetros del formulario"""
    
    print(f"[CONTENIDO] Determinando contenido para: Producto={producto}, Tipo={tipo_dato}, Año={anio}, Sexo={sexo}")
    
    # Para productos específicos, mostrar imagen solo si es el caso exacto
    if producto == 'Mapa' and tipo_dato == 'conteos':
        return {
            'tipo': 'imagen',
            'archivo': 'mapa.png',
            'ruta': 'images/'
        }
    
    # Nuevo producto: Mapa Folium
    if producto == 'Mapa Folium':
        archivo_generado = f"mapa_folium_{anio}_{tipo_dato}_{sexo}.html"
        ruta_archivo = f'static/data/{archivo_generado}'
        
        print(f"[CONTENIDO] Buscando archivo: {ruta_archivo}")
        if os.path.exists(ruta_archivo):
            archivo_html = archivo_generado
            print(f"[CONTENIDO] Archivo encontrado: {archivo_html}")
        else:
            archivo_html = 'mapa_folium_default.html'  # Fallback
            print(f"[CONTENIDO] Archivo no encontrado, usando fallback: {archivo_html}")
        
        return {
            'tipo': 'html',
            'archivo': archivo_html,
            'ruta': 'data/'
        }
    
    # Para otros casos, determinar archivo HTML dinámicamente
    if producto == 'Mapa' or producto == 'Heatmap':
        # Buscar archivo generado dinámicamente
        archivo_generado = f"heatmap_{anio}_{tipo_dato}_{sexo}.html"
        ruta_archivo = f'static/data/{archivo_generado}'
        
        print(f"[CONTENIDO] Buscando archivo: {ruta_archivo}")
        if os.path.exists(ruta_archivo):
            archivo_html = archivo_generado
            print(f"[CONTENIDO] Archivo encontrado: {archivo_html}")
        else:
            archivo_html = 'heatmap_plot.html'  # Fallback
            print(f"[CONTENIDO] Archivo no encontrado, usando fallback: {archivo_html}")
            
    elif producto == 'Line plot':
        archivo_generado = f"lineplot_{anio_ini}_{anio_fin}_{tipo_dato}_{sexo}.html"
        ruta_archivo = f'static/data/{archivo_generado}'
        
        print(f"[CONTENIDO] Buscando archivo: {ruta_archivo}")
        if os.path.exists(ruta_archivo):
            archivo_html = archivo_generado
            print(f"[CONTENIDO] Archivo encontrado: {archivo_html}")
        else:
            archivo_html = 'lineplot_mortalidad.html'  # Fallback
            print(f"[CONTENIDO] Archivo no encontrado, usando fallback: {archivo_html}")
            
    elif producto == 'Box plot':
        archivo_generado = f"boxplot_{anio}_{tipo_dato}_{sexo}.html"
        ruta_archivo = f'static/data/{archivo_generado}'
        
        print(f"[CONTENIDO] Buscando archivo: {ruta_archivo}")
        if os.path.exists(ruta_archivo):
            archivo_html = archivo_generado
            print(f"[CONTENIDO] Archivo encontrado: {archivo_html}")
        else:
            archivo_html = 'boxplot_mortalidad.html'  # Fallback
            print(f"[CONTENIDO] Archivo no encontrado, usando fallback: {archivo_html}")
    else:
        archivo_html = 'heatmap_plot.html'  # Por defecto
        print(f"[CONTENIDO] Producto no reconocido, usando por defecto: {archivo_html}")
    
    return {
        'tipo': 'html',
        'archivo': archivo_html,
        'ruta': 'data/'
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Obtener valores del formulario
        cie10 = request.form.get('cie10', 'C910')  # Valor por defecto
        producto = request.form.get('producto')
        tipo_dato = request.form.get('tipo_dato')
        nivel = request.form.get('nivel', 'nacional')  # Nacional por defecto
        estado = request.form.get('estado', '00')  # 00 = Nacional
        municipio = request.form.get('municipio', 'todos')  # todos = todos los municipios del estado
        sexo_raw = request.form.get('sexo')
        sexo = sexo_raw if sexo_raw is not None else 'ambos'  # Valor por defecto si es None
        edad_ini = request.form.get('edad_ini', '0')
        edad_fin = request.form.get('edad_fin', '125')

        print(f"Parámetros recibidos: CIE10={cie10}, Producto={producto}, Tipo={tipo_dato}, Nivel={nivel}, Estado={estado}, Municipio={municipio}, Sexo={sexo}, Edad={edad_ini}-{edad_fin}")
        
        # Debug adicional
        print(f"[DEBUG] Sexo raw: '{request.form.get('sexo')}' -> mapeado a: {mapear_sexo(sexo)}")
        print(f"[DEBUG] Tipo dato raw: '{tipo_dato}' -> mapeado a: {mapear_escala(tipo_dato)}")

        try:
            contenido = None
            # Inicializar variables de tiempo
            anio = None
            anio_ini = None
            anio_fin = None
            
            # Generación dinámica de los productos usando el backend y el CSV consolidado
            if FUNCIONES_DISPONIBLES and df_mortalidad is not None:
                if producto == 'Mapa' or producto == 'Heatmap':
                    anio = request.form.get('anio')
                    sexo_id = mapear_sexo(sexo)
                    escala = mapear_escala(tipo_dato)
                    
                    # Mapear edades para heatmap
                    edad_inicio_str = mapear_edad(edad_ini)
                    edad_fin_str = mapear_edad(edad_fin)
                    
                    print(f"[HEATMAP] Parámetros: anio={anio}, sexo_id={sexo_id}, escala={escala}, sexo={sexo}, tipo_dato={tipo_dato}")
                    print(f"[HEATMAP DEBUG] Edades: inicio={edad_inicio_str}, fin={edad_fin_str}")
                    try:
                        html_content = generar_heatmap_plotly(
                            dataframe_mortalidad=df_mortalidad,
                            anio_seleccionado=int(anio),
                            escala_datos=escala,
                            id_sexo=sexo_id,
                            edad_inicio=edad_inicio_str,
                            edad_final=edad_fin_str,
                            titulo_grafico=None
                        )
                        print(f"Heatmap generado exitosamente")
                        contenido = {
                            'tipo': 'html_directo',
                            'contenido': html_content
                        }
                    except Exception as e:
                        print(f"Error generando heatmap: {e}")
                        contenido = {'tipo': 'error', 'mensaje': f'Error generando heatmap: {e}'}
                elif producto == 'Line plot':
                    anio_ini = request.form.get('anio_ini')
                    anio_fin = request.form.get('anio_fin')
                    sexo_id = mapear_sexo(sexo)
                    escala = mapear_escala(tipo_dato)
                    
                    # Elegir enfoque según escala (estructura de los datos)
                    if escala == 1:
                        enfoque = 1  # Conteos: enfoque nacional
                        cve_ent = 1  # Usar primer estado disponible para enfoque 1
                    elif escala == 2:
                        enfoque = 2  # Tasa cruda: enfoque estatal
                        cve_ent = 1  # Usar primer estado disponible
                    elif escala == 3:
                        enfoque = 3  # ASMR: enfoque municipal (corregido)
                        cve_ent = None  # ASMR sí tiene datos nacionales
                    else:
                        enfoque = 2
                        cve_ent = 1
                        
                    edad_inicio_str = mapear_edad(edad_ini)
                    edad_fin_str = mapear_edad(edad_fin)
                    print(f"[LINEPLOT] Parámetros: anio_ini={anio_ini}, anio_fin={anio_fin}, sexo_id={sexo_id}, escala={escala}, enfoque={enfoque}, sexo={sexo}, tipo_dato={tipo_dato}")
                    try:
                        html_content = generar_lineplot_html(
                            dataframe_mortalidad=df_mortalidad,
                            enfoque=enfoque,
                            id_sexo=sexo_id,
                            escala_datos=escala,
                            edad_inicio=edad_inicio_str,
                            edad_fin=edad_fin_str,
                            anio_inicio=int(anio_ini),
                            anio_final=int(anio_fin),
                            codigo_entidad=cve_ent,
                            codigo_municipio=None
                        )
                        print(f"Line plot generado exitosamente")
                        contenido = {
                            'tipo': 'html_directo',
                            'contenido': html_content
                        }
                    except Exception as e:
                        print(f"Error generando lineplot: {e}")
                        contenido = {'tipo': 'error', 'mensaje': f'Error generando lineplot: {e}'}
                elif producto == 'Box plot':
                    anio = request.form.get('anio')
                    sexo_id = mapear_sexo(sexo)
                    escala = mapear_escala(tipo_dato)
                    edad_inicio_str = mapear_edad_boxplot(edad_ini)
                    edad_fin_str = mapear_edad_boxplot(edad_fin)  # Usar función específica para boxplot
                    
                    # Elegir enfoque según escala
                    if escala == 1:
                        enfoque = 1  # Conteos: enfoque nacional
                    elif escala == 2:
                        enfoque = 2  # Tasa cruda: enfoque estatal
                    elif escala == 3:
                        enfoque = 3  # ASMR: enfoque municipal (corregido)
                    else:
                        enfoque = 2
                        
                    print(f"[BOXPLOT] Parámetros: anio={anio}, sexo_id={sexo_id}, escala={escala}, enfoque={enfoque}, sexo={sexo}, tipo_dato={tipo_dato}")
                    print(f"[BOXPLOT DEBUG] Edades: inicio={edad_inicio_str}, fin={edad_fin_str}")
                    try:
                        html_content = generar_boxplot(
                            dataframe_consolidado=df_mortalidad,
                            año=int(anio),
                            escala_datos=escala,
                            codigo_cie10=cie10,
                            edad_inicio=edad_inicio_str,
                            edad_final=edad_fin_str,
                            tipo_enfoque=enfoque,
                            codigo_sexo=sexo_id
                        )
                        print(f"Box plot generado exitosamente")
                        contenido = {
                            'tipo': 'html_directo',
                            'contenido': html_content
                        }
                    except Exception as e:
                        print(f"Error generando boxplot: {e}")
                        import traceback
                        traceback.print_exc()
                        contenido = {'tipo': 'error', 'mensaje': f'Error generando boxplot: {e}'}
                elif producto == 'Mapa Folium':
                    anio = request.form.get('anio')
                    sexo_id = mapear_sexo(sexo)
                    escala = mapear_escala(tipo_dato)
                    
                    # Mapear edades para el mapa
                    edad_inicio_str = mapear_edad(edad_ini)
                    edad_fin_str = mapear_edad(edad_fin)
                    
                    print(f"[MAPA FOLIUM] Parámetros: anio={anio}, sexo_id={sexo_id}, escala={escala}, sexo={sexo}, tipo_dato={tipo_dato}")
                    print(f"[MAPA FOLIUM DEBUG] Edades: inicio={edad_inicio_str}, fin={edad_fin_str}")
                    print(f"[MAPA FOLIUM DEBUG] Nivel={nivel}, Estado={estado}, Municipio={municipio}")
                    try:
                        # Determinar parámetros según el nivel
                        if nivel == 'nacional':
                            codigo_estado_param = None
                            filtro_municipio_param = False
                        elif nivel == 'estatal':
                            codigo_estado_param = estado if estado and estado != '00' else None
                            filtro_municipio_param = True
                        else:
                            codigo_estado_param = estado if estado != '00' else None
                            filtro_municipio_param = (municipio != 'todos')
                        
                        html_content = generar_mapa_folium(
                            dataframe_mortalidad=df_mortalidad,
                            anio_seleccionado=int(anio),
                            escala_datos=escala,
                            id_sexo=sexo_id,
                            edad_inicio=edad_inicio_str,
                            edad_final=edad_fin_str,
                            codigo_cie10=cie10,
                            codigo_estado=codigo_estado_param,
                            filtro_municipio=filtro_municipio_param
                        )
                        print(f"Mapa Folium generado exitosamente")
                        contenido = {
                            'tipo': 'html_directo',
                            'contenido': html_content
                        }
                    except Exception as e:
                        print(f"Error generando mapa Folium: {e}")
                        import traceback
                        traceback.print_exc()
                        contenido = {'tipo': 'error', 'mensaje': f'Error generando mapa Folium: {e}'}
                else:
                    contenido = {'tipo': 'error', 'mensaje': 'Producto no válido'}
            else:
                contenido = {'tipo': 'error', 'mensaje': 'Datos requeridos no proporcionados'}
            
            # Preparar valores del formulario para mantenerlos
            form_values = {
                'cie10': cie10,
                'producto': producto,
                'tipo_dato': tipo_dato,
                'nivel': nivel,
                'estado': estado,
                'municipio': municipio,
                'sexo': sexo,
                'edad_ini': edad_ini,
                'edad_fin': edad_fin,
                'anio': anio,
                'anio_ini': anio_ini,
                'anio_fin': anio_fin
            }
            
            # Mostrar página con resultado
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            ruta_csv = os.path.join(base_dir, 'static', 'data', 'resultados.csv')

            if os.path.exists(ruta_csv):
                df = pd.read_csv(ruta_csv)
                tabla_html = df.to_html(classes='table table-striped', index=False, border=0)
                show_resultcsv = True
            else:
                tabla_html = ''
                show_resultcsv = False
            
            return render_template('index.html', show_result=True, contenido=contenido, form_values=form_values,  tabla_datos=tabla_html, show_resultcsv = show_resultcsv)
            
        except Exception as e:
            print(f"Error en el procesamiento: {e}")
            # Fallback a datos dummy
            generar_mapa_dummy("2020", tipo_dato, sexo)
            generar_csv_dummy(tipo_dato, "2020", sexo)
            contenido = {'tipo': 'html', 'archivo': 'heatmap_plot.html', 'ruta': 'data/'}  # Contenido por defecto en caso de error
            
            # Preparar valores del formulario para mantenerlos incluso en caso de error
            form_values = {
                'cie10': cie10,
                'producto': producto,
                'tipo_dato': tipo_dato,
                'nivel': nivel,
                'estado': estado,
                'municipio': municipio,
                'sexo': sexo,
                'edad_ini': edad_ini,
                'edad_fin': edad_fin,
                'anio': request.form.get('anio'),
                'anio_ini': request.form.get('anio_ini'),
                'anio_fin': request.form.get('anio_fin')
            }
            
            return render_template('index.html', show_result=True, error=str(e), contenido=contenido, form_values=form_values)

    return render_template('index.html', show_result=False)

@app.route('/descargar_csv')
def descargar_csv():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(base_dir, 'static', 'data', 'datos_filtrados.csv')
    if os.path.exists(ruta):
        return send_file(ruta, as_attachment=True)
    else:
        return "Archivo no encontrado", 404

@app.route('/ver_datos')
def ver_datos():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_csv = os.path.join(base_dir, 'static', 'data', 'datos_filtrados.csv')

    if os.path.exists(ruta_csv):
        df = pd.read_csv(ruta_csv)
        tabla_html = df.to_html(classes='table table-striped', index=False)
        return tabla_html
    else:
        return "<p>No hay datos para mostrar.</p>"

def generar_mapa_dummy(anio="2020", tipo_dato="conteos", sexo="ambos"):
    """Crea un gráfico dummy usando Plotly y lo guarda como HTML"""
    os.makedirs('static/data', exist_ok=True)
    
    # Crear un gráfico simple con Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, 1], 
        y=[0, 1], 
        mode='lines',
        line=dict(width=3),
        name='Datos dummy'
    ))
    
    fig.update_layout(
        title=f"Mapa dummy<br>Año: {anio}, Tipo: {tipo_dato}, Sexo: {sexo}",
        xaxis_title="Filtros aplicados correctamente",
        yaxis_title="Los datos cambian según filtros",
        showlegend=False,
        width=800,
        height=600
    )
    
    # Guardar como HTML
    html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
    with open('static/data/heatmap_plot.html', 'w', encoding='utf-8') as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mapa Dummy</title>
            <meta charset="utf-8">
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """)
    
    print(f"Mapa dummy generado con filtros: Año={anio}, Tipo={tipo_dato}, Sexo={sexo}")

def generar_csv_dummy(tipo_dato="conteos", anio="2020", sexo="ambos"):
    """Crea archivo CSV de ejemplo en /static/data/datos.csv con filtros aplicados"""
    os.makedirs('static/data', exist_ok=True)
    
    # Generar datos diferentes según los filtros
    estados = ['Tamaulipas', 'Veracruz', 'Yucatán']
    
    if tipo_dato == 'conteos':
        valores = [400, 600, 200]
    elif tipo_dato == 'tasa_cruda':
        valores = [0.4, 0.6, 0.2]
    else:  # asmr
        valores = [0.35, 0.55, 0.18]
    
    # Modificar según año
    factor_anio = 1 + (int(anio) - 2020) * 0.1
    valores = [v * factor_anio for v in valores]
    
    # Modificar según sexo
    if sexo == 'hombres':
        valores = [v * 1.2 for v in valores]
    elif sexo == 'mujeres':
        valores = [v * 0.8 for v in valores]
    
    df = pd.DataFrame({
        'Estado': estados,
        'ASR': [round(v, 3) for v in valores],
        'Año': [anio] * 3,
        'Sexo': [sexo] * 3,
        'Tipo': [tipo_dato] * 3
    })
    df.to_csv('static/data/datos.csv', index=False)
    print(f"CSV dummy generado con filtros: Año={anio}, Tipo={tipo_dato}, Sexo={sexo}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Puerto por defecto 5001
    app.run(host='0.0.0.0', port=port, debug=True)
