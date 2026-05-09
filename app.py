import streamlit as st
import pandas as pd
import numpy_financial as npf
import plotly.express as px
from io import BytesIO
from datetime import datetime

# Configuración de Identidad Tulip S.A. 🌷
st.set_page_config(page_title="Tulip S.A. ERP", page_icon="🌷", layout="wide")

# --- MEMORIA ACTIVA (Session State) ---
if 'df_inv' not in st.session_state:
    st.session_state.df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
if 'df_ven' not in st.session_state:
    st.session_state.df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
if 'df_ops' not in st.session_state:
    st.session_state.df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

def convertir_a_excel(df_inv, df_ven, df_ops):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_inv.to_excel(writer, index=False, sheet_name='Inventario')
        df_ven.to_excel(writer, index=False, sheet_name='Ventas')
        df_ops.to_excel(writer, index=False, sheet_name='Gastos')
    return output.getvalue()

st.markdown("<h1 style='text-align: center;'>🌷 Tulip S.A.</h1>", unsafe_allow_html=True)

# --- CARGA AUTOMÁTICA DE DATOS ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos Tulip S.A.", type=["xlsx"])

if archivo_subido is not None:
    try:
        # Solo cargamos si la memoria está vacía para no borrar lo que el usuario acaba de escribir
        if st.sidebar.button("🔄 Sincronizar/Resetear con este archivo"):
            st.session_state.df_inv = pd.read_excel(archivo_subido, sheet_name=0)
            st.session_state.df_ven = pd.read_excel(archivo_subido, sheet_name=1)
            st.session_state.df_ops = pd.read_excel(archivo_subido, sheet_name=2)
            # Asegurar formato fecha
            st.session_state.df_ven['Fecha'] = pd.to_datetime(st.session_state.df_ven['Fecha'], errors='coerce').fillna(pd.Timestamp.now())
            st.session_state.df_ops['Fecha'] = pd.to_datetime(st.session_state.df_ops['Fecha'], errors='coerce').fillna(pd.Timestamp.now())
            st.success("✅ Datos cargados en memoria.")
    except:
        st.sidebar.error("Formato no compatible.")

# Referencias directas a la memoria activa
inv = st.session_state.df_inv
ven = st.session_state.df_ven
ops = st.session_state.df_ops

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📦 Stock", "🛒 Ventas", "💸 Gastos", "📑 Balance", "📈 Dashboard", "💾 Guardar"])

# --- PESTAÑA 1: STOCK (SUMA CORREGIDA) ---
with tab1:
    st.subheader("Gestión de Inventario 🌷")
    opciones = ["--- Nuevo Producto ---"] + sorted(list(inv['Producto'].unique())) if not inv.empty else ["--- Nuevo Producto ---"]
    sel = st.selectbox("Selecciona producto:", opciones)
    
    if sel != "--- Nuevo Producto ---":
        f_idx = inv[inv['Producto'] == sel].index[0]
        d_n, d_c, d_s, d_co, d_v = sel, inv.at[f_idx, 'Categoria'], int(inv.at[f_idx, 'Stock']), float(inv.at[f_idx, 'Costo']), float(inv.at[f_idx, 'Venta'])
    else:
        f_idx, d_n, d_c, d_s, d_co, d_v = None, "", "", 0, 0.0, 0.0

    nom_i = st.text_input("Nombre del Producto", value=d_n).capitalize()
    cat_i = st.text_input("Categoría", value=d_c).capitalize()
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write(f"**Stock actual en sistema: {d_s}**")
        sumar_cant = st.number_input("¿Cuánto vas a SUMAR?", min_value=0, step=1, value=0)
    with col_s2:
        costo_i = st.number_input("Costo Unitario:", value=d_co, format="%.2f")
        venta_i = st.number_input("Precio Venta:", value=d_v, format="%.2f")
    
    if st.button("✅ GUARDAR CAMBIOS"):
        if nom_i:
            nuevo_total = d_s + sumar_cant
            if f_idx is not None:
                st.session_state.df_inv.loc[f_idx, ['Producto', 'Categoria', 'Stock', 'Costo', 'Venta']] = [nom_i, cat_i, nuevo_total, costo_i, venta_i]
            else:
                nueva_f = pd.DataFrame([{"Producto": nom_i, "Categoria": cat_i, "Stock": sumar_cant, "Costo": costo_i, "Venta": venta_i}])
                st.session_state.df_inv = pd.concat([st.session_state.df_inv, nueva_f], ignore_index=True)
            st.success(f"📦 ¡{nom_i} actualizado! Total: {nuevo_total}")
            st.rerun()

    st.write("---")
    st.dataframe(st.session_state.df_inv, use_container_width=True)

