"""Enter an applicant, see the score, the decision and the reasons.

Run from the project root:  streamlit run app/streamlit_app.py
"""
import json
from base64 import b64encode
from html import escape
from pathlib import Path

import streamlit as st

from scoring import is_approved, load_card, reasons, risk_of_default, score

SCORE_LOW = 300
SCORE_HIGH = 800
BACKGROUND = Path(__file__).parent / "background.svg"
ART = Path(__file__).parent / "art"
PASSBOOK = Path(__file__).parent / "passbook.js"
VAULT_CODE = "7041"
PROFILES = {"Strong borrower": "best", "Typical applicant": "typical", "Overstretched": "weak"}
FIXED_GROUP = "Job"  # not something an applicant changes quickly, so never a suggested step
EXPLORER = Path(__file__).parent / "explorer.html"
STATS = Path(__file__).parent / "stats.json"
EXPLORER_HEIGHT = 640
HEADLINE_STATS = [("246,008", "applicants trained on"), ("61,503", "held back for the final test"),
                  ("0.704", "AUC on the final test"), ("97.0%", "approved at the cutoff")]

STYLE = """
<style>
.block-container {max-width: 1240px; padding-top: 1.5rem; padding-bottom: 3rem}
[data-testid="stHeader"] {background: transparent}
.hero {position: relative; overflow: hidden; background: var(--hero); color: #FFFFFF; border-radius: 18px;
       padding: 2.25rem 2.25rem 1.75rem; isolation: isolate}
.hero::before {content: ""; position: absolute; inset: 0 -4%; z-index: -1; opacity: 0.13; pointer-events: none;
               background: url("data:image/svg+xml;base64,BACKGROUND_DATA") bottom / 100% 100% no-repeat;
               animation: drift 45s ease-in-out infinite alternate}
@keyframes drift {from {transform: translateX(-2%)} to {transform: translateX(2%)}}
.hero.compact {padding: 1.4rem 2rem}
.hero.compact h1 {font-size: 1.9rem}
.hero.compact .lead {margin-bottom: 0}
.home {padding: 2.75rem 2.5rem}
.home-grid {display: grid; grid-template-columns: 1.35fr 1fr; gap: 2.5rem; align-items: center}
.home-grid > * {min-width: 0}
.home h1 {font-size: 3.4rem !important; line-height: 1.05}
.home .lead {font-size: 1.15rem; margin: 0.9rem 0 1.75rem}
.home .stats {grid-template-columns: repeat(auto-fit, minmax(130px, 1fr))}
.preview {background: var(--surface); color: var(--ink); border: 1px solid var(--line); border-radius: 16px; padding: 1.25rem}
.preview .reasons {margin: 0.6rem 0 0}
.st-key-rail {position: absolute; height: 0; overflow: hidden}
.st-key-cta {margin: 0.25rem 0 0.5rem}
.hero h1 {color: #FFFFFF; font-size: 2.6rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.1;
          margin: 0; padding: 0}
.hero .lead {color: #C9D3E6; font-size: 1.05rem; max-width: 44rem; margin: 0.6rem 0 1.5rem}
.hero .stats {display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem}
.hero .stats strong {display: block; font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em;
                     font-variant-numeric: tabular-nums; line-height: 1.2}
.hero .stats span {color: #C9D3E6; font-size: 0.875rem}
.card, [class*="st-key-group-"], .st-key-result, .st-key-explorer-panel, .st-key-notes-panel {
  background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 1.4rem;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05)}
[class*="st-key-group-"] h3, .st-key-notes-panel h3 {font-size: 1.15rem; font-weight: 600; letter-spacing: -0.01em; padding: 0 0 0.25rem}
[data-testid="stSelectbox"] > div:last-child > div {background: var(--field); border: 1px solid var(--field-line); transition: border-color 0.15s}
[data-testid="stSelectbox"] > div:last-child > div:hover {border-color: var(--accent)}
[data-testid="stColumn"]:has(.st-key-result) {position: sticky; top: 1rem; align-self: flex-start}
.verdict {display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; margin: 0 0 0.25rem}
.verdict h3 {font-size: 1.15rem; font-weight: 600; margin: 0; padding: 0}
.decision {font-size: 0.95rem; font-weight: 600; padding: 0.2rem 0.75rem; border-radius: 999px; margin: 0}
.decision.approve {color: var(--good-ink); background: var(--good-soft)}
.decision.refuse {color: var(--bad-ink); background: var(--bad-soft)}
.decision.flipped {animation: flip 0.5s ease-out}
@keyframes flip {from {transform: scale(1.25)} to {transform: scale(1)}}
.dial {position: relative; max-width: 300px; margin: 0.25rem auto 0}
.gauge {position: relative; aspect-ratio: 2 / 1; overflow: hidden}
@property --p {syntax: "\\3C number\\3E "; inherits: false; initial-value: 0}
.ring {width: 100%; aspect-ratio: 1; border-radius: 50%; --p: var(--to); --fill: var(--good);
       background: conic-gradient(from 270deg, var(--fill) calc(var(--p) * 1.8deg), transparent 0),
                   conic-gradient(from 270deg, var(--bad-soft) calc(var(--cut) * 1.8deg), var(--good-soft) 0 180deg, transparent 0);
       -webkit-mask: radial-gradient(closest-side, transparent 80%, #000 81%);
       mask: radial-gradient(closest-side, transparent 80%, #000 81%);
       animation: sweep 0.7s cubic-bezier(.2, .8, .2, 1)}
.dial.refuse .ring {--fill: var(--bad)}
@keyframes sweep {from {--p: var(--from)} to {--p: var(--to)}}
.tick {position: absolute; left: 50%; bottom: 0; height: 100%; width: 0; transform: rotate(var(--angle));
       transform-origin: bottom}
.tick::after {content: ""; position: absolute; top: -2px; left: -1.5px; width: 3px; height: 22%; background: var(--ink)}
.dial-ends {display: flex; justify-content: space-between; color: var(--quiet); font-size: 0.8rem; padding: 0.15rem 0.2rem 0}
.dial-score {position: absolute; left: 0; right: 0; bottom: 1.5rem; text-align: center}
.score {font-size: 3.6rem; font-weight: 700; line-height: 1; letter-spacing: -0.03em;
        font-variant-numeric: tabular-nums; margin: 0}
@property --n {syntax: "\\3C integer\\3E "; inherits: false; initial-value: 0}
.count {--n: var(--to); counter-reset: score var(--n); animation: count 0.7s cubic-bezier(.2, .8, .2, 1)}
.count::after {content: counter(score)}
@keyframes count {from {--n: var(--from)} to {--n: var(--to)}}
.hidden-text {position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%)}
.risk {text-align: center; font-size: 1rem; color: var(--quiet); margin: 0.6rem 0 0}
.change {text-align: center; font-size: 0.9rem; font-weight: 600; min-height: 1.5em; margin: 0.1rem 0 0.6rem;
         animation: pop 0.4s ease-out}
.change.up {color: var(--good-ink)}
.change.down {color: var(--bad-ink)}
@keyframes pop {from {opacity: 0; transform: translateY(6px)} to {opacity: 1; transform: none}}
.dial-note {text-align: center; font-size: 0.85rem; color: var(--quiet); margin: 0 0 1rem}
.reasons {margin: 0 0 0.9rem}
.reasons h4 {font-size: 0.9rem; font-weight: 600; margin: 0 0 0.35rem; padding: 0}
.reason {display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.3rem 0}
.reason p {font-size: 0.875rem; line-height: 1.3; margin: 0}
.reason small {display: block; color: var(--quiet); font-size: 0.8rem}
.points {flex: none; font-size: 0.8rem; font-weight: 600; font-variant-numeric: tabular-nums;
         padding: 0.1rem 0.5rem; border-radius: 999px}
.points.down {color: var(--bad-ink); background: var(--bad-soft)}
.points.up {color: var(--good-ink); background: var(--good-soft)}
.ledger {width: 100%; border-collapse: collapse; font-size: 0.925rem}
.ledger th {color: var(--quiet); font-weight: 500; text-align: left; padding: 0.5rem 0.75rem 0.5rem 0;
            border-bottom: 1px solid var(--line)}
.ledger td {text-align: left; padding: 0.5rem 0.75rem 0.5rem 0; border-bottom: 1px solid var(--line-soft)}
.ledger .number {text-align: right; font-variant-numeric: tabular-nums; padding-right: 0}
.ledger .optional {padding-right: 0.9rem}
.ledger tfoot td {font-weight: 700; border-bottom: 0; font-size: 1.05rem}
.ledger tbody tr {transition: background 0.15s}
.ledger tbody tr:hover {background: var(--tint)}
.plain {display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem}
.plain div {background: var(--tint); border-radius: 12px; padding: 1rem 1.1rem}
.plain h3 {font-size: 0.95rem !important; font-weight: 600; margin: 0 0 0.3rem; padding: 0}
.plain p {font-size: 0.925rem; margin: 0}
.st-key-result, .ledger, .plain, .verdict h3, .reasons h4, .plain h3, .reason p {color: var(--ink)}
.intro-cards {display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem}
.intro-cards h2, .steps h2 {color: var(--ink); font-size: 1.1rem; font-weight: 600; margin: 0 0 0.4rem; padding: 0}
.intro-cards p {color: var(--ink); font-size: 0.95rem; margin: 0}
.steps ol {display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; list-style-position: inside; margin: 0.5rem 0 0; padding: 0}
.steps li {color: var(--ink); font-weight: 600; font-size: 0.95rem}
.steps li p {color: var(--quiet); font-weight: 400; font-size: 0.9rem; margin: 0.2rem 0 0}
.intro-foot {color: var(--quiet); font-size: 0.9rem; margin: 1rem 0 0}
.intro-foot a {color: var(--accent)}
.stApp button[kind="secondary"] {background: var(--surface); border-color: var(--line); color: var(--ink)}
.stApp button[kind="secondary"] * {color: var(--ink)}
.stApp [data-testid="stLinkButton"] a {background: var(--surface); border-color: var(--line); color: var(--ink)}
.stApp [data-testid="stLinkButton"] a * {color: var(--ink)}
.stApp button[kind="primary"] {background: var(--accent); border-color: var(--accent); color: var(--on-accent); font-weight: 600}
.stApp button[kind="primary"] * {color: var(--on-accent)}
.source-note {color: var(--quiet); font-size: 0.85rem; margin: 0.75rem 0 0}
.stApp, .card, [class*="st-key-group-"], .st-key-result, .st-key-explorer-panel, .st-key-notes-panel {
  transition: background 0.3s, border-color 0.3s, box-shadow 0.5s}
[data-testid="stMainBlockContainer"] {position: relative; z-index: 1}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {background: transparent}
.scene {position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden}
.scene i {position: absolute; display: block; background: var(--engrave); -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
          -webkit-mask-size: 100% 100%; mask-size: 100% 100%}
.scene .one {top: -230px; left: -230px; width: 620px; height: 620px; opacity: 0.34; animation: turn 150s linear infinite}
.scene .two {bottom: -330px; right: -300px; width: 860px; height: 860px; opacity: 0.3; animation: turn 190s linear infinite reverse}
.scene .wave-left {top: 0; bottom: 0; left: 0; width: 170px; opacity: 0.2}
.scene .wave-right {top: 0; bottom: 0; right: 60px; width: 170px; opacity: 0.2}
@keyframes turn {to {transform: rotate(360deg)}}
.vault {position: fixed; inset: 0; z-index: 9999; pointer-events: none; display: grid; grid-template-columns: 1fr 1fr; overflow: hidden}
.vault b {background: repeating-linear-gradient(0deg, #1B2A47 0 40px, #16223A 40px 80px); animation: left 0.34s 0.62s cubic-bezier(.7, 0, .3, 1) both}
.vault b + b {animation-name: right; border-left: 3px solid #D9A62E}
.lock {position: fixed; top: 50%; left: 50%; z-index: 10000; pointer-events: none; width: 230px; height: 230px; margin: -115px;
       border-radius: 50%; background: #101A2E; border: 10px solid #D9A62E; display: grid; align-content: center; justify-items: center; gap: 0.7rem;
       animation: granted 0.16s 0.4s ease-out both, leave 0.16s 0.6s ease-in both}
.pad {display: flex; gap: 0.4rem}
.pad i {width: 38px; height: 48px; display: grid; place-items: center; font-style: normal; font-weight: 700; font-size: 1.6rem; color: #F4F5F7;
        background: #1F2E4D; border-radius: 6px; animation: digit 0.09s ease-out both}
.pad i:nth-child(1) {animation-delay: 0.05s} .pad i:nth-child(2) {animation-delay: 0.13s}
.pad i:nth-child(3) {animation-delay: 0.21s} .pad i:nth-child(4) {animation-delay: 0.29s}
.lock em {font-style: normal; font-weight: 700; color: #4ADE80; font-size: 1.05rem; animation: appear 0.1s 0.42s both}
@keyframes digit {from {opacity: 0; transform: scale(1.5)} to {opacity: 1; transform: none}}
@keyframes granted {to {border-color: #22C55E; box-shadow: 0 0 34px #22C55E}}
@keyframes appear {from {opacity: 0} to {opacity: 1}}
@keyframes left {to {transform: translateX(-102%)}}
@keyframes right {to {transform: translateX(102%)}}
@keyframes leave {to {opacity: 0; transform: scale(0.8)}}
#passbook {position: fixed; top: 74px; bottom: 26px; right: 8px; z-index: 900; width: 96px; display: flex; flex-direction: column;
           align-items: center; gap: 0.15rem; color: var(--ink); font-variant-numeric: tabular-nums}
#passbook.idle {opacity: 0.45}
#passbook small {color: var(--quiet); font-size: 0.72rem}
#passbook .amount {font-size: 0.82rem; font-weight: 700}
#passbook .tube {position: relative; flex: 1; width: 16px; margin: 1.5rem 0 1.1rem; border-radius: 8px; background: var(--tint);
                 border: 1px solid var(--field-line); cursor: grab; touch-action: none}
#passbook .fill {position: absolute; top: 0; left: 0; right: 0; border-radius: 8px; background: #22A06B; transition: height 0.08s linear}
#passbook .coin {position: absolute; left: 50%; width: 34px; height: 34px; margin: -17px 0 0 -17px; border-radius: 50%; background: #D9A62E; color: #1B2A47;
                 border: 2px solid #1B2A47; display: grid; place-items: center; font-weight: 700; transition: top 0.08s linear, transform 0.25s}
#passbook .coin.flip {transform: rotateY(180deg)}
#passbook .slip {position: absolute; top: 46%; right: 104px; white-space: nowrap; padding: 0.35rem 0.7rem; border-radius: 8px; font-size: 0.85rem; font-weight: 700;
                 color: #FFFFFF; opacity: 0; transform: translateX(10px); transition: opacity 0.14s, transform 0.14s; pointer-events: none}
#passbook .slip.show {opacity: 1; transform: none}
#passbook .slip.in {background: #15803D} #passbook .slip.out {background: #B42318}
[data-testid="stMain"] {scrollbar-width: none}
[data-testid="stMain"]::-webkit-scrollbar {display: none}
.block-container {padding-right: 118px; padding-left: 118px}
.card, [class*="st-key-group-"], .st-key-result, .preview, .plain div {transition: transform 0.16s, box-shadow 0.16s, border-color 0.16s}
.card:hover, [class*="st-key-group-"]:hover, .plain div:hover {transform: translateY(-3px); box-shadow: 0 8px 20px rgba(16, 24, 40, 0.14); border-color: var(--accent)}
.reason {border-radius: 8px; transition: background 0.15s, padding 0.15s}
.reason:hover {background: var(--tint); padding-left: 0.4rem; padding-right: 0.4rem}
.st-key-profiles {background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 0.8rem 1rem}
.profile-label {color: var(--ink); font-weight: 600; margin: 0}
.st-key-next-box {background: var(--tint); border-radius: 12px; padding: 0.75rem}
.next-title {color: var(--ink); font-size: 0.9rem; font-weight: 600; margin: 0}
.next-note {color: var(--quiet); font-size: 0.8rem; margin: 0}
@keyframes pagein {from {opacity: 0; transform: translateY(24px)} to {opacity: 1; transform: none}}
.hero, .card, [class*="st-key-group-"], .st-key-result, .st-key-explorer-panel, .st-key-notes-panel {animation: pagein 0.55s 0.8s ease-out both}
@media (max-width: 860px) {#passbook {display: none} [data-testid="stMain"] {scrollbar-width: auto}
  .block-container {padding-right: 1rem; padding-left: 1rem} .scene .wave-left, .scene .wave-right {display: none}}
@media (prefers-reduced-motion: reduce) {
  .scene i, .hero, .card, [class*="st-key-group-"], .st-key-result, .st-key-explorer-panel, .st-key-notes-panel {animation: none}
  .vault, .lock {display: none}
  .hero::before, .count, .change, .decision.flipped, .ring {animation: none}
}
@media (max-width: 960px) {
  .home-grid {grid-template-columns: 1fr; gap: 1.75rem}
  .preview {max-width: 440px}
}
@media (max-width: 640px) {
  .hero {padding: 1.5rem 1.25rem}
  .home-grid {grid-template-columns: 1fr; gap: 1.5rem}
  .home h1 {font-size: 2.3rem !important}
  .hero h1 {font-size: 2rem}
  .hero .stats {grid-template-columns: repeat(2, 1fr)}
  .st-key-layout > div > [data-testid="stHorizontalBlock"] {flex-direction: column-reverse}
  [data-testid="stColumn"]:has(.st-key-result) {position: static; align-self: stretch}
  .ledger .optional {display: none}
  .plain, .intro-cards, .steps ol {grid-template-columns: 1fr}
  .st-key-explorer-panel iframe, .st-key-explorer-panel div:has(> iframe) {height: 800px !important}
}
</style>
"""

