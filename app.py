from flask import Flask, Blueprint, render_template, request, redirect, send_file,flash,url_for
import pandas as pd
from io import BytesIO
from datetime import datetime
import psycopg2
from openpyxl import Workbook




# 📌 Conexión directa a Render PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        host="dpg-cv8oiprqf0us73bbbbfg-a.oregon-postgres.render.com",
        database="patrimonio_ppfk",
        user="patrimonio_ppfk_user",
        password="SabopRq1mqHqRXBZaZBaWsEcqfHYJWM2"
    )

# 📦 Blueprint
bp = Blueprint('altas', __name__)

@bp.route('/altas', methods=['GET', 'POST'])
def altas():
    if request.method == 'POST':
        data = request.form

        def parse_numeric(value):
            try:
                if isinstance(value, str):
                    value = value.replace("$", "").replace(",", ".").strip()
                return float(value)
            except (ValueError, TypeError):
                return 0.0

        # ✅ Recolección segura de datos
        fecha_alta = data['fecha_alta']
        cantidad = int(data['cantidad']) if data['cantidad'] else None
        concepto = data['concepto']
        disposicion = data['disposicion']
        fecha_resolucion = data.get('fecha_resolucion')  # ← nuevo campo
        valor_unitario = parse_numeric(data.get('valor_unitario'))
        valor_total = parse_numeric(data.get('valor_total'))
        causa_alta = data['causa_alta']
        codigo_presup = data['codigo_presup']
        identidad = data['identidad']
        mes_planilla = data['mes_planilla']
        anio_planilla = data['anio_planilla']
        id_rubro = int(data['id_rubro']) if data['id_rubro'] else None
        id_clase = int(data['id_clase']) if data['id_clase'] else None

        # ✅ Ejecutar INSERT con fecha_resolucion incluida
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO movimientos_altas (
                        fecha_alta, cantidad, concepto, disposicion, fecha_resolucion,
                        valor_unitario, valor_total, causa_alta,
                        codigo_presup, identidad,
                        mes_planilla, anio_planilla, id_rubro, id_clase
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fecha_alta,
                    cantidad,
                    concepto,
                    disposicion,
                    fecha_resolucion,
                    valor_unitario,
                    valor_total,
                    causa_alta,
                    codigo_presup,
                    identidad,
                    mes_planilla,
                    anio_planilla,
                    id_rubro,
                    id_clase
                ))
        return redirect('/altas')

    # GET: obtener datos con filtros
    mes = request.args.get('mes')
    anio = request.args.get('anio')

    with get_db_connection() as conn:
        query = """
            SELECT m.*, r.nombre AS rubro_nombre, c.descripcion AS clase_nombre
            FROM movimientos_altas m
            LEFT JOIN rubros r ON m.id_rubro = r.id_rubro
            LEFT JOIN clases_bienes c ON m.id_clase = c.id_clase
            WHERE 1=1
        """
        params = []

        if mes:
            query += " AND m.mes_planilla = %s"
            params.append(mes)
        if anio:
            query += " AND m.anio_planilla = %s"
            params.append(anio)

        query += " ORDER BY m.fecha_alta DESC"

        df = pd.read_sql(query, conn, params=params)

        def parse_column_numeric(col):
            return col.apply(lambda x: float(str(x).replace(",", ".").replace("$", "").strip()) if x not in [None, "", "None"] else 0.0)

        df['valor_total'] = parse_column_numeric(df['valor_total'])
        df['valor_unitario'] = parse_column_numeric(df['valor_unitario'])

        rubros = pd.read_sql("SELECT id_rubro, nombre FROM rubros ORDER BY nombre", conn)
        clases = pd.read_sql("SELECT id_clase, id_rubro, descripcion FROM clases_bienes ORDER BY descripcion", conn)

    return render_template('altas.html',
                           registros=df.to_dict(orient='records'),
                           rubros=rubros.to_dict(orient='records'),
                           clases=clases.to_dict(orient='records'))







