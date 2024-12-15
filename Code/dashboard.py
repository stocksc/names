import streamlit as st
import pandas as pd
import numpy as np
import os
import altair as alt

#############
# Data Prep #
#############

# dir_data = "C:/Users/chris/Documents/Projects/Names/Data/clean/"
# overall_data = pd.read_parquet(os.path.join(dir_data, 'name_overall_data.parquet'))
# year_data = pd.read_parquet(os.path.join(dir_data, 'name_year_data.parquet'))
overall_data = pd.read_parquet("https://github.com/stocksc/names/blob/master/Data/clean/name_overall_data.parquet?raw=true")
year_data = pd.read_parquet("https://github.com/stocksc/names/blob/master/Data/clean/name_year_data.parquet?raw=true")

colors = {
    'Female': '#FF77B4',
    'Male': '#89CFF0'
}

#########
# Title #
#########
# Initialize
if 'name' not in st.session_state:
    st.session_state.name = "Abby"
    st.session_state.eligible_text = ""

st.title(f"✨Bebe✨")

##############
# Name input #
##############

# Manual input
name = st.text_input(
    label="Enter a name:",
    value=st.session_state.name,
    help="Enter a name to see its data (not case sensitive)."
).title()

# Select random name
def get_random_name():
    
    # 2023 names (for popularity)
    eligible_names_year = year_data.loc[year_data['Year'] == 2023]

    # Gender and popularity
    if male_or_female == "All Names":
        eligible_names_overall = overall_data
        eligible_names_year = eligible_names_year.loc[
            (
                eligible_names_year['Rank_Female'].between(popularity_range_2023[0], popularity_range_2023[1]) | 
                eligible_names_year['Rank_Male'].between(popularity_range_2023[0], popularity_range_2023[1]) 
            )
        ]
    elif male_or_female == "Girls":
        eligible_names_overall = overall_data.loc[
            (overall_data['Percent_Female'] > 0.8)
        ]
        eligible_names_year = eligible_names_year.loc[ 
            (eligible_names_year['Rank_Female'].between(popularity_range_2023[0], popularity_range_2023[1]))
        ]
    elif male_or_female == "Boys":
        eligible_names_overall = overall_data.loc[
            (overall_data['Percent_Female'] < 0.2)
        ]
        eligible_names_year = eligible_names_year.loc[ 
            (eligible_names_year['Rank_Male'].between(popularity_range_2023[0], popularity_range_2023[1]))
        ]
    elif male_or_female == "Gender Neutral":
        eligible_names_overall = overall_data.loc[
            (overall_data['Percent_Female'].between(0.2, 0.8))
        ]
        eligible_names_year = eligible_names_year.loc[ 
            (
                eligible_names_year['Rank_Female'].between(popularity_range_2023[0], popularity_range_2023[1]) | 
                eligible_names_year['Rank_Male'].between(popularity_range_2023[0], popularity_range_2023[1]) 
            )
        ]
    else:
        st.write("no")
    # Race
    eligible_names_overall = eligible_names_overall.loc[
        eligible_names_overall['White'].between(pct_white[0], pct_white[1])
    ]

    eligible_names = pd.Series(list(set(eligible_names_year['Name']).intersection(set(eligible_names_overall['Name']))))
    if len(eligible_names) > 0:
        random_name = eligible_names.sample(1).values[0]
    else:
        random_name = "[No names meet those criteria]"
    return random_name, eligible_names.shape[0]

def set_random_name():
    st.session_state.name = get_random_name()[0]
    st.session_state.eligible_text = f"Selecting from {get_random_name()[1]} eligible names."

# Random options
use_random = st.checkbox(label="Generate random name", value=False)
if use_random: 
    popularity_range_2023 = st.slider(
        "Popularity Ranking (2023)", min_value=1, max_value=5000, value=(50, 500),
        help="Min and max rankings (inclusive). Uses either gender, unless Percent Female is set."
    )    
    # popularity_range_all = st.slider(
    #     "Popularity Ranking (since 1950)", min_value=1, max_value=5000, value=(1, 5000),
    #     help="Min and max rankings (inclusive) for either boys or girls using all births since 1950."
    # )
    pct_white = st.slider(
        "Percent White", min_value=0, max_value=100, value=(30,100),
        help="Share of births with that name that are non-Hispanic White."
    )  
    male_or_female = st.radio(
        "Boy or Girl Names?", options=["All Names", "Girls", "Boys", "Gender Neutral"],
        help="Names will either by boys (>80% male), girls (<20% male), gender neutral (20-80% male), or all."
    ) 
    st.text(st.session_state.eligible_text)
    st.button("Randomize", on_click=set_random_name)


# Make data for chosen name
chosen_overall = overall_data.loc[overall_data['Name'] == name]
chosen_year = year_data.loc[year_data['Name'] == name]

