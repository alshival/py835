<img src="DHR-Health-Logo.png" width="50%">

# py835

This Python package provides functionality for parsing EDI 835 files using the `pyx12` library. It extracts and organizes data from the EDI file, such as transaction sets, claims, services, and functional groups, into a structured format like Pandas DataFrames for easy data manipulation and analysis. It also supports exporting parsed data to JSON.

## Features

- **Parse EDI 835 Files:** Load and process `.835` EDI files for healthcare claims.
- **Extract Data:** Extracts functional groups, transaction sets, claims, and service-level information.
- **DataFrame Output:** Converts the parsed data into a Pandas DataFrame for easier analysis and manipulation.
- **Column Renaming:** Automatically renames columns based on EDI segment codes and descriptions.
- **JSON Export:** Supports exporting parsed data to JSON for further use in other systems.

## Installation

To install this package, run the following command:

```bash
pip install git+https://github.com/DHR-Health/py835.git
```

### Dependencies

- `pyx12`: Python library for EDI file parsing.
- `pandas`: Used for organizing parsed data into DataFrames.
- `io`: Standard Python module for handling input/output operations.

## Usage

### Parsing an EDI 835 File

```python
from py835 import Parser

# Initialize the parser with the path to your EDI file
edi_parser = Parser(file_path='path/to/your/file.835')

# Get line item transactions as a Pandas DataFrame with pretty column names
transactions_df = edi_parser.transactions(colnames=True)

# Display the DataFrame
print(transactions_df)
```

## Class Attributes

The `Parser` class extracts data from the EDI 835 file and stores it in several class attributes for easy access and manipulation. Below is a breakdown of the key attributes:

### `self.isa`
- **Type:** Dictionary
- **Description:** Stores data from the `ISA` (Interchange Control Header) segment, which includes general information such as sender/receiver IDs and interchange control numbers.

### `self.functional_groups`
- **Type:** List of dictionaries
- **Description:** Contains data from `GS` (Functional Group Header) segments. Each dictionary represents one functional group and includes details such as functional group control numbers.

### `self.transaction_sets`
- **Type:** List of dictionaries
- **Description:** Contains data from `ST` (Transaction Set Header) segments. Each dictionary represents a transaction set, storing details like transaction set control numbers and references.

### `self.transaction_refs`
- **Type:** List of dictionaries
- **Description:** Stores `REF` (Reference Identification) segment data related to transaction sets. It includes references such as EV and F2 for the transaction set.

### `self.claims`
- **Type:** List of dictionaries
- **Description:** Contains data from `CLP` (Claim Payment Information) segments. Each dictionary represents a claim, with details such as claim ID, claim status, total charge amount, and payment amount.

### `self.claims_refs`
- **Type:** List of dictionaries
- **Description:** Stores `REF` segment data related to claims. This includes claim-level references not directly included in the `CLP` segment (e.g., provider identifiers).

### `self.claims_cas`
- **Type:** List of dictionaries
- **Description:** Contains data from `CAS` (Claim Adjustment) segments, which represent claim-level adjustments. Each dictionary holds adjustment reason codes, group codes, and amounts for the claim.

### `self.services`
- **Type:** List of dictionaries
- **Description:** Contains data from `SVC` (Service Payment Information) segments, representing individual service-line items within a claim. Each dictionary stores service details such as service ID, billed amount, and allowed amount.

### `self.services_cas`
- **Type:** List of dictionaries
- **Description:** Contains data from `CAS` segments, representing service-line adjustments. Each dictionary holds adjustment codes, group codes, and amounts for the specific service.

### `self.colnames`
- **Type:** Dictionary
- **Description:** A mapping of the column names dynamically created from segment identifiers. This can be used to rename columns in the resulting DataFrame for better readability.

## File Structure

- `Parser`: Main class responsible for loading and parsing the EDI 835 file.
- `transactions()`: Method to extract parsed line item data into a Pandas DataFrame.
- `colnames`: Dictionary that holds dynamic column names based on the EDI segment.

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.