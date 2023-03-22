import os
import base64
import pandas as pd
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
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
import base64
import time
import streamlit as st
# Set up InfluxDB client
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"  # Replace with your InfluxDB URL
INFLUXDB_TOKEN = "0rCx4vJj_a9HaBQJSBrwY3nQBR94uQuJlMu_CmqPVAwBOEOBu7lN7s7_FiqfQh0hBHf0Ecvz7H_EayMDSo9GEw=="  # Replace with your InfluxDB token
INFLUXDB_ORG = "organisation"  # Replace with your InfluxDB organization
INFLUXDB_BUCKET = "Temperature"  # Replace with your InfluxDB bucket

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)


def create_download_link_csv(df, filename="temperature_data.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    return href
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

# Add your Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = "6299578760:AAGTR2NH2h1pUfolycwUsvNDtPHBM8bePYg"
TELEGRAM_CHAT_ID = "146697908"

# Add your email credentials
EMAIL_ADDRESS = "atabdellatifbot@gmail.com"
EMAIL_PASSWORD = "shlzaqmcgtldcfiq"

# Alarm notification function
def send_alarm_notification(temperature):
    # Send email notification
    #msg = MIMEMultipart()
    #msg["From"] = EMAIL_ADDRESS
    #msg["To"] = ALARM_RECIPIENT
    #msg["Subject"] = f"Temperature Alarm: {temperature} °C"
    #msg.attach(MIMEText(f"Temperature has exceeded the threshold of {ALARM_THRESHOLD} °C. Current temperature: {temperature} °C.", "plain"))
    #context = ssl.create_default_context()
    #with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    #    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD) 
    #    server.sendmail(EMAIL_ADDRESS, ALARM_RECIPIENT, msg.as_string())
    
    # Send Telegram notification
    text = f"Temperature Alarm: {temperature} °C\nTemperature has exceeded the threshold of {ALARM_THRESHOLD} °C."
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={text}")


@st.cache_resource
def get_data():
    query = f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1h) |> filter(fn: (r) => r["_measurement"] == "temperature_data")'
    result = client.query_api().query(org=INFLUXDB_ORG, query=query)

    # Convert query result to pandas DataFrame
    data = []
    for table in result:
        for record in table.records:
            if record["table"]==1:
                data.append((record["_time"], record["_field"], record["_value"]))
    df = pd.DataFrame(data, columns=["Time", "Field", "Value"])
    return df   

if username != USER or password != PASSWORD:
    st.warning("Incorrect credentials. Please try again.")
else:
    chart_placeholder = st.empty()
    df_placeholder = st.empty()
    refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 1, 60, 10)
    while True:
        df = get_data()
           # Check if the temperature has exceeded the alarm threshold
        max_temperature = df["Value"].max()
        if max_temperature > ALARM_THRESHOLD:
            send_alarm_notification(max_temperature)
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
        # Add the export button to the sidebar
        if st.sidebar.button("Download CSV", key="download_csv_button"):
            download_link = create_download_link_csv(df)
            st.sidebar.markdown(download_link, unsafe_allow_html=True)
            st.sidebar.success("CSV file is ready for download!")

        chart_placeholder.altair_chart(chart, use_container_width=True)
        time.sleep(refresh_rate)
        st.experimental_rerun()


