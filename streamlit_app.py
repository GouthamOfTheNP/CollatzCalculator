import ast
import math
import time
import random
import operator
import pandas as pd
import altair as alt
import streamlit as st

MAX_DIGITS = 10000

st.set_page_config(page_title="Collatz Conjecture Explorer", page_icon="🔢", layout="wide")


def new_captcha():
    operations = [
        (lambda a, b: a + b, '+'),
        (lambda a, b: a * b, '×')
    ]
    
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    op_func, op_symbol = random.choice(operations)
    
    if op_symbol == '-':
        a = random.randint(10, 30)
        b = random.randint(1, a)
    
    st.session_state['captcha_a'] = a
    st.session_state['captcha_b'] = b
    st.session_state['captcha_op'] = op_func
    st.session_state['captcha_symbol'] = op_symbol
    st.session_state['captcha_answer'] = op_func(a, b)
    st.session_state['captcha_passed'] = False
    st.session_state['captcha_feedback'] = None


if 'captcha_passed' not in st.session_state:
    new_captcha()

st.title("Collatz Conjecture Explorer")

if not st.session_state.get('captcha_passed', False):
    st.markdown("This app explores the Collatz Conjecture by generating and visualizing the sequence for a given positive integer input. Please solve the CAPTCHA below to continue.")
    
    a = st.session_state['captcha_a']
    b = st.session_state['captcha_b']
    symbol = st.session_state['captcha_symbol']
    
    with st.form("captcha_form"):
        captcha_input = st.number_input(
            f"What is {a} {symbol} {b}?", 
            min_value=0, 
            max_value=1000,
            step=1, 
            format="%d"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Submit", use_container_width=True)
        
        with col2:
            refresh = st.form_submit_button("New Captcha", use_container_width=True)
        
        if submitted:
            if captcha_input == st.session_state['captcha_answer']:
                st.session_state['captcha_passed'] = True
                st.session_state['captcha_feedback'] = 'success'
                with st.spinner("Verifying..."):
                    time.sleep(2)
                    st.rerun()
            else:
                st.session_state['captcha_feedback'] = 'error'
        
        if refresh:
            new_captcha()
            st.session_state['captcha_feedback'] = None
            st.rerun()
    
    if st.session_state.get('captcha_feedback') == 'error':
        st.error("Incorrect answer. Please try again.")

if st.session_state.get('captcha_passed', False):
    st.badge("Visual Logarithmic Scale: e")
    user_input = st.text_input("Enter a positive integer (supports commas and powers like 10^25).")
    if user_input.strip() != "":
        st.session_state["user_input"] = user_input
else:
    user_input = ""


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


@st.cache_data(max_entries=10)
def compute_full_sequence(n):
    return [str(val) for val in collatz_generator(n)]


if st.session_state.get('captcha_passed', False) and st.session_state.get("user_input", "") != "":
    try:
        n = parse_number(st.session_state.get("user_input", ""))
        if n <= 0:
            st.error("Please enter a positive integer.")
        else:
            with st.spinner("Calculating Collatz sequence..."):
                log_sequence = compute_log_sequence(n)
                with st.spinner("Rendering sequence values"):
                    df = pd.DataFrame({"Step": range(len(log_sequence)), "Value": log_sequence})
                    chart = alt.Chart(df).mark_line().encode(x="Step", y="Value")
                    st.altair_chart(chart, use_container_width=True)
                st.info(f"Sequence length (excluding start): {len(log_sequence) - 1}")
                
                sequence_str = compute_sequence_strings(n)
                full_sequence_str = compute_full_sequence(n)
                
                with st.spinner("Preparing full sequence display"):
                    df_display = pd.DataFrame({
                        "Step": range(len(sequence_str)),
                        "Value": sequence_str
                    })
                    
                if 'expander_open' not in st.session_state:
                    st.session_state['expander_open'] = False
                
                with st.expander("Full Collatz sequence", expanded=st.session_state['expander_open']):
                        if len(sequence_str) >= 10000:
                            st.warning("⚠️ Sequence truncated to first 10,000 values for display.")
                        st.dataframe(df_display, height=600)
                        csv_data = pd.DataFrame({
                            "Step": range(len(full_sequence_str)),
                            "Value": full_sequence_str
                        }).to_csv(index=False).encode('utf-8')
                        st.download_button("Download full sequence as CSV", csv_data, file_name="collatz_sequence.csv")
                        st.session_state['expander_open'] = True

    except ValueError:
        st.error("Invalid input or too large of an input. Please enter a positive integer (supports commas and powers like 10^25).")
