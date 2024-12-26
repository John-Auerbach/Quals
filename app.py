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
    total_completed = 0
    total_boxes = 0

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

            # Count completed and total boxes for overall calculation
            for topic, topic_data in progress[subject].items():
                if isinstance(topic_data, dict):
                    for category, files in topic_data.items():
                        if isinstance(files, dict):
                            total_boxes += len(files)
                            total_completed += sum(1 for completed in files.values() if completed)

        else:
            overall_progress[subject] = 0

    # Calculate overall progress percentage
    overall_percentage = int((total_completed / total_boxes) * 100) if total_boxes else 0

    return render_template("dashboard.html", subjects=subjects, overall_progress=overall_progress, overall_percentage=overall_percentage)

@app.route("/exam_topics")
def exam_topics():
    return send_from_directory(directory="study_materials", path="Exam_Topics.pdf", as_attachment=False)

@app.route("/subject/<subject>")
def subject_page(subject):
    subject_dir = os.path.join(STUDY_MATERIALS_DIR, subject.lower())
    if not os.path.exists(subject_dir):
        return "Subject not found.", 404

    topics = []
    for topic in os.listdir(subject_dir):
        topic_dir = os.path.join(subject_dir, topic)
        if os.path.isdir(topic_dir):
            categories = {"notes": [], "practice": [], "exam": []}

            for category in categories.keys():
                category_dir = os.path.join(topic_dir, category.capitalize())
                if os.path.exists(category_dir):
                    categories[category] = os.listdir(category_dir)

            if subject not in progress:
                progress[subject] = {}
            if topic not in progress[subject]:
                progress[subject][topic] = {cat: {} for cat in categories.keys()}

            for category, files in categories.items():
                if category not in progress[subject][topic]:
                    progress[subject][topic][category] = {}
                for file in files:
                    if file not in progress[subject][topic][category]:
                        progress[subject][topic][category][file] = False

            completed_files = sum(
                progress[subject][topic][cat].get(file, False)
                for cat, files in categories.items()
                for file in files
            )
            total_files = sum(len(files) for files in categories.values())
            overall_progress = int((completed_files / total_files) * 100) if total_files else 0
            progress[subject][topic]["overall"] = overall_progress

            topics.append({
                "name": topic,
                "notes": categories["notes"],
                "practice": categories["practice"],
                "exam": categories["exam"],
                "total_files": total_files,
                "completed_files": completed_files,
                "progress": overall_progress
            })

    save_progress()
    return render_template("subject.html", subject=subject, topics=topics, progress=progress)

@app.route("/download/<subject>/<topic>/<category>/<file>")
def download_file(subject, topic, category, file):
    directory = os.path.join(STUDY_MATERIALS_DIR, subject.lower(), topic, category.capitalize())
    if os.path.exists(os.path.join(directory, file)):
        return send_from_directory(directory=directory, path=file, as_attachment=False)
    else:
        return "File not found.", 404

@app.route("/update_progress", methods=["POST"])
def update_progress():
    data = request.json
    subject = data["subject"]
    topic = data["topic"]
    file = data["file"]
    category = data["category"]
    is_checked = data["isChecked"]

    if subject not in progress:
        progress[subject] = {}
    if topic not in progress[subject]:
        progress[subject][topic] = {}

    if category not in progress[subject][topic]:
        progress[subject][topic][category] = {}

    progress[subject][topic][category][file] = is_checked

    topic_dir = os.path.join(STUDY_MATERIALS_DIR, subject.lower(), topic, category.capitalize())
    if os.path.exists(topic_dir):
        total_files = sum(len(files) for files in progress[subject][topic].values() if isinstance(files, dict))
        completed_files = sum(
            1 for files in progress[subject][topic].values() if isinstance(files, dict)
            for f in files.values() if f is True
        )
        new_progress = int((completed_files / total_files) * 100) if total_files else 0
        progress[subject][topic]["overall"] = new_progress

    save_progress()
    return jsonify({"status": "success", "newProgress": progress[subject][topic]["overall"]})

if __name__ == "__main__":
    app.run(debug=True)
