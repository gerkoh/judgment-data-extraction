import pandas as pd
import streamlit as st
from datetime import datetime
import numpy as np

# streamlit_app.py integration for aws
# from st_files_connection import FilesConnection


#cleaning the dataframe first
#cleaning date of judgmenets:
# Example dates formats are "27-Jul-15" or "2/3/2020"
def standardize_date(date_str):     
    if date_str == "":
        return "NA"
    try:
        # Try parsing the date as "DD-MONTH-YY" format
        date_obj = datetime.strptime(date_str, "%d-%b-%y")
        return date_obj.strftime("%d %b %Y")  # Format as "27 Jul 2015"
    except ValueError:
        try:
            # If parsing as "DD-MONTH-YY" fails, try parsing as "dd/mm/yyyy" format
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            return date_obj.strftime("%d %b %Y")  # Format as "2 Mar 2020"
        except ValueError:
            return "Invalid"

# Filter length of marriage float
def convert_to_float_years(duration_str):
    # Check if the duration string is empty
    if duration_str == "" or duration_str =='Undisclosed':
        return 'NA'
    
    try:
        # Attempt to convert the duration string to a float
        total_years = float(duration_str)
    except ValueError:
        # If conversion fails, parse the string and calculate the duration in years
        parts = duration_str.split()
        years = 0
        months = 0
        for i, part in enumerate(parts):
            if part == 'years' or part == 'year' or part == 'Years' or part =='Year':
                years = float(parts[i - 1])
            elif part == 'months' or part == 'month'or part == 'Months' or part == 'Month':
                months = float(parts[i - 1])    
        fraction_of_year = round(months / 12, 2)
        total_years = years + fraction_of_year
        
        # Check if the duration is still zero after parsing
        if years == 0 and months == 0:
            total_years = 'Invalid'
    
    
    return total_years

#cleaning children data
def process_number_of_children(input_str):
    if pd.isna(input_str):  # Check if the input is NaN
        return 'NA'  # Return a suitable value for NaN
    try:
        # Attempt to convert the entire input string to an integer
        num_children = int(input_str)
        return num_children
    except ValueError:
        try:
            # Attempt to extract the first index and convert it to an integer
            num_children = int(input_str.split()[0])
            return num_children
        except ValueError:
            # If both attempts fail, return 'Invalid'
            return 'Invalid'

#clean income type data
def clean_single_or_dual_income_marriage(value):
    if value == "":
        return 'NA'
    # Check if the value is a string and not empty
    if isinstance(value, str) and value.strip():  # Check if string is not empty after stripping whitespace
        if len(value)==0:
            return 'NA'
        # Remove leading and trailing whitespace (including non-breaking space)
        value = value.strip()
        # Convert to lowercase
        value = value.lower()
        return value
    else:
        # If the value is empty or not a string, return NaN
        return np.nan

#clean final ratio
def clean_final_ratio(value):
    # Check if the value can be converted to a float directly
    if value =="":
        return 'NaN'
    try:
        return float(value)
    except ValueError:
        pass
    
    # Check if the value contains "%"
    if "%" in value:
        # Remove everything after the first occurrence of "%"
        value = value.split("%", 1)[0].strip()
        # Check if the remaining string can be converted to a float
        try:
            return float(value)
        except ValueError:
            pass

    # If conversion fails, return 'Invalid'
    return 'Invalid'
#remove invalid data

def remove_invalid_data(df):
    # List of columns to consider for dropping NA values
    columns_to_check = ['Date of Judgments', 
                        'Length of marriage till IJ (include separation period) in years',
                        'Number of children',
                        'Single or Dual Income Marriage',
                        'Final ratio (Wife:Husband, post-adjustments)']

    # Initialize an empty DataFrame to store the cleaned data
    cleaned_df = df
    
    # Iterate through each column and drop NaN and 'Invalid' values
    for col in columns_to_check:
        # Drop rows with NaN values in the current column
        cleaned_df = cleaned_df.dropna(subset=[col], how='any')
        
        # Drop rows containing 'Invalid' in the current column
        cleaned_df = cleaned_df[~cleaned_df[col].isin(['Invalid','NA'])]
        
    # Reset index if needed
    cleaned_df.reset_index(drop=True, inplace=True)
    
    return cleaned_df

def add_url_to_df(df):
    # Define the position and name for the new column
    position = 2
    new_column_name = 'URL'
    new_column_data = []
    base_url = 'https://www.elitigation.sg/gd/s/'

    # Iterate over the 'Citation' column to construct the URL
    for i in df['Citation']:
        parts = i.split(' ', 2)
        stripped_part_0 = parts[0].strip('[]')
        url = f"{base_url}{stripped_part_0}_{parts[1]}_{parts[2]}"
        new_column_data.append(url)

    df.insert(position, new_column_name, new_column_data)
    return df
    
    