##############
# Popularity #
##############
st.title(f"{name}")
st.subheader(f"Popularity")

# Current Rank
rank = {}
for sex in ["Female", "Male"]:
    rank[sex] = chosen_year.loc[chosen_year['Year']==2023, f'Rank_{sex}'].values[0].astype(int)

# Rank since 1950
rank_all = {}
for sex in ["Female", "Male"]:
    rank_all[sex] = chosen_overall[f'Rank_{sex}'].values[0].astype(int)

# Peak rank (and year)
peak_rank = {}
peak_rank_year = {}
for sex in ["Female", "Male"]:
    peak_rank[sex] = chosen_year[f'Rank_{sex}'].min().astype(int)
    peak_rank_year[sex] = chosen_year.loc[chosen_year[f'Rank_{sex}'] == peak_rank[sex], 'Year'].values[0]

# Growth in last 3 years
growth = {}
for sex in ["Female", "Male"]:
    rate_now = chosen_year.loc[chosen_year['Year'] == 2023, f'Rate_{sex}'].values[0]
    rate_past = chosen_year.loc[chosen_year['Year'] == 2020, f'Rate_{sex}'].values[0]
    growth[sex] = round((rate_now - rate_past) / rate_past * 100, 1)

# Same name in class/grade
same_in_class = {}
same_in_grade = {}
for sex in ["Female", "Male"]:
    same_in_class[sex] = round(chosen_year.loc[chosen_year['Year']==2023, f'Pr_Same_In_Class_{sex}'].values[0], 1)
    same_in_grade[sex] = round(chosen_year.loc[chosen_year['Year']==2023, f'Pr_Same_In_Grade_{sex}'].values[0], 1)

# Display
st.markdown(f"""
<table style='width:65%; table-layout:fixed;'>
    <tr>
        <th style='width:50%;'></th>
        <th style='width:25%; color:{colors["Female"]}; text-align: center;'>Female</th>
        <th style='width:25%; color:{colors["Male"]}; text-align: center;'>Male</th>
    </tr>
    <tr>
        <td>Rank (in 2023):</td>
        <td style='color:{colors["Female"]};'><strong>{rank["Female"]:,}</strong></td>
        <td style='color:{colors["Male"]};'><strong>{rank["Male"]:,}</strong></td>
    </tr>
    <tr>
        <td>Rank (since 1950):</td>
        <td style='color:{colors["Female"]};'><strong>{rank_all["Female"]:,}</strong></td>
        <td style='color:{colors["Male"]};'><strong>{rank_all["Male"]:,}</strong></td>
    </tr>
    <tr>
        <td>Peak Rank:</td>
        <td style='color:{colors["Female"]};'><strong>{peak_rank["Female"]:,} ({peak_rank_year["Female"]})</strong></td>
        <td style='color:{colors["Male"]};'><strong>{peak_rank["Male"]:,} ({peak_rank_year["Male"]})</strong></td>
    </tr>
    <tr>
        <td>3yr Change:</td>
        <td style='color:{colors["Female"]};'><strong>{growth["Female"]}%</strong></td>
        <td style='color:{colors["Male"]};'><strong>{growth["Male"]}%</strong></td>
    </tr>
    <tr>
        <td>Prob Same Name in Class:</td>
        <td style='color:{colors["Female"]};'><strong>{same_in_class["Female"]}%</strong></td>
        <td style='color:{colors["Male"]};'><strong>{same_in_class["Male"]}%</strong></td>
    </tr>
    <tr>
        <td>Prob Same Name in Grade:</td>
        <td style='color:{colors["Female"]};'><strong>{same_in_grade["Female"]}%</strong></td>
        <td style='color:{colors["Male"]};'><strong>{same_in_grade["Male"]}%</strong></td>
    </tr>
</table>
""", unsafe_allow_html=True)

# Plot data
year_range = (1950, 2023)
reference_names = ['Christopher', 'Liam', 'Ezra', 'Jennifer', 'Lucy', 'Nora']
year_data_with_references = year_data.loc[
    (year_data['Name'].isin([name]+reference_names)) & 
    (year_data['Year'] >= year_range[0]) &
    (year_data['Year'] <= year_range[1])
]
# Reference names 
reference_names_checkboxes = st.multiselect(
    label="Reference names:",
    options=reference_names,
    default=[]
)

# Select which plots to show
female_chart = False
male_chart = False
female_share = chosen_overall['Percent_Female'].values[0]
if female_share > 0.05:
    female_chart = True
if female_share < 0.95:
    male_chart = True

# Line chart
year_data_plot = year_data_with_references.loc[year_data_with_references['Name'].isin([name]+reference_names_checkboxes)]

