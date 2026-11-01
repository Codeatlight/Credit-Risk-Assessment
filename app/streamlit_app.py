"""Enter an applicant, see the score, the decision and the reasons.

Run from the project root:  streamlit run app/streamlit_app.py
"""
from html import escape

import streamlit as st

from scoring import is_approved, load_card, reasons, risk_of_default, score

SCORE_LOW = 300
SCORE_HIGH = 800

STYLE = """
<style>
.block-container {max-width: 1240px; padding-top: 2.5rem; padding-bottom: 4rem}
h1 {font-size: 3rem; letter-spacing: -0.02em; line-height: 1.05}
h2 {font-size: 1.35rem; letter-spacing: -0.01em}
.st-key-result {background: #E6ECEB; padding: 1.5rem}
[data-testid="stColumn"]:has(.st-key-result) {position: sticky; top: 1.5rem; align-self: flex-start}
.decision {font-size: 1.5rem; font-weight: 700; margin: 0}
.decision.approve {color: #0F6B62}
.decision.refuse {color: #B3261E}
.score {font-size: 5.5rem; font-weight: 700; line-height: 1; letter-spacing: -0.03em;
        font-variant-numeric: tabular-nums; margin: 0.25rem 0 0.5rem}
.risk {font-size: 1.1rem; margin: 0 0 1.25rem}
.scale {position: relative; height: 12px; background: #CBD6D5; margin: 0 0 0.4rem}
.scale .fill {position: absolute; inset: 0 auto 0 0; background: #12242B}
.scale .cutoff {position: absolute; top: -5px; bottom: -5px; width: 3px; background: #B3261E}
.scale-note {font-size: 0.9rem; margin: 0 0 1.25rem}
.reasons {margin: 0 0 1rem}
.reasons h3 {font-size: 1rem; font-weight: 700; margin: 0 0 0.25rem; padding: 0}
.reasons p {font-size: 0.95rem; margin: 0 0 0.25rem}
.ledger {width: 100%; border-collapse: collapse; font-size: 0.95rem}
.ledger th, .ledger td {text-align: left; padding: 0.45rem 0.75rem 0.45rem 0; border-bottom: 1px solid #DCE4E3}
.ledger .number {text-align: right; font-variant-numeric: tabular-nums; padding-right: 0}
.ledger tfoot td {font-weight: 700; border-bottom: 0; font-size: 1.1rem}
@media (max-width: 640px) {
  h1 {font-size: 2.25rem}
  .st-key-layout > div > [data-testid="stHorizontalBlock"] {flex-direction: column-reverse}
  [data-testid="stColumn"]:has(.st-key-result) {position: static; align-self: stretch}
  .score {font-size: 4.5rem}
  .ledger .optional {display: none}
}
</style>
"""

st.set_page_config(page_title="Credit Risk Scorecard", layout="wide")
st.html(STYLE)
card = load_card()


def scale_position(value):
    return min(max((value - SCORE_LOW) / (SCORE_HIGH - SCORE_LOW), 0.0), 1.0) * 100


def reason_html(title, lines, empty):
    rows = "".join(f"<p>{escape(line['question'])}: {escape(line['answer'])} ({line['gap']:+.0f})</p>" for line in lines)
    return f"<div class='reasons'><h3>{title}</h3>{rows or f'<p>{empty}</p>'}</div>"


def result_html(total, risk, against, helping):
    approved = is_approved(card, total)
    decision = "Approve" if approved else "Refuse"
    cutoff = card["min_score"]
    return f"""
    <div role="status" aria-live="polite">
      <p class="decision {decision.lower()}">{decision}</p>
      <p class="score">{total}</p>
      <p class="risk">{risk:.1%} estimated risk of default</p>
      <div class="scale" role="img" aria-label="Score {total} on a scale of {SCORE_LOW} to {SCORE_HIGH}, cutoff {cutoff}">
        <div class="fill" style="width: {scale_position(total):.1f}%"></div>
        <div class="cutoff" style="left: {scale_position(cutoff):.1f}%"></div>
      </div>
      <p class="scale-note">Red mark: cutoff of {cutoff}. Every 50 points doubles the odds of repaying.</p>
      {reason_html("Pulling the score down", against, "Nothing is below a typical applicant.")}
      {reason_html("Lifting the score", helping, "Nothing is above a typical applicant.")}
    </div>"""


def ledger_html(total, answers):
    rows = []
    for q in card["questions"]:
        answer = q["answers"][answers[q["feature"]]]
        rows.append(f"<tr><td>{escape(q['question'])}</td><td>{escape(answer['label'])}</td>"
                    f"<td class='number optional'>{q['typical']:+.0f}</td><td class='number'>{answer['points']:+d}</td></tr>")
    return f"""
    <table class="ledger">
      <thead><tr><th scope="col">Line</th><th scope="col">Answer</th>
        <th scope="col" class="number optional">Typical</th><th scope="col" class="number">Points</th></tr></thead>
      <tbody><tr><td colspan="2">Starting points</td><td class="optional"></td>
        <td class="number">{card['base_points']}</td></tr>{''.join(rows)}</tbody>
      <tfoot><tr><td colspan="2">Score</td><td class="optional"></td><td class="number">{total}</td></tr></tfoot>
    </table>"""


st.title("Credit Risk Scorecard")
st.write("Fifteen answers become one score and an approve or refuse decision. "
         "A portfolio demo built on public Kaggle data, not a real credit decision.")

answers = {}
with st.container(key="layout"):
    form, result = st.columns([3, 2], gap="large")

with form:
    for group in dict.fromkeys(q["group"] for q in card["questions"]):
        st.subheader(group)
        left, right = st.columns(2)
        questions = [q for q in card["questions"] if q["group"] == group]
        for position, q in enumerate(questions):
            labels = [a["label"] for a in q["answers"]]
            with left if position % 2 == 0 else right:
                answers[q["feature"]] = st.selectbox(q["question"], range(len(labels)), index=q["default"],
                                                     format_func=labels.__getitem__, key=q["feature"])

total = score(card, answers)
against, helping = reasons(card, answers)

with result:
    with st.container(key="result"):
        st.html(result_html(total, risk_of_default(card, total), against, helping))

st.subheader("How the score adds up")
st.html(ledger_html(total, answers))

st.subheader("How this works, and its limits")
model_notes, limit_notes = st.columns(2, gap="large")
model_notes.markdown(
    "**Model.** A 15-line scorecard without the undocumented `EXT_SOURCE` scores, chosen because every point can "
    "be explained. On 61,503 applicants held back from training it reached AUC 0.704. LightGBM with `EXT_SOURCE` "
    "reached 0.788, so explainability has a real cost.\n\n"
    "**Cutoff.** Chosen for the most profit, assuming a repaid loan earns 15% of its size and a default loses 60%. "
    "Those figures are assumptions, not data.\n\n"
    "**Risk estimates.** On held-back applicants, predicted and actual default rates matched closely.")
limit_notes.markdown(
    "**Fairness.** The model doesn't use gender or age directly, but other answers can carry them. Occupation is "
    "strongly linked to gender. Good payers under 30 were refused 4.4% of the time, against 0.4% for those 60 and "
    "over. Men's risk was underestimated by about 1.2 points and women's overestimated by about 0.6.\n\n"
    "**Limits.** The data only covers people who were given loans. Answers here aren't checked against each other, "
    "so a form can describe an applicant who couldn't exist.")
