import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import io

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Recompra de Clientes",
    page_icon="📊",
    layout="wide"
)

# ============================================
# CONFIGURACIÓN: ID del archivo de Google Drive
# ============================================
GOOGLE_DRIVE_FILE_ID = "1qu0rICC-zdXROZyH9TGktcmF5EfGvece"
# ============================================

# Función para cargar datos desde Google Drive
@st.cache_data(ttl=3600)  # Cache por 1 hora
def cargar_datos_desde_drive(file_id):
    """Carga el CSV desde Google Drive"""
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        df = pd.read_csv(url)
        return df, None
    except Exception as e:
        return None, str(e)

# Título principal
st.title("📊 Análisis de Recompra de Clientes")
st.markdown("---")

# Sidebar para instrucciones
with st.sidebar:
    st.header("ℹ️ Instrucciones")
    st.markdown("""
    1. **Selecciona los filtros** que deseas aplicar.
    2. **Haz clic en Analizar.** El aplicativo te mostrará los estadísticos de total de clientes y recompra por períodos.
    3. Si lo deseas **Descarga** las gráficas y el Excel con la información para armar otros informes.
    4. En la parte inferior de estas instrucciones puedes **actualizar** la búsqueda.
    """)
    st.markdown("---")
    st.markdown("💡 **Tip:** Puedes seleccionar múltiples opciones en cada filtro")
    
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

# SECCIÓN DE FILTROS
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
if st.button("🚀 ANALIZAR DATOS", type="primary", use_container_width=True):
    
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
        
        # Verificar si hay datos después del filtro
        if len(df_filtrado) == 0:
            st.error("❌ No hay datos que coincidan con los filtros seleccionados. Por favor, ajusta tus criterios.")
        else:
            st.success(f"✅ Se encontraron {len(df_filtrado)} registros con los filtros aplicados")
            
            # Procesar datos
            columna_id = df_filtrado.columns[3]
            columna_fecha = df_filtrado.columns[2]
            columna_nombre = df_filtrado.columns[4]
            
            df_filtrado[columna_fecha] = pd.to_datetime(df_filtrado[columna_fecha], errors='coerce')
            df_filtrado['Año'] = df_filtrado[columna_fecha].dt.year
            
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
            años_numeros = []
            
            if 'Visitas_2022' in tabla_final.columns:
                clientes_por_año['2022'] = len(tabla_final[tabla_final['Visitas_2022'] > 0])
                años_numeros.append('2022')
            
            if 'Visitas_2023' in tabla_final.columns:
                clientes_por_año['2023'] = len(tabla_final[tabla_final['Visitas_2023'] > 0])
                años_numeros.append('2023')
            
            if 'Visitas_2024' in tabla_final.columns:
                clientes_por_año['2024'] = len(tabla_final[tabla_final['Visitas_2024'] > 0])
                años_numeros.append('2024')
            
            clientes_2022_2023 = 0
            clientes_2023_2024 = 0
            clientes_2022_2024 = 0
            clientes_tres_años = 0
            
            if 'Visitas_2022' in tabla_final.columns and 'Visitas_2023' in tabla_final.columns:
                clientes_2022_2023 = len(tabla_final[(tabla_final['Visitas_2022'] > 0) & (tabla_final['Visitas_2023'] > 0)])
            
            if 'Visitas_2023' in tabla_final.columns and 'Visitas_2024' in tabla_final.columns:
                clientes_2023_2024 = len(tabla_final[(tabla_final['Visitas_2023'] > 0) & (tabla_final['Visitas_2024'] > 0)])
            
            if 'Visitas_2022' in tabla_final.columns and 'Visitas_2024' in tabla_final.columns:
                clientes_2022_2024 = len(tabla_final[(tabla_final['Visitas_2022'] > 0) & (tabla_final['Visitas_2024'] > 0)])
            
            if all(col in tabla_final.columns for col in ['Visitas_2022', 'Visitas_2023', 'Visitas_2024']):
                clientes_tres_años = len(tabla_final[(tabla_final['Visitas_2022'] > 0) & 
                                                      (tabla_final['Visitas_2023'] > 0) & 
                                                      (tabla_final['Visitas_2024'] > 0)])
            
            total_clientes_2024 = clientes_por_año.get('2024', 0)
            
            categorias = ['2022 a 2023', '2023 a 2024', '2022 a 2024', 'Los 3 años']
            valores = [clientes_2022_2023, clientes_2023_2024, clientes_2022_2024, clientes_tres_años]
            
            if total_clientes_2024 > 0:
                porcentajes = [(v / total_clientes_2024) * 100 for v in valores]
            else:
                porcentajes = [0, 0, 0, 0]
            
            # Mostrar métricas principales
            st.markdown("---")
            st.header("📈 Métricas Principales")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Clientes Únicos", len(tabla_final))
            with col2:
                if '2022' in clientes_por_año:
                    st.metric("Clientes 2022", clientes_por_año['2022'])
            with col3:
                if '2023' in clientes_por_año:
                    st.metric("Clientes 2023", clientes_por_año['2023'])
            with col4:
                if '2024' in clientes_por_año:
                    st.metric("Clientes 2024", clientes_por_año['2024'])
            
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
            st.subheader("Gráfica 3: Porcentaje de recompra en relación a clientes 2024")
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            
            barras = ax3.bar(categorias, porcentajes, color=colores, edgecolor='black', linewidth=1.5)
            
            for barra, porcentaje in zip(barras, porcentajes):
                altura = barra.get_height()
                ax3.text(barra.get_x() + barra.get_width()/2., altura,
                        f'{porcentaje:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')
            
            ax3.set_title('Gráfica 3: Porcentaje de recompra en relación a cantidad de clientes 2024', 
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
                        'Porcentaje respecto a 2024': [f"{p:.2f}%" for p in porcentajes]
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
