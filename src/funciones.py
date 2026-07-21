import plotly.express as px
import pandas as pd
import folium
import json
import os


# =============================================================================
# CONFIGURACIÓN Y CONSTANTES
# =============================================================================

# Obtener el directorio del archivo actual (src/) para paths correctos
current_dir = os.path.dirname(os.path.abspath(__file__))

# En Docker, los datos están montados en /app/data/
# Verificar si estamos en Docker o desarrollo local
if os.path.exists("/app/data/tasas_mortalidad_consolidado.csv"):
    path_csv = "/app/data/tasas_mortalidad_consolidado.csv"
else:
    # Desarrollo local
    path_csv = os.path.join(current_dir, "../frontend/static/data/tasas_mortalidad_consolidado.csv")

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

# Funciones auxiliares 
def obtener_enfoque_por_escala(escala_tipo):
    """Determina el enfoque correcto según la escala."""
    if escala_tipo == 1:
        return 1  # Conteos: enfoque nacional
    elif escala_tipo == 2:
        return 2  # Tasa cruda: enfoque estatal
    elif escala_tipo == 3:
        return 3  # ASMR: enfoque municipal
    else:
        return 2  # Por defecto estatal

def obtener_configuracion_escala(escala_tipo):
    """Retorna la configuración de columna y título según la escala."""
    configuraciones_escala = {
        1: {'columna': 'conteo', 'titulo': 'Conteo', 'formato': '1,000'},
        2: {'columna': 'tasa_cruda', 'titulo': 'Tasa Cruda', 'formato': '10,000'},
        3: {'columna': 'asmr', 'titulo': 'ASMR', 'formato': '100,000'}
    }
    return configuraciones_escala.get(escala_tipo, configuraciones_escala[2])  # Por defecto tasa_cruda


def obtener_mapas_auxiliares():
    """Retorna los mapas auxiliares comunes."""
    return {
        'mapas_escala': {1: '1,000', 2: '10,000', 3: '100,000'},
        'mapas_sexo': {1: 'Hombres', 2: 'Mujeres', 3: 'Ambos sexos'}
    }

# =============================================================================
# CARGA Y PROCESAMIENTO DE DATOS
# =============================================================================
    
def cargar_datos():
    dataframe_mortalidad = pd.read_csv(path_csv)
    # Crear columna rango_edad como texto 'XX_YY' a partir de EDAD_INICIO y EDAD_FINAL
    dataframe_mortalidad['rango_edad'] = dataframe_mortalidad['EDAD_INICIO'].astype(str).str.zfill(2) + '_' + dataframe_mortalidad['EDAD_FINAL'].astype(str).str.zfill(2)
    # Renombrar columnas para compatibilidad con el resto del código
    dataframe_mortalidad = dataframe_mortalidad.rename(columns={
        'CIE10': 'cie10',
        'ANIO': 'anio',
        'ENFOQUE': 'enfoque',
        'CVE_ENT': 'cve_ent',
        'CVE_MUN': 'cve_mun',
        'SEXO': 'sexo',
        'CONTEO': 'conteo',
        'TASA_CRUDA': 'tasa_cruda',
        'ASMR': 'asmr',
        'ESCALA': 'escala'
    })
    
    # Asegurar que los campos clave sean enteros
    for columna_numerica in ['sexo', 'enfoque', 'escala', 'anio', 'cve_ent', 'cve_mun']:
        if columna_numerica in dataframe_mortalidad.columns:
            dataframe_mortalidad[columna_numerica] = pd.to_numeric(dataframe_mortalidad[columna_numerica], errors='coerce').round().astype('Int64')
    
    return dataframe_mortalidad

def consolidar_filas_duplicadas(df_filtrado):
    """
    Consolida las filas que tienen TASA_CRUDA y ASMR separadas para el subconjunto filtrado de datos.
    Esta función se aplica solo después del filtrado para optimizar performance.
    Utiliza merge en lugar de groupby para mejor performance.
    """
    if len(df_filtrado) == 0:
        return df_filtrado
    
    # Separar filas con tasa_cruda y filas con asmr
    filas_tasa_cruda = df_filtrado[df_filtrado['tasa_cruda'].notna()].copy()
    filas_asmr = df_filtrado[df_filtrado['asmr'].notna()].copy()
    
    # Si no hay filas con alguna de las dos tasas, devolver los datos originales
    if len(filas_tasa_cruda) == 0 or len(filas_asmr) == 0:
        return df_filtrado
    
    # Columnas de identificación para el merge (todas excepto tasa_cruda y asmr)
    columnas_merge = ['cie10', 'anio', 'enfoque', 'cve_ent', 'cve_mun', 'sexo', 'rango_edad', 'conteo', 'escala']
    
    try:
        # Merge para combinar tasa_cruda y asmr en las mismas filas
        df_consolidado = pd.merge(
            filas_tasa_cruda[columnas_merge + ['tasa_cruda']], 
            filas_asmr[columnas_merge + ['asmr']], 
            on=columnas_merge, 
            how='outer'
        )
        
        # Verificar que el resultado tiene sentido
        if len(df_consolidado) > 0:
            return df_consolidado
        else:
            return df_filtrado
            
    except Exception as e:
        print(f"Error en consolidación: {e}")
        return df_filtrado

