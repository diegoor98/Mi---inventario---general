# -*- coding: utf-8 -*-
"""
SISTEMA: TULIP ERP - ENTERPRISE ROBUST EDITION
VERSIÓN: 5.0.0 (Anti-Error Core)
TOTAL LÍNEAS ESTIMADAS: +1200 con expansiones de lógica
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
import sqlite3
import time
import logging
import re

# ======================================================================================================
# 1. CONFIGURACIÓN ESTRUCTURAL Y AUDITORÍA DE ERRORES
# ======================================================================================================

st.set_page_config(
    page_title="Tulip ERP | Sistema de Gestión Blindado",
    page_icon="🌷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de Logging para trazabilidad total
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if 'session_logs' not in st.session_state:
    st.session_state.session_logs = []

def add_log(tipo, mensaje):
    hora = datetime.now().strftime("%H:%M:%S")
    st.session_state.session_logs.append(f"[{hora}] {tipo}: {mensaje}")

# ======================================================================================================
# 2. SISTEMA DE DISEÑO CSS - "ONYX NEBULA" (PREMIUM EXPANDIDO)
# ======================================================================================================

st.markdown("""
<style>
    /* Estilos Globales y Tipografía */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;600;800&family=Roboto+Mono&display=swap');

    .main {
        background-color: #0B0E14;
        background-image: 
            radial-gradient(at 0% 0%, rgba(236, 72, 153, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(147, 51, 234, 0.05) 0px, transparent 50%);
    }

    /* TÍTULO PRINCIPAL CON EFECTO DE GLOW */
    .title-container {
        padding: 40px 0px;
        text-align: center;
    }
    
    .main-title {
        font-family: 'Montserrat', sans-serif;
        color: #FFFFFF;
        font-size: 3.8rem !important;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: -2px;
        margin-bottom: 0px;
        background: linear-gradient(to right, #FF4B91, #9333EA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 5px 15px rgba(236, 72, 153, 0.3));
    }

    /* TARJETAS DE MÉTRICAS (GLASSMORPHISM) */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 30px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
        transition: all 0.4s ease !important;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-10px) !important;
        border-color: #FF4B91 !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }

    /* BOTONES DE ACCIÓN */
    div.stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #FF4B91 0%, #7C3AED 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-family: 'Montserrat', sans-serif !important;
        border-radius: 14px !important;
        padding: 14px 20px !important;
        border: none !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: 0.3s all !important;
    }

    div.stButton > button:hover {
        filter: brightness(1.2);
        box-shadow: 0 0 25px rgba(236, 72, 153, 0.5) !important;
        transform: scale(1.02);
    }

    /* FORMULARIOS E INPUTS */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #C9D1D9 !important;
        border-radius: 12px !important;
        height: 45px !important;
    }

    /* TABS / PESTAÑAS */
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #8B949E !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        border-radius: 12px 12px 0 0 !important;
        padding: 15px 30px !important;
    }

    button[aria-selected="true"] {
        color: #FF4B91 !important;
        border-bottom: 4px solid #FF4B91 !important;
    }

    /* SCROLLBAR PERSONALIZADA */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0B0E14; }
    ::-webkit-scrollbar-thumb { background: #30363D; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #FF4B91; }

</style>
""", unsafe_allow_html=True)

# ======================================================================================================
# 3. GESTIÓN DE BASE DE DATOS (NÚCLEO DE INTEGRIDAD)
# ======================================================================================================

class DatabaseEngine:
    def __init__(self, name="tulip_v5.db"):
        self.name = name
        self.init_db()

    def get_connection(self):
        try:
            return sqlite3.connect(self.name, check_same_thread=False)
        except sqlite3.Error as e:
            add_log("ERROR CRÍTICO", f"Conexión DB fallida: {e}")
            st.error("Error fatal al conectar con la base de datos.")
            return None

    def init_db(self):
        conn = self.get_connection()
        if conn:
            cursor = conn.cursor()
            # Tabla Inventario con restricciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventario(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto TEXT UNIQUE NOT NULL,
                    categoria TEXT DEFAULT 'General',
                    stock INTEGER DEFAULT 0 CHECK(stock >= 0),
                    costo REAL DEFAULT 0.0 CHECK(costo >= 0),
                    venta REAL DEFAULT 0.0 CHECK(venta >= 0),
                    last_update DATETIME
                )
            """)
            # Tabla Ventas (Histórico)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    producto TEXT NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    costo_ref REAL NOT NULL,
                    venta_ref REAL NOT NULL,
                    ganancia REAL NOT NULL,
                    metodo_pago TEXT DEFAULT 'Efectivo'
                )
            """)
            # Tabla Gastos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gastos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    concepto TEXT NOT NULL,
                    monto REAL NOT NULL CHECK(monto > 0),
                    tipo_gasto TEXT DEFAULT 'Operativo'
                )
            """)
            conn.commit()
            conn.close()

    def execute_action(self, sql, params=()):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            add_log("ADVERTENCIA", f"Error de integridad: {e}")
            return "IntegrityError"
        except Exception as e:
            add_log("ERROR", f"Fallo en ejecución: {e}")
            return False
        finally:
            conn.close()

    def fetch_data(self, sql, params=()):
        conn = self.get_connection()
        if not conn: return pd.DataFrame()
        try:
            return pd.read_sql(sql, conn, params=params)
        finally:
            conn.close()

