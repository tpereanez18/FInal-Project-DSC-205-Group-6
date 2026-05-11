import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# --- DATA LOADING ---
CSV_URL = "https://raw.githubusercontent.com/tpereanez18/FInal-Project-DSC-205-Group-6/refs/heads/main/Next_Generation_Accountability_System_20260407.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Core columns for analysis
    numeric_cols = [
        'Ind4Rate', 'Accountability Index', 'Ind9Rate', 'Ind10Rate',
        'Ind1ELA_All_Points', 'Ind1Math_All_Points', 
        'Ind1Sci_All_Points', 'Ind11FitnessRate', 'Ind12Rate', 'FallOfYear'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Normalize Decimals to Percentages
    if df['Ind9Rate'].max() <= 1.1: df['Ind9Rate'] *= 100
    if df['Ind4Rate'].max() <= 1.1: df['Ind4Rate'] *= 100
    if 'Ind11FitnessRate' in df.columns and df['Ind11FitnessRate'].max() <= 1.1: 
        df['Ind11FitnessRate'] *= 100
    if 'Ind12Rate' in df.columns and df['Ind12Rate'].max() <= 1.1: 
        df['Ind12Rate'] *= 100
        
    return df

st.set_page_config(page_title="CT Accountability Dashboard", layout="wide")

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- COLUMN MAPPING ---
DIST_COL = 'RptngDistrictName'
SCH_COL = 'SchoolName'
INDEX_COL = 'Accountability Index'
ABSENT_COL = 'Ind4Rate' 
GRAD_COL = 'Ind9Rate' 
GROWTH_COL = 'Ind12Rate'
CAT_COL = 'Category'
GROUP_COL = 'StudentGroup'
YEAR_COL = 'FallOfYear'

# --- SIDEBAR FILTERS ---
st.sidebar.header("Dashboard Filters")

# 1. UPDATED YEAR FILTER WITH "ALL YEARS"
years_list = sorted(df[YEAR_COL].dropna().unique().astype(int), reverse=True)
options = ["All Years"] + [str(y) for y in years_list]
selected_year_option = st.sidebar.selectbox("Select School Year", options=options)

# 2. District Filter
districts = sorted(df[DIST_COL].dropna().unique())
selected_dist = st.sidebar.multiselect("Select District", options=districts, default=["Bridgeport School District"])

# 3. School Filter
school_options = sorted(df[df[DIST_COL].isin(selected_dist)][SCH_COL].unique())
selected_schools = st.sidebar.multiselect("Select School", options=school_options)

# --- FILTERING LOGIC ---
filtered_df = df.copy()

# Apply Year Filter only if a specific year is chosen
if selected_year_option != "All Years":
    filtered_df = filtered_df[filtered_df[YEAR_COL] == int(selected_year_option)]

# Apply District/School Filters
filtered_df = filtered_df[filtered_df[DIST_COL].isin(selected_dist)]
if selected_schools:
    filtered_df = filtered_df[filtered_df[SCH_COL].isin(selected_schools)]

# --- MAIN UI ---
st.title(f"Next Generation Accountability Dashboard: {selected_year_option}")

# --- DEEP DIVE: THE "SCHOOL HEALTH SCORE" ---
st.subheader("Deep Dive: What is the Accountability Index?")
with st.expander( "How schools in CT are actually graded", expanded=True):
    st.write("### Think of it like a 'GPA' for the whole building.")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
        **1. It’s more than just a test grade** 📝
        If you get an 'A' on a test but never show up to class, are you a great student? The state says no. 
        * **The Index** combines test scores with **Attendance**. 
        * If students are 'Chronic Absentees' (missing 10%+ of school), the school loses points—no matter how high the test scores are.
        
        **2. Progress > Perfection** 📈
        The Index tracks **Growth**. This means a school gets credit for a student moving from a 'D' to a 'C', even if they aren't at an 'A' yet. It rewards schools for the hard work of improving.
        """)
    
    with col_b:
        st.markdown("""
        **3. The 'Well-Rounded' Factor** 🎨
        The state wants schools to be more than 'test factories.' Points are awarded for:
        * **Arts Access:** Does the school offer music, theater, and art?
        * **Physical Fitness:** Are students healthy and active?
        * **College Prep:** Is the school actually getting students ready for the real world?
        """)
        
    st.info("""
    **💡 The Bottom Line:** A score of **75** is the 'Passing Grade' set by Connecticut. 
    When you see a school with a low bar in our charts, it usually means they are struggling with **Attendance** or **Subject Growth**, not just that the students are 'bad at testing.'
    """)

# --- KPI METRICS ---
m1, m2, m3 = st.columns(3)
with m1: st.metric("Avg Accountability Index", f"{filtered_df[INDEX_COL].mean():.1f}")
with m2: st.metric("Avg Graduation Rate", f"{filtered_df[GRAD_COL].mean():.1f}%")
with m3: st.metric("Avg Chronic Absenteeism", f"{filtered_df[ABSENT_COL].mean():.1f}%")

st.divider()

# --- SECTION 1: ACHIEVEMENT VS GROWTH (SCATTERPLOT) ---
st.header("1. How do Academic Achievement and Academic Growth relate?")
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

# --- SECTION 2: ABSENTEEISM ---
st.header("2. Does Chronic Absenteeism Impact Student Performance?")
if not filtered_df.empty:
    # We group by school here so that "All Years" doesn't create duplicate bars for the same school
    absent_summary = filtered_df.groupby(SCH_COL)[[INDEX_COL, ABSENT_COL]].mean().reset_index()
    fig_absent = px.bar(
        absent_summary, x=SCH_COL, y=INDEX_COL, color=ABSENT_COL,
        color_continuous_scale='RdYlGn_r', 
        title=f"Performance vs. Absenteeism ({selected_year_option})"
    )
    st.plotly_chart(fig_absent, use_container_width=True)

st.divider()

# --- SECTION 3: GRADUATION GAPS (SCATTERPLOT BY STUDENT GROUP) ---
st.header("3. Are Graduation Rates Consistent Across All Student Groups?")
if not filtered_df.empty:
# Filter out the "All Students" category to see specific group gaps more clearly
    group_df = filtered_df[filtered_df[CAT_COL] != 'All Students'].dropna(subset=[GRAD_COL, INDEX_COL])

# Create an interactive Plotly scatter to allow hovering over group names
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

    st.info("""     **How to analyze this chart:**     * If the dots are all mixed together, graduation rates are consistent.     * **If certain colors (like 'Students with Disabilities' or 'English Learners') are consistently lower than others**, it shows a 'Graduation Gap' that the school needs to address.     """)
else:
    st.warning("No category-specific data available for this selection.")

 

st.divider()



st.divider()

# --- SECTION 4: SUBJECT BREAKDOWN ---
st.header("4. What is Driving the Score? ELA, Math, and Science")
if not filtered_df.empty:
    subject_map = {'Ind1ELA_All_Points': 'ELA', 'Ind1Math_All_Points': 'Math', 'Ind1Sci_All_Points': 'Science'}
    # Average subjects by school if "All Years" is selected
    subj_summary = filtered_df.groupby(SCH_COL)[list(subject_map.keys())].mean().reset_index()
    melted_df = subj_summary.melt(id_vars=[SCH_COL], value_vars=list(subject_map.keys()), var_name='Subject', value_name='Points')
    melted_df['Subject'] = melted_df['Subject'].map(subject_map)
    fig_subjects = px.bar(melted_df, x=SCH_COL, y='Points', color='Subject', barmode='group')
    st.plotly_chart(fig_subjects, use_container_width=True)

st.divider()

# --- SECTION 5: HEATMAP ---
st.header("5. Do Non-Academic Factors Correlate with Success?")
heatmap_source = filtered_df if len(filtered_df) > 5 else df[df[DIST_COL].isin(selected_dist)]
if not heatmap_source.empty:
    heatmap_cols = {INDEX_COL: 'Success', ABSENT_COL: 'Absenteeism', 'Ind11FitnessRate': 'Fitness', GROWTH_COL: 'Growth', 'Ind10Rate': 'Graduation'}
    h_data = heatmap_source[list(heatmap_cols.keys())].rename(columns=heatmap_cols)
    fig_heat, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(h_data.corr(), annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
    st.pyplot(fig_heat)

# Raw Data Table
if st.checkbox("Show Raw Data Table"):
    st.dataframe(filtered_df)

st.divider()

# --- SECTION 6: STRONGEST PREDICTORS ---
st.header("6. Which indicators are the strongest predictors of overall school performance?")
st.markdown("This chart shows the **correlation** between various school indicators and the overall Accountability Index. Items stretching further to the right have the strongest positive relationship with overall performance, while items stretching to the left (like Absenteeism) pull the score down.")

if not filtered_df.empty:
    # 1. Define the predictor columns to test against the Accountability Index
    predictor_cols = [
        'Ind1ELA_All_Points', 'Ind1Math_All_Points', 'Ind1Sci_All_Points',
        'Ind4Rate', 'Ind9Rate', 'Ind11FitnessRate', 'Ind12Rate'
    ]
    
    # 2. Map them to reader-friendly names for the chart
    friendly_names = {
        'Ind1ELA_All_Points': 'ELA Achievement',
        'Ind1Math_All_Points': 'Math Achievement',
        'Ind1Sci_All_Points': 'Science Achievement',
        'Ind4Rate': 'Chronic Absenteeism',
        'Ind9Rate': 'Graduation Rate',
        'Ind11FitnessRate': 'Physical Fitness',
        'Ind12Rate': 'Academic Growth'
    }
    
    # Ensure columns exist in the current dataframe subset
    available_cols = [c for c in predictor_cols if c in filtered_df.columns]
    
    if available_cols:
        # 3. Calculate the Pearson correlation with the Accountability Index
        # We drop the Index itself so it doesn't plot a perfect 1.0 correlation with itself
        corr_data = filtered_df[available_cols + [INDEX_COL]].corr()[INDEX_COL].drop(INDEX_COL)
        
        # 4. Format into a DataFrame for Plotly Express
        corr_df = corr_data.reset_index()
        corr_df.columns = ['Indicator', 'Correlation']
        corr_df['Indicator'] = corr_df['Indicator'].map(friendly_names)
        
        # Sort values so the graph looks clean and descending
        corr_df = corr_df.sort_values(by='Correlation', ascending=True)
        
        # 5. Build the horizontal bar chart
        fig_predictors = px.bar(
            corr_df, 
            x='Correlation', 
            y='Indicator', 
            orientation='h',
            color='Correlation',
            color_continuous_scale='RdYlGn', # Red (negative) to Green (positive)
            text_auto='.2f', # Show the exact decimal on the bars
            title=f"Predictors of School Success ({selected_year_option})"
        )
        
        fig_predictors.update_layout(xaxis_title="Correlation Coefficient (-1.0 to 1.0)", yaxis_title="")
        st.plotly_chart(fig_predictors, use_container_width=True)
else:
    st.warning("Please adjust filters to see the predictor analysis.")