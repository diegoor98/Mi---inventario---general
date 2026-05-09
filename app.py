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
# ESTILOS PREMIUM
# =========================================================

st.markdown("""
<style>

/* =======================================================
FONDO GENERAL
======================================================= */

.main{
    background: linear-gradient(
        135deg,
        #0E1117 0%,
        #161B22 100%
    );
}

/* =======================================================
TEXTOS
======================================================= */

h1{
    color:#FFFFFF;
    font-weight:800;
}

h2,h3,h4{
    color:#F8FAFC;
}

/* =======================================================
METRICS
======================================================= */

[data-testid="stMetric"]{

    background: linear-gradient(
        145deg,
        #1E293B,
        #111827
    );

    border:1px solid #334155;

    padding:20px;

    border-radius:18px;

    box-shadow:
    0 4px 20px rgba(0,0,0,0.35);

    transition:0.3s;
}

[data-testid="stMetric"]:hover{

    transform:translateY(-3px);

    border:1px solid #FF4B91;
}

/* =======================================================
BOTONES
======================================================= */

div.stButton > button{

    background: linear-gradient(
        90deg,
        #FF4B91,
        #FF2E7A
    );

    color:white;

    border:none;

    border-radius:12px;

    padding:10px 18px;

    font-weight:700;

    transition:0.25s;

    box-shadow:
    0 4px 12px rgba(255,75,145,0.3);
}

div.stButton > button:hover{

    transform:scale(1.04);

    background: linear-gradient(
        90deg,
        #7C3AED,
        #9333EA
    );
}

/* =======================================================
INPUTS
======================================================= */

.stTextInput input,
.stNumberInput input,
.stDateInput input{

    background-color:#111827;

    color:white;

    border:1px solid #334155;

    border-radius:10px;
}

/* =======================================================
SELECTBOX
======================================================= */

.stSelectbox div[data-baseweb="select"]{

    background-color:#111827;

    border-radius:10px;

    border:1px solid #334155;
}

/* =======================================================
TABS
======================================================= */

button[data-baseweb="tab"]{

    background:#111827;

    color:#CBD5E1;

    border-radius:12px;

    margin-right:5px;

    padding:10px 20px;

    transition:0.2s;
}

button[data-baseweb="tab"]:hover{

    background:#1E293B;

    color:white;
}

button[aria-selected="true"]{

    background: linear-gradient(
        90deg,
        #EC4899,
        #8B5CF6
    ) !important;

    color:white !important;
}

/* =======================================================
DATAFRAMES
======================================================= */

[data-testid="stDataFrame"]{

    border:1px solid #334155;

    border-radius:15px;

    overflow:hidden;
}

/* =======================================================
SIDEBAR
======================================================= */

section[data-testid="stSidebar"]{

    background: linear-gradient(
        180deg,
        #111827,
        #0F172A
    );
}

/* =======================================================
SUCCESS
======================================================= */

.stSuccess{

    background-color:#052E16;

    border:1px solid #22C55E;

    color:#DCFCE7;

    border-radius:12px;
}

/* =======================================================
ERROR
======================================================= */

.stError{

    background-color:#450A0A;

    border:1px solid #EF4444;

    color:#FEE2E2;

    border-radius:12px;
}

/* =======================================================
WARNING
======================================================= */

.stWarning{

    background-color:#451A03;

    border:1px solid #F59E0B;

    color:#FEF3C7;

    border-radius:12px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "tulip_erp.db",
    check_same_thread=False
)

cursor = conn.cursor()

# =========================================================
# TABLAS
# =========================================================

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
# FUNCIONES
# =========================================================

def cargar():

    return (
        pd.read_sql(
            "SELECT * FROM inventario",
            conn
        ),

        pd.read_sql(
            "SELECT * FROM ventas",
            conn
        ),

        pd.read_sql(
            "SELECT * FROM gastos",
            conn
        )
    )

# =========================================================

def guardar_producto(
    producto,
    categoria,
    stock,
    costo,
    venta
):

    cursor.execute(
        "SELECT * FROM inventario WHERE producto=?",
        (producto,)
    )

    existe = cursor.fetchone()

    if existe:

        nuevo_stock = existe[3] + stock

        cursor.execute("""
        UPDATE inventario
        SET categoria=?,
            stock=?,
            costo=?,
            venta=?
        WHERE producto=?
        """,(
            categoria,
            nuevo_stock,
            costo,
            venta,
            producto
        ))

    else:

        cursor.execute("""
        INSERT INTO inventario
        VALUES(NULL,?,?,?,?,?)
        """,(
            producto,
            categoria,
            stock,
            costo,
            venta
        ))

    conn.commit()

# =========================================================

def registrar_venta(
    fecha,
    producto,
    cantidad
):

    cursor.execute(
        "SELECT * FROM inventario WHERE producto=?",
        (producto,)
    )

    d = cursor.fetchone()

    if not d:
        return False, "Producto no existe"

    _,_,_,stock,costo,venta = d

    if cantidad > stock:
        return False, f"Stock insuficiente ({stock})"

    nuevo_stock = stock - cantidad

    ganancia = cantidad * (
        venta - costo
    )

    cursor.execute("""
    UPDATE inventario
    SET stock=?
    WHERE producto=?
    """,(
        nuevo_stock,
        producto
    ))

    cursor.execute("""
    INSERT INTO ventas
    VALUES(NULL,?,?,?,?,?,?)
    """,(
        fecha,
        producto,
        cantidad,
        costo,
        venta,
        ganancia
    ))

    conn.commit()

    return True, "Venta registrada"

# =========================================================

def registrar_gasto(
    fecha,
    concepto,
    monto
):

    cursor.execute("""
    INSERT INTO gastos
    VALUES(NULL,?,?,?)
    """,(
        fecha,
        concepto,
        monto
    ))

    conn.commit()

# =========================================================

def eliminar_producto(producto):

    cursor.execute(
        "DELETE FROM inventario WHERE producto=?",
        (producto,)
    )

    conn.commit()

# =========================================================
# DATOS
# =========================================================

inv, ven, gas = cargar()

# =========================================================
# TITULO
# =========================================================

st.markdown("""
<h1 style='text-align:center;'>
🌷 Tulip ERP
</h1>
""", unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
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

    st.subheader("📦 Inventario")

    modo = st.radio(
        "Modo",
        ["Existente","Nuevo"],
        horizontal=True
    )

    with st.form("inventario_form"):

        producto = ""
        categoria0 = ""
        costo0 = 0.0
        venta0 = 0.0

        if modo == "Existente" and not inv.empty:

            producto = st.selectbox(
                "Producto",
                inv["producto"]
            )

            fila = inv[
                inv["producto"] == producto
            ].iloc[0]

            categoria0 = fila["categoria"]
            costo0 = fila["costo"]
            venta0 = fila["venta"]

        else:

            producto = st.text_input(
                "Nuevo Producto"
            )

        categoria = st.text_input(
            "Categoria",
            value=categoria0
        )

        c1,c2,c3 = st.columns(3)

        with c1:
            stock = st.number_input(
                "Stock",
                min_value=0
            )

        with c2:
            costo = st.number_input(
                "Costo",
                min_value=0.0,
                value=float(costo0)
            )

        with c3:
            venta = st.number_input(
                "Venta",
                min_value=0.0,
                value=float(venta0)
            )

        guardar = st.form_submit_button(
            "Guardar"
        )

        if guardar:

            guardar_producto(
                producto.title(),
                categoria,
                stock,
                costo,
                venta
            )

            st.success(
                "Producto guardado"
            )

            st.rerun()

    st.dataframe(
        inv,
        use_container_width=True
    )

# =========================================================
# VENTAS
# =========================================================

with tab2:

    st.subheader("🛒 Ventas")

    if not inv.empty:

        with st.form("ventas_form"):

            producto = st.selectbox(
                "Producto",
                inv["producto"]
            )

            stock_actual = int(
                inv[
                    inv["producto"] == producto
                ]["stock"].values[0]
            )

            st.info(
                f"Stock disponible: {stock_actual}"
            )

            cantidad = st.number_input(
                "Cantidad",
                min_value=1
            )

            fecha = st.date_input(
                "Fecha",
                datetime.now()
            )

            vender = st.form_submit_button(
                "Vender"
            )

            if vender:

                ok, msg = registrar_venta(
                    str(fecha),
                    producto,
                    cantidad
                )

                if ok:

                    st.success(msg)
                    st.rerun()

                else:

                    st.error(msg)

    st.dataframe(
        ven,
        use_container_width=True
    )

# =========================================================
# GASTOS
# =========================================================

with tab3:

    st.subheader("💸 Gastos")

    with st.form("gastos_form"):

        concepto = st.text_input(
            "Concepto"
        )

        monto = st.number_input(
            "Monto",
            min_value=0.0
        )

        fecha = st.date_input(
            "Fecha",
            datetime.now()
        )

        guardar_gasto = st.form_submit_button(
            "Guardar"
        )

        if guardar_gasto:

            registrar_gasto(
                str(fecha),
                concepto,
                monto
            )

            st.success(
                "Gasto registrado"
            )

            st.rerun()

    st.dataframe(
        gas,
        use_container_width=True
    )

# =========================================================
# BALANCE
# =========================================================

with tab4:

    st.subheader("📑 Balance")

    ventas_total = (
        ven["venta_ref"].sum()
        if not ven.empty else 0
    )

    ganancias = (
        ven["ganancia"].sum()
        if not ven.empty else 0
    )

    gastos_total = (
        gas["monto"].sum()
        if not gas.empty else 0
    )

    utilidad = ganancias - gastos_total

    stock_total = (
        inv["stock"].sum()
        if not inv.empty else 0
    )

    inventario_costo = (
        (inv["stock"] * inv["costo"]).sum()
        if not inv.empty else 0
    )

    inventario_venta = (
        (inv["stock"] * inv["venta"]).sum()
        if not inv.empty else 0
    )

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "💰 Ventas",
        f"S/ {ventas_total:,.2f}"
    )

    c2.metric(
        "📈 Ganancias",
        f"S/ {ganancias:,.2f}"
    )

    c3.metric(
        "💸 Gastos",
        f"S/ {gastos_total:,.2f}"
    )

    c4.metric(
        "🏦 Utilidad",
        f"S/ {utilidad:,.2f}"
    )

    c5,c6,c7 = st.columns(3)

    c5.metric(
        "📦 Stock",
        stock_total
    )

    c6.metric(
        "🏭 Inventario Costo",
        f"S/ {inventario_costo:,.2f}"
    )

    c7.metric(
        "🏪 Inventario Valorizado",
        f"S/ {inventario_venta:,.2f}"
    )

# =========================================================
# DASHBOARD PRO
# =========================================================

with tab5:

    st.subheader("📈 Dashboard Ejecutivo")

    ventas_total = (
        ven["venta_ref"].sum()
        if not ven.empty else 0
    )

    utilidad = (
        ven["ganancia"].sum()
        if not ven.empty else 0
    ) - (
        gas["monto"].sum()
        if not gas.empty else 0
    )

    productos_vendidos = (
        ven["cantidad"].sum()
        if not ven.empty else 0
    )

    stock_total = (
        inv["stock"].sum()
        if not inv.empty else 0
    )

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "💰 Ventas",
        f"S/ {ventas_total:,.2f}"
    )

    c2.metric(
        "📈 Utilidad",
        f"S/ {utilidad:,.2f}"
    )

    c3.metric(
        "🛒 Vendidos",
        productos_vendidos
    )

    c4.metric(
        "📦 Stock",
        stock_total
    )

    st.divider()

    # =====================================================
    # GRAFICO BARRAS
    # =====================================================

    if not ven.empty:

        st.subheader(
            "📊 Ganancia por Producto"
        )

        fig1 = px.bar(

            ven.groupby("producto")[
                "ganancia"
            ].sum().reset_index(),

            x="producto",
            y="ganancia",

            color="producto",

            text_auto=True,

            template="plotly_dark",

            color_discrete_sequence=
            px.colors.qualitative.Bold
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    # =====================================================
    # GRAFICO PASTEL
    # =====================================================

    if not ven.empty:

        st.subheader(
            "🥧 Participación de Ventas"
        )

        pie = px.pie(

            ven.groupby("producto")[
                "cantidad"
            ].sum().reset_index(),

            names="producto",
            values="cantidad",

            hole=0.4,

            template="plotly_dark",

            color_discrete_sequence=
            px.colors.qualitative.Bold
        )

        st.plotly_chart(
            pie,
            use_container_width=True
        )

    # =====================================================
    # LINEA
    # =====================================================

    if not ven.empty:

        ven["fecha"] = pd.to_datetime(
            ven["fecha"]
        )

        st.subheader(
            "📈 Evolución de Ganancias"
        )

        linea = px.line(

            ven.groupby("fecha")[
                "ganancia"
            ].sum().reset_index(),

            x="fecha",
            y="ganancia",

            markers=True,

            template="plotly_dark",

            color_discrete_sequence=
            px.colors.qualitative.Bold
        )

        st.plotly_chart(
            linea,
            use_container_width=True
        )

    # =====================================================
    # STOCK
    # =====================================================

    if not inv.empty:

        st.subheader(
            "📦 Stock Actual"
        )

        stock_fig = px.bar(

            inv,

            x="stock",
            y="producto",

            orientation="h",

            color="producto",

            text_auto=True,

            template="plotly_dark",

            color_discrete_sequence=
            px.colors.qualitative.Bold
        )

        st.plotly_chart(
            stock_fig,
            use_container_width=True
        )

# =========================================================
# EXPORTAR
# =========================================================

with tab6:

    st.subheader("💾 Exportar")

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="xlsxwriter"
    ) as writer:

        inv.to_excel(
            writer,
            index=False,
            sheet_name="Inventario"
        )

        ven.to_excel(
            writer,
            index=False,
            sheet_name="Ventas"
        )

        gas.to_excel(
            writer,
            index=False,
            sheet_name="Gastos"
        )

    st.download_button(
        "📥 Descargar ERP",
        output.getvalue(),
        "tulip_erp.xlsx"
    )
