# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 09:16:43 2024

@author: zzulk
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import os

# Load CSS file
css_file_path = os.path.join(os.path.dirname(__file__), 'styles.css')
if os.path.exists(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
else:
    st.error("CSS file not found.")

# Load your dataset from GitHub
data_url = 'https://raw.githubusercontent.com/zulianizulkoffli/soil-studies-peninsular-malaysia-extension1/main/Data_For_Viz.csv'  # Replace with your actual GitHub URL

# Attempt to load the dataset with multiple encoding attempts
try:
    data = pd.read_csv(data_url, delimiter=',', encoding='utf-8', low_memory=False)
except UnicodeDecodeError:
    st.warning("UTF-8 encoding failed. Trying ISO-8859-1 encoding.")
    try:
        data = pd.read_csv(data_url, delimiter=',', encoding='ISO-8859-1', low_memory=False)
    except UnicodeDecodeError:
        st.warning("ISO-8859-1 encoding failed. Trying cp1252 encoding.")
        try:
            data = pd.read_csv(data_url, delimiter=',', encoding='cp1252', low_memory=False)
        except Exception as e:
            st.error(f"Failed to read the file with cp1252 encoding: {e}")
            st.stop()
except FileNotFoundError:
    st.error("File not found. Please check the file path.")
    st.stop()
except pd.errors.ParserError:
    st.error("Parsing error: Please check the file format and content.")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.stop()

# Ensure that data is loaded correctly before proceeding
if 'data' in locals():
    # Correcting the column names
    data.columns = data.columns.str.strip()

    # Define the required columns
    required_columns = ['Location', 'Latitude', 'Longitude', 'Depth (m)', 'Clay (%)', 'Silt (%)', 
                        'Sand (%)', 'Gravels (%)', '1D inverted resistivity', 
                        'Moisture content (%)', 'pH', 'Soil Type', 'Fine Soil (%)', 
                        'Sand (%)', 'USCS Group Symbol']

    # Check if optional columns exist and add them if they do
    optional_columns = ['D10', 'D30', 'D60', 'CU', 'CC']
    existing_optional_columns = [col for col in optional_columns if col in data.columns]
    all_columns = required_columns + existing_optional_columns

    # Check if the required columns exist in the dataset
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        st.error(f"Missing columns in the dataset: {missing_columns}")
    else:
        filtered_data = data[all_columns]

        # Streamlit app
        st.markdown("<style>h1{margin-top: 0px !important;}</style>", unsafe_allow_html=True)
        st.title("Data Visualization for Soil Classes Data in Peninsular Malaysia")

        # Adjust layout width
        st.markdown("""
            <style>
            .main .block-container {
                max-width: 80%;
                padding: 1rem;
            }
            .sidebar .sidebar-content {
                background-color: #D0EFFF;
            }
            </style>
            """, unsafe_allow_html=True)

        # Initialize session state
        if "location" not in st.session_state:
            st.session_state.location = None

        # Add a large "Filter Options" title
        st.sidebar.markdown("<div class='filter-options'></div>", unsafe_allow_html=True)
        st.sidebar.markdown(f"""
            <div style='width: 100%; font-size: 2.5em; text-align: justify; padding: 10px; border: bold: none;'>
            {'FILTER OPTIONS'}
            </div>
            """, unsafe_allow_html=True)

        # Location selection
        location_filter = st.sidebar.selectbox("Select Location(s)", sorted(data['Location'].unique()))

        # Filter data based on location selection
        if location_filter:
            st.session_state.location = location_filter

        if st.session_state.location:
            filtered_data = data[data['Location'] == st.session_state.location]

            # Display map above the data
            if not filtered_data.empty:
                # Create a folium map centered around the average coordinates of selected locations
                avg_lat = filtered_data['Latitude'].mean()
                avg_long = filtered_data['Longitude'].mean()
                m = folium.Map(location=[avg_lat, avg_long], zoom_start=6)

                # Add data points to the map with detailed popups
                for idx, row in filtered_data.iterrows():
                    popup_text = (
                        f"Location: {row['Location']}<br>"
                        f"Depth (m): {row['Depth (m)']}<br>"
                        f"Soil Type: {row['Soil Type']}<br>"
                        f"Fine Soil (%): {row['Fine Soil (%)']}<br>"
                        f"Sand (%): {row['Sand (%)']}<br>"
                        f"USCS Group Symbol: {row['USCS Group Symbol']}"
                    )
                    folium.Marker(
                        location=[row['Latitude'], row['Longitude']],
                        popup=popup_text,
                    ).add_to(m)

                # Display the map in Streamlit
                st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
                folium_static(m)
                st.markdown("</div>", unsafe_allow_html=True)

                # Display filtered data below the map
                st.write("## Raw Data Acquired at Tested Location")
                st.dataframe(filtered_data)

                # Add a note below the data table
                st.markdown("<p style='text-align: center; font-style: italic; color: gray;'>0 = Nil data (non-numerical values replaced by 0)</p>", unsafe_allow_html=True)

                # Plot depth vs parameters chart with depth on y-axis
                st.write("## Depth vs Parameters")
                parameters = ['Clay (%)', 'Silt (%)', 'Sand (%)', 'Moisture content (%)']
                
                # Arrange graphs in rows of three
                for i in range(0, len(parameters), 3):
                    cols = st.columns(3)  # Create three columns
                    for col, param in zip(cols, parameters[i:i+3]):  # Iterate over columns and parameters
                        fig = px.line(filtered_data, y='Depth (m)', x=param, 
                                      title=f'Depth vs {param}', 
                                      labels={'y': 'Depth (m)', 'x': param})
                        fig.update_yaxes(autorange="reversed")  # Invert y-axis to display depth from top to bottom
                        col.plotly_chart(fig, use_container_width=True)

                # Add extra space below the data table
                st.markdown("<div style='margin-bottom: 3in;'></div>", unsafe_allow_html=True)
            else:
                st.warning("No data available for the selected location.")
