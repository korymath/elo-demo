import random
from typing_extensions import assert_type
from flask import Flask, render_template, jsonify, request
from firebase_admin import credentials, firestore, initialize_app

# Initialize Flask App
app = Flask(__name__)

# Initialize Firestore DB
cred = credentials.Certificate("key.json")
default_app = initialize_app(cred)
db_client = firestore.client()
db = db_client.collection("all_letters")

# Define Sensible Defaults
all_examples = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
default_score = 100


def calculate_updated_elo_score(
    score_winner, score_loser, k_factor=32, scale_rating_factor=400.0
):
    """Update ELO scores."""

    # Calculated the expected scores for winner and loser.
    expected_score_winner = 1.0 / (
        1.0 + 10.0 ** ((score_loser - score_winner) / scale_rating_factor)
    )
    expected_score_loser = 1.0 / (
        1.0 + 10.0 ** ((score_winner - score_loser) / scale_rating_factor)
    )

    # Calculate the updated scores for the winner and loser.
    updated_score_winner = score_winner + k_factor * (1.0 - expected_score_winner)
    updated_score_loser = score_loser + k_factor * (0.0 - expected_score_loser)

    return int(updated_score_winner), int(updated_score_loser)


@app.route("/api/submit_preference/", methods=["GET"])
def submit_preference():
    """Submit a new preference."""
    selected_candidate_id = request.args["selected_candidate_id"]
    non_selected_candidate_id = request.args["non_selected_candidate_id"]

    print(
        f"Selected candidate ID: {selected_candidate_id} \n",
        f"Nonselected candidate ID: {non_selected_candidate_id}",
    )

    # Handle selected candidate
    selected_score_docs = db.where(
        "candidate_id", "==", selected_candidate_id).stream()
    for sel_doc in selected_score_docs:
        selected_doc_id = sel_doc.id
        selected_doc = sel_doc.to_dict()
        selected_score = selected_doc["score"]

    # Handle nonselected candidate
    nonselected_score_docs = db.where(
        "candidate_id", "==", non_selected_candidate_id
    ).stream()
    for non_doc in nonselected_score_docs:
        non_selected_doc_id = non_doc.id
        non_selected_doc = non_doc.to_dict()
        nonselected_score = non_selected_doc["score"]

    print(
        f"Selected_score: {selected_score}", 
        f"Nonselected_score: {nonselected_score}"
    )

    # Calculate the new scores
    selected_new_score, non_selected_new_score = calculate_updated_elo_score(
        selected_score, nonselected_score
    )
    print(
        f"Selected_new_score: {selected_new_score}",
        f"Non_selected_new_score: {non_selected_new_score}",
    )

    # Update the database
    # Modify the selected candidate score
    db.document(f"{selected_doc_id}").update({"score": selected_new_score})
    # Modify the non-selected candidate score
    db.document(f"{non_selected_doc_id}").update({"score": non_selected_new_score})

    print("Preference registered and scores updated.")
    
    all_candidates = [doc.to_dict() for doc in db.stream()]
    all_cand_sorted = sorted(all_candidates, key=lambda d: d['candidate_id']) 
    return jsonify(all_cand_sorted), 200


# @app.route("/api/reset")
# def reset():
#     """Reset scores."""
#     # Get and print all existing candidates.
#     docs = db.stream()
#     for doc in docs:
#         print(f"{doc.id} => {doc.to_dict()}")
#         db.document(f"{doc.id}").update({"score": default_score})
#         print(f"{doc.id} => {doc.to_dict()}")

#     print("Scores reset.")
#     all_candidates = [doc.to_dict() for doc in db.stream()]
#     all_cand_sorted = sorted(all_candidates, key=lambda d: d['candidate_id']) 
#     return jsonify(all_cand_sorted), 200


# @app.route("/rebuild_index")
# def rebuild_index():

#     # Get and print all existing candidates.
#     docs = db.stream()
#     for doc in docs:
#         print(f"{doc.id} => {doc.to_dict()}")
#         # Delete candidate
#         db.document(f"{doc.id}").delete()

#     print("All existing candidates deleted.")

#     for example in all_examples:
#         data = {"candidate_id": example, "score": default_score}
#         db.add(data)

#     # Get and print all existing candidates.
#     docs = db.stream()
#     for doc in docs:
#         print(f"{doc.id} => {doc.to_dict()}")

#     print("Index rebuilt.")
#     all_candidates = [doc.to_dict() for doc in db.stream()]
#     all_cand_sorted = sorted(all_candidates, key=lambda d: d['candidate_id']) 
#     return jsonify(all_cand_sorted), 200


@app.route("/")
def index():
    """Render the main index page."""

    # Sample Candidates
    all_candidates = [doc.to_dict() for doc in db.stream()]
    all_cand_sorted = sorted(all_candidates, key=lambda d: d['candidate_id']) 
    candidates = random.sample(all_candidates, 2)

    # Render the Page
    return render_template(
        "index.html", data=all_cand_sorted, candidates=candidates)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