LIGHT = {"canvas": "#D5D9E0", "surface": "#E9EBEF", "tint": "#DDE0E6", "hero": "#0F1B33", "engrave": "#2D4A78", "line": "#C2C7D0",
         "line-soft": "#D3D7DE", "field": "#F1F2F5", "field-line": "#AEB4BF", "ink": "#101828", "quiet": "#4C5563",
         "accent": "#2F5BEA", "on-accent": "#FFFFFF", "good": "#0E9F6E", "good-soft": "#D1FADF", "good-ink": "#05603A", "bad": "#D92D20",
         "bad-soft": "#FEE4E2", "bad-ink": "#912018"}
NIGHT_VAULT = {"canvas": "#0A0D12", "surface": "#12171F", "tint": "#1A212C", "hero": "#12171F", "engrave": "#E8B44C", "line": "#262F3C",
               "line-soft": "#1D2530", "field": "#1A212C", "field-line": "#364152", "ink": "#F3F5F8", "quiet": "#A3AFBF",
               "accent": "#E8B44C", "on-accent": "#12171F", "good": "#34D399", "good-soft": "#10362B", "good-ink": "#6EE7B7", "bad": "#F87171",
               "bad-soft": "#431A1A", "bad-ink": "#FCA5A5"}

# Streamlit's own widgets take their colours from config.toml, so the dark theme restyles them here
NIGHT_WIDGETS = """
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMarkdownContainer"] *,
.stApp [data-testid="stHeading"] *, .stApp [data-testid="stWidgetLabel"] * {color: var(--ink)}
.stApp code {background: var(--tint); color: var(--accent)}
[data-testid="stSelectbox"] input {color: var(--ink); -webkit-text-fill-color: var(--ink)}
[data-testid="stSelectbox"] svg {color: var(--ink); fill: var(--ink)}
[data-testid="stSelectboxVirtualDropdown"] {background: var(--tint); border: 1px solid var(--line)}
[data-testid="stSelectboxVirtualDropdown"] [role="option"], [data-testid="stSelectboxVirtualDropdown"] [role="option"] * {color: var(--ink)}
[data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover, [data-testid="stSelectboxVirtualDropdown"] [aria-selected="true"] {background: var(--line)}
.hero {border: 1px solid var(--line)}
.scene {opacity: 0.6}
.hero::before {opacity: 0.13; filter: sepia(1) saturate(5) hue-rotate(-12deg)}
.hero h1 {color: var(--accent)}
.stApp::before {content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none; transition: background 0.6s;
                background: radial-gradient(60rem 40rem at 85% 30%, var(--aura-soft), transparent 70%)}
[data-testid="stAppViewContainer"] {background: transparent; position: relative; z-index: 1}
.st-key-result {border-color: var(--aura); box-shadow: 0 0 44px -12px var(--aura)}
.dial {filter: drop-shadow(0 0 10px var(--aura))}
"""


