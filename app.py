import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime
import sqlite3

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Tulip ERP",
    page_icon="🌷",
    layout="wide"
)

# =========================================================
# ESTILOS
# =========================================================

st.markdown("""
<style>
.main{
    background: linear-gradient(135deg,#0E1117 0%,#161B22 100%);
}
h1{color:white;font-weight:800;}
h2,h3,h4{color:#F8FAFC;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# DB
# =========================================================

conn = sqlite3.connect("tulip_erp.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario(
id INTEGER PRIMARY KEY AUTOINCREMENT,
producto TEXT UNIQUE,
categoria TEXT,
stock INTEGER,
costo REAL,
venta REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas(
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
CREATE TABLE IF NOT EXISTS gastos(
id INTEGER PRIMARY KEY AUTOINCREMENT,
fecha TEXT,
concepto TEXT,
monto REAL
)
""")

conn.commit()

# =========================================================
# 🔥 RECUPERAR EXCEL ANTIGUO
# =========================================================

st.sidebar.header("📂 Recuperar ERP antiguo")

archivo_excel = st.sidebar.file_uploader(
    "Sube tu Excel antiguo",
    type=["xlsx"]
)

def importar_excel(file):

    xls = pd.ExcelFile(file)

    if "Inventario" in xls.sheet_names:
        inv = pd.read_excel(xls, "Inventario")

        for _, r in inv.iterrows():
            cursor.execute("""
            INSERT OR REPLACE INTO inventario
            VALUES(
            (SELECT id FROM inventario WHERE producto=?),
            ?,?,?,?,?
            )
            """,(
                r["producto"],
                r["producto"],
                r["categoria"],
                r["stock"],
                r["costo"],
                r["venta"]
            ))

    if "Ventas" in xls.sheet_names:
        ven = pd.read_excel(xls, "Ventas")

        for _, r in ven.iterrows():
            cursor.execute("""
            INSERT INTO ventas VALUES(NULL,?,?,?,?,?,?)
            """,(
                str(r["fecha"]),
                r["producto"],
                r["cantidad"],
                r["costo_ref"],
                r["venta_ref"],
                r["ganancia"]
            ))

    if "Gastos" in xls.sheet_names:
        gas = pd.read_excel(xls, "Gastos")

        for _, r in gas.iterrows():
            cursor.execute("""
            INSERT INTO gastos VALUES(NULL,?,?,?)
            """,(
                str(r["fecha"]),
                r["concepto"],
                r["monto"]
            ))

    conn.commit()

    return True

if archivo_excel:
    if st.sidebar.button("🔄 Restaurar ERP"):
        importar_excel(archivo_excel)
        st.sidebar.success("ERP restaurado correctamente")
        st.rerun()

# =========================================================
# CARGA
# =========================================================

def cargar():
    return (
        pd.read_sql("SELECT * FROM inventario", conn),
        pd.read_sql("SELECT * FROM ventas", conn),
        pd.read_sql("SELECT * FROM gastos", conn)
    )

inv, ven, gas = cargar()

# =========================================================
# GUARDAR PRODUCTO
# =========================================================

def guardar_producto(producto,categoria,stock,costo,venta):

    cursor.execute("SELECT * FROM inventario WHERE producto=?", (producto,))
    existe = cursor.fetchone()

    if existe:
        nuevo_stock = existe[3] + stock
        cursor.execute("""
        UPDATE inventario
        SET categoria=?,stock=?,costo=?,venta=?
        WHERE producto=?
        """,(categoria,nuevo_stock,costo,venta,producto))
    else:
        cursor.execute("""
        INSERT INTO inventario VALUES(NULL,?,?,?,?,?)
        """,(producto,categoria,stock,costo,venta))

    conn.commit()

# =========================================================
# VENTA
# =========================================================

def registrar_venta(fecha,producto,cantidad):

    cursor.execute("SELECT * FROM inventario WHERE producto=?", (producto,))
    d = cursor.fetchone()

    if not d:
        return False,"No existe"

    _,_,_,stock,costo,venta = d

    if cantidad > stock:
        return False,"Stock insuficiente"

    nuevo_stock = stock - cantidad
    ganancia = cantidad * (venta - costo)

    cursor.execute("UPDATE inventario SET stock=? WHERE producto=?",
                   (nuevo_stock,producto))

    cursor.execute("""
    INSERT INTO ventas VALUES(NULL,?,?,?,?,?,?)
    """,(fecha,producto,cantidad,costo,venta,ganancia))

    conn.commit()

    return True,"OK"

# =========================================================
# GASTO
# =========================================================

def registrar_gasto(fecha,concepto,monto):
    cursor.execute("INSERT INTO gastos VALUES(NULL,?,?,?)",
                   (fecha,concepto,monto))
    conn.commit()

# =========================================================
# UI
# =========================================================

st.title("🌷 Tulip ERP")

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
"Inventario","Ventas","Gastos","Balance","Dashboard","Exportar"
])

# =========================================================
# INVENTARIO
# =========================================================

with tab1:

    st.subheader("Inventario")

    with st.form("inv"):

        producto = st.text_input("Producto")
        categoria = st.text_input("Categoria")
        stock = st.number_input("Stock",0)
        costo = st.number_input("Costo",0.0)
        venta = st.number_input("Venta",0.0)

        if st.form_submit_button("Guardar"):
            guardar_producto(producto,categoria,stock,costo,venta)
            st.rerun()

    st.dataframe(inv)

# =========================================================
# VENTAS
# =========================================================

with tab2:

    st.subheader("Ventas")

    if not inv.empty:

        producto = st.selectbox("Producto",inv["producto"])
        cantidad = st.number_input("Cantidad",1)
        fecha = st.date_input("Fecha",datetime.now())

        if st.button("Vender"):

            ok,msg = registrar_venta(str(fecha),producto,cantidad)

            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.dataframe(ven)

# =========================================================
# GASTOS
# =========================================================

with tab3:

    st.subheader("Gastos")

    concepto = st.text_input("Concepto")
    monto = st.number_input("Monto",0.0)
    fecha = st.date_input("Fecha gasto",datetime.now())

    if st.button("Guardar gasto"):
        registrar_gasto(str(fecha),concepto,monto)
        st.rerun()

    st.dataframe(gas)

# =========================================================
# BALANCE
# =========================================================

with tab4:

    st.subheader("Balance")

    ventas_total = ven["venta_ref"].sum() if not ven.empty else 0
    ganancias = ven["ganancia"].sum() if not ven.empty else 0
    gastos_total = gas["monto"].sum() if not gas.empty else 0

    utilidad = ganancias - gastos_total

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Ventas",ventas_total)
    c2.metric("Ganancia",ganancias)
    c3.metric("Gastos",gastos_total)
    c4.metric("Utilidad",utilidad)

# =========================================================
# DASHBOARD
# =========================================================

with tab5:

    if not ven.empty:

        fig = px.bar(ven.groupby("producto")["ganancia"].sum().reset_index(),
                     x="producto",y="ganancia")

        st.plotly_chart(fig,use_container_width=True)

# =========================================================
# EXPORTAR
# =========================================================

with tab6:

    output = BytesIO()

    with pd.ExcelWriter(output,engine="xlsxwriter") as writer:
        inv.to_excel(writer,"Inventario",index=False)
        ven.to_excel(writer,"Ventas",index=False)
        gas.to_excel(writer,"Gastos",index=False)

    st.download_button(
        "Descargar ERP",
        output.getvalue(),
        "tulip_erp.xlsx"
    )
