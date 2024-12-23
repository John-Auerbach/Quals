from flask import Flask, jsonify, request, send_from_directory, render_template
import os
import json

app = Flask(__name__)

# Path to study materials
STUDY_MATERIALS_DIR = "study_materials"
PROGRESS_FILE = "progress.json"

# Load or initialize progress
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r') as file:
        progress = json.load(file)
else:
    progress = {}

def save_progress():
    with open(PROGRESS_FILE, 'w') as file:
        json.dump(progress, file, indent=4)

@app.route("/")
def dashboard():
    subjects = ["Fluids", "Math", "Dynamics", "Structures"]
    overall_progress = {}

    # Calculate overall progress for each subject
    for subject in subjects:
        if subject in progress:
            subject_progress = [
                topic_data["overall"]
                for topic, topic_data in progress[subject].items()
                if isinstance(topic_data, dict) and "overall" in topic_data
            ]
            overall_progress[subject] = (
                int(sum(subject_progress) / len(subject_progress)) if subject_progress else 0
            )
        else:
            overall_progress[subject] = 0

    return render_template("dashboard.html", subjects=subjects, overall_progress=overall_progress)

@app.route("/subject/<subject>")
def subject_page(subject):
    subject_dir = os.path.join(STUDY_MATERIALS_DIR, subject.lower())
    if not os.path.exists(subject_dir):
        return "Subject not found.", 404

    topics = []
    for topic in os.listdir(subject_dir):
        topic_dir = os.path.join(subject_dir, topic)
        if os.path.isdir(topic_dir):
            files = os.listdir(topic_dir)
            if subject not in progress:
                progress[subject] = {}
            if topic not in progress[subject]:
                progress[subject][topic] = {file: False for file in files}

            completed_files = sum(progress[subject][topic].get(file, False) for file in files)
            overall_progress = int((completed_files / len(files)) * 100) if files else 0
            progress[subject][topic]["overall"] = overall_progress

            topics.append({
                "name": topic,
                "files": files,
                "progress": overall_progress
            })

    save_progress()
    return render_template("subject.html", subject=subject, topics=topics, progress=progress)

@app.route("/download/<subject>/<topic>/<file>")
def download_file(subject, topic, file):
    directory = os.path.join(STUDY_MATERIALS_DIR, subject.lower(), topic)
    if os.path.exists(os.path.join(directory, file)):
        return send_from_directory(directory=directory, path=file, as_attachment=True)
    else:
        return "File not found.", 404

@app.route("/update_progress", methods=["POST"])
def update_progress():
    data = request.json
    subject = data["subject"]
    topic = data["topic"]
    file = data["file"]
    is_checked = data["isChecked"]

    if subject not in progress:
        progress[subject] = {}
    if topic not in progress[subject]:
        progress[subject][topic] = {}

    progress[subject][topic][file] = is_checked

    topic_dir = os.path.join(STUDY_MATERIALS_DIR, subject.lower(), topic)
    if os.path.exists(topic_dir):
        total_files = len(os.listdir(topic_dir))
        completed_files = sum(1 for f in progress[subject][topic].values() if f is True)
        new_progress = int((completed_files / total_files) * 100) if total_files else 0
        progress[subject][topic]["overall"] = new_progress

    save_progress()
    return jsonify({"status": "success", "newProgress": progress[subject][topic]["overall"]})

if __name__ == "__main__":
    app.run(debug=True)
