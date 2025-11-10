import os  # Added for environment variables
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import pymysql.cursors
import bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CONFIGURATION (MODIFIED FOR PRODUCTION) ---

# Secret key is now read from an environment variable for security
app.secret_key = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_dev') 

# Database config is now read from environment variables
# These will be set in the Render dashboard
app.config['MYSQL_HOST'] = os.environ.get('DB_HOST')
app.config['MYSQL_USER'] = os.environ.get('DB_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('DB_NAME')

# --- END OF CONFIGURATION ---


def get_db_connection_and_cursor(cursor_type=pymysql.cursors.DictCursor):
    try:
        # This function now automatically uses the environment variables 
        # set in app.config above
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=cursor_type
        )
        return connection, connection.cursor()
    except pymysql.Error as e:
        print(f"Database Connection Error: {e}")
        flash("Could not connect to the database. Please check configuration.", 'danger')
        return None, None


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        
        user_data = None
        user_type = None
        conn, cursor = get_db_connection_and_cursor()

        if conn and cursor:
            try:
                
                cursor.execute('SELECT student_id AS id, first_name, email, password FROM students WHERE email = %s', (email,))
                student = cursor.fetchone()

                if student:
                    if bcrypt.checkpw(password, student['password'].encode('utf-8')):
                        user_data = student
                        user_type = 'student'

                
                if not user_data:
                    cursor.execute('SELECT teacher_id AS id, first_name, email, password FROM teachers WHERE email = %s', (email,))
                    teacher = cursor.fetchone()
                    
                    if teacher:
                        if bcrypt.checkpw(password, teacher['password'].encode('utf-8')):
                            user_data = teacher
                            user_type = 'teacher'

            finally:
                cursor.close()
                conn.close()

            if user_data:
                
                session['loggedin'] = True
                session['id'] = user_data['id']
                session['email'] = user_data['email']
                session['first_name'] = user_data['first_name']
                session['user_type'] = user_type
                
                flash('Login Successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect Email or Password!', 'danger')

    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

