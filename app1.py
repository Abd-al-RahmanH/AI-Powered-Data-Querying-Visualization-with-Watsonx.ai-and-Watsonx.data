import streamlit as st
import pandas as pd
from sqlalchemy.engine import create_engine
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# Watsonx Credentials
credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "XfyqbHqkZSatzDxeQzzEdQbfu-DP-_ihUvSSmrmIiTmT"
}
project_id = "289854e9-af72-4464-8bb2-4dedc59ad405"

# Watsonx Model Initialization (Using ModelInference instead of Model)
model_id = "meta-llama/llama-3-405b-instruct"
parameters = {
    GenParams.MIN_NEW_TOKENS: 10,
    GenParams.MAX_NEW_TOKENS: 200,
    GenParams.TEMPERATURE: 0.7
}
model = ModelInference(
    model_id=model_id,
    params=parameters,
    credentials=credentials,
    project_id=project_id
)

# Presto Connection (Using SQLAlchemy)
PRESTO_HOST = "34.238.192.61"
PRESTO_PORT = 8443
PRESTO_USERNAME = "ibmlhadmin"
PRESTO_PASSWORD = "password"

# Create Presto Connection URL
presto_url = f"presto://{PRESTO_USERNAME}:{PRESTO_PASSWORD}@{PRESTO_HOST}:{PRESTO_PORT}/tpch/sf100"
engine = create_engine(presto_url)

# Streamlit UI
st.markdown("<h1 style='text-align: center; color: #2196F3;'>NLP with WatsonX + Pandas</h1>", unsafe_allow_html=True)

# Catalog & Schema Selection
st.sidebar.header("Database Selection")
catalog = st.sidebar.selectbox("Select Catalog", ["tpch", "rahmans_cos", "analytics_catalog"])
schema = st.sidebar.selectbox("Select Schema", ["sf100", "adidas1", "schema2"])

# User Input for NLP Query
st.header("Ask a Question")
nlp_query = st.text_area("Enter your question", "How many customers are in the customer table?")

if st.button("Get Answer"):
    with st.spinner("Fetching data..."):
        try:
            # Fetch Data from Presto
            query = f"SELECT * FROM {catalog}.{schema}.customer"
            df = pd.read_sql_query(query, engine)

            st.write("### 📊 Sample Data from Selected Table:")
            st.dataframe(df.head())

            # Generate Pandas query from NLP question
            query_prompt = f"Convert this question into a valid Pandas DataFrame filtering operation: {nlp_query}\nDataFrame name: df"
            response = model.generate_text(prompt=query_prompt)
            pandas_query = response.strip()

            # Execute the generated Pandas query
            result = eval(pandas_query)  # Caution: Ensure trusted input in production

            # Display results
            st.success(f"Answer based on `{catalog}.{schema}`:")
            if isinstance(result, pd.DataFrame):
                st.dataframe(result)
            else:
                st.write(result)

        except Exception as e:
            st.error(f"Error processing query: {e}")
