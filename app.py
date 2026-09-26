from flask import Flask, render_template, request
import sqlite3
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)


# --------------------------------
# Create Database
# --------------------------------

def create_database():

    connection = sqlite3.connect("monitor.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu REAL,
            memory REAL,
            response REAL,
            error REAL,
            status TEXT
        )
    """)

    connection.commit()
    connection.close()


# --------------------------------
# AI Anomaly Detection
# --------------------------------

def detect_anomaly(cpu, memory, response, error):

    connection = sqlite3.connect("monitor.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT cpu, memory, response, error
        FROM health_checks
        WHERE status = 'Healthy'
    """)

    history = cursor.fetchall()

    connection.close()


    if len(history) < 5:

        return "Not enough normal data for AI analysis"


    scaler = StandardScaler()

    normal_data = scaler.fit_transform(history)


    model = IsolationForest(
        contamination=0.1,
        random_state=42
    )


    model.fit(normal_data)


    new_data = [[cpu, memory, response, error]]

    new_data_scaled = scaler.transform(new_data)


    prediction = model.predict(new_data_scaled)


    if prediction[0] == -1:

        return "Anomaly Detected"

    else:

        return "Normal"


# --------------------------------
# Get Health Check History
# --------------------------------

def get_history():

    connection = sqlite3.connect("monitor.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM health_checks
        ORDER BY id DESC
    """)

    history = cursor.fetchall()

    connection.close()

    return history


# --------------------------------
# Home Page
# --------------------------------

@app.route("/")
def home():

    history = get_history()


    if history:

        latest = history[0]

        cpu = latest[1]
        memory = latest[2]
        response = latest[3]
        error = latest[4]
        status = latest[5]


        # --------------------------------
        # Health Analysis
        # --------------------------------

        if status == "Healthy":

            health_analysis = (
                "The deployment appears to be operating normally."
            )


        elif status == "Warning":

            health_analysis = (
                "The deployment shows signs of increasing load."
            )


        else:

            health_analysis = (
                "Serious performance problems detected."
            )


        # --------------------------------
        # AI Analysis
        # --------------------------------

        ai_result = detect_anomaly(
            cpu,
            memory,
            response,
            error
        )


    else:

        cpu = 0
        memory = 0
        response = 0
        error = 0
        status = "No Data"

        health_analysis = (
            "No health check has been performed yet."
        )

        ai_result = "No AI analysis yet"


    return render_template(
        "index.html",
        history=history,
        cpu=cpu,
        memory=memory,
        response=response,
        error=error,
        status=status,
        health_analysis=health_analysis,
        ai_result=ai_result
    )


# --------------------------------
# Check Deployment Health
# --------------------------------

@app.route("/check", methods=["POST"])
def check_health():

    cpu = float(request.form["cpu"])
    memory = float(request.form["memory"])
    response = float(request.form["response"])
    error = float(request.form["error"])


    # --------------------------------
    # AI Anomaly Detection
    # --------------------------------

    ai_result = detect_anomaly(
        cpu,
        memory,
        response,
        error
    )


    # --------------------------------
    # Determine Health Status
    # --------------------------------

    if cpu > 80 or memory > 80 or response > 1000 or error > 5:

        status = "Critical"

        health_analysis = (
            "Serious performance problems detected."
        )


    elif cpu > 60 or memory > 60 or response > 700 or error > 2:

        status = "Warning"

        health_analysis = (
            "The deployment shows signs of increasing load."
        )


    else:

        status = "Healthy"

        health_analysis = (
            "The deployment appears to be operating normally."
        )


    # --------------------------------
    # Save Result
    # --------------------------------

    connection = sqlite3.connect("monitor.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO health_checks
        (cpu, memory, response, error, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        cpu,
        memory,
        response,
        error,
        status
    ))

    connection.commit()
    connection.close()


    # --------------------------------
    # Return Dashboard
    # --------------------------------

    return render_template(
        "index.html",
        history=get_history(),
        cpu=cpu,
        memory=memory,
        response=response,
        error=error,
        status=status,
        health_analysis=health_analysis,
        ai_result=ai_result
    )


# --------------------------------
# Start Flask Application
# --------------------------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)