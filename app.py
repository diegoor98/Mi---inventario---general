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

.main{
background: linear-gradient(
135deg,
#0E1117 0%,
#161B22 100%
);
} 

h1{
color:white;
font-weight:800;
} 

h2,h3,h4{
color:#F8FAFC;
} 

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

[data-testid="stMetric"]:hover {
transform:translateY(-3px);
border:1px solid #FF4B91;
} 

div.stButton > button{ 

background: linear-gradient(
90deg,
#FF4B91,
#9333EA
); 

color:white; 

border:none; 

border-radius:12px; 

padding:10px 18px; 

font-weight:700;
} 

div.stButton > button:hover{ 

background: linear-gradient(
90deg,
#7C3AED,
#EC4899
); 

transform:scale(1.03);
} 

.stTextInput input,
.stNumberInput input,
.stDateInput input{ 

background:#111827;
color:white;
border-radius:10px;
border:1px solid #334155;
} 

.stSelectbox div[data-baseweb="select"]{ 

background:#111827;
border-radius:10px;
} 

button[data-baseweb="tab"]{ 

background:#111827;
color:#CBD5E1; 

border-radius:12px; 

margin-right:5px; 

padding:10px 20px;
} 

button[aria-selected="true"]{ 

background: linear-gradient(
90deg,
#EC4899,
#8B5CF6
) !important; 

color:white !important;
} 

[data-testid="stDataFrame"]{
border-radius:15px;
overflow:hidden;
} 

.stSuccess{
border-radius:12px;
} 

.stError{
border-radius:12px;
} 

.stWarning{
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
# IMPORTAR BACKUP ERP
# =========================================================

st.sidebar.header("📂 Importar Backup ERP")

file = st.sidebar.file_uploader(
"Subir Excel",
type=["xlsx"]
)

if file:

    try:

        xls = pd.ExcelFile(file)

        # =================================================
        # INVENTARIO
        # =================================================

        if "Inventario" in xls.sheet_names:

            df_inv = pd.read_excel(
            xls,
            "Inventario"
            )

            cursor.execute(
            "DELETE FROM inventario"
            )

            for _,r in df_inv.iterrows():

                cursor.execute("""
                INSERT INTO inventario
                VALUES(?,?,?,?,?,?)
                """,(
                int(r["id"]),
                str(r["producto"]),
                str(r["categoria"]),
                int(r["stock"]),
                float(r["costo"]),
                float(r["venta"])
                ))

        # =================================================
        # VENTAS
        # =================================================

        if "Ventas" in xls.sheet_names:

            df_ven = pd.read_excel(
            xls,
            "Ventas"
            )

            cursor.execute(
            "DELETE FROM ventas"
            )

            for _,r in df_ven.iterrows():

                cursor.execute("""
                INSERT INTO ventas
                VALUES(?,?,?,?,?,?,?)
                """,(
                int(r["id"]),
                str(r["fecha"]),
                str(r["producto"]),
                int(r["cantidad"]),
                float(r["costo_ref"]),
                float(r["venta_ref"]),
                float(r["ganancia"])
                ))

        # =================================================
        # GASTOS
        # =================================================

        if "Gastos" in xls.sheet_names:

            df_gas = pd.read_excel(
            xls,
            "Gastos"
            )

            cursor.execute(
            "DELETE FROM gastos"
            )

            for _,r in df_gas.iterrows():

                cursor.execute("""
                INSERT INTO gastos
                VALUES(?,?,?,?)
                """,(
                int(r["id"]),
                str(r["fecha"]),
                str(r["concepto"]),
                float(r["monto"])
                ))

        conn.commit()

        st.sidebar.success(
        "Backup restaurado correctamente"
        )

        st.rerun()

    except Exception as e:

        st.sidebar.error(
        f"Error: {e}"
        )


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

    # CORREGIDO: Desempaquetado explícito de los 6 campos de la tabla inventario
    id_p, prod_p, cat_p, stock, costo, venta = d 

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

def eliminar_venta(id_venta): 

    cursor.execute("""
    SELECT producto,cantidad
    FROM ventas
    WHERE id=?
    """,(id_venta,)) 

    venta = cursor.fetchone() 

    if venta: 

        producto,cantidad = venta 

        cursor.execute("""
        UPDATE inventario
        SET stock = stock + ?
        WHERE producto=?
        """,(cantidad,producto)) 

        cursor.execute("""
        DELETE FROM ventas
        WHERE id=?
        """,(id_venta,)) 

        conn.commit() 

# ========================================================= 

def eliminar_gasto(id_gasto): 

    cursor.execute("""
    DELETE FROM gastos
    WHERE id=?
    """,(id_gasto,)) 

    conn.commit() 

# ========================================================= 

def deshacer_ultima_venta(): 

    cursor.execute("""
    SELECT id
    FROM ventas
    ORDER BY id DESC
    LIMIT 1
    """) 

    ultima = cursor.fetchone() 

    if ultima: 

        eliminar_venta(ultima[0]) 
# =========================================================
# LIMPIAR ERP
# =========================================================

def limpiar_erp():

    cursor.execute(
    "DELETE FROM inventario"
    )

    cursor.execute(
    "DELETE FROM ventas"
    )

    cursor.execute(
    "DELETE FROM gastos"
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
"📦 Inventario",
"🛒 Ventas",
"💸 Gastos",
"📊 Control Inventario",
"📑 Balance",
"📈 Dashboard",
"💾 Exportar"
]) 
        
