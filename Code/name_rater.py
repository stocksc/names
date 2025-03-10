import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import altair as alt

colors = {
    'Female': '#FF77B4',
    'Male': '#89CFF0'
}

st.title(f"✨Name Rater✨")

##################
# Initialization #
##################

if "login_status" not in st.session_state:
    st.session_state.login_status = None
    st.session_state.username = None

if st.session_state.login_status is None:
    placeholder = st.empty()
    with placeholder.form("login"):
        user_file = st.file_uploader(
            "If you are an existing user, upload your most recent ratings file"
        )
        partner_file = st.file_uploader(
            "If you have one, upload partner's ratings file"
        )
        st.session_state.username = st.text_input(
            "If you are a new user, enter your name"
        )
        login_submit = st.form_submit_button("Login")

    if partner_file:
        st.session_state.partner_ratings = pd.read_csv(partner_file)
    else:
        st.session_state.partner_ratings = None

    if login_submit and user_file:
        st.session_state.login_status = "existing"
        st.session_state.ratings = pd.read_csv(user_file)
        st.session_state.username = st.session_state.ratings['User'].values[0]
        placeholder.success(f"Welcome back {st.session_state.username}!")
        time.sleep(2)
        placeholder.empty()
    elif login_submit and st.session_state.username:
        st.session_state.login_status = "new"
        st.session_state.ratings = pd.DataFrame(columns=["User", "Name", "Rating", "Timestamp"])
        placeholder.success("New user created!")
        time.sleep(2)
        placeholder.empty()
    elif login_submit:
        st.error("Please enter a username or upload a user file.")
    else:
        pass

##############
# Data Setup #
##############

overall_data = pd.read_parquet("https://github.com/stocksc/names/blob/master/Data/clean/name_overall_data.parquet?raw=true")
year_data = pd.read_parquet("https://github.com/stocksc/names/blob/master/Data/clean/name_year_data.parquet?raw=true")
year_data_2023 = year_data.loc[year_data['Year'] == 2023].sort_values(['Rank_Female'])

def get_name():
    if manual_select != []:
        name = manual_select[0]
        num_names = "N/A"
        names_list = pd.DataFrame()
        return name, num_names, names_list
    else:
        # Eligibility based on 2023 ranking and overall pct female
        eligible_names_year = year_data_2023.loc[year_data_2023['Rank_Female'].between(min_rank_2023, max_rank_2023)]
        eligible_names_overall = overall_data.loc[overall_data['Percent_Female'].between(female_pct_range[0]/100, female_pct_range[1]/100)]
        eligible_names = pd.merge(
            eligible_names_year[['Name', 'Rank_Female', 'Count_Female']], 
            eligible_names_overall[['Name', 'Rate_Female', 'Percent_Female']], 
            on='Name', how='inner'
        )
        
        # Weight by rate by default
        eligible_names['weight'] = eligible_names['Rate_Female']

        name = eligible_names.sample(1, weights=eligible_names['weight'])['Name'].values[0]
        num_names = eligible_names.shape[0]
        names_list = eligible_names[['Name', 'Rank_Female', 'Percent_Female', 'Count_Female']]

    return name, num_names, names_list

if st.session_state.login_status is not None:
    c1, c2, c3 = st.columns(3)
    with c1:
        min_rank_2023 = st.number_input("Minimum Female rank in 2023", min_value=1, value=1, step=100)
    with c2:
        max_rank_2023 = st.number_input("Maximum Female rank in 2023", min_value=1, value=10000, step=100)
    with c3:
        female_pct_range = st.slider("Percent Female (since 1950)", min_value=0, max_value=100, value=(20, 100))
    manual_select = st.multiselect(
        "Manually choose a name", year_data_2023['Name'].values, max_selections=1
    )

###########
# Ratings #
###########

