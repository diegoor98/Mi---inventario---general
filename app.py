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
        st.success("✅ Datos Tulip S.A. sincronizados.")
    except:
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📦 Stock", "🛒 Ventas", "💸 Gastos", "📑 Balance", "📈 Dashboard", "💾 Guardar"])

with tab1:
    st.subheader("Gestión de Inventario")
    with st.expander("Añadir / Editar"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Producto:", opciones)
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
    st.subheader("Historial de Ventas Diarias")
    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        with st.form("venta_nueva"):
            p_v = st.selectbox("Producto", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            f_v = st.date_input("Fecha", datetime.now())
            if st.form_submit_button("Registrar"):
                idx = df_inv[df_inv['Producto'] == p_v].index
                if df_inv.at[idx[0], 'Stock'] >= c_v:
                    gan = c_v * (df_inv.at[idx[0], 'Venta'] - df_inv.at[idx[0], 'Costo'])
                    nueva = pd.DataFrame([{"Fecha": pd.to_datetime(f_v), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": df_inv.at[idx[0], 'Costo'], "Venta_Ref": df_inv.at[idx[0], 'Venta'], "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                    df_inv.at[idx[0], 'Stock'] -= c_v
                    st.success("Venta OK")
                else: st.error("Sin stock")
    
    with col_v2:
        meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        m_sel = st.selectbox("Filtrar Historial por Mes:", list(meses.values()), index=datetime.now().month-1)
        m_num = [k for k, v in meses.items() if v == m_sel][0]
        
        df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
        v_mes = df_ven[df_ven['Fecha'].dt.month == m_num]
        
        st.write(f"### Detalle {m_sel}")
        st.dataframe(v_mes, use_container_width=True)
        st.write(f"**Suma Total Ganancia {m_sel}:** ${v_mes['Ganancia'].sum():,.2f}")

with tab3:
    st.subheader("Gastos")
    with st.form("f_g"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto", min_value=0.0); f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Registrar Gasto"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": pd.to_datetime(f_g), "Concepto": con, "Monto": mon}])], ignore_index=True)
    st.dataframe(df_ops, use_container_width=True)

with tab4:
    st.header("📊 Balance Numérico Tulip S.A.")
    # Selector único de tiempo para Balance
    col_b1, col_b2 = st.columns(2)
    m_b = col_b1.selectbox("Mes Balance:", list(meses.values()), index=datetime.now().month-1, key="b_m")
    a_b = col_b2.selectbox("Año Balance:", [2024, 2025, 2026, 2027], index=2, key="b_a")
    
    m_n = [k for k, v in meses.items() if v == m_b][0]
    v_b = df_ven[(df_ven['Fecha'].dt.month == m_n) & (df_ven['Fecha'].dt.year == a_b)]
    g_b = df_ops[(df_ops['Fecha'].dt.month == m_n) & (df_ops['Fecha'].dt.year == a_b)]
    
    bruta = v_b['Ganancia'].sum()
    gastos = g_b['Monto'].sum()
    neta = bruta - gastos
    inv_val = (df_inv['Stock'] * df_inv['Costo']).sum()

    st.write("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Utilidad Bruta", f"${bruta:,.2f}")
    c2.metric("Gastos Operativos", f"- ${gastos:,.2f}")
    c3.metric("Utilidad Neta", f"${neta:,.2f}")

    st.write("### Indicadores de Inversión")
    f1, f2, f3 = st.columns(3)
    f1.write(f"**Capital en Stock:** ${inv_val:,.2f}")
    renta = (neta / inv_val * 100) if inv_val > 0 else 0
    f2.write(f"**Rentabilidad Mensual:** {renta:.2f}%")
    
    if inv_val > 0:
        flujos = [-inv_val] + [neta] * 12
        tir = npf.irr(flujos)
        van = npf.npv(0.1, flujos)
        f3.write(f"**TIR:** {tir*100:.2f}%" if not pd.isna(tir) else "TIR: N/D")
        st.write(f"**VAN (Valor Actual Neto):** ${van:,.2f}")

with tab5:
    st.header("📈 Dashboard Visual Tulip S.A.")
    # Selector de tiempo exclusivo para gráficas
    c_d1, c_d2 = st.columns(2)
    m_d = c_d1.selectbox("Mes Dashboard:", list(meses.values()), index=datetime.now().month-1, key="d_m")
    a_d = c_d2.selectbox("Año Dashboard:", [2024, 2025, 2026, 2027], index=2, key="d_a")
    
    m_dn = [k for k, v in meses.items() if v == m_d][0]
    v_d = df_ven[(df_ven['Fecha'].dt.month == m_dn) & (df_ven['Fecha'].dt.year == a_d)]
    g_d = df_ops[(df_ops['Fecha'].dt.month == m_dn) & (df_ops['Fecha'].dt.year == a_d)]

    if not v_d.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.write("### 🏆 Ganancia por Producto")
            fig1 = px.bar(v_d.groupby('Producto')['Ganancia'].sum().reset_index(), x='Producto', y='Ganancia', color='Producto', template="plotly_dark")
            st.plotly_chart(fig1, use_container_width=True)
        
        with g2:
            st.write("### 🍩 Estructura de Gastos")
            if not g_d.empty:
                fig2 = px.pie(g_d.groupby('Concepto')['Monto'].sum().reset_index(), values='Monto', names='Concepto', hole=0.5, template="plotly_dark")
                st.plotly_chart(fig2, use_container_width=True)
            else: st.info("No hay gastos para graficar.")

        g3, g4 = st.columns(2)
        with g3:
            st.write("### 📅 Evolución Diaria")
            fig3 = px.line(v_d.groupby('Fecha')['Ganancia'].sum().reset_index(), x='Fecha', y='Ganancia', markers=True, template="plotly_dark")
            st.plotly_chart(fig3, use_container_width=True)
        
        with g4:
            st.write("### 🗺️ Mapa de Ventas (Treemap)")
            fig4 = px.treemap(v_d, path=['Producto'], values='Ganancia', template="plotly_dark")
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("Sin datos para generar el Dashboard visual.")

with tab6:
    st.download_button("📥 Guardar Base Tulip S.A.", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name="Tulip_SA.xlsx", use_container_width=True)
