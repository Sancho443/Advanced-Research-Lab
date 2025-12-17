# vulnerable_app.py
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Database of "Students"
DATABASE = {
    "100": {"id": 100, "name": "Sanchez", "role": "Hacker", "gpa": 4.0},
    "101": {"id": 101, "name": "Harry Maguire", "role": "Defender", "gpa": 1.2},
    "102": {"id": 102, "name": "Pep Guardiola", "role": "Manager", "gpa": 3.9},
    "103": {"id": 103, "name": "Darwin Nunez", "role": "Striker", "gpa": 2.5}
}

@app.route('/')
def home():
    # Hidden link for the Detector to find
    return '<html><body><h1>Welcome to MMUST Portal</h1><a href="/api/student/100">View My Profile</a></body></html>'

@app.route('/api/student/<user_id>', methods=['GET'])
def get_student(user_id):
    # AUTH CHECK: Just checks if a cookie exists (Weak Auth)
    if not request.cookies.get("session_token"):
        return jsonify({"error": "Unauthorized"}), 401

    # VULNERABILITY: No check if session_token belongs to user_id (IDOR!)
    student = DATABASE.get(str(user_id))
    
    if student:
        return jsonify(student) # 200 OK + Data
    else:
        return jsonify({"error": "Student not found"}), 404

if __name__ == '__main__':
    print("⚽ Training Ground Started on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

    #python hunter.py -u http://127.0.0.1:5000/ --cookie "session_token=valid" --baseline-url http://127.0.0.1:5000/api/student/100