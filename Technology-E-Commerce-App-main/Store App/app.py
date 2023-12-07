from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Krishna15!'
app.config['MYSQL_DB'] = 'abc'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

class MaintenanceRequest:
    def __init__(self, **kwargs):
        self.request_id = kwargs.get('request_id', str(uuid.uuid4())[:8])
        self.apartment_number = kwargs.get('apartment_number', '')
        self.problem_area = kwargs.get('problem_area', '')
        self.problem_description = kwargs.get('problem_description', '')
        self.date_time = kwargs.get('date_time', datetime.now())
        self.photo = kwargs.get('photo', None)
        self.status = kwargs.get('status', 'pending')

class Manager:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Tenant:
    def __init__(self, tenant_id, name, phone, email, check_in_date, apartment_number):
        self.tenant_id = tenant_id
        self.name = name
        self.phone = phone
        self.email = email
        self.check_in_date = check_in_date
        self.apartment_number = apartment_number

tenants = []  # Store tenant objects in a list

# Create the table if it doesn't exist
with app.app_context():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_requests (
            request_id VARCHAR(8) PRIMARY KEY,
            apartment_number VARCHAR(255) NOT NULL,
            problem_area VARCHAR(255) NOT NULL,
            problem_description TEXT NOT NULL,
            date_time DATETIME NOT NULL,
            photo VARCHAR(255),
            status VARCHAR(50) NOT NULL
        )
    ''')
    cursor.close()
    mysql.connection.commit()

@app.route('/')
def index():
    try:
        if session.get('is_manager'):
            return render_template('manager_dashboard.html')
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM maintenance_requests")
            requests = [MaintenanceRequest(**row) for row in cursor.fetchall()]
            cursor.close()

            return render_template('index.html', requests=requests, tenants=tenants)
    except Exception as e:
        return f"Error rendering template: {e}"


@app.route('/submit_request', methods=['POST'])
def submit_request():
    try:
        apartment_number = request.form['apartment_number']
        problem_area = request.form['problem_area']
        problem_description = request.form['problem_description']
        photo = request.form['photo'][:255] if 'photo' in request.form else None

        request_obj = MaintenanceRequest(apartment_number=apartment_number, problem_area=problem_area,
                                         problem_description=problem_description, photo=photo)
        
        # Insert into the database
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO maintenance_requests 
            (request_id, apartment_number, problem_area, problem_description, date_time, photo, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (request_obj.request_id, request_obj.apartment_number, request_obj.problem_area,
              request_obj.problem_description, request_obj.date_time, request_obj.photo, request_obj.status))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('index'))
    except Exception as e:
        return f"Error submitting request: {e}"


@app.route('/browse_requests', methods=['POST'])
def browse_requests():
    try:
        apartment_filter = request.form.get('filter_apartment', '')
        area_filter = request.form.get('filter_area', '')
        start_date_filter = request.form.get('filter_date_range_start', '')
        end_date_filter = request.form.get('filter_date_range_end', '')
        status_filter = request.form.get('filter_status', '')

        # Construct the SQL query based on the filters
        query = "SELECT * FROM maintenance_requests WHERE 1=1"
        params = []

        if apartment_filter:
            query += " AND apartment_number = %s"
            params.append(apartment_filter)

        if area_filter:
            query += " AND problem_area = %s"
            params.append(area_filter)

        if start_date_filter:
            query += " AND date_time >= %s"
            params.append(start_date_filter)

        if end_date_filter:
            query += " AND date_time <= %s"
            params.append(end_date_filter)

        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)

        cursor = mysql.connection.cursor()
        cursor.execute(query, tuple(params))
        maintenance_requests = [MaintenanceRequest(**row) for row in cursor.fetchall()]
        cursor.close()

        return render_template('index.html', maintenance_requests=maintenance_requests)
    except Exception as e:
        return f"Error browsing requests: {e}"
    

    # Add this route to your Flask app
@app.route('/update_status', methods=['POST'])
def update_status():
    try:
        request_id = request.form['request_id']
        new_status = request.form['new_status']

        # Update the status in the database
        cursor = mysql.connection.cursor()
        cursor.execute('''
            UPDATE maintenance_requests
            SET status = %s
            WHERE request_id = %s
        ''', (new_status, request_id))
        mysql.connection.commit()
        cursor.close()

        flash(f"Status updated successfully for request ID {request_id}", 'success')
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error updating status: {e}"
    
# Add Tenant route
@app.route('/add_tenant', methods=['POST'])
def add_tenant():
    try:
        tenant_name = request.form['tenant_name']
        tenant_phone = request.form['tenant_phone']
        tenant_email = request.form['tenant_email']
        check_in_date = request.form['check_in_date']
        apartment_number = request.form['apartment_number']

        # Generate a unique ID for the new tenant (you can use a UUID for this)
        new_tenant_id = str(uuid.uuid4())[:8]

        new_tenant = Tenant(
            tenant_id=new_tenant_id,
            name=tenant_name,
            phone=tenant_phone,
            email=tenant_email,
            check_in_date=check_in_date,
            apartment_number=apartment_number
        )

        tenants.append(new_tenant)

        return redirect(url_for('index'))
    except Exception as e:
        return f"Error adding tenant: {e}"

# Move Tenant route
@app.route('/move_tenant', methods=['POST'])
def move_tenant():
    try:
        tenant_id_move = request.form['tenant_id_move']
        new_apartment_number = request.form['new_apartment_number']

        # Find the tenant by ID
        tenant_to_move = next((tenant for tenant in tenants if tenant.tenant_id == tenant_id_move), None)

        if tenant_to_move:
            tenant_to_move.apartment_number = new_apartment_number

        return redirect(url_for('index'))
    except Exception as e:
        return f"Error moving tenant: {e}"

# Delete Tenant route
@app.route('/delete_tenant', methods=['POST'])
def delete_tenant():
    try:
        tenant_id_delete = request.form['tenant_id_delete']

        # Remove the tenant by ID
        tenants[:] = [tenant for tenant in tenants if tenant.tenant_id != tenant_id_delete]

        return redirect(url_for('index'))
    except Exception as e:
        return f"Error deleting tenant: {e}"


if __name__ == '__main__':
    app.run(debug=True)