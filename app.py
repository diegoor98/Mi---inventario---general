import streamlit as st
import pandas as pd
import numpy_financial as npf
from io import BytesIO
from datetime import datetime

# Configuración Pro para Celular
st.set_page_config(page_title="ERP Negocio Pro", layout="wide", initial_sidebar_state="collapsed")

# Función para exportar a Excel con varias pestañas
def convertir_a_excel(df_inv, df_ven, df_ops):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_inv.to_excel(writer, index=False, sheet_name='Inventario')
        df_ven.to_excel(writer, index=False, sheet_name='Ventas')
        df_ops.to_excel(writer, index=False, sheet_name='Costos_Operativos')
    return output.getvalue()

st.title("💼 Gestión Empresarial Ultra-Pro")
st.write("Sube tu archivo para continuar o rellena datos nuevos.")

# --- 1. CARGA DE DATOS ---
archivo_subido = st.file_uploader("📂 Cargar Base de Datos (Excel)", type=["xlsx"])

if archivo_subido:
    try:
        df_inv = pd.read_excel(archivo_subido, sheet_name='Inventario')
        df_ven = pd.read_excel(archivo_subido, sheet_name='Ventas')
        df_ops = pd.read_excel(archivo_subido, sheet_name='Costos_Operativos')
    except:
        df_inv = pd.read_excel(archivo_subido)
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Ganancia"])
        df_ops = pd.DataFrame(columns=["Concepto", "Monto"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Ganancia"])
    df_ops = pd.DataFrame(columns=["Concepto", "Monto"])

# --- 2. MENU PRINCIPAL POR PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Stock", "🛒 Ventas", "💸 Gastos Ops", "📊 Balance", "💾 Guardar"])

# PESTAÑA 1: INVENTARIO
with tab1:
    st.subheader("Control de Existencias")
    with st.expander("➕ Añadir / Editar Producto"):
        with st.form("add_form"):
            n = st.text_input("Nombre").capitalize()
            c = st.text_input("Categoría").capitalize()
            can = st.number_input("Cantidad", min_value=0)
            cos = st.number_input("Costo Unitario", min_value=0.0)
            ven = st.number_input("Precio Venta", min_value=0.0)
            if st.form_submit_button("Guardar Producto"):
                if n in df_inv['Producto'].values:
                    df_inv.loc[df_inv['Producto'] == n, ['Stock', 'Costo', 'Venta']] = [can, cos, ven]
                else:
                    nuevo = pd.DataFrame([{"Producto": n, "Categoria": c, "Stock": can, "Costo": cos, "Venta": ven}])
                    df_inv = pd.concat([df_inv, nuevo], ignore_index=True)
                st.success("Actualizado")

    st.write("### Inventario Actual")
    st.dataframe(df_inv, use_container_width=True)
    inversion_stock = (df_inv['Stock'] * df_inv['Costo']).sum()
    st.metric("Costo Total de Inventario", f"${inversion_stock:,.2f}")

# PESTAÑA 2: VENTAS
with tab2:
    st.subheader("Registrar Venta")
    if not df_inv.empty:
        prod_v = st.selectbox("Seleccionar Producto", df_inv['Producto'].unique())
        cant_v = st.number_input("Cantidad Vendida", min_value=1)
        if st.button("🚀 Procesar Venta"):
            idx = df_inv[df_inv['Producto'] == prod_v].index[0]
            if df_inv.at[idx, 'Stock'] >= cant_v:
                df_inv.at[idx, 'Stock'] -= cant_v
                gan_v = cant_v * (df_inv.at[idx, 'Venta'] - df_inv.at[idx, 'Costo'])
                nueva_v = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%y %H:%M"), "Producto": prod_v, "Cantidad": cant_v, "Ganancia": gan_v}])
                df_ven = pd.concat([df_ven, nueva_v], ignore_index=True)
                st.success(f"Venta Exitosa. Ganancia: ${gan_v:,.2f}")
            else:
                st.error("No hay suficiente Stock")

# PESTAÑA 3: GASTOS OPERATIVOS
with tab3:
    st.subheader("Gastos Mensuales (Alquiler, Luz, etc.)")
    with st.form("ops_form"):
        con_op = st.text_input("Concepto (Ej: Alquiler)")
        mon_op = st.number_input("Monto", min_value=0.0)
        if st.form_submit_button("Registrar Gasto"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Concepto": con_op, "Monto": mon_op}])], ignore_index=True)
            st.success("Gasto añadido")
    st.dataframe(df_ops, use_container_width=True)

# PESTAÑA 4: BALANCE FINANCIERO (VAN/TIR)
with tab4:
    st.header("📊 Balance y Rentabilidad")
    
    ganancia_ventas = df_ven['Ganancia'].sum() if not df_ven.empty else 0
    gastos_totales = df_ops['Monto'].sum() if not df_ops.empty else 0
    utilidad_neta = ganancia_ventas - gastos_totales
    inv_stock = (df_inv['Stock'] * df_inv['Costo']).sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Ganancia por Ventas", f"${ganancia_ventas:,.2f}")
    c2.metric("Costos Operativos", f"- ${gastos_totales:,.2f}")
    c3.metric("Utilidad Neta", f"${utilidad_neta:,.2f}")

    st.divider()
    
    col_fin1, col_fin2 = st.columns(2)
    with col_fin1:
        st.write("### Indicadores")
        renta = (utilidad_neta / inv_stock * 100) if inv_stock > 0 else 0
        st.write(f"**Rentabilidad:** {renta:.2f}%")
        
        if inv_stock > 0:
            flujos = [-inv_stock] + [utilidad_neta] * 12
            tir = npf.irr(flujos)
            van = npf.npv(0.12/12, flujos)
            st.write(f"**TIR:** {tir*100:.2f}%" if not pd.isna(tir) else "**TIR:** calculando...")
            st.write(f"**VAN:** ${van:,.2f}")
    
    with col_fin2:
        st.write("### Inversión")
        st.write(f"**Costo de Stock Actual:** ${inv_stock:,.2f}")

# PESTAÑA 5: GUARDAR
with tab5:
    st.subheader("💾 Guardar y Descargar")
    st.info("Descarga tu archivo Excel para no perder los datos del día.")
    excel_final = convertir_a_excel(df_inv, df_ven, df_ops)
    st.download_button(
        label="📥 DESCARGAR EXCEL ACTUALIZADO",
        data=excel_final,
        file_name=f"Balance_{datetime.now().strftime('%d_%m_%y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