if female_chart:
    line_chart_female = alt.Chart(year_data_plot).mark_line().encode(
        x=alt.X('Year:O', axis=alt.Axis(tickCount=8, values=[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020], labelAngle=0)),
        y=alt.Y('Rate_10k_Female:Q', title='Rate (# per 10,000)'),
        color=alt.Color('Name:N', scale=alt.Scale(domain=[name]+reference_names_checkboxes, range=[colors['Female']]+['#D3D3D3']*len(reference_names_checkboxes)), legend=None),
        strokeDash=alt.StrokeDash('Name:N', scale=alt.Scale(domain=[name]+reference_names_checkboxes, range=[[0,0] for _ in range(len(reference_names_checkboxes)+1)]), legend=None),
        tooltip=['Name', 'Year', 'Rate_10k_Female']
    ).properties(
        height=300
    )
if male_chart:
    line_chart_male = alt.Chart(year_data_plot).mark_line().encode(
        x=alt.X('Year:O', axis=alt.Axis(tickCount=8, values=[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020], labelAngle=0)),
        y=alt.Y('Rate_10k_Male:Q', title='Rate (# per 10,000)'),
        color=alt.Color('Name:N', scale=alt.Scale(domain=[name]+reference_names_checkboxes, range=[colors['Male']]+['#D3D3D3']*len(reference_names_checkboxes)), legend=None),
        strokeDash=alt.StrokeDash('Name:N', scale=alt.Scale(domain=[name]+reference_names_checkboxes, range=[[0,0] for _ in range(len(reference_names_checkboxes)+1)]), legend=None),
        tooltip=['Name', 'Year', 'Rate_10k_Male']
    ).properties(
        height=300
    )

if male_chart and female_chart:
    layered_chart = alt.layer(line_chart_female, line_chart_male).resolve_scale(y='shared', color='independent').configure_legend(orient='none')
    st.altair_chart(layered_chart, use_container_width=True)
elif male_chart:
    st.altair_chart(line_chart_male, use_container_width=True)
elif female_chart:
    st.altair_chart(line_chart_female, use_container_width=True)


##########
# Gender #
##########
st.subheader(f"Gender")

# Share
sex_share = {}
for sex in ["Female", "Male"]:
    sex_share[sex] = round(chosen_overall[f'Percent_{sex}'].values[0]*100,1)

# Change in last 10 years
share_change = {}
for sex in ["Female", "Male"]:
    share_now = chosen_year.loc[chosen_year['Year'] == 2023, f'Percent_{sex}'].values[0]
    share_past = chosen_year.loc[chosen_year['Year'] == 2013, f'Percent_{sex}'].values[0]
    share_change[sex] = round(share_now - share_past, 1)


col1, col2 = st.columns(2)
with col1:
    sex = "Female"
    st.write(f"{sex} Share: <span style='color:{colors[sex]}'>**{sex_share[sex]}%**", unsafe_allow_html=True)
    st.write(f"3yr Change: <span style='color:{colors[sex]}'>**{share_change[sex]}%**", unsafe_allow_html=True)
with col2:
    sex = "Male"
    st.write(f"{sex} Share: <span style='color:{colors[sex]}'>**{sex_share[sex]}%**", unsafe_allow_html=True)
    st.write(f"3yr Change: <span style='color:{colors[sex]}'>**{share_change[sex]}%**", unsafe_allow_html=True)

gender_plot_data = year_data.loc[
    (year_data['Name'] == name) & 
    (year_data['Year'] >= year_range[0]) &
    (year_data['Year'] <= year_range[1])
]

pop_data_melted = gender_plot_data.melt(id_vars=['Year'], value_vars=['Percent_Female', 'Percent_Male'], var_name='Gender', value_name='Percentage')
pop_data_melted['Gender'] = pop_data_melted['Gender'].map({'Percent_Female': 'Female', 'Percent_Male': 'Male'})

stacked_area_chart = alt.Chart(pop_data_melted).mark_area().encode(
    x=alt.X('Year:O', axis=alt.Axis(tickCount=10)),
    y='Percentage:Q',
    color=alt.Color('Gender:N', scale=alt.Scale(domain=['Female', 'Male'], range=[colors['Female'], colors['Male']]), legend=None)
).properties(
    height=220
)
st.altair_chart(stacked_area_chart, use_container_width=True)

################
# Demographics #
################
st.subheader(f"Demographics")

colors = {
    'White': '#B0B0B0',  # Softer grey
    'Black': '#66CDAA',  # Softer green
    'Hispanic': '#FFA07A',  # Lighter orange
    'Asian': '#FF7F7F',  # Softer red
    'Other': '#87CEFA'  # Softer blue
}

demo_data = chosen_overall[['White', 'Black', 'Hispanic', 'Asian', 'Other']]
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
