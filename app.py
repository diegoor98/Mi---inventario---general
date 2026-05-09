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

# --- CARGA DE DATOS ROBUSTA ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos Tulip S.A.", type=["xlsx"])

if archivo_subido:
    try:
        df_inv = pd.read_excel(archivo_subido, sheet_name=0)
        try:
            df_ven = pd.read_excel(archivo_subido, sheet_name=1)
            df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'], errors='coerce')
        except:
            df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        try:
            df_ops = pd.read_excel(archivo_subido, sheet_name=2)
            df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'], errors='coerce')
        except:
            df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
        st.success("✅ Conexión establecida con éxito.")
    except Exception as e:
        st.error(f"Error al cargar: {e}")
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
                    nuevo = pd.DataFrame([{"Producto": n, "Categoria": c, "Stock": can, "Costo": cos, "Venta": ven}])
                    df_inv = pd.concat([df_inv, nuevo], ignore_index=True)
                st.rerun()
    st.dataframe(df_inv, use_container_width=True)

with tab2:
    st.subheader("Registro de Ventas")
    col_v1, col_v2 = st.columns()
    with col_v1:
        with st.form("f_v"):
            p_v = st.selectbox("Producto", df_inv['Producto'].unique() if not df_inv.empty else [])
            cant_v = st.number_input("Cantidad", min_value=1)
            if st.form_submit_button("Registrar Venta"):
                idx = df_inv[df_inv['Producto'] == p_v].index
                if not idx.empty and df_inv.at[idx, 'Stock'] >= cant_v:
                    gan = cant_v * (df_inv.at[idx, 'Venta'] - df_inv.at[idx, 'Costo'])
                    nueva = pd.DataFrame([{"Fecha": datetime.now(), "Producto": p_v, "Cantidad": cant_v, "Costo_Ref": df_inv.at[idx, 'Costo'], "Venta_Ref": df_inv.at[idx, 'Venta'], "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                    df_inv.at[idx, 'Stock'] -= cant_v
                    st.success("¡Venta OK!")
                else: st.error("Error en Stock")
    with col_v2:
        if not df_ven.empty:
            df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
            st.write("### Historial")
            st.dataframe(df_ven.sort_values(by="Fecha", ascending=False), use_container_width=True)

with tab3:
    st.subheader("Gastos Operativos")
    with st.form("f_g"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto", min_value=0.0)
        f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Registrar"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": f_g, "Concepto": con, "Monto": mon}])], ignore_index=True)
            st.success("Gasto añadido")
    st.dataframe(df_ops, use_container_width=True)

with tab4:
    st.header("📊 Balance Integral Tulip S.A.")
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    # --- LISTA DE AÑOS AUTOMÁTICA ---
    ano_actual = datetime.now().year
    lista_anos = list(range(2024, ano_actual + 5))
    
    c1, c2 = st.columns(2)
    m_sel = c1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1)
    a_sel = c2.selectbox("Año:", lista_anos, index=lista_anos.index(ano_actual))
    
    m_num = [k for k, v in meses.items() if v == m_sel]

    # Filtrado
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    if not df_ops.empty:
        df_ops['Fecha'] = pd.to_datetime(df_ops['Fecha'])
        g_f = df_ops[(df_ops['Fecha'].dt.month == m_num) & (df_ops['Fecha'].dt.year == a_sel)]
        gastos = g_f['Monto'].sum()
    else: gastos = 0
    
    v_f = df_ven[(df_ven['Fecha'].dt.month == m_num) & (df_ven['Fecha'].dt.year == a_sel)]
    bruta = v_f['Ganancia'].sum()
    neta = bruta - gastos
    inv = (df_inv['Stock'] * df_inv['Costo']).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Ganancia Bruta", f"${bruta:,.2f}")
    col2.metric("Gastos Totales", f"- ${gastos:,.2f}", delta_color="inverse")
    col3.metric("Utilidad Neta", f"${neta:,.2f}")

    st.divider()
    st.subheader("Indicadores Financieros")
    f1, f2, f3 = st.columns(3)
    f1.write(f"**Capital en Stock:** ${inv:,.2f}")
    renta = (neta / inv * 100) if inv > 0 else 0
    f2.write(f"**Rentabilidad:** {renta:.2f}%")
    
    if inv > 0:
        flujos = [-inv] + [neta] * 12
        tir = npf.irr(flujos)
        van = npf.npv(0.12/12, flujos)
        f3.write(f"**TIR:** {tir*100:.2f}%" if not pd.isna(tir) else "TIR: N/D")
        st.write(f"**VAN (Valor Actual Neto):** ${van:,.2f}")

with tab5:
    st.download_button("📥 Descargar Excel Tulip S.A.", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name=f"Tulip_SA_{datetime.now().strftime('%d_%m')}.xlsx", use_container_width=True)
