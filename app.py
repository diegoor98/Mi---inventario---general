import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Mi Inventario", layout="centered")

def convertir_a_excel(df_inv, df_ven):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_inv.to_excel(writer, index=False, sheet_name='Inventario')
        df_ven.to_excel(writer, index=False, sheet_name='Ventas')
    return output.getvalue()

st.title("📱 Mi Negocio en la Web")

archivo_subido = st.file_uploader("📂 Abre tu Excel", type=["xlsx"])

if archivo_subido:
    try:
        df_inv = pd.read_excel(archivo_subido, sheet_name='Inventario')
        df_ven = pd.read_excel(archivo_subido, sheet_name='Ventas')
    except:
        df_inv = pd.read_excel(archivo_subido)
        df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Ganancia"])
else:
    df_inv = pd.DataFrame(columns=["Producto", "Categoria", "Stock", "Costo", "Venta"])
    df_ven = pd.DataFrame(columns=["Fecha", "Producto", "Cantidad", "Ganancia"])

tab1, tab2, tab3, tab4 = st.tabs(["📦 Stock", "➕ Rellenar", "💰 Vender", "📊 Balance"])

with tab1:
    st.subheader("Inventario Actual")
    st.dataframe(df_inv, use_container_width=True)

with tab2:
    st.subheader("Añadir Productos")
    with st.form("form_add"):
        nom = st.text_input("Producto").capitalize()
        cat = st.text_input("Categoría").capitalize()
        can = st.number_input("Cantidad", min_value=1)
        cos = st.number_input("Costo Unitario", min_value=0.0)
        ven = st.number_input("Precio Venta", min_value=0.0)
        if st.form_submit_button("Guardar"):
            if nom in df_inv['Producto'].values:
                df_inv.loc[df_inv['Producto'] == nom, 'Stock'] += can
            else:
                nuevo = pd.DataFrame([{"Producto": nom, "Categoria": cat, "Stock": can, "Costo": cos, "Venta": ven}])
                df_inv = pd.concat([df_inv, nuevo], ignore_index=True)
            st.success("✅ Añadido")

with tab3:
    st.subheader("Registrar Venta")
    if not df_inv.empty:
        prod_v = st.selectbox("¿Qué vendiste?", df_inv['Producto'].tolist())
        cant_v = st.number_input("¿Cuántas?", min_value=1)
        if st.button("Confirmar Venta"):
            idx = df_inv[df_inv['Producto'] == prod_v].index
            if df_inv.at[idx[0], 'Stock'] >= cant_v:
                df_inv.at[idx[0], 'Stock'] -= cant_v
                ganancia = cant_v * (df_inv.at[idx[0], 'Venta'] - df_inv.at[idx[0], 'Costo'])
                nueva_v = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Producto": prod_v, "Cantidad": cant_v, "Ganancia": ganancia}])
                df_ven = pd.concat([df_ven, nueva_v], ignore_index=True)
                st.success(f"💰 Ganancia: ${ganancia:.2f}")
            else: st.error("Sin stock")

with tab4:
    st.subheader("Balance Financiero")
    if not df_ven.empty:
        st.metric("Utilidad Total", f"${df_ven['Ganancia'].sum():.2f}")
        st.metric("Capital en Stock", f"${(df_inv['Stock'] * df_inv['Costo']).sum():.2f}")
        st.dataframe(df_ven, use_container_width=True)

st.divider()
excel_data = convertir_a_excel(df_inv, df_ven)
st.download_button(label="📥 Descargar Excel", data=excel_data, file_name="Inventario_Negocio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
