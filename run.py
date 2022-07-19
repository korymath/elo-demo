import random
from tinydb import TinyDB, Query
from tinydb.operations import set
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Build some sensible defaults.
db = TinyDB('db.json')
all_examples = ['A', 'B', 'C', 'D']
default_score = 100.


def calculate_updated_elo_score(score_winner, score_loser):
    """Update ELO scores."""

    k_factor = 32.
    scale_rating_factor = 400.

    # Calculated the expected scores for winner and loser.
    expected_score_winner = 1. / \
        (1. + 10.**((score_loser - score_winner) / scale_rating_factor))
    expected_score_loser = 1. / \
        (1. + 10.**((score_winner - score_loser) / scale_rating_factor))

    # Caluclate the updated scores for the winner and loser.
    updated_score_winner = score_winner + \
        k_factor * (1. - expected_score_winner)
    updated_score_loser = score_loser + \
        k_factor * (0. - expected_score_loser)

    return int(updated_score_winner), int(updated_score_loser)


@app.route('/api/submit_preference/', methods=['GET'])
def submit_preference():
    """Submit a new preference."""
    selected_candidate_id = request.args['selected_candidate_id']
    non_selected_candidate_id = request.args['non_selected_candidate_id']

    print(f'Selected candidate ID: {selected_candidate_id}',
          f'nonselected candidate ID: {non_selected_candidate_id}')

    selected_score = db.search(
        Query().candidate_id == selected_candidate_id)[0]['score']
    nonselected_score = db.search(
        Query().candidate_id == non_selected_candidate_id)[0]['score']

    print(f'selected_score: {selected_score}',
          f'nonselected_score: {nonselected_score}')

    # Update the database
    selected_new_score, non_selected_new_score = calculate_updated_elo_score(
        selected_score, nonselected_score)

    print(f'selected_new_score: {selected_new_score}',
          f'non_selected_new_score: {non_selected_new_score}')

    # Modify the selected candidate score
    db.update(set('score', selected_new_score), Query().candidate_id ==
              selected_candidate_id)

    # Modify the non-selected candidate score
    db.update(set('score', non_selected_new_score), Query().candidate_id ==
              non_selected_candidate_id)

    print('Scores updated.')
    return jsonify(db.all())


@app.route('/api/reset')
def reset():
    """Reset scores."""
    for candidate in all_examples:
        db.update({'score': default_score}, Query().candidate_id == candidate)
    print('Scores reset.')
    print(db.all())
    return jsonify(db.all())


@app.route('/rebuild_index')
def rebuild_index():
    all_doc_ids = []

    # Get all existing doc ids
    for entry in db.all():
        all_doc_ids.append(entry.doc_id)
    # Remove all existing doc ids
    db.remove(doc_ids=all_doc_ids)

    # Reset to default scores
    for candidate in all_examples:
        db.insert({"candidate_id": candidate, "score": default_score})
    return jsonify(db.all())


@app.route('/')
def index():
    """Render the main index page."""

    # Sample Candidates
    all_candidates = db.all()
    print('all_candidates', all_candidates)
    candidates = random.sample(all_candidates, 2)

    # Render the Page
    return render_template('index.html', data=db.all(), candidates=candidates)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
