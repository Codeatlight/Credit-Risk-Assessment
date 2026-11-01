"""Enter an applicant, see the score, the decision and the reasons.

Run from the project root:  streamlit run app/streamlit_app.py
"""
import streamlit as st

from scoring import is_approved, load_card, reasons, risk_of_default, score

SCORE_LOW = 300
SCORE_HIGH = 800

st.set_page_config(page_title="Credit Risk Scorecard", layout="wide")
card = load_card()


def reason_lines(lines):
    return "\n".join(f"- **{line['question']}:** {line['answer']} ({line['gap']:+.0f} points against typical)"
                     for line in lines)


st.title("Credit Risk Scorecard")
st.write("Answer the 15 questions to see how a points-based scorecard would treat a loan applicant. "
         "This is a portfolio demo built on public Kaggle data, not a real credit decision.")

form, result = st.columns([3, 2], gap="large")

answers = {}
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
risk = risk_of_default(card, total)
against, helping = reasons(card, answers)

with result:
    st.subheader("Result")
    if is_approved(card, total):
        st.success(f"Approve: the score is at or above the cutoff of {card['min_score']}")
    else:
        st.error(f"Refuse: the score is below the cutoff of {card['min_score']}")
    score_column, risk_column = st.columns(2)
    score_column.metric("Score", total)
    risk_column.metric("Estimated risk of default", f"{risk:.1%}")
    st.progress(min(max((total - SCORE_LOW) / (SCORE_HIGH - SCORE_LOW), 0.0), 1.0))
    st.caption(f"A higher score is safer. Every 50 points doubles the odds of repaying. "
               f"Starting points: {card['base_points']}.")

    st.markdown("**Pulling the score down**")
    st.markdown(reason_lines(against) if against else "Nothing here is below a typical applicant.")
    st.markdown("**Lifting the score**")
    st.markdown(reason_lines(helping) if helping else "Nothing here is above a typical applicant.")

    with st.expander("How this works, and its limits"):
        st.markdown(
            "- **Model:** a 15-line scorecard without the undocumented `EXT_SOURCE` scores, chosen because every point "
            "can be explained. On 61,503 applicants held back from training it reached AUC 0.704. LightGBM with "
            "`EXT_SOURCE` reached 0.788, so explainability has a real cost.\n"
            "- **Cutoff:** chosen for the most profit, assuming a repaid loan earns 15% of its size and a default "
            "loses 60%. Those figures are assumptions, not data.\n"
            "- **Risk estimates:** on held-back applicants, predicted and actual default rates matched closely.\n"
            "- **Fairness:** the model doesn't use gender or age directly, but other answers can carry them. "
            "Occupation is strongly linked to gender. Good payers under 30 were refused 4.4% of the time, against "
            "0.4% for those 60 and over. Men's risk was underestimated by about 1.2 points and women's "
            "overestimated by about 0.6.\n"
            "- **Limits:** the data only covers people who were given loans. Answers here aren't checked against "
            "each other, so a form can describe an applicant who couldn't exist.")
