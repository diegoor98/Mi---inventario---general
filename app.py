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

.main {
    background-color: #0E1117;
}

h1, h2, h3 {
    color: white;
}

.stMetric {
    background-color: #161B22;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #30363D;
}

div.stButton > button {
    background-color: #FF4B91;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px;
    font-weight: bold;
}

div.stButton > button:hover {
    background-color: #FF2E7A;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# BASE DE DATOS SQLITE
# =========================================================

conn = sqlite3.connect(
    "tulip_erp.db",
    check_same_thread=False
)

cursor = conn.cursor()

# INVENTARIO

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

# VENTAS

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

# GASTOS

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

    df_inv = pd.read_sql(
        "SELECT * FROM inventario",
        conn
    )

    df_ven = pd.read_sql(
        "SELECT * FROM ventas",
        conn
    )

    df_gas = pd.read_sql(
        "SELECT * FROM gastos",
        conn
    )

    return df_inv, df_ven, df_gas


def guardar_producto(
    producto,
    categoria,
    stock,
    costo,
    venta
):

    cursor.execute("""
    SELECT * FROM inventario
    WHERE producto=?
    """, (producto,))

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
        """, (
            categoria,
            nuevo_stock,
            costo,
            venta,
            producto
        ))

    else:

        cursor.execute("""
        INSERT INTO inventario
        (producto, categoria, stock, costo, venta)
        VALUES (?, ?, ?, ?, ?)
        """, (
            producto,
            categoria,
            stock,
            costo,
            venta
        ))

    conn.commit()


def registrar_venta(
    fecha,
    producto,
    cantidad
):

    cursor.execute("""
    SELECT * FROM inventario
    WHERE producto=?
    """, (producto,))

    prod = cursor.fetchone()

    if prod is None:
        return False, "Producto no encontrado"

    id_p, nom, cat, stock, costo, venta = prod

    if stock < cantidad:
        return False, "Stock insuficiente"

    nuevo_stock = stock - cantidad

    ganancia = cantidad * (
        venta - costo
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
    (fecha, producto, cantidad,
    costo_ref, venta_ref, ganancia)

    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        fecha,
        producto,
        cantidad,
        costo,
        venta,
        ganancia
    ))

    conn.commit()

    return True, "Venta registrada"


def registrar_gasto(
    fecha,
    concepto,
    monto
):

    cursor.execute("""
    INSERT INTO gastos
    (fecha, concepto, monto)

    VALUES (?, ?, ?)
    """, (
        fecha,
        concepto,
        monto
    ))

    conn.commit()


def eliminar_producto(id_producto):

    cursor.execute("""
    DELETE FROM inventario
    WHERE id=?
    """, (id_producto,))

    conn.commit()


def convertir_excel(
    df_inv,
    df_ven,
    df_gas
):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine='xlsxwriter'
    ) as writer:

        df_inv.to_excel(
            writer,
            index=False,
            sheet_name='Inventario'
        )

        df_ven.to_excel(
            writer,
            index=False,
            sheet_name='Ventas'
        )

        df_gas.to_excel(
            writer,
            index=False,
            sheet_name='Gastos'
        )

    return output.getvalue()

# =========================================================
# CARGAR DATOS
# =========================================================

inv, ven, gas = cargar_datos()

# =========================================================
# IMPORTAR EXCEL
# =========================================================

st.sidebar.header("📂 Importar Excel")

archivo = st.sidebar.file_uploader(
    "Subir Excel",
    type=["xlsx"]
)

if archivo is not None:

    try:

        xls = pd.ExcelFile(archivo)

        hojas = xls.sheet_names

        st.sidebar.success(
            f"Hojas detectadas: {hojas}"
        )

        # =============================================
        # IMPORTAR INVENTARIO
        # =============================================

        if len(hojas) >= 1:

            df_import = pd.read_excel(
                archivo,
                sheet_name=hojas[0]
            )

            # columnas en minúscula
            df_import.columns = [
                c.lower()
                for c in df_import.columns
            ]

            if (
                'producto' in df_import.columns
                and
                'stock' in df_import.columns
            ):

                for _, row in df_import.iterrows():

                    producto = str(
                        row.get(
                            'producto',
                            ''
                        )
                    ).strip().title()

                    categoria = str(
                        row.get(
                            'categoria',
                            ''
                        )
                    ).strip().title()

                    stock = int(
                        row.get(
                            'stock',
                            0
                        )
                    )

                    costo = float(
                        row.get(
                            'costo',
                            0
                        )
                    )

                    venta = float(
                        row.get(
                            'venta',
                            0
                        )
                    )

                    if producto != "":

                        guardar_producto(
                            producto,
                            categoria,
                            stock,
                            costo,
                            venta
                        )

                st.sidebar.success(
                    "✅ Inventario importado"
                )

    except Exception as e:

        st.sidebar.error(
            f"Error: {e}"
        )

# =========================================================
# TÍTULO
# =========================================================

st.markdown(
    """
    <h1 style='text-align:center;'>
    🌷 Tulip S.A. ERP
    </h1>
    """,
    unsafe_allow_html=True
)

# =========================================================
# RECARGAR DATOS
# =========================================================

inv, ven, gas = cargar_datos()

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
# TAB INVENTARIO
# =========================================================

with tab1:

    st.subheader(
        "Gestión de Inventario"
    )

    with st.form("form_producto"):

        producto = st.text_input(
            "Producto"
        ).strip().title()

        categoria = st.text_input(
            "Categoría"
        ).strip().title()

        col1, col2, col3 = st.columns(3)

        with col1:

            stock = st.number_input(
                "Cantidad",
                min_value=0,
                step=1
            )

        with col2:

            costo = st.number_input(
                "Costo",
                min_value=0.0,
                format="%.2f"
            )

        with col3:

            venta = st.number_input(
                "Precio Venta",
                min_value=0.0,
                format="%.2f"
            )

        guardar = st.form_submit_button(
            "✅ Guardar Producto"
        )

        if guardar:

            if producto == "":

                st.warning(
                    "Ingrese nombre"
                )

            else:

                guardar_producto(
                    producto,
                    categoria,
                    stock,
                    costo,
                    venta
                )

                st.success(
                    "Producto guardado"
                )

                st.rerun()

    st.divider()

    st.dataframe(
        inv,
        use_container_width=True
    )

    st.divider()

    st.subheader(
        "Eliminar Producto"
    )

    if not inv.empty:

        producto_del = st.selectbox(
            "Seleccionar producto",
            inv['producto']
        )

        if st.button(
            "🗑 Eliminar"
        ):

            id_del = inv[
                inv['producto']
                == producto_del
            ]['id'].values[0]

            eliminar_producto(id_del)

            st.success(
                "Producto eliminado"
            )

            st.rerun()

# =========================================================
# TAB VENTAS
# =========================================================

with tab2:

    st.subheader(
        "Registro de Ventas"
    )

    if not inv.empty:

        with st.form("form_venta"):

            producto_v = st.selectbox(
                "Producto",
                inv['producto']
            )

            cantidad_v = st.number_input(
                "Cantidad",
                min_value=1,
                step=1
            )

            fecha_v = st.date_input(
                "Fecha",
                datetime.now()
            )

            enviar_v = st.form_submit_button(
                "🚀 Registrar Venta"
            )

            if enviar_v:

                ok, msg = registrar_venta(
                    str(fecha_v),
                    producto_v,
                    cantidad_v
                )

                if ok:

                    st.success(msg)

                    st.rerun()

                else:

                    st.error(msg)

    st.divider()

    st.dataframe(
        ven,
        use_container_width=True
    )

# =========================================================
# TAB GASTOS
# =========================================================

with tab3:

    st.subheader(
        "Registro de Gastos"
    )

    with st.form("form_gastos"):

        concepto = st.text_input(
            "Concepto"
        )

        monto = st.number_input(
            "Monto",
            min_value=0.0
        )

        fecha_g = st.date_input(
            "Fecha",
            datetime.now()
        )

        enviar_g = st.form_submit_button(
            "💸 Registrar Gasto"
        )

        if enviar_g:

            registrar_gasto(
                str(fecha_g),
                concepto,
                monto
            )

            st.success(
                "Gasto registrado"
            )

            st.rerun()

    st.divider()

    st.dataframe(
        gas,
        use_container_width=True
    )

# =========================================================
# TAB BALANCE
# =========================================================

with tab4:

    st.header(
        "📑 Balance General"
    )

    meses = {
        1:"Enero",
        2:"Febrero",
        3:"Marzo",
        4:"Abril",
        5:"Mayo",
        6:"Junio",
        7:"Julio",
        8:"Agosto",
        9:"Septiembre",
        10:"Octubre",
        11:"Noviembre",
        12:"Diciembre"
    }

    filtro = st.radio(
        "Filtro",
        ["Mes", "Año"],
        horizontal=True
    )

    col1, col2 = st.columns(2)

    with col1:

        mes_nombre = st.selectbox(
            "Mes",
            list(meses.values()),
            index=datetime.now().month - 1
        )

    with col2:

        anio = st.selectbox(
            "Año",
            list(range(2024, 2031)),
            index=0
        )

    mes_num = [
        k for k, v in meses.items()
        if v == mes_nombre
    ][0]

    # =============================================
    # ASEGURAR FECHAS
    # =============================================

    if (
        not ven.empty
        and
        'fecha' in ven.columns
    ):

        ven['fecha'] = pd.to_datetime(
            ven['fecha'],
            errors='coerce'
        )

    if (
        not gas.empty
        and
        'fecha' in gas.columns
    ):

        gas['fecha'] = pd.to_datetime(
            gas['fecha'],
            errors='coerce'
        )

    # =============================================
    # FILTRADO
    # =============================================

    if (
        not ven.empty
        and
        'fecha' in ven.columns
    ):

        if filtro == "Mes":

            v_fil = ven[
                (
                    ven['fecha'].dt.month
                    == mes_num
                )
                &
                (
                    ven['fecha'].dt.year
                    == anio
                )
            ]

        else:

            v_fil = ven[
                ven['fecha'].dt.year
                == anio
            ]

    else:

        v_fil = pd.DataFrame()

    if (
        not gas.empty
        and
        'fecha' in gas.columns
    ):

        if filtro == "Mes":

            g_fil = gas[
                (
                    gas['fecha'].dt.month
                    == mes_num
                )
                &
                (
                    gas['fecha'].dt.year
                    == anio
                )
            ]

        else:

            g_fil = gas[
                gas['fecha'].dt.year
                == anio
            ]

    else:

        g_fil = pd.DataFrame()

    # =============================================
    # MÉTRICAS
    # =============================================

    ganancia = (
        v_fil['ganancia'].sum()
        if not v_fil.empty
        else 0
    )

    gastos_total = (
        g_fil['monto'].sum()
        if not g_fil.empty
        else 0
    )

    utilidad = (
        ganancia - gastos_total
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Ganancia Bruta",
        f"${ganancia:,.2f}"
    )

    c2.metric(
        "Gastos",
        f"${gastos_total:,.2f}"
    )

    c3.metric(
        "Utilidad Neta",
        f"${utilidad:,.2f}"
    )

    stock_total = (
        inv['stock'] * inv['costo']
    ).sum() if not inv.empty else 0

    st.info(
        f"📦 Capital en Stock: "
        f"${stock_total:,.2f}"
    )

# =========================================================
# TAB DASHBOARD
# =========================================================

with tab5:

    st.header("📈 Dashboard")

    if not ven.empty:

        # asegurar fecha
        if 'fecha' in ven.columns:

            ven['fecha'] = pd.to_datetime(
                ven['fecha'],
                errors='coerce'
            )

        col1, col2 = st.columns(2)

        # =========================================
        # GANANCIA PRODUCTOS
        # =========================================

        fig1 = px.bar(
            ven.groupby(
                'producto'
            )['ganancia']
            .sum()
            .reset_index(),
            x='producto',
            y='ganancia',
            color='producto',
            template='plotly_dark',
            title='Ganancia por Producto'
        )

        col1.plotly_chart(
            fig1,
            use_container_width=True
        )

        # =========================================
        # GASTOS
        # =========================================

        if not gas.empty:

            fig2 = px.pie(
                gas,
                values='monto',
                names='concepto',
                hole=0.5,
                template='plotly_dark',
                title='Distribución Gastos'
            )

            col2.plotly_chart(
                fig2,
                use_container_width=True
            )

        # =========================================
        # EVOLUCIÓN
        # =========================================

        ventas_fecha = ven.groupby(
            'fecha'
        )['ganancia'].sum().reset_index()

        fig3 = px.line(
            ventas_fecha,
            x='fecha',
            y='ganancia',
            markers=True,
            template='plotly_dark',
            title='Evolución Ganancias'
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

    else:

        st.info(
            "No hay datos aún."
        )

# =========================================================
# TAB EXPORTAR
# =========================================================

with tab6:

    st.subheader(
        "💾 Exportar ERP"
    )

    excel_file = convertir_excel(
        inv,
        ven,
        gas
    )

    st.download_button(
        label="📥 Descargar Excel",
        data=excel_file,
        file_name="Tulip_ERP.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
