import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import io

# Configuración de la página
st.set_page_config(
    page_title="Tasa Recompra TLL",
    page_icon="📊",
    layout="wide"
)

# ============================================
# CONFIGURACIÓN: ID del archivo de Google Drive
# ============================================
GOOGLE_DRIVE_FILE_ID = "1CCKbRsijh7qls7-tUWgVoeHhlGHTrflY"
# ============================================

# Función para cargar datos desde Google Drive
@st.cache_data(ttl=3600)  # Cache por 1 hora
def cargar_datos_desde_drive(file_id):
    """Carga el CSV desde Google Drive y convierte las fechas correctamente"""
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        df = pd.read_csv(url)
        # Convertir la columna de fecha AQUÍ, una sola vez, en formato DD/MM/YYYY
        columna_fecha = df.columns[2]  # Columna C [2]
        df[columna_fecha] = pd.to_datetime(df[columna_fecha], format='%d/%m/%Y', errors='coerce')
        return df, None
    except Exception as e:
        return None, str(e)

def temporalidad(df):
    """
    Identifica el año actual (último año con datos) y los 3 años anteriores.

    Args:
        df: DataFrame con los datos de ventas (con fechas ya convertidas)

    Returns:
        dict: Diccionario con año_actual y lista de años_anteriores
    """
    columna_fecha = df.columns[2]  # Columna C [2]

    # Obtener años (la fecha ya viene convertida desde cargar_datos_desde_drive)
    df_temp = df.copy()
    df_temp['Año'] = df_temp[columna_fecha].dt.year

    # Obtener el último año con datos
    año_actual = int(df_temp['Año'].max())

    # Calcular los 3 años anteriores
    años_anteriores = [año_actual - 1, año_actual - 2, año_actual - 3]

    return {
        'año_actual': año_actual,
        'años_anteriores': años_anteriores,
        'todos_años': [año_actual] + años_anteriores
    }

