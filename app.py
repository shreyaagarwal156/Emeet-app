from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql 
import pymysql.cursors
import bcrypt 

DB_HOST = '127.0.0.1'
DB_USER = 'root'
DB_PASSWORD = 'Root@123' 
DB_NAME = 'emeet_db'

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_emeet' 

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        raw_password = request.form['password'] 
        
        user_data = None
        user_type = None
        connection = get_db_connection()
        
        try:
            with connection.cursor() as cursor:
                
                cursor.execute('SELECT student_id AS id, first_name, email, password FROM students WHERE email = %s', (email,))
                student = cursor.fetchone()

                if student:
                    if bcrypt.checkpw(raw_password.encode('utf-8'), student['password'].encode('utf-8')):
                        user_data = student
                        user_type = 'student'

                if not user_data:
                    cursor.execute('SELECT teacher_id AS id, first_name, email, password FROM teachers WHERE email = %s', (email,))
                    teacher = cursor.fetchone()
                    
                    if teacher:
                        if bcrypt.checkpw(raw_password.encode('utf-8'), teacher['password'].encode('utf-8')):
                            user_data = teacher
                            user_type = 'teacher'
        finally:
            connection.close()

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

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        raw_password = request.form['password']
        user_type = request.form['user_type']
        
        hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())

        connection = get_db_connection()
        
        try:
            with connection.cursor() as cursor:
                # Check karo ki yeh email pehle se hai ya nahi
                cursor.execute('SELECT email FROM students WHERE email = %s UNION ALL SELECT email FROM teachers WHERE email = %s', (email, email))
                if cursor.fetchone():
                    flash('An account with this email already exists!', 'danger')
                    return redirect(url_for('register'))

                # Data ko database mein daalo
                if user_type == 'student':
                    enrollment_no = request.form['enrollment_no']
                    cursor.execute('INSERT INTO students (first_name, last_name, email, password, enrollment_no) VALUES (%s, %s, %s, %s, %s)', 
                                   (first_name, last_name, email, hashed_password, enrollment_no))
                    
                elif user_type == 'teacher':
                    department = request.form['department']
                    cursor.execute('INSERT INTO teachers (first_name, last_name, email, password, department) VALUES (%s, %s, %s, %s, %s)', 
                                   (first_name, last_name, email, hashed_password, department))
                
                connection.commit()
        finally:
            connection.close()
        
        flash('Registration Successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html', first_name=session['first_name'], user_type=session['user_type'])
    
    flash('Please login to access this page.', 'warning')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
   session.clear()
   flash('You have been logged out.', 'info')
   return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)