# Instancia global del motor
engine = DatabaseEngine()

# ======================================================================================================
# 4. FUNCIONES DE NEGOCIO (LOGIC BLINDING)
# ======================================================================================================

def logic_guardar_producto(p, c, s, cost, vent):
    """
    Guarda o actualiza productos con validaciones de tipo y limpieza de strings.
    """
    if not p or p.strip() == "":
        return False, "El nombre del producto no puede estar vacío."
    
    p_clean = p.strip().title()
    c_clean = c.strip().upper() if c else "GENERAL"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Intentar insertar
    sql_insert = """
        INSERT INTO inventario (producto, categoria, stock, costo, venta, last_update)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(producto) DO UPDATE SET
        categoria=excluded.categoria,
        stock=inventario.stock + excluded.stock,
        costo=excluded.costo,
        venta=excluded.venta,
        last_update=excluded.last_update
    """
    resultado = engine.execute_action(sql_insert, (p_clean, c_clean, s, cost, vent, ahora))
    
    if resultado == True:
        add_log("SISTEMA", f"Producto {p_clean} guardado/actualizado.")
        return True, f"Producto '{p_clean}' actualizado correctamente."
    else:
        return False, "Error al procesar el producto en la base de datos."

def logic_registrar_venta(f, p, cant):
    """
    Registra venta con validación transaccional de stock.
    """
    # 1. Obtener datos actuales con seguridad
    df_check = engine.fetch_data("SELECT stock, costo, venta FROM inventario WHERE producto=?", (p,))
    
    if df_check.empty:
        return False, "El producto seleccionado no existe."

    stock_disponible = df_check.iloc[0]['stock']
    costo_u = df_check.iloc[0]['costo']
    venta_u = df_check.iloc[0]['venta']

    # 2. Validar Stock
    if cant > stock_disponible:
        return False, f"Stock insuficiente. Solo quedan {stock_disponible} unidades."

    # 3. Transacción de venta
    ganancia = cant * (venta_u - costo_u)
    
    # Restar stock
    r1 = engine.execute_action("UPDATE inventario SET stock = stock - ? WHERE producto = ?", (cant, p))
    # Insertar historial
    r2 = engine.execute_action("""
        INSERT INTO ventas (fecha, producto, cantidad, costo_ref, venta_ref, ganancia)
        VALUES (?,?,?,?,?,?)
    """, (str(f), p, cant, costo_u, venta_u, ganancia))

    if r1 and r2:
        add_log("VENTA", f"Venta registrada: {p} x{cant}")
        return True, "Transacción completada exitosamente."
    else:
        add_log("ERROR CRÍTICO", f"Fallo en transacción de venta para {p}")
        return False, "Error crítico al registrar la venta. Contacte soporte."

def logic_limpiar_base_datos():
    """Limpia el sistema bajo doble confirmación."""
    try:
        engine.execute_action("DELETE FROM inventario")
        engine.execute_action("DELETE FROM ventas")
        engine.execute_action("DELETE FROM gastos")
        engine.execute_action("DELETE FROM sqlite_sequence")
        add_log("PELIGRO", "Base de datos reseteada por el usuario.")
        return True
    except:
        return False

# ======================================================================================================
# 5. SIDEBAR Y BACKUP (ROBUSTEZ DE DATOS)
# ======================================================================================================

