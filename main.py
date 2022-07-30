import random
import logging
from typing_extensions import assert_type
from flask import Flask, render_template, jsonify, request
from firebase_admin import credentials, firestore, initialize_app

# Initialize Flask App
app = Flask(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
)


# Initialize Firestore DB
cred = credentials.Certificate("key.json")
default_app = initialize_app(cred)
db_client = firestore.client()
db = db_client.collection("all_letters")

# Define candidate names for list of letters
candidate_names = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
]
default_elo_score = 100


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
    selected_name = request.args["selected_name"]
    non_selected_name = request.args["non_selected_name"]

    app.logger.info(
        (
            f"selected name: {selected_name}, "
            + f"nonselected name: {non_selected_name}"
        ),
    )

    # Handle selected candidate
    selected_score_docs = db.where("name", "==", selected_name).stream()
    for sel_doc in selected_score_docs:
        selected_doc_id = sel_doc.id
        selected_doc = sel_doc.to_dict()
        selected_elo_score = selected_doc["elo_score"]
        selected_matches = selected_doc["matches"]
        selected_wins = selected_doc["wins"]
    app.logger.info(f"selected_doc: {selected_doc}")

    # Handle nonselected candidate
    nonselected_score_docs = db.where("name", "==", non_selected_name).stream()
    for non_doc in nonselected_score_docs:
        non_selected_doc_id = non_doc.id
        non_selected_doc = non_doc.to_dict()
        nonselected_elo_score = non_selected_doc["elo_score"]
        nonselected_matches = non_selected_doc["matches"]
        nonselected_wins = non_selected_doc["wins"]
        nonselected_losses = non_selected_doc["losses"]
    app.logger.info(f"non_selected_doc: {non_selected_doc}")

    # Calculate new win rate, matches, wins and losses
    selected_matches += 1
    selected_wins += 1
    selected_win_rate = str(round(100 * (selected_wins / selected_matches), 2)) + "%"

    nonselected_matches += 1
    nonselected_losses += 1
    nonselected_win_rate = str(round(100 * (nonselected_wins / nonselected_matches), 2)) + "%"

    # Calculate the new elo scores
    selected_new_elo_score, non_selected_new_elo_score = calculate_updated_elo_score(
        selected_elo_score, nonselected_elo_score
    )
    app.logger.info(
        (
            f"selected_new_elo_score: {selected_new_elo_score}, "
            + f"non_selected_new_score: {non_selected_new_elo_score}"
        ),
    )

    # Update the database
    batch = db_client.batch()

    # Modify the selected candidate score
    selected_ref = db.document(f"{selected_doc_id}")
    batch.update(
        selected_ref,
        {
            "elo_score": selected_new_elo_score,
            "win_rate": selected_win_rate,
            "matches": selected_matches,
            "wins": selected_wins,
        },
    )

    # Modify the non-selected candidate score
    non_selected_ref = db.document(f"{non_selected_doc_id}")
    batch.update(
        non_selected_ref, 
        {
            "elo_score": non_selected_new_elo_score,
            "win_rate": nonselected_win_rate,
            "matches": nonselected_matches,
            "losses": nonselected_losses,
        },
    )

    # Commit the batch
    batch.commit()

    app.logger.info("Preference registered and scores updated as a batched write.")

    # Return list of all candidates sorted by name.
    all_candidates = [
        doc.to_dict()
        for doc in db.order_by("name", direction=firestore.Query.ASCENDING).stream()
    ]
    return jsonify(all_candidates), 200


@app.route("/api/reset")
def reset():
    """Reset scores."""
    # Get and print all existing candidates.
    docs = db.stream()
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")
        db.document(f"{doc.id}").update(
            {
                "elo_score": default_elo_score,
                "win_rate": "-",
                "matches": 0,
                "wins": 0,
                "losses": 0,
            }
        )
        print(f"{doc.id} => {doc.to_dict()}")
    print("Scores reset.")

    # Return list of all candidates sorted by name.
    all_candidates = [
        doc.to_dict()
        for doc in db.order_by("name", direction=firestore.Query.ASCENDING).stream()
    ]
    return jsonify(all_candidates), 200


@app.route("/rebuild_index")
def rebuild_index():

    # Get, print, and delete all existing candidates.
    docs = db.stream()
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")
        db.document(f"{doc.id}").delete()
    print("All existing candidates deleted.")

    # Add a set of candidates from a pre-set list.
    for name in candidate_names:
        data = {
            "name": name,
            "elo_score": default_elo_score,
            "win_rate": "-",
            "matches": 0,
            "wins": 0,
            "losses": 0,
        }
        db.add(data)

    # Get and print all existing candidates.
    docs = db.stream()
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")
    print("Index rebuilt.")

    # Return list of all candidates sorted by name.
    all_candidates = [
        doc.to_dict()
        for doc in db.order_by("name", direction=firestore.Query.ASCENDING).stream()
    ]
    return jsonify(all_candidates), 200


@app.route("/")
def index():
    """Render the main index page."""

    # Return list of all candidates sorted by name.
    all_candidates = [
        doc.to_dict()
        for doc in db.order_by("name", direction=firestore.Query.ASCENDING).stream()
    ]

    # Sample 2 candidates for next match
    next_match_candidates = random.sample(all_candidates, 2)

    # Render the Page
    return render_template(
        "index.html",
        all_candidates=all_candidates,
        next_match_candidates=next_match_candidates,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