# =========================================================
# INVENTARIO
# =========================================================

with tab1:

    st.subheader("📦 Inventario")

    with st.form("inventario_form"):

        # =====================================================
        # CONTROL DE MODO
        # =====================================================

        if "modo_inv" not in st.session_state:
            st.session_state.modo_inv = "Existente"

        c1, c2 = st.columns(2)

        with c1:
            if st.form_submit_button("📌 Existente"):
                st.session_state.modo_inv = "Existente"

        with c2:
            if st.form_submit_button("➕ Nuevo"):
                st.session_state.modo_inv = "Nuevo"

        modo = st.session_state.modo_inv

        st.info(f"Modo seleccionado: {modo}")

        # =====================================================
        # VARIABLES
        # =====================================================

        producto_final = ""
        categoria0 = ""

        # =====================================================
        # EXISTENTE
        # =====================================================

        if modo == "Existente":

            if not inv.empty:

                producto_final = st.selectbox(
                    "Selecciona producto existente",
                    inv["producto"]
                )

                fila = inv[
                    inv["producto"] == producto_final
                ].iloc[0]

                categoria0 = str(fila["categoria"]) if pd.notna(fila["categoria"]) else ""

            else:

                st.warning("No hay productos en inventario")
                producto_final = ""

        # =====================================================
        # NUEVO
        # =====================================================

        else:

            producto_final = st.text_input(
                "Nuevo Producto"
            )

        # =====================================================
        # CATEGORIA (CORREGIDA)
        # =====================================================

        if modo == "Existente" and producto_final:

            categoria = st.text_input(
                "Categoria",
                value=categoria0,
                disabled=True
            )

        else:

            categoria = st.text_input(
                "Categoria"
            )

        # =====================================================
        # CAMPOS ECONÓMICOS
        # =====================================================

        c1, c2, c3 = st.columns(3)

        with c1:
            stock = st.number_input(
                "Stock",
                min_value=0
            )

        with c2:
            costo = st.number_input(
                "Costo",
                min_value=0.0,
                value=0.0
            )

        with c3:
            venta = st.number_input(
                "Venta",
                min_value=0.0,
                value=0.0
            )

        # =====================================================
        # GUARDAR
        # =====================================================

        guardar = st.form_submit_button("Guardar")

        if guardar:

            guardar_producto(
                producto_final.title(),
                categoria,
                stock,
                costo,
                venta
            )

            st.success("Producto guardado")
            st.rerun()

    # =====================================================
    # TABLA
    # =====================================================

    st.dataframe(
        inv,
        use_container_width=True
    )

    # =====================================================
    # ELIMINAR
    # =====================================================

    st.subheader("🗑 Eliminar Producto")

    if not inv.empty:

        producto_eliminar = st.selectbox(
            "Producto",
            inv["producto"],
            key="eliminar"
        )

        confirmar = st.checkbox("Estoy seguro de eliminar")

        c1, c2 = st.columns([1, 5])

        with c1:
            if st.button("Eliminar"):

                if confirmar:

                    eliminar_producto(producto_eliminar)

                    st.success("Producto eliminado")
                    st.rerun()

                else:
                    st.warning("Debes confirmar")      
                    
