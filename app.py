import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px
from io import BytesIO
from datetime import datetime

# Configuración Tulip S.A. 🌷
st.set_page_config(page_title="Tulip S.A. ERP", page_icon="🌷", layout="wide")

# --- FUNCIONES DE APOYO ---
def convertir_a_excel(df_inv, df_ven, df_ops):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_inv.to_excel(writer, index=False, sheet_name='Inventario')
        df_ven.to_excel(writer, index=False, sheet_name='Ventas')
        df_ops.to_excel(writer, index=False, sheet_name='Gastos')
    return output.getvalue()

# --- INICIALIZACIÓN DE MEMORIA (Session State) ---
if 'df_inv' not in st.session_state:
    st.session_state.df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
if 'df_ven' not in st.session_state:
    st.session_state.df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
if 'df_ops' not in st.session_state:
    st.session_state.df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

st.markdown("<h1 style='text-align: center;'>🌷 Tulip S.A.</h1>", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos Tulip S.A.", type=["xlsx"])

if archivo_subido is not None and st.button("📥 Sincronizar Archivo"):
    try:
        st.session_state.df_inv = pd.read_excel(archivo_subido, sheet_name=0)
        st.session_state.df_ven = pd.read_excel(archivo_subido, sheet_name=1)
        st.session_state.df_ops = pd.read_excel(archivo_subido, sheet_name=2)
        st.session_state.df_ven['Fecha'] = pd.to_datetime(st.session_state.df_ven['Fecha'], errors='coerce')
        st.session_state.df_ops['Fecha'] = pd.to_datetime(st.session_state.df_ops['Fecha'], errors='coerce')
        st.success("✅ ¡Datos cargados en la memoria de Tulip S.A.!")
    except:
        st.error("Error en el archivo. Verifica las pestañas.")

# Usamos los datos de la MEMORIA, no del archivo directo
df_inv = st.session_state.df_inv
df_ven = st.session_state.df_ven
df_ops = st.session_state.df_ops

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📦 Stock", "🛒 Ventas", "💸 Gastos", "📑 Balance", "📈 Dashboard", "💾 Guardar"])

# --- PESTAÑA 1: STOCK (Suma Infalible) ---
with tab1:
    st.subheader("Gestión de Inventario 🌷")
    opciones = ["--- Nuevo Producto ---"] + sorted(list(df_inv['Producto'].unique())) if not df_inv.empty else ["--- Nuevo Producto ---"]
    sel = st.selectbox("Selecciona producto:", opciones)
    
    if sel != "--- Nuevo Producto ---":
        f_idx = df_inv[df_inv['Producto'] == sel].index[0]
        d_n, d_c, d_s, d_co, d_v = sel, df_inv.at[f_idx, 'Categoria'], int(df_inv.at[f_idx, 'Stock']), float(df_inv.at[f_idx, 'Costo']), float(df_inv.at[f_idx, 'Venta'])
    else:
        f_idx, d_n, d_c, d_s, d_co, d_v = None, "", "", 0, 0.0, 0.0

    nombre_i = st.text_input("Nombre del Producto", value=d_n).capitalize()
    cat_i = st.text_input("Categoría", value=d_c).capitalize()
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.info(f"Stock actual: {d_s}")
        sumar_i = st.number_input("¿Cuánto vas a SUMAR?", min_value=0, step=1, value=0)
    with col_s2:
        costo_i = st.number_input("Costo Unitario:", value=d_co, format="%.2f")
        venta_i = st.number_input("Precio Venta:", value=d_v, format="%.2f")
    
    if st.button("✅ GUARDAR CAMBIOS"):
        if nombre_i:
            nuevo_total = d_s + sumar_i
            if f_idx is not None:
                st.session_state.df_inv.loc[f_idx, ['Producto', 'Categoria', 'Stock', 'Costo', 'Venta']] = [nombre_i, cat_i, nuevo_total, costo_i, venta_i]
            else:
                nueva_f = pd.DataFrame([{"Producto": nombre_i, "Categoria": cat_i, "Stock": sumar_i, "Costo": costo_i, "Venta": venta_i}])
                st.session_state.df_inv = pd.concat([st.session_state.df_inv, nueva_f], ignore_index=True)
            st.success(f"📦 ¡{nombre_i} actualizado! Nuevo total: {nuevo_total}")
            st.rerun()

    st.write("---")
    st.dataframe(st.session_state.df_inv, use_container_width=True)

# --- PESTAÑA 2: VENTAS (Con Tabla de Suma) ---
with tab2:
    st.subheader("Historial de Ventas")
    with st.expander("🛒 Registrar Nueva Venta"):
        if not df_inv.empty:
            p_v = st.selectbox("¿Qué se vendió?", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            f_v = st.date_input("Fecha", datetime.now())
            if st.button("🚀 Confirmar Venta"):
                idx_v = df_inv[df_inv['Producto'] == p_v].index[0]
                if df_inv.at[idx_v, 'Stock'] >= c_v:
                    costo_m, venta_m = df_inv.at[idx_v, 'Costo'], df_inv.at[idx_v, 'Venta']
                    gan = c_v * (venta_m - costo_m)
                    # Actualizar Stock en memoria
                    st.session_state.df_inv.at[idx_v, 'Stock'] -= c_v
                    # Registrar venta
                    nueva_v = pd.DataFrame([{"Fecha": pd.to_datetime(f_v), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": costo_m, "Venta_Ref": venta_m, "Ganancia": gan}])
                    st.session_state.df_ven = pd.concat([st.session_state.df_ven, nueva_v], ignore_index=True)
                    st.success("Venta Exitosa")
                    st.rerun()
                else: st.error("Stock insuficiente")

    st.divider()
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    m_hist = st.selectbox("Seleccionar Mes para ver Historial:", list(meses.values()), index=datetime.now().month-1)
    
    if not st.session_state.df_ven.empty:
        df_ven_dt = st.session_state.df_ven.copy()
        df_ven_dt['Fecha'] = pd.to_datetime(df_ven_dt['Fecha'])
        m_num = [k for k, v in meses.items() if v == m_hist][0]
        v_mes = df_ven_dt[df_ven_dt['Fecha'].dt.month == m_num]
        
        st.write(f"### Detalle de Ventas - {m_hist}")
        st.dataframe(v_mes, use_container_width=True)
        total_m = v_mes['Ganancia'].sum()
        st.markdown(f"### 💰 Suma Total Ganancia {m_hist}: **${total_m:,.2f}**")

# --- PESTAÑA 4: BALANCE (Numérico) ---
with tab4:
    st.header("📑 Balance tulip S.A.")
    filtro_b = st.radio("Tipo de Balance:", ["Mes", "Año"], horizontal=True)
    anos_l = list(range(2024, datetime.now().year + 3))
    
    col_b1, col_b2 = st.columns(2)
    m_b = col_b1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1, key="mb")
    a_b = col_b2.selectbox("Año:", anos_l, index=anos_l.index(datetime.now().year), key="ab")
    
    m_nb = [k for k, v in meses.items() if v == m_b][0]
    
    # Filtrado para Balance
    v_b = df_ven[(df_ven['Fecha'].dt.month == m_nb) & (df_ven['Fecha'].dt.year == a_b)] if filtro_b == "Mes" else df_ven[df_ven['Fecha'].dt.year == a_b]
    g_b = df_ops[(df_ops['Fecha'].dt.month == m_nb) & (df_ops['Fecha'].dt.year == a_b)] if filtro_b == "Mes" else df_ops[df_ops['Fecha'].dt.year == a_b]
    
    bruta, gastos = v_b['Ganancia'].sum(), g_b['Monto'].sum()
    st.write("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ganancia Bruta", f"${bruta:,.2f}")
    c2.metric("Gastos Totales", f"- ${gastos:,.2f}")
    c3.metric("Utilidad Neta", f"${bruta - gastos:,.2f}")
    
    st.write("---")
    st.subheader("Indicadores Pro")
    inv_val = (df_inv['Stock'] * df_inv['Costo']).sum()
    renta = ((bruta - gastos) / inv_val * 100) if inv_val > 0 else 0
    
    f1, f2, f3 = st.columns(3)
    f1.write(f"**Capital en Stock:** ${inv_val:,.2f}")
    f2.write(f"**Rentabilidad:** {renta:.2f}%")
    if inv_val > 0:
        flujos = [-inv_val] + [(bruta - gastos)] * 12
        f3.write(f"**TIR Estimada:** {npf.irr(flujos)*100:.2f}%")
        st.write(f"**VAN:** ${npf.npv(0.1, flujos):,.2f}")

# --- PESTAÑA 5: DASHBOARD (Visual) ---
with tab5:
    st.header("📈 Dashboard Pro")
    if not v_b.empty:
        col_d1, col_d2 = st.columns(2)
        fig1 = px.bar(v_b.groupby('Producto')['Ganancia'].sum().reset_index(), x='Producto', y='Ganancia', color='Producto', title="🏆 Top Ventas", template="plotly_dark")
        col_d1.plotly_chart(fig1, use_container_width=True)
        
        if not g_b.empty:
            fig2 = px.pie(g_b, values='Monto', names='Concepto', hole=0.5, title="💸 Gastos", template="plotly_dark")
            col_d2.plotly_chart(fig2, use_container_width=True)
        
        fig3 = px.treemap(v_b, path=['Producto'], values='Ganancia', title="Mapa de Negocio", template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)
        
        fig4 = px.line(v_b.groupby('Fecha')['Ganancia'].sum().reset_index(), x='Fecha', y='Ganancia', title="Flujo Diario", markers=True, template="plotly_dark")
        st.plotly_chart(fig4, use_container_width=True)
    else: st.info("Sin datos para graficar.")

# --- PESTAÑA 6: GUARDAR ---
with tab6:
    st.subheader("💾 Guardar Cambios")
    st.warning("Pulsa el botón para generar el nuevo archivo.")
    excel_ready = convertir_a_excel(st.session_state.df_inv, st.session_state.df_ven, st.session_state.df_ops)
    st.download_button("📥 DESCARGAR EXCEL FINAL", data=excel_ready, file_name=f"Tulip_SA_{datetime.now().strftime('%d_%m')}.xlsx", use_container_width=True)