def analisis_recompra(df):
    """
    Función principal que realiza el análisis de recompra de los 3 años anteriores.
    Incluye filtros, procesamiento y visualización de datos.
    """
    # Obtener temporalidad
    temp = temporalidad(df)
    años_anteriores = temp['años_anteriores']  # Los 3 años anteriores al actual
    año_1, año_2, año_3 = años_anteriores[0], años_anteriores[1], años_anteriores[2]

    # SECCIÓN DE FILTROS
    st.header("🔍 Filtros de Análisis")
    st.info(f"📅 Analizando los años: **{año_3}, {año_2}, {año_1}** (3 años anteriores)")

    col1, col2, col3, col4 = st.columns(4)

    # Obtener nombres de columnas
    columna_tipo_asesor = df.columns[11]  # Columna L
    columna_departamento = df.columns[13]  # Columna N
    columna_familia = df.columns[18]  # Columna S
    columna_area = df.columns[22]  # Columna W

    with col1:
        st.subheader("👤 Asesor")
        valores_asesor = ['Todos'] + sorted(df[columna_tipo_asesor].dropna().unique().tolist())
        filtro_asesor = st.multiselect(
            "Selecciona tipo(s) de asesor:",
            valores_asesor,
            default=['Todos'],
            key='asesor'
        )

    with col2:
        st.subheader("🏢 CDS")
        valores_depto = ['Todos'] + sorted(df[columna_departamento].dropna().unique().tolist())
        filtro_depto = st.multiselect(
            "Selecciona departamento(s):",
            valores_depto,
            default=['Todos'],
            key='depto'
        )

    with col3:
        st.subheader("🛞 Producto")
        valores_familia = ['Todos'] + sorted(df[columna_familia].dropna().unique().tolist())
        filtro_familia = st.multiselect(
            "Selecciona familia(s):",
            valores_familia,
            default=['Todos'],
            key='familia'
        )

    with col4:
        st.subheader("📍 Área")
        valores_area = ['Todos'] + sorted(df[columna_area].dropna().unique().tolist())
        filtro_area = st.multiselect(
            "Selecciona área(s):",
            valores_area,
            default=['Todos'],
            key='area'
        )

    st.markdown("---")

    # Botón de análisis
    if st.button("🚀 ANALIZAR DATOS", type="primary", use_container_width=True, key='btn_analizar_recompra'):

        with st.spinner('Procesando datos...'):

            # Aplicar filtros
            df_filtrado = df.copy()

            if 'Todos' not in filtro_asesor:
                df_filtrado = df_filtrado[df_filtrado[columna_tipo_asesor].isin(filtro_asesor)]

            if 'Todos' not in filtro_depto:
                df_filtrado = df_filtrado[df_filtrado[columna_departamento].isin(filtro_depto)]

            if 'Todos' not in filtro_familia:
                df_filtrado = df_filtrado[df_filtrado[columna_familia].isin(filtro_familia)]

            if 'Todos' not in filtro_area:
                df_filtrado = df_filtrado[df_filtrado[columna_area].isin(filtro_area)]

            # Filtrar solo los 3 años anteriores (la fecha ya viene convertida)
            columna_fecha = df_filtrado.columns[2]
            df_filtrado['Año'] = df_filtrado[columna_fecha].dt.year
            df_filtrado = df_filtrado[df_filtrado['Año'].isin(años_anteriores)]

            # Verificar si hay datos después del filtro
            if len(df_filtrado) == 0:
                st.error("❌ No hay datos que coincidan con los filtros seleccionados. Por favor, ajusta tus criterios.")
            else:
                st.success(f"✅ Se encontraron {len(df_filtrado)} registros con los filtros aplicados")

                # Procesar datos
                columna_id = df_filtrado.columns[3]
                columna_nombre = df_filtrado.columns[4]

                df_limpio = df_filtrado.dropna(subset=[columna_id, columna_nombre])

                visitas_por_año = df_limpio.groupby([columna_id, columna_nombre, 'Año']).size().reset_index(name='Visitas')

                tabla_final = visitas_por_año.pivot_table(
                    index=[columna_id, columna_nombre],
                    columns='Año',
                    values='Visitas',
                    fill_value=0
                ).reset_index()

                tabla_final.columns.name = None
                año_cols = [col for col in tabla_final.columns if isinstance(col, (int, float))]
                for año in año_cols:
                    tabla_final.rename(columns={año: f'Visitas_{int(año)}'}, inplace=True)

                columnas_visitas = [col for col in tabla_final.columns if col.startswith('Visitas_')]
                tabla_final['Total_Visitas'] = tabla_final[columnas_visitas].sum(axis=1)
                tabla_final = tabla_final.sort_values('Total_Visitas', ascending=False)

                # Calcular métricas
                clientes_por_año = {}

                for año in años_anteriores:
                    col_año = f'Visitas_{año}'
                    if col_año in tabla_final.columns:
                        clientes_por_año[str(año)] = len(tabla_final[tabla_final[col_año] > 0])

                # Calcular recompras entre años
                clientes_año1_año2 = 0
                clientes_año2_año3 = 0
                clientes_año1_año3 = 0
                clientes_tres_años = 0

                col_año1 = f'Visitas_{año_1}'
                col_año2 = f'Visitas_{año_2}'
                col_año3 = f'Visitas_{año_3}'

                if col_año1 in tabla_final.columns and col_año2 in tabla_final.columns:
                    clientes_año1_año2 = len(tabla_final[(tabla_final[col_año1] > 0) & (tabla_final[col_año2] > 0)])

                if col_año2 in tabla_final.columns and col_año3 in tabla_final.columns:
                    clientes_año2_año3 = len(tabla_final[(tabla_final[col_año2] > 0) & (tabla_final[col_año3] > 0)])

                if col_año1 in tabla_final.columns and col_año3 in tabla_final.columns:
                    clientes_año1_año3 = len(tabla_final[(tabla_final[col_año1] > 0) & (tabla_final[col_año3] > 0)])

                if all(col in tabla_final.columns for col in [col_año1, col_año2, col_año3]):
                    clientes_tres_años = len(tabla_final[(tabla_final[col_año1] > 0) &
                                                          (tabla_final[col_año2] > 0) &
                                                          (tabla_final[col_año3] > 0)])

                total_clientes_año1 = clientes_por_año.get(str(año_1), 0)

                categorias = [f'{año_2} a {año_1}', f'{año_3} a {año_2}', f'{año_3} a {año_1}', 'Los 3 años']
                valores = [clientes_año1_año2, clientes_año2_año3, clientes_año1_año3, clientes_tres_años]

                if total_clientes_año1 > 0:
                    porcentajes = [(v / total_clientes_año1) * 100 for v in valores]
                else:
                    porcentajes = [0, 0, 0, 0]

                # Mostrar métricas principales
                st.markdown("---")
                st.header("📈 Métricas Principales")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Clientes Únicos", len(tabla_final))
                with col2:
                    st.metric(f"Clientes {año_3}", clientes_por_año.get(str(año_3), 0))
                with col3:
                    st.metric(f"Clientes {año_2}", clientes_por_año.get(str(año_2), 0))
                with col4:
                    st.metric(f"Clientes {año_1}", clientes_por_año.get(str(año_1), 0))

                # GRÁFICAS
                st.markdown("---")
                st.header("📊 Gráficas de Análisis")

                # Gráfica 1
                st.subheader("Gráfica 1: Total de clientes por año")
                fig1, ax1 = plt.subplots(figsize=(10, 6))
                años_labels = list(clientes_por_año.keys())
                valores_años = list(clientes_por_año.values())
                colores_años = ['#f39c12', '#16a085', '#8e44ad']

                barras = ax1.bar(años_labels, valores_años, color=colores_años[:len(años_labels)],
                                 edgecolor='black', linewidth=1.5, width=0.6)

                for barra, valor in zip(barras, valores_años):
                    altura = barra.get_height()
                    ax1.text(barra.get_x() + barra.get_width()/2., altura,
                            f'{int(valor)}', ha='center', va='bottom', fontsize=13, fontweight='bold')

                ax1.set_title('Gráfica 1: Total de clientes por año', fontsize=15, fontweight='bold', pad=20)
                ax1.set_ylabel('Número de Clientes', fontsize=12)
                ax1.set_xlabel('Año', fontsize=12)
                ax1.grid(axis='y', alpha=0.3, linestyle='--')
                plt.tight_layout()
                st.pyplot(fig1)

                # Gráfica 2
                st.subheader("Gráfica 2: Cantidad de recompra en combinaciones por años")
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                colores = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6']

                barras = ax2.bar(categorias, valores, color=colores, edgecolor='black', linewidth=1.5)

                for barra, valor in zip(barras, valores):
                    altura = barra.get_height()
                    ax2.text(barra.get_x() + barra.get_width()/2., altura,
                            f'{int(valor)}', ha='center', va='bottom', fontsize=12, fontweight='bold')

                ax2.set_title('Gráfica 2: Cantidad de recompra en combinaciones por años',
                             fontsize=15, fontweight='bold', pad=20)
                ax2.set_ylabel('Número de Clientes', fontsize=12)
                ax2.grid(axis='y', alpha=0.3, linestyle='--')
                plt.xticks(rotation=15, ha='right')
                plt.tight_layout()
                st.pyplot(fig2)

                # Gráfica 3
                st.subheader(f"Gráfica 3: Porcentaje de recompra en relación a clientes {año_1}")
                fig3, ax3 = plt.subplots(figsize=(10, 6))

                barras = ax3.bar(categorias, porcentajes, color=colores, edgecolor='black', linewidth=1.5)

                for barra, porcentaje in zip(barras, porcentajes):
                    altura = barra.get_height()
                    ax3.text(barra.get_x() + barra.get_width()/2., altura,
                            f'{porcentaje:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

                ax3.set_title(f'Gráfica 3: Porcentaje de recompra en relación a cantidad de clientes {año_1}',
                             fontsize=15, fontweight='bold', pad=20)
                ax3.set_ylabel('Porcentaje (%)', fontsize=12)
                ax3.grid(axis='y', alpha=0.3, linestyle='--')
                plt.xticks(rotation=15, ha='right')
                ax3.set_ylim(0, max(porcentajes) * 1.15 if max(porcentajes) > 0 else 100)
                plt.tight_layout()
                st.pyplot(fig3)

                # DESCARGAS
                st.markdown("---")
                st.header("💾 Descargar Resultados")

                col1, col2 = st.columns(2)

                with col1:
                    # Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        stats_generales = pd.DataFrame({
                            'Métrica': ['Total de clientes únicos', 'Años analizados'],
                            'Valor': [len(tabla_final), ', '.join([col.replace('Visitas_', '') for col in columnas_visitas])]
                        })
                        stats_generales.to_excel(writer, sheet_name='Estadísticas Generales', index=False)

                        clientes_año_df = pd.DataFrame({
                            'Año': list(clientes_por_año.keys()),
                            'Total de Clientes': list(clientes_por_año.values())
                        })
                        clientes_año_df.to_excel(writer, sheet_name='Clientes por Año', index=False)

                        retencion_df = pd.DataFrame({
                            'Combinación de Años': categorias,
                            'Cantidad de Clientes': valores
                        })
                        retencion_df.to_excel(writer, sheet_name='Retención de Clientes', index=False)

                        porcentajes_df = pd.DataFrame({
                            'Combinación de Años': categorias,
                            'Cantidad de Clientes': valores,
                            f'Porcentaje respecto a {año_1}': [f"{p:.2f}%" for p in porcentajes]
                        })
                        porcentajes_df.to_excel(writer, sheet_name='Resumen de Porcentajes', index=False)

                        tabla_final.to_excel(writer, sheet_name='Datos Completos', index=False)

                    output.seek(0)
                    st.download_button(
                        label="📥 Descargar Excel Completo",
                        data=output,
                        file_name="analisis_completo_clientes.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col2:
                    # CSV
                    csv = tabla_final.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Descargar CSV de Datos",
                        data=csv,
                        file_name="frecuencia_clientes.csv",
                        mime="text/csv"
                    )

                st.success("✅ Análisis completado exitosamente!")

