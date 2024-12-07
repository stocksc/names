import streamlit as st
import pandas as pd
import numpy as np
import os
import altair as alt

dir_data = "C:/Users/chris/Documents/Projects/Names/Data/clean/"

overall_data = pd.read_parquet(os.path.join(dir_data, 'name_overall_data.parquet'))
overall_data['pr_other'] = 1 - overall_data[['pr_white', 'pr_black', 'pr_hispanic', 'pr_asian']].sum(axis=1)
for col in ['pr_white', 'pr_black', 'pr_hispanic', 'pr_asian', 'pr_other']:
    overall_data[col] = overall_data[col].fillna(0)
    overall_data[col] = round(overall_data[col]*100,1)
overall_data.rename(columns={
    'pr_white': 'White',
    'pr_black': 'Black',
    'pr_hispanic': 'Hispanic',
    'pr_asian': 'Asian',
    'pr_other': 'Other'
}, inplace=True)

year_data = pd.read_parquet(os.path.join(dir_data, 'name_year_data.parquet'))
year_data['Rate_Female'] = year_data['Rate_Female']*10000
year_data['Rate_Male'] = year_data['Rate_Male']*10000
year_data['Percent_Female'] = year_data['Percent_Female']*100
year_data['Percent_Male'] = year_data['Percent_Male']*100

colors = {
    'Female': '#FFC0CB',
    'Male': '#89CFF0'
}

# Title
st.title("Bebe")

# Name input 
name = st.text_input(
    label="Enter a name:",
    value="Abby",
    help="Enter a name to see its data."
).title()
chosen_name_data = overall_data.loc[overall_data['Name'] == name]

# Popularity
st.subheader("Popularity")

Female_rank = chosen_name_data['Rank_Female'].values[0].astype(int)
Male_rank = chosen_name_data['Rank_Male'].values[0].astype(int)

chosen_year_data = year_data.loc[year_data['Name']==name]
Female_peak = chosen_year_data['Rank_Female'].min().astype(int)
Female_peak_year = chosen_year_data.loc[chosen_year_data['Rank_Female'] == Female_peak, 'Year'].values[0]
Male_peak = chosen_year_data['Rank_Male'].min().astype(int)
Male_peak_year = chosen_year_data.loc[chosen_year_data['Rank_Male'] == Male_peak, 'Year'].values[0]


col1, col2 = st.columns(2)
with col1:
    st.markdown(f"Female Rank: <span style='color:{colors['Female']}'>**{Female_rank:,}**</span>", unsafe_allow_html=True)
    st.markdown(f"Female Peak: <span style='color:{colors['Female']}'>**{Female_peak:,} ({Female_peak_year})**</span>", unsafe_allow_html=True)
with col2:
    st.markdown(f"Male Rank: <span style='color:{colors['Male']}'>**{Male_rank:,}**</span>", unsafe_allow_html=True)
    st.markdown(f"Male Peak: <span style='color:{colors['Male']}'>**{Male_peak:,} ({Male_peak_year})**</span>", unsafe_allow_html=True)

year_range = (1900, int(year_data['Year'].max()))
pop_data = year_data.loc[
    (year_data['Name'] == name) & 
    (year_data['Year'] >= year_range[0]) &
    (year_data['Year'] <= year_range[1])
]

st.line_chart(
    pop_data,
    x='Year',
    y=['Rate_Female', 'Rate_Male'],
    # y=['Count_Female', 'Count_Male'],
    y_label='Popularity (# in 10,000)',
    color=[colors['Female'], colors['Male']],
)

# Gender
st.subheader("Gender")
col1, col2 = st.columns(2)
with col1:
    st.write(f"Female Share: <span style='color:{colors['Female']}'>**{round(chosen_name_data['Percent_Female'].values[0]*100,1)}%**", unsafe_allow_html=True)
with col2:
    st.write(f"Male Share: <span style='color:{colors['Male']}'>**{round(chosen_name_data['Percent_Male'].values[0]*100,1)}%**", unsafe_allow_html=True)

pop_data_melted = pop_data.melt(id_vars=['Year'], value_vars=['Percent_Female', 'Percent_Male'], var_name='Gender', value_name='Percentage')
pop_data_melted['Gender'] = pop_data_melted['Gender'].map({'Percent_Female': 'Female', 'Percent_Male': 'Male'})

stacked_area_chart = alt.Chart(pop_data_melted).mark_area().encode(
    x=alt.X('Year:O', axis=alt.Axis(tickCount=10)),
    y='Percentage:Q',
    color=alt.Color('Gender:N', scale=alt.Scale(domain=['Female', 'Male'], range=[colors['Female'], colors['Male']]), legend=None)
).properties(
    height=250
)
st.altair_chart(stacked_area_chart, use_container_width=True)

# Demographics
st.subheader("Demographics")

colors = {
    'White': '#B0B0B0',  # Softer grey
    'Black': '#66CDAA',  # Softer green
    'Hispanic': '#FFA07A',  # Lighter orange
    'Asian': '#FF7F7F',  # Softer red
    'Other': '#87CEFA'  # Softer blue
}

demo_data = chosen_name_data[['White', 'Black', 'Hispanic', 'Asian', 'Other']]
display_demo_data = demo_data.astype(str) + "%"
display_demo_data.index = [name]

# Create HTML table with colored values
html_table = display_demo_data.T.to_html(escape=False)
for group, color in colors.items():
    html_table = html_table.replace(f'>{demo_data[group].values[0]}%', f' style="color: {color};"><b>{demo_data[group].values[0]}%')
    html_table = html_table.replace('<th>', '<th style="font-weight: normal;">')
    html_table = html_table.replace('<th style="text-align: right;">', '<th style="text-align: right; font-weight: normal;">')
demo_data = demo_data.T
demo_data.columns = ['Percentage']
demo_data['Percentage'] = demo_data['Percentage'].astype(float)

demo_data = demo_data.loc[['White', 'Black', 'Hispanic', 'Asian', 'Other']].reset_index()
pie_chart = alt.Chart(demo_data).mark_arc().encode(
    theta=alt.Theta(field="Percentage", type="quantitative"),
    color=alt.Color(field="index", type="nominal", scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values())), title="Demographic"),
    order=alt.Order('index', sort='ascending'),  # Ensure the order is maintained
    tooltip=['index', 'Percentage']
).properties(
    width=330,
    height=300
)


# Display table and pie chart
col1, col2 = st.columns(2)
with col1:
    st.markdown(html_table, unsafe_allow_html=True)
with col2:
    st.altair_chart(pie_chart)

# Similar names
# Reference names checkboxes
# Roll random name