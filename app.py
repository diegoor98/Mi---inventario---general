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
        excel_file = pd.ExcelFile(archivo_subido)
        df_inv = pd.read_excel(archivo_subido, sheet_name=0)
        df_ven = pd.read_excel(archivo_subido, sheet_name=1)
        df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'], errors='coerce')
        df_ops = pd.read_excel(archivo_subido, sheet_name=2)
        df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'], errors='coerce')
    except:
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance Total", "💾 Guardar"])

with tab1:
    st.subheader("Gestión de Inventario")
    with st.expander("➕ Añadir / Editar Producto"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Seleccionar:", opciones)
        if sel != "Nuevo":
            d = df_inv[df_inv['Producto'] == sel].iloc
            v_n, v_c, v_s, v_co, v_v = sel, d['Categoria'], int(d['Stock']), float(d['Costo']), float(d['Venta'])
        else: v_n, v_c, v_s, v_co, v_v = "", "", 0, 0.0, 0.0

        with st.form("f_inv"):
            n = st.text_input("Nombre", value=v_n).capitalize()
            c = st.text_input("Categoría", value=v_c).capitalize()
            can = st.number_input("Stock", value=v_s, min_value=0)
            cos = st.number_input("Costo", value=v_co)
            ven = st.number_input("Venta", value=v_v)
            if st.form_submit_button("Guardar"):
                if n in df_inv['Producto'].values:
                    df_inv.loc[df_inv['Producto'] == n, ['Categoria', 'Stock', 'Costo', 'Venta']] = [c, can, cos, ven]
                else:
                    df_inv = pd.concat([df_inv, pd.DataFrame([{"Producto": n, "Categoria": c, "Stock": can, "Costo": cos, "Venta": ven}])], ignore_index=True)
                st.rerun()
    st.dataframe(df_inv, use_container_width=True)

with tab2:
    st.subheader("Ventas y Auditoría")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        with st.form("f_v"):
            p_v = st.selectbox("Producto", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            if st.form_submit_button("Vender"):
                idx = df_inv[df_inv['Producto'] == p_v].index
                if df_inv.at[idx, 'Stock'] >= c_v:
                    gan = c_v * (df_inv.at[idx, 'Venta'] - df_inv.at[idx, 'Costo'])
                    nueva = pd.DataFrame([{"Fecha": datetime.now(), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": df_inv.at[idx, 'Costo'], "Venta_Ref": df_inv.at[idx, 'Venta'], "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                    df_inv.at[idx, 'Stock'] -= c_v
                    st.success("¡Venta registrada!")
                else: st.error("Stock insuficiente")
    
    with col_b:
        st.write("### Historial de Ventas")
        if not df_ven.empty:
            df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
            f_inicio = st.date_input("Desde", df_ven['Fecha'].min())
            f_fin = st.date_input("Hasta", df_ven['Fecha'].max())
            mask = (df_ven['Fecha'].dt.date >= f_inicio) & (df_ven['Fecha'].dt.date <= f_fin)
            st.dataframe(df_ven[mask].sort_values(by="Fecha", ascending=False), use_container_width=True)

with tab3:
    st.subheader("Registro de Gastos Operativos")
    with st.form("f_g"):
        con = st.text_input("Concepto (Alquiler, Luz, etc.)")
        mon = st.number_input("Monto", min_value=0.0)
        f_g = st.date_input("Fecha del gasto", datetime.now())
        if st.form_submit_button("Registrar Gasto"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": f_g, "Concepto": con, "Monto": mon}])], ignore_index=True)
            st.success("Gasto guardado")
    st.dataframe(df_ops, use_container_width=True)

with tab4:
    st.header("📊 Balance y Rentabilidad Tulip S.A.")
    
    # Filtros de Balance
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    c1, c2 = st.columns(2)
    m_sel = c1.selectbox("Filtrar Mes:", list(meses.values()), index=datetime.now().month-1)
    a_sel = c2.selectbox("Filtrar Año:",, index=2)
    m_num = [k for k, v in meses.items() if v == m_sel]

    # Cálculos filtrados
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'])
    
    v_filtradas = df_ven[(df_ven['Fecha'].dt.month == m_num) & (df_ven['Fecha'].dt.year == a_sel)]
    g_filtrados = df_ops[(df_ops['Fecha'].dt.month == m_num) & (df_ops['Fecha'].dt.year == a_sel)]
    
    gan_bruta = v_filtradas['Ganancia'].sum()
    total_gastos = g_filtrados['Monto'].sum()
    utilidad_neta = gan_bruta - total_gastos
    inversion_stock = (df_inv['Stock'] * df_inv['Costo']).sum()

    # Visualización
    col1, col2, col3 = st.columns(3)
    col1.metric("Ganancia Bruta", f"${gan_bruta:,.2f}")
    col2.metric("Gastos (Alquiler/Ops)", f"- ${total_gastos:,.2f}", delta_color="inverse")
    col3.metric("Utilidad Neta", f"${utilidad_neta:,.2f}")

    st.divider()
    
    st.subheader("Indicadores Financieros")
    f1, f2, f3 = st.columns(3)
    f1.write(f"**Costo de Stock:** ${inversion_stock:,.2f}")
    
    # Rentabilidad, VAN y TIR
    renta = (utilidad_neta / inversion_stock * 100) if inversion_stock > 0 else 0
    f2.write(f"**Rentabilidad:** {renta:.2f}%")
    
    if inversion_stock > 0:
        flujos = [-inversion_stock] + [utilidad_neta] * 12
        tir_val = npf.irr(flujos)
        van_val = npf.npv(0.12/12, flujos)
        f3.write(f"**TIR:** {tir_val*100:.2f}%" if not pd.isna(tir_val) else "**TIR:** N/D")
        st.write(f"**VAN (Valor Actual Neto):** ${van_val:,.2f}")

with tab5:
    st.download_button("📥 Descargar Excel Final", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name="Tulip_SA_Final.xlsx", use_container_width=True)
