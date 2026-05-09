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

# --- CARGA DE DATOS SEGURA ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos Tulip S.A.", type=["xlsx"])

# Columnas estándar que debe tener el programa
COLS_INV = ["Producto", "Categoria", "Stock", "Costo", "Venta"]
COLS_VEN = ["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"]
COLS_OPS = ["Fecha", "Concepto", "Monto"]

if archivo_subido:
    try:
        excel = pd.ExcelFile(archivo_subido)
        hojas = excel.sheet_names
        
        # Cargar Inventario (Hoja 1)
        df_inv = pd.read_excel(archivo_subido, sheet_name=0)
        
        # Cargar Ventas (Hoja 2)
        if len(hojas) > 1:
            df_ven = pd.read_excel(archivo_subido, sheet_name=1)
        else:
            df_ven = pd.DataFrame(columns=COLS_VEN)
            
        # Cargar Gastos (Hoja 3)
        if len(hojas) > 2:
            df_ops = pd.read_excel(archivo_subido, sheet_name=2)
        else:
            df_ops = pd.DataFrame(columns=COLS_OPS)

        # SEGURO ANTI-ERRORES: Si falta la columna 'Fecha', la creamos
        if 'Fecha' in df_ven.columns:
            df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'], errors='coerce')
        else:
            df_ven['Fecha'] = datetime.now()

        if 'Fecha' in df_ops.columns:
            df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'], errors='coerce')
        else:
            df_ops['Fecha'] = datetime.now()

        st.success("✅ Datos sincronizados y actualizados.")
    except Exception as e:
        st.error(f"⚠️ Se inició una base limpia para evitar errores.")
        df_inv = pd.DataFrame(columns=COLS_INV)
        df_ven = pd.DataFrame(columns=COLS_VEN)
        df_ops = pd.DataFrame(columns=COLS_OPS)
else:
    df_inv = pd.DataFrame(columns=COLS_INV)
    df_ven = pd.DataFrame(columns=COLS_VEN)
    df_ops = pd.DataFrame(columns=COLS_OPS)

# --- INTERFAZ ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance", "💾 Guardar"])

with tab1:
    st.subheader("Gestión de Inventario 🌷")
    with st.expander("➕ Añadir / Editar Producto"):
        opciones = ["Nuevo"] + (list(df_inv['Producto'].unique()) if not df_inv.empty else [])
        sel = st.selectbox("Producto:", opciones)
        
        d_n, d_c, d_s, d_co, d_v = "", "", 0, 0.0, 0.0
        if sel != "Nuevo" and not df_inv.empty:
            f = df_inv[df_inv['Producto'] == sel].iloc[0]
            d_n, d_c, d_s, d_co, d_v = sel, f['Categoria'], int(f['Stock']), float(f['Costo']), float(f['Venta'])

        with st.form("f_inv"):
            n = st.text_input("Nombre", value=d_n).capitalize()
            c = st.text_input("Categoría", value=d_c).capitalize()
            can = st.number_input("Stock", value=d_s, min_value=0)
            cos = st.number_input("Costo", value=d_co, format="%.2f")
            ven = st.number_input("Venta", value=d_v, format="%.2f")
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
            p_v = st.selectbox("Seleccionar:", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            if st.form_submit_button("Vender"):
                idx = df_inv[df_inv['Producto'] == p_v].index[0]
                if df_inv.at[idx, 'Stock'] >= c_v:
                    c_m, v_m = df_inv.at[idx, 'Costo'], df_inv.at[idx, 'Venta']
                    gan = c_v * (v_m - c_m)
                    df_inv.at[idx, 'Stock'] -= c_v
                    nueva = pd.DataFrame([{"Fecha": datetime.now(), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": c_m, "Venta_Ref": v_m, "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                    st.success("¡Venta OK!")
                else: st.error("Stock insuficiente")
    st.dataframe(df_ven.sort_values(by="Fecha", ascending=False) if not df_ven.empty else df_ven, use_container_width=True)

with tab3:
    st.subheader("Gastos Operativos")
    with st.form("f_g"):
        con = st.text_input("Concepto (Alquiler, etc.)")
        mon = st.number_input("Monto", min_value=0.0)
        f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Registrar"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": f_g, "Concepto": con, "Monto": mon}])], ignore_index=True)
            st.success("Gasto guardado")
    st.dataframe(df_ops, use_container_width=True)

with tab4:
    st.header("📊 Balance Tulip S.A.")
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    anos = [2024, 2025, 2026, 2027, 2028]
    
    col1, col2 = st.columns(2)
    m_sel = col1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1)
    a_sel = col2.selectbox("Año:", anos, index=anos.index(datetime.now().year))
    
    m_num = [k for k, v in meses.items() if v == m_sel][0]
    
    # Filtrar datos de forma segura
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'], errors='coerce')
    v_f = df_ven[(df_ven['Fecha'].dt.month == m_num) & (df_ven['Fecha'].dt.year == a_sel)] if not df_ven.empty else pd.DataFrame()
    bruta = v_f['Ganancia'].sum() if not v_f.empty else 0
    
    if not df_ops.empty:
        df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'], errors='coerce')
        g_f = df_ops[(df_ops['Fecha'].dt.month == m_num) & (df_ops['Fecha'].dt.year == a_sel)]
        gastos = g_f['Monto'].sum()
    else: gastos = 0
    
    inv = (df_inv['Stock'] * df_inv['Costo']).sum() if not df_inv.empty else 0
    
    st.metric("Utilidad Bruta", f"${bruta:,.2f}")
    st.metric("Gastos (Alquiler/Luz)", f"- ${gastos:,.2f}")
    st.metric("Utilidad Neta", f"${bruta - gastos:,.2f}")
    st.metric("Capital en Stock", f"${inv:,.2f}")

    if inv > 0:
        flujos = [-inv] + [bruta - gastos] * 12
        try:
            st.write(f"**TIR:** {npf.irr(flujos)*100:.2f}%")
            st.write(f"**VAN:** ${npf.npv(0.1, flujos):,.2f}")
        except: st.write("Indicadores en cálculo...")

with tab5:
    st.subheader("💾 Guardar Cambios")
    st.download_button("📥 Descargar Excel Tulip S.A.", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name="Tulip_SA_Backup.xlsx", use_container_width=True)
