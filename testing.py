import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# DATA LOADING
CSV_URL = "https://raw.githubusercontent.com/tpereanez18/FInal-Project-DSC-205-Group-6/refs/heads/main/Next_Generation_Accountability_System_20260407.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Define columns to be used in dashboard
    cols_to_keep = [
        'RptngDistrictName', 'SchoolName', 'Accountability Index', 
        'Ind4Rate', 'Ind9Rate', 'Ind10Rate', 
        'Ind1ELA_All_Points', 'Ind1Math_All_Points', 'Ind1Sci_All_Points', 
        'Ind11FitnessRate', 'Ind12Rate', 
        'Ind2ELA_All_Rate', 'Ind2Math_All_Rate', 
        'Category', 'StudentGroup', 'FallOfYear'
    ]
    
    # Filter the dataframe to only include these columns
    existing_cols = [col for col in cols_to_keep if col in df.columns]
    df = df[existing_cols]
    
    numeric_cols = [
        'Ind4Rate', 'Accountability Index', 'Ind9Rate', 'Ind10Rate',
        'Ind1ELA_All_Points', 'Ind1Math_All_Points', 
        'Ind1Sci_All_Points', 'Ind11FitnessRate', 'Ind12Rate', 
        'Ind2ELA_All_Rate', 'Ind2Math_All_Rate', 'FallOfYear'
    ]
    
    # Convert to numbers and forcing bad data into NaN
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Calculate Average Academic Growth
    if 'Ind2ELA_All_Rate' in df.columns and 'Ind2Math_All_Rate' in df.columns:
        df['Academic_Growth_Avg'] = df[['Ind2ELA_All_Rate', 'Ind2Math_All_Rate']].mean(axis=1)
    else:
        df['Academic_Growth_Avg'] = None
    
    # 5. Normalize Decimals to Percentages
    if df['Ind9Rate'].max() <= 1.1: df['Ind9Rate'] *= 100
    if df['Ind4Rate'].max() <= 1.1: df['Ind4Rate'] *= 100
    if 'Ind11FitnessRate' in df.columns and df['Ind11FitnessRate'].max() <= 1.1: 
        df['Ind11FitnessRate'] *= 100
    if 'Ind12Rate' in df.columns and df['Ind12Rate'].max() <= 1.1: 
        df['Ind12Rate'] *= 100
    if 'Academic_Growth_Avg' in df.columns and df['Academic_Growth_Avg'].max() <= 1.1: 
        df['Academic_Growth_Avg'] *= 100
        
    # 6. Drop completely empty rows
    df = df.dropna(subset=['Accountability Index', 'RptngDistrictName'], how='all')
        
    return df

st.set_page_config(page_title="CT Accountability Dashboard", layout="wide")

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# COLUMN MAPPING
DIST_COL = 'RptngDistrictName'
SCH_COL = 'SchoolName'
INDEX_COL = 'Accountability Index'
ABSENT_COL = 'Ind4Rate' 
GRAD_COL = 'Ind9Rate' 
GROWTH_COL = 'Academic_Growth_Avg'   # Calculated
ARTS_COL = 'Ind12Rate'               
CAT_COL = 'Category'
GROUP_COL = 'StudentGroup'
YEAR_COL = 'FallOfYear'

# FILTERS
st.sidebar.header("Filters")

# Year Filter
years_list = sorted(df[YEAR_COL].dropna().unique().astype(int), reverse=True)
options = ["All Years"] + [str(y) for y in years_list]
selected_year_option = st.sidebar.selectbox("Select School Year", options=options)

# District Filter
districts = sorted(df[DIST_COL].dropna().unique())
selected_dist = st.sidebar.multiselect("Select District", options=districts, default=["Bridgeport School District"])

# School Filter
school_options = sorted(df[df[DIST_COL].isin(selected_dist)][SCH_COL].unique())
selected_schools = st.sidebar.multiselect("Select School", options=school_options)

# FILTERING LOGIC
filtered_df = df.copy()

# Apply Year Filter only if a specific year is chosen
if selected_year_option != "All Years":
    filtered_df = filtered_df[filtered_df[YEAR_COL] == int(selected_year_option)]