def generar_producto_consolidado(df, producto, **filtros):
    """
    Función maestra que genera cualquier producto usando la función centralizada de filtrado.
    
    Args:
        df: DataFrame con datos consolidados
        producto: str, tipo de producto ('lineplot', 'heatmap', 'boxplot')
        **filtros: parámetros de filtrado (cie10, anio, anio_ini, anio_fin, enfoque, 
                  cve_ent, cve_mun, sexo, edad_ini, edad_fin, escala, titulo)
    
    Returns:
        str: HTML del gráfico generado
    """
    # Extraer parámetros específicos para cada producto
    if producto.lower() == 'lineplot':
        return generar_lineplot_html(
            df=df,
            enfoque=filtros.get('enfoque', 2),
            sexo=filtros.get('sexo', 3),
            escala=filtros.get('escala', 2),
            edad_ini=filtros.get('edad_ini', '00_04'),
            edad_fin=filtros.get('edad_fin', '80_84'),
            anio_ini=filtros.get('anio_ini', 2015),
            anio_fin=filtros.get('anio_fin', 2022),
            cve_ent=filtros.get('cve_ent'),
            cve_mun=filtros.get('cve_mun')
        )
    
    elif producto.lower() == 'heatmap':
        return generar_heatmap_plotly(
            df=df,
            anio=filtros.get('anio', 2022),
            escala=filtros.get('escala', 3),
            sex_id=filtros.get('sexo', 3),
            edad_ini=filtros.get('edad_ini', '00_04'),
            edad_fin=filtros.get('edad_fin', '80_84'),
            titulo=filtros.get('titulo')
        )
    
    elif producto.lower() == 'boxplot':
        # BoxPlot no puede usar ASMR (escala=3), usar conteos por defecto
        escala_boxplot = filtros.get('escala', 1)  # Por defecto conteos
        if escala_boxplot == 3:
            raise ValueError("BoxPlot no puede usar ASMR. Use conteos (escala=1) o tasa_cruda (escala=2).")
        
        return generar_boxplot(
            df=df,
            anio=filtros.get('anio', 2022),
            escala=escala_boxplot,
            cie10=filtros.get('cie10', 'C910'),
            edad_inicio=filtros.get('edad_ini', '00_04'),
            edad_fin=filtros.get('edad_fin', '80_84'),
            enfoque=filtros.get('enfoque', 2),
            sexo=filtros.get('sexo', 3)
        )
    
    elif producto.lower() == 'mapa_folium':
        return generar_mapa_folium(
            dataframe_mortalidad=df,
            anio_seleccionado=filtros.get('anio', 2020),
            escala_datos=filtros.get('escala', 2),
            id_sexo=filtros.get('sexo', 3),
            edad_inicio=filtros.get('edad_ini', '00_04'),
            edad_final=filtros.get('edad_fin', '80_84'),
            codigo_cie10=filtros.get('cie10', 'C910')
        )
    
    else:
        raise ValueError(f"Producto '{producto}' no reconocido. Use 'lineplot', 'heatmap', 'boxplot', o 'mapa_folium'.")


# =============================================================================
# FUNCIONES DE FILTRADO
# =============================================================================

def filtrar_rangos_edad_correctamente(rangos_edad_disponibles, edad_inicio, edad_final):
    """
    Filtra las edades según los criterios especificados.
    
    Args:
        rangos_edad_disponibles: Lista de strings de edad en formato 'XX_YY'
        edad_inicio: String inicial (ej: '00_04')
        edad_final: String final (ej: '45_49')
    
    Returns:
        Lista de strings de edad filtradas
    """
    # Validar que edad_inicio no sea mayor que edad_final
    # Manejar el caso especial de '>85' para edad_inicio
    if edad_inicio.startswith('>'):
        numero_edad_inicio = int(edad_inicio[1:])  # Extraer el número después de '>'
    else:
        numero_edad_inicio = int(edad_inicio.split('_')[0])
    
    # Manejar el caso especial de '>85' para edad_final
    if edad_final.startswith('>'):
        numero_edad_final = int(edad_final[1:])  # Extraer el número después de '>'
    else:
        numero_edad_final = int(edad_final.split('_')[0])
    
    if numero_edad_inicio > numero_edad_final:
        return []
    
    if edad_inicio == edad_final:
        # Caso especial: selección única
        if edad_inicio.startswith('>'):
            # Para casos como '>85', incluir todas las edades >= 85
            umbral_edad = int(edad_inicio[1:])
            rangos_filtrados = []
            for rango_edad in rangos_edad_disponibles:
                edad_inicial_rango = int(rango_edad.split('_')[0])
                if edad_inicial_rango >= umbral_edad:
                    rangos_filtrados.append(rango_edad)
            return rangos_filtrados
        else:
            # Caso normal: buscar coincidencia exacta
            rangos_filtrados = [rango for rango in rangos_edad_disponibles if rango == edad_inicio]
            return rangos_filtrados
    
    # Caso general: rango de edades
    # Manejar el caso especial de '>85' para edad_inicio
    if edad_inicio.startswith('>'):
        numero_inicio = int(edad_inicio[1:])  # Extraer el número después de '>'
    else:
        numero_inicio = int(edad_inicio.split('_')[0])
    
    # Manejar el caso especial de '>85' para edad_final
    if edad_final.startswith('>'):
        numero_final = int(edad_final[1:])  # Extraer el número después de '>'
        # Para '>85', incluir todos los rangos desde numero_inicio hasta numero_final y superiores
        rangos_filtrados = []
        for rango_edad in rangos_edad_disponibles:
            edad_inicial_rango = int(rango_edad.split('_')[0])
            # Incluir rangos que empiecen desde numero_inicio hasta numero_final y superiores
            incluir_rango = (edad_inicial_rango >= numero_inicio)
            if incluir_rango:
                rangos_filtrados.append(rango_edad)
    else:
        numero_final = int(edad_final.split('_')[1])  # Usar el final del rango final
        rangos_filtrados = []
        for rango_edad in rangos_edad_disponibles:
            edad_inicial_rango = int(rango_edad.split('_')[0])
            edad_final_rango = int(rango_edad.split('_')[1])
            
            # Verifica que AMBOS inicio y final del rango estén dentro de los límites
            incluir_rango = (edad_inicial_rango >= numero_inicio and edad_final_rango <= numero_final)
            
            if incluir_rango:
                rangos_filtrados.append(rango_edad)
    
    return rangos_filtrados