def fidelizacion_clientes(df):
    """
    Función que identifica clientes que NO han regresado en el año actual
    pero que sí compraron en años anteriores.
    Incluye filtros y muestra análisis detallado por año.
    """
    # Obtener temporalidad
    temp = temporalidad(df)
    año_actual = temp['año_actual']
    años_anteriores = temp['años_anteriores']
    año_1, año_2, año_3 = años_anteriores[0], años_anteriores[1], años_anteriores[2]

    st.header("🔄 Fidelización de Clientes")
    st.info(f"📅 Año actual: **{año_actual}** | Años anteriores: **{año_1}, {año_2}, {año_3}**")

    # SECCIÓN DE FILTROS (igual que analisis_recompra)
    st.header("🔍 Filtros de Análisis")

    col1, col2, col3, col4 = st.columns(4)

    # Obtener nombres de columnas
    columna_tipo_asesor = df.columns[11]  # Columna L
    columna_departamento = df.columns[13]  # Columna N
    columna_familia = df.columns[18]  # Columna S
    columna_area = df.columns[22]  # Columna W

    with col1:
        st.subheader("👤 Asesor")
        valores_asesor = ['Todos'] + sorted(df[columna_tipo_asesor].dropna().unique().tolist())
        filtro_asesor = st.multiselect(
            "Selecciona tipo(s) de asesor:",
            valores_asesor,
            default=['Todos'],
            key='asesor_fidelizacion'
        )

    with col2:
        st.subheader("🏢 CDS")
        valores_depto = ['Todos'] + sorted(df[columna_departamento].dropna().unique().tolist())
        filtro_depto = st.multiselect(
            "Selecciona departamento(s):",
            valores_depto,
            default=['Todos'],
            key='depto_fidelizacion'
        )

    with col3:
        st.subheader("🛞 Producto")
        valores_familia = ['Todos'] + sorted(df[columna_familia].dropna().unique().tolist())
        filtro_familia = st.multiselect(
            "Selecciona familia(s):",
            valores_familia,
            default=['Todos'],
            key='familia_fidelizacion'
        )

    with col4:
        st.subheader("📍 Área")
        valores_area = ['Todos'] + sorted(df[columna_area].dropna().unique().tolist())
        filtro_area = st.multiselect(
            "Selecciona área(s):",
            valores_area,
            default=['Todos'],
            key='area_fidelizacion'
        )

    st.markdown("---")

    if st.button("🔍 ANALIZAR FIDELIZACIÓN", type="primary", use_container_width=True, key='btn_fidelizacion'):

        with st.spinner('Procesando datos...'):

            # Aplicar filtros
            df_filtrado = df.copy()

            if 'Todos' not in filtro_asesor:
                df_filtrado = df_filtrado[df_filtrado[columna_tipo_asesor].isin(filtro_asesor)]

            if 'Todos' not in filtro_depto:
                df_filtrado = df_filtrado[df_filtrado[columna_departamento].isin(filtro_depto)]

            if 'Todos' not in filtro_familia:
                df_filtrado = df_filtrado[df_filtrado[columna_familia].isin(filtro_familia)]

            if 'Todos' not in filtro_area:
                df_filtrado = df_filtrado[df_filtrado[columna_area].isin(filtro_area)]

            # Procesar datos
            columna_id = df_filtrado.columns[3]  # Código de cliente
            columna_fecha = df_filtrado.columns[2]  # Fecha
            columna_nombre = df_filtrado.columns[4]  # Nombre
            columna_correo = df_filtrado.columns[5]  # Correo
            columna_tel1 = df_filtrado.columns[6]  # Teléfono 1
            columna_tel2 = df_filtrado.columns[7]  # Teléfono 2
            columna_placa = df_filtrado.columns[8]  # Placa

            df_temp = df_filtrado.copy()
            df_temp['Año'] = df_temp[columna_fecha].dt.year

            df_limpio = df_temp.dropna(subset=[columna_id])

            # Verificar si hay datos después del filtro
            if len(df_limpio) == 0:
                st.error("❌ No hay datos que coincidan con los filtros seleccionados. Por favor, ajusta tus criterios.")
            else:
                st.success(f"✅ Se encontraron {len(df_limpio)} registros con los filtros aplicados")

                # Clientes del año actual
                clientes_año_actual = set(df_limpio[df_limpio['Año'] == año_actual][columna_id].unique())

                # Clientes de cada año anterior
                clientes_año_1 = set(df_limpio[df_limpio['Año'] == año_1][columna_id].unique())
                clientes_año_2 = set(df_limpio[df_limpio['Año'] == año_2][columna_id].unique())
                clientes_año_3 = set(df_limpio[df_limpio['Año'] == año_3][columna_id].unique())

                # Clientes de años anteriores (todos)
                clientes_años_anteriores = clientes_año_1 | clientes_año_2 | clientes_año_3

                # Clientes de cada año anterior que han regresado al año actual
                clientes_año_1_regresaron = clientes_año_1 & clientes_año_actual
                clientes_año_2_regresaron = clientes_año_2 & clientes_año_actual
                clientes_año_3_regresaron = clientes_año_3 & clientes_año_actual

                # Clientes que NO han regresado en el año actual
                clientes_no_regresaron = clientes_años_anteriores - clientes_año_actual

                # Clientes que SÍ regresaron
                clientes_regresaron = clientes_años_anteriores & clientes_año_actual

                # Total de clientes únicos en el año actual
                total_clientes_año_actual = len(clientes_año_actual)

                # Mostrar métricas principales
                st.markdown("---")
                st.header("📊 Resultados de Fidelización")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Clientes Años Anteriores", len(clientes_años_anteriores))
                with col2:
                    st.metric("✅ Clientes que Regresaron", len(clientes_regresaron))
                with col3:
                    st.metric("❌ Clientes que NO Regresaron", len(clientes_no_regresaron))
                with col4:
                    st.metric(f"Clientes {año_actual}", total_clientes_año_actual)

                # Mostrar última fecha de actualización (del archivo completo)
                columna_fecha_completa = df.columns[2]  # Columna C [2]
                fecha_maxima = df[columna_fecha_completa].max()

                meses = {
                    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
                }
                dia = fecha_maxima.day
                mes = meses[fecha_maxima.month]
                año = fecha_maxima.year
                st.info(f"📅 Estos datos están actualizados al {dia} de {mes} de {año}")

                # GRÁFICAS
                st.markdown("---")
                st.header("📈 Análisis de Retorno por Año")

                # Gráfica 1: Cantidad de clientes de cada año anterior que regresaron
                st.subheader(f"Gráfica 1: Clientes de cada año anterior que regresaron en {año_actual}")

                fig1, ax1 = plt.subplots(figsize=(10, 6))
                categorias_años = [f'Del año {año_3}', f'Del año {año_2}', f'Del año {año_1}']
                valores_regreso = [
                    len(clientes_año_3_regresaron),
                    len(clientes_año_2_regresaron),
                    len(clientes_año_1_regresaron)
                ]
                colores_años = ['#f39c12', '#16a085', '#8e44ad']

                barras1 = ax1.bar(categorias_años, valores_regreso, color=colores_años,
                                 edgecolor='black', linewidth=1.5, width=0.6)

                for barra, valor in zip(barras1, valores_regreso):
                    altura = barra.get_height()
                    ax1.text(barra.get_x() + barra.get_width()/2., altura,
                            f'{int(valor)}', ha='center', va='bottom', fontsize=13, fontweight='bold')

                ax1.set_title(f'Clientes de cada año anterior que regresaron en {año_actual}',
                             fontsize=15, fontweight='bold', pad=20)
                ax1.set_ylabel('Número de Clientes', fontsize=12)
                ax1.set_xlabel('Año de origen', fontsize=12)
                ax1.grid(axis='y', alpha=0.3, linestyle='--')
                plt.tight_layout()
                st.pyplot(fig1)

                # Gráfica 2: Porcentaje respecto al total del año actual
                st.subheader(f"Gráfica 2: Porcentaje respecto a clientes únicos de {año_actual}")

                fig2, ax2 = plt.subplots(figsize=(10, 6))

                if total_clientes_año_actual > 0:
                    porcentajes = [
                        (len(clientes_año_3_regresaron) / total_clientes_año_actual) * 100,
                        (len(clientes_año_2_regresaron) / total_clientes_año_actual) * 100,
                        (len(clientes_año_1_regresaron) / total_clientes_año_actual) * 100
                    ]
                else:
                    porcentajes = [0, 0, 0]

                barras2 = ax2.bar(categorias_años, porcentajes, color=colores_años,
                                 edgecolor='black', linewidth=1.5, width=0.6)

                for barra, porcentaje in zip(barras2, porcentajes):
                    altura = barra.get_height()
                    ax2.text(barra.get_x() + barra.get_width()/2., altura,
                            f'{porcentaje:.1f}%', ha='center', va='bottom', fontsize=13, fontweight='bold')

                ax2.set_title(f'Porcentaje de clientes de años anteriores respecto a total de {año_actual}',
                             fontsize=15, fontweight='bold', pad=20)
                ax2.set_ylabel('Porcentaje (%)', fontsize=12)
                ax2.set_xlabel('Año de origen', fontsize=12)
                ax2.grid(axis='y', alpha=0.3, linestyle='--')
                ax2.set_ylim(0, max(porcentajes) * 1.15 if max(porcentajes) > 0 else 100)
                plt.tight_layout()
                st.pyplot(fig2)

                # Gráfica 3: Comparación de clientes que regresaron vs no regresaron
                st.markdown("---")
                st.subheader("Gráfica 3: Comparación general de fidelización")

                fig3, ax3 = plt.subplots(figsize=(10, 6))
                categorias = ['Clientes que\nRegresaron', 'Clientes que\nNO Regresaron']
                valores = [len(clientes_regresaron), len(clientes_no_regresaron)]
                colores = ['#2ecc71', '#e74c3c']

                barras3 = ax3.bar(categorias, valores, color=colores, edgecolor='black', linewidth=1.5)

                for barra, valor in zip(barras3, valores):
                    altura = barra.get_height()
                    ax3.text(barra.get_x() + barra.get_width()/2., altura,
                            f'{int(valor)}', ha='center', va='bottom', fontsize=13, fontweight='bold')

                ax3.set_title(f'Comparación de Fidelización de Clientes en {año_actual}',
                             fontsize=15, fontweight='bold', pad=20)
                ax3.set_ylabel('Número de Clientes', fontsize=12)
                ax3.grid(axis='y', alpha=0.3, linestyle='--')
                plt.tight_layout()
                st.pyplot(fig3)

                # Obtener datos de clientes que no regresaron
                if len(clientes_no_regresaron) > 0:
                    st.markdown("---")
                    st.header("📋 Listado de Clientes que NO Regresaron")

                    # Crear DataFrame con información de clientes perdidos
                    clientes_perdidos = []

                    for cliente_id in clientes_no_regresaron:
                        # Obtener datos del cliente (tomar el primer registro)
                        datos_cliente = df_limpio[df_limpio[columna_id] == cliente_id].iloc[0]

                        # Determinar en qué años compró
                        años_compra = df_limpio[df_limpio[columna_id] == cliente_id]['Año'].unique()
                        años_compra_str = ', '.join([str(año) for año in sorted(años_compra)])

                        clientes_perdidos.append({
                            'Código Cliente': cliente_id,
                            'Nombre': datos_cliente[columna_nombre],
                            'Correo': datos_cliente[columna_correo],
                            'Teléfono 1': datos_cliente[columna_tel1],
                            'Teléfono 2': datos_cliente[columna_tel2],
                            'Placa': datos_cliente[columna_placa],
                            'Años en que compró': años_compra_str
                        })

                    df_perdidos = pd.DataFrame(clientes_perdidos)

                    # Mostrar tabla
                    st.dataframe(df_perdidos, use_container_width=True)

                    # Botón de descarga
                    st.markdown("---")
                    st.subheader("💾 Descargar Listado")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_perdidos.to_excel(writer, sheet_name='Clientes No Regresaron', index=False)
                        output.seek(0)
                        st.download_button(
                            label="📥 Descargar Excel",
                            data=output,
                            file_name=f"clientes_no_regresaron_{año_actual}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    with col2:
                        # CSV
                        csv = df_perdidos.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📥 Descargar CSV",
                            data=csv,
                            file_name=f"clientes_no_regresaron_{año_actual}.csv",
                            mime="text/csv"
                        )

                    st.success(f"✅ Análisis completado: {len(clientes_no_regresaron)} clientes no han regresado en {año_actual}")
                else:
                    st.success("🎉 Excelente! Todos los clientes anteriores han regresado en el año actual.")


