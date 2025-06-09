import streamlit as st
import pandas as pd
import io
from thefuzz import fuzz, process

# Académie determination logic based on matching.md
ACADEMIE_DEPARTEMENT_MAP = {
    "04": "Aix-Marseille", "13": "Aix-Marseille", "83": "Aix-Marseille", "84": "Aix-Marseille",
    "02": "Amiens", "60": "Amiens", "80": "Amiens",
    "25": "Besançon", "39": "Besançon", "70": "Besançon", "90": "Besançon",
    "24": "Bordeaux", "33": "Bordeaux", "40": "Bordeaux", "47": "Bordeaux", "64": "Bordeaux",
    "14": "Caen", "50": "Caen", "61": "Caen", # Note: Caen is now part of Normandie
    "03": "Clermont-Ferrand", "15": "Clermont-Ferrand", "43": "Clermont-Ferrand", "63": "Clermont-Ferrand",
    "2A": "Corse", "2B": "Corse", "20": "Corse", # 20 is often used for Corse
    "77": "Créteil", "93": "Créteil", "94": "Créteil",
    "21": "Dijon", "58": "Dijon", "71": "Lyon", # Note: 71 is listed under Lyon in some contexts, but Dijon historically. matching.md says Dijon.
    "89": "Dijon",
    "05": "Grenoble", "07": "Grenoble", "26": "Grenoble", "38": "Grenoble", "73": "Grenoble", "74": "Grenoble",
    "59": "Lille", "62": "Lille",
    "19": "Limoges", "23": "Limoges", "87": "Limoges",
    "01": "Lyon", "69": "Lyon", # 71 is listed for Lyon in matching.md, also for Dijon. Prioritizing matching.md for Lyon here.
    "11": "Montpellier", "30": "Montpellier", "34": "Montpellier", "48": "Montpellier", "66": "Montpellier",
    "54": "Nancy-Metz", "55": "Nancy-Metz", "57": "Nancy-Metz", "88": "Nancy-Metz",
    "44": "Nantes", "49": "Nantes", "53": "Nantes", "72": "Nantes", "85": "Nantes",
    "06": "Nice", # 20 is listed for Nice in matching.md, but also for Corse. Corse is more specific for 2A/2B.
    "18": "Orléans-Tours", "28": "Orléans-Tours", "36": "Orléans-Tours", "37": "Orléans-Tours", "41": "Orléans-Tours", "45": "Orléans-Tours",
    "75": "Paris",
    "16": "Poitiers", "17": "Poitiers", "79": "Poitiers", "86": "Poitiers",
    "08": "Reims", "10": "Reims", "51": "Reims", "52": "Reims",
    "22": "Rennes", "29": "Rennes", "35": "Rennes", "56": "Rennes",
    "974": "La Réunion",
    "67": "Strasbourg", "68": "Strasbourg",
    "09": "Toulouse", "12": "Toulouse", "31": "Toulouse", "32": "Toulouse", "46": "Toulouse", "65": "Toulouse", "81": "Toulouse", "82": "Toulouse",
    "78": "Versailles", "91": "Versailles", "92": "Versailles", "95": "Versailles"
}
# Handle specific case for 71 (Saône-et-Loire) which is listed for both Dijon and Lyon in matching.md
# Given Lyon is a larger academie, and it's listed second, we might prefer it, or acknowledge ambiguity.
# For now, the last entry in the dict for "71" would be "Lyon" due to dict creation order if not careful.
# Let's explicitly set it based on matching.md's structure. matching.md lists 71 under Dijon and Lyon.
# The provided matching.md lists 71 under Dijon (line 11) and Lyon (line 15).
# Let's be consistent with the first mention or a chosen priority. For this implementation,
# the dictionary above will map 71 to Lyon because it appears later in the list of departments for Lyon.
# If a different priority is needed, this map should be adjusted.
# For Corsica, 2A, 2B are specific. 20 is a general code sometimes used.
ACADEMIE_DEPARTEMENT_MAP["20"] = "Corse" # Explicitly ensure 20 maps to Corse if not covered by 2A/2B

