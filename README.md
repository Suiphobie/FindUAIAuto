# UAI Finder and Académie Determiner

This application helps educational institutions in France:
1. Find UAI (Unité Administrative Immatriculée) codes
2. Determine Académie affiliations
3. Process CSV files with fuzzy matching logic

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run find_uai_app.py
```

The application will launch in your default web browser at `http://localhost:8501`

## Input File Requirements
Your CSV file must include these columns (case-insensitive):
- `NomEtablissement` (Establishment Name)
- `CodePostal` (Postal Code)
- `Adresse` (Address)

Example input structure:
```
NomEtablissement,CodePostal,Adresse
Lycée Jean Moulin,75015,123 Rue de l'Éducation
Collège Victor Hugo,13001,456 Avenue de la République
```

## How It Works
1. Upload your CSV file
2. The application:
   - Matches establishments using fuzzy logic
   - Determines Académie based on postal code
   - Flags non-educational institutions
   - Generates results with match scores
3. Download processed results as CSV

## Reference File
The application requires `fr-en-annuaire-education.csv` in the project directory. This file contains official education directory data from the French government.

## Notes
- Fuzzy matching requires at least 70% similarity score
- Académie mapping follows official postal code prefixes
- Non-educational institutions are automatically flagged
