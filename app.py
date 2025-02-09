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

# Custom CSS for tag styling
st.markdown(
    """
    <style>
    .tag {
        display: inline-block;
        background-color: #3498db;
        color: white;
        padding: 5px 10px;
        margin: 5px;
        border-radius: 15px;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App
st.markdown("<h1 style='text-align: center; color: #2196F3;'>NLP with WatsonX.data</h1>", unsafe_allow_html=True)

# Sidebar for Navigation
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to", ["SQL Query Editor", "BI Interaction Section"])

# Initialize session state for query results
if "query_result" not in st.session_state:
    st.session_state["query_result"] = None

if "generated_query" not in st.session_state:
    st.session_state["generated_query"] = ""

if section == "SQL Query Editor":
    # Sidebar for Multi-Select Catalog and Schema
    st.sidebar.header("Configuration")
    available_catalogs = ["tpch", "rahmans_cos", "analytics_catalog"]
    available_schemas = ["sf100", "adidas1", "schema2"]

    selected_catalogs = st.sidebar.multiselect("Select Catalogs", available_catalogs)
    selected_schemas = st.sidebar.multiselect("Select Schemas", available_schemas)

    # Display selected catalogs as tags
    st.sidebar.write("### Selected Catalogs:")
    for catalog in selected_catalogs:
        st.sidebar.markdown(f'<span class="tag">{catalog}</span>', unsafe_allow_html=True)

    # Display selected schemas as tags
    st.sidebar.write("### Selected Schemas:")
    for schema in selected_schemas:
        st.sidebar.markdown(f'<span class="tag" style="background-color: #e67e22;">{schema}</span>', unsafe_allow_html=True)

    # Step 1: Generate SQL Query
    st.header("Generate SQL Query")
    sql_prompt = st.text_area("Enter SQL prompt", "Write a SQL statement to select all rows from a table called customer.")
    
    if st.button("Generate SQL"):
        with st.spinner("Generating SQL query..."):
            try:
                # Generate SQL query using Watsonx
                response = model.generate_text(prompt=sql_prompt)
                generated_query = response.strip() if isinstance(response, str) else response.get("generated_text", "").strip()
                if generated_query:
                    st.success("SQL query generated successfully!")
                    st.session_state["generated_query"] = generated_query
                else:
                    st.error("Error: Generated query is empty.")
            except Exception as e:
                st.error(f"Error generating SQL: {e}")

    # Step 2: Edit and Execute SQL Query
    st.header("Edit and Execute SQL Query")
    edited_query = st.text_area(
        "Edit SQL Query",
        value=st.session_state.get("generated_query", ""),
        height=150,
        key="edited_query"
    )

    execute = st.button("Execute Query")

    # Execute Query Logic for Multiple Catalogs/Schemas
    if execute:
        with st.spinner("Executing SQL query..."):
            try:
                if not edited_query.strip():
                    st.error("Error: SQL query cannot be empty!")
                elif not selected_catalogs or not selected_schemas:
                    st.error("Error: Please select at least one catalog and one schema!")
                else:
                    df_list = []
                    for catalog in selected_catalogs:
                        for schema in selected_schemas:
                            conn = presto.connect(
                                host=PRESTO_HOST,
                                port=PRESTO_PORT,
                                catalog=catalog,
                                schema=schema,
                                username=PRESTO_USERNAME,
                                password=PRESTO_PASSWORD,
                                protocol="https",
                                requests_kwargs={"verify": False}
                            )
                            df = pd.read_sql(edited_query, conn)
                            df["Catalog"] = catalog
                            df["Schema"] = schema
                            df_list.append(df)
                    
                    final_df = pd.concat(df_list, ignore_index=True)
                    st.success("Query executed successfully!")
                    st.dataframe(final_df)
                    st.session_state["query_result"] = final_df
            except Exception as e:
                st.error(f"Error executing SQL query: {e}")
