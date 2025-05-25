from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import sqlite3
import google.generativeai as genai

# Configure GenAI Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load Gemini model and generate SQL query
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
    response = model.generate_content([prompt, question])
    return response.text.strip()

# Read and execute SQL query on the database
def read_sql_query(sql, db_path):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        col_names = [description[0] for description in cur.description]
        conn.close()
        return rows, col_names, None
    except sqlite3.Error as e:
        return [], [], f"SQLite error: {e}"

# Prompt to Gemini
prompt = """
You are an expert at converting English questions into SQL queries.
The SQL database is named STUDENT and has the following columns:
- NAME (Text)
- CLASS (Text)
- SECTION (Text)

Here are some examples:
1. English: How many entries of records are present?
   SQL: SELECT COUNT(*) FROM STUDENT;

2. English: Tell me all the students studying in Data Science class.
   SQL: SELECT * FROM STUDENT WHERE CLASS = "Data Science";

Ensure your response is only valid SQL — no explanations, no markdown, no triple backticks.
"""

# Streamlit App
st.set_page_config(page_title="SQL Assistant", page_icon="🔍")
st.title("🔍 HelloSQL: Ask Questions in English")

question = st.text_input("💬 Enter your question:")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Generating SQL query..."):
            sql_query = get_gemini_response(question, prompt)
            st.code(sql_query, language='sql')

            # Check if SQL query looks valid before execution
            if not sql_query.lower().startswith(("select", "with")):
                st.error("The generated query doesn't seem to be a valid SQL SELECT query.")
            else:
                rows, columns, error = read_sql_query(sql_query, "student.db")
                if error:
                    st.error(error)
                elif not rows:
                    st.info("Query executed successfully, but no results found.")
                else:
                    st.success("Query executed successfully.")
                    st.table([dict(zip(columns, row)) for row in rows])

# Show available Gemini models
if st.button("Show Available Models"):
    with st.spinner("Fetching models..."):
        try:
            models = genai.list_models()
            st.subheader("🧠 Available Models")
            for model in models:
                st.markdown(f"**{model.name}**")
                st.markdown(f"Supported: `{', '.join(model.supported_generation_methods)}`")
                st.markdown("---")
        except Exception as e:
            st.error(f"Error fetching models: {e}")
