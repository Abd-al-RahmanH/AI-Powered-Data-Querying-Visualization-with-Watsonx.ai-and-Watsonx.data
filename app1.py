import streamlit as st
import pandas as pd
from sqlalchemy.engine import create_engine
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# 🔹 Watsonx Credentials
credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "XfyqbHqkZSatzDxeQzzEdQbfu-DP-_ihUvSSmrmIiTmT"
}
project_id = "289854e9-af72-4464-8bb2-4dedc59ad405"

# 🔹 Initialize WatsonX Model
model_id = "meta-llama/llama-3-405b-instruct"
parameters = {
    GenParams.MIN_NEW_TOKENS: 10,
    GenParams.MAX_NEW_TOKENS: 196,
    GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
    GenParams.TEMPERATURE: 0.7,
    GenParams.REPETITION_PENALTY: 1
}
model = ModelInference(
    model_id=model_id,
    params=parameters,
    credentials=credentials,
    project_id=project_id
)

# 🔹 Presto Connection Parameters (Hardcoded)
PRESTO_HOST = "34.238.192.61"
PRESTO_PORT = 8443
PRESTO_USERNAME = "ibmlhadmin"
PRESTO_PASSWORD = "password"
CATALOG = "tpch"
SCHEMA = "sf100"

# 🔹 Create Presto Connection Using SQLAlchemy
engine = create_engine(
    f"presto://{PRESTO_USERNAME}:{PRESTO_PASSWORD}@{PRESTO_HOST}:{PRESTO_PORT}/{CATALOG}/{SCHEMA}?protocol=https"
)

# 🔹 Streamlit App UI
st.markdown("<h1 style='text-align: center; color: #2196F3;'>NLP-Powered Data Querying</h1>", unsafe_allow_html=True)

# 🔹 User Input for NLP Query
st.header("Ask a Question")
nlp_query = st.text_area("Enter your question", "How many customers are in the customer table?")

if st.button("Get Answer"):
    with st.spinner("Processing your question..."):
        try:
            # 🔹 Step 1: Convert NLP Query to SQL Query
            sql_prompt = f"Convert this question into a SQL query using the `{CATALOG}` catalog and `{SCHEMA}` schema: {nlp_query}"
            response = model.generate_text(prompt=sql_prompt)
            generated_query = response.strip()
            st.info(f"Generated SQL: ```{generated_query}```")

            # 🔹 Step 2: Execute the Query in Presto
            df = pd.read_sql(generated_query, engine)

            # 🔹 Step 3: Display Results
            st.success(f"Answer from `{CATALOG}.{SCHEMA}`:")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error processing query: {e}")
