from flask import Flask, request, render_template, redirect, jsonify, send_file
import mysql.connector
from datetime import datetime
import csv
import io

app = Flask(__name__)

# Configuración de la base de datos
app.config.from_pyfile('config.py')

def crear_conexion():
    return mysql.connector.connect(**app.config['DB_CONFIG'])

@app.route('/')
def index():
    conn = crear_conexion()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM solicitudes ORDER BY fecha_hora DESC")
    solicitudes = cursor.fetchall()

    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM solicitudes
        GROUP BY estado
    """)
    estado_stats = {row['estado']: row['cantidad'] for row in cursor.fetchall()}

    conn.close()
    return render_template('index.html', solicitudes=solicitudes, estado_stats=estado_stats)

@app.route('/submit', methods=['POST'])
def submit():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    persona = request.form['persona']
    estado = 'Pendiente'
    fecha_hora = datetime.now()

    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO solicitudes (nombre, descripcion, persona_asignada, estado, fecha_hora)
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre, descripcion, persona, estado, fecha_hora))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    nueva_persona = request.form.get('persona')
    nuevo_estado = request.form.get('estado')
    conn = crear_conexion()
    cursor = conn.cursor()
    if nueva_persona:
        cursor.execute("UPDATE solicitudes SET persona_asignada = %s WHERE id = %s", (nueva_persona, id))
    if nuevo_estado:
        cursor.execute("UPDATE solicitudes SET estado = %s WHERE id = %s", (nuevo_estado, id))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route('/export')
def export():
    conn = crear_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, descripcion, persona_asignada, estado, fecha_hora FROM solicitudes ORDER BY fecha_hora DESC")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "Descripción", "Persona Asignada", "Estado", "Fecha y Hora"])
    for row in cursor.fetchall():
        writer.writerow(row)
    output.seek(0)
    conn.close()
    return send_file(io.BytesIO(output.read().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='solicitudes.csv')

@app.route('/persona_sugerida', methods=['POST'])
def persona_sugerida():
    descripcion = request.form.get('descripcion', '')
    descripcion_lower = descripcion.lower()

    sugerida = 'Sebastian'  # Valor por defecto
    if 'impresora' in descripcion_lower or 'papel' in descripcion_lower:
        sugerida = 'Alex'
    elif 'sistema' in descripcion_lower or 'software' in descripcion_lower or 'programa' in descripcion_lower:
        sugerida = 'Harold'

    return jsonify({'persona': sugerida})

if __name__ == '__main__':
    app.run(debug=True)



DB_CONFIG = {
    'host': '192.168.20.22',
    'user': 'root',
    'password': '',
    'database': 'soporte_ti'
}