INTRO_CARDS = [
    ("The problem", "A lender has to decide who will repay. A wrong yes loses money, and a wrong no turns away a good "
                    "customer. The decision also has to be explainable to the person affected."),
    ("What I built", "A points-based scorecard from 307,511 loan applicants and seven data tables. It turns 15 facts "
                     "into one score, sets the approval cutoff from expected profit, and shows the reasons."),
    ("What it shows", "On applicants held back until the end, the 15-line scorecard reached AUC 0.704 and a complex "
                      "LightGBM model 0.788. Explaining decisions has a measurable cost, which I report openly."),
]
INTRO_STEPS = [("Build features", "One row per applicant from repayment history, with leakage checks."),
               ("Score", "Bin the features, then convert a logistic model into points."),
               ("Decide", "Choose the cutoff from assumed profit, tested across other assumptions."),
               ("Check", "Test on unseen applicants, and measure gaps by gender and age.")]
TECH = "Python, pandas, scikit-learn, LightGBM, SHAP, Streamlit"
REPOSITORY = "https://github.com/Codeatlight/Credit-Risk-Assessment"

PLAIN_ENGLISH = [
    ("What this does", "A lender has to guess who will repay. This tool turns 15 facts about an applicant into one "
                       "score, then approves or refuses, and shows which facts helped or hurt."),
    ("What we expected", "Applicants with higher scores should default less often, and a score that can be explained "
                         "line by line should cost some accuracy against a harder-to-explain model."),
    ("What happened", "Among applicants the model had never seen, about 18% of those scoring 500 to 549 ran into "
                      "payment trouble, against about 3% of those scoring 650 to 699. The best complex model was "
                      "more accurate, as expected."),
    ("How we checked", "We kept 20% of applicants aside and tested on them once at the end. With the outcomes shuffled "
                       "at random, the models scored no better than chance, as an honest setup should. The scoring "
                       "here matches the saved model on 3,000 of those applicants."),
]

