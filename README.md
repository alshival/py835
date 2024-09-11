<img src="DHR-Health-Logo.png" width="50%">


# PY835

The `EDI835Parser` is a Python-based tool designed to parse `.835` EDI files using the `pyx12` library. It extracts critical information such as patient data and transaction details, providing an easy-to-use interface that outputs the parsed data as Pandas DataFrames for further analysis.

## Features
- **Parse EDI 835 Files**: Efficiently load and parse `.835` files to extract important financial and transaction data.
- **Transaction Details**: Extract comprehensive transaction information, including service line data, payer, and payee information.
- **Column Naming**: Optional renaming of DataFrame columns using dynamic attributes extracted from the EDI file.

## Installation

To install `py835`, run 
```
pip install git+https://github.com/DHR-Health/py835.git
```

## Usage

`py835` is meant to streamline importing data from 835 files into your data warehouse.

### Basic Example: Parsing an 835 EDI File for Line-Item Transactions

Here is a simple example of how to parse a single `.835` file and extract its transaction details:

```python
import py835

# Path to a single .835 file
file_path = '/path/to/your/835/file.835'

# Initialize the parser
parser = py835.EDI835Parser(file_path)

# Extract transaction data with optional renaming of columns
transaction_df = parser.transactions(column_names=True)

# Display the transaction data
print(transaction_df)

# Upload to a database
import sqlite3
conn = sqlite3.connect('example.db')
transaction_df.to_sql('835_transaction_line_items',conn,index=False,if_exists='append')
```

### More Complicated Example: Parsing a Directory of 835 Files

If you need to process multiple `.835` files in a directory, the following example demonstrates how to loop through each file, extract the transaction data, and combine the results into a single DataFrame.

```python
import os
import re
import py835
import pandas as pd

# Directory containing .835 files
directory_path = '/path/to/your/directory'

# Initialize a list to hold all parsed DataFrames
dfs = []

# Loop through files in the directory, parse, and extract transactions
for file835 in [os.path.join(directory_path, x) for x in os.listdir(directory_path) if re.search(r'.*\.835.*', x)]:
    parser = py835.EDI835Parser(file835)
    transaction_data = parser.transactions(column_names=True)
    transaction_data['file'] = file835  # Add the file name to each row
    dfs.append(transaction_data)

# Combine all dataframes into one
combined_df = pd.concat(dfs, ignore_index=True)

# Display the combined dataframe
print(combined_df)

# Upload to a database
import sqlite3
conn = sqlite3.connect('example.db')
combined_df.to_sql('835_transaction_line_items',conn,index=False,if_exists='append')
```

## Methods

- **`patients()`**: Returns a Pandas DataFrame containing patient-related information extracted from the `.835` file.
- **`transactions(column_names=False)`**: Returns a Pandas DataFrame of transaction data. Optionally, renames columns based on attributes extracted from the file.

## Dependencies
- `pyx12`
- `pandas`

## License
This project is licensed under the MIT License.
