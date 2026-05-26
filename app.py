from flask import Flask, render_template, request, redirect
from markupsafe import Markup, escape

app = Flask(__name__)

FILE_NAME = "notes.csv"


# ------------------------
# FILE HANDLING
# ------------------------

def read_notes():
    try:
        with open(FILE_NAME, "r") as file:
            return file.readlines()
    except FileNotFoundError:
        return []


def save_notes(notes):
    with open(FILE_NAME, "w") as file:
        file.writelines(notes)


# ------------------------
# PARSE NOTES
# ------------------------

def parse_note(raw_note, index):
    note = raw_note.strip()

    if note.startswith("[") and "]" in note:
        end = note.index("]")
        tag = note[1:end]
        text = note[end + 1:].strip()
    else:
        tag = "untagged"
        text = note

    return {
        "index": index,
        "tag": tag,
        "text": text,
        "raw": raw_note,
    }


# ------------------------
# HIGHLIGHT SEARCH
# ------------------------

def highlight_text(text, search):
    if search == "":
        return escape(text)

    lower_text = text.lower()
    lower_search = search.lower()
    start = lower_text.find(lower_search)

    if start == -1:
        return escape(text)

    end = start + len(search)

    return Markup(
        escape(text[:start]) +
        Markup("<mark>") +
        escape(text[start:end]) +
        Markup("</mark>") +
        escape(text[end:])
    )


# ------------------------
# GROUP NOTES (FIXED MISSING FUNCTION)
# ------------------------

def group_notes_by_tag(notes):
    groups = {}

    for note in notes:
        tag = note["tag"]

        if tag not in groups:
            groups[tag] = []

        groups[tag].append(note)

    return groups


# ------------------------
# PROCESS NOTES
# ------------------------

def get_parsed_notes():
    notes = read_notes()
    return [parse_note(note, i) for i, note in enumerate(notes)]


def filter_notes(notes, search="", tag=""):
    filtered = []

    for note in notes:
        matches_search = search.lower() in note["raw"].lower() if search else True
        matches_tag = note["tag"].lower() == tag.lower() if tag else True

        if matches_search and matches_tag:
            note["highlighted_text"] = highlight_text(note["text"], search)
            filtered.append(note)

    return filtered


def analyze_notes(notes):
    note_count = len(notes)
    word_count = sum(len(note["text"].split()) for note in notes)
    return note_count, word_count


# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    tag = request.args.get("tag", "").strip().lower()

    notes = get_parsed_notes()
    filtered_notes = filter_notes(notes, search, tag)
    note_count, word_count = analyze_notes(filtered_notes)

    return render_template(
        "index.html",
        notes=filtered_notes,
        search=search,
        tag=tag,
        note_count=note_count,
        word_count=word_count,
    )


@app.route("/stats")
def stats():
    notes = get_parsed_notes()
    note_count, word_count = analyze_notes(notes)

    average = word_count / note_count if note_count > 0 else 0

    return render_template(
        "stats.html",
        note_count=note_count,
        word_count=word_count,
        average=average,
    )


@app.route("/tags")
def tags():
    notes = get_parsed_notes()
    grouped_notes = group_notes_by_tag(notes)

    return render_template(
        "tags.html",
        grouped_notes=grouped_notes,
    )


@app.route("/add", methods=["POST"])
def add_note():
    tag = request.form.get("tag", "").strip().lower()
    note = request.form.get("note", "").strip()

    if tag == "" or note == "":
        return redirect("/")

    notes = read_notes()
    notes.append(f"[{tag}] {note}\n")
    save_notes(notes)

    return redirect("/")


@app.route("/delete/<int:index>", methods=["POST"])
def delete_note(index):
    notes = read_notes()

    if 0 <= index < len(notes):
        notes.pop(index)
        save_notes(notes)

    return redirect("/")


@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit_note(index):
    notes = read_notes()

    if index < 0 or index >= len(notes):
        return redirect("/")

    if request.method == "POST":
        tag = request.form.get("tag", "").strip().lower()
        note = request.form.get("note", "").strip()

        if tag != "" and note != "":
            notes[index] = f"[{tag}] {note}\n"
            save_notes(notes)

        return redirect("/")

    note = parse_note(notes[index], index)

    return render_template(
        "edit.html",
        note=note
    )


# ------------------------
# RUN APP
# ------------------------

if __name__ == "__main__":
    app.run(debug=True)
