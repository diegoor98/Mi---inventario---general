import streamlit as st
import pandas as pd
import plotly.express as px
from meta_ai_api import MetaAI # Si no usas esta libreria puedes borrarla, la mantengo por si acaso
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
# DATABASE - Usamos v4 para asegurar que cree codigo, talla y color sin errores
# ========================================================= 

conn = sqlite3.connect(
"tulip_erp_v4.db",
check_same_thread=False
) 

cursor = conn.cursor() 

# =========================================================
# TABLAS
# ========================================================= 

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventario(
id INTEGER PRIMARY KEY AUTOINCREMENT,
codigo TEXT,
producto TEXT,
talla TEXT,
color TEXT,
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
codigo TEXT,
producto TEXT,
talla TEXT,
color TEXT,
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
        if "Inventario" in xls.sheet_names:
            df_inv = pd.read_excel(xls, "Inventario")
            cursor.execute("DELETE FROM inventario")
            for _,r in df_inv.iterrows():
                cursor.execute("""
                INSERT INTO inventario
                VALUES(?,?,?,?,?,?,?,?,?)
                """,(
                int(r["id"]),
                str(r.get("codigo", "")),
                str(r["producto"]),
                str(r.get("talla", "")),
                str(r.get("color", "")),
                str(r["categoria"]),
                int(r["stock"]),
                float(r["costo"]),
                float(r["venta"])
                ))

        if "Ventas" in xls.sheet_names:
            df_ven = pd.read_excel(xls, "Ventas")
            cursor.execute("DELETE FROM ventas")
            for _,r in df_ven.iterrows():
                cursor.execute("""
                INSERT INTO ventas
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,(
                int(r["id"]),
                str(r["fecha"]),
                str(r.get("codigo", "")),
                str(r["producto"]),
                str(r.get("talla", "")),
                str(r.get("color", "")),
                int(r["cantidad"]),
                float(r["costo_ref"]),
                float(r["venta_ref"]),
                float(r["ganancia"])
                ))

        if "Gastos" in xls.sheet_names:
            df_gas = pd.read_excel(xls, "Gastos")
            cursor.execute("DELETE FROM gastos")
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
        st.sidebar.success("Backup restaurado correctamente")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")


# =========================================================
# FUNCIONES
# ========================================================= 

if "historial_stock" not in st.session_state:
    st.session_state.historial_stock = []

def cargar(): 
    return (
    pd.read_sql("SELECT * FROM inventario", conn), 
    pd.read_sql("SELECT * FROM ventas", conn), 
    pd.read_sql("SELECT * FROM gastos", conn)
    ) 

# ========================================================= 

def guardar_producto(
codigo,
producto,
talla,
color,
categoria,
stock,
costo,
venta
): 
    cursor.execute(
    "SELECT * FROM inventario WHERE producto=? AND talla=? AND color=?",
    (producto, talla, color)
    ) 
    existe = cursor.fetchone() 

    if existe: 
        nuevo_stock = existe[6] + stock 
        cursor.execute("""
        UPDATE inventario
        SET codigo=?,
        categoria=?,
        stock=?,
        costo=?,
        venta=?
        WHERE producto=? AND talla=? AND color=?
        """,(codigo, categoria, nuevo_stock, costo, venta, producto, talla, color)) 
    else: 
        cursor.execute("""
        INSERT INTO inventario
        VALUES(NULL,?,?,?,?,?,?,?,?)
        """,(codigo, producto, talla, color, categoria, stock, costo, venta)) 
    conn.commit() 

# ========================================================= 

def registrar_venta(
fecha,
producto,
talla,
color,
cantidad
): 
    cursor.execute(
    "SELECT * FROM inventario WHERE producto=? AND talla=? AND color=?",
    (producto, talla, color)
    ) 
    d = cursor.fetchone() 

    if not d:
        return False, "Producto no existe" 

    id_p, cod_p, prod_p, tall_p, col_p, cat_p, stock, costo, venta = d 

    if cantidad > stock:
        return False, f"Stock insuficiente ({stock})" 

    nuevo_stock = stock - cantidad 
    ganancia = cantidad * (venta - costo) 

    cursor.execute("""
    UPDATE inventario
    SET stock=?
    WHERE producto=? AND talla=? AND color=?
    """,(nuevo_stock, producto, talla, color)) 

    cursor.execute("""
    INSERT INTO ventas
    VALUES(NULL,?,?,?,?,?,?,?,?,?)
    """,(fecha, cod_p, producto, talla, color, cantidad, costo, venta, ganancia)) 

    conn.commit() 
    return True, "Venta registrada" 

# ========================================================= 

def registrar_gasto(fecha, concepto, monto): 
    cursor.execute("INSERT INTO gastos VALUES(NULL,?,?,?)",(fecha, concepto, monto)) 
    conn.commit() 

# ========================================================= 

def eliminar_producto(producto, talla, color): 
    cursor.execute(
    "DELETE FROM inventario WHERE producto=? AND talla=? AND color=?",
    (producto, talla, color)
    ) 
    conn.commit() 

# ========================================================= 

def eliminar_venta(id_venta): 
    cursor.execute("SELECT producto, talla, color, cantidad FROM ventas WHERE id=?",(id_venta,)) 
    venta = cursor.fetchone() 
    if venta: 
        producto, talla, color, cantidad = venta 
        cursor.execute("""
        UPDATE inventario
        SET stock = stock + ?
        WHERE producto=? AND talla=? AND color=?
        """,(cantidad, producto, talla, color)) 
        cursor.execute("DELETE FROM ventas WHERE id=?",(id_venta,)) 
        conn.commit() 

# ========================================================= 

def eliminar_gasto(id_gasto): 
    cursor.execute("DELETE FROM gastos WHERE id=?",(id_gasto,)) 
    conn.commit() 

# ========================================================= 

def deshacer_ultima_venta(): 
    cursor.execute("SELECT id FROM ventas ORDER BY id DESC LIMIT 1") 
    ultima = cursor.fetchone() 
    if ultima: eliminar_venta(ultima[0])
        
# ========================================================= 

def reducir_stock(producto, talla, color, cantidad):
    cursor.execute(
        "SELECT stock FROM inventario WHERE producto=? AND talla=? AND color=?",
        (producto, talla, color)
    )
    data = cursor.fetchone()
    if not data:
        return False, "Producto no existe"

    stock_actual = data[0] # Al ser SELECT stock solamente, el indice es 0
    if cantidad > stock_actual:
        return False, f"No hay suficiente stock ({stock_actual})"

    st.session_state.historial_stock.append((producto, talla, color, stock_actual))
    nuevo_stock = stock_actual - cantidad

    cursor.execute("""
        UPDATE inventario
        SET stock=?
        WHERE producto=? AND talla=? AND color=?
    """, (nuevo_stock, producto, talla, color))
    conn.commit()
    return True, "Stock reducido"

# ========================================================= 

def deshacer_stock():
    if not st.session_state.historial_stock:
        return False, "No hay acciones para deshacer"
    producto, talla, color, stock_anterior = st.session_state.historial_stock.pop()
    cursor.execute("""
        UPDATE inventario
        SET stock=?
        WHERE producto=? AND talla=? AND color=?
    """, (stock_anterior, producto, talla, color))
    conn.commit()
    return True, "Acción deshecha"

# =========================================================

def limpiar_erp():
    cursor.execute("DELETE FROM inventario")
    cursor.execute("DELETE FROM ventas")
    cursor.execute("DELETE FROM gastos")
    conn.commit()
        

# =========================================================
# DATOS
# ========================================================= 

inv, ven, gas = cargar() 

# =========================================================
# TITULO
# ========================================================= 

st.markdown("<h1 style='text-align:center;'>🌷 Tulip ERP</h1>", unsafe_allow_html=True) 

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

        producto_final = ""
        talla_final = ""
        color_final = ""
        categoria0 = ""
        codigo_final = ""

        if modo == "Existente":
            if not inv.empty:
                inv["display"] = inv["producto"] + " (" + inv["talla"] + " - " + inv["color"] + ")"
                seleccion = st.selectbox("Selecciona producto existente", inv["display"])
                fila = inv[inv["display"] == seleccion].iloc[0]
                producto_final = fila["producto"]
                talla_final = fila["talla"]
                color_final = fila["color"]
                codigo_final = str(fila["codigo"])
                categoria0 = str(fila["categoria"]) if pd.notna(fila["categoria"]) else ""
            else:
                st.warning("No hay productos en inventario")
        else:
            codigo_final = st.text_input("Código de Producto")
            producto_final = st.text_input("Nuevo Producto")
            talla_final = st.text_input("Talla")
            color_final = st.text_input("Color")

        if modo == "Existente" and producto_final:
            st.text(f"Código: {codigo_final}")
            categoria = st.text_input("Categoria", value=categoria0, disabled=True)
        else:
            categoria = st.text_input("Categoria")

        c1, c2, c3 = st.columns(3)
        stock = c1.number_input("Stock", min_value=0)
        costo = c2.number_input("Costo", min_value=0.0)
        venta = c3.number_input("Venta", min_value=0.0)

        if st.form_submit_button("Guardar"):
            guardar_producto(codigo_final, producto_final.title(), talla_final.upper(), color_final.title(), categoria, stock, costo, venta)
            st.success("Producto guardado")
            st.rerun()

    st.dataframe(inv, use_container_width=True)

    st.subheader("📉 Reducir Stock")
    if not inv.empty:
        producto_r_display = st.selectbox("Seleccionar variante para reducir", inv["display"], key="reduce_stock")
        fila_r = inv[inv["display"] == producto_r_display].iloc[0]
        cantidad_r = st.number_input("Cantidad a reducir", min_value=1)
        if st.button("Reducir stock"):
            ok, msg = reducir_stock(fila_r["producto"], fila_r["talla"], fila_r["color"], cantidad_r)
            if ok: st.success(msg); st.rerun()
            else: st.error(msg)
    
    st.subheader("↩ Deshacer acción")
    if st.button("Deshacer último cambio"):
        ok, msg = deshacer_stock()
        if ok: st.success(msg); st.rerun()
        else: st.warning(msg)

    st.subheader("🗑 Eliminar Producto")
    if not inv.empty:
        producto_eliminar_display = st.selectbox("Seleccionar variante a eliminar", inv["display"], key="eliminar")
        fila_e = inv[inv["display"] == producto_eliminar_display].iloc[0]
        confirmar = st.checkbox("Estoy seguro de eliminar")
        if st.button("Eliminar"):
            if confirmar:
                eliminar_producto(fila_e["producto"], fila_e["talla"], fila_e["color"])
                st.success("Variante eliminada")
                st.rerun()
            else: st.warning("Debes confirmar")      
                    
# =========================================================
# VENTAS
# ========================================================= 

with tab2: 
    st.subheader("🛒 Ventas") 
    if not inv.empty: 
        with st.form("ventas_form"): 
            inv["v_display"] = inv["producto"] + " (" + inv["talla"] + " - " + inv["color"] + ")"
            producto_v_display = st.selectbox("Producto", inv["v_display"]) 
            fila_v = inv[inv["v_display"] == producto_v_display].iloc[0]
            st.info(f"Stock disponible: {fila_v['stock']} | Código: {fila_v['codigo']}") 

            cantidad = st.number_input("Cantidad", min_value=1) 
            fecha = st.date_input("Fecha", datetime.now()) 
            if st.form_submit_button("Vender"): 
                ok, msg = registrar_venta(str(fecha), fila_v["producto"], fila_v["talla"], fila_v["color"], cantidad) 
                if ok: st.success(msg); st.rerun() 
                else: st.error(msg) 

    st.divider() 
    st.subheader("↩ Retroceder Venta") 
    if st.button("Deshacer Última Venta"): 
        deshacer_ultima_venta() 
        st.success("Última venta eliminada") 
        st.rerun() 

    st.subheader("🗑 Eliminar Venta Específica") 
    if not ven.empty: 
        id_venta = st.selectbox("ID Venta", ven["id"]) 
        if st.button("Eliminar Venta"): 
            eliminar_venta(id_venta) 
            st.success("Venta eliminada") 
            st.rerun() 
    st.dataframe(ven, use_container_width=True) 

# =========================================================
# GASTOS
# ========================================================= 

with tab3: 
    st.subheader("💸 Gastos") 
    with st.form("gastos_form"): 
        concepto = st.text_input("Concepto") 
        monto = st.number_input("Monto", min_value=0.0) 
        fecha_g = st.date_input("Fecha", datetime.now(), key="fecha_gasto") 
        if st.form_submit_button("Guardar Gasto"): 
            registrar_gasto(str(fecha_g), concepto, monto) 
            st.success("Gasto registrado"); st.rerun() 

    st.divider() 
    if not gas.empty: 
        id_gasto = st.selectbox("ID Gasto", gas["id"]) 
        if st.button("Eliminar Gasto"): 
            eliminar_gasto(id_gasto); st.rerun()
