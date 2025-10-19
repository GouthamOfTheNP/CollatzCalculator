import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="Collatz Conjecture Explorer", page_icon="🔢")
st.title("Collatz Conjecture Explorer")
st.badge("Visual Logarithmic Scale")

user_input = st.text_input("Enter a positive integer (supports commas and powers like 10^25).")


@st.cache_data
def parse_number(s: str) -> int:
    s = s.replace(",", "").strip()
    if "^" in s:
        base, exp = s.split("^")
        return int(base) ** int(exp)
    return int(s)


def collatz_generator(n):
    while n != 1:
        yield n
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    yield 1


@st.cache_data
def compute_log_sequence(n):
    return [math.log(x) for x in collatz_generator(n)]


@st.cache_data(max_entries=10)
def compute_sequence_strings(n, max_items=10000):
    sequence_str = []
    for i, val in enumerate(collatz_generator(n)):
        if i >= max_items:
            sequence_str.append(f"... (truncated at {max_items} items)")
            break
        sequence_str.append(str(val))
    return sequence_str


if user_input:
    try:
        n = parse_number(user_input)
        if n <= 0:
            st.error("Please enter a positive integer.")
        else:
            with st.spinner(f"Calculating Collatz sequence for {n}..."):
                log_sequence = compute_log_sequence(n)
                
                st.line_chart(log_sequence)
                st.badge(f"Sequence length (excluding start): {len(log_sequence) - 1}")
                
                sequence_str = compute_sequence_strings(n)
                
                df = pd.DataFrame({
                    "Step": range(len(sequence_str)),
                    "Value": sequence_str
                })
                
                with st.expander("Full Collatz sequence"):
                    if len(sequence_str) >= 10000:
                        st.warning("⚠️ Sequence truncated to first 10,000 values for display.")
                    st.dataframe(df, height=600)

    except ValueError:
        st.error("Invalid input. Please enter a positive integer (supports commas and powers like 10^25).")