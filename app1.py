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
model_id ="meta-llama/llama-3-405b-instruct"
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

# Custom CSS for enhanced UI
st.markdown(
    """
    <style>
    body {
        background-color: #f4f4f9;
        font-family: 'Arial', sans-serif;
    }
    .title {
        color: #2196F3;
        text-align: center;
        padding: 20px;
    }
    .sidebar .sidebar-content {
        background-color: #e3f2fd;
    }
    .css-1lcbmhc {
        background-color: #e3f2fd;
    }
    .css-1d391kg {  /* For buttons */
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .css-1d391kg:hover {
        background-color: #45a049;
    }
    .dataframe-container {
        margin: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App
st.markdown("<h1 class='title'>NLP with WatsonX.data</h1>", unsafe_allow_html=True)

# Sidebar for Navigation
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to", ["SQL Query Editor", "BI Interaction Section"])

# Initialize session state for query results
if "query_result" not in st.session_state:
    st.session_state["query_result"] = None

if "generated_query" not in st.session_state:
    st.session_state["generated_query"] = ""

if section == "SQL Query Editor":
    # Sidebar for Catalog and Schema Selection
    st.sidebar.header("Configuration")
    catalog = st.sidebar.selectbox("Select Catalog", ["tpch", "rahmans_cos", "analytics_catalog"])
    schema = st.sidebar.selectbox("Select Schema", ["sf100", "adidas1", "schema2"])

    # Step 1: Generate SQL Query
    st.header("Generate SQL Query")
    sql_prompt = st.text_area("Enter SQL prompt", "Write a SQL statement to select all rows from a table called customer.")
    if st.button("Generate SQL"):
        with st.spinner("Generating SQL query..."):
            try:
                # Generate SQL query
                response = model.generate_text(prompt=sql_prompt)

                # Check if the response is a string or dictionary-like object
                if isinstance(response, str):
                    generated_query = response.strip()
                else:
                    generated_query = response.get("generated_text", "").strip()

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

    # Execute and Refresh Buttons
    col1, col2 = st.columns(2)
    execute = col1.button("Execute Query")
    refresh = col2.button("Refresh")

    # Execute Query Logic
    if execute:
        with st.spinner("Executing SQL query..."):
            try:
                if not edited_query.strip():
                    st.error("Error: SQL query cannot be empty!")
                else:
                    start_time = time.time()
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
                    df = pd.read_sql(edited_query, conn)
                    execution_time = time.time() - start_time
                    st.success(f"Query executed successfully in {execution_time:.2f} seconds!")
                    st.dataframe(df)

                    # Save query result in session state
                    st.session_state["query_result"] = df
            except Exception as e:
                st.error(f"Error executing SQL query: {e}")

    # Refresh Logic
    if refresh:
        for key in st.session_state.keys():
            del st.session_state[key]  # Clear all session state variables
        st.experimental_rerun()

elif section == "BI Interaction Section":
    # BI Interaction Section
    st.header("BI Interaction Section")
    st.write("Analyze and interact with data visually.")

    # Check if query results exist
    if st.session_state["query_result"] is not None:
        df = st.session_state["query_result"]

        # Visualization Options
        st.subheader("Select Visualization Type")
        chart_type = st.selectbox("Choose a chart type", ["Bar Chart", "Pie Chart", "Scatter Plot"])

        # X and Y Axis Selection
        st.subheader("Choose X and Y Axes")
        x_axis = st.selectbox("X-Axis", options=df.columns)
        y_axis = st.selectbox("Y-Axis", options=df.columns)

        # Generate Chart
        if chart_type == "Bar Chart":
            fig = px.bar(df, x=x_axis, y=y_axis, title="Bar Chart", color=x_axis)
            st.plotly_chart(fig)
        elif chart_type == "Pie Chart":
            fig = px.pie(df, names=x_axis, values=y_axis, title="Pie Chart")
            st.plotly_chart(fig)
        elif chart_type == "Scatter Plot":
            fig = px.scatter(df, x=x_axis, y=y_axis, title="Scatter Plot")
            st.plotly_chart(fig)

        # Display Dataframe
        st.subheader("Dataframe View")
        st.dataframe(df)
    else:
        st.warning("No query results found! Please execute a query in the SQL Query Editor section first.")
