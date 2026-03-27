import os
import boto3
import logging
import random
from flask import Flask, render_template, request
from pymysql import connections

app = Flask(__name__)

# --- STEP 1: LOGGING CONFIGURATION (Requirement) ---
logging.basicConfig(level=logging.INFO)

# --- STEP 2: ENVIRONMENT VARIABLES (ConfigMap/Secrets) ---
S3_URL = os.environ.get("BACKGROUND_IMAGE_URL") # s3://bucket-name/image.jpg
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Student")
DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER")
DBPWD = os.environ.get("DBPWD")
DATABASE = os.environ.get("DATABASE") or "employees"
DBPORT = int(os.environ.get("DBPORT") or 3306)

# --- STEP 3: S3 IMAGE DOWNLOAD LOGIC (Requirement) ---
def download_s3_image():
    if S3_URL and S3_URL.startswith("s3://"):
        logging.info(f"Background Image URL from ConfigMap: {S3_URL}") # Requirement
        try:
            # Split s3://bucket/key
            path_parts = S3_URL.replace("s3://", "").split("/", 1)
            bucket_name = path_parts[0]
            file_key = path_parts[1]

            s3 = boto3.client('s3')
            # Ensure static folder exists
            os.makedirs("static", exist_ok=True)
            # Save to static/bg.jpg so HTML can find it
            s3.download_file(bucket_name, file_key, "static/bg.jpg")
            logging.info("Successfully downloaded background image from S3.")
        except Exception as e:
            logging.error(f"Error downloading from S3: {e}")

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

# --- STEP 5: ROUTES ---

@app.route("/", methods=['GET', 'POST'])
def home():
    # Requirement: Pass name from ConfigMap to template
    return render_template('addemp.html', name=STUDENT_NAME)

@app.route("/about", methods=['GET','POST'])
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
    finally:
        cursor.close()
    return render_template('addempoutput.html', name=emp_name)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("getemp.html")

@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
    cursor = db_conn.cursor()
    try:
        cursor.execute(select_sql, (emp_id))
        result = cursor.fetchone()
        output = {
            "emp_id": result[0],
            "first_name": result[1],
            "last_name": result[2],
            "primary_skills": result[3],
            "location": result[4]
        }
    except Exception as e:
        logging.error(e)
        output = {"emp_id": "Not Found"}
    finally:
        cursor.close()

    return render_template("getempoutput.html", **output)

# --- STEP 6: EXECUTION ---
if __name__ == '__main__':
    # Download image before starting server
    download_s3_image()
    # Requirement: Run on Port 81
    app.run(host='0.0.0.0', port=81, debug=True)