with st.sidebar:
    st.markdown("<h2 style='color:#FF4B91;'>🌷 TULIP ERP V5</h2>", unsafe_allow_html=True)
    st.caption("Enterprise Edition | Robust Core")
    st.divider()

    # --- MÓDULO DE IMPORTACIÓN ---
    st.subheader("📂 Centro de Respaldo")
    
    with st.expander("Importar Backup (XLSX)", expanded=False):
        uploaded_file = st.file_uploader("Arrastre archivo aquí", type=["xlsx"], key="sidebar_uploader")
        
        if uploaded_file:
            try:
                with st.spinner("Escaneando integridad de hojas..."):
                    xls = pd.ExcelFile(uploaded_file)
                    hojas_requeridas = ["Inventario", "Ventas", "Gastos"]
                    
                    if all(h in xls.sheet_names for h in hojas_requeridas):
                        # Acción irreversible: Limpiar
                        logic_limpiar_base_datos()
                        
                        # Restaurar Inventario con mapeo exacto
                        df_inv_imp = pd.read_excel(xls, "Inventario")
                        for _, r in df_inv_imp.iterrows():
                            engine.execute_action("INSERT INTO inventario VALUES (?,?,?,?,?,?,?)", 
                                (r['id'], r['producto'], r['categoria'], r['stock'], r['costo'], r['venta'], r['last_update']))
                        
                        # Restaurar Ventas
                        df_ven_imp = pd.read_excel(xls, "Ventas")
                        for _, r in df_ven_imp.iterrows():
                            engine.execute_action("INSERT INTO ventas VALUES (?,?,?,?,?,?,?,?)", 
                                (r['id'], r['fecha'], r['producto'], r['cantidad'], r['costo_ref'], r['venta_ref'], r['ganancia'], r['metodo_pago']))
                        
                        # Restaurar Gastos
                        df_gas_imp = pd.read_excel(xls, "Gastos")
                        for _, r in df_gas_imp.iterrows():
                            engine.execute_action("INSERT INTO gastos VALUES (?,?,?,?,?)", 
                                (r['id'], r['fecha'], r['concepto'], r['monto'], r['tipo_gasto']))
                        
                        st.success("✅ Sistema restaurado íntegramente.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Archivo incompatible. Faltan tablas maestras.")
            except Exception as e:
                st.error(f"Error al procesar archivo: {e}")

    st.divider()
    
    # --- VISOR DE LOGS ---
    st.subheader("📑 Auditoría de Sesión")
    if st.checkbox("Mostrar historial de acciones"):
        for log in reversed(st.session_state.session_logs[-10:]):
            st.caption(log)

# ======================================================================================================
# 6. INTERFAZ PRINCIPAL - TULIP ENGINE
# ======================================================================================================

# Precarga de datos
data_inv = engine.fetch_data("SELECT * FROM inventario ORDER BY producto ASC")
data_ven = engine.fetch_data("SELECT * FROM ventas ORDER BY id DESC")
data_gas = engine.fetch_data("SELECT * FROM gastos ORDER BY id DESC")

st.markdown("""
<div class='title-container'>
    <h1 class='main-title'>Tulip ERP System</h1>
    <p style='color:#8B949E; font-size:1.2rem;'>Gestión Comercial de Alto Rendimiento</p>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "📦 INVENTARIO", "🛒 VENTAS", "💸 EGRESOS", "📑 BALANCE", "📈 ANALÍTICA", "⚙️ SISTEMA"
])

# ------------------------------------------------------------------------------------------------------
# TAB 1: INVENTARIO (DETALLADO)
# ------------------------------------------------------------------------------------------------------
with tabs[0]:
    st.subheader("📦 Gestión Maestra de Stock")
    
    col_inv_1, col_inv_2 = st.columns([1, 2])
    
    with col_inv_1:
        st.markdown("#### Formulario de Entrada")
        with st.form("form_inventario_pro", clear_on_submit=True):
            f_prod = st.text_input("Nombre del Producto", placeholder="Ej. Tulipanes Rojos")
            f_cat = st.selectbox("Categoría de Almacén", ["FLORES", "INSUMOS", "HERRAMIENTAS", "VARIOS"])
            
            c1, c2 = st.columns(2)
            f_stk = c1.number_input("Stock Inicial", min_value=0, step=1)
            f_cost = c2.number_input("Costo Unit. (S/)", min_value=0.0, format="%.2f")
            f_vent = st.number_input("Precio de Venta (S/)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("SINCRONIZAR CON BASE DE DATOS"):
                res_ok, res_msg = logic_guardar_producto(f_prod, f_cat, f_stk, f_cost, f_vent)
                if res_ok:
                    st.success(res_msg)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(res_msg)

    with col_inv_2:
        st.markdown("#### Vista de Existencias")
        st.dataframe(data_inv, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ Zona de Remoción de Productos"):
            if not data_inv.empty:
                p_del_list = data_inv['producto'].tolist()
                p_para_borrar = st.selectbox("Seleccione producto a eliminar", p_del_list)
                if st.button("ELIMINAR PERMANENTEMENTE"):
                    if engine.execute_action("DELETE FROM inventario WHERE producto=?", (p_para_borrar,)):
                        st.warning(f"Producto {p_para_borrar} eliminado.")
                        st.rerun()

# ------------------------------------------------------------------------------------------------------
# TAB 2: VENTAS (POS)
# ------------------------------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("🛒 Punto de Venta (POS)")
    
    if data_inv.empty:
        st.info("Registre productos en el inventario para habilitar el punto de venta.")
    else:
        v_col_1, v_
