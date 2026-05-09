import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px
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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance", "📈 Dashboard Pro", "💾 Guardar"])

# [Las pestañas de Stock, Ventas y Gastos se mantienen con la lógica de guardado anterior]
with tab1:
    st.subheader("Gestión de Inventario")
    with st.expander("Añadir / Editar"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Buscar:", opciones)
        d_n = sel if sel != "Nuevo" else ""
        d_c = df_inv[df_inv['Producto']==sel]['Categoria'].iloc[0] if (sel != "Nuevo" and not df_inv.empty) else ""
        d_s = int(df_inv[df_inv['Producto']==sel]['Stock'].iloc[0]) if (sel != "Nuevo" and not df_inv.empty) else 0
        d_co = float(df_inv[df_inv['Producto']==sel]['Costo'].iloc[0]) if (sel != "Nuevo" and not df_inv.empty) else 0.0
        d_v = float(df_inv[df_inv['Producto']==sel]['Venta'].iloc[0]) if (sel != "Nuevo" and not df_inv.empty) else 0.0

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
    st.subheader("Ventas")
    if not df_inv.empty:
        with st.form("f_v"):
            p_v = st.selectbox("Seleccionar:", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            f_v = st.date_input("Fecha", datetime.now())
            if st.form_submit_button("Vender"):
                idx = df_inv[df_inv['Producto'] == p_v].index
                if df_inv.at[idx[0], 'Stock'] >= c_v:
                    gan = c_v * (df_inv.at[idx[0], 'Venta'] - df_inv.at[idx[0], 'Costo'])
                    nueva = pd.DataFrame([{"Fecha": pd.to_datetime(f_v), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": df_inv.at[idx[0], 'Costo'], "Venta_Ref": df_inv.at[idx[0], 'Venta'], "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                    df_inv.at[idx[0], 'Stock'] -= c_v
                    st.success("Venta Exitosa")
                else: st.error("Stock insuficiente")

with tab3:
    st.subheader("Gastos")
    with st.form("f_g"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto", min_value=0.0); f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Registrar"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": pd.to_datetime(f_g), "Concepto": con, "Monto": mon}])], ignore_index=True)
    st.dataframe(df_ops, use_container_width=True)

# --- DASHBOARD PRO CON GRÁFICOS INTERACTIVOS ---
with tab5:
    st.header("📈 Dashboard de Rendimiento")
    
    tipo = st.radio("Filtro Maestro:", ["Mes Específico", "Año Completo"], horizontal=True)
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    col_a, col_b = st.columns(2)
    a_sel = col_a.selectbox("Año:", list(range(2024, 2031)), index=list(range(2024, 2031)).index(datetime.now().year))
    
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'])

    if tipo == "Mes Específico":
        m_nom = col_b.selectbox("Mes:", list(meses_dict.values()), index=datetime.now().month-1)
        m_num = [k for k, v in meses_dict.items() if v == m_nom][0]
        v_f = df_ven[(df_ven['Fecha'].dt.month == m_num) & (df_ven['Fecha'].dt.year == a_sel)]
        g_f = df_ops[(df_ops['Fecha'].dt.month == m_num) & (df_ops['Fecha'].dt.year == a_sel)]
    else:
        v_f = df_ven[df_ven['Fecha'].dt.year == a_sel]
        g_f = df_ops[df_ops['Fecha'].dt.year == a_sel]

    if not v_f.empty:
        # Fila 1: Métricas rápidas
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingreso Total", f"${v_f['Ganancia'].sum():,.2f}")
        c2.metric("Gasto Total", f"${g_f['Monto'].sum():,.2f}")
        c3.metric("Margen Neto", f"${v_f['Ganancia'].sum() - g_f['Monto'].sum():,.2f}")

        # Fila 2: Gráficos Pro
        g1, g2 = st.columns(2)
        with g1:
            st.write("### 🥇 Ventas por Producto")
            fig_bar = px.bar(v_f.groupby('Producto')['Ganancia'].sum().reset_index(), x='Producto', y='Ganancia', color='Producto', template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with g2:
            st.write("### 🍩 Distribución de Gastos")
            if not g_f.empty:
                fig_pie = px.pie(g_f.groupby('Concepto')['Monto'].sum().reset_index(), values='Monto', names='Concepto', hole=0.4, template="plotly_dark")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sin gastos registrados.")
    else:
        st.warning("No hay datos en el periodo seleccionado.")

with tab4:
    st.header("📊 Balance")
    st.info("Usa el Dashboard Pro para el análisis detallado.")

with tab6:
    st.download_button("📥 Guardar en Excel", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name="Tulip_SA.xlsx", use_container_width=True)
