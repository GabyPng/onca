# Documentación detallada del notebook `calculo_tasas.ipynb` por Laura :)


## Descripción general

Este notebook implementa el cálculo de tasas de mortalidad (crudas y estandarizadas, ASMR) para diferentes combinaciones de grupos de edad, sexo, año y nivel geográfico (municipal, estatal, nacional) en México. El flujo abarca desde la carga de datos y catálogos, el procesamiento de registros de defunciones, la generación de tasas, hasta la consolidación y exportación de los resultados finales en un archivo CSV listo para análisis y visualización.

---

## Índice
1. [Importación de librerías y módulos](#importacion-librerias)
2. [Definición de rutas de entrada](#rutas-entrada)
3. [Carga de catálogos y datos](#carga-catalogos)
4. [Carga y filtrado de registros de mortalidad](#carga-mortalidad)
5. [Configuración de escalas y grupos de edad](#configuracion-escalas)
6. [Bucle principal de cálculo de tasas](#bucle-principal)
7. [Consolidación y exportación de resultados](#consolidacion-exportacion)

---

## 1. <a name="importacion-librerias"></a>Importación de librerías y módulos

Se importan las librerías esenciales para el procesamiento de datos, operaciones numéricas y utilidades propias del proyecto:

```python
import pandas as pd
import onca_utils as ou
import numpy as np
import os
```

- **pandas**: Manipulación y análisis de datos tabulares.
- **numpy**: Operaciones numéricas y manejo de arrays.
- **os**: Operaciones de sistema de archivos.
- **onca_utils**: Módulo propio con utilidades para cargar catálogos y calcular tasas.

---

## 2. <a name="rutas-entrada"></a>Definición de rutas de entrada

Se definen las rutas a los archivos de entrada requeridos para el procesamiento:

```python
input_conapo_poblaciones = "/data3/onca_lite/requirements/poblaciones_group_quinq.csv"
poblaciones_who = "/data3/onca_lite/requirements/poblaciones_WHO.csv"
input_cat_entidades = "/data3/onca_lite/requirements/entidades_fed.csv"
input_cat_municipios = "/data3/onca_lite/requirements/municipios_geo.csv"
input_cat_edades = "/data3/onca_lite/requirements/EDADES.csv"
input_mortality_folder = "/data3/onca_lite/DATOS_CRUDOS/"
cie10 = "C910"
```

- **Archivos de población**: Para denominadores de tasas.
- **Catálogos**: Entidades, municipios y grupos de edad.
- **Registros de mortalidad**: Carpeta con los datos crudos de defunciones.
- **CIE10**: Código de causa de muerte a analizar.

---

## 3. <a name="carga-catalogos"></a>Carga de catálogos y datos

Se utilizan utilidades propias para cargar los catálogos y las poblaciones:

```python
catalog_loader = ou.CatalogLoader()
conapo_populations = catalog_loader.load_conapo_populations(input_conapo_poblaciones)
cat_entidades = catalog_loader.load_states(input_cat_entidades)
cat_municipios = catalog_loader.load_municipalities(input_cat_municipios)
cat_edades = catalog_loader.load_ages(input_cat_edades)
del(catalog_loader)
```

- **CatalogLoader**: Clase que centraliza la carga de catálogos.
- **cat_edades**: Permite mapear los rangos de edad a intervalos numéricos.

---

## 4. <a name="carga-mortalidad"></a>Carga y filtrado de registros de mortalidad

Se cargan los registros de defunciones y se filtran los años válidos:

```python
deaths = ou.DeathRegistryLoader().load_deaths(input_mortality_folder, cat_edades, cie10)
deaths = deaths[(deaths.ANIO_REGIS >= 2000) & (deaths.ANIO_REGIS != 9999)]
```

- **DeathRegistryLoader**: Clase para cargar y limpiar los registros de defunciones.
- **Filtrado**: Se excluyen años inválidos o registros sin año.

---

## 5. <a name="configuracion-escalas"></a>Configuración de escalas y grupos de edad

Se define la configuración de escalas y los grupos de edad estándar:

```python
scale_config = {
    'Municipal': {'code': 1, 'scale': '1K', 'factor': 1000},
    'Estatal': {'code': 2, 'scale': '10K', 'factor': 10000},
    'Nacional': {'code': 3, 'scale': '100K', 'factor': 100000}
}
def get_scale_config(nivel):
    return scale_config[nivel]

age_groups = np.array([...])
def create_edad_ranges(): ...
edad_ranges = create_edad_ranges()
```

- **scale_config**: Diccionario con la configuración de cada nivel geográfico.
- **age_groups**: Lista de los grupos de edad a analizar.
- **create_edad_ranges**: Función que mapea los rangos de edad a sus valores numéricos de inicio y fin.

---

## 6. <a name="bucle-principal"></a>Bucle principal de cálculo de tasas

El bucle anidado explora todas las combinaciones posibles de grupos de edad contiguos, para cada sexo y año, y para cada nivel geográfico. Este enfoque nos permite calcular tasas para intervalos de edad simples y compuestos.

### Lógica del bucle

1. **Recorrido de combinaciones de grupos de edad:**
   - El bucle externo (`l`) define la longitud del intervalo de edad 
   - El bucle interno (`i`) recorre los posibles inicios de cada intervalo dentro del arreglo de grupos de edad, asegurando que no se exceda el rango.
   - Así, `current_age_groups = age_groups[i:i+l]` selecciona el subconjunto de grupos de edad a analizar en esa iteración.


### Flexibilidad del codigo a futuro.

    - **Población estándar ajustable:**
    - El cálculo de la ASMR utiliza una población estándar WHO, pero el código está preparado para aceptar cualquier otra población estándar simplemente cambiando el dataframe o archivo de referencia (`pop_std`). Esto permite adaptar el análisis a estándares nacionales, regionales o personalizados en el futuro.

    - **Campos geográficos escalables:**
    - Actualmente se consideran entidad y municipio, pero la lógica de filtrado y agrupación puede extenderse fácilmente para incluir otros niveles geográficos (región, distrito, localidad) o variables adicionales (por ejemplo, área urbana o rural, marginación, etc.).

    - Para agregar un nuevo campo, basta con:
        - **Incluirlo en las claves de filtrado:** Por ejemplo, si agregas el nivel geográfico `localidad` (más bajo que municipio), deberás filtrar los registros así: `deaths[(deaths['CVE_LOC'] == valor)]` y lo mismo para la población.
        - **Agregarlo en la estructura de los resultados:** Incluir el campo en el diccionario o dataframe donde se almacenan los resultados, por ejemplo:
          ```python
          resultados.append({
              'ANIO': year,
              'SEXO': sex,
              'EDAD_INI': current_age_groups[0],
              'EDAD_FIN': current_age_groups[-1],
              'CVE_ENT': cve_ent,
              'CVE_MUN': cve_mun,
              'CVE_LOC': cve_loc,  # Nuevo campo para localidad
              ...
          })
          ```
        - **Ajustar el merge:** Incluir el nuevo campo en la lista de columnas clave para el merge, por ejemplo:
          ```python
          pd.merge(
              df_tasas_crudas,
              df_tasas_asmr,
              on=['ANIO_REGIS', 'SEXO', 'EDAD_INI', 'EDAD_FIN', 'CVE_ENT', 'CVE_MUN', 'CVE_LOC']
          )
          ```

        - **Modificar la exportación final:** Asegurarse de que el nuevo campo esté presente en el dataframe final exportado a CSV y, si es necesario, documentarlo en la descripción de columnas.


2. **Filtrado de registros:**
   - Para cada combinación de año, sexo y grupo de edad, se filtran los registros de defunciones y las poblaciones correspondientes.
   - El filtrado puede incluir condiciones adicionales, como entidad, municipio o causa específica (CIE10).

3. **Cálculo de tasas:**
   - Se utilizan las clases `MortalityCalculator` y `MortalityStandardizer` de `onca_utils` para calcular:
     - **Tasa cruda**: Número de defunciones dividido entre la población, multiplicado por el factor de escala.
     - **ASMR**: Tasa ajustada por edad usando una población estándar (en nuestro caso, WHO).
   - Los resultados se almacenan en listas o dataframes temporales, junto con las claves de combinación (año, sexo, grupo de edad, entidad, municipio, etc.).

4. **Manejo de casos especiales:**
   - Si no existen defunciones o población para una combinación, se puede registrar un valor nulo o cero, según la lógica del análisis.
   - Se documenta la ausencia de datos para facilitar la interpretación posterior.

### Ejemplo de bloque de código
```python
for l in np.arange(arr_l) + 1:  # Longitud del intervalo de edad
    for i in np.arange(arr_l - l + 1):  # Posición de inicio del intervalo
        current_age_groups = age_groups[i:i+l]
        for year in years:
            for sex in sexes:
                # Filtrar defunciones y población
                deaths_sub = deaths[(deaths['ANIO_REGIS'] == year) & (deaths['SEXO'] == sex) & (deaths['EDAD'].isin(current_age_groups))]
                pop_sub = pop[(pop['ANIO'] == year) & (pop['SEXO'] == sex) & (pop['EDAD'].isin(current_age_groups))]
                # Calcular tasas si hay datos
                if not deaths_sub.empty and not pop_sub.empty:
                    tasa_cruda = MortalityCalculator().calculate(deaths_sub, pop_sub, escala)
                    tasa_asmr = MortalityStandardizer().calculate(deaths_sub, pop_sub, pop_std)
                    # Guardar resultados
                    resultados.append({
                        'ANIO': year,
                        'SEXO': sex,
                        'EDAD_INI': current_age_groups[0],
                        'EDAD_FIN': current_age_groups[-1],
                        'TASA_CRUDA': tasa_cruda,
                        'ASMR': tasa_asmr,
                        # ...otros campos clave...
                    })
                else:
                    # Registrar ausencia de datos
                    resultados.append({
                        'ANIO': year,
                        'SEXO': sex,
                        'EDAD_INI': current_age_groups[0],
                        'EDAD_FIN': current_age_groups[-1],
                        'TASA_CRUDA': None,
                        'ASMR': None,
                        # ...otros campos clave...
                    })
```


---

## 7. <a name="consolidacion-exportacion"></a>Consolidación y exportación de resultados

Esta sección sirve para transformar los resultados de los cálculos de tasas en un archivo final limpio para análisis y/o visualización. El proceso implica varias etapas:

### a) Consolidación de resultados

Durante el bucle principal, los resultados de tasas crudas y estandarizadas (ASMR) se almacenan en listas o dataframes separados, generalmente por nivel geográfico (municipal, estatal, nacional) y por tipo de tasa. Al finalizar los cálculos:

- **Agrupación**: Se agrupan los resultados por las claves relevantes (año, sexo, grupo de edad, entidad, municipio, etc.).
- **Limpieza**: Se eliminan duplicados y se asegura la consistencia de los datos (por ejemplo, que no haya combinaciones imposibles o registros vacíos).
- **Conversión de tipos**: Se convierten los tipos de datos para asegurar compatibilidad (por ejemplo, enteros para códigos, floats para tasas).

### b) Unión (merge) de tasas crudas y ASMR

Para cada nivel geográfico, se realiza un merge entre los dataframes de tasas crudas y ASMR usando columnas clave como identificadores geográficos, año, sexo y grupo de edad. Esto permite que cada fila del resultado final contenga tanto la tasa cruda como la estandarizada para la misma combinación de variables.

**Ejemplo de código:**
```python
df_final = pd.merge(df_tasas_crudas, df_tasas_asmr, on=['ANIO_REGIS', 'SEXO', 'EDAD_INI', 'EDAD_FIN', 'CVE_ENT', 'CVE_MUN'], how='outer')
```

**Consideraciones:**
- Se utiliza `how='outer'` para no perder combinaciones que puedan estar presentes solo en uno de los dos conjuntos.
- Se renombran columnas si es necesario para evitar ambigüedades.

### c) Exportación a CSV

El dataframe consolidado se exporta a un archivo CSV en la carpeta `output`. Se recomienda:
- Usar `index=False` para evitar columnas de índice innecesarias.
- Especificar el encoding (`utf-8` o `latin1`) según el uso previsto.
- Validar que no haya valores nulos críticos antes de exportar.

**Ejemplo de código:**
```python
df_final.to_csv('output/tasas_mortalidad_consolidado.csv', index=False, encoding='utf-8')
```

### d) Estadísticas y validación

Tras la exportación, es buena práctica imprimir estadísticas de completitud y consistencia, por ejemplo:
- Número total de filas exportadas.
- Conteo de combinaciones únicas de año, sexo, grupo de edad, entidad, municipio.
- Porcentaje de valores nulos en columnas clave.

**Ejemplo de una validación:**
```python
print('Filas exportadas:', len(df_final))
print('Combinaciones únicas de año:', df_final['ANIO_REGIS'].nunique())
print('Valores nulos por columna:', df_final.isnull().mean())
```

---
## Ejemplo de docstring para una función clave

```python
def get_scale_config(nivel):
    """
    Devuelve la configuración de escala para el nivel geográfico solicitado.

    Parámetros:
        nivel (str): Uno de 'Municipal', 'Estatal', 'Nacional'.

    Retorna:
        dict: Diccionario con código, escala y factor de multiplicación.
    """
    return scale_config[nivel]
```

---

**Autor:** ONCA-Lite  
**Fecha:** Julio 2025
