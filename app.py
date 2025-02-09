import streamlit as st
import pandas as pd
from pyhive import presto
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes, DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import time

# Watsonx Credentials (Hardcoded for demo purposes)
credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "XfyqbHqkZSatzDxeQzzEdQbfu-DP-_ihUvSSmrmIiTmT"
}
project_id = "289854e9-af72-4464-8bb2-4dedc59ad405"

# Watsonx Model Initialization
model_id = "meta-llama/llama-3-405b-instruct"
parameters = {
    GenParams.MIN_NEW_TOKENS: 10,
    GenParams.MAX_NEW_TOKENS: 196,
    GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
    GenParams.TEMPERATURE: 0.7,
    GenParams.REPETITION_PENALTY: 1
}
model = Model(
    model_id=model_id,
    params=parameters,
    credentials=credentials,
    project_id=project_id
)

# Presto Connection Parameters
PRESTO_HOST = "98.82.128.53"
PRESTO_PORT = 8443
PRESTO_USERNAME = "ibmlhadmin"
PRESTO_PASSWORD = "password"

# Streamlit App UI
st.markdown("<h1 style='text-align: center;'>NLP with WatsonX.data</h1>", unsafe_allow_html=True)

# Sidebar for Configuration
st.sidebar.header("Configuration")
catalog = st.sidebar.selectbox("Select Catalog", ["tpch", "cloud_cos", "analytics_catalog"])
schema = st.sidebar.selectbox("Select Schema", ["sf100", "adidas1", "schema2"])

# Interactive Chat Section
st.header("Chat with WatsonX SQL Generator")
user_input = st.text_area("Enter your SQL request", "Write a SQL statement to select all rows from a table called customer.")

if st.button("Generate SQL"):
    with st.spinner("Generating SQL query..."):
        try:
            response = model.generate_text(prompt=user_input)
            generated_query = response.strip() if isinstance(response, str) else response.get("generated_text", "").strip()
            if generated_query:
                st.session_state["generated_query"] = generated_query
                st.success("SQL query generated successfully!")
                st.code(generated_query, language="sql")
            else:
                st.error("Error: Generated query is empty.")
        except Exception as e:
            st.error(f"Error generating SQL: {e}")

# Reasoning Feature
if "generated_query" in st.session_state and st.button("Reason"):
    with st.spinner("Generating explanation..."):
        explanation = model.generate_text(prompt=f"Explain the following SQL query: {st.session_state['generated_query']}")
        st.write("### Explanation")
        st.write(explanation)

# RAG Feature (Executing SQL Query)
if "generated_query" in st.session_state and st.button("RAG (Retrieve Data)"):
    with st.spinner("Executing SQL query..."):
        try:
            conn = presto.connect(
                host=PRESTO_HOST,
                port=PRESTO_PORT,
                catalog=catalog,
                schema=schema,
                username=PRESTO_USERNAME,
                password=PRESTO_PASSWORD,
                protocol="https",
                requests_kwargs={"verify": False}  # Bypass SSL verification
            )
            df = pd.read_sql(st.session_state["generated_query"], conn)
            st.success("Query executed successfully!")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error executing SQL query: {e}")
