import streamlit as st
import pandas as pd
import numpy_financial as npf
from io import BytesIO
from datetime import datetime

# Configuración Tulip S.A. 🌷
st.set_page_config(page_title="Tulip S.A. ERP", page_icon="🌷", layout="wide")

def convertir_a_excel(df_inv, df_ven, df_ops):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_inv.to_excel(writer, index=False, sheet_name='Inventario')
        df_ven.to_excel(writer, index=False, sheet_name='Ventas')
        df_ops.to_excel(writer, index=False, sheet_name='Gastos')
    return output.getvalue()

st.markdown("<h1 style='text-align: center;'>🌷 Tulip S.A.</h1>", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos Tulip S.A.", type=["xlsx"])

if archivo_subido:
    try:
        df_inv = pd.read_excel(archivo_subido, sheet_name=0)
        df_ven = pd.read_excel(archivo_subido, sheet_name=1)
        df_ops = pd.read_excel(archivo_subido, sheet_name=2)
        df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'], errors='coerce')
        df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'], errors='coerce')
        st.success("✅ Conexión con base de datos exitosa.")
    except:
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

# --- MENU PRINCIPAL ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance", "📈 Dashboard Pro", "💾 Guardar"])

# PESTAÑAS DE DATOS (Mantenemos la lógica anterior)
with tab1:
    st.subheader("Gestión de Inventario")
    with st.expander("Añadir / Editar"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Buscar:", opciones)
        d_n = sel if sel != "Nuevo" else ""
        d_c = df_inv[df_inv['Producto']==sel]['Categoria'].iloc[0] if sel != "Nuevo" else ""
        d_s = int(df_inv[df_inv['Producto']==sel]['Stock'].iloc[0]) if sel != "Nuevo" else 0
        d_co = float(df_inv[df_inv['Producto']==sel]['Costo'].iloc[0]) if sel != "Nuevo" else 0.0
        d_v = float(df_inv[df_inv['Producto']==sel]['Venta'].iloc[0]) if sel != "Nuevo" else 0.0

        with st.form("f_inv"):
            n = st.text_input("Nombre", value=d_n).capitalize()
            c = st.text_input("Categoría", value=d_c).capitalize()
            can = st.number_input("Stock", value=d_s, min_value=0)
            cos = st.number_input("Costo", value=d_co)
            ven = st.number_input("Venta", value=d_v)
            if st.form_submit_button("Guardar"):
                if n in df_inv['Producto'].values:
                    df_inv.loc[df_inv['Producto'] == n, ['Categoria', 'Stock', 'Costo', 'Venta']] = [c, can, cos, ven]
                else:
                    df_inv = pd.concat([df_inv, pd.DataFrame([{"Producto": n, "Categoria": c, "Stock": can, "Costo": cos, "Venta": ven}])], ignore_index=True)
                st.rerun()
    st.dataframe(df_inv, use_container_width=True)

with tab2:
    st.subheader("Registrar Ventas")
    if not df_inv.empty:
        with st.form("f_v"):
            p_v = st.selectbox("Producto", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            f_v = st.date_input("Fecha", datetime.now())
            if st.form_submit_button("Vender"):
                idx = df_inv[df_inv['Producto'] == p_v].index[0]
                if df_inv.at[idx, 'Stock'] >= c_v:
                    gan = c_v * (df_inv.at[idx, 'Venta'] - df_inv.at[idx, 'Costo'])
                    nueva = pd.DataFrame([{"Fecha": f_v, "Producto": p_v, "Cantidad": c_v, "Costo_Ref": df_inv.at[idx, 'Costo'], "Venta_Ref": df_inv.at[idx, 'Venta'], "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                    df_inv.at[idx, 'Stock'] -= c_v
                    st.success("¡Venta OK!")
                else: st.error("Stock insuficiente")
    st.dataframe(df_ven.sort_values(by="Fecha", ascending=False), use_container_width=True)

with tab3:
    st.subheader("Gastos")
    with st.form("f_g"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto", min_value=0.0); f_g = st.date_input("Fecha Gasto", datetime.now())
        if st.form_submit_button("Registrar"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": f_g, "Concepto": con, "Monto": mon}])], ignore_index=True)
    st.dataframe(df_ops, use_container_width=True)

# --- NUEVO DASHBOARD PRO ---
with tab5:
    st.header("📈 Dashboard de Rendimiento Tulip S.A.")
    
    # Selector de Tiempo para el Dashboard
    filtro_dash = st.radio("Analizar por:", ["Mes Específico", "Año Completo"], horizontal=True, key="dash_filtro")
    
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    anos_list = list(range(2024, datetime.now().year + 2))
    
    c1, c2 = st.columns(2)
    a_dash = c1.selectbox("Seleccionar Año:", anos_list, index=anos_list.index(datetime.now().year), key="dash_ano")
    
    if filtro_dash == "Mes Específico":
        m_dash_nom = c2.selectbox("Seleccionar Mes:", list(meses.values()), index=datetime.now().month-1, key="dash_mes")
        m_dash_num = [k for k, v in meses.items() if v == m_dash_nom][0]
        v_dash = df_ven[(df_ven['Fecha'].dt.month == m_dash_num) & (df_ven['Fecha'].dt.year == a_dash)]
        g_dash = df_ops[(df_ops['Fecha'].dt.month == m_dash_num) & (df_ops['Fecha'].dt.year == a_dash)]
        st.info(f"Mostrando datos de {m_dash_nom} {a_dash}")
    else:
        v_dash = df_ven[df_ven['Fecha'].dt.year == a_dash]
        g_dash = df_ops[df_ops['Fecha'].dt.year == a_dash]
        st.info(f"Mostrando consolidado de todo el año {a_dash}")

    # Gráficas
    if not v_dash.empty:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.write("### 🏆 Top Productos (Ganancia)")
            top_prod = v_dash.groupby('Producto')['Ganancia'].sum().sort_values(ascending=False)
            st.bar_chart(top_prod)
            
        with col_g2:
            st.write("### 💸 Distribución de Gastos")
            if not g_dash.empty:
                gastos_pie = g_dash.groupby('Concepto')['Monto'].sum()
                st.write("Resumen de egresos por concepto:")
                st.table(gastos_pie)
            else:
                st.write("No hay gastos registrados en este periodo.")
    else:
        st.warning("No hay ventas registradas en el periodo seleccionado para generar gráficas.")

# --- PESTAÑA BALANCE (REDUX) ---
with tab4:
    st.header("📊 Balance Contable")
    # Lógica de balance similar al Dashboard pero con métricas numéricas
    st.write("Consulta el Dashboard Pro para gráficas detalladas.")
    # (Aquí puedes mantener tus métricas de VAN/TIR anteriores)

with tab6:
    st.subheader("💾 Guardar Datos")
    st.download_button("📥 Descargar Excel Tulip S.A.", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name="Tulip_SA_Data.xlsx", use_container_width=True)
