import math
import ast
import operator
import streamlit as st
import pandas as pd
import altair as alt

MAX_DIGITS = 10000

st.set_page_config(page_title="Collatz Conjecture Explorer", page_icon="🔢")
st.title("Collatz Conjecture Explorer")
st.badge("Visual Logarithmic Scale: e")

user_input = st.text_input("Enter a positive integer (supports commas and powers like 10^25).")


@st.cache_data
def parse_number(s: str) -> int:
    s = s.replace(",", "").replace(" ", "")
    s = s.replace("^", "**")

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.floordiv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Unsupported operator: {op_type}")
            if op_type is ast.Pow:
                if left <= 0 or right < 0:
                    raise ValueError("Invalid exponentiation")
                est_digits = right * math.log10(left)
                if est_digits > MAX_DIGITS:
                    raise ValueError(f"Number too large: exceeds {MAX_DIGITS} digits")
            return operators[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in operators:
                raise ValueError(f"Unsupported unary operator: {op_type}")
            return operators[op_type](eval_node(node.operand))
        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, int):
                raise ValueError("Only integers are allowed")
            return node.value
        else:
            raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    try:
        tree = ast.parse(s, mode='eval')
        value = eval_node(tree)
    except Exception as e:
        raise ValueError(f"Invalid numerical expression: {e}")

    if not isinstance(value, int) or value <= 0:
        raise ValueError("Result is not a positive integer")
    return value

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

                df = pd.DataFrame({"Step": range(len(log_sequence)), "Value": log_sequence})
                chart = alt.Chart(df).mark_line().encode(x="Step", y="Value")
                st.altair_chart(chart, use_container_width=True)
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
        st.error("Invalid input or too large of an input. Please enter a positive integer (supports commas and powers like 10^25).")