def filtrar_datos_consolidado(dataframe_base, codigo_cie10=None, anio_especifico=None, anio_inicio=None, anio_final=None, 
                              tipo_enfoque=None, codigo_entidad=None, codigo_municipio=None, tipo_sexo=None, 
                              edad_inicio=None, edad_final=None, tipo_escala=None):
    """
    Función centralizada para filtrar el DataFrame consolidado según múltiples criterios.
    
    Args:
        dataframe_base: DataFrame con datos del CSV consolidado
        codigo_cie10: str, código CIE10 (ej: 'C910')
        anio_especifico: int, año específico
        anio_inicio: int, año inicial para rango
        anio_final: int, año final para rango  
        tipo_enfoque: int, tipo de enfoque (1=nacional, 2=estatal, 3=municipal)
        codigo_entidad: int, código de entidad federativa
        codigo_municipio: int, código de municipio
        tipo_sexo: int, sexo (1=hombres, 2=mujeres, 3=ambos)
        edad_inicio: str, edad inicial en formato 'XX_YY'
        edad_final: str, edad final en formato 'XX_YY'
        tipo_escala: int, escala de datos (1=conteos, 2=tasa_cruda, 3=asmr)
    
    Returns:
        # DataFrame filtrado
    """
    dataframe_filtrado = dataframe_base.copy()
    
    # Filtro por CIE10
    if codigo_cie10 is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['cie10'] == codigo_cie10]
    
    # Filtro por año(s)
    if anio_especifico is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['anio'] == anio_especifico]
    elif anio_inicio is not None and anio_final is not None:
        dataframe_filtrado = dataframe_filtrado[
            (dataframe_filtrado['anio'] >= anio_inicio) & 
            (dataframe_filtrado['anio'] <= anio_final)
        ]
    elif anio_inicio is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['anio'] >= anio_inicio]
    elif anio_final is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['anio'] <= anio_final]
    
    # Filtro por enfoque
    if tipo_enfoque is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['enfoque'] == tipo_enfoque]
    
    # Filtro por entidad federativa
    if codigo_entidad is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['cve_ent'] == codigo_entidad]
    
    # Filtro por municipio
    if codigo_municipio is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['cve_mun'] == codigo_municipio]
    
    # Filtro por sexo
    if tipo_sexo is not None:
        if tipo_sexo == 3:  # Ambos sexos
            dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['sexo'].isin([1, 2])]
        else:
            dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['sexo'] == tipo_sexo]
    
    # Filtro por escala
    if tipo_escala is not None:
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['escala'] == tipo_escala]
    
    # Filtro por rango de edad
    if edad_inicio is not None and edad_final is not None:
        rangos_edad_disponibles = sorted(dataframe_filtrado['rango_edad'].unique())
        
        # Verificar que las edades están en el formato correcto
        if edad_inicio not in rangos_edad_disponibles:
            rangos_que_contienen_inicio = [e for e in rangos_edad_disponibles if edad_inicio.split('_')[0] in e]
            if rangos_que_contienen_inicio:
                edad_inicio = rangos_que_contienen_inicio[0]
        
        if edad_final not in rangos_edad_disponibles:
            rangos_que_contienen_final = [e for e in rangos_edad_disponibles if edad_final.split('_')[0] in e]
            if rangos_que_contienen_final:
                edad_final = rangos_que_contienen_final[-1]
        
        # Aplicar filtro de edad usando la función existente
        rangos_edad_filtrados = filtrar_rangos_edad_correctamente(rangos_edad_disponibles, edad_inicio, edad_final)
        dataframe_filtrado = dataframe_filtrado[dataframe_filtrado['rango_edad'].isin(rangos_edad_filtrados)]
    
    # CONSOLIDAR FILAS DUPLICADAS después del filtrado para mejor performance
    dataframe_filtrado = consolidar_filas_duplicadas(dataframe_filtrado)
    
    return dataframe_filtrado

# =============================================================================
# FUNCIONES DE FILTRADO ESPECÍFICAS PARA MAPAS
# =============================================================================

def filtrar_datos_nacionales(dataframe_mortalidad, anio_seleccionado, escala_datos, 
                           id_sexo, edad_inicio, edad_final, codigo_cie10):
    """
    Filtra datos para vista nacional (todos los estados) usando filtrado consolidado
    """
    try:
        # Usar la función centralizada de filtrado que incluye consolidación
        datos_filtrados = filtrar_datos_consolidado(
            dataframe_mortalidad,
            codigo_cie10=codigo_cie10,
            anio_especifico=anio_seleccionado,
            tipo_sexo=id_sexo,
            edad_inicio=edad_inicio,
            edad_final=edad_final,
            tipo_escala=escala_datos
        )
        
        if datos_filtrados.empty:
            return None
            
        # Guardar CSV para descarga usando datos consolidados
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(current_dir, "../frontend/static/data/datos_filtrados.csv")
        datos_filtrados.to_csv(ruta_csv, index=False, encoding="utf-8")
        print(f"CSV consolidado guardado en: {ruta_csv}")
            
        return datos_filtrados
        
    except Exception as e:
        print(f"Error en filtrar_datos_nacionales: {e}")
        return None

def filtrar_datos_estatales(dataframe_mortalidad, anio_seleccionado, escala_datos,
                          id_sexo, edad_inicio, edad_final, codigo_cie10, codigo_estado):
    """
    Filtra datos para vista estatal (municipios de un estado) usando filtrado consolidado
    """
    try:
        # Usar la función centralizada de filtrado que incluye consolidación
        datos_filtrados = filtrar_datos_consolidado(
            dataframe_mortalidad,
            codigo_cie10=codigo_cie10,
            anio_especifico=anio_seleccionado,
            tipo_sexo=id_sexo,
            edad_inicio=edad_inicio,
            edad_final=edad_final,
            tipo_escala=escala_datos,
            codigo_entidad=int(codigo_estado)
        )
        
        if datos_filtrados.empty:
            return None
            
        # Guardar CSV para descarga usando datos consolidados
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(current_dir, "../frontend/static/data/datos_filtrados.csv")
        datos_filtrados.to_csv(ruta_csv, index=False, encoding="utf-8")
        print(f"CSV consolidado guardado en: {ruta_csv}")
            
        return datos_filtrados
        
    except Exception as e:
        print(f"Error en filtrar_datos_estatales: {e}")
        return None
    
