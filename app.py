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
    except:
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📦 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance", "📈 Dashboard", "💾 Guardar"])

# --- PESTAÑA 1: STOCK (SUMA CORREGIDA) ---
with tab1:
    st.subheader("Gestión de Inventario 🌷")
    lista_nombres = sorted(list(df_inv['Producto'].unique())) if not df_inv.empty else []
    opciones = ["--- Nuevo Producto ---"] + lista_nombres
    sel = st.selectbox("Selecciona producto para editar o añadir stock:", opciones)
    
    d_n, d_c, d_s, d_co, d_v = "", "", 0, 0.0, 0.0
    if sel != "--- Nuevo Producto ---":
        f_data = df_inv[df_inv['Producto'] == sel].iloc[0]
        d_n, d_c, d_s, d_co, d_v = sel, f_data['Categoria'], int(f_data['Stock']), float(f_data['Costo']), float(f_data['Venta'])

    with st.form("form_stock_final", clear_on_submit=False):
        col1, col2 = st.columns(2)
        n_f = col1.text_input("Nombre del Producto", value=d_n).capitalize()
        c_f = col2.text_input("Categoría", value=d_c).capitalize()
        
        col3, col4, col5 = st.columns(3)
        st.write(f"Stock actual en sistema: **{d_s}**")
        s_sumar = col3.number_input("SUMAR cantidad nueva", min_value=0, step=1, value=0)
        cos_f = col4.number_input("Costo Unitario", value=d_co, format="%.2f")
        ven_f = col5.number_input("Precio Venta", value=d_v, format="%.2f")
        
        if st.form_submit_button("✅ GUARDAR CAMBIOS"):
            if n_f:
                # AQUÍ SE HACE LA SUMA REAL
                total_calculado = d_s + s_sumar
                if n_f in df_inv['Producto'].values:
                    df_inv.loc[df_inv['Producto'] == n_f, ['Categoria', 'Stock', 'Costo', 'Venta']] = [c_f, total_calculado, cos_f, ven_f]
                else:
                    nueva_f = pd.DataFrame([{"Producto": n_f, "Categoria": c_f, "Stock": s_sumar, "Costo": cos_f, "Venta": ven_f}])
                    df_inv = pd.concat([df_inv, nueva_f], ignore_index=True)
                
                st.success(f"📦 ¡{n_f} actualizado! Nuevo total: {total_calculado}")
                st.rerun()
            else:
                st.error("Falta el nombre.")

    st.write("### Listado General")
    st.dataframe(df_inv, use_container_width=True)

# --- PESTAÑA 2: VENTAS ---
with tab2:
    st.subheader("Ventas")
    if not df_inv.empty:
        with st.form("f_v"):
            p_v = st.selectbox("Producto", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            f_v = st.date_input("Fecha", datetime.now())
            if st.form_submit_button("Vender"):
                idx = df_inv[df_inv['Producto'] == p_v].index
                if df_inv.at[idx[0], 'Stock'] >= c_v:
                    gan = c_v * (df_inv.at[idx[0], 'Venta'] - df_inv.at[idx[0], 'Costo'])
                    nueva_v = pd.DataFrame([{"Fecha": pd.to_datetime(f_v), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": df_inv.at[idx[0], 'Costo'], "Venta_Ref": df_inv.at[idx[0], 'Venta'], "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva_v], ignore_index=True)
                    df_inv.at[idx[0], 'Stock'] -= c_v
                    st.success("Venta OK")
                    st.rerun()
                else: st.error("Stock insuficiente")
    if not df_ven.empty:
        st.dataframe(df_ven.sort_values(by="Fecha", ascending=False), use_container_width=True)

# --- PESTAÑA 3: GASTOS ---
with tab3:
    st.subheader("Gastos")
    with st.form("f_g"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto"); f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Registrar"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": pd.to_datetime(f_g), "Concepto": con, "Monto": mon}])], ignore_index=True)
            st.rerun()
    st.dataframe(df_ops.sort_values(by="Fecha", ascending=False) if not df_ops.empty else df_ops)

# --- PESTAÑA 4: BALANCE ---
with tab4:
    st.header("📊 Balance Contable")
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    anos_l = list(range(2024, datetime.now().year + 5))
    
    c1, c2 = st.columns(2)
    m_s = c1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1, key="mb")
    a_s = c2.selectbox("Año:", anos_l, index=anos_l.index(datetime.now().year), key="ab")
    
    m_n = [k for k, v in meses.items() if v == m_s][0]
    
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    v_f = df_ven[(df_ven['Fecha'].dt.month == m_n) & (df_ven['Fecha'].dt.year == a_s)]
    g_f = df_ops[(pd.to_datetime(df_ops['Fecha']).dt.month == m_n) & (pd.to_datetime(df_ops['Fecha']).dt.year == a_s)] if not df_ops.empty else pd.DataFrame()
    
    bruta = v_f['Ganancia'].sum(); gastos = g_f['Monto'].sum(); neta = bruta - gastos
    inv_v = (df_inv['Stock'] * df_inv['Costo']).sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Ingresos", f"${bruta:,.2f}")
    m2.metric("Gastos", f"- ${gastos:,.2f}")
    m3.metric("Utilidad Neta", f"${neta:,.2f}")
    st.write(f"**Capital en Stock:** ${inv_v:,.2f}")

# --- PESTAÑA 5: DASHBOARD ---
with tab5:
    st.header("📈 Dashboard Visual")
    if not v_f.empty:
        g1, g2 = st.columns(2)
        fig1 = px.bar(v_f.groupby('Producto')['Ganancia'].sum().reset_index(), x='Producto', y='Ganancia', color='Producto', template="plotly_dark", title="Ganancia por Producto")
        g1.plotly_chart(fig1, use_container_width=True)
        if not g_f.empty:
            fig2 = px.pie(g_f, values='Monto', names='Concepto', hole=0.5, template="plotly_dark", title="Distribución de Gastos")
            g2.plotly_chart(fig2, use_container_width=True)
        fig3 = px.treemap(v_f, path=['Producto'], values='Ganancia', template="plotly_dark", title="Mapa de Ventas")
        st.plotly_chart(fig3, use_container_width=True)
    else: st.info("Sin datos en el periodo.")

# --- PESTAÑA 6: GUARDAR ---
with tab5:
    st.divider()
    st.download_button("📥 Descargar Excel Final", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name=f"Tulip_SA_{datetime.now().strftime('%d_%m')}.xlsx", use_container_width=True)