# =========================================================
# VENTAS
# ========================================================= 

with tab2: 

    st.subheader("🛒 Ventas") 

    if not inv.empty: 

        with st.form("ventas_form"): 

            producto_v = st.selectbox(
            "Producto",
            inv["producto"]
            ) 

            stock_actual = int(
            inv[
            inv["producto"] == producto_v
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
                producto_v,
                cantidad
                ) 

                if ok: 

                    st.success(msg)
                    st.rerun() 

                else: 

                    st.error(msg) 

    st.divider() 

    st.subheader("↩ Retroceder Venta") 

    c1,c2 = st.columns([1,5]) 

    with c1: 

        if st.button("Deshacer"): 

            deshacer_ultima_venta() 

            st.success(
            "Última venta eliminada"
            ) 

            st.rerun() 

    st.subheader("🗑 Eliminar Venta") 

    if not ven.empty: 

        id_venta = st.selectbox(
        "ID Venta",
        ven["id"]
        ) 

        confirmar_v = st.checkbox(
        "Confirmar eliminación venta"
        ) 

        c1,c2 = st.columns([1,5]) 

        with c1: 

            if st.button("Eliminar Venta"): 

                if confirmar_v: 

                    eliminar_venta(id_venta) 

                    st.success(
                    "Venta eliminada"
                    ) 

                    st.rerun() 

                else: 

                    st.warning(
                    "Debes confirmar"
                    ) 

    st.divider() 

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

        fecha_g = st.date_input(
        "Fecha",
        datetime.now(),
        key="fecha_gasto"
        ) 

        guardar_gasto = st.form_submit_button(
        "Guardar"
        ) 

        if guardar_gasto: 

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

    st.subheader("🗑 Eliminar Gasto") 

    if not gas.empty: 

        id_gasto = st.selectbox(
        "ID Gasto",
        gas["id"]
        ) 

        confirmar_gasto = st.checkbox(
        "Confirmar eliminación gasto"
        ) 

        c1,c2 = st.columns([1,5]) 

        with c1: 

            if st.button("Eliminar Gasto"): 

                if confirmar_gasto: 

                    eliminar_gasto(id_gasto) 

                    st.success(
                    "Gasto eliminado"
                    ) 

                    st.rerun() 

                else: 

                    st.warning(
                    "Debes confirmar"
                    ) 

    st.divider() 

    st.dataframe(
    gas,
    use_container_width=True
    ) 

# =========================================================
# CONTROL DE INVENTARIO
# =========================================================

with tab4:

    st.subheader("📊 Control de Inventario (Entradas / Salidas)")

    if inv.empty:
        st.info("No hay datos en inventario")
    else:

        # filtro por categoría
        categorias = ["Todas"] + list(inv["categoria"].dropna().unique())

        cat_sel = st.selectbox(
            "Filtrar por categoría",
            categorias
        )

        data = inv.copy()

        if cat_sel != "Todas":
            data = data[data["categoria"] == cat_sel]

        # cálculo de entradas/salidas simuladas
        data["valor_stock"] = data["stock"] * data["costo"]

        st.metric("📦 Total productos", len(data))
        st.metric("📦 Stock total", int(data["stock"].sum()))
        st.metric("💰 Valor inventario", f"S/ {data['valor_stock'].sum():,.2f}")

        st.divider()

        st.dataframe(
            data,
            use_container_width=True
        )
        
# =========================================================
# BALANCE
# ========================================================= 

with tab5: 

    st.subheader("📑 Balance Financiero") 

    tipo_balance = st.radio(
    "Ver balance por:",
    ["Todo","Mes","Año"],
    horizontal=True,
    key="tipo_bal"
    ) 

    ven_balance = ven.copy()
    gas_balance = gas.copy() 

    if not ven_balance.empty:
        ven_balance["fecha"] = pd.to_datetime(
        ven_balance["fecha"]
        ) 

    if not gas_balance.empty:
        gas_balance["fecha"] = pd.to_datetime(
        gas_balance["fecha"]
        ) 

    if tipo_balance == "Mes": 

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

        c1,c2 = st.columns(2) 

        with c1: 

            mes = st.selectbox(
            "Mes",
            list(meses.keys()),
            format_func=lambda x: meses[x]
            ) 

        with c2: 

            anio = st.selectbox(
            "Año",
            sorted(
            ven_balance["fecha"]
            .dt.year.unique()
            ) if not ven_balance.empty
            else [datetime.now().year]
            ) 

        if not ven_balance.empty: 

            ven_balance = ven_balance[
            (ven_balance["fecha"].dt.month == mes) &
            (ven_balance["fecha"].dt.year == anio)
            ] 

        if not gas_balance.empty: 

            gas_balance = gas_balance[
            (gas_balance["fecha"].dt.month == mes) &
            (gas_balance["fecha"].dt.year == anio)
            ] 

    elif tipo_balance == "Año": 

        anio = st.selectbox(
        "Año",
        sorted(
        ven_balance["fecha"]
        .dt.year.unique()
        ) if not ven_balance.empty
        else [datetime.now().year],
        key="anio_bal"
        ) 

        if not ven_balance.empty: 

            ven_balance = ven_balance[
            ven_balance["fecha"].dt.year == anio
            ] 

        if not gas_balance.empty: 

            gas_balance = gas_balance[
            gas_balance["fecha"].dt.year == anio
            ] 

    ventas_total = (
    ven_balance["venta_ref"].sum()
    if not ven_balance.empty else 0
    ) 

    ganancias = (
    ven_balance["ganancia"].sum()
    if not ven_balance.empty else 0
    ) 

    gastos_total = (
    gas_balance["monto"].sum()
    if not gas_balance.empty else 0
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
# DASHBOARD
# ========================================================= 

with tab6: 

    st.subheader("📈 Dashboard Ejecutivo") 

    tipo_dashboard = st.radio(
    "Ver dashboard por:",
    ["Todo","Mes","Año"],
    horizontal=True,
    key="tipo_dash"
    ) 

    ven_dash = ven.copy() 

    if not ven_dash.empty:
        ven_dash["fecha"] = pd.to_datetime(
        ven_dash["fecha"]
        ) 

    if tipo_dashboard == "Mes": 

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

        c1,c2 = st.columns(2) 

        with c1: 

            mes_d = st.selectbox(
            "Mes Dashboard",
            list(meses.keys()),
            format_func=lambda x: meses[x]
            ) 

        with c2: 

            anio_d = st.selectbox(
            "Año Dashboard",
            sorted(
            ven_dash["fecha"]
            .dt.year.unique()
            ) if not ven_dash.empty
            else [datetime.now().year]
            ) 

        if not ven_dash.empty: 

            ven_dash = ven_dash[
            (ven_dash["fecha"].dt.month == mes_d) &
            (ven_dash["fecha"].dt.year == anio_d)
            ] 

    elif tipo_dashboard == "Año": 

        anio_d = st.selectbox(
        "Año Dashboard",
        sorted(
        ven_dash["fecha"]
        .dt.year.unique()
        ) if not ven_dash.empty
        else [datetime.now().year],
        key="anio_dash_sel"
        ) 

        if not ven_dash.empty: 

            ven_dash = ven_dash[
            ven_dash["fecha"].dt.year == anio_d
            ] 

    if not ven_dash.empty: 

        fig1 = px.bar(
        ven_dash.groupby("producto")[
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

        pie = px.pie(
        ven_dash.groupby("producto")[
        "cantidad"
        ].sum().reset_index(), 

        names="producto",
        values="cantidad", 

        hole=0.4, 

        template="plotly_dark", 

        color_discrete_sequence=
        px.colors.qualitative.Vivid
        ) 

        st.plotly_chart(
        pie,
        use_container_width=True
        ) 

        ventas_fecha = ven_dash.groupby(
        "fecha"
        )["ganancia"].sum().reset_index() 

        linea = px.line(
        ventas_fecha,
        x="fecha",
        y="ganancia",
        markers=True,
        template="plotly_dark"
        ) 

        st.plotly_chart(
        linea,
        use_container_width=True
        ) 

        top = ven_dash.groupby(
        "producto"
        )["cantidad"].sum().reset_index() 

        top = top.sort_values(
        by="cantidad",
        ascending=False
        ) 

        st.subheader(
        "🏆 Top Productos"
        ) 

        st.dataframe(
        top,
        use_container_width=True
        ) 
            
# =========================================================
# EXPORTAR + IMPORTAR + LIMPIAR ERP
# =========================================================

with tab7:

    st.subheader("💾 Exportar ERP")

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

        inv.to_excel(writer, index=False, sheet_name="Inventario")
        ven.to_excel(writer, index=False, sheet_name="Ventas")
        gas.to_excel(writer, index=False, sheet_name="Gastos")

    st.download_button(
        "📥 Descargar ERP",
        output.getvalue(),
        "tulip_erp.xlsx"
    )

    st.divider()

    # =====================================================
    # IMPORTAR ERP ROBUSTO (NO SE ROMPE SI FALTAN DATOS)
    # =====================================================

    st.subheader("📥 Importar ERP desde Excel")

    file = st.file_uploader(
        "Subir archivo Excel",
        type=["xlsx"]
    )

    if file:

        try:
            xls = pd.ExcelFile(file)

            # =================================================
            # INVENTARIO
            # =================================================
            if "Inventario" in xls.sheet_names:

                df_inv = pd.read_excel(xls, "Inventario")
                df_inv.columns = [c.lower() for c in df_inv.columns]

                cursor.execute("DELETE FROM inventario")

                for _, r in df_inv.iterrows():

                    producto = str(r.get("producto", "")).title()
                    categoria = str(r.get("categoria", ""))

                    stock = int(r.get("stock", 0) or 0)
                    costo = float(r.get("costo", 0) or 0)
                    venta = float(r.get("venta", 0) or 0)

                    if producto.strip() == "":
                        continue

                    cursor.execute("""
                    INSERT INTO inventario
                    VALUES(NULL,?,?,?,?,?)
                    """, (
                        producto,
                        categoria,
                        stock,
                        costo,
                        venta
                    ))

            # =================================================
            # VENTAS
            # =================================================
            if "Ventas" in xls.sheet_names:

                df_ven = pd.read_excel(xls, "Ventas")
                df_ven.columns = [c.lower() for c in df_ven.columns]

                cursor.execute("DELETE FROM ventas")

                for _, r in df_ven.iterrows():

                    cursor.execute("""
                    INSERT INTO ventas
                    VALUES(NULL,?,?,?,?,?,?)
                    """, (
                        str(r.get("fecha", "")),
                        str(r.get("producto", "")),
                        int(r.get("cantidad", 0) or 0),
                        float(r.get("costo_ref", 0) or 0),
                        float(r.get("venta_ref", 0) or 0),
                        float(r.get("ganancia", 0) or 0)
                    ))

            # =================================================
            # GASTOS
            # =================================================
            if "Gastos" in xls.sheet_names:

                df_gas = pd.read_excel(xls, "Gastos")
                df_gas.columns = [c.lower() for c in df_gas.columns]

                cursor.execute("DELETE FROM gastos")

                for _, r in df_gas.iterrows():

                    cursor.execute("""
                    INSERT INTO gastos
                    VALUES(NULL,?,?,?)
                    """, (
                        str(r.get("fecha", "")),
                        str(r.get("concepto", "")),
                        float(r.get("monto", 0) or 0)
                    ))

            conn.commit()

            st.success("📦 Backup importado correctamente")
            st.rerun()

        except Exception as e:
            st.error(f"Error al importar: {e}")

    st.divider()

    # =====================================================
    # LIMPIAR ERP
    # =====================================================

    st.subheader("🧹 Limpiar ERP")

    st.warning("⚠ Esto eliminará TODO el sistema")

    confirmar = st.checkbox("Confirmo limpiar todo")

    if st.button("🧨 Limpiar ERP"):

        if confirmar:

            limpiar_erp()
            st.success("ERP limpiado correctamente")
            st.rerun()

        else:
            st.error("Debes confirmar primero")
            
