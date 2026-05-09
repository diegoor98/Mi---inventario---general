import streamlit as st
import pandas as pd
import numpy_financial as npf
from io import BytesIO
from datetime import datetime

# Configuración Tulip S.A. 🌷
st.set_page_config(page_title="Tulip S.A. ERP", page_icon="🌷", layout="wide")

def convertir_a_excel(df_inv, df_ven, df_ops):
    output = BytesIO()
    fecha_str = datetime.now().strftime('%d-%m-%Y')
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_inv.to_excel(writer, index=False, sheet_name='Stock_General')
        df_ven.to_excel(writer, index=False, sheet_name='Historial_Ventas')
        df_ops.to_excel(writer, index=False, sheet_name='Gastos_Operativos')
    return output.getvalue()

st.markdown("<h1 style='text-align: center;'>🌷 Tulip S.A.</h1>", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos Tulip S.A.", type=["xlsx"])

if archivo_subido:
    try:
        df_inv = pd.read_excel(archivo_subido, sheet_name=0)
        df_ven = pd.read_excel(archivo_subido, sheet_name=1)
        df_ops = pd.read_excel(archivo_subido, sheet_name=2)
        df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    except:
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance Mensual", "💾 Guardar"])

with tab1:
    st.subheader("Gestión de Inventario Permanente 🌷")
    with st.expander("➕ Añadir / Editar Producto"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Producto:", opciones)
        d_n = sel if sel != "Nuevo" else ""
        d_c = df_inv[df_inv['Producto']==sel].iloc[0]['Categoria'] if sel != "Nuevo" else ""
        d_s = int(df_inv[df_inv['Producto']==sel].iloc[0]['Stock']) if sel != "Nuevo" else 0
        d_co = float(df_inv[df_inv['Producto']==sel].iloc[0]['Costo']) if sel != "Nuevo" else 0.0
        d_v = float(df_inv[df_inv['Producto']==sel].iloc[0]['Venta']) if sel != "Nuevo" else 0.0

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
    st.subheader("Registrar Venta 💰")
    if not df_inv.empty:
        p_v = st.selectbox("Vender:", df_inv['Producto'].unique())
        cant_v = st.number_input("Cant:", min_value=1)
        if st.button("Procesar Venta"):
            idx = df_inv[df_inv['Producto'] == p_v].index
            if df_inv.at[idx[0], 'Stock'] >= cant_v:
                c_m, v_m = df_inv.at[idx[0], 'Costo'], df_inv.at[idx[0], 'Venta']
                gan = cant_v * (v_m - c_m)
                df_inv.at[idx[0], 'Stock'] -= cant_v
                nueva = pd.DataFrame([{"Fecha": datetime.now(), "Producto": p_v, "Cantidad": cant_v, "Costo_Ref": c_m, "Venta_Ref": v_m, "Ganancia": gan}])
                df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                st.success("Venta Exitosa")
            else: st.error("Sin stock")

with tab3:
    st.subheader("Gastos Tulip S.A. 🏢")
    with st.form("f_gastos"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto", min_value=0.0)
        if st.form_submit_button("Añadir Gasto"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Monto": mon}])], ignore_index=True)
    st.dataframe(df_ops, use_container_width=True)

with tab4:
    st.header("📊 Balance Inteligente Tulip S.A.")
    
    # Selector de Mes y Año para el Balance
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    
    col_f1, col_f2 = st.columns(2)
    mes_sel = col_f1.selectbox("Seleccionar Mes:", list(meses_dict.values()), index=datetime.now().month-1)
    ano_sel = col_f2.selectbox("Seleccionar Año:", [2024, 2025, 2026], index=2)
    
    # Filtrar datos por mes seleccionado
    mes_num = [k for k, v in meses_dict.items() if v == mes_sel][0]
    ventas_mes = df_ven[(df_ven['Fecha'].dt.month == mes_num) & (df_ven['Fecha'].dt.year == ano_sel)]
    gastos_mes = df_ops[(pd.to_datetime(df_ops['Fecha']).dt.month == mes_num) & (pd.to_datetime(df_ops['Fecha']).dt.year == ano_sel)]
    
    utilidad_bruta = ventas_mes['Ganancia'].sum()
    costo_operativo = gastos_mes['Monto'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Ventas {mes_sel}", f"${utilidad_bruta:,.2f}")
    m2.metric(f"Gastos {mes_sel}", f"- ${costo_operativo:,.2f}")
    m3.metric("Utilidad Neta", f"${utilidad_bruta - costo_operativo:,.2f}")
    
    st.divider()
    st.subheader("Situación Actual de Mercancía")
    inv_valor = (df_inv['Stock'] * df_inv['Costo']).sum()
    st.write(f"💼 **Capital invertido en stock hoy:** ${inv_valor:,.2f}")

with tab5:
    st.subheader("💾 Guardar y Exportar")
    st.download_button(f"📥 Descargar Reporte de Tulip S.A.", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name=f"Tulip_SA_{datetime.now().strftime('%d_%m_%Y')}.xlsx", use_container_width=True)
