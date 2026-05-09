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
    except:
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance", "💾 Guardar"])

with tab1:
    st.subheader("Gestión de Inventario")
    with st.expander("➕ Añadir / Editar"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Producto:", opciones)
        
        d_n = sel if sel != "Nuevo" else ""
        # Protección para campos vacíos
        d_c = ""
        d_s, d_co, d_v = 0, 0.0, 0.0
        if sel != "Nuevo" and not df_inv.empty:
            fila = df_inv[df_inv['Producto']==sel].iloc[0]
            d_c, d_s, d_co, d_v = fila['Categoria'], int(fila['Stock']), float(fila['Costo']), float(fila['Venta'])

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
        # AQUÍ ESTÁ EL ERROR CORREGIDO: st.columns(2) en lugar de st.columns()
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            with st.form("f_v"):
                p_v = st.selectbox("Seleccionar:", df_inv['Producto'].unique())
                c_v = st.number_input("Cantidad", min_value=1)
                if st.form_submit_button("Vender"):
                    idx = df_inv[df_inv['Producto'] == p_v].index
                    if df_inv.at[idx[0], 'Stock'] >= c_v:
                        gan = c_v * (df_inv.at[idx[0], 'Venta'] - df_inv.at[idx[0], 'Costo'])
                        nueva = pd.DataFrame([{"Fecha": datetime.now(), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": df_inv.at[idx[0], 'Costo'], "Venta_Ref": df_inv.at[idx[0], 'Venta'], "Ganancia": gan}])
                        df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                        df_inv.at[idx[0], 'Stock'] -= c_v
                        st.success("Venta Exitosa")
                    else: st.error("Stock insuficiente")
        with col_v2:
            if not df_ven.empty:
                st.write("### Historial")
                st.dataframe(df_ven.sort_values(by="Fecha", ascending=False), use_container_width=True)

with tab3:
    st.subheader("Gastos")
    with st.form("f_g"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto", min_value=0.0)
        f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Registrar"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": f_g, "Concepto": con, "Monto": mon}])], ignore_index=True)
    st.dataframe(df_ops, use_container_width=True)

with tab4:
    st.header("Balance Tulip S.A.")
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    anos = [2024, 2025, 2026, 2027, 2028, 2029, 2030]
    
    c1, c2 = st.columns(2)
    m_sel = c1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1)
    a_sel = c2.selectbox("Año:", anos, index=anos.index(datetime.now().year))
    
    m_num = [k for k, v in meses.items() if v == m_sel][0]
    
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    v_f = df_ven[(df_ven['Fecha'].dt.month == m_num) & (df_ven['Fecha'].dt.year == a_sel)]
    bruta = v_f['Ganancia'].sum()
    
    if not df_ops.empty:
        df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'])
        g_f = df_ops[(df_ops['Fecha'].dt.month == m_num) & (df_ops['Fecha'].dt.year == a_sel)]
        gastos = g_f['Monto'].sum()
    else: gastos = 0
    
    inv = (df_inv['Stock'] * df_inv['Costo']).sum()
    
    st.metric("Utilidad Bruta", f"${bruta:,.2f}")
    st.metric("Gastos", f"${gastos:,.2f}")
    st.metric("Utilidad Neta", f"${bruta - gastos:,.2f}")
    st.metric("Capital en Stock", f"${inv:,.2f}")

    if inv > 0:
        flujos = [-inv] + [bruta - gastos] * 12
        try:
            st.write(f"**TIR:** {npf.irr(flujos)*100:.2f}%")
            st.write(f"**VAN:** ${npf.npv(0.1, flujos):,.2f}")
        except: st.write("Indicadores en cálculo...")

with tab5:
    st.download_button("📥 Descargar Excel", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name="Tulip_SA.xlsx", use_container_width=True)
