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

# --- PESTAÑA 1: STOCK (NUEVO MOTOR DE SUMA) ---
with tab1:
    st.subheader("Gestión de Inventario 🌷")
    
    opciones = ["--- Nuevo Producto ---"] + sorted(list(df_inv['Producto'].unique())) if not df_inv.empty else ["--- Nuevo Producto ---"]
    sel = st.selectbox("Selecciona producto:", opciones)
    
    # Extraer valores actuales
    if sel != "--- Nuevo Producto ---":
        f_idx = df_inv[df_inv['Producto'] == sel].index[0]
        v_cat = df_inv.at[f_idx, 'Categoria']
        v_stock_actual = int(df_inv.at[f_idx, 'Stock'])
        v_costo = float(df_inv.at[f_idx, 'Costo'])
        v_venta = float(df_inv.at[f_idx, 'Venta'])
    else:
        f_idx, v_cat, v_stock_actual, v_costo, v_venta = None, "", 0, 0.0, 0.0

    # Campos de entrada
    nombre_i = st.text_input("Nombre del Producto", value=sel if sel != "--- Nuevo Producto ---" else "").capitalize()
    cat_i = st.text_input("Categoría", value=v_cat).capitalize()
    
    col_a, col_b = st.columns(2)
    st.info(f"Stock actual: {v_stock_actual}")
    sumar_i = col_a.number_input("SUMAR cantidad nueva:", min_value=0, step=1, value=0)
    
    col_c, col_d = st.columns(2)
    costo_i = col_c.number_input("Costo Unitario:", value=v_costo, format="%.2f")
    venta_i = col_d.number_input("Precio Venta:", value=v_venta, format="%.2f")
    
    if st.button("✅ GUARDAR CAMBIOS EN TULIP S.A."):
        if nombre_i:
            nuevo_total = v_stock_actual + sumar_i
            if sel != "--- Nuevo Producto ---":
                # Actualizar existente
                df_inv.loc[df_inv['Producto'] == sel, ['Producto', 'Categoria', 'Stock', 'Costo', 'Venta']] = [nombre_i, cat_i, nuevo_total, costo_i, venta_i]
            else:
                # Crear nuevo
                nueva_f = pd.DataFrame([{"Producto": nombre_i, "Categoria": cat_i, "Stock": sumar_i, "Costo": costo_i, "Venta": venta_i}])
                df_inv = pd.concat([df_inv, nueva_f], ignore_index=True)
            
            st.success(f"📦 ¡Actualizado! {nombre_i} ahora tiene {nuevo_total} unidades.")
            st.rerun()
        else:
            st.error("Escribe un nombre.")

    st.write("---")
    st.dataframe(df_inv, use_container_width=True)

# [El resto de las pestañas se mantienen igual]
# PESTAÑA 6: GUARDAR
with tab6:
    st.subheader("💾 Guardar Datos")
    st.info("No olvides descargar tu Excel antes de salir.")
    excel_final = convertir_a_excel(df_inv, df_ven, df_ops)
    st.download_button("📥 Descargar Excel", data=excel_final, file_name=f"Tulip_SA_{datetime.now().strftime('%d_%m')}.xlsx", use_container_width=True)
