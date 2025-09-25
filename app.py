# app.py
from flask import Flask, request, jsonify, render_template
import pandas as pd
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DB_FILE = "conciliacion.db"

# --- Función para inicializar la base de datos ---
def init_db():
    if not os.path.exists(DB_FILE):
        print("Creando la base de datos...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE conciliacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                colectiva TEXT NOT NULL,
                banco TEXT,
                cuenta TEXT,
                retiros_banco_no_conta REAL,
                depositos_conta_no_banco REAL,
                depositos_banco_no_conta REAL,
                saldo_contabilidad REAL,
                saldo_conciliado REAL,
                tipo_cuenta TEXT,
                UNIQUE(fecha, colectiva)
            );
        """)
        conn.commit()
        conn.close()
        print("Base de datos y tabla creadas.")

# --- Rutas de la aplicación ---

# Ruta principal que muestra la interfaz
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para subir y procesar el archivo Excel
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400
    
    file = request.files['file']
    month_date_str = request.form['month_date'] # Ej: '2025-09'
    
    if file.filename == '' or month_date_str == '':
        return jsonify({"error": "Falta el archivo o la fecha"}), 400

    try:
        month_date = datetime.strptime(month_date_str + '-01', '%Y-%m-%d').date()
        df = pd.read_excel(file)
        
        # Asegúrate de que los nombres de columna en tu Excel coincidan exactamente
        # con las llaves usadas aquí (ej. df['Colectiva'], df['Banco'])
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        for _, row in df.iterrows():
            colectiva_id = str(row['Colectiva'])
            
            # Usamos INSERT OR REPLACE para simplificar: si ya existe un registro
            # para esa fecha y colectiva, lo reemplaza. Si no, lo inserta.
            cursor.execute("""
                INSERT OR REPLACE INTO conciliacion (fecha, colectiva, banco, cuenta, retiros_banco_no_conta, depositos_conta_no_banco, depositos_banco_no_conta, saldo_contabilidad, saldo_conciliado, tipo_cuenta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                month_date,
                colectiva_id,
                row.get('Banco'),
                str(row.get('Cuenta')),
                row.get('Retiros banco no conta', 0),
                row.get('Depositos conta no Banco', 0),
                row.get('Depositos banco no conta', 0),
                row.get('Saldo Contabilidad', 0),
                row.get('Saldo Conciliado', 0),
                row.get('Tipo de Cuenta')
            ))
            
        conn.commit()
        conn.close()
        return jsonify({"message": f"Datos del {month_date_str} guardados correctamente."}), 200

    except Exception as e:
        return jsonify({"error": f"Error al procesar el archivo: {e}"}), 500

# Ruta para obtener datos para la tabla y la gráfica
@app.route('/get_data')
def get_data():
    colectiva_id = request.args.get('colectiva')
    if not colectiva_id:
        return jsonify({"error": "Se requiere una 'Colectiva'"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT fecha, saldo_contabilidad, saldo_conciliado
        FROM conciliacion
        WHERE colectiva = ?
        ORDER BY fecha ASC
    """, (colectiva_id,))
    
    data = cursor.fetchall()
    conn.close()
    
    # Formatear datos para la gráfica
    chart_data = {
        "labels": [row[0] for row in data],
        "saldoContabilidad": [row[1] for row in data],
        "saldoConciliado": [row[2] for row in data]
    }
    
    return jsonify(chart_data)


if __name__ == '__main__':
    init_db() # Llama a la función para crear la BD al iniciar
    app.run(debug=True)