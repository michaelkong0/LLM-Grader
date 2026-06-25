import io
from typing import Dict, Any

import pandas as pd
import streamlit as st

# =============================
# Scoring helpers
# =============================

DISCERN_SECTION1 = list(range(1, 9))
DISCERN_SECTION2 = list(range(9, 16))

def score_discern(row: pd.Series) -> Dict[str, Any]:
    s1 = sum(row.get(f"discern_q{i}", None) or 0 for i in DISCERN_SECTION1)
    s2 = sum(row.get(f"discern_q{i}", None) or 0 for i in DISCERN_SECTION2)
    total_1_15 = s1 + s2
    return {
        "discern_section1_sum": s1,
        "discern_section2_sum": s2,
        "discern_total_1_15": total_1_15,
        "discern_total_mean_1_15": total_1_15 / 15.0 if total_1_15 else 0.0,
    }

PEMAT_UNDER_ITEMS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19]
PEMAT_ACT_ITEMS = [20, 21, 22, 23, 24, 25, 26]

def score_pemat(row: pd.Series) -> Dict[str, Any]:
    u_vals = []
    for i in PEMAT_UNDER_ITEMS:
        v = row.get(f"pemat_u_q{i}", None)
        if v is not None and v != -1:
            u_vals.append(v)
    a_vals = []
    for i in PEMAT_ACT_ITEMS:
        v = row.get(f"pemat_a_q{i}", None)
        if v is not None and v != -1:
            a_vals.append(v)

    u_score = 100 * (sum(u_vals) / len(u_vals)) if u_vals else None
    a_score = 100 * (sum(a_vals) / len(a_vals)) if a_vals else None

    return {
        "pemat_understand_points": sum(u_vals) if u_vals else None,
        "pemat_understand_items": len(u_vals),
        "pemat_understand_score_pct": u_score,
        "pemat_action_points": sum(a_vals) if a_vals else None,
        "pemat_action_items": len(a_vals),
        "pemat_action_score_pct": a_score,
    }

# =============================
# Rating item definitions
# =============================

DISCERN_ITEMS = {
    1: "Are the aims clear?",
    2: "Does it achieve its aims?",
    3: "Is it relevant?",
    4: "Is it clear what sources of information were used (other than author/producer)?",
    5: "Is it clear when the information was produced?",
    6: "Is it balanced and unbiased?",
    7: "Does it provide details of additional sources of support and information?",
    8: "Does it refer to areas of uncertainty?",
    9: "Does it describe how the treatment works?",
    10: "Does it describe the benefits of each treatment?",
    11: "Does it describe the risks of each treatment?",
    12: "Does it describe what would happen if no treatment is used?",
    13: "Does it describe how treatment choices affect overall quality of life?",
    14: "Is it clear that there may be more than one possible treatment choice?",
    15: "Does it provide support for shared decision-making?",
    16: "Overall quality as a source of information on treatment choices.",
}

PEMAT_UNDER_TEXT = {
    1: "The material makes its purpose completely evident.",
    2: "The material does not include information that distracts from its purpose.",
    3: "The material uses common, everyday language.",
    4: "Medical terms are defined or used only to familiarize the audience.",
    5: "The material uses the active voice.",
    6: "Numbers are clear and easy to understand. (No numbers = N/A)",
    7: "The material does not expect the user to perform calculations.",
    8: "Information is broken into short sections. (Very short material = N/A)",
    9: "Sections have informative headers. (Very short material = N/A)",
    10: "Information is presented in a logical sequence.",
    11: "The material provides a summary. (Very short material = N/A)",
    12: "The material uses visual cues (arrows, boxes, bullets, bold, larger font…). (Video = N/A)",
    15: "The material uses visual aids when they help understanding.",
    16: "Visual aids reinforce rather than distract.",
    17: "Visual aids have clear titles or captions.",
    18: "Illustrations/photos are clear and uncluttered. (No visual aids = N/A)",
    19: "Tables are simple with clear headings. (No tables = N/A)",
}

PEMAT_UNDER_NA = {6, 8, 9, 11, 12, 18, 19}

PEMAT_ACT_TEXT = {
    20: "The material clearly identifies at least one action the user can take.",
    21: "The material addresses the user directly when describing actions.",
    22: "Actions are broken into manageable, explicit steps.",
    23: "The material provides a tangible tool (checklist, planner, etc.) when helpful.",
    24: "The material provides simple instructions/examples for calculations. (No calculations = N/A)",
    25: "The material explains how to use charts/graphs/tables/diagrams to take action. (No such visuals = N/A)",
    26: "The material uses visual aids when they help the user act on instructions.",
}

