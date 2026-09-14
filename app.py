import random
import streamlit as st

# REFACTOR: the pure game-logic functions (no Streamlit dependency) now live in
# logic_utils.py so tests/test_game_logic.py can import and test them directly
# without spinning up a Streamlit app.
from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    # FIX: started at 1, so a fresh game already showed one attempt used.
    # attempts counts guesses actually made, so it starts at 0.
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty

# Message carried across an st.rerun() to be shown on the next pass.
if "notice" not in st.session_state:
    st.session_state.notice = None

# Changing difficulty changes the range, so the old secret is no longer valid.
if st.session_state.difficulty != difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []

st.subheader("Make a guess")

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    # FIX: only attempts and secret were reset. status stayed "won"/"lost", so a
    # finished game could never restart, and score/history carried over. Reset
    # every piece of game state.
    st.session_state.attempts = 0
    # FIX: was hardcoded randint(1, 100), which ignored the selected difficulty.
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    # st.rerun() throws away anything drawn before it, so the old st.success()
    # here never appeared. Stash the notice and render it after the rerun.
    st.session_state.notice = "New game started."
    st.rerun()

# FIX (render order): the banner and debug panel used to sit ABOVE this block.
# Streamlit runs top-to-bottom, so they drew themselves before the new guess was
# recorded and always showed the PREVIOUS click's state. Now the guess is
# processed first and messages are collected here, then everything renders below
# against current state.
feedback = []
celebrate = False

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        feedback.append((st.success, "You already won. Start a new game to play again."))
    else:
        feedback.append((st.error, "Game over. Start a new game to try again."))
elif submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        feedback.append((st.error, err))
    else:
        st.session_state.history.append(guess_int)

        # FIX: on even attempts the secret was cast to str, which made
        # check_guess compare text lexicographically ("9" > "50") instead of
        # numerically. Always compare the int.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            feedback.append((st.warning, message))

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            celebrate = True
            st.session_state.status = "won"
            feedback.append((
                st.success,
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}",
            ))
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                feedback.append((
                    st.error,
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}",
                ))

if st.session_state.notice:
    st.success(st.session_state.notice)
    st.session_state.notice = None

for show, text in feedback:
    show(text)

if celebrate:
    st.balloons()

attempts_left = max(attempt_limit - st.session_state.attempts, 0)

# FIX: banner was hardcoded to "1 and 100" and contradicted the sidebar.
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempts_left}"
)

# FIX: expanded=True keeps the panel open across reruns. A Streamlit expander
# resets to its default on every script run, so it snapped shut after each guess.
with st.expander("Developer Debug Info", expanded=True):
    st.write("Secret:", st.session_state.secret)
    # FIX: showed the attempt number you were on. Now matches the banner.
    st.write("Attempts left:", attempts_left)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    # FIX: a plain list renders with 0-based indices, so the first guess read as
    # 0. Key each guess by its attempt number instead, counting from 1.
    st.write(
        "History:",
        {n: guess for n, guess in enumerate(st.session_state.history, start=1)},
    )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
