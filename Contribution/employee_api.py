from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Hardcoded secrets (Agent should scream at this)
API_SECRET_KEY = "sk_live_9876543210qwertyuiop_do_not_share"
DB_PATH = "company_data.db"

# Global database connection shared across all requests
# This will cause threading issues and SQLite locked database errors
db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)

@app.route('/api/v1/employees', methods=['GET'])
def get_employees():
    department = request.args.get('department')
    cursor = db_conn.cursor()
    
    if department:
        # CRITICAL: Classic SQL Injection vulnerability.
        # Malicious input like: ' OR '1'='1 
        # could expose the entire database.
        query = f"SELECT * FROM employees WHERE department = '{department}'"
        cursor.execute(query)
    else:
        cursor.execute("SELECT * FROM employees")
        
    results = cursor.fetchall()
    
    return jsonify({"data": results, "count": len(results)})

@app.route('/api/v1/employees/add', methods=['POST'])
def add_employee():
    data = request.json
    
    # Missing input validation: Will throw an unhandled KeyError 
    # and crash the request if any of these are missing in the payload
    name = data['name']
    age = data['age']
    department = data['department']
    
    try:
        cursor = db_conn.cursor()
        # Another SQL Injection, plus vulnerable to type mismatch errors
        cursor.execute(
            f"INSERT INTO employees (name, age, department) VALUES ('{name}', {age}, '{department}')"
        )
        db_conn.commit()
        return jsonify({"status": "success", "message": "Employee added"}), 201
        
    except Exception as e:
        # Information Leak: Returning raw database exception strings 
        # directly to the API consumer gives attackers DB schema details.
        return jsonify({"status": "error", "error_detail": str(e)}), 500

if __name__ == "__main__":
    # Running the built-in Flask dev server in production-like binding (0.0.0.0) 
    # with Debug=True is a massive security risk.
    app.run(host='0.0.0.0', port=8080, debug=True)