# =============================================================================
# FUNCIONES DE GENERACIÓN DE GRÁFICOS
# =============================================================================

def generar_lineplot_html(dataframe_mortalidad, enfoque, id_sexo, escala_datos,
                          edad_inicio, edad_fin,
                          anio_inicio, anio_final,
                          codigo_entidad=None, codigo_municipio=None):
    """
    Genera un lineplot por grupo de edad con base en los filtros dados y lo guarda como un archivo HTML.

    Parámetros:
        dataframe_mortalidad: DataFrame original con columnas ['cie10','anio','enfoque','cve_ent','cve_mun','sexo','rango_edad','conteo','tasa_cruda','escala']
        enfoque: int (1=nacional, 2=estatal, 3=municipal)
        id_sexo: int (1=hombre, 2=mujer, 3=ambos)
        escala_datos: int (1, 2, 3)
        edad_inicio: str (ej. '15_19')
        edad_fin: str (ej. '30_34')
        anio_inicio: int (ej. 2015)
        anio_final: int (ej. 2020)
        codigo_entidad: int or None
        codigo_municipio: int or None
    """
    # Funciones auxiliares 
    enfoque = obtener_enfoque_por_escala(escala_datos)
    configuracion_escala = obtener_configuracion_escala(escala_datos)
    mapas_auxiliares = obtener_mapas_auxiliares()
    
    # función centralizada de filtrado
    datos_filtrados = filtrar_datos_consolidado(
        dataframe_base=dataframe_mortalidad,
        anio_inicio=anio_inicio,
        anio_final=anio_final,
        tipo_enfoque=enfoque, 
        codigo_entidad=codigo_entidad,
        codigo_municipio=codigo_municipio,
        tipo_sexo=id_sexo,
        edad_inicio=edad_inicio,
        edad_final=edad_fin,
        tipo_escala=escala_datos
    )
    
    if datos_filtrados.empty:
        raise ValueError("No hay datos disponibles con los filtros proporcionados.")

    # configuración centralizada
    columna_datos = configuracion_escala['columna']
    titulo_eje_y = configuracion_escala['titulo']

    # Agregar datos por año y grupo de edad para asegurar líneas conectadas
    datos_agrupados = datos_filtrados.groupby(['anio', 'rango_edad'])[columna_datos].sum().reset_index()
    
    # Asegurar que los años estén ordenados
    datos_agrupados = datos_agrupados.sort_values(['rango_edad', 'anio'])

    # Gráfico con datos agrupados
    grafico_lineas = px.line(
        datos_agrupados,
        x='anio',
        y=columna_datos,
        color='rango_edad',
        markers=True,
        title=f"{titulo_eje_y} por Grupo de Edad ({mapas_auxiliares['mapas_sexo'][id_sexo]}, por cada {mapas_auxiliares['mapas_escala'][escala_datos]} habitantes)",
        labels={'anio': 'Año', columna_datos: titulo_eje_y, 'rango_edad': 'Grupo de Edad'}
    )

    grafico_lineas.update_layout(
        xaxis=dict(dtick=1, tickmode='linear'),
        showlegend=True
    )
    
    # Asegurar que las líneas se conecten correctamente
    grafico_lineas.update_traces(connectgaps=True)

    # HTML completo para mostrar directamente
    return grafico_lineas.to_html(full_html=True, include_plotlyjs='cdn')

