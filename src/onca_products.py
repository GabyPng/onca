import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import json
import janitor
import folium
import geopandas as gpd
from folium import plugins

class ProductGenerator:
    def create_lineplot(self, data: pd.DataFrame, x: str, y: str, color: str, output_path: str,
                        cie10: str, place: str, scale: str, hover_data: list, cve_geo: str, sex: str) -> None:

        fig_title = f"{place} age-specific rate per {scale} inhabitants, {sex}"
        fig = px.line(data.sort_values([color,x]),
                        x=x,
                        y=y,
                        color=color,
                        hover_name=color,
                        hover_data=hover_data,
                        width=1080,
                        height=720,
                        markers=True)
        
        years = data.sort_values(x)[x].unique()
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title=f"Mortality rate per {scale} inhabitants",
            title_text=fig_title,
            legend_title="Age group",
            xaxis = dict(
                tickmode = 'array',
                tickvals = years,
                ticktext = years,
                tickangle = 45
            )
        )

        min_year = data[x].min()
        max_year = data[x].max()
        age_groups = data.sort_values(color)[color].unique()
        min_age = age_groups[0].split("_")[0]
        max_age = age_groups[-1].split("_")[-1]
        file_name = f"lineplot_{cie10}_" + f"[{min_year}-{max_year}]_" + f"{cve_geo}_" + sex.replace(" ","") + "_" + f"[{min_age}-{max_age}]_" + y.lower().replace('_', '')
        fig.write_html(output_path + "/" + file_name + ".html")
        data[[x,color,y]].to_csv(output_path + "/" + file_name + ".csv", index=False)
        
    def create_state_map(self, data: pd.DataFrame, geojson_file_path: str, x: str, y: str, output_path: str,
                        cie10: str, place: str, rate: str, scale: str, hover_data: list, labels: dict,
                        cve_geo: str, sex: str, ages: str, year: str) -> None:

        fig_title = f"{rate} per {scale} inhabitants, {place}, {sex}, age[{ages}], in {year}"
        
        geo = json.load(open(geojson_file_path,"r"))

        fig = px.choropleth_mapbox(data, geojson=geo, locations=x, 
                                featureidkey="properties.CVE_ENT",
                                color=y,
                                hover_data=hover_data,
                                labels=labels,
                                color_continuous_scale="YlOrRd",
                                mapbox_style="carto-positron",
                                zoom=4,
                                center={"lat":22.3969, "lon": -101.2833},
                                opacity=0.5,
                                title=fig_title)
        
        file_name = f"states_map_{cie10}_" + f"{year}_" + f"{cve_geo}_" + sex.replace(" ","") + "_" + f"[{ages}]_" + y.lower().replace('_', '')
        fig.write_html(output_path + "/" + file_name + ".html")
        data[hover_data].to_csv(output_path + "/" + file_name + ".csv", index=False)
        
    def create_municipality_map(self, data: pd.DataFrame, geojson_file_path: str, x: str, y: str, output_path: str,
                        cie10: str, place: str, rate: str, scale: str, hover_data: list, labels: dict,
                        cve_geo: str, sex: str, ages: str, year: str) -> None:

        fig_title = f"{rate} per {scale} inhabitants, {place}, {sex}, age[{ages}], in {year}"
        
        geo = json.load(open(geojson_file_path,"r"))

        fig = px.choropleth_mapbox(data, geojson=geo, locations=x, 
                                featureidkey="properties.CVEGEO",
                                color=y,
                                hover_data=hover_data,
                                labels=labels,
                                color_continuous_scale="YlOrRd",
                                mapbox_style="carto-positron",
                                zoom=4,
                                center={"lat":22.3969, "lon": -101.2833},
                                opacity=0.5,
                                title=fig_title)
        
        file_name = f"municipalities_map_{cie10}_" + f"{year}_" + f"{cve_geo}_" + \
            sex.replace(" ","") + "_" + y.lower().replace('_', '')
        fig.write_html(output_path + "/" + file_name + ".html")
        data[hover_data].to_csv(output_path + "/" + file_name + ".csv", index=False)

    # Esta funcione esta incompleta
    def create_age_state_heatmap(self, data: pd.DataFrame, x: str, y: str, z: str, output_path: str,
                        cie10: str, place: str, rate: str, scale: str, hover_data: list, labels: dict,
                        cve_geo: str, sex: str, ages: str, year: str) -> None:
        
        ######## hacer esto fuera de la funcion
        df_cancer_c = estados.complete("ENT_NOMBRE","RANGO_EDAD").fillna(0, downcast='infer')
        df_cancer_c = df_cancer_c.sort_values(by=["TASA_EST_2_1_100k"], ascending=False)
        ########

        fig_title = f"{rate} per {scale} inhabitants, {place}, {sex}, age[{ages}], in {year}"

        fig = px.density_heatmap(data.round(2), 
                                x=x, 
                                y=y, 
                                z=z,
                                width=1080, 
                                height=480,
                                text_auto=True
                                )
        fig.update_layout(
            title=fig_title,
            yaxis_title="Age",
            xaxis_title="State"
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(coloraxis_colorbar_title_text = 'SMR')
        fig.write_image("outputs/heatmap_tasas_estandarizadas_2022.pdf")
        fig.show()

    def create_folium_map(self, data: pd.DataFrame, geojson_file_path: str, geo_key: str, data_key: str, 
                         value_column: str, output_path: str, cie10: str, place: str, rate: str, scale: str, 
                         sex: str, ages: str, year: str, color_scheme: str = 'YlOrRd') -> None:
        """
        Crea un mapa interactivo con Folium usando datos de tasas de mortalidad
        
        Args:
            data: DataFrame con los datos de mortalidad
            geojson_file_path: Ruta al archivo GeoJSON
            geo_key: Clave en el GeoJSON para hacer el join (ej: 'properties.CVE_ENT')
            data_key: Columna en el DataFrame para hacer el join (ej: 'CVE_ENT')
            value_column: Columna con los valores a mapear (ej: 'TASA_CRUDA')
            output_path: Directorio donde guardar el mapa
            cie10: Código CIE10
            place: Nombre del lugar (ej: 'México')
            rate: Tipo de tasa (ej: 'Crude mortality rate')
            scale: Escala (ej: '100,000')
            sex: Sexo
            ages: Rangos de edad
            year: Año
            color_scheme: Esquema de colores para el mapa
        """
        
        # Crear el mapa base centrado en México
        m = folium.Map(
            location=[23.6345, -102.5528],  # Centro de México
            zoom_start=5,
            tiles='OpenStreetMap'
        )
        
        # Crear el choropleth
        choropleth = folium.Choropleth(
            geo_data=geojson_file_path,
            name='Tasas de Mortalidad',
            data=data,
            columns=[data_key, value_column],
            key_on=geo_key,
            fill_color=color_scheme,
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=f'{rate} per {scale} inhabitants'
        ).add_to(m)
        
        # Agregar tooltips con información detallada
        choropleth.geojson.add_child(
            folium.features.GeoJsonTooltip(
                fields=['NOM_ENT'] if 'CVE_ENT' in geo_key else ['NOMGEO'],
                aliases=['Estado:'] if 'CVE_ENT' in geo_key else ['Municipio:'],
                style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
            )
        )
        
        # Crear un DataFrame para mostrar información adicional en popups
        for idx, row in data.iterrows():
            # Buscar la geometría correspondiente
            try:
                # Leer el GeoJSON
                gdf = gpd.read_file(geojson_file_path)
                
                # Hacer el join basado en la clave
                if 'CVE_ENT' in geo_key:
                    matching_geom = gdf[gdf['CVE_ENT'] == str(row[data_key]).zfill(2)]
                    location_name = matching_geom['NOM_ENT'].iloc[0] if not matching_geom.empty else 'Desconocido'
                else:
                    matching_geom = gdf[gdf['CVEGEO'] == str(row[data_key])]
                    location_name = matching_geom['NOMGEO'].iloc[0] if not matching_geom.empty else 'Desconocido'
                
                if not matching_geom.empty:
                    # Obtener el centroide para colocar el marcador
                    centroid = matching_geom.geometry.centroid.iloc[0]
                    
                    # Crear popup con información detallada
                    popup_html = f"""
                    <div style="font-family: Arial; font-size: 12px; width: 200px;">
                        <h4 style="margin: 0; color: #333;">{location_name}</h4>
                        <hr style="margin: 5px 0;">
                        <b>Año:</b> {year}<br>
                        <b>Sexo:</b> {sex}<br>
                        <b>Edades:</b> {ages}<br>
                        <b>{rate}:</b> {row[value_column]:.2f} per {scale}<br>
                        <b>CIE10:</b> {cie10}
                    </div>
                    """
                    
                    folium.Marker(
                        location=[centroid.y, centroid.x],
                        popup=folium.Popup(popup_html, max_width=250),
                        icon=folium.Icon(color='red', icon='info-sign', prefix='glyphicon')
                    ).add_to(m)
                    
            except Exception as e:
                print(f"Error procesando fila {idx}: {e}")
                continue
        
        # Agregar controles del mapa
        folium.LayerControl().add_to(m)
        
        # Agregar plugin de pantalla completa
        plugins.Fullscreen().add_to(m)
        
        # Agregar título al mapa
        title_html = f'''
                     <h3 align="center" style="font-size:16px; margin-top:0;"><b>{place}</b></h3>
                     <h4 align="center" style="font-size:14px; margin-top:-15px;">
                     {rate} per {scale} inhabitants<br>
                     {sex}, Age: {ages}, Year: {year}
                     </h4>
                     '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Guardar el mapa
        file_name = f"folium_map_{cie10}_{year}_{sex.replace(' ', '')}_{ages.replace('-', '_')}"
        output_file = f"{output_path}/{file_name}.html"
        m.save(output_file)
        
        print(f"Mapa guardado en: {output_file}")
        return m