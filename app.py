import os
import boto3
import logging
from flask import Flask, render_template, request
from pymysql import connections

app = Flask(__name__)

# --- STEP 1: LOGGING ---
logging.basicConfig(level=logging.INFO)

# --- STEP 2: ENVIRONMENT VARIABLES ---
S3_URL = os.environ.get("BACKGROUND_IMAGE_URL") 
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Ivy Omondi")
DBHOST = os.environ.get("DBHOST") or "mysql-service" # Use the service name
DBUSER = os.environ.get("DBUSER")
DBPWD = os.environ.get("DBPWD")
DATABASE = os.environ.get("DATABASE") or "employees"
DBPORT = int(os.environ.get("DBPORT") or 3306)

# --- STEP 3: S3 IMAGE DOWNLOAD ---
def download_s3_image():
    if S3_URL and S3_URL.startswith("s3://"):
        logging.info(f"Background Image URL: {S3_URL}")
        try:
            path_parts = S3_URL.replace("s3://", "").split("/", 1)
            bucket_name = path_parts[0]
            file_key = path_parts[1]

            s3 = boto3.client('s3')
            os.makedirs("static", exist_ok=True)
            # Save as static/bg.jpg
            s3.download_file(bucket_name, file_key, "static/bg.jpg")
            logging.info("Successfully downloaded background image from S3.")
        except Exception as e:
            logging.error(f"Error downloading from S3: {e}")

# Call this immediately so it runs even under Gunicorn/Production
download_s3_image()

# --- STEP 4: DATABASE CONNECTION ---
try:
    db_conn = connections.Connection(
        host=DBHOST,
        port=DBPORT,
        user=DBUSER,
        password=DBPWD,
        db=DATABASE
    )
    logging.info("Connected to MySQL successfully.")
except Exception as e:
    logging.error(f"Could not connect to MySQL: {e}")
    db_conn = None

# --- STEP 5: ROUTES ---

@app.route("/", methods=['GET', 'POST'])
def home():
    # Using addemp.html as your main landing page
    return render_template('addemp.html', name=STUDENT_NAME)

@app.route("/about")
def about():
    return render_template('about.html', name=STUDENT_NAME)

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = f"{first_name} {last_name}"
        return render_template('addempoutput.html', name=emp_name)
    except Exception as e:
        logging.error(e)
        return "Error adding employee."
    finally:
        cursor.close()

@app.route("/getemp")
def GetEmp():
    return render_template("getemp.html")

@app.route("/fetchdata", methods=['POST'])
def FetchData():
    emp_id = request.form['emp_id']
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()
    try:
        cursor.execute(select_sql, (emp_id,))
        result = cursor.fetchone()
        if result:
            output = {
                "emp_id": result[0],
                "first_name": result[1],
                "last_name": result[2],
                "primary_skills": result[3],
                "location": result[4]
            }
        else:
            output = {"emp_id": "Not Found"}
    except Exception as e:
        logging.error(e)
        output = {"emp_id": "Error fetching data"}
    finally:
        cursor.close()
    return render_template("getempoutput.html", **output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)