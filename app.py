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
    background-color:#0E1117;
}

h1,h2,h3{
    color:white;
}

.stMetric{
    background:#161B22;
    padding:15px;
    border-radius:15px;
    border:1px solid #30363D;
}

div.stButton > button{
    background:#FF4B91;
    color:white;
    border:none;
    border-radius:10px;
    padding:10px 18px;
    font-weight:bold;
}

div.stButton > button:hover{
    background:#FF2E7A;
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

def cargar_datos():

    inventario = pd.read_sql(
        "SELECT * FROM inventario",
        conn
    )

    ventas = pd.read_sql(
        "SELECT * FROM ventas",
        conn
    )

    gastos = pd.read_sql(
        "SELECT * FROM gastos",
        conn
    )

    return inventario, ventas, gastos

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

    dato = cursor.fetchone()

    if not dato:
        return False, "Producto no existe"

    _,_,_,stock,costo,venta = dato

    if cantidad > stock:
        return False, "Stock insuficiente"

    nuevo_stock = stock - cantidad

    ganancia = cantidad * (venta - costo)

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
# CARGAR DATOS
# =========================================================

inv, ven, gas = cargar_datos()

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

    st.subheader("Inventario")

    buscar = st.text_input(
        "🔍 Buscar producto"
    )

    inv_filtrado = inv.copy()

    if buscar:

        inv_filtrado = inv[
            inv["producto"]
            .str.contains(
                buscar,
                case=False
            )
        ]

    with st.form("inventario_form"):

        modo = st.radio(
            "Modo",
            ["Existente","Nuevo"],
            horizontal=True
        )

        producto = ""

        categoria_default = ""
        costo_default = 0.0
        venta_default = 0.0

        # =================================================
        # EXISTENTE
        # =================================================

        if modo == "Existente":

            if not inv.empty:

                producto = st.selectbox(
                    "Producto",
                    inv["producto"]
                )

                fila = inv[
                    inv["producto"] == producto
                ].iloc[0]

                categoria_default = fila["categoria"]
                costo_default = fila["costo"]
                venta_default = fila["venta"]

        # =================================================
        # NUEVO
        # =================================================

        else:

            producto = st.text_input(
                "Nuevo Producto"
            )

        categoria = st.text_input(
            "Categoria",
            value=categoria_default
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
                value=float(costo_default)
            )

        with c3:
            venta = st.number_input(
                "Venta",
                min_value=0.0,
                value=float(venta_default)
            )

        guardar = st.form_submit_button(
            "Guardar"
        )

        if guardar:

            if producto.strip() == "":

                st.error(
                    "Ingrese producto"
                )

            else:

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
        inv_filtrado,
        use_container_width=True
    )

    # =====================================================
    # ELIMINAR PRODUCTO
    # =====================================================

    st.subheader("🗑 Eliminar Producto")

    if not inv.empty:

        producto_eliminar = st.selectbox(
            "Seleccionar producto",
            inv["producto"],
            key="eliminar_producto"
        )

        confirmar = st.checkbox(
            "Estoy seguro de eliminar"
        )

        c1,c2 = st.columns([1,5])

        with c1:

            if st.button(
                "Eliminar",
                key="btn_eliminar"
            ):

                if confirmar:

                    eliminar_producto(
                        producto_eliminar
                    )

                    st.success(
                        "Producto eliminado"
                    )

                    st.rerun()

                else:

                    st.warning(
                        "Debes confirmar"
                    )

# =========================================================
# VENTAS
# =========================================================

with tab2:

    st.subheader("Ventas")

    if not inv.empty:

        with st.form("ventas_form"):

            producto = st.selectbox(
                "Producto",
                inv["producto"]
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

                ok, mensaje = registrar_venta(
                    str(fecha),
                    producto,
                    cantidad
                )

                if ok:

                    st.success(mensaje)

                    st.rerun()

                else:

                    st.error(mensaje)

    st.dataframe(
        ven,
        use_container_width=True
    )

# =========================================================
# GASTOS
# =========================================================

with tab3:

    st.subheader("Gastos")

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

    ganancias_total = (
        ven["ganancia"].sum()
        if not ven.empty else 0
    )

    gastos_total = (
        gas["monto"].sum()
        if not gas.empty else 0
    )

    utilidad_neta = (
        ganancias_total - gastos_total
    )

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
        f"S/ {ganancias_total:,.2f}"
    )

    c3.metric(
        "💸 Gastos",
        f"S/ {gastos_total:,.2f}"
    )

    c4.metric(
        "🏦 Utilidad Neta",
        f"S/ {utilidad_neta:,.2f}"
    )

    c5,c6,c7 = st.columns(3)

    c5.metric(
        "📦 Stock Total",
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
# DASHBOARD
# =========================================================

with tab5:

    st.subheader("📈 Dashboard Ejecutivo")

    # =====================================================
    # KPIs
    # =====================================================

    ventas_total = (
        ven["venta_ref"].sum()
        if not ven.empty else 0
    )

    ganancias_total = (
        ven["ganancia"].sum()
        if not ven.empty else 0
    )

    gastos_total = (
        gas["monto"].sum()
        if not gas.empty else 0
    )

    utilidad_neta = (
        ganancias_total - gastos_total
    )

    productos_vendidos = (
        ven["cantidad"].sum()
        if not ven.empty else 0
    )

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

    stock_bajo = (
        len(inv[inv["stock"] < 5])
        if not inv.empty else 0
    )

    producto_top = "-"

    if not ven.empty:

        producto_top = (
            ven.groupby("producto")[
                "cantidad"
            ]
            .sum()
            .idxmax()
        )

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "💰 Ventas",
        f"S/ {ventas_total:,.2f}"
    )

    c2.metric(
        "📈 Utilidad",
        f"S/ {utilidad_neta:,.2f}"
    )

    c3.metric(
        "🛒 Vendidos",
        productos_vendidos
    )

    c4.metric(
        "📦 Stock",
        stock_total
    )

    c5,c6,c7,c8 = st.columns(4)

    c5.metric(
        "⚠ Stock Bajo",
        stock_bajo
    )

    c6.metric(
        "🏆 Más Vendido",
        producto_top
    )

    c7.metric(
        "🏭 Inventario",
        f"S/ {inventario_costo:,.2f}"
    )

    c8.metric(
        "🏪 Valorizado",
        f"S/ {inventario_venta:,.2f}"
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
            text_auto=True
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
            hole=0.4
        )

        st.plotly_chart(
            pie,
            use_container_width=True
        )

    # =====================================================
    # GRAFICO LINEA
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
            markers=True
        )

        st.plotly_chart(
            linea,
            use_container_width=True
        )

    # =====================================================
    # STOCK ACTUAL
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
            text_auto=True
        )

        st.plotly_chart(
            stock_fig,
            use_container_width=True
        )

    # =====================================================
    # ALERTAS
    # =====================================================

    st.subheader("🚨 Alertas")

    agotados = inv[
        inv["stock"] == 0
    ]

    bajos = inv[
        (inv["stock"] > 0) &
        (inv["stock"] < 5)
    ]

    if not agotados.empty:

        st.error(
            f"❌ {len(agotados)} productos agotados"
        )

        st.dataframe(
            agotados[
                ["producto","stock"]
            ]
        )

    if not bajos.empty:

        st.warning(
            f"⚠ {len(bajos)} productos con stock bajo"
        )

        st.dataframe(
            bajos[
                ["producto","stock"]
            ]
        )

# =========================================================
# EXPORTAR
# =========================================================

with tab6:

    st.subheader("💾 Exportar Excel")

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