def determine_academie(code_postal):
    """
    Determines the Académie based on the postal code using the mapping from matching.md.
    """
    if not isinstance(code_postal, str) or len(code_postal) < 2:
        return "Unknown (Invalid Postal Code)"

    dept_code = code_postal[:2].upper() # Use first two characters for department

    # Handle Corsica specific codes if postal code is like "2A..." or "2B..."
    if dept_code == "2A" or dept_code == "2B":
        return ACADEMIE_DEPARTEMENT_MAP.get(dept_code, "Unknown (Corse Dept. Not Found)")
    
    # For numeric department codes
    if dept_code.isdigit():
        return ACADEMIE_DEPARTEMENT_MAP.get(dept_code, "Unknown (Dept. Not Found)")
    
    return "Unknown (Non-standard Postal Code Format)"

def find_most_probable_uai(school_info, reference_df_with_search_string, uai_col_name="Identifiant_de_l_etablissement"):
    """
    Searches for the most probable UAI using fuzzy matching on a combined search string.
    Returns UAI and match score.
    """
    nom_etablissement = str(school_info.get("NomEtablissement", ""))
    adresse = str(school_info.get("Adresse", ""))
    code_postal = str(school_info.get("CodePostal", ""))

    query_string = f"{nom_etablissement} {adresse} {code_postal}".strip()

    if not query_string or reference_df_with_search_string.empty or 'search_string_ref' not in reference_df_with_search_string.columns:
        return "Not Found", 0

    # Use process.extractOne to find the best match with a score
    # The choices are the 'search_string_ref' Series from the reference DataFrame
    # extractOne returns (value, score, key) where key is the index from the Series
    match = process.extractOne(query_string, reference_df_with_search_string['search_string_ref'], scorer=fuzz.WRatio, score_cutoff=70)

    if match:
        # match is (matched_string_from_reference, score, index_in_reference_df)
        matched_index = match[2]
        uai = reference_df_with_search_string.loc[matched_index, uai_col_name]
        score = match[1]
        return uai, score
    
    return "Not Found", 0

def get_column_name(df_columns, potential_names):
    """Helper function to find the first matching column name from a list of potentials."""
    for name in potential_names:
        if name in df_columns:
            return name
    return None

def process_files(input_df, reference_df):
    """
    Processes the input DataFrame to find UAI and determine Académie using the reference DataFrame.
    Handles variations in input column names.
    """
    results = []
    df_cols = input_df.columns

    # Define potential variations for essential column names
    potential_nom_cols = ["NomEtablissement", "nomEtablissement", "nom_etablissement", "Nom Etablissement", "NOM ETABLISSEMENT"]
    potential_cp_cols = ["CodePostal", "codePostal", "code_postal", "Code Postal", "CODE POSTAL"]
    potential_adresse_cols = ["Adresse", "adresse", "ADRESSE"]

    # Get actual column names from input_df
    col_nom_actual = get_column_name(df_cols, potential_nom_cols)
    col_cp_actual = get_column_name(df_cols, potential_cp_cols)
    col_adresse_actual = get_column_name(df_cols, potential_adresse_cols)

    # Check if essential columns were found
    missing_actual_cols = []
    if not col_nom_actual: missing_actual_cols.append(f"Establishment Name (e.g., {potential_nom_cols[0]})")
    if not col_cp_actual: missing_actual_cols.append(f"Postal Code (e.g., {potential_cp_cols[0]})")
    if not col_adresse_actual: missing_actual_cols.append(f"Address (e.g., {potential_adresse_cols[0]})")

    if missing_actual_cols:
        st.error(f"Input CSV is missing required columns: {', '.join(missing_actual_cols)}.")
        return pd.DataFrame()

    for _, row in input_df.iterrows():
        # Use the dynamically found column names to access data
        nom_etablissement_val = row[col_nom_actual]
        code_postal_val = row[col_cp_actual]
        adresse_val = row[col_adresse_actual]

        school_info = {
            "NomEtablissement": nom_etablissement_val, # Standardized key for find_most_probable_uai
            "CodePostal": code_postal_val,           # Standardized key
            "Adresse": adresse_val                   # Standardized key
        }

        uai, uai_score = find_most_probable_uai(school_info, reference_df) # Pass the prepared reference_df
        academie = determine_academie(str(code_postal_val)) # Ensure code_postal is string for academie logic

        results.append({
            "NomEtablissement": nom_etablissement_val,
            "CodePostal": code_postal_val,
            "Adresse": adresse_val,
            "Identifiant_de_l_etablissement": uai, # uai already includes "Not Found" if applicable
            "Match_Score_UAI": uai_score,
            "Académie": academie
        })

    return pd.DataFrame(results)

st.title("UAI Finder and Académie Determiner")

