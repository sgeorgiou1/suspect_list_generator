# suspect_list_generator

## Overview
This Python script is designed to extract and analyze indexing data from Inspec2 XML files. It performs various operations such as extracting indexing information, generating suspect term lists, and saving the results for further analysis. - These codes assume you have already downloaded the item XML files.

## Requirements
- Python 3.x
- numpy
- pandas
- tqdm
- dodgyextract_v2
- bypass_checker

## Usage
1. Clone or download this repository to your local machine. - save in the same directory where you have saved your XML files folder
2. Ensure that all required packages are installed using `pip install numpy pandas tqdm`.
3. Open and run `directory-setup.py` to setup correct output folders
4. Import the `suspect_list_generator.py` script in your preferred Python editor or IDE.
5. Run the script using Python. 
 ### NOTE: Ensure `bypass_checker.py` and `dodgyextract_v2` are saved in the same directory as   `suspect_list_generator.py`
## Features
- **Index Extraction:** Extracts indexing data from files using the `dodgyextract_v2` module.
- **Index Analysis:** Analyzes the extracted indexing data and generates statistics such as term counts, precision values, and more.
- **Suspect Term Generation:** Generates suspect term lists based on specified criteria such as precision limits or desired bypass rates.
- **Output Saving:** Saves the generated suspect term lists and analysis results to CSV files for further examination.

## Example
```python
# Example usage of the script
from suspect_list_generator import suspect_list_generator

# Initialize the suspect list generator
suspect_generator = suspect_list_generator('/path/to/data/', extract='n')

# Generate suspect term lists for CT and CC
suspect_generator.generate_ct_list(bypass_cutoff=0.5, max_precision=0.2)
suspect_generator.generate_cc_list(bypass_cutoff=0.6, desired_bypass=0.7)

# Save the generated lists
suspect_generator.save_lists()
