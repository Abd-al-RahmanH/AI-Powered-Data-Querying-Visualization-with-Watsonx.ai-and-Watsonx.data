import streamlit as st
import pandas as pd
from pyhive import presto
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes, DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# Watsonx Credentials
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

# Presto Connection Parameters (Hardcoded tpch catalog and sf100 schema)
PRESTO_HOST = "34.238.192.61"
PRESTO_PORT = 8443
PRESTO_USERNAME = "ibmlhadmin"
PRESTO_PASSWORD = "password"
CATALOG = "tpch"
SCHEMA = "sf100"

# Streamlit App
st.markdown("<h1 style='text-align: center; color: #2196F3;'>NLP with WatsonX.data</h1>", unsafe_allow_html=True)

# User Input for NLP Query
st.header("Ask a Question")
nlp_query = st.text_area("Enter your question", "How many customers are there in the customer table?")

if st.button("Get Answer"):
    with st.spinner("Processing your question..."):
        try:
            # Generate SQL query from NLP query
            sql_prompt = f"Convert this question into a SQL query using the tpch catalog and sf100 schema: {nlp_query}"
            response = model.generate_text(prompt=sql_prompt)
            generated_query = response.strip()
            
            # Execute SQL query
            conn = presto.connect(
                host=PRESTO_HOST,
                port=PRESTO_PORT,
                catalog=CATALOG,
                schema=SCHEMA,
                username=PRESTO_USERNAME,
                password=PRESTO_PASSWORD,
                protocol="https",
                requests_kwargs={"verify": False}
            )
            df = pd.read_sql(generated_query, conn)
            
            # Display result in statement and table format
            st.success(f"Answer: Based on the data from `{CATALOG}.{SCHEMA}`, here are the results:")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error processing query: {e}")