st.set_page_config(page_title="Credit Risk Scorecard", layout="wide")
night = st.session_state.get("night", False)
st.html(STYLE.replace("BACKGROUND_DATA", b64encode(BACKGROUND.read_bytes()).decode()))
card = load_card()


def theme_html(night):
    colours = NIGHT_VAULT if night else LIGHT
    variables = " ".join(f"--{name}: {value};" for name, value in colours.items())
    return (f"<style>.stApp, [data-testid='stSelectboxVirtualDropdown'] {{{variables}}} .stApp {{background: var(--canvas)}} "
            f"{NIGHT_WIDGETS if night else ''}</style>")


def aura_html(total):
    """Colour the glow by score: red at the bottom of the scale, through amber, to green at the top."""
    hue = round(dial_position(total) * 1.6)
    return f"<style>.stApp {{--aura: hsl({hue} 75% 55%); --aura-soft: hsl({hue} 75% 45% / 0.16)}}</style>"


def mask(name):
    return f"url('data:image/svg+xml;base64,{b64encode((ART / f'{name}.svg').read_bytes()).decode()}')"


def art_html():
    """Banknote engraving as masks, so its colour follows the theme."""
    rosette, waves = mask("rosette"), mask("waves")
    rules = (f".scene .one, .scene .two {{-webkit-mask-image: {rosette}; mask-image: {rosette}}}"
             f".scene .wave-left, .scene .wave-right {{-webkit-mask-image: {waves}; mask-image: {waves}}}")
    pieces = "".join(f"<i class='{name}'></i>" for name in ["one", "two", "wave-left", "wave-right"])
    return f"<style>{rules}</style><div class='scene' aria-hidden='true'>{pieces}</div>"