# --- PESTAÑA 2: VENTAS (CON SUMA TOTAL) ---
with tab2:
    st.subheader("Historial y Registro de Ventas")
    with st.expander("🛒 Registrar Venta"):
        if not inv.empty:
            p_v = st.selectbox("¿Qué vendiste?", inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            f_v = st.date_input("Fecha", datetime.now())
            if st.button("🚀 Confirmar Venta"):
                idx_v = inv[inv['Producto'] == p_v].index[0]
                if inv.at[idx_v, 'Stock'] >= c_v:
                    c_m, v_m = inv.at[idx_v, 'Costo'], inv.at[idx_v, 'Venta']
                    gan = c_v * (v_m - c_m)
                    st.session_state.df_inv.at[idx_v, 'Stock'] -= c_v
                    nueva_v = pd.DataFrame([{"Fecha": pd.to_datetime(f_v), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": c_m, "Venta_Ref": v_m, "Ganancia": gan}])
                    st.session_state.df_ven = pd.concat([st.session_state.df_ven, nueva_v], ignore_index=True)
                    st.success("Venta Exitosa")
                    st.rerun()

    st.divider()
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    m_h = st.selectbox("Seleccionar Mes para Historial:", list(meses.values()), index=datetime.now().month-1)
    
    if not ven.empty:
        ven['Fecha'] = pd.to_datetime(ven['Fecha'])
        m_num = [k for k, v in meses.items() if v == m_h][0]
        v_mes = ven[ven['Fecha'].dt.month == m_num]
        st.dataframe(v_mes, use_container_width=True)
        st.markdown(f"### 💰 Ganancia Total {m_h}: **${v_mes['Ganancia'].sum():,.2f}**")

# --- PESTAÑA 3: GASTOS ---
with tab3:
    st.subheader("Registro de Gastos")
    with st.form("g_add"):
        con_g = st.text_input("Concepto (Alquiler, Luz, etc.)")
        mon_g = st.number_input("Monto", min_value=0.0)
        f_g = st.date_input("Fecha Gasto", datetime.now())
        if st.form_submit_button("Añadir Gasto"):
            new_g = pd.DataFrame([{"Fecha": pd.to_datetime(f_g), "Concepto": con_g, "Monto": mon_g}])
            st.session_state.df_ops = pd.concat([st.session_state.df_ops, new_g], ignore_index=True)
            st.rerun()
    st.dataframe(st.session_state.df_ops, use_container_width=True)

# --- PESTAÑA 4: BALANCE (SIN ERRORES) ---
with tab4:
    st.header("📑 Balance tulip S.A.")
    fil_b = st.radio("Filtro:", ["Mes", "Año"], horizontal=True)
    col_b1, col_b2 = st.columns(2)
    m_b = col_b1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1, key="mb")
    a_b = col_b2.selectbox("Año:", list(range(2024, 2030)), index=list(range(2024, 2030)).index(datetime.now().year), key="ab")
    
    m_nb = [k for k, v in meses.items() if v == m_b][0]
    
    # Filtrado Seguro
    df_v_filt = ven.copy()
    df_o_filt = ops.copy()
    df_v_filt['Fecha'] = pd.to_datetime(df_v_filt['Fecha'])
    df_o_filt['Fecha'] = pd.to_datetime(df_o_filt['Fecha'])

    if fil_b == "Mes":
        v_final = df_v_filt[(df_v_filt['Fecha'].dt.month == m_nb) & (df_v_filt['Fecha'].dt.year == a_b)]
        o_final = df_o_filt[(df_o_filt['Fecha'].dt.month == m_nb) & (df_o_filt['Fecha'].dt.year == a_b)]
    else:
        v_final = df_v_filt[df_v_filt['Fecha'].dt.year == a_b]
        o_final = df_o_filt[df_o_filt['Fecha'].dt.year == a_b]

    bruta, gastos = v_final['Ganancia'].sum(), o_final['Monto'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Ganancia Bruta", f"${bruta:,.2f}")
    c2.metric("Gastos", f"- ${gastos:,.2f}")
    c3.metric("Utilidad Neta", f"${bruta - gastos:,.2f}")
    
    inv_val = (inv['Stock'] * inv['Costo']).sum() if not inv.empty else 0
    st.info(f"Capital en Stock hoy: ${inv_val:,.2f}")

# --- PESTAÑA 5: DASHBOARD ---
with tab5:
    st.header("📈 Dashboard Visual")
    if not v_final.empty:
        col_d1, col_d2 = st.columns(2)
        fig1 = px.bar(v_final.groupby('Producto')['Ganancia'].sum().reset_index(), x='Producto', y='Ganancia', color='Producto', template="plotly_dark", title="Ganancia por Producto")
        col_d1.plotly_chart(fig1, use_container_width=True)
        if not o_final.empty:
            fig2 = px.pie(o_final, values='Monto', names='Concepto', hole=0.5, template="plotly_dark", title="Gastos")
            col_d2.plotly_chart(fig2, use_container_width=True)
    else: st.info("Sin datos para graficar.")

# --- PESTAÑA 6: GUARDAR ---
with tab6:
    st.subheader("💾 Guardar y Descargar")
    st.info("Descarga tu archivo para llevarte tus cambios.")
    excel_ready = convertir_a_excel(st.session_state.df_inv, st.session_state.df_ven, st.session_state.df_ops)
    st.download_button("📥 DESCARGAR EXCEL FINAL", data=excel_ready, file_name=f"Tulip_SA_ERP.xlsx", use_container_width=True)