PEMAT_ACT_NA = {24, 25}

JAMA_ITEMS = {
    "jama_authorship": "Authorship: Authors/editors and their credentials provided?",
    "jama_attribution": "Attribution: References and sources explicitly listed?",
    "jama_disclosure": "Disclosure: Sponsorship/advertising/commercial interests stated?",
    "jama_currency": "Currency: Dates for posting and updates clearly provided?",
}

HON_ITEMS = {
    "hon_authority": "Authority: Does it show who wrote the information and advice?",
    "hon_complementarity": "Complementarity: Does it state purpose and target audience?",
    "hon_privacy": "Privacy: Does it state how personal data are used?",
    "hon_attribution": "Attribution: Does it state sources and dates of information?",
    "hon_justifiability": "Justifiability: Is information presented fairly and justified?",
    "hon_transparency": "Transparency: Contact info for responsible people / error contact?",
    "hon_financial_disclosure": "Financial Disclosure: Who pays and any conflicts of interest?",
    "hon_advertising_policy": "Advertising Policy: Is advertising clearly distinguished from content?",
}

LIKERT_LABELS = [
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]

# =============================
# Streamlit app
# =============================

st.set_page_config(page_title="Patient Education Grader", layout="wide")

st.title("Patient Education Grading UI")

uploaded = st.file_uploader("Upload Excel file with COMPLETE responses", type=["xlsx", "xls"])

if "df" not in st.session_state:
    st.session_state.df = None

if uploaded is not None:
    df = pd.read_excel(uploaded)
    st.session_state.df = df
    st.session_state.current_idx = 0  # reset index on new file

if st.session_state.df is None:
    st.info("Upload an Excel file to begin.")
    st.stop()

df = st.session_state.df

# Choose columns
cols = list(df.columns)
text_col = st.selectbox(
    "Text column (Complete response)",
    cols,
    index=cols.index("Complete Response") if "Complete Response" in cols else 0,
)
model_col = st.selectbox(
    "Model column",
    cols,
    index=cols.index("Model") if "Model" in cols else 0,
)
prompt_col = st.selectbox("Prompt column (optional)", ["<none>"] + cols)

n_rows = len(df)
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0

# Navigation
nav_left, nav_right = st.columns(2)
with nav_left:
    if st.button("⟵ Previous", use_container_width=True, disabled=st.session_state.current_idx <= 0):
        st.session_state.current_idx = max(0, st.session_state.current_idx - 1)
with nav_right:
    if st.button("Next ⟶", use_container_width=True, disabled=st.session_state.current_idx >= n_rows - 1):
        st.session_state.current_idx = min(n_rows - 1, st.session_state.current_idx + 1)

row_idx = st.session_state.current_idx
row = df.iloc[row_idx]

# Layout: left (scrollable text), right (ratings)
left, right = st.columns([1.7, 1.3])

with left:
    st.subheader(f"Response {row_idx + 1} / {n_rows}")
    st.markdown(f"**Model:** {row.get(model_col, '')}")
    if prompt_col != "<none>":
        st.markdown(f"**Prompt:** {row.get(prompt_col, '')}")
    st.markdown("---")

    response_md = str(row.get(text_col, ""))

    # Scrollable text area for long responses
    st.text_area(
        "Response text",
        value=response_md,
        height=500,          # adjust height as you like
    )