def passbook_html():
    """Passes the scrollbar code to the main page, where the scrolling happens."""
    code = json.dumps(PASSBOOK.read_text(encoding="utf-8")).replace("</", "<\\/")
    return f"<script>const page = window.parent.document; const tag = page.createElement('script'); tag.textContent = {code}; page.body.appendChild(tag);</script>"


def set_answers(chosen):
    saved = st.session_state.setdefault("saved_answers", {})
    for feature, position in chosen.items():
        st.session_state[feature] = position
        saved[feature] = position


def profile_answers(kind):
    """Answers for an example applicant, from each line's points."""
    chosen = {}
    for q in card["questions"]:
        order = sorted(range(len(q["answers"])), key=lambda i: q["answers"][i]["points"])
        chosen[q["feature"]] = {"best": order[-1], "typical": q["default"], "weak": order[len(order) // 4]}[kind]
    return chosen


def best_step(answers):
    """The changeable answer worth the most extra points."""
    steps = []
    for q in card["questions"]:
        if q["group"] == FIXED_GROUP:
            continue
        points = [a["points"] for a in q["answers"]]
        best = max(range(len(points)), key=points.__getitem__)
        steps.append((points[best] - points[answers[q["feature"]]], q, best))
    gain, q, best = max(steps, key=lambda step: step[0])
    return (gain, q, best) if gain > 0 else None


def vault(page):
    """Key in the code and open the doors the first time a page opens, not on every answer change."""
    if st.session_state.get("shown_page") == page:
        return
    st.session_state["shown_page"] = page
    st.session_state["visits"] = st.session_state.get("visits", 0) + 1
    digits = "".join(f"<i>{digit}</i>" for digit in VAULT_CODE)
    # The visit number changes the markup, otherwise Streamlit keeps the old finished animation
    st.html(f"<div class='vault' data-visit='{st.session_state['visits']}' aria-hidden='true'><b></b><b></b></div>"
            f"<div class='lock' aria-hidden='true'><div class='pad'>{digits}</div><em>Access granted</em></div>")


def dial_position(value):
    return min(max((value - SCORE_LOW) / (SCORE_HIGH - SCORE_LOW), 0.0), 1.0) * 100


def tool_header_html():
    return """
    <header class="hero compact">
      <h1>Try the scorecard</h1>
      <p class="lead">Change the 15 answers and watch the score, decision and reasons respond.
        A portfolio demo built on public Kaggle data, not a real credit decision.</p>
    </header>"""


def preview_html():
    """A real worked example: the most common answer to every question."""
    answers = {q["feature"]: q["default"] for q in card["questions"]}
    total = score(card, answers)
    against, helping = reasons(card, answers)
    decision = "approve" if is_approved(card, total) else "refuse"
    return f"""
    <div class="preview">
      <div class="verdict"><h3>Example applicant</h3><p class="decision {decision}">{decision.title()}</p></div>
      {dial_html(total, SCORE_LOW, decision)}
      <p class="risk">{risk_of_default(card, total):.1%} estimated risk of default</p>
      {reason_html("Biggest reason against", against[:1], "", "down")}
      {reason_html("Biggest reason for", helping[:1], "", "up")}
    </div>"""


def home_html():
    stats = "".join(f"<p><strong>{value}</strong><span>{label}</span></p>" for value, label in HEADLINE_STATS)
    return f"""
    <header class="hero home">
      <div class="home-grid">
        <div>
          <h1>Who gets the loan, and why?</h1>
          <p class="lead">An explainable credit scorecard that turns 15 facts about an applicant into one score,
            a decision and plain reasons, with the approval cutoff set from expected profit.</p>
          <div class="stats">{stats}</div>
        </div>
        {preview_html()}
      </div>
    </header>"""


def intro_html():
    cards = "".join(f"<div class='card'><h2>{title}</h2><p>{text}</p></div>" for title, text in INTRO_CARDS)
    steps = "".join(f"<li>{title}<p>{text}</p></li>" for title, text in INTRO_STEPS)
    return f"""
    <div class="intro-cards">{cards}</div>
    <div class="card steps"><h2>How it works</h2><ol>{steps}</ol></div>
    <p class="intro-foot">Built with {TECH}. Data: Home Credit Default Risk on Kaggle.
      <a href="{REPOSITORY}" target="_blank" rel="noopener">Code on GitHub</a></p>"""


def go_to(page):
    st.session_state["page"] = page


def reason_html(title, lines, empty, direction):
    rows = "".join(f"<div class='reason'><p>{escape(line['question'])}<small>{escape(line['answer'])}</small></p>"
                   f"<span class='points {direction}'>{line['gap']:+.0f}</span></div>" for line in lines)
    return f"<div class='reasons'><h4>{title}</h4>{rows or f'<p>{empty}</p>'}</div>"


def change_html(total, previous):
    if total == previous:
        return "<p class='change'></p>"
    direction = "up" if total > previous else "down"
    return f"<p class='change {direction}'>{total - previous:+d} points from the last change</p>"


def dial_html(total, previous, decision):
    cutoff = dial_position(card["min_score"])
    label = f"Score {total} on a scale of {SCORE_LOW} to {SCORE_HIGH}, with a cutoff of {card['min_score']}"
    return f"""
    <div class="dial {decision}">
      <div class="gauge" role="img" aria-label="{label}">
        <div class="ring" style="--from: {dial_position(previous):.1f}; --to: {dial_position(total):.1f}; --cut: {cutoff:.1f}"></div>
        <div class="tick" style="--angle: {cutoff * 1.8 - 90:.1f}deg"></div>
      </div>
      <div class="dial-ends" aria-hidden="true"><span>{SCORE_LOW}</span><span>{SCORE_HIGH}</span></div>
      <div class="dial-score">
        <p class="score"><span class="hidden-text">{total}</span>
          <span class="count" aria-hidden="true" style="--from: {previous}; --to: {total}"></span></p>
      </div>
    </div>"""


def result_html(total, previous, risk, against, helping):
    approved = is_approved(card, total)
    decision = "approve" if approved else "refuse"
    flipped = " flipped" if approved != is_approved(card, previous) else ""
    return f"""
    <div role="status" aria-live="polite">
      <div class="verdict"><h3>Result</h3><p class="decision {decision}{flipped}">{decision.title()}</p></div>
      {dial_html(total, previous, decision)}
      <p class="risk">{risk:.1%} estimated risk of default</p>
      {change_html(total, previous)}
      <p class="dial-note">The black mark is the cutoff of {card['min_score']}. Every 50 points doubles the odds of repaying.</p>
      {reason_html("Pulling the score down", against, "Nothing is below a typical applicant.", "down")}
      {reason_html("Lifting the score", helping, "Nothing is above a typical applicant.", "up")}
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


def plain_english_html():
    return "<div class='plain'>" + "".join(f"<div><h3>{title}</h3><p>{text}</p></div>" for title, text in PLAIN_ENGLISH) + "</div>"


st.html(theme_html(night))
st.html(art_html())
page = st.session_state.get("page", "home")
vault(page)
with st.container(key="nav", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
    st.button("Home", key="nav-home", on_click=go_to, args=("home",), type="primary" if page == "home" else "secondary")
    st.button("Scorecard", key="nav-tool", on_click=go_to, args=("tool",), type="primary" if page == "tool" else "secondary")
    st.toggle("Night Vault", key="night", help="Dark theme with a glow that follows the score")
with st.container(key="rail"):
    st.iframe(passbook_html(), height=1)

if page == "home":
    st.html(home_html())
    with st.container(key="cta", horizontal=True):
        st.button("Try the scorecard", key="cta-tool", type="primary", on_click=go_to, args=("tool",))
        st.link_button("View the code", REPOSITORY)
    st.html(intro_html())
    st.stop()

st.html(tool_header_html())
saved = st.session_state.setdefault("saved_answers", {})
with st.container(key="profiles", horizontal=True, vertical_alignment="center"):
    st.html("<p class='profile-label'>Try an applicant:</p>")
    for name, kind in PROFILES.items():
        st.button(name, key=f"profile-{kind}", on_click=set_answers, args=(profile_answers(kind),))

answers = {}
with st.container(key="layout"):
    form, result = st.columns([3, 2], gap="medium")

with form:
    groups = dict.fromkeys(q["group"] for q in card["questions"])
    for number, group in enumerate(groups):
        with st.container(key=f"group-{number}"):
            st.subheader(group)
            left, right = st.columns(2)
            questions = [q for q in card["questions"] if q["group"] == group]
            for position, q in enumerate(questions):
                labels = [a["label"] for a in q["answers"]]
                with left if position % 2 == 0 else right:
                    st.session_state.setdefault(q["feature"], saved.get(q["feature"], q["default"]))
                    answers[q["feature"]] = st.selectbox(q["question"], range(len(labels)),
                                                         format_func=labels.__getitem__, key=q["feature"])
                    saved[q["feature"]] = answers[q["feature"]]

total = score(card, answers)
against, helping = reasons(card, answers)
previous = st.session_state.get("last_score", total)
st.session_state["last_score"] = total
st.html(aura_html(total))

with result:
    with st.container(key="result"):
        st.html(result_html(total, previous, risk_of_default(card, total), against, helping))
        step = best_step(answers)
        if step:
            gain, question, position = step
            with st.container(key="next-box"):
                st.html("<p class='next-title'>Biggest available gain</p>")
                st.button(f"{question['question']}: {question['answers'][position]['label']} (+{gain})", key="next-step",
                          width="stretch", on_click=set_answers, args=({question['feature']: position},))
                st.html("<p class='next-note'>Shows how the points work, not financial advice.</p>")

with st.container(key="explorer-panel"):
    explorer = EXPLORER.read_text(encoding="utf-8").replace("__STATS__", STATS.read_text(encoding="utf-8"))
    st.iframe(explorer.replace("__THEME__", "night" if night else "light"), height=EXPLORER_HEIGHT)

with st.container(key="notes-panel"):
    st.subheader("How the score adds up")
    st.html(ledger_html(total, answers))

    st.subheader("In plain English")
    st.html(plain_english_html())

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
    st.html("<p class='source-note'>The bars behind the title show how real applicants' scores are spread.</p>")