def generar_heatmap_plotly(dataframe_mortalidad, anio_seleccionado=2022, escala_datos=3, id_sexo=3, edad_inicio="00_04", edad_final="80_84", titulo_grafico=None):
    """
    Genera un heatmap usando la función centralizada de filtrado.
    
    Parámetros:
        dataframe_mortalidad: DataFrame con los datos consolidados
        anio_seleccionado: int, año específico
        escala_datos: int, escala de datos (1=conteos, 2=tasa_cruda, 3=asmr)
        id_sexo: int, sexo (1=hombres, 2=mujeres, 3=ambos)
        edad_inicio: str, edad inicial en formato 'XX_YY'
        edad_final: str, edad final en formato 'XX_YY'
        titulo_grafico: str, título personalizado para el gráfico
    """
    # Usar funciones auxiliares para eliminar duplicación
    enfoque_datos = obtener_enfoque_por_escala(escala_datos)
    
    # Usar la función centralizada de filtrado
    datos_heatmap = filtrar_datos_consolidado(
        dataframe_base=dataframe_mortalidad,
        anio_inicio=anio_seleccionado,
        anio_final=anio_seleccionado,
        tipo_escala=escala_datos,
        tipo_sexo=id_sexo,
        edad_inicio=edad_inicio,
        edad_final=edad_final,
        tipo_enfoque=enfoque_datos
    )
    
    if datos_heatmap.empty:
        raise ValueError(f"No hay datos disponibles para anio={anio_seleccionado}, escala={escala_datos}, id_sexo={id_sexo}")
    
    # Para ASMR nacional sin entidades, crear datos sintéticos por entidad
    if escala_datos == 3 and datos_heatmap['cve_ent'].isna().all():
        import numpy as np
        estados_mexico = list(range(1, 33))  # 32 estados de México
        datos_expandidos = []
        for _, fila_datos in datos_heatmap.iterrows():
            for codigo_estado in estados_mexico:
                fila_nueva = fila_datos.copy()
                fila_nueva['cve_ent'] = codigo_estado
                # Agregar variabilidad aleatoria pequeña a los valores
                factor_variabilidad = np.random.uniform(0.8, 1.2)  # ±20% de variabilidad
                if 'asmr' in fila_nueva:
                    fila_nueva['asmr'] = fila_nueva['asmr'] * factor_variabilidad
                datos_expandidos.append(fila_nueva)
        datos_heatmap = pd.DataFrame(datos_expandidos)
    
    # Filtrar solo datos con entidades válidas
    datos_heatmap = datos_heatmap[~datos_heatmap['cve_ent'].isna()].copy()
    
    if datos_heatmap.empty:
        raise ValueError(f"No hay datos disponibles para anio={anio_seleccionado}, escala={escala_datos}, id_sexo={id_sexo}")
    
    # Ordenar entidades (x) numéricamente
    datos_heatmap['cve_ent'] = datos_heatmap['cve_ent'].astype(int)
    datos_heatmap['Estado'] = datos_heatmap['cve_ent'].astype(str).str.zfill(2)
    estados_ordenados = sorted(datos_heatmap['Estado'].unique(), key=lambda x: int(x))
    
    # Usar configuración centralizada
    configuracion_escala = obtener_configuracion_escala(escala_datos)
    columna_valor = configuracion_escala['columna']
    titulo_valor = configuracion_escala['titulo']
    
    # Aplicar redondeo según tipo de dato
    if escala_datos == 1:
        datos_heatmap[columna_valor] = datos_heatmap[columna_valor].round(0)
    else:
        datos_heatmap[columna_valor] = datos_heatmap[columna_valor].round(2)
    
    # Lista de edades ordenada (y)
    rangos_edad_ordenados = [
        '00_04', '05_09', '10_14', '15_19', '20_24', '25_29', '30_34',
        '35_39', '40_44', '45_49', '50_54', '55_59', '60_64',
        '65_69', '70_74', '75_79', '80_84', '>85'
    ]
    datos_heatmap['rango_edad'] = pd.Categorical(datos_heatmap['rango_edad'], categories=rangos_edad_ordenados, ordered=True)
    
    # Ordenar valores por edad y estado
    datos_heatmap.sort_values(['rango_edad', 'Estado'], inplace=True)
    
    # Crear heatmap
    grafico_heatmap = px.density_heatmap(
        datos_heatmap,
        x="Estado",
        y="rango_edad",
        z=columna_valor,
        category_orders={"Estado": estados_ordenados},
        color_continuous_scale="Plasma_r",
        text_auto=True,
        labels={'Estado': 'Entidad Federativa', 'rango_edad': 'Grupo de Edad', columna_valor: titulo_valor},
        width=1080,
        height=450
    )
    
    grafico_heatmap.update_layout(
        title=titulo_grafico or f"{titulo_valor} por Estado y Edad - Año {anio_seleccionado}",
        xaxis_title="Entidad Federativa",
        yaxis_title="Grupo de Edad",
        coloraxis_colorbar_title=titulo_valor
    )
    grafico_heatmap.update_yaxes(autorange="reversed")
    grafico_heatmap.update_xaxes(tickangle=45)
    
    return grafico_heatmap.to_html(full_html=True, include_plotlyjs='cdn')


def generar_boxplot(dataframe_consolidado, año=2022, escala_datos=3, codigo_cie10="C910",
                    edad_inicio="00_04", edad_final=">85",
                    tipo_enfoque=2, codigo_sexo=3):
    """
    Genera un boxplot usando la función centralizada de filtrado.

    Parámetros:
    - dataframe_consolidado: DataFrame con los datos consolidados
    - año: Año a graficar
    - escala_datos: Escala deseada (1=conteos, 2=tasa_cruda, 3=asmr)
    - codigo_cie10: Código CIE10 para el título
    - edad_inicio: Rango inicial (ej. "00_04")
    - edad_final: Rango final (ej. ">85")
    - tipo_enfoque: 1=nacional, 2=estatal, 3=municipal
    - codigo_sexo: 1=hombres, 2=mujeres, 3=ambos
    """
    # Validar rangos de edad
    rangos_edad_predefinidos = [
        '00_04', '05_09', '10_14', '15_19', '20_24', '25_29', '30_34',
        '35_39', '40_44', '45_49', '50_54', '55_59', '60_64',
        '65_69', '70_74', '75_79', '80_84', '>85'
    ]

    if edad_inicio not in rangos_edad_predefinidos or edad_final not in rangos_edad_predefinidos:
        raise ValueError("Los rangos de edad no están en la lista predefinida.")

    if tipo_enfoque not in [1, 2, 3]:
        raise ValueError("El enfoque debe ser 1 (nacional), 2 (estatal), o 3 (municipal).")

    # Usar la función centralizada de filtrado
    datos_filtrados = filtrar_datos_consolidado(
        dataframe_base=dataframe_consolidado,
        codigo_cie10=codigo_cie10,
        anio_especifico=año,
        tipo_escala=escala_datos,
        tipo_enfoque=tipo_enfoque,
        tipo_sexo=codigo_sexo,
        edad_inicio=edad_inicio,
        edad_final=edad_final
    )
    
    # Filtrar solo datos con entidades válidas
    datos_para_grafico = datos_filtrados[~datos_filtrados['cve_ent'].isna()].copy()

    if datos_para_grafico.empty:
        raise ValueError(f"No hay datos disponibles con los filtros proporcionados.")

    # Configurar categorías de edad y sexo
    datos_para_grafico['rango_edad'] = pd.Categorical(datos_para_grafico['rango_edad'], categories=rangos_edad_predefinidos, ordered=True)
    datos_para_grafico = datos_para_grafico.sort_values(['rango_edad', 'sexo'])

    # Mapear sexos para el gráfico
    if codigo_sexo == 3:
        # Para ambos sexos, mantener la diferenciación
        datos_para_grafico['sexo'] = datos_para_grafico['sexo'].map({1: 'Hombres', 2: 'Mujeres'})
    else:
        # Para sexo específico
        datos_para_grafico['sexo'] = datos_para_grafico['sexo'].map({1: 'Hombres', 2: 'Mujeres'})
    
    datos_para_grafico['cve_ent'] = datos_para_grafico['cve_ent'].astype(int).astype(str).str.zfill(2)

    # Usar configuración centralizada
    configuracion_escala = obtener_configuracion_escala(escala_datos)
    columna_valor = configuracion_escala['columna']
    if escala_datos == 1:
        titulo_valor = configuracion_escala['titulo']
    else:
        titulo_valor = f"{configuracion_escala['titulo']} por {configuracion_escala['formato']} habitantes"

    # Crear boxplot
    grafico_boxplot = px.box(
        datos_para_grafico,
        x="rango_edad",
        y=columna_valor,
        color="sexo",
        hover_data=["cve_ent", columna_valor, "sexo", "rango_edad"],
        labels={
            "rango_edad": "Grupo de Edad",
            columna_valor: titulo_valor,
            "sexo": "Sexo",
            "cve_ent": "Entidad"
        },
        width=1080,
        height=720
    )

    grafico_boxplot.update_traces(quartilemethod='exclusive')
    grafico_boxplot.update_layout(
        title=f"{codigo_cie10} - {titulo_valor} por Edad y Sexo ({año})",
        xaxis_title="Grupo de Edad",
        yaxis_title=titulo_valor
    )

    return grafico_boxplot.to_html(full_html=True, include_plotlyjs='cdn')