# --- REGISTRATION PAGE ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        raw_password = request.form['password']
        user_type = request.form['user_type']
        
        # Validation check
        if not first_name or not last_name or not email or not raw_password:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('register'))
            
        
        hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn, cursor = get_db_connection_and_cursor(cursor_type=pymysql.cursors.Cursor)

        if conn and cursor:
            try:
                
                cursor.execute('SELECT 1 FROM students WHERE email = %s UNION ALL SELECT 1 FROM teachers WHERE email = %s', (email, email))
                if cursor.fetchone():
                    flash('An account with this email already exists!', 'danger')
                    return redirect(url_for('register'))

                
                if user_type == 'student':
                    
                    enrollment_no = request.form.get('enrollment_no')
                    if not enrollment_no:
                        flash('Student registration requires an Enrollment No.', 'danger')
                        return redirect(url_for('register'))

                    cursor.execute('INSERT INTO students (first_name, last_name, email, password, enrollment_no) VALUES (%s, %s, %s, %s, %s)', 
                                (first_name, last_name, email, hashed_password, enrollment_no))
                    
                elif user_type == 'teacher':
                    
                    department = request.form.get('department')
                    if not department:
                        flash('Teacher registration requires a Department.', 'danger')
                        return redirect(url_for('register'))

                    cursor.execute('INSERT INTO teachers (first_name, last_name, email, password, department) VALUES (%s, %s, %s, %s, %s)', 
                                (first_name, last_name, email, hashed_password, department))
                    
                conn.commit()
                flash('Registration Successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                
                print(f"Registration Error: {e}") 
                conn.rollback()
                flash(f'Registration failed: {e}', 'danger')
                return redirect(url_for('register'))
            finally:
                cursor.close()
                conn.close()
            
    return render_template('register.html')

# --- DASHBOARD REDIRECTOR ---
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        if session['user_type'] == 'student':
            return redirect(url_for('student_dashboard'))
        elif session['user_type'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
    
    flash('Please login to access this page.', 'warning')
    return redirect(url_for('login'))

# --- STUDENT DASHBOARD LOGIC ---
@app.route('/student_dashboard')
def student_dashboard():
    if 'loggedin' not in session or session['user_type'] != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    student_id = session['id']
    conn, cursor = get_db_connection_and_cursor()
    teachers = []
    my_requests = []
    
    if conn and cursor:
        try:
            
            cursor.execute("SELECT teacher_id AS id, CONCAT(first_name, ' ', last_name) AS name, department FROM teachers")
            teachers = cursor.fetchall()
            
            
            cursor.execute("""
                SELECT 
                    a.*, 
                    CONCAT(t.first_name, ' ', t.last_name) AS teacher_name,
                    t.department
                FROM appointments a
                JOIN teachers t ON a.teacher_id = t.teacher_id
                WHERE a.student_id = %s
                ORDER BY a.created_at DESC
            """, (student_id,))
            my_requests = cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('student_dashboard.html', teachers=teachers, my_requests=my_requests)


@app.route('/request_meeting', methods=['POST'])
def request_meeting():
    if 'loggedin' not in session or session['user_type'] != 'student':
        flash('Please login as a student to request a meeting.', 'danger')
        return redirect(url_for('login'))
    
    student_id = session['id']
    teacher_id = request.form['teacher_id']
    reason = request.form['reason']
    preferred_time_str = request.form['preferred_time']
    
    conn, cursor = get_db_connection_and_cursor()

    if conn and cursor:
        try:
            preferred_time = datetime.strptime(preferred_time_str, '%Y-%m-%dT%H:%M')
            
            cursor.execute(
                "INSERT INTO appointments (student_id, teacher_id, reason, preferred_time) VALUES (%s, %s, %s, %s)",
                (student_id, teacher_id, reason, preferred_time)
            )
            conn.commit()
            flash('Meeting request submitted successfully! Teacher ko notification mil gayi hogi.', 'success')
        except ValueError:
            flash('Invalid date/time format submitted.', 'danger')
        except Exception as e:
            print(f"Request Submission Error: {e}")
            conn.rollback()
            flash(f'An error occurred during request submission: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('student_dashboard'))


# --- TEACHER DASHBOARD LOGIC ---
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'loggedin' not in session or session['user_type'] != 'teacher':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    teacher_id = session['id']
    conn, cursor = get_db_connection_and_cursor()
    pending_requests = []
    all_requests = []
    
    if conn and cursor:
        try:
            
            cursor.execute("""
                SELECT 
                    a.*, 
                    CONCAT(s.first_name, ' ', s.last_name) AS student_name
                FROM appointments a
                JOIN students s ON a.student_id = s.student_id
                WHERE a.teacher_id = %s AND a.status = 'Pending'
                ORDER BY a.preferred_time ASC
            """, (teacher_id,))
            pending_requests = cursor.fetchall()
            
            
            cursor.execute("""
                SELECT 
                    a.*, 
                    CONCAT(s.first_name, ' ', s.last_name) AS student_name
                FROM appointments a
                JOIN students s ON a.student_id = s.student_id
                WHERE a.teacher_id = %s
                ORDER BY a.created_at DESC
            """, (teacher_id,))
            all_requests = cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('teacher_dashboard.html', pending_requests=pending_requests, all_requests=all_requests)


@app.route('/handle_request', methods=['POST'])
def handle_request():
    if 'loggedin' not in session or session['user_type'] != 'teacher':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))
    

    appointment_id = request.form['appointment_id']
    action = request.form['action'] 
    comment = request.form.get('teacher_comment')
    new_time_str = request.form.get('new_time') 
    
    conn, cursor = get_db_connection_and_cursor()
    
    if conn and cursor:
        try:
            if action == 'Rescheduled' and new_time_str:
                new_time = datetime.strptime(new_time_str, '%Y-%m-%dT%H:%M')
                update_query = "UPDATE appointments SET status = %s, teacher_comment = %s, preferred_time = %s WHERE appointment_id = %s AND teacher_id = %s"
                cursor.execute(update_query, (action, comment, new_time, appointment_id, session['id']))
                flash('Request approved and a new time suggested/confirmed.', 'info')
                
            elif action == 'Approved':
                update_query = "UPDATE appointments SET status = %s, teacher_comment = %s WHERE appointment_id = %s AND teacher_id = %s"
                cursor.execute(update_query, (action, comment, appointment_id, session['id']))
                flash('Request approved.', 'success')

            elif action == 'Rejected':
                update_query = "UPDATE appointments SET status = %s, teacher_comment = %s WHERE appointment_id = %s AND teacher_id = %s"
                cursor.execute(update_query, (action, comment, appointment_id, session['id']))
                flash('Request rejected.', 'danger')
                
            conn.commit()
        except ValueError:
            flash('Invalid date/time format for rescheduling.', 'danger')
        except Exception as e:
            print(f"Request Handling Error: {e}") 
            conn.rollback()
            flash(f'An error occurred during request handling: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('teacher_dashboard'))


# --- ANALYTICS ROUTE ---
@app.route('/analytics')
def analytics():
    if 'loggedin' not in session:
        flash('Please login to view analytics.', 'danger')
        return redirect(url_for('login'))
        
    user_id = session['id']
    role = session['user_type']
    
    role_field = 'teacher_id' if role == 'teacher' else 'student_id'
    
    conn, cursor = get_db_connection_and_cursor()
    status_summary = []
    monthly_trend = []
    
    if conn and cursor:
        try:
            cursor.execute(f"""
                SELECT status, COUNT(*) as count 
                FROM appointments 
                WHERE {role_field} = %s 
                GROUP BY status
            """, (user_id,))
            status_summary = cursor.fetchall()

            cursor.execute(f"""
                SELECT 
                    YEAR(created_at) as year, 
                    MONTH(created_at) as month, 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) as approved_count
                FROM appointments 
                WHERE {role_field} = %s 
                GROUP BY year, month 
                ORDER BY year DESC, month DESC
            """, (user_id,))
            monthly_trend = cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close()
    
    return render_template('analytics.html', status_summary=status_summary, monthly_trend=monthly_trend, role=role)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# The if __name__ == '__main__': block has been REMOVED
# This is correct for production, as gunicorn will run the 'app' object.