# ============================================
# INTERFAZ PRINCIPAL
# ============================================

# Contenedor con título y logo (responsive con CSS)
st.markdown("""
<style>
.header-box {
    background-color: #272F59;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
}
.header-box h1 {
    color: white;
    margin: 0;
    font-size: 22px;
}
.header-box img {
    height: 50px; /* tamaño en pantallas grandes */
    margin-top: 10px;
}

/* 📱 Ajuste para móviles */
@media (max-width: 600px) {
    .header-box img {
        height: auto;
        width: 70%; /* logo se ajusta al ancho de pantalla */
        max-width: 200px; /* límite para que no se agrande demasiado */
    }
}
</style>

<div class="header-box">
    <img src="https://www.tellantas.com/wp-content/uploads/2022/11/cropped-cropped-logo392negativo-png.avif" alt="Logo">
    <h1>📊 Análisis de Recompra de Clientes</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Sidebar con menú y instrucciones
with st.sidebar:
    # Marca de registro del programa
    logo_url = "https://elchorro.com.co/wp-content/uploads/2025/04/ch-plano.png?w=106&h=106"
    col_logo, col_texto = st.columns([1, 3], vertical_alignment="center")
    with col_logo:
        st.image(logo_url, width=60)
    with col_texto:
        st.markdown("""
            <div style="font-size:10px; line-height:1.1;">
                <span style="font-style:italic;">Este programa fue desarrollado por:</span><br>
                <span style="font-weight:bold;">Daniel Cortázar Triana</span><br>
                <span style="font-weight:bold;">El Chorro Producciones SAS</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # MENÚ DE SELECCIÓN DE FUNCIONES
    st.header("📋 Menú Principal")

    opcion = st.radio(
        "Selecciona una función:",
        ["📈 Análisis de Recompra", "🔄 Fidelización de Clientes"],
        key='menu_principal'
    )

    st.markdown("---")

    # INSTRUCCIONES SEGÚN LA OPCIÓN
    st.header("ℹ️ Instrucciones")

    if opcion == "📈 Análisis de Recompra":
        st.markdown("""
        1. **Selecciona los filtros** que deseas aplicar.
        2. **Haz clic en Analizar.** El aplicativo te mostrará los estadísticos de total de clientes y recompra de los **3 años anteriores**.
        3. **Descarga** las gráficas y el Excel con la información para armar otros informes.
        """)
    else:  # Fidelización de Clientes
        st.markdown("""
        1. **Selecciona los filtros** que deseas aplicar (igual que en Análisis de Recompra).
        2. **Haz clic en Analizar Fidelización** para identificar clientes que no han regresado en el año actual.
        3. Verás **gráficas detalladas** de:
           - Clientes de cada año anterior que regresaron
           - Porcentajes respecto al total del año actual
           - Comparación general de fidelización
        4. Podrás **descargar un listado completo** con datos de contacto de clientes que no han regresado.
        """)

    st.markdown("---")
    st.markdown("💡 **Tip:** Puedes cambiar de función en cualquier momento usando el menú superior")

    # Botón para recargar datos
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()

# Cargar datos
with st.spinner('Cargando datos...'):
    df, error = cargar_datos_desde_drive(GOOGLE_DRIVE_FILE_ID)

if error:
    st.error(f"❌ Error al cargar los datos: {error}")
    st.info("""
    **Posibles soluciones:**
    1. Verifica que el archivo esté compartido como "Cualquiera con el enlace puede ver"
    2. Verifica que sea un archivo CSV válido
    3. Intenta recargar la página
    """)
    st.stop()

if df is None:
    st.error("❌ No se pudieron cargar los datos.")
    st.stop()

st.success(f"✅ Datos cargados correctamente: {len(df)} registros")

# Mostrar información de temporalidad
temp = temporalidad(df)
st.info(f"📅 **Período de datos:** Año actual: **{temp['año_actual']}** | Años anteriores: **{temp['años_anteriores'][0]}, {temp['años_anteriores'][1]}, {temp['años_anteriores'][2]}**")

st.markdown("---")

# EJECUTAR LA FUNCIÓN SELECCIONADA
if opcion == "📈 Análisis de Recompra":
    analisis_recompra(df)
else:  # Fidelización de Clientes
    fidelizacion_clientes(df)