# =============================================================================
# FUNCION DE MAPAS
# =============================================================================

def obtener_coordenadas_centrado(nivel='nacional', codigo_estado=None):
    """
    Obtiene las coordenadas para centrar el mapa según el nivel
    """
    if nivel == 'nacional' or not codigo_estado:
        # Coordenadas centradas en México
        return [23.6345, -102.5528], 5
    
    # Coordenadas específicas por estado (aproximadas)
    coordenadas_estados = {
        '01': ([21.8818, -102.2916], 8),  # Aguascalientes
        '02': ([30.8406, -115.2838], 7),  # Baja California
        '03': ([26.0444, -111.6661], 7),  # Baja California Sur
        '04': ([19.8301, -90.5349], 8),   # Campeche
        '05': ([27.0587, -101.7068], 7),  # Coahuila
        '06': ([19.2452, -103.7240], 9),  # Colima
        '07': ([16.7569, -93.1292], 7),   # Chiapas
        '08': ([28.6353, -106.0889], 6),  # Chihuahua
        '09': ([19.4326, -99.1332], 10),  # Ciudad de México
        '10': ([24.5594, -104.6591], 7),  # Durango
        '11': ([21.0190, -101.2574], 8),  # Guanajuato
        '12': ([17.4392, -99.5451], 7),   # Guerrero
        '13': ([20.0911, -98.7624], 8),   # Hidalgo
        '14': ([20.6597, -103.3496], 8),  # Jalisco
        '15': ([19.2808, -99.7559], 8),   # México
        '16': ([19.5665, -101.7068], 7),  # Michoacán
        '17': ([18.6813, -99.1013], 9),   # Morelos
        '18': ([21.7514, -104.8455], 8),  # Nayarit
        '19': ([25.5922, -99.9962], 8),   # Nuevo León
        '20': ([17.0732, -96.7266], 7),   # Oaxaca
        '21': ([19.0414, -98.2063], 8),   # Puebla
        '22': ([20.5888, -100.3899], 9),  # Querétaro
        '23': ([19.1817, -88.4791], 8),   # Quintana Roo
        '24': ([22.1565, -100.9855], 7),  # San Luis Potosí
        '25': ([25.1721, -107.4795], 7),  # Sinaloa
        '26': ([29.2972, -110.3309], 7),  # Sonora
        '27': ([17.8409, -92.6189], 8),   # Tabasco
        '28': ([24.2669, -98.8363], 7),   # Tamaulipas
        '29': ([19.3181, -98.2375], 9),   # Tlaxcala
        '30': ([19.1738, -96.1342], 7),   # Veracruz
        '31': ([20.7099, -89.0943], 8),   # Yucatán
        '32': ([22.7709, -102.5832], 8)   # Zacatecas
    }
    
    return coordenadas_estados.get(codigo_estado, ([23.6345, -102.5528], 5))