def save_feedback():
    if st.session_state.feedback is None:
        rating = None
    else:
        rating = st.session_state.feedback + 1
        if (rating >= 4) and (st.session_state.partner_ratings is not None):
            most_recent_partner_ranking = st.session_state.partner_ratings.loc[
                (st.session_state.partner_ratings['Name'] == st.session_state.name) &
                (~pd.isna(st.session_state.partner_ratings['Rating']))
                , 'Rating'].values[0]
            if most_recent_partner_ranking >= 4:
                st.balloons()
                st.toast(f"Most recently, they rated it a {int(most_recent_partner_ranking)}.")
                st.toast(f"You and your partner both like this name!")
        st.session_state.num_ratings += 1
        if st.session_state.name != "Press Submit to start":
            new_entry = pd.DataFrame({"User": [st.session_state.username], "Name": [st.session_state.name], "Rating": [rating], "Timestamp": [pd.Timestamp.now()]})
            st.session_state.ratings = pd.concat([new_entry, st.session_state.ratings], axis=0)
    
    # st.session_state.feedback = None
    st.session_state.name, st.session_state.num_names, st.session_state.names_list = get_name()

if 'name' not in st.session_state:
    st.session_state.name = "Press Submit to start"
    st.session_state.num_names = "?"
    st.session_state.names_list = pd.DataFrame()
    st.session_state.num_ratings = -1