with right:
    st.subheader("Ratings")

    # SINGLE form with explicit submit button
    with st.form(key=f"rating_form_{row_idx}"):

        # DISCERN
        with st.expander("DISCERN (1–5)", expanded=True):
            for i, text in DISCERN_ITEMS.items():
                col_name = f"discern_q{i}"
                key = f"{col_name}_{row_idx}"
                raw_val = row.get(col_name, None)
                default = raw_val if raw_val in [1, 2, 3, 4, 5] else 3
                st.session_state.setdefault(key, default)
                st.radio(
                    f"Q{i}. {text}",
                    options=[1, 2, 3, 4, 5],
                    index=[1, 2, 3, 4, 5].index(st.session_state[key]),
                    key=key,
                    horizontal=True,
                )

        # PEMAT – Understandability
        with st.expander("PEMAT – Understandability (0=Disagree,1=Agree,N/A)", expanded=False):
            for i, text in PEMAT_UNDER_TEXT.items():
                col_name = f"pemat_u_q{i}"
                key = f"{col_name}_{row_idx}"
                raw_val = row.get(col_name, None)
                default = "N/A" if raw_val == -1 else raw_val
                if default not in [0, 1, "N/A"]:
                    default = 0
                st.session_state.setdefault(key, default)
                options = [0, 1, "N/A"]
                st.radio(
                    f"U{i}. {text}",
                    options=options,
                    index=options.index(st.session_state[key]),
                    key=key,
                    horizontal=True,
                )

        # PEMAT – Actionability
        with st.expander("PEMAT – Actionability (0=Disagree,1=Agree,N/A)", expanded=False):
            for i, text in PEMAT_ACT_TEXT.items():
                col_name = f"pemat_a_q{i}"
                key = f"{col_name}_{row_idx}"
                raw_val = row.get(col_name, None)
                default = "N/A" if raw_val == -1 else raw_val
                if default not in [0, 1, "N/A"]:
                    default = 0
                st.session_state.setdefault(key, default)
                options = [0, 1, "N/A"]
                st.radio(
                    f"A{i}. {text}",
                    options=options,
                    index=options.index(st.session_state[key]),
                    key=key,
                    horizontal=True,
                )

        # JAMA
        with st.expander("JAMA Benchmark (0=No, 1=Yes)", expanded=False):
            for col_name, text in JAMA_ITEMS.items():
                key = f"{col_name}_{row_idx}"
                raw_val = row.get(col_name, None)
                default = int(raw_val) if raw_val in [0, 1] else 0
                st.session_state.setdefault(key, default)
                st.radio(
                    text,
                    options=[0, 1],
                    index=[0, 1].index(st.session_state[key]),
                    key=key,
                    horizontal=True,
                )

        # HON
        with st.expander("HONcode principles (0=No, 1=Yes)", expanded=False):
            for col_name, text in HON_ITEMS.items():
                key = f"{col_name}_{row_idx}"
                raw_val = row.get(col_name, None)
                default = int(raw_val) if raw_val in [0, 1] else 0
                st.session_state.setdefault(key, default)
                st.radio(
                    text,
                    options=[0, 1],
                    index=[0, 1].index(st.session_state[key]),
                    key=key,
                    horizontal=True,
                )

        # Likert
        with st.expander("Overall ratings (1–5)", expanded=False):
            for label, col_name in [
                ("Accuracy", "rating_accuracy"),
                ("Comprehensiveness", "rating_comprehensiveness"),
                ("Accessibility", "rating_accessibility"),
            ]:
                key = f"{col_name}_{row_idx}"
                raw_val = row.get(col_name, None)
                default = raw_val if raw_val in [1, 2, 3, 4, 5] else 3
                st.session_state.setdefault(key, default)
                st.radio(
                    label,
                    options=[1, 2, 3, 4, 5],
                    index=[1, 2, 3, 4, 5].index(st.session_state[key]),
                    key=key,
                    horizontal=True,
                )

        # THE submit button the warning is complaining about if missing
        submitted = st.form_submit_button("Save ratings for this response")

    if submitted:
        # Write all ratings back
        for i in DISCERN_ITEMS.keys():
            df.loc[row_idx, f"discern_q{i}"] = st.session_state[f"discern_q{i}_{row_idx}"]

        for i in PEMAT_UNDER_TEXT.keys():
            val = st.session_state[f"pemat_u_q{i}_{row_idx}"]
            df.loc[row_idx, f"pemat_u_q{i}"] = -1 if val == "N/A" else val

        for i in PEMAT_ACT_TEXT.keys():
            val = st.session_state[f"pemat_a_q{i}_{row_idx}"]
            df.loc[row_idx, f"pemat_a_q{i}"] = -1 if val == "N/A" else val

        for col_name in JAMA_ITEMS.keys():
            df.loc[row_idx, col_name] = st.session_state[f"{col_name}_{row_idx}"]

        for col_name in HON_ITEMS.keys():
            df.loc[row_idx, col_name] = st.session_state[f"{col_name}_{row_idx}"]

        for label, col_name in [
            ("Accuracy", "rating_accuracy"),
            ("Comprehensiveness", "rating_comprehensiveness"),
            ("Accessibility", "rating_accessibility"),
        ]:
            df.loc[row_idx, col_name] = st.session_state[f"{col_name}_{row_idx}"]

        # Recompute aggregates
        row_after = df.loc[row_idx]
        disc_scores = score_discern(row_after)
        pemat_scores = score_pemat(row_after)
        for k, v in disc_scores.items():
            df.loc[row_idx, k] = v
        for k, v in pemat_scores.items():
            df.loc[row_idx, k] = v

        st.session_state.df = df
        st.success("Ratings saved for this response.")

# Download graded Excel
st.markdown("---")
st.subheader("Download graded Excel")

buffer = io.BytesIO()
st.session_state.df.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    label="Download graded Excel",
    data=buffer,
    file_name="graded_responses_ui.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