@bp.route('/altas/editar/<int:id>', methods=['GET', 'POST'])
def editar_alta(id):
    with get_db_connection() as conn:
        if request.method == 'POST':
            data = request.form

            def parse_numeric(value):
                try:
                    if isinstance(value, str):
                        value = value.replace("$", "").replace(",", ".").strip()
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0

            cur = conn.cursor()
            cur.execute("""
                UPDATE movimientos_altas
                SET fecha_alta = %s,
                    cantidad = %s,
                    concepto = %s,
                    disposicion = %s,
                    valor_unitario = %s,
                    valor_total = %s,
                    causa_alta = %s,
                    codigo_presup = %s,
                    identidad = %s,
                    id_rubro = %s,
                    id_clase = %s
                WHERE id = %s
            """, (
                data['fecha_alta'],
                int(data['cantidad']),
                data['concepto'],
                data['disposicion'],
                parse_numeric(data['valor_unitario']),
                parse_numeric(data['valor_total']),
                data['causa_alta'],
                data['codigo_presup'],
                data['identidad'],
                int(data['id_rubro']) if data['id_rubro'] else None,
                int(data['id_clase']) if data['id_clase'] else None,
                id
            ))
            conn.commit()
            return redirect('/altas')

        # GET: cargar datos del registro a editar
        cur = conn.cursor()
        cur.execute("SELECT * FROM movimientos_altas WHERE id = %s", (id,))
        registro = cur.fetchone()

        columnas = [desc[0] for desc in cur.description]
        registro_dict = dict(zip(columnas, registro))

        rubros = pd.read_sql("SELECT id_rubro, nombre FROM rubros ORDER BY nombre", conn)
        clases = pd.read_sql("SELECT id_clase, id_rubro, descripcion FROM clases_bienes ORDER BY descripcion", conn)

    return render_template('editar_alta.html',
                           registro=registro_dict,
                           rubros=rubros.to_dict(orient='records'),
                           clases=clases.to_dict(orient='records'))






@bp.route('/altas/eliminar/<int:id>', methods=['POST'])
def eliminar_alta(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM movimientos_altas WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Registro eliminado con éxito.', 'success')
    return redirect(url_for('altas.altas'))

#@bp.route('/')
#def index():
#    return render_template('altas.html')



@bp.route("/altas/exportar_pdf")
def exportar_pdf_altas():
    mes = request.args.get("mes")
    anio = request.args.get("anio")

    if not mes or not anio:
        return "Faltan parámetros de mes o año", 400

    conn = get_db_connection()
    query = """
        SELECT m.*, r.nombre AS rubro_nombre, c.descripcion AS clase_nombre
        FROM movimientos_altas m
        LEFT JOIN rubros r ON m.id_rubro = r.id_rubro
        LEFT JOIN clases_bienes c ON m.id_clase = c.id_clase
        WHERE m.mes_planilla = %s AND m.anio_planilla = %s
        ORDER BY r.nombre, c.descripcion
    """
    df = pd.read_sql(query, conn, params=(mes, anio))

    # Extraer rubro_codigo desde codigo_presup
    df["rubro_codigo"] = df["codigo_presup"].astype(str).str.extract(r'(\d{2})')

    # Generar rubro_general a partir del código
    mapa_rubro_general = {
        "43": "MAQUINARIA Y EQUIPO",
        "44": "INMUEBLES",
        "45": "VEHÍCULOS",
        "46": "MOBILIARIO",
        "47": "EQUIPO DE COMUNICACIONES",
        # agregá más si los tenés
    }
    df["rubro_general"] = df["rubro_codigo"].map(mapa_rubro_general).fillna("SIN RUBRO")

    fecha_presentacion = datetime.now().strftime("%d/%m/%Y")
    total_general = df["valor_total"].fillna(0).astype(float).sum()

    return render_template("formato_oficial_altas.html",
                           registros=df.to_dict(orient="records"),
                           mes=mes,
                           anio=anio,
                           fecha_presentacion=fecha_presentacion,
                           total_general=total_general)




# 🚀 Crear app y registrar blueprint
app = Flask(__name__)
app.secret_key = 'clave-secreta-segura-123'  # 🔐 solo esta instancia
app.register_blueprint(bp)

# ▶️ Ejecutar con python app.py
if __name__ == '__main__':
    app.run(debug=True)
