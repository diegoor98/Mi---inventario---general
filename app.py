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
    transition:0.2s;
}

div.stButton > button:hover{
    background:#FF2E7A;
    transform:scale(1.03);
}

.stCheckbox{
    padding-top:10px;
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

    return True, "Producto guardado"

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

    datos = cursor.fetchone()

    if not datos:
        return False, "Producto no existe"

    _, _, _, stock, costo, precio_venta = datos

    if cantidad > stock:
        return False, "Stock insuficiente"

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

    return True, "Venta registrada"

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
# IMPORTAR EXCEL
# =========================================================

st.sidebar.header("📂 Importar Excel")

archivo = st.sidebar.file_uploader(
    "Subir archivo",
    type=["xlsx"]
)

if archivo:

    try:

        df = pd.read_excel(archivo)

        df.columns = [
            c.lower()
            for c in df.columns
        ]

        columnas = [
            "producto",
            "categoria",
            "stock",
            "costo",
            "venta"
        ]

        if not all(
            c in df.columns
            for c in columnas
        ):

            st.sidebar.error(
                "Columnas inválidas"
            )

        else:

            for _, r in df.iterrows():

                guardar_producto(
                    str(r["producto"]).title(),
                    str(r["categoria"]),
                    int(r["stock"]),
                    float(r["costo"]),
                    float(r["venta"])
                )

            st.sidebar.success(
                "Importado correctamente"
            )

            st.rerun()

    except Exception as e:

        st.sidebar.error(
            f"Error: {e}"
        )

# =========================================================
# TITULO
# =========================================================

st.markdown("""
<h1 style='text-align:center;'>
🌷 Tulip ERP
</h1>
""", unsafe_allow_html=True)

# =========================================================
# RECARGAR DATOS
# =========================================================

inv, ven, gas = cargar_datos()

# =========================================================
# STOCK BAJO
# =========================================================

if not inv.empty:

    bajo = inv[
        inv["stock"] < 5
    ]

    if not bajo.empty:

        st.warning(
            "⚠ Productos con stock bajo"
        )

        st.dataframe(
            bajo[["producto", "stock"]]
        )

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

    # =====================================================
    # FORM INVENTARIO
    # =====================================================

    with st.form("inventario_form"):

        modo = st.radio(
            "Modo",
            ["Existente", "Nuevo"],
            horizontal=True
        )

        producto = ""

        categoria0 = ""
        costo0 = 0.0
        venta0 = 0.0

        if (
            modo == "Existente"
            and not inv.empty
        ):

            producto = st.selectbox(
                "Producto",
                inv["producto"]
            )

            d = inv[
                inv["producto"] == producto
            ].iloc[0]

            categoria0 = d["categoria"]
            costo0 = d["costo"]
            venta0 = d["venta"]

        else:

            producto = st.text_input(
                "Producto"
            )

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

        if st.form_submit_button("Guardar"):

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

    # =====================================================
    # DESCONTAR STOCK
    # =====================================================

    st.subheader("➖ Descontar Stock")

    if not inv.empty:

        p = st.selectbox(
            "Producto",
            inv["producto"],
            key="descontar"
        )

        stock_actual = int(
            inv[
                inv["producto"] == p
            ]["stock"].values[0]
        )

        st.info(
            f"Stock actual: {stock_actual}"
        )

        cantidad = st.number_input(
            "Cantidad",
            min_value=1,
            step=1
        )

        if st.button("Quitar"):

            if cantidad <= stock_actual:

                cursor.execute("""
                UPDATE inventario
                SET stock=?
                WHERE producto=?
                """, (
                    stock_actual - cantidad,
                    p
                ))

                conn.commit()

                st.success(
                    "Stock actualizado"
                )

                st.rerun()

            else:

                st.error(
                    "Cantidad mayor al stock"
                )

    # =====================================================
    # ELIMINAR PRODUCTO SEGURO
    # =====================================================

    st.subheader("🗑 Eliminar Producto")

    if not inv.empty:

        pe = st.selectbox(
            "Seleccionar producto",
            inv["producto"],
            key="eliminar_producto"
        )

        st.markdown(
            f"""
            <div style="
                background:#161B22;
                padding:12px;
                border-radius:10px;
                border:1px solid #30363D;
                margin-bottom:10px;
            ">
            ⚠ Está a punto de eliminar:
            <b>{pe}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

        confirmar = st.checkbox(
            "Sí, estoy seguro de eliminar este producto"
        )

        col1, col2, col3 = st.columns([1,1,5])

        with col1:

            eliminar_btn = st.button(
                "Eliminar",
                key="btn_eliminar"
            )

        with col2:

            cancelar_btn = st.button(
                "Cancelar",
                key="btn_cancelar"
            )

        # =================================================
        # ELIMINAR
        # =================================================

        if eliminar_btn:

            if confirmar:

                eliminar_producto(pe)

                st.success(
                    f"{pe} eliminado correctamente"
                )

                st.rerun()

            else:

                st.warning(
                    "Debe confirmar la eliminación"
                )

        # =================================================
        # CANCELAR
        # =================================================

        if cancelar_btn:

            st.info(
                "Operación cancelada"
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
                min_value=1,
                step=1
            )

            fecha = st.date_input(
                "Fecha",
                datetime.now()
            )

            if st.form_submit_button("Vender"):

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

        if st.form_submit_button("Guardar"):

            registrar_gasto(
                str(fecha),
                concepto,
                monto
            )

            st.success(
                "Gasto registrado"
            )

            st.rerun()

    st.divider()

    st.dataframe(gas)

# =========================================================
# BALANCE
# =========================================================

with tab4:

    st.subheader(
        "Balance General"
    )

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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Ventas",
        f"S/ {ventas_total:,.2f}"
    )

    col2.metric(
        "Ganancia",
        f"S/ {ganancias:,.2f}"
    )

    col3.metric(
        "Gastos",
        f"S/ {gastos_total:,.2f}"
    )

    col4.metric(
        "Utilidad",
        f"S/ {utilidad:,.2f}"
    )

# =========================================================
# DASHBOARD
# =========================================================

with tab5:

    st.subheader("Dashboard")

    if not ven.empty:

        fig1 = px.bar(
            ven.groupby("producto")[
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

        ventas_fecha = ven.groupby(
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