def run_me(df):
    #rename all the columns to the appropriate names if they are not already
    current_column_names = df.columns.tolist()

    new_column_names = [
        "Cases",
        "Citation",
        "Date of Judgments",
        "Length of marriage till IJ (include separation period) in years",
        "Length of marriage (exclude separation period)",
        "Number of children",
        "Wife's income (monthly $)",
        "Husband's income (monthly $)",
        "Single or Dual Income Marriage",
        "Direct contribution (Wife)",
        "Indirect contribution (Wife)",
        "Average ratio (Wife)",
        "Final ratio (Wife:Husband, post-adjustments)",
        "Adjustments?",
        "Adjustments were for",
        "Remarks",
        "",
        "",
        "New columns",	
        "Cost of Court"]

    # Rename each column
    for i in range(len(current_column_names)):
        df = df.rename(columns={current_column_names[i]: new_column_names[i]})
    # Drop the 3rd & 4th last columns which are empty
    df = df.drop(df.columns[-5:], axis=1)
    
    #convert dates to string just in case not all are string
    df['Date of Judgments'] = df['Date of Judgments'].astype(str)    
    df['Date of Judgments'] = df['Date of Judgments'].apply(lambda x: standardize_date(x))
    
    df["Length of marriage till IJ (include separation period) in years"] = df["Length of marriage till IJ (include separation period) in years"].apply(convert_to_float_years)
    df["Number of children"] = df["Number of children"].apply(process_number_of_children)
    df['Single or Dual Income Marriage'] = df['Single or Dual Income Marriage'].apply(clean_single_or_dual_income_marriage)
    df["Final ratio (Wife:Husband, post-adjustments)"] = df["Final ratio (Wife:Husband, post-adjustments)"].apply(clean_final_ratio)
    
    
    df=remove_invalid_data(df)
    df = add_url_to_df(df)
    return df

#import the csv into a pandas df and clean it up
# Create connection object and retrieve file contents.
# Specify input format is a csv and to cache the result for 600 seconds.
# conn = st.connection('s3', type=FilesConnection)
# df = conn.read("sg-family-law-judgments/gold_standard_elit.csv", input_format="csv", ttl=600)

#remove index row if it exists
file = 'streamlit/gold_standard_elit.csv'
df = pd.read_csv(file)
if df.columns[0] == 'Unnamed: 0':
    df = df.drop(columns=df.columns[0])
df = run_me(df)

########
########
########

# STREAMLIT WEBAPP
st.set_page_config(page_title='Family Courts Case Bank')
st.header('Case Bank: Division of Matrimonial Assets')
st.subheader('Filter cases by categories below')


#Streamlit Selection
# Length of marriage till IJ (include separation period)
loms_ij = df['Length of marriage till IJ (include separation period) in years'].unique().tolist()
loms_ij = [float(item) for item in loms_ij]
lom_ij  = st.slider('Length of marriage till IJ (include separation period) in years:',
                        min_value= 0,
                        max_value= 100,
                        value=(0, 100))

# Number of children
num_children = df['Number of children'].unique().tolist()
num_children = [float(item) for item in num_children]
child = st.slider('Number of children:',
                        min_value= 0,
                        max_value= 30,
                        value=(0, 30))


# Single or dual income marriage
marriage_types = sorted(df['Single or Dual Income Marriage'].unique().tolist())
marriage_type = st.multiselect('Income Type:',
                                    marriage_types,
                                    default=marriage_types)

# Final Ratio
final_ratios = df['Final ratio (Wife:Husband, post-adjustments)'].unique().tolist()
final_ratios = [float(item) for item in final_ratios]
final_ratio = st.slider('Final Ratio of Contributions, Wife:Husband:',
                        min_value= 0,
                        max_value= 100,
                        value=(0,100))

    
mask = (
    df['Length of marriage till IJ (include separation period) in years'].between(*lom_ij) &
    df['Number of children'].between(*child) &
    df['Single or Dual Income Marriage'].isin(marriage_type) &
    df['Final ratio (Wife:Husband, post-adjustments)'].between(*final_ratio)
)


number_of_result = df[mask].shape[0]
st.markdown(f'*Available Results: {number_of_result}*')

st.data_editor(
    df[mask],
    column_config={
        "URL": st.column_config.LinkColumn("URL")
    },
    hide_index=True,
    use_container_width=True
)
