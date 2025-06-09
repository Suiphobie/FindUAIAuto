# Plan for Finding UAI of Schools

## Steps

1. **Read the Input CSV File and the Reference File**
   - Use pandas to read the input CSV file and the reference CSV file.

2. **Search for the Most Probable UAI**
   - For each school in the input file, search for the most probable UAI in the reference file using the three pieces of information available (NomEtablissement, CodePostal, and Adresse).

3. **Determine the Académie**
   - Determine the Académie from the Code_postal even if no UAI is found.

4. **Add Results to a New DataFrame**
   - Add the results to a new DataFrame with the columns NomEtablissement, CodePostal, Adresse, Identifiant_de_l_etablissement, and Académie.

5. **Allow Download of the Result as a CSV**
   - Allow the download of the result as a CSV file.

6. **Create a Streamlit Script**
   - Create a Streamlit script with a user interface that allows the user to upload the input CSV file, start the processing, and download the result as a CSV.

## Libraries Used

- **pandas**: For data manipulation.
- **streamlit**: For the user interface.

## Mermaid Diagram

```mermaid
graph TD;
    A[Start] --> B[Read Input CSV File];
    B --> C[Read Reference CSV File];
    C --> D[For each school in input file];
    D --> E[Search for most probable UAI in reference file];
    E --> F[Determine Académie from Code_postal];
    F --> G[Add results to new DataFrame];
    G --> H[Allow download of result as CSV];
    H --> I[End];