st.header("1. Upload Input File")
input_file = st.file_uploader("Upload Input CSV File (with NomEtablissement, CodePostal, Adresse)", type="csv")

# Load the reference file directly
REFERENCE_FILE_PATH = "fr-en-annuaire-education.csv"
reference_df = None # Initialize reference_df
try:
    reference_df = pd.read_csv(REFERENCE_FILE_PATH, sep=';', low_memory=False)
    st.success(f"Successfully loaded reference file: {REFERENCE_FILE_PATH}")
    # Normalize column names in reference_df for broader compatibility
    reference_df.columns = reference_df.columns.str.replace(' ', '_').str.replace('-', '_').str.replace('.', '_', regex=False)
    cols_to_normalize_ref = {
        'NOM_ETABLISSEMENT': 'Nom_etablissement',
        'LIBELLE_ETABLISSEMENT': 'Nom_etablissement',
        'CODE_POSTAL': 'Code_postal',
        'UAI': 'Identifiant_de_l_etablissement',
        'IDENTIFIANT_ETABLISSEMENT': 'Identifiant_de_l_etablissement',
        # Address fields for reference data - first one found will be used as 'Adresse_ref' (expanded list)
        'ADRESSE_ETABLISSEMENT': 'Adresse_ref',
        'LIBELLE_VOIE': 'Adresse_ref',
        'ADRESSE_LIGNE_1': 'Adresse_ref',
        'ADRESSE_LIGNE1': 'Adresse_ref',
        'ADRESSE1': 'Adresse_ref',
        'LIEU_DIT_OU_BP': 'Adresse_ref',
        'LieuDitOuBP': 'Adresse_ref',
        'ADRESSE': 'Adresse_ref',
        'AdressePostale': 'Adresse_ref',
        'ADRESSE_POSTALE': 'Adresse_ref',
        'Localisation': 'Adresse_ref', # Sometimes used for full address or part of it
        'LOCALISATION': 'Adresse_ref',
        'ADRESSE_DE_L_ETABLISSEMENT': 'Adresse_ref',
        'ADRESSE_DE_L_ÉTABLISSEMENT': 'Adresse_ref', # With accent
        'ADRESSE_COMPLETE': 'Adresse_ref',
        'AdresseComplete': 'Adresse_ref',
        'Street': 'Adresse_ref', # English variations sometimes appear
        'Address': 'Adresse_ref'
    }
    reference_df = reference_df.rename(columns=lambda c: cols_to_normalize_ref.get(c.upper(), c))

    # Ensure essential columns for matching exist in reference_df after normalization
    required_ref_cols = ['Nom_etablissement', 'Code_postal', 'Identifiant_de_l_etablissement']
    if 'Adresse_ref' not in reference_df.columns:
        st.warning("Could not find a standard address column (e.g., Adresse_etablissement, Libelle_voie) in reference file. Fuzzy matching quality might be reduced.")
        reference_df['Adresse_ref'] = "" # Create an empty column to prevent errors
    else:
        required_ref_cols.append('Adresse_ref')

    for col in required_ref_cols:
        if col not in reference_df.columns:
            st.error(f"Critical Error: Reference file is missing essential column '{col}' after normalization. Cannot proceed with matching.")
            st.stop()
    
    # Create a combined search string in the reference DataFrame for fuzzy matching
    # Fill NaN values with empty strings before concatenation
    reference_df['search_string_ref'] = reference_df['Nom_etablissement'].fillna('').astype(str) + " " + \
                                        reference_df['Adresse_ref'].fillna('').astype(str) + " " + \
                                        reference_df['Code_postal'].fillna('').astype(str)
    reference_df['search_string_ref'] = reference_df['search_string_ref'].str.strip()

except FileNotFoundError:
    st.error(f"Critical Error: The reference file '{REFERENCE_FILE_PATH}' was not found in the application directory. Please ensure it is present.")
    st.stop()
except pd.errors.EmptyDataError:
    st.error(f"Critical Error: The reference file '{REFERENCE_FILE_PATH}' is empty.")
    st.stop()
except Exception as e:
    st.error(f"Critical Error: Could not load or parse the reference file '{REFERENCE_FILE_PATH}'. Error: {e}")
    st.stop()

if input_file and reference_df is not None: # Check reference_df is loaded
    st.header("2. Process Data")
    if st.button("Start Processing"):
        try:
            input_df = None
            encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'windows-1252']
            delimiters_to_try = [',', ';', '\t']
            read_successful = False
            last_error = None

            for encoding in encodings_to_try:
                for delimiter in delimiters_to_try:
                    try:
                        # Reset file pointer before each attempt
                        if hasattr(input_file, 'seek'):
                            input_file.seek(0)
                        
                        current_df = pd.read_csv(input_file, encoding=encoding, sep=delimiter)
                        
                        # Basic validation: Check if expected columns can be found (using existing helper)
                        # This helps to confirm if the delimiter was correct.
                        temp_cols = current_df.columns
                        potential_nom_cols = ["NomEtablissement", "nomEtablissement", "nom_etablissement"] # Simplified for quick check
                        if get_column_name(temp_cols, potential_nom_cols):
                            input_df = current_df
                            st.success(f"Successfully read input file with encoding '{encoding}' and delimiter '{delimiter}'.")
                            read_successful = True
                            break # Break from delimiter loop
                        else:
                            # This delimiter might not be the right one, even if parsing didn't error
                            st.write(f"Parsed with encoding '{encoding}', delimiter '{delimiter}', but couldn't find expected columns. Trying next.")
                            last_error = "Could not find expected columns after parsing."
                            
                    except UnicodeDecodeError:
                        last_error = f"UnicodeDecodeError with encoding '{encoding}'"
                        # Continue to next encoding or delimiter
                    except pd.errors.ParserError as pe:
                        last_error = f"ParserError with encoding '{encoding}', delimiter '{delimiter}': {pe}"
                        # Continue
                    except Exception as e:
                        last_error = f"General error with encoding '{encoding}', delimiter '{delimiter}': {e}"
                        # Continue
                if read_successful:
                    break # Break from encoding loop
            
            if not read_successful or input_df is None:
                st.error(f"Failed to read input file with all attempted encodings and delimiters. Last error: {last_error}")
                st.stop()
            # reference_df is already loaded and normalized globally
            
            # Column normalization for reference_df is now done at initial load.


            st.subheader("Input Data Preview (First 5 rows)")
            st.dataframe(input_df.head())

            st.subheader("Reference Data Preview (First 5 rows)")
            st.dataframe(reference_df.head())
            st.write(f"Reference data columns: {reference_df.columns.tolist()}")


            with st.spinner("Processing..."):
                result_df = process_files(input_df, reference_df)

            st.subheader("3. Results")
            st.dataframe(result_df)

            if not result_df.empty:
                csv_buffer = io.StringIO()
                result_df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                st.download_button(
                    label="Download Results as CSV",
                    data=csv_buffer.getvalue(),
                    file_name="uai_results.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Processing resulted in an empty DataFrame. Check input data and matching logic.")

        except pd.errors.EmptyDataError:
            st.error("One of the uploaded CSV files is empty.")
        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
            st.error("Please ensure your input CSV file is correctly formatted and column names match expectations (e.g., 'NomEtablissement', 'CodePostal', 'Adresse').")

# If the main 'if input_file and reference_df is not None:' is false,
# and reference_df is not None (meaning it loaded successfully),
# then it must be that input_file is None.
elif reference_df is not None and not input_file:
    st.info("Upload an input CSV file to begin processing.")
# The case where reference_df is None is handled by st.stop() at the beginning.
# If execution reaches here and input_file is None, it means reference_df loaded.
elif not input_file: # Catches the case where input_file is None (and reference_df was loaded)
     st.info("Please upload an input CSV file to start.")

st.markdown("---")
st.markdown("Script based on plan.md")
st.markdown("""
### Notes on UAI Matching and Académie:
- The UAI matching logic (`find_most_probable_uai`) now uses fuzzy matching (via `thefuzz` library with `WRatio` scorer) on a combination of establishment name, address, and postal code. It requires a match score of at least 70%.
- The reference data is preprocessed to create a combined search string. An address column (e.g., 'Adresse_etablissement', 'Libelle_voie') is sought in the reference file; if not found, matching quality may be reduced.
- The Académie determination (`determine_academie`) uses a direct mapping from postal code prefixes to Académies based on `matching.md`.
- Column names in the reference CSV for UAI, establishment name, postal code, and address are normalized to standard internal names.
- **Dependency**: This script now requires the `thefuzz` library (and its dependency `python-Levenshtein` for better performance). Install with `pip install thefuzz python-Levenshtein`.
""")