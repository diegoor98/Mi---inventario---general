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
        # Carga por posición para máxima compatibilidad
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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📦 Stock", "🛒 Ventas", "💸 Gastos", "📑 Balance", "📈 Dashboard", "💾 Guardar"])

# --- STOCK MEJORADO ---
with tab1:
    st.subheader("Gestión de Inventario 🌷")
    # Buscador de productos existentes
    lista_nombres = sorted(list(df_inv['Producto'].unique())) if not df_inv.empty else []
    opciones = ["--- Nuevo Producto ---"] + lista_nombres
    sel = st.selectbox("Selecciona para editar o añadir stock:", opciones)
    
    if sel != "--- Nuevo Producto ---":
        f = df_inv[df_inv['Producto'] == sel].iloc[0]
        d_n, d_c, d_s, d_co, d_v = sel, f['Categoria'], int(f['Stock']), float(f['Costo']), float(f['Venta'])
    else:
        d_n, d_c, d_s, d_co, d_v = "", "", 0, 0.0, 0.0

    with st.form("form_stock_final", clear_on_submit=False):
        col_f1, col_f2 = st.columns(2)
        n_f = col_f1.text_input("Nombre del Producto", value=d_n).capitalize()
        c_f = col_f2.text_input("Categoría", value=d_c).capitalize()
        
        col_f3, col_f4, col_f5 = st.columns(3)
        # Mostramos el stock actual y pedimos cuánto añadir
        s_actual = col_f3.number_input("Stock actual", value=d_s, disabled=True)
        s_nuevo = col_f3.number_input("SUMAR cantidad", min_value=0, step=1)
        cos_f = col_f4.number_input("Costo Unitario", value=d_co, format="%.2f")
        ven_f = col_f5.number_input("Precio Venta", value=d_v, format="%.2f")
        
        if st.form_submit_button("✅ GUARDAR CAMBIOS"):
            if n_f:
                total_unidades = d_s + s_nuevo
                if n_f in df_inv['Producto'].values:
                    df_inv.loc[df_inv['Producto'] == n_f, ['Categoria', 'Stock', 'Costo', 'Venta']] = [c_f, total_unidades, cos_f, ven_f]
                else:
                    nueva_fila = pd.DataFrame([{"Producto": n_f, "Categoria": c_f, "Stock": s_nuevo, "Costo": cos_f, "Venta": ven_f}])
                    df_inv = pd.concat([df_inv, nueva_fila], ignore_index=True)
                
                st.success(f"📦 ¡{n_f} guardado con éxito! Nuevo total: {total_unidades}")
                st.rerun() # Esto hace que la tabla se actualice al momento
            else:
                st.error("Escribe un nombre para el producto.")

    st.write("### Listado General")
    st.dataframe(df_inv, use_container_width=True)

# --- VENTAS ---
with tab2:
    st.subheader("Registrar Ventas")
    if not df_inv.empty:
        with st.form("v_final"):
            p_v = st.selectbox("Elegir Producto", df_inv['Producto'].unique())
            c_v = st.number_input("Cantidad", min_value=1)
            f_v = st.date_input("Fecha", datetime.now())
            if st.form_submit_button("🛒 Procesar Venta"):
                idx = df_inv[df_inv['Producto'] == p_v].index
                if df_inv.at[idx[0], 'Stock'] >= c_v:
                    gan = c_v * (df_inv.at[idx[0], 'Venta'] - df_inv.at[idx[0], 'Costo'])
                    nueva_v = pd.DataFrame([{"Fecha": pd.to_datetime(f_v), "Producto": p_v, "Cantidad": c_v, "Costo_Ref": df_inv.at[idx[0], 'Costo'], "Venta_Ref": df_inv.at[idx[0], 'Venta'], "Ganancia": gan}])
                    df_ven = pd.concat([df_ven, nueva_v], ignore_index=True)
                    df_inv.at[idx[0], 'Stock'] -= c_v
                    st.success("✅ Venta realizada")
                    st.rerun()
                else: st.error("Stock insuficiente")
    st.dataframe(df_ven.sort_values(by="Fecha", ascending=False) if not df_ven.empty else df_ven)

# --- GASTOS ---
with tab3:
    st.subheader("Gastos Operativos")
    with st.form("g_final"):
        concepto = st.text_input("Concepto"); monto = st.number_input("Monto"); f_g = st.date_input("Fecha", datetime.now())
        if st.form_submit_button("Registrar Gasto"):
            df_ops = pd.concat([df_ops, pd.DataFrame([{"Fecha": pd.to_datetime(f_g), "Concepto": concepto, "Monto": monto}])], ignore_index=True)
            st.rerun()
    st.dataframe(df_ops.sort_values(by="Fecha", ascending=False) if not df_ops.empty else df_ops)

# --- BALANCE Y DASHBOARD (FILTROS UNIFICADOS) ---
meses = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
anos_list = list(range(2024, datetime.now().year + 5))

with tab4:
    st.header("📊 Balance Contable")
    filtro = st.radio("Ver por:", ["Mes", "Año"], horizontal=True, key="f_bal")
    c1, c2 = st.columns(2)
    m_s = c1.selectbox("Mes:", list(meses.values()), index=datetime.now().month-1, key="m_bal")
    a_s = c2.selectbox("Año:", anos_list, index=anos_list.index(datetime.now().year), key="a_bal")
    
    m_n = [k for k, v in meses.items() if v == m_s][0]
    
    # Filtrado seguro
    df_ven['Fecha'] = pd.to_datetime(df_ven['Fecha'])
    if filtro == "Mes":
        v_f = df_ven[(df_ven['Fecha'].dt.month == m_n) & (df_ven['Fecha'].dt.year == a_s)]
        o_f = df_ops[(pd.to_datetime(df_ops['Fecha']).dt.month == m_n) & (pd.to_datetime(df_ops['Fecha']).dt.year == a_s)]
    else:
        v_f = df_ven[df_ven['Fecha'].dt.year == a_s]
        o_f = df_ops[pd.to_datetime(df_ops['Fecha']).dt.year == a_s]
        
    bruta = v_f['Ganancia'].sum(); gastos = o_f['Monto'].sum(); neta = bruta - gastos
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingresos", f"${bruta:,.2f}")
    m2.metric("Gastos", f"- ${gastos:,.2f}")
    m3.metric("Utilidad Neta", f"${neta:,.2f}")

with tab5:
    st.header("📈 Dashboard Visual")
    if not v_f.empty:
        g1, g2 = st.columns(2)
        fig1 = px.bar(v_f.groupby('Producto')['Ganancia'].sum().reset_index(), x='Producto', y='Ganancia', color='Producto', template="plotly_dark", title="Ganancia por Producto")
        g1.plotly_chart(fig1, use_container_width=True)
        
        if not o_f.empty:
            fig2 = px.pie(o_f, values='Monto', names='Concepto', hole=0.5, template="plotly_dark", title="Distribución de Gastos")
            g2.plotly_chart(fig2, use_container_width=True)
            
        fig3 = px.treemap(v_f, path=['Producto'], values='Ganancia', template="plotly_dark", title="Mapa de Ventas")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No hay datos para mostrar gráficas en este periodo.")

with tab6:
    st.download_button("📥 Descargar Excel Final", data=convertir_a_excel(df_inv, df_ven, df_ops), file_name=f"Tulip_SA_{datetime.now().strftime('%d_%m')}.xlsx", use_container_width=True)
