from _mysql_connector import MySQL
from flask import Flask, render_template, redirect, url_for, request, session, flash
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from waitress import serve
import logging
import bcrypt
from passlib.hash import sha256_crypt


import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'sumanth'  # Change this to a secure secret key

# Configure the logger
logging.basicConfig(level=logging.INFO)

# Configure MySQL
app.config['MYSQL_HOST'] = "rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com"
app.config['MYSQL_USER'] = "masterUsername"
app.config['MYSQL_PASSWORD'] = "qwerty#123"
app.config['MYSQL_DB'] = "database"
app.config['MYSQL_PORT'] = 3306

mysql = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB'],
    port=app.config['MYSQL_PORT'],
    cursorclass=pymysql.cursors.DictCursor
)


def create_tables():
    try:
        # Create a connection and cursor
        connection = pymysql.connect(
            host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
            user="masterUsername", password="qwerty#123", database="database"
        )
        cursor = connection.cursor()

        # Attempt to create the doctor table only if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctor (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        ''')

        # Attempt to create the patient table only if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                age INT NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        ''')

        # Attempt to create the appointments table only if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_email VARCHAR(255),
                date DATE,
                time TIME,
                FOREIGN KEY (patient_email) REFERENCES patient(email)
            )
        ''')

        print("Tables created successfully.")

        # Commit the changes and close the connection
        connection.commit()
        cursor.close()
        connection.close()

    except pymysql.err.InternalError as e:
        # Handle other potential errors
        print("Error creating tables:", e)

    except Exception as e:
        print("Error creating tables:", e)

# Call the create_tables function
create_tables()

def get_doctors_from_database():
    connection = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",user="masterUsername", password="qwerty#123", database="database")
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM doctor")
    doctors = cursor.fetchall()
    connection.close()
    return doctors


@app.route('/')
def home():
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Check if a patient is logged in
    if 'user' in session:
        session.pop('user', None)
        session.pop('email', None)
    # Check if a doctor is logged in
    elif 'doctor_id' in session:
        session.pop('doctor_id', None)
        session.pop('doctor_email', None)

    # Redirect to the home page
    return redirect(url_for('home'))

@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    # Check if the user is logged in
    if 'user' not in session:
        flash("You need to log in first.", "danger")
        return redirect(url_for('patient_login'))

    if request.method == 'POST':
        try:
            # Get the appointment details from the form
            patient_email = session['user']['email']
            date = request.form.get('date')
            time = request.form.get('time')

            # Connect to the database
            connection = pymysql.connect(
                host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                user="masterUsername",
                password="qwerty#123",
                database="database"
            )

            with connection.cursor() as cursor:
                # Insert the appointment into the database
                q = "INSERT INTO appointments (patient_email, date, time) VALUES (%s, %s, %s)"
                cursor.execute(q, (patient_email, date, time))

            # Commit the changes to the database
            connection.commit()

            # Close the cursor and connection
            cursor.close()
            connection.close()

            # Optionally, you can redirect to a success page or display a success message
            flash("Appointment booked successfully", "success")
            return redirect(url_for('patient_appointments'))

        except Exception as e:
            # Handle any exceptions, such as database errors
            print("Error:", e)
            # Optionally, you can redirect to an error page or display an error message
            flash("An error occurred. Please try again.", "danger")
            return render_template('error.html', message="An error occurred.")

    # Render the book appointment page
    return render_template('book_appointment.html')

@app.route('/doctor-register', methods=['GET', 'POST'], endpoint='doctor_register')
def doctor_register():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('Name')
        email = request.form.get('Email')
        phone = request.form.get('Phone')
        password = request.form.get('Password')

        try:
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Create a cursor
            cur = mysql.cursor()

            # Perform the INSERT operation with hashed password
            q = "INSERT INTO doctor (name, email, phone, password) VALUES (%s, %s, %s, %s)"
            cur.execute(q, (name, email, phone, hashed_password))

            # Commit the changes to the database
            mysql.commit()

            # Close the cursor
            cur.close()

            # Redirect to a success page or another appropriate route
            flash("Registration successful", "success")
            return redirect(url_for('doctor_login'))
        except Exception as e:
            # Handle any exceptions, such as database errors
            print("Error:", e)
            # Optionally, you can redirect to an error page or display an error message
            flash("An error occurred during registration. Please try again.", "danger")
            return render_template('error.html', message="An error occurred during registration.")

    # Render the registration form
    return render_template('doctor_register.html')

@app.route('/doctor-login', methods=['GET', 'POST']) #checking the code above is the original code
def doctor_login():
    conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                           user="masterUsername", password="qwerty#123", database="database")
    cur = conn.cursor()

    q_doctor = "SELECT * FROM doctor;"
    cur.execute(q_doctor)
    doctor_records = cur.fetchone()

    if request.method == 'POST':
        # Retrieve form data
        email = request.form.get('Email')
        password = request.form.get('Password')

        # Retrieve the hashed password from the database
        q = "SELECT id, name, email, password FROM doctor WHERE email = %s"
        cur.execute(q, (email,))
        doctor = cur.fetchone()

        # Debugging print statements
        print(f"Input email: {email}")
        print(f"Input password: {password}")
        print(f"Database password hash: {doctor['password'] if doctor else None}")

        # Check if the email exists and verify the password
        if doctor and check_password_hash(doctor['password'], password):
            # Set doctor session
            session['doctor_id'] = doctor['id']
            session['doctor_name'] = doctor['name']
            session['doctor_email'] = doctor['email']

            # Redirect to the doctor dashboard or another appropriate route
            flash('Login successful!', 'success')
            return redirect(url_for('doctor'))
        else:
            # Invalid email or password
            flash('Invalid email or password. Please try again.', 'danger')

        # Close the cursor
        cur.close()

    # Render the login form
    return render_template('doctor_login.html',doctors=doctor_records)

@app.route('/patient-register', methods=['GET', 'POST'], endpoint='patient_register')
def patient_register():
    print("Inside patient_register function")  # Add this line

    if request.method == 'POST':
        print("Handling POST request")  # Add this line
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('Name')
        email = request.form.get('Email')
        age = request.form.get('Age')
        password = request.form.get('Password')

        try:
            # Create a cursor
            cur = mysql.cursor()

            # Check if the email already exists in the database
            q_check_email = "SELECT id FROM patient WHERE email = %s"
            cur.execute(q_check_email, (email,))
            existing_patient = cur.fetchone()

            if existing_patient:
                # If email already exists, redirect to registration page with an error message
                flash("Email already exists. Please use a different email.", "danger")
                return redirect(url_for('patient_register'))

            # Perform the INSERT operation (without password hashing for now)
            q_insert_patient = "INSERT INTO patient (name, email, age, password) VALUES (%s, %s, %s, %s)"
            cur.execute(q_insert_patient, (name, email, age, password))

            # Commit the changes to the database
            mysql.commit()

            # Close the cursor
            cur.close()

            # Redirect to a success page or another appropriate route
            flash("Registration successful", "success")
            return redirect(url_for('patient_login'))

        except Exception as e:
            # Handle any exceptions, such as database errors
            print("Error:", e)

            # Rollback the changes (to maintain consistency)
            mysql.rollback()

            # Optionally, you can redirect to an error page or display an error message
            flash("An error occurred during registration. Please try again.", "danger")
            return render_template('error.html', message="An error occurred during registration.")

    # Render the registration form
    return render_template('patient_register.html')


@app.route('/patient-login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        email = request.form.get('Email')
        password = request.form.get('Password')

        # Connect to the database
        try:
            with pymysql.connect(
                    host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                    user="masterUsername",
                    password="qwerty#123",
                    database="database"
            ) as connection:
                with connection.cursor() as cursor:
                    # Retrieve the user with the given email and password (without hashing)
                    cursor.execute('SELECT * FROM patient WHERE email = %s AND password = %s', (email, password))
                    user = cursor.fetchone()

                    print("User:", user)  # Add this line for debugging

                    if user:
                        # Successful login, set the user in the session
                        session['user'] = {
                            'id': user[0],
                            'name': user[1],
                            'email': user[2],
                            'age': user[3]
                            # Add other fields as needed
                        }
                        session['email'] = user[2]
                        flash('Login successful!', 'success')
                        return redirect(url_for('patient_appointments'))  # Redirect to the book_appointment route
                    else:
                        # Invalid email or password
                        flash('Invalid email or password. Please try again.', 'danger')

        except pymysql.MySQLError as e:
            # Handle MySQL database errors
            print("MySQL Error:", e)
            flash('An error occurred. Please try again.', 'danger')

    return render_template('patient_login.html')


@app.route('/doctor', methods=["GET", "POST"], endpoint='doctor') #Issue, when doctor login by giving any login credentials getting loin
def doctor():
    # Use your existing database connection setup
    conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                           user="masterUsername", password="qwerty#123", database="database")
    cur = conn.cursor()

    # Fetch doctors' details
    q_doctor = "SELECT * FROM doctor;"
    cur.execute(q_doctor)
    doctor_records = cur.fetchall()

    # Fetch patient appointments
    q_appointments = "SELECT id, patient_email, date, time FROM appointments;"
    cur.execute(q_appointments)
    appointments = cur.fetchall()

    conn.close()  # Close the connection after fetching the records
    return render_template("doctor.html", doctors=doctor_records, appointments=appointments)

@app.route('/patient', methods=["GET", "POST"], endpoint='patient')
def patient():
    # Use your existing database connection setup
    conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                           user="masterUsername", password="qwerty#123", database="database")
    cur = conn.cursor()
    q = "select * from patient;"
    cur.execute(q)
    records = cur.fetchall()
    conn.close()  # Close the connection after fetching the records
    return render_template("patient.html", data=records)


@app.route('/adddoctor', methods=["GET", "POST"], endpoint='adddoctor')
def adddoctor():
    if request.method == "POST":
        # Use your existing database connection setup
        conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                               user="masterUsername", password="qwerty#123", database="database")
        cur = conn.cursor()
        name = request.form.get('name')
        q = f'insert into doctor(fname) values("{name}");'
        cur.execute(q)
        conn.commit()
        conn.close()  # Close the connection after executing the query
    return render_template("adddoctor.html")


@app.route('/addpatient', methods=["GET", "POST"], endpoint='addpatient')
def addpatient():
    if request.method == "POST":
        # Use your existing database connection setup
        conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                               user="masterUsername", password="qwerty#123", database="database")
        cur = conn.cursor()
        name = request.form.get('name')
        q = f'insert into patient(fname) values("{name}");'
        print(q)
        cur.execute(q)
        conn.commit()
        conn.close()  # Close the connection after executing the query
    return render_template("addpatient.html")


@app.route('/deldoctor', methods=["POST"], endpoint='deldoctor')
def deldoctor():
    if request.method == "POST":
        # Use your existing database connection setup
        conn = pymysql.connect(
            host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
            user="masterUsername", password="qwerty#123", database="database")
        cur = conn.cursor()
        name = request.form.get('name')  # Change to 'name' if that's how you identify doctors
        q = f'delete from doctor where name = "{name}";'
        cur.execute(q)
        conn.commit()
        conn.close()  # Close the connection after executing the query
    return render_template("doctor.html", data=get_doctors_from_database())

@app.route('/delpatient/<string:patient_email>', methods=["GET", "POST"], endpoint='delpatient')
def delpatient(patient_email):
    if request.method == "POST":
        try:
            # Use your existing database connection setup
            conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                                user="masterUsername", password="qwerty#123", database="database")
            cur = conn.cursor()

            # Execute the DELETE query with a parameterized query to avoid SQL injection
            q = 'DELETE FROM patient WHERE email = %s;'
            cur.execute(q, (patient_email,))

            # Commit the changes to the database
            conn.commit()

            # Close the cursor and connection
            cur.close()
            conn.close()

            # Redirect back to the patient list page
            return redirect(url_for('patient'))

        except Exception as e:
            # Handle any exceptions, such as database errors
            print("Error:", e)

            # Optionally, you can redirect to an error page or display an error message
            flash("An error occurred during deletion. Please try again.", "danger")
            return render_template('error.html', message="An error occurred during deletion.")

    return render_template("delpatient.html", patient_email=patient_email)

@app.route('/patient-appointments', endpoint='patient_appointments')
def patient_appointments():
    # Get patient email from the session
    patient_email = session.get('email')

    # Use your existing database connection setup
    conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                           user="masterUsername", password="qwerty#123", database="database")
    cur = conn.cursor()

    # Retrieve appointments for the logged-in patient
    q = "SELECT date, time FROM appointments WHERE patient_email = %s"
    cur.execute(q, (patient_email,))
    appointments = cur.fetchall()

    # Close the cursor and connection
    cur.close()
    conn.close()

    # Render the patient appointments page with the retrieved appointments
    return render_template('patient_appointments.html', appointments=appointments)

@app.route('/cancel-appointment', methods=['POST'])
def cancel_appointment():
    # Get appointment date and time from the form
    appointment_date = request.form['appointment_date']
    appointment_time = request.form['appointment_time']

    # Use your existing database connection setup
    conn = pymysql.connect(host="rds-mysql-10mintutorial.cir0zovlxdnt.us-east-1.rds.amazonaws.com",
                           user="masterUsername", password="qwerty#123", database="database")
    cur = conn.cursor()

    # Delete the appointment from the database
    q = "DELETE FROM appointments WHERE patient_email = %s AND date = %s AND time = %s"
    cur.execute(q, (session.get('email'), appointment_date, appointment_time))

    # Commit the changes and close the cursor and connection
    conn.commit()
    cur.close()
    conn.close()

    # Redirect back to the patient appointments page
    return redirect(url_for('patient_appointments'))

if __name__ == '__main__':
    app.run(debug=True)