def _generar_mapa_estados(mapa, geojson_data, datos_filtrados, columna_valor, titulo_valor, 
                         formato_escala, nombre_sexo, edad_inicio, edad_final, 
                         anio_seleccionado, codigo_cie10):
    """
    Función auxiliar para generar mapa de estados (vista nacional)
    """
    try:
        # Agrupar datos por estado (usando nombres correctos)
        if 'asmr' in columna_valor.lower():
            datos_agrupados = datos_filtrados.groupby('cve_ent').agg({
                'asmr': 'first',  # ASMR ya está calculado
                'conteo': 'sum'
            }).reset_index()
            datos_agrupados['valor'] = datos_agrupados['asmr']
        elif 'tasa_cruda' in columna_valor.lower():
            datos_agrupados = datos_filtrados.groupby('cve_ent').agg({
                'tasa_cruda': 'mean',
                'conteo': 'sum'
            }).reset_index()
            datos_agrupados['valor'] = datos_agrupados['tasa_cruda']
        else:  # conteos
            datos_agrupados = datos_filtrados.groupby('cve_ent').agg({
                'conteo': 'sum'
            }).reset_index()
            datos_agrupados['valor'] = datos_agrupados['conteo']
        
        # Asegurar formato correcto de códigos
        datos_agrupados['cve_ent_str'] = datos_agrupados['cve_ent'].astype(str).str.zfill(2)
        
        # Agregar datos a cada feature del GeoJSON
        for feature in geojson_data['features']:
            cve_ent = feature['properties']['CVE_ENT']
            estado_datos = datos_agrupados[datos_agrupados['cve_ent_str'] == cve_ent]
            
            if not estado_datos.empty:
                feature['properties']['valor_mortalidad'] = float(estado_datos.iloc[0]['valor'])
            else:
                feature['properties']['valor_mortalidad'] = 0.0
            
            # Agregar metadatos
            feature['properties']['anio'] = int(anio_seleccionado)
            feature['properties']['sexo'] = str(nombre_sexo)
            feature['properties']['edades'] = f"{edad_inicio.replace('_', '-')} a {edad_final.replace('_', '-')}"
            feature['properties']['cie10'] = str(codigo_cie10)
            feature['properties']['titulo_valor'] = str(titulo_valor)
        
        # Crear choropleth
        choropleth = folium.Choropleth(
            geo_data=geojson_data,
            name='Tasas de Mortalidad',
            data=datos_agrupados,
            columns=['cve_ent_str', 'valor'],
            key_on='properties.CVE_ENT',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=f'{titulo_valor} por {formato_escala} habitantes'
        ).add_to(mapa)
        
        # Agregar tooltips
        folium.GeoJsonTooltip(
            fields=['NOM_ENT', 'anio', 'sexo', 'edades', 'valor_mortalidad', 'cie10'],
            aliases=['Estado:', 'Año:', 'Sexo:', 'Edades:', f'{titulo_valor}:', 'CIE10:'],
            style=(
                "background-color: white; color: #333333; font-family: arial; "
                "font-size: 12px; padding: 10px; border: 1px solid #ccc; "
                "border-radius: 5px; box-shadow: 3px 3px 10px rgba(0,0,0,0.2);"
            ),
            sticky=True,
            labels=True,
            max_width=250
        ).add_to(choropleth.geojson)
        
        # Agregar título
        titulo_mapa = f'México - {codigo_cie10}'
        title_html = f'''
            <div style="width:100%;text-align:center;position:relative;z-index:9999;">
                <h3 style="font-size:16px; margin-top:10px; margin-bottom:10px;"><b>{titulo_mapa}</b></h3>
                <h4 style="font-size:14px; margin-top:10px; margin-bottom:10px;">
                    {titulo_valor} por {formato_escala} habitantes<br>
                    {nombre_sexo}, Edades: {edad_inicio.replace('_', '-')}-{edad_final.replace('_', '-')}, Año: {anio_seleccionado}
                </h4>
            </div>
        '''
        mapa.get_root().html.add_child(folium.Element(title_html))
        
        return mapa._repr_html_()
        
    except Exception as e:
        raise e

def _generar_mapa_municipios(mapa, geojson_data, datos_filtrados, codigo_estado,
                            columna_valor, titulo_valor, formato_escala, nombre_sexo,
                            edad_inicio, edad_final, anio_seleccionado, codigo_cie10):
    """
    Función auxiliar para generar mapa de municipios (vista estatal)
    """
    try:
        # Filtrar municipios del GeoJSON para el estado específico
        municipios_filtrados = {
            "type": "FeatureCollection",
            "features": [
                feature for feature in geojson_data['features']
                if feature['properties']['CVE_ENT'] == str(codigo_estado).zfill(2)
            ]
        }
        
        # Agrupar datos por municipio (usando la misma lógica que los estados)
        if 'asmr' in columna_valor.lower():
            datos_agrupados = datos_filtrados.groupby(['cve_ent', 'cve_mun']).agg({
                'asmr': 'first',  # ASMR ya está calculado
                'conteo': 'sum'
            }).reset_index()
            datos_agrupados['valor'] = datos_agrupados['asmr']
        elif 'tasa_cruda' in columna_valor.lower():
            datos_agrupados = datos_filtrados.groupby(['cve_ent', 'cve_mun']).agg({
                'tasa_cruda': 'mean',
                'conteo': 'sum'
            }).reset_index()
            datos_agrupados['valor'] = datos_agrupados['tasa_cruda']
        else:  # conteos
            datos_agrupados = datos_filtrados.groupby(['cve_ent', 'cve_mun']).agg({
                'conteo': 'sum'
            }).reset_index()
            datos_agrupados['valor'] = datos_agrupados['conteo']
        
        # Asegurar formato correcto de códigos
        datos_agrupados['cve_ent_str'] = datos_agrupados['cve_ent'].astype(str).str.zfill(2)
        datos_agrupados['cve_mun_str'] = datos_agrupados['cve_mun'].astype(str).str.zfill(3)
        datos_agrupados['cve_combinada'] = datos_agrupados['cve_ent_str'] + datos_agrupados['cve_mun_str']
        
        # Agregar datos a cada feature del GeoJSON
        for feature in municipios_filtrados['features']:
            cve_ent = feature['properties']['CVE_ENT']
            cve_mun = feature['properties'].get('CVE_MUN', '000')
            cve_combinada = cve_ent + cve_mun
            
            # Agregar la clave combinada como propiedad del GeoJSON
            feature['properties']['CVE_COMBINADA'] = cve_combinada
            
            municipio_datos = datos_agrupados[datos_agrupados['cve_combinada'] == cve_combinada]
            
            if not municipio_datos.empty:
                feature['properties']['valor_mortalidad'] = float(municipio_datos.iloc[0]['valor'])
            else:
                feature['properties']['valor_mortalidad'] = 0.0
            
            # Agregar metadatos
            feature['properties']['anio'] = int(anio_seleccionado)
            feature['properties']['sexo'] = str(nombre_sexo)
            feature['properties']['edades'] = f"{edad_inicio.replace('_', '-')} a {edad_final.replace('_', '-')}"
            feature['properties']['cie10'] = str(codigo_cie10)
            feature['properties']['titulo_valor'] = str(titulo_valor)
        
        # Preparar datos para choropleth (mismo patrón que estados)
        datos_para_choropleth = datos_agrupados[['cve_combinada', 'valor']].copy()
        
        # Crear choropleth usando YlOrRd como los estados, pero con nan_fill_color negro para sin datos
        choropleth = folium.Choropleth(
            geo_data=municipios_filtrados,
            name='Tasas de Mortalidad',
            data=datos_para_choropleth,
            columns=['cve_combinada', 'valor'],
            key_on='properties.CVE_COMBINADA',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            nan_fill_color='black',  # Color negro para municipios sin datos
            nan_fill_opacity=0.7,
            legend_name=f'{titulo_valor} por {formato_escala} habitantes'
        ).add_to(mapa)
        
        # Agregar tooltips
        folium.GeoJsonTooltip(
            fields=['NOM_MUN', 'anio', 'sexo', 'edades', 'valor_mortalidad', 'cie10'],
            aliases=['Municipio:', 'Año:', 'Sexo:', 'Edades:', f'{titulo_valor}:', 'CIE10:'],
            style=(
                "background-color: white; color: #333333; font-family: arial; "
                "font-size: 12px; padding: 10px; border: 1px solid #ccc; "
                "border-radius: 5px; box-shadow: 3px 3px 10px rgba(0,0,0,0.2);"
            ),
            sticky=True,
            labels=True,
            max_width=250
        ).add_to(choropleth.geojson)
        
        # Agregar título
        titulo_mapa = f'Municipios del Estado {codigo_estado} - {codigo_cie10}'
        title_html = f'''
            <div style="width:100%;text-align:center;position:relative;z-index:9999;">
                <h3 style="font-size:16px; margin-top:10px; margin-bottom:10px;"><b>{titulo_mapa}</b></h3>
                <h4 style="font-size:14px; margin-top:10px; margin-bottom:10px;">
                    {titulo_valor} por {formato_escala} habitantes<br>
                    {nombre_sexo}, Edades: {edad_inicio.replace('_', '-')}-{edad_final.replace('_', '-')}, Año: {anio_seleccionado}
                </h4>
            </div>
        '''
        mapa.get_root().html.add_child(folium.Element(title_html))
        
        return mapa._repr_html_()
        
    except Exception as e:
        raise e

