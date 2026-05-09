import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime
import sqlite3
import openpyxl

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Tulip S.A. ERP",
    page_icon="🌷",
    layout="wide"
)

# =========================================================
# ESTILOS
# =========================================================

st.markdown("""
<style>
.main {background-color: #0E1117;}
h1,h2,h3{color:white;}
.stMetric{background-color:#161B22;padding:15px;border-radius:12px;border:1px solid #30363D;}
div.stButton > button{background:#FF4B91;color:white;border-radius:10px;padding:10px;font-weight:bold;}
div.stButton > button:hover{background:#FF2E7A;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# BASE DE DATOS
# =========================================================

conn = sqlite3.connect("tulip_erp.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario (
id INTEGER PRIMARY KEY AUTOINCREMENT,
producto TEXT UNIQUE,
categoria TEXT,
stock INTEGER,
costo REAL,
venta REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas (
id INTEGER PRIMARY KEY AUTOINCREMENT,
fecha TEXT,
producto TEXT,
cantidad INTEGER,
costo_ref REAL,
venta_ref REAL,
ganancia REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
fecha TEXT,
concepto TEXT,
monto REAL
)
""")

conn.commit()

# =========================================================
# FUNCIONES
# =========================================================

def cargar():
    return (
        pd.read_sql("SELECT * FROM inventario", conn),
        pd.read_sql("SELECT * FROM ventas", conn),
        pd.read_sql("SELECT * FROM gastos", conn)
    )

def guardar_producto(p,c,s,co,v):
    cursor.execute("SELECT * FROM inventario WHERE producto=?", (p,))
    ex = cursor.fetchone()

    if ex:
        nuevo = ex[3] + s
        cursor.execute("""
        UPDATE inventario SET categoria=?, stock=?, costo=?, venta=?
        WHERE producto=?
        """,(c,nuevo,co,v,p))
    else:
        cursor.execute("""
        INSERT INTO inventario VALUES (NULL,?,?,?,?,?)
        """,(p,c,s,co,v))

    conn.commit()

def venta(fecha,producto,cant):

    cursor.execute("SELECT * FROM inventario WHERE producto=?",(producto,))
    d = cursor.fetchone()

    if not d:
        return False,"No existe"

    _,_,_,stock,costo,venta = d

    if cant>stock:
        return False,"Stock insuficiente"

    nuevo = stock-cant
    gan = cant*(venta-costo)

    cursor.execute("UPDATE inventario SET stock=? WHERE producto=?",(nuevo,producto))

    cursor.execute("""
    INSERT INTO ventas VALUES (NULL,?,?,?,?,?,?)
    """,(fecha,producto,cant,costo,venta,gan))

    conn.commit()
    return True,"OK"

def gasto(fecha,concepto,monto):
    cursor.execute("""
    INSERT INTO gastos VALUES (NULL,?,?,?)
    """,(fecha,concepto,monto))
    conn.commit()

# =========================================================
# DATOS
# =========================================================

inv, ven, gas = cargar()

# =========================================================
# IMPORTAR EXCEL
# =========================================================

st.sidebar.header("📂 Importar Excel")
file = st.sidebar.file_uploader("Subir", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.columns = [c.lower() for c in df.columns]

    for _,r in df.iterrows():
        guardar_producto(
            str(r.get("producto","")).title(),
            str(r.get("categoria","")),
            int(r.get("stock",0)),
            float(r.get("costo",0)),
            float(r.get("venta",0))
        )

    st.sidebar.success("Importado")

# =========================================================
# TÍTULO
# =========================================================

st.markdown("<h1 style='text-align:center;'>🌷 Tulip ERP</h1>", unsafe_allow_html=True)

inv, ven, gas = cargar()

# =========================================================
# TABS
# =========================================================

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
"📦 Inventario",
"🛒 Ventas",
"💸 Gastos",
"📑 Balance",
"📈 Dashboard",
"💾 Exportar"
])

# =========================================================
# INVENTARIO
# =========================================================

with tab1:

    st.subheader("Inventario")

    with st.form("f"):

        modo = st.radio("Modo",["Existente","Nuevo"],horizontal=True)

        prod=""
        c0=v0=co0=0.0

        if modo=="Existente" and not inv.empty:
            prod=st.selectbox("Producto",inv["producto"])
            d=inv[inv["producto"]==prod].iloc[0]
            c0=d["categoria"]
            co0=d["costo"]
            v0=d["venta"]

        else:
            prod=st.text_input("Producto")

        cat=st.text_input("Categoria",value=c0)

        col1,col2,col3=st.columns(3)

        with col1:
            stock=st.number_input("Stock",0)

        with col2:
            costo=st.number_input("Costo",value=co0)

        with col3:
            venta=st.number_input("Venta",value=v0)

        if st.form_submit_button("Guardar"):
            guardar_producto(prod,cat,stock,costo,venta)
            st.rerun()

    st.dataframe(inv)

    st.subheader("➖ Descontar")

    if not inv.empty:

        p=st.selectbox("Producto",inv["producto"],key="x")
        s=int(inv[inv["producto"]==p]["stock"].values[0])

        st.info(f"Stock {s}")

        c=st.number_input("Cantidad",1)

        if st.button("Quitar"):

            if c<=s:
                cursor.execute("UPDATE inventario SET stock=? WHERE producto=?",(s-c,p))
                conn.commit()
                st.rerun()

# =========================================================
# VENTAS
# =========================================================

with tab2:

    st.subheader("Ventas")

    if not inv.empty:

        with st.form("v"):

            p=st.selectbox("Producto",inv["producto"])
            c=st.number_input("Cantidad",1)
            f=st.date_input("Fecha",datetime.now())

            if st.form_submit_button("Vender"):
                ok,msg=venta(str(f),p,c)
                st.success(msg) if ok else st.error(msg)
                if ok: st.rerun()

    st.dataframe(ven)

# =========================================================
# GASTOS
# =========================================================

with tab3:

    st.subheader("Gastos")

    with st.form("g"):

        c=st.text_input("Concepto")
        m=st.number_input("Monto",0.0)
        f=st.date_input("Fecha",datetime.now())

        if st.form_submit_button("Guardar"):
            gasto(str(f),c,m)
            st.rerun()

    st.dataframe(gas)

# =========================================================
# BALANCE
# =========================================================

with tab4:

    st.subheader("Balance")

    st.metric("Ventas",ven["ganancia"].sum() if not ven.empty else 0)
    st.metric("Gastos",gas["monto"].sum() if not gas.empty else 0)

# =========================================================
# DASHBOARD
# =========================================================

with tab5:

    st.subheader("Dashboard")

    if not ven.empty:
        fig=px.bar(ven.groupby("producto")["ganancia"].sum().reset_index(),
        x="producto",y="ganancia")
        st.plotly_chart(fig)

# =========================================================
# EXPORTAR
# =========================================================

with tab6:

    st.subheader("Exportar")

    output=BytesIO()

    with pd.ExcelWriter(output,engine="xlsxwriter") as w:
        inv.to_excel(w,index=False,sheet_name="Inv")
        ven.to_excel(w,index=False,sheet_name="Ven")
        gas.to_excel(w,index=False,sheet_name="Gas")

    st.download_button("Descargar",output.getvalue(),"erp.xlsx")
