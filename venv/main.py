
import os
import base64
import pandas as pd
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from influxdb_client import InfluxDBClient
import warnings
import altair as alt
warnings.filterwarnings("ignore")
import pandas as pd
import smtplib
import ssl
import requests

# Set up InfluxDB client
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"  # Replace with your InfluxDB URL
INFLUXDB_TOKEN = "0rCx4vJj_a9HaBQJSBrwY3nQBR94uQuJlMu_CmqPVAwBOEOBu7lN7s7_FiqfQh0hBHf0Ecvz7H_EayMDSo9GEw=="  # Replace with your InfluxDB token
INFLUXDB_ORG = "organisation"  # Replace with your InfluxDB organization
INFLUXDB_BUCKET = "Temperature"  # Replace with your InfluxDB bucket

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)

# User authentication (replace with your desired credentials)
USER = "admin"
PASSWORD = "admin"

st.title("Temperature Monitoring Dashboard")

# User authentication
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")


st.sidebar.title("Alarm Settings")
ALARM_THRESHOLD = st.sidebar.number_input("Alarm Threshold (°C)", value=30)
ALARM_RECIPIENT = st.sidebar.text_input("Email Recipient", value="taha196tr@gmail.com")

# Export report
def export_report(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="temperature_report.csv">Download CSV</a>'
    return href


if username != USER or password != PASSWORD:
    st.warning("Incorrect credentials. Please try again.")
else:
    chart_placeholder = st.empty()
    df_placeholder = st.empty()
    while True:
        query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1h) |> filter(fn: (r) => r["_measurement"] == "temperature_data")'
        result = client.query_api().query(org=INFLUXDB_ORG, query=query)

        # Convert query result to pandas DataFrame
        data = []
        for table in result:
            for record in table.records:
                if record["table"]==1:
                    data.append((record["_time"], record["_field"], record["_value"]))
        df = pd.DataFrame(data, columns=["Time", "Field", "Value"])
        # Display temperature data as line chart
        # Customize the chart appearance
        line = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X('Time:T', axis=alt.Axis(title='Time', labelAngle=-45)),
            y=alt.Y('Value:Q', axis=alt.Axis(title='Temperature (°C)')),
            tooltip=[alt.Tooltip('Time:T', title='Time'), alt.Tooltip('Value:Q', title='Temperature (°C)', format='.2f')]
        )

        # Set chart properties
        chart = line.properties(
            title='Temperature Monitoring Dashboard',
            width='container',
            height=300
        )

        chart_placeholder.altair_chart(chart, use_container_width=True)
        df_placeholder.dataframe(df)
        st.markdown(export_report(df), unsafe_allow_html=True)

        # Check for temperature threshold
        if df["Value"].iloc[-1] > ALARM_THRESHOLD:
            st.warning("Temperature exceeded threshold!")
            # Send email alert
            message = MIMEMultipart()
            message['From'] = 'temperature_alert@mycompany.com'
            message['To'] = ALARM_RECIPIENT
            message['Subject'] = 'Temperature Alert'
            body = f"Temperature exceeded {ALARM_THRESHOLD}°C!"
            message.attach(MIMEText(body, 'plain'))
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login("atabdellatif1@gmail.com", "1965729698As")
                server.sendmail("taha196tr@gmail.com", ALARM_RECIPIENT, message.as_string())
