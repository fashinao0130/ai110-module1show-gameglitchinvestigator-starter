# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The game ran without crashing, but the logic underneath it was full of small bugs. The difficulty ranges were backwards: "Normal" secretly used a 1–100 range while "Hard" used 1–50, so Hard was actually easier than Normal. The hint text was also misdirected the user on the secret number.A guess that was correctly identified as "Too High" would still tell the player to "Go HIGHER," which sends you further from the answer instead of closer. Every other guess silently compared the secret as a string instead of an int, so hints could come out wrong just because of which attempt number you were on, and "New Game" didn't fully reset the game so a finished game could never really restart.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|--------------------|------------------|--------------------------|
| 48 (secret 38) | "Too High" outcome paired with "Go LOWER" hint | Hint said "Go higher" | No error just the wrong hint text |
| 27 (secret 38) | "Too Low" outcome paired with "Go HIGHER" hint | Hint said "Go lower" | No error just the wrong hint text |
| 38 (secret 38) | "Win" outcome, correct message | Correct | No exception |

---

## 2. How did you use AI as a teammate?

I used Claude Code as a teammate for reviewing the code, writing commit messages, and troubleshooting problems outside the code itself, like a Git push failure. One example of a correct AI suggestion: when I asked it to summarize my changes to "app.py", it correctly identified that the Normal/Hard difficulty ranges had been swapped and that the outcome/hint pairing in the "check_guess" function had been inverted giving you the wrong output. I verified this by re-reading the diff line by line and manually tracing the check_guess function to confirm the fixed version now returns "Too High" paired with "Go LOWER" instead of the old backwards pairing. One example of an AI suggestion that didn't pan out: when refactoring the game logic into `logic_utils.py`, the AI's first draft of the `app.py` edit simply deleted the old function definitions and replaced them with an import, which would have silently thrown away the `# FIX:` comments explaining what each bug was and why the fix worked. I caught this before applying the edit and asked for those comments to be preserved in their new location instead of lost, which showed me that an AI refactor can quietly drop important context even when the code itself still runs correctly.

---

## 3. Debugging and testing your fixes

I decided a bug was really fixed by tracing through the function with the same inputs that had exposed the bug and confirming the output matched what the game was supposed to do, not just that it looked different. The clearest test I ran was `pytest tests/test_game_logic.py`: before any refactoring, all three tests failed with `NotImplementedError`, because the logic functions (`check_guess`, `get_range_for_difficulty`, etc.) had never actually been moved out of `app.py` into `logic_utils.py` — the file the tests imported from was still just stubs. After porting the real (already-fixed) functions into `logic_utils.py` and having `app.py` import them instead of duplicating them, I reran pytest and got 3 passed. Along the way I also found a bug in the test file itself: it compared `check_guess(50, 50)` directly to the string `"Win"`, but `check_guess` actually returns a tuple `("Win", "🎉 Correct!")`, so that assertion could never have passed even with correct game logic — I fixed the test to unpack the tuple before asserting on the outcome. AI helped me spot this mismatch by pointing out the difference between the docstring's documented return type and what the test actually asserted, but I confirmed it myself by running the test and reading the failure output.

---

## 4. What did you learn about Streamlit and state?

Streamlit doesn't update your page in place the way a normal web app does — every single time you click a button or type into a box, Streamlit throws away the whole page and reruns your entire Python script from top to bottom. That's why `st.session_state` exists: it's a dictionary that survives across those reruns, so things like the secret number, your score, and your attempt count don't get wiped out every time you click something. This app actually shows why rerun order matters: the banner and debug panel used to be written *above* the code that processes your guess, so because Streamlit runs top to bottom, they'd draw themselves using last click's state and always looked one step behind. It also explains why `st.rerun()` needs a workaround to show a message — anything you `st.success()` right before calling `st.rerun()` gets thrown away because the rerun restarts the script immediately, so the message has to be stashed in `session_state` and displayed on the *next* run instead.

---

## 5. Looking ahead: your developer habits

One habit I want to keep from this project is writing down a concrete repro (exact input, expected output, actual output) before trying to fix a bug — it's what let me tell the difference between "this looks fixed" and "this is actually fixed," especially for the hint-inversion bug where the wrong version could still look plausible at a glance. One thing I'd do differently next time is review an AI's proposed edit against the original code before applying it, not just skim the result after — the logic_utils.py refactor almost shipped without the comments documenting why each bug was a bug, and I only caught that by comparing the proposed change to what was already there. This project changed how I think about AI-generated code because it made clear that "the code runs" and "the code is correct" are very different claims — several of these bugs (the swapped ranges, the inverted hints, the str/int comparison) would never show up as a crash or error message, only as subtly wrong behavior you'd have to actually test for.
