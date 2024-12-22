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
    return render_template("dashboard.html", subjects=subjects)

@app.route("/subject/Fluids")
def fluids_page():
    # Custom page for Fluids
    return render_template("fluids.html")

@app.route("/subject/<subject>")
def subject_page(subject):
    if subject.lower() == "fluids":
        # Redirect to custom Fluids page
        return render_template("fluids.html")
    else:
        # Generic subject page
        subject_dir = os.path.join(STUDY_MATERIALS_DIR, subject.lower())
        if not os.path.exists(subject_dir):
            return "Subject not found.", 404

        topics = []
        for topic in os.listdir(subject_dir):
            topic_dir = os.path.join(subject_dir, topic)
            if os.path.isdir(topic_dir):
                files = os.listdir(topic_dir)

                # Ensure progress[subject][topic] is always a dictionary
                subject_progress = progress.get(subject, {})
                topic_progress = subject_progress.get(topic, {})
                if isinstance(topic_progress, int):  # If it's an int, convert it to a dictionary
                    topic_progress = {"overall": topic_progress}

                # Initialize file progress if not already present
                for file in files:
                    if file not in topic_progress:
                        topic_progress[file] = False

                # Calculate overall progress
                completed_files = sum(1 for file in files if topic_progress[file])
                overall_progress = int((completed_files / len(files)) * 100) if files else 0
                topic_progress["overall"] = overall_progress

                # Update progress dictionary
                subject_progress[topic] = topic_progress
                progress[subject] = subject_progress

                topics.append({
                    "name": topic,
                    "files": files,
                    "progress": topic_progress["overall"]
                })

        return render_template("subject.html", subject=subject, topics=topics, progress=progress)

@app.route("/download/<subject>/<topic>/<filename>")
def download_file(subject, topic, filename):
    file_path = os.path.join(STUDY_MATERIALS_DIR, subject.lower(), topic, filename)
    if os.path.exists(file_path):
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
    return "File not found.", 404

@app.route("/templates/<path:filename>")
def serve_template_files(filename):
    return send_from_directory('templates', filename)

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

    # Update file progress
    progress[subject][topic][file] = is_checked

    # Calculate new progress percentage
    topic_dir = os.path.join(STUDY_MATERIALS_DIR, subject.lower(), topic)
    if os.path.exists(topic_dir):
        total_files = len(os.listdir(topic_dir))
        completed_files = sum(1 for f in progress[subject][topic].values() if f)
        new_progress = int((completed_files / total_files) * 100) if total_files else 0
        progress[subject][topic]["overall"] = new_progress

    save_progress()
    return jsonify({"status": "success", "newProgress": new_progress})

if __name__ == "__main__":
    app.run(debug=True)