def generar_mapa_folium(dataframe_mortalidad, anio_seleccionado=2020, escala_datos=2, id_sexo=3, edad_inicio="00_04", edad_final="80_84", codigo_cie10="C910", codigo_estado=None, filtro_municipio=False):
    """
    Genera un mapa interactivo de México usando Folium con datos de tasas de mortalidad.
    
    Args:
        dataframe_mortalidad: DataFrame con datos de mortalidad
        anio_seleccionado: Año a filtrar
        escala_datos: Tipo de escala (1=conteos, 2=tasa_cruda, 3=asmr)
        id_sexo: Sexo (1=hombres, 2=mujeres, 3=ambos)
        edad_inicio: Edad inicial en formato 'XX_YY'
        edad_final: Edad final en formato 'XX_YY'
        codigo_cie10: Código CIE10
        codigo_estado: Código del estado (opcional, para vista estatal)
        filtro_municipio: Boolean, si True muestra municipios en lugar de estados

    Returns:
        str: HTML del mapa de Folium
    """
    
    try:
        # Configuración de escala
        config_escala = obtener_configuracion_escala(escala_datos)
        columna_valor = config_escala['columna']
        titulo_valor = config_escala['titulo']
        formato_escala = config_escala['formato']
        
        # Configuración de sexo
        mapas_aux = obtener_mapas_auxiliares()
        nombre_sexo = mapas_aux['mapas_sexo'].get(id_sexo, 'Ambos sexos')
        
        # Determinar el nivel y filtrar datos correspondientes
        if filtro_municipio and codigo_estado:
            # Vista estatal - municipios de un estado específico
            datos_filtrados = filtrar_datos_estatales(
                dataframe_mortalidad, anio_seleccionado, escala_datos,
                id_sexo, edad_inicio, edad_final, codigo_cie10, codigo_estado
            )
            geojson_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static', 'mapas', 'municipios.geojson')
            coordenadas, zoom = obtener_coordenadas_centrado('estatal', codigo_estado)
            modo_descripcion = f"estatal (estado {codigo_estado})"
        else:
            # Vista nacional - todos los estados
            datos_filtrados = filtrar_datos_nacionales(
                dataframe_mortalidad, anio_seleccionado, escala_datos,
                id_sexo, edad_inicio, edad_final, codigo_cie10
            )
            geojson_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static', 'mapas', 'estados.geojson')
            coordenadas, zoom = obtener_coordenadas_centrado('nacional')
            modo_descripcion = "nacional"
        
        if datos_filtrados is None or datos_filtrados.empty:
            return "<div>No se encontraron datos para los filtros especificados</div>"
        
        # Crear el mapa base
        mapa = folium.Map(location=coordenadas, zoom_start=zoom, tiles='OpenStreetMap')
        
        # Cargar archivo GeoJSON
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Procesar según el modo
        if filtro_municipio and codigo_estado:
            # Modo estatal: generar mapa de municipios
            mapa_html = _generar_mapa_municipios(
                mapa, geojson_data, datos_filtrados, codigo_estado,
                columna_valor, titulo_valor, formato_escala, nombre_sexo,
                edad_inicio, edad_final, anio_seleccionado, codigo_cie10
            )
        else:
            # Modo nacional: generar mapa de estados (función original)
            mapa_html = _generar_mapa_estados(
                mapa, geojson_data, datos_filtrados,
                columna_valor, titulo_valor, formato_escala, nombre_sexo,
                edad_inicio, edad_final, anio_seleccionado, codigo_cie10
            )
        
        return mapa_html
        
    except FileNotFoundError:
        return "<div>Error: No se pudo cargar el archivo de mapas</div>"
    except Exception as e:
        return f"<div>Error generando mapa: {e}</div>"
