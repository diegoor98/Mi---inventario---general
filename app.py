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
        st.success("✅ Base de datos cargada.")
    except:
        st.error("⚠️ Error en formato. Se inició base limpia.")
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📦 Stock", "🛒 Ventas", "💸 Gastos", "📑 Balance", "📈 Dashboard", "💾 Guardar"])

# --- STOCK ---
with tab1:
    st.subheader("Gestión de Inventario")
    with st.expander("Añadir / Editar"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Producto:", opciones)
        d_n = sel if sel != "Nuevo" else ""
        d_c, d_s, d_co, d_v = "", 0, 0.0, 0.0
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

# --- VENTAS ---
with tab2:
    st.subheader("Ventas")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        with st.form("nv"):
            p_v = st.selectbox("Producto", df_inv['Producto'].unique() if not df_inv.empty else ["Vacío"])
            c_v = st.number_input("Cant:", min_value=1)
            f_v = st.date_input("Fecha Venta", datetime.now())
            if st.form_submit_button("Vender") and not df_inv.empty:
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
        m_sel = st.selectbox("Historial Mensual:", list(meses.values()), index=datetime.now().month-1)
        if not df_ven.empty:
            df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
            m_num = [k for k, v in meses.items() if v == m_sel][0]
            v_mes = df_ven[df_ven['Fecha'].dt.month == m_num]
            st.dataframe(v_mes, use_container_width=True)
            st.write(f"**Total Ganancia {m_sel}:** ${v_mes['Ganancia'].sum():,.2f}")

# --- GASTOS ---
with tab3:
    st.subheader("Gastos")
    with st.form("fg"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto"); f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Añadir"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": pd.to_datetime(f_g), "Concepto": con, "Monto": mon}])], ignore_index=True)
    st.dataframe(df_ops, use_container_width=True)

# --- LÓGICA DE FILTRADO ---
def filtrar_datos(df_v, df_o, tipo, mes_n, ano_n):
    if df_v.empty and df_o.empty: return df_v, df_o
    if tipo == "Mes Específico":
        v_f = df_v[(df_v['Fecha'].dt.month == mes_n) & (df_v['Fecha'].dt.year == ano_n)] if not df_v.empty else df_v
        o_f = df_o[(df_o['Fecha'].dt.month == mes_n) & (df_o['Fecha'].dt.year == ano_n)] if not df_o.empty else df_o
    else:
        v_f = df_v[df_v['Fecha'].dt.year == ano_n] if not df_v.empty else df_v
        o_f = df_o[df_o['Fecha'].dt.year == ano_n] if not df_o.empty else df_o
    return v_f, o_f

# --- BALANCE ---
with tab4:
    st.header("📊 Balance Numérico")
    fil_b = st.radio("Filtro:", ["Mes Específico", "Año Completo"], horizontal=True, key="fb")
    anos = list(range(2024, datetime.now().year + 5))
    c1, c2 = st.columns(2)
    m_b = c1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1, key="mb")
    a_b = c2.selectbox("Año:", anos, index=anos.index(datetime.now().year), key="ab")
    
    m_num_b = [k for k, v in meses.items() if v == m_b][0]
    v_b, o_b = filtrar_datos(df_ven, df_ops, fil_b, m_num_b, a_b)
    
    bruta = v_b['Ganancia'].sum() if not v_b.empty else 0
    gastos = o_b['Monto'].sum() if not o_b.empty else 0
    neta = bruta - gastos
    inv_val = (df_inv['Stock'] * df_inv['Costo']).sum() if not df_inv.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Ganancia Bruta", f"${bruta:,.2f}")
    col2.metric("Gastos", f"- ${gastos:,.2f}")
    col3.metric("Utilidad Neta", f"${neta:,.2f}")
    st.write(f"**Capital en Stock:** ${inv_val:,.2f}")

# --- DASHBOARD ---
with tab5:
    st.header("📈 Dashboard Visual Pro")
    fil_d = st.radio("Filtro Visual:", ["Mes Específico", "Año Completo"], horizontal=True, key="fd")
    cd1, cd2 = st.columns(2)
    m_d = cd1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1, key="md")
    a_d = cd2.selectbox("Año:", anos, index=anos.index(datetime.now().year), key="ad")
    
    m_num_d = [k for k, v in meses.items() if v == m_d][0]
    v_d, o_d = filtrar_datos(df_ven, df_ops, fil_d, m_num_d, a_d)

    if not v_d.empty:
        g1, g2 = st.columns(2)
        fig1 = px.bar(v_d.groupby('Producto')['Ganancia'].sum().reset_index(), x='Producto', y='Ganancia', color='Producto', title="🏆 Top Ganancias", template="plotly_dark")
        g1.plotly_chart(fig1, use_container_width=True)
        
        if not o_d.empty:
            fig2 = px.pie(o_d, values='Monto', names='Concepto', hole=0.5, title="💸 Distribución Gastos", template="plotly_dark")
            g2.plotly_chart(fig2, use_container_width=True)
        
        # NUEVO TREEMAP
        st.write("### 🗺️ Mapa de Importancia (Treemap)")
        fig_tree = px.treemap(v_d, path=['Producto'], values='Ganancia', color='Ganancia', color_continuous_scale='RdYlGn', title="Proporción de Ganancia por Producto", template="plotly_dark")
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.write("### 📅 Evolución del Tiempo")
        fig3 = px.line(v_d.groupby('Fecha')['Ganancia'].sum().reset_index(), x='Fecha', y='Ganancia', markers=True, title="Flujo de Ventas Diarias", template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Sin datos para graficar.")

# --- GUARDAR ---
with tab6:
    st.download_button("📥 Descargar Excel Tulip S.A.", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name="Tulip_SA.xlsx", use_container_width=True)