if st.session_state.login_status is not None:
    st.markdown(f"Selecting from {st.session_state.num_names} names")
    st.title(st.session_state.name)
    feedback = st.feedback('stars', key='feedback')
    submit_button = st.button("Submit", on_click=save_feedback)
    
    if (st.session_state.num_ratings > 0) and (st.session_state.num_ratings < 20):
        st.write(f"You have made {st.session_state.num_ratings} ratings this session.")
    elif st.session_state.num_ratings >= 20:
        st.write(f"You have made {st.session_state.num_ratings} ratings this session. Don't forget to download and save your progress!")
    
    st.download_button("Download ratings", st.session_state.ratings.to_csv(index=False), f"name_ratings_{st.session_state.username}_{pd.Timestamp.now()}.csv")

    ###################
    # Ratings History #
    ###################

    ratings_history = st.checkbox("View name's ratings history", value=True)
    if ratings_history:
        user_ratings = st.session_state.ratings.loc[st.session_state.ratings['Name'] == st.session_state.name]
        if st.session_state.partner_ratings is not None:
            partner_ratings = st.session_state.partner_ratings.loc[st.session_state.partner_ratings['Name'] == st.session_state.name]

        c1, c2 = st.columns(2)
        with c1:
            st.write("Your Ratings")
            st.dataframe(user_ratings, hide_index=True)
        with c2:
            if st.session_state.partner_ratings is not None:
                st.write("Partner's Ratings")
                st.dataframe(partner_ratings, hide_index=True)

    ####################
    # Popularity Stats #
    ####################
    popularity_stats = st.checkbox("View popularity stats")
    if popularity_stats:
        # Make data for chosen name
        chosen_overall = overall_data.loc[overall_data['Name'] == st.session_state.name]
        chosen_year = year_data.loc[year_data['Name'] == st.session_state.name]

        count = {}
        rank = {}
        rank_all = {}
        peak_rank = {}
        peak_rank_year = {}
        growth = {}
        same_in_class = {}
        same_in_grade = {}
        for sex in ["Female", "Male"]:
            # Current Count
            count[sex] = chosen_year.loc[chosen_year['Year']==2023, f'Count_{sex}'].values[0].astype(int)
            
            # Current Rank
            rank[sex] = chosen_year.loc[chosen_year['Year']==2023, f'Rank_{sex}'].values[0].astype(int)
            
            # Rank since 1950
            rank_all[sex] = chosen_overall[f'Rank_{sex}'].values[0].astype(int)

            # Peak rank (and year)
            peak_rank[sex] = chosen_year[f'Rank_{sex}'].min().astype(int)
            peak_rank_year[sex] = chosen_year.loc[chosen_year[f'Rank_{sex}'] == peak_rank[sex], 'Year'].values[0]

            # Growth in last 3 years
            rate_now = chosen_year.loc[chosen_year['Year'] == 2023, f'Rate_{sex}'].values[0]
            rate_past = chosen_year.loc[chosen_year['Year'] == 2020, f'Rate_{sex}'].values[0]
            if rate_past == 0:
                growth[sex] = "N/A"
            else:
                growth[sex] = round((rate_now - rate_past) / rate_past * 100, 1)

            # Probability of same name in class/grade
            same_in_class[sex] = round(chosen_year.loc[chosen_year['Year']==2023, f'Pr_Same_In_Class_{sex}'].values[0]/2, 1)
            same_in_grade[sex] = round(chosen_year.loc[chosen_year['Year']==2023, f'Pr_Same_In_Grade_{sex}'].values[0]/2, 1)

        # Display table
        st.markdown(f"""
        <table style='width:100%; table-layout:fixed;'>
            <tr>
                <th style='width:50%;'></th>
                <th style='width:25%; color:{colors["Female"]}; text-align: center;'>Female</th>
                <th style='width:25%; color:{colors["Male"]}; text-align: center;'>Male</th>
            </tr>
            <tr>
                <td>Count (in 2023):</td>
                <td style='color:{colors["Female"]};'><strong>{count["Female"]:,}</strong></td>
                <td style='color:{colors["Male"]};'><strong>{count["Male"]:,}</strong></td>
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
                <td>Prob Same Name in Class (25):</td>
                <td style='color:{colors["Female"]};'><strong>{same_in_class["Female"]}%</strong></td>
                <td style='color:{colors["Male"]};'><strong>{same_in_class["Male"]}%</strong></td>
            </tr>
            <tr>
                <td>Prob Same Name in Grade (100):</td>
                <td style='color:{colors["Female"]};'><strong>{same_in_grade["Female"]}%</strong></td>
                <td style='color:{colors["Male"]};'><strong>{same_in_grade["Male"]}%</strong></td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
    
    ###################
    # Popularity Plot #
    ###################
    popularity_plot = st.checkbox("View popularity plot")
    if popularity_plot:
        # Plot data
        year_range = (1950, 2023)
        reference_names = ['Jennifer', 'Lucy', 'Nora']
        year_data_with_references = year_data.loc[
            (year_data['Name'].isin([st.session_state.name]+reference_names)) & 
            (year_data['Year'] >= year_range[0]) &
            (year_data['Year'] <= year_range[1])
        ]
        # Reference names 
        reference_names_checkboxes = st.multiselect(
            label="Reference names:",
            options=reference_names,
            default=[]
        )
        year_data_plot = year_data_with_references.loc[year_data_with_references['Name'].isin([st.session_state.name]+reference_names_checkboxes)]
        line_chart_female = alt.Chart(year_data_plot).mark_line().encode(
            x=alt.X('Year:O', axis=alt.Axis(tickCount=8, values=[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020], labelAngle=0)),
            y=alt.Y('Rate_10k_Female:Q', title='Rate (# per 10,000)'),
            color=alt.Color('Name:N', scale=alt.Scale(domain=[st.session_state.name]+reference_names_checkboxes, range=[colors['Female']]+['#D3D3D3']*len(reference_names_checkboxes)), legend=None),
            strokeDash=alt.StrokeDash('Name:N', scale=alt.Scale(domain=[st.session_state.name]+reference_names_checkboxes, range=[[0,0] for _ in range(len(reference_names_checkboxes)+1)]), legend=None),
            tooltip=['Name', 'Year', 'Rate_10k_Female']
        ).properties(
            height=300
        )
        st.altair_chart(line_chart_female, use_container_width=True)

    ##########
    # Gender #
    ##########
    gender_plot = st.checkbox("View sex distribution plot")
    if gender_plot:
        chosen_overall = overall_data.loc[overall_data['Name'] == st.session_state.name]
        chosen_year = year_data.loc[year_data['Name'] == st.session_state.name]
        year_range = (1950, 2023)

        sex_share = {}
        share_change = {}
        for sex in ["Female", "Male"]:
            # Share
            sex_share[sex] = round(chosen_overall[f'Percent_{sex}'].values[0]*100,1)

            # Change in last 10 years
            share_now = chosen_year.loc[chosen_year['Year'] == 2023, f'Percent_{sex}'].values[0]
            share_past = chosen_year.loc[chosen_year['Year'] == 2013, f'Percent_{sex}'].values[0]
            share_change[sex] = round(share_now - share_past, 1)

        # Display descriptives
        col1, col2 = st.columns(2)
        with col1:
            sex = "Female"
            st.write(f"{sex} Share: <span style='color:{colors[sex]}'>**{sex_share[sex]}%**", unsafe_allow_html=True)
            st.write(f"3yr Change: <span style='color:{colors[sex]}'>**{share_change[sex]}%**", unsafe_allow_html=True)
        with col2:
            sex = "Male"
            st.write(f"{sex} Share: <span style='color:{colors[sex]}'>**{sex_share[sex]}%**", unsafe_allow_html=True)
            st.write(f"3yr Change: <span style='color:{colors[sex]}'>**{share_change[sex]}%**", unsafe_allow_html=True)

        # Plot data
        gender_plot_data = year_data.loc[
            (year_data['Name'] == st.session_state.name) & 
            (year_data['Year'] >= year_range[0]) &
            (year_data['Year'] <= year_range[1])
        ]

        # Stacked area chart
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
    demo_plot = st.checkbox("View demographics plot")
    if demo_plot:
        chosen_overall = overall_data.loc[overall_data['Name'] == st.session_state.name]
        chosen_year = year_data.loc[year_data['Name'] == st.session_state.name]
        demo_colors = {
            'White': '#B0B0B0',  # Softer grey
            'Black': '#66CDAA',  # Softer green
            'Hispanic': '#FFA07A',  # Lighter orange
            'Asian': '#FF7F7F',  # Softer red
            'Other': '#87CEFA'  # Softer blue
        }

        # Data prep for table
        demo_data = chosen_overall[['White', 'Black', 'Hispanic', 'Asian', 'Other']]
        display_demo_data = demo_data.astype(str) + "%"
        display_demo_data.index = [st.session_state.name]

        # Display table
        html_table = display_demo_data.T.to_html(escape=False)
        for group, color in demo_colors.items():
            html_table = html_table.replace(f'>{demo_data[group].values[0]}%', f' style="color: {color};"><b>{demo_data[group].values[0]}%')
            html_table = html_table.replace('<th>', '<th style="font-weight: normal;">')
            html_table = html_table.replace('<th style="text-align: right;">', '<th style="text-align: right; font-weight: normal;">')

        # Modify data for pie chart
        demo_data = demo_data.T
        demo_data.columns = ['Percentage']
        demo_data['Percentage'] = demo_data['Percentage'].astype(float)
        demo_data = demo_data.loc[['White', 'Black', 'Hispanic', 'Asian', 'Other']].reset_index()

        # Pie chart
        pie_chart = alt.Chart(demo_data).mark_arc().encode(
            theta=alt.Theta(field="Percentage", type="quantitative"),
            color=alt.Color(field="index", type="nominal", scale=alt.Scale(domain=list(demo_colors.keys()), range=list(demo_colors.values())), title="Demographic"),
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

    ##################
    # Eligible Names #
    ##################
    view_eligible = st.checkbox("View eligible names")
    if view_eligible:
        st.dataframe(st.session_state.names_list, hide_index=True)

    ###################
    # Ratings History #
    ###################

    full_ratings_history = st.checkbox("View all ratings history")
    if full_ratings_history:
        c1, c2 = st.columns(2)
        with c1:
            st.write("Your Ratings")
            st.dataframe(st.session_state.ratings, hide_index=True)
        with c2:
            if st.session_state.partner_ratings is not None:
                st.write("Partner's Ratings")
                st.dataframe(st.session_state.partner_ratings, hide_index=True)
    
    ######################
    # Partner Comparison #
    ######################

    partner_compare = st.checkbox("Compare ratings with partner")
    if partner_compare:
        if st.session_state.partner_ratings is None:
            st.warning("You have not uploaded a partner's ratings file.")
        else:
            ratings_last_only = st.session_state.ratings.drop_duplicates(subset=['Name'], keep='first')
            partner_ratings_last_only = st.session_state.partner_ratings.drop_duplicates(subset=['Name'], keep='first')
            partner_ratings_last_only.rename(columns={"Rating": "Partner's Rating"}, inplace=True)
            ratings_compare = pd.merge(ratings_last_only[['Name', 'Rating']], partner_ratings_last_only[['Name', "Partner's Rating"]], on=['Name'], how='outer')
            ratings_compare['Min Rating'] = ratings_compare[['Rating', "Partner's Rating"]].min(axis=1)
            ratings_compare.sort_values('Min Rating', ascending=False, inplace=True)
            st.dataframe(ratings_compare, hide_index=True, width=400, use_container_width=False)
