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
        # Al guardar, forzamos nombres estándar para que siempre funcione
        df_inv.to_excel(writer, index=False, sheet_name='Inventario')
        df_ven.to_excel(writer, index=False, sheet_name='Ventas')
        df_ops.to_excel(writer, index=False, sheet_name='Gastos')
    return output.getvalue()

st.markdown("<h1 style='text-align: center;'>🌷 Tulip S.A.</h1>", unsafe_allow_html=True)

# --- CARGA DE DATOS INTELIGENTE (POR POSICIÓN) ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos Tulip S.A.", type=["xlsx"])

if archivo_subido:
    try:
        excel_file = pd.ExcelFile(archivo_subido)
        hojas = excel_file.sheet_names
        
        # Carga Hoja 1: Stock
        df_inv = pd.read_excel(archivo_subido, sheet_name=0)
        
        # Carga Hoja 2: Ventas
        if len(hojas) > 1:
            df_ven = pd.read_excel(archivo_subido, sheet_name=1)
            df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'], errors='coerce')
        else:
            df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
            
        # Carga Hoja 3: Gastos
        if len(hojas) > 2:
            df_ops = pd.read_excel(archivo_subido, sheet_name=2)
        else:
            df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
            
        st.success("✅ Datos sincronizados correctamente.")
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Costo_Ref", "Venta_Ref", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Fecha", "Concepto", "Monto"])

# --- MENU POR PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos", "📊 Balance Mensual", "💾 Guardar"])

with tab1:
    st.subheader("Gestión de Inventario Permanente 🌷")
    with st.expander("➕ Añadir / Editar Producto"):
        opciones = ["Nuevo"] + list(df_inv['Producto'].unique())
        sel = st.selectbox("Producto:", opciones)
        
        if sel != "Nuevo":
            d = df_inv[df_inv['Producto'] == sel].iloc[0]
            val_n, val_c, val_s, val_co, val_v = sel, d['Categoria'], int(d['Stock']), float(d['Costo']), float(d['Venta'])
        else:
            val_n, val_c, val_s, val_co, val_v = "", "", 0, 0.0, 0.0

        with st.form("f_inv"):
            n = st.text_input("Nombre", value=val_n).capitalize()
            c = st.text_input("Categoría", value=val_c).capitalize()
            can = st.number_input("Stock", value=val_s, min_value=0)
            cos = st.number_input("Costo", value=val_co, format="%.2f")
            ven = st.number_input("Venta", value=val_v, format="%.2f")
            if st.form_submit_button("Guardar Cambios"):
                if n in df_inv['Producto'].values:
                    df_inv.loc[df_inv['Producto'] == n, ['Categoria', 'Stock', 'Costo', 'Venta']] = [c, can, cos, ven]
                else:
                    df_inv = pd.concat([df_inv, pd.DataFrame([{"Producto": n, "Categoria": c, "Stock": can, "Costo": cos, "Venta": ven}])], ignore_index=True)
                st.success("Guardado"); st.rerun()
    st.dataframe(df_inv, use_container_width=True)

with tab2:
    st.subheader("Registrar Venta 💰")
    if not df_inv.empty:
        p_v = st.selectbox("Vender:", df_inv['Producto'].unique())
        cant_v = st.number_input("Cantidad:", min_value=1)
        if st.button("Procesar Venta"):
            idx = df_inv[df_inv['Producto'] == p_v].index[0]
            if df_inv.at[idx, 'Stock'] >= cant_v:
                c_m, v_m = df_inv.at[idx, 'Costo'], df_inv.at[idx, 'Venta']
                gan = cant_v * (v_m - c_m)
                df_inv.at[idx, 'Stock'] -= cant_v
                nueva = pd.DataFrame([{"Fecha": datetime.now(), "Producto": p_v, "Cantidad": cant_v, "Costo_Ref": c_m, "Venta_Ref": v_m, "Ganancia": gan}])
                df_ven = pd.concat([df_ven, nueva], ignore_index=True)
                st.balloons(); st.success("Venta Exitosa")
            else: st.error("Stock insuficiente")

with tab3:
    st.subheader("Gastos Tulip S.A. 🏢")
    with st.form("f_gastos"):
        con = st.text_input("Concepto (Ej: Alquiler)"); mon = st.number_input("Monto", min_value=0.0)
        if st.form_submit_button("Registrar"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": datetime.now(), "Concepto": con, "Monto": mon}])], ignore_index=True)
            st.success("Gasto añadido")
    st.dataframe(df_ops, use_container_width=True)

with tab4:
    st.header("📊 Balance Mensual Tulip S.A.")
    meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    col1, col2 = st.columns(2)
    m_sel = col1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1)
    a_sel = col2.selectbox("Año:", [2024, 2025, 2026], index=2)
    
    m_num = [k for k, v in meses.items() if v == m_sel][0]
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    v_mes = df_ven[(df_ven['Fecha'].dt.month == m_num) & (df_ven['Fecha'].dt.year == a_sel)]
    
    u_bruta = v_mes['Ganancia'].sum()
    c_inv = (df_inv['Stock'] * df_inv['Costo']).sum()
    
    st.metric(f"Utilidad Bruta {m_sel}", f"${u_bruta:,.2f}")
    st.metric("Inversión en Stock", f"${c_inv:,.2f}")

with tab5:
    st.subheader("💾 Guardar Datos")
    st.download_button("📥 Descargar Excel Final", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name=f"Tulip_SA_{datetime.now().strftime('%d_%m')}.xlsx", use_container_width=True)