# Apply District/School Filters
filtered_df = filtered_df[filtered_df[DIST_COL].isin(selected_dist)]
if selected_schools:
    filtered_df = filtered_df[filtered_df[SCH_COL].isin(selected_schools)]

# MAIN BODY
st.title(f"Next Generation Accountability Dashboard: {selected_year_option}")

# ACCOUNTABILITY INDEX EXPLANATION
st.subheader("What is the Accountability Index?")
with st.expander( "The Accountability Index", expanded=True):
    st.write("### Connecticut takes in many factors to assign an overall score for a school.")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
        1. The Index combines test scores with attendance. If students are 'Chronic Absentees' (missing 10%+ of school), the school loses points.
        
        2. The Index tracks academic growth. This means a school gets credit for a student moving from a 'D' to a 'C', even if they aren't at an 'A' yet. It rewards schools for the hard work of improving.
        """)
    
    with col_b:
        st.markdown("""
        3. The Index awards points for:
        * Arts Access: Does the school offer music, theater, and art?
        * Physical Fitness: Are students healthy and active?
        * College Prep: Is the school getting students ready for the real world?
        """)
        
    st.info("""
    A score of **75** is the 'Passing Grade' set by Connecticut. Keep in mind that a school with a low bar in our charts can mean they are struggling with things like attendance or academic growth, not just poor testing grades.
    """)
    st.info('In this dashboard, Accountability Index and \'success\' are used interchangeably.')

# PERFORMANCE
m1, m2, m3 = st.columns(3)
with m1: st.metric("Average Accountability Index", f"{filtered_df[INDEX_COL].mean():.1f}")
with m2: st.metric("Average Graduation Rate", f"{filtered_df[GRAD_COL].mean():.1f}%")
with m3: st.metric("Average Chronic Absenteeism", f"{filtered_df[ABSENT_COL].mean():.1f}%")

st.divider()

# SECTION 1: ACHIEVEMENT VS GROWTH
st.header("1. How do Academic Achievement and Academic Growth relate?")

st.markdown('Academic achievement looks at current student test scores, while academic growth looks at the progress made over the school year, whether that is from an F to a C or a B to an A. This graph shows the relationship between these two factors')
st.markdown('It is expected that higher academic achievement correlates positively with academic growth. Those that improve student learning also earn higher scores.')

st.info('Data from the Bridgeport School District from all years shows a positive trend, as expected. Looking at individual years also shows the same trend. This relationship is strongly supported.')

if not filtered_df.empty:
    fig_scatter, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=filtered_df, x=INDEX_COL, y=GROWTH_COL, ax=ax, s=100, color='blue', alpha=0.6)
    sns.regplot(data=filtered_df, x=INDEX_COL, y=GROWTH_COL, scatter=False, color='red', ax=ax)
    plt.title(f'Achievement vs. Growth: {selected_year_option}')
    plt.xlabel('Academic Achievement (Accountability Index)')
    plt.ylabel('Academic Growth (Growth Rate %)')
    st.pyplot(fig_scatter)
else:
    st.warning("Please adjust filters to see the scatterplot.")

st.divider()

# SECTION 2: CHRONIC ABSENTEEISM
st.header("2. Does Chronic Absenteeism Impact Student Performance?")

st.markdown('This graph shows whether showing up to class matters to success. The height of a bar represents its Accountability Index, and the color represents chronic absenteeism rates. A darker red shows a problem with absenteeism.')

st.info('Schools from the Bridgeport School District show a clear trend. Schools with higher bars, or accountability indices, have darker green. Most of the students regularly attend classes at these schools, like Multicultural Magnet School and Interdistrict Discovery Magnet School. Schools with scores even below 50 have a deep red, like Warren Harding. These schools have a serious problem of students not attending class.')

if not filtered_df.empty:
    # Grouping by school
    absent_summary = filtered_df.groupby(SCH_COL)[[INDEX_COL, ABSENT_COL]].mean().reset_index()
    fig_absent = px.bar(
        absent_summary, x=SCH_COL, y=INDEX_COL, color=ABSENT_COL,
        color_continuous_scale='RdYlGn_r', 
        title=f"Performance vs. Absenteeism ({selected_year_option})"
    )
    st.plotly_chart(fig_absent, use_container_width=True)

st.divider()

# SECTION 3: GRADUATION GAPS
st.header("3. Are Graduation Rates Consistent Across All Schools?")

st.markdown('Graduating high school may not be a universal constant. The chance of graduating may change depending on which school students attend. This graph explores the relationship between graduation rates and Accountability Index.')

st.info('The Bridgeport school district has a generally positive trend between graduation rate and accountability index. This is reasonable, as schools that do not perform well are less likely to retain students. They may not attend class or dropout, leading to a lower graduation rate. There are some outliers at around an index of 52, all of which are Bridgeport Military Academy from different years. This may be attributed to the different nature of a military academy.')

if not filtered_df.empty:
# Filter out "All Students"
    group_df = filtered_df[filtered_df[CAT_COL] != 'All Students'].dropna(subset=[GRAD_COL, INDEX_COL])

# Interactive Plotly scatter
    fig_groups = px.scatter(
        group_df, 
        x=INDEX_COL, 
        y=GRAD_COL, 
        color=CAT_COL,
        hover_data=[SCH_COL],
        title=f"Graduation Rates vs. Index by Student Group ({selected_year_option})",
        labels={INDEX_COL: "Accountability Index", GRAD_COL: "Graduation Rate %", CAT_COL: "Student Group"}
    )

    fig_groups.update_traces(marker=dict(size=12, opacity=0.7))
    st.plotly_chart(fig_groups, use_container_width=True)

else:
    st.warning("No category-specific data available for this selection.")

st.divider()

# SECTION 4: SUBJECT BREAKDOWN
st.header("4. What is Driving the Score? ELA, Math, and Science")

st.markdown('This grouped bar chart goes into the academics of the index, showing where students are meeting standards or falling behind in different academic subjects.')

st.info('There is a consistent pattern visible in almost all schools of the Bridgeport school district. ELA contributes the most to the academic points of the Accountability Index, followed by math, then science. It does not necessarily matter what success score the school has; each subject follows closely behind the next in this step pattern. This difference is heightened in schools with higher success scores, but it is still present in other ones.')

if not filtered_df.empty:
    subject_map = {'Ind1ELA_All_Points': 'ELA', 'Ind1Math_All_Points': 'Math', 'Ind1Sci_All_Points': 'Science'}
    # Average subjects by school if "All Years" is selected
    subj_summary = filtered_df.groupby(SCH_COL)[list(subject_map.keys())].mean().reset_index()
    melted_df = subj_summary.melt(id_vars=[SCH_COL], value_vars=list(subject_map.keys()), var_name='Subject', value_name='Points')
    melted_df['Subject'] = melted_df['Subject'].map(subject_map)
    fig_subjects = px.bar(melted_df, x=SCH_COL, y='Points', color='Subject', barmode='group')
    st.plotly_chart(fig_subjects, use_container_width=True)

st.divider()

# SECTION 5: NON ACADEMICS
st.header("5. Do Non-Academic Factors Correlate with Success?")

st.markdown('The Accountability Index importantly takes into account physical fitness scores and arts access, looking beyond pure academic ratings. It shows whether fitness and creativity can create a more successful student, and in turn, a more successful school.')

st.info('The data points for Bridgeport district schools across all years in both physical fitness and arts are very scattered. It would almost be difficult to spot the positive trend of physical fitness with success if the trend line was not there. Surprisingly, arts access shows a slightly negative correlation with success. Due to the very low R2 values, it is possible that other districts, or even years, show opposite correlations. For example, this same school district in 2024 has a positive correlation of arts access with success, but just barely.')

if not filtered_df.empty:
    col1, col2 = st.columns(2)
    
    # Physical Fitness Graph
    with col1:
        if 'Ind11FitnessRate' in filtered_df.columns:
            fig_fitness = px.scatter(
                filtered_df, 
                x='Ind11FitnessRate', 
                y=INDEX_COL,
                color=DIST_COL,
                hover_data=[SCH_COL],
                labels={
                    'Ind11FitnessRate': 'Physical Fitness Rate (%)',
                    INDEX_COL: 'Accountability Index'
                },
                title="Physical Fitness vs. Success",
                template="plotly_white",
                trendline="ols",             
                trendline_scope="overall"    
            )
            
            fig_fitness.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
            
            fig_fitness.update_traces(line=dict(color="black", width=3), selector=dict(mode="lines"))
            
            st.plotly_chart(fig_fitness, use_container_width=True)
            
            # Correlation
            fitness_corr = filtered_df['Ind11FitnessRate'].corr(filtered_df[INDEX_COL])
            st.info(f"**Fitness Correlation:** {fitness_corr:.2f}")
        else:
            st.warning("Physical Fitness data not found.")

    # Arts Access Graph
    with col2:
        if 'Ind12Rate' in filtered_df.columns:
            fig_arts = px.scatter(
                filtered_df, 
                x='Ind12Rate', 
                y=INDEX_COL,
                color=DIST_COL, 
                hover_data=[SCH_COL],
                labels={
                    'Ind12Rate': 'Arts Access Rate (%)',
                    INDEX_COL: 'Accountability Index'
                },
                title="Arts Access vs. Success",
                template="plotly_white",
                trendline="ols",            
                trendline_scope="overall"  
            )
            
            fig_arts.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=1, color='DarkSlateGrey')))
            
            fig_arts.update_traces(line=dict(color="black", width=3), selector=dict(mode="lines"))
            
            st.plotly_chart(fig_arts, use_container_width=True)
            
            # Correlation
            arts_corr = filtered_df['Ind12Rate'].corr(filtered_df[INDEX_COL])
            st.info(f"**Arts Correlation:** {arts_corr:.2f}")
        else:
            st.warning("Arts Access data not found.")
else:
    st.warning("Please adjust filters to see the non-academic analysis.")

st.divider()

# SECTION 6: STRONGEST PREDICTORS
st.header("6. Which indicators are the strongest predictors of overall school performance?")

st.markdown('This graph shows the correlation, if any, of academic, non-academic, and other factors with success. A more green score, to the right, indicates a positive impact on the school index, while a red score, to the left, indicates a negative impact on the school index.')

st.info('The factors that contribute most positively to the Accountability Index of the Bridgeport School District are graduation rate and academic growth. Previous graphs showed the positive correlation between graduation and success, but it is now clear that this is one of the most important factors for this school district. Academic growth is also more strongly correlated with success than individual academic achievements. Again, arts access has a negative contribution here, but this often varies. What is very clear is that chronic absenteeism has a very negative correlation with success.')

if not filtered_df.empty:
    predictor_cols = [
        'Ind1ELA_All_Points', 'Ind1Math_All_Points', 'Ind1Sci_All_Points',
        'Ind4Rate', 'Ind9Rate', 'Ind11FitnessRate', 'Ind12Rate', 'Academic_Growth_Avg'
    ]
    
    friendly_names = {
        'Ind1ELA_All_Points': 'ELA Achievement',
        'Ind1Math_All_Points': 'Math Achievement',
        'Ind1Sci_All_Points': 'Science Achievement',
        'Ind4Rate': 'Chronic Absenteeism',
        'Ind9Rate': 'Graduation Rate',
        'Ind11FitnessRate': 'Physical Fitness',
        'Ind12Rate': 'Arts Access',               
        'Academic_Growth_Avg': 'Academic Growth'  
    }
    
    # Ensure columns exist
    available_cols = [c for c in predictor_cols if c in filtered_df.columns]
    
    if available_cols:
        # Calculate Pearson correlation
        corr_data = filtered_df[available_cols + [INDEX_COL]].corr()[INDEX_COL].drop(INDEX_COL)
        
        # Format into a DataFrame
        corr_df = corr_data.reset_index()
        corr_df.columns = ['Indicator', 'Correlation']
        corr_df['Indicator'] = corr_df['Indicator'].map(friendly_names)
        
        corr_df = corr_df.sort_values(by='Correlation', ascending=True)
        
        # Horizontal bar chart
        fig_predictors = px.bar(
            corr_df, 
            x='Correlation', 
            y='Indicator', 
            orientation='h',
            color='Correlation',
            color_continuous_scale='RdYlGn',
            text_auto='.2f',
            title=f"Predictors of School Success ({selected_year_option})"
        )
        
        fig_predictors.update_layout(xaxis_title="Correlation Coefficient (-1.0 to 1.0)", yaxis_title="")
        st.plotly_chart(fig_predictors, use_container_width=True)
else:
    st.warning("Please adjust filters to see the predictor analysis.")

st.divider()

# SECTION 7: DISTRICT DISPARITIES
st.header("7. Are there disparities between districts in different indicators?")

st.markdown('This boxplot shows not only a district\'s performance through each individual school, but how districts of different Accountability Indices fare against each other in different metrics.')

st.info('Comparing two districts like Bridgeport and Darien shows the disparities in every factor investigated. The Accountability Index of Darien schools are higher than Bridgeport schools, and this follows for academic growth,  graduation rate, arts access, and somewhat physical fitness. Chronic absenteeism is very prevalent in the Bridgeport school district but is minimized to under 7 percent in the Darien school district. Physical fitness slightly overlaps for both districts, but Darien is still on the higher side of these scores.')

if not filtered_df.empty:
    # Choose indicator
    disparity_metrics = {
        'Overall Success (Accountability Index)': INDEX_COL,
        'Academic Growth': GROWTH_COL,
        'Chronic Absenteeism': ABSENT_COL,
        'Graduation Rate': GRAD_COL,
        'Physical Fitness': 'Ind11FitnessRate',
        'Arts Access': 'Ind12Rate'
    }
    
    # Filter out missing metrics
    available_metrics = {k: v for k, v in disparity_metrics.items() if v in filtered_df.columns}
    
    selected_metric_name = st.selectbox("Select an Indicator to analyze for disparities:", options=list(available_metrics.keys()))
    selected_metric_col = available_metrics[selected_metric_name]
    
    # Reminder to choose more than one district
    if len(selected_dist) < 2:
        st.info("Select at least two districts in the sidebar to compare disparities!")

    # Boxplot
    fig_box = px.box(
        filtered_df, 
        x=DIST_COL, 
        y=selected_metric_col, 
        color=DIST_COL,
        points="all", # This overlays the actual schools as dots next to the boxes!
        hover_data=[SCH_COL], # Show the school name when hovering over a dot
        title=f"Disparities in {selected_metric_name} by District",
        template="plotly_white"
    )
    
    fig_box.update_layout(
        xaxis_title="School District", 
        yaxis_title=selected_metric_name,
        showlegend=False 
    )
    
    st.plotly_chart(fig_box, use_container_width=True)

    # Each District Accountability Index
    district_summary = filtered_df.groupby(DIST_COL)[INDEX_COL].mean().reset_index()
    num_districts = len(district_summary)
    
    if num_districts > 0:
        cols = st.columns(num_districts)
        
        # Loop through each district
        for index, row in district_summary.iterrows():
            district_name = row[DIST_COL]
            avg_score = row[INDEX_COL]
            
            with cols[index]:
                st.metric(
                    label=f"{district_name}", 
                    value=f"{avg_score:.1f}"
                )

else:
    st.warning("Please adjust filters to see the disparity analysis.")

st.divider()

# CONCLUSION
st.info('In analyzing the Bridgeport school district, several strong positive and negative correlations of factors with success were seen. Inarguably, graduation rate and academic growth are very highly positively correlated with the Accountability Index. A sign that a school is able to retain its students is a strong indicator of the quality of that school. Academic growth is also very important, rather than just students achieving high test scores. This signifies the degree to which a student has learned and has been able to improve themselves. Schools with arts access and good physical fitness scores could have better success scores, but it is difficult to tell from these factors alone. Often, schools that already have high success scores have greater arts access and physical fitness scores. As epxected, academic achievement in subjects like ELA, math, and science support Accountability Index, but since this score is so well rounded, there are many other factors that determine the final value.')