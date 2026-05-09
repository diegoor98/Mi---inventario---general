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

h1,h2,h3,h4{
    color:white;
}

[data-testid="stMetric"]{
    background:#161B22;
    border:1px solid #30363D;
    padding:20px;
    border-radius:15px;
    box-shadow:0 0 10px rgba(0,0,0,0.3);
}

div.stButton > button{
    background:#FF4B91;
    color:white;
    border:none;
    border-radius:8px;
    padding:6px 14px;
    font-size:14px;
    font-weight:600;
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
    precio_venta
):

    if not producto.strip():
        return False, "Ingrese producto"

    cursor.execute(
        "SELECT * FROM inventario WHERE producto=?",
        (producto,)
    )

    existente = cursor.fetchone()

    if existente:

        nuevo_stock = existente[3] + stock

        cursor.execute("""
        UPDATE inventario
        SET categoria=?,
            stock=?,
            costo=?,
            venta=?
        WHERE producto=?
        """, (
            categoria,
            nuevo_stock,
            costo,
            precio_venta,
            producto
        ))

    else:

        cursor.execute("""
        INSERT INTO inventario
        VALUES (NULL,?,?,?,?,?)
        """, (
            producto,
            categoria,
            stock,
            costo,
            precio_venta
        ))

    conn.commit()

    return True, "✅ Producto guardado"

# =========================================================

def registrar_venta(
    fecha,
    producto,
    cantidad
):

    try:

        cursor.execute(
            "SELECT * FROM inventario WHERE producto=?",
            (producto,)
        )

        datos = cursor.fetchone()

        if not datos:
            return False, "❌ Producto no existe"

        _, _, _, stock, costo, precio_venta = datos

        if stock <= 0:
            return False, "❌ Producto sin stock"

        if cantidad > stock:
            return False, f"❌ Stock insuficiente. Disponible: {stock}"

        nuevo_stock = stock - cantidad

        ganancia = cantidad * (
            precio_venta - costo
        )

        cursor.execute("""
        UPDATE inventario
        SET stock=?
        WHERE producto=?
        """, (
            nuevo_stock,
            producto
        ))

        cursor.execute("""
        INSERT INTO ventas
        VALUES (NULL,?,?,?,?,?,?)
        """, (
            fecha,
            producto,
            cantidad,
            costo,
            precio_venta,
            ganancia
        ))

        conn.commit()

        return True, "✅ Venta registrada"

    except Exception as e:

        return False, f"❌ Error: {e}"

# =========================================================

def registrar_gasto(
    fecha,
    concepto,
    monto
):

    cursor.execute("""
    INSERT INTO gastos
    VALUES (NULL,?,?,?)
    """, (
        fecha,
        concepto,
        monto
    ))

    conn.commit()

# =========================================================

def eliminar_producto(producto):

    cursor.execute("""
    DELETE FROM inventario
    WHERE producto=?
    """, (producto,))

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

    if buscar:

        filtro = inv[
            inv["producto"]
            .str.contains(
                buscar,
                case=False
            )
        ]

        st.dataframe(filtro)

    modo = st.radio(
        "Modo",
        ["Existente", "Nuevo"],
        horizontal=True
    )

    with st.form("inventario_form"):

        categoria0 = ""
        costo0 = 0.0
        venta0 = 0.0

        # =================================================
        # EXISTENTE
        # =================================================

        if modo == "Existente" and not inv.empty:

            producto_existente = st.selectbox(
                "Producto",
                inv["producto"],
                key="producto_existente"
            )

            producto = producto_existente

            d = inv[
                inv["producto"] == producto
            ].iloc[0]

            categoria0 = d["categoria"]
            costo0 = d["costo"]
            venta0 = d["venta"]

        # =================================================
        # NUEVO
        # =================================================

        else:

            producto_nuevo = st.text_input(
                "Nuevo Producto",
                key="producto_nuevo"
            )

            producto = producto_nuevo

        categoria = st.text_input(
            "Categoria",
            value=categoria0
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            stock = st.number_input(
                "Stock",
                min_value=0,
                step=1
            )

        with col2:

            costo = st.number_input(
                "Costo",
                min_value=0.0,
                value=float(costo0)
            )

        with col3:

            precio_venta = st.number_input(
                "Venta",
                min_value=0.0,
                value=float(venta0)
            )

        guardar_btn = st.form_submit_button(
            "Guardar"
        )

        if guardar_btn:

            ok, msg = guardar_producto(
                producto,
                categoria,
                stock,
                costo,
                precio_venta
            )

            if ok:

                st.success(msg)
                st.rerun()

            else:

                st.error(msg)

    st.divider()

    st.dataframe(inv)

# =========================================================
# VENTAS
# =========================================================

with tab2:

    st.subheader("Ventas")

    if "mensaje_venta" not in st.session_state:
        st.session_state.mensaje_venta = ""

    if "tipo_venta" not in st.session_state:
        st.session_state.tipo_venta = ""

    if st.session_state.mensaje_venta != "":

        if st.session_state.tipo_venta == "ok":
            st.success(st.session_state.mensaje_venta)
        else:
            st.error(st.session_state.mensaje_venta)

        if st.button("OK"):

            st.session_state.mensaje_venta = ""
            st.session_state.tipo_venta = ""

            st.rerun()

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
                min_value=1,
                step=1
            )

            fecha = st.date_input(
                "Fecha",
                datetime.now()
            )

            vender_btn = st.form_submit_button(
                "Vender"
            )

            if vender_btn:

                ok, msg = registrar_venta(
                    str(fecha),
                    producto,
                    cantidad
                )

                st.session_state.mensaje_venta = msg

                if ok:
                    st.session_state.tipo_venta = "ok"
                else:
                    st.session_state.tipo_venta = "error"

                st.rerun()

    st.divider()

    st.dataframe(ven)

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
                "✅ Gasto registrado"
            )

            st.rerun()

    st.divider()

    st.dataframe(gas)

# =========================================================
# BALANCE
# =========================================================

with tab4:

    st.subheader("📑 Balance General")

    tipo_balance = st.radio(
        "Ver balance por:",
        ["Todo", "Mes", "Año"],
        horizontal=True,
        key="radio_balance"
    )

    ven_filtrado = ven.copy()
    gas_filtrado = gas.copy()

    if not ven.empty:
        ven_filtrado["fecha"] = pd.to_datetime(
            ven_filtrado["fecha"]
        )

    if not gas.empty:
        gas_filtrado["fecha"] = pd.to_datetime(
            gas_filtrado["fecha"]
        )

    if tipo_balance == "Mes":

        meses = [
            "Enero","Febrero","Marzo",
            "Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre",
            "Octubre","Noviembre","Diciembre"
        ]

        mes = st.selectbox(
            "Mes",
            range(1,13),
            format_func=lambda x: meses[x-1],
            key="mes_balance"
        )

        anio = st.selectbox(
            "Año",
            sorted(
                ven_filtrado["fecha"]
                .dt.year.unique()
            ) if not ven_filtrado.empty else [datetime.now().year],
            key="anio_balance"
        )

        if not ven_filtrado.empty:

            ven_filtrado = ven_filtrado[
                (ven_filtrado["fecha"].dt.month == mes) &
                (ven_filtrado["fecha"].dt.year == anio)
            ]

        if not gas_filtrado.empty:

            gas_filtrado = gas_filtrado[
                (gas_filtrado["fecha"].dt.month == mes) &
                (gas_filtrado["fecha"].dt.year == anio)
            ]

    elif tipo_balance == "Año":

        anio = st.selectbox(
            "Año",
            sorted(
                ven_filtrado["fecha"]
                .dt.year.unique()
            ) if not ven_filtrado.empty else [datetime.now().year],
            key="anio_balance_only"
        )

        if not ven_filtrado.empty:

            ven_filtrado = ven_filtrado[
                ven_filtrado["fecha"].dt.year == anio
            ]

        if not gas_filtrado.empty:

            gas_filtrado = gas_filtrado[
                gas_filtrado["fecha"].dt.year == anio
            ]

    ventas_total = (
        ven_filtrado["venta_ref"].sum()
        if not ven_filtrado.empty else 0
    )

    ganancias = (
        ven_filtrado["ganancia"].sum()
        if not ven_filtrado.empty else 0
    )

    gastos_total = (
        gas_filtrado["monto"].sum()
        if not gas_filtrado.empty else 0
    )

    utilidad = ganancias - gastos_total

    valor_inventario_costo = (
        (inv["stock"] * inv["costo"]).sum()
        if not inv.empty else 0
    )

    valor_inventario_venta = (
        (inv["stock"] * inv["venta"]).sum()
        if not inv.empty else 0
    )

    c1, c2, c3, c4 = st.columns(4)

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
        "🏆 Utilidad",
        f"S/ {utilidad:,.2f}"
    )

    st.divider()

    c5, c6 = st.columns(2)

    c5.metric(
        "🏭 Valor Inventario Costo",
        f"S/ {valor_inventario_costo:,.2f}"
    )

    c6.metric(
        "🏪 Inventario Valorizado",
        f"S/ {valor_inventario_venta:,.2f}"
    )

# =========================================================
# DASHBOARD
# =========================================================

with tab5:

    st.subheader("📈 Dashboard")

    tipo_dashboard = st.radio(
        "Ver dashboard por:",
        ["Todo", "Mes", "Año"],
        horizontal=True,
        key="radio_dashboard"
    )

    ven_dash = ven.copy()

    if not ven_dash.empty:

        ven_dash["fecha"] = pd.to_datetime(
            ven_dash["fecha"]
        )

    if tipo_dashboard == "Mes":

        meses = [
            "Enero","Febrero","Marzo",
            "Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre",
            "Octubre","Noviembre","Diciembre"
        ]

        mes_dash = st.selectbox(
            "Mes",
            range(1,13),
            format_func=lambda x: meses[x-1],
            key="mes_dashboard"
        )

        anio_dash = st.selectbox(
            "Año",
            sorted(
                ven_dash["fecha"]
                .dt.year.unique()
            ) if not ven_dash.empty else [datetime.now().year],
            key="anio_dashboard"
        )

        if not ven_dash.empty:

            ven_dash = ven_dash[
                (ven_dash["fecha"].dt.month == mes_dash) &
                (ven_dash["fecha"].dt.year == anio_dash)
            ]

    elif tipo_dashboard == "Año":

        anio_dash = st.selectbox(
            "Año",
            sorted(
                ven_dash["fecha"]
                .dt.year.unique()
            ) if not ven_dash.empty else [datetime.now().year],
            key="anio_dashboard_only"
        )

        if not ven_dash.empty:

            ven_dash = ven_dash[
                ven_dash["fecha"].dt.year == anio_dash
            ]

    if not ven_dash.empty:

        fig1 = px.bar(
            ven_dash.groupby("producto")[
                "ganancia"
            ].sum().reset_index(),
            x="producto",
            y="ganancia",
            title="Ganancia por Producto"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        ventas_fecha = ven_dash.groupby(
            "fecha"
        )["ganancia"].sum().reset_index()

        fig2 = px.line(
            ventas_fecha,
            x="fecha",
            y="ganancia",
            title="Ganancias por Fecha"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

# =========================================================
# EXPORTAR
# =========================================================

with tab6:

    st.subheader(
        "Exportar Excel"
    )

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
        file_name="tulip_erp.xlsx"
    )
