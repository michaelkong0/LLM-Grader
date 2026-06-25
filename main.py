import io
from typing import Dict, Any

import pandas as pd
import streamlit as st

# ... [all the scoring helpers, DISCERN / PEMAT / JAMA / HON definitions above stay identical] ...


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

# Choose text column & metadata columns
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

# Navigation buttons
nav_left, nav_right = st.columns(2)
with nav_left:
    if st.button("⟵ Previous", use_container_width=True, disabled=st.session_state.current_idx <= 0):
        st.session_state.current_idx = max(0, st.session_state.current_idx - 1)
with nav_right:
    if st.button("Next ⟶", use_container_width=True, disabled=st.session_state.current_idx >= n_rows - 1):
        st.session_state.current_idx = min(n_rows - 1, st.session_state.current_idx + 1)

row_idx = st.session_state.current_idx
row = df.iloc[row_idx]

# Make left slightly larger and scrollable
left, right = st.columns([1.7, 1.3])

with left:
    st.subheader(f"Response {row_idx + 1} / {n_rows}")
    st.markdown(f"**Model:** {row.get(model_col, '')}")
    if prompt_col != "<none>":
        st.markdown(f"**Prompt:** {row.get(prompt_col, '')}")
    st.markdown("---")

    response_md = str(row.get(text_col, ""))

    # Scrollable container for long text
    st.markdown(
        f"""
        <div style="
            height: 500px;
            overflow-y: auto;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #fafafa;
            ">
            {response_md.replace('\n', '<br>')}
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.subheader("Ratings")

    with st.form(key=f"rating_form_{row_idx}"):

        # DISCERN as radio buttons
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

        # PEMAT Understandability as radio buttons
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

        # PEMAT Actionability as radio buttons
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

        # Likert ratings as radio buttons
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

        submitted = st.form_submit_button("Save ratings for this response")

    if submitted:
        # DISCERN
        for i in DISCERN_ITEMS.keys():
            df.loc[row_idx, f"discern_q{i}"] = st.session_state[f"discern_q{i}_{row_idx}"]

        # PEMAT understandability
        for i in PEMAT_UNDER_TEXT.keys():
            val = st.session_state[f"pemat_u_q{i}_{row_idx}"]
            df.loc[row_idx, f"pemat_u_q{i}"] = -1 if val == "N/A" else val

        # PEMAT actionability
        for i in PEMAT_ACT_TEXT.keys():
            val = st.session_state[f"pemat_a_q{i}_{row_idx}"]
            df.loc[row_idx, f"pemat_a_q{i}"] = -1 if val == "N/A" else val

        # JAMA
        for col_name in JAMA_ITEMS.keys():
            df.loc[row_idx, col_name] = st.session_state[f"{col_name}_{row_idx}"]

        # HON
        for col_name in HON_ITEMS.keys():
            df.loc[row_idx, col_name] = st.session_state[f"{col_name}_{row_idx}"]

        # Likert
        for label, col_name in [
            ("Accuracy", "rating_accuracy"),
            ("Comprehensiveness", "rating_comprehensiveness"),
            ("Accessibility", "rating_accessibility"),
        ]:
            df.loc[row_idx, col_name] = st.session_state[f"{col_name}_{row_idx}"]

        # Recompute DISCERN + PEMAT aggregates
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
