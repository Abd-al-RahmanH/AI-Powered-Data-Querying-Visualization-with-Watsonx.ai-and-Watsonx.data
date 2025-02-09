import streamlit as st
import pandas as pd
import plotly.express as px
from pyhive import presto
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes, DecodingMethods
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import time

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

# Presto Connection Parameters
PRESTO_HOST = "34.238.192.61"
PRESTO_PORT = 8443
PRESTO_USERNAME = "ibmlhadmin"
PRESTO_PASSWORD = "password"

# Define available catalogs and schemas
catalog_schema_map = {
    "rahmans_cos": ["adidas1", "schema2"],
    "tpch": ["sf100"],
    "analytics_catalog": ["schema2"]
}

def extract_catalog_schema(prompt):
    """Extract catalog and schema from the prompt."""
    detected_catalog = None
    detected_schema = None
    for catalog, schemas in catalog_schema_map.items():
        if catalog in prompt.lower():
            detected_catalog = catalog
            for schema in schemas:
                if schema in prompt.lower():
                    detected_schema = schema
                    break
    return detected_catalog, detected_schema

# Streamlit App
st.markdown("<h1 style='text-align: center; color: #2196F3;'>NLP with WatsonX.data</h1>", unsafe_allow_html=True)

# Step 1: Generate SQL Query
st.header("Ask in Natural Language")
nlp_prompt = st.text_area("Enter your question", "How many people wear Adidas in rahmans_cos catalog and adidas1 schema?")

if st.button("Generate SQL"):
    with st.spinner("Processing query..."):
        detected_catalog, detected_schema = extract_catalog_schema(nlp_prompt)
        if not detected_catalog or not detected_schema:
            st.error("Error: Could not detect catalog or schema. Please specify them in your query.")
        else:
            try:
                # Generate SQL query using Watsonx
                response = model.generate_text(prompt=f"Generate an SQL query only without explanation: {nlp_prompt}")
                generated_query = response.strip()
                
                if generated_query:
                    st.success("SQL query generated successfully!")
                    st.text_area("Generated SQL Query", value=generated_query, height=150, key="generated_query")
                    st.session_state["generated_query"] = generated_query
                else:
                    st.error("Error: Generated query is empty.")
            except Exception as e:
                st.error(f"Error generating SQL: {e}")

# Step 2: Execute SQL Query
if "generated_query" in st.session_state and st.button("Execute Query"):
    with st.spinner("Executing SQL query..."):
        try:
            conn = presto.connect(
                host=PRESTO_HOST,
                port=PRESTO_PORT,
                catalog=detected_catalog,
                schema=detected_schema,
                username=PRESTO_USERNAME,
                password=PRESTO_PASSWORD,
                protocol="https",
                requests_kwargs={"verify": False}
            )
            df = pd.read_sql(st.session_state["generated_query"], conn)
            df["Catalog"] = detected_catalog
            df["Schema"] = detected_schema
            
            st.success("Query executed successfully!")
            st.dataframe(df)
            st.session_state["query_result"] = df
        except Exception as e:
            st.error(f"Error executing SQL query: {e}")
