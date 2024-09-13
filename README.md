<img src="DHR-Health-Logo.png" width="50%">

# py835

The **py835** Python package provides a robust toolset for parsing EDI 835 files using the `pyx12` library. It processes healthcare claim information from EDI 835 files into structured formats like Pandas DataFrames and JSON for seamless data manipulation, reporting, and analysis.

Note that this project is still very much in the early stages. If you require a stable version, please fork this Github repository.

## Features

- **Parse EDI 835 Files:** Load and process `.835` EDI files for healthcare claims and payment information.
- **Extract Data:** Extracts detailed information, including functional groups, transaction sets, claims, services, adjustments, and references.
- **DataFrame Output:** Organizes parsed data into Pandas DataFrames for more convenient analysis.
- **Column Renaming:** Automatically renames columns based on EDI segment codes and descriptions for better readability.
- **Pivot Tables:** Supports pivoting data (e.g., CAS and REF segments) for deeper analysis.
- **JSON Export:** Supports exporting parsed data to JSON format for further use in other systems.

## Installation

To install this package, run the following command:

```bash
pip install git+https://github.com/DHR-Health/py835.git
```

### Dependencies

- `pyx12`: Python library for EDI file parsing.
- `pandas`: Used for organizing parsed data into DataFrames.
- `io`: Standard Python module for handling input/output operations.
- `json`: Used for exporting data to JSON format.

## Usage

### Parsing an EDI 835 File

```python
from py835 import Parser

# Initialize the parser with the path to your EDI file
edi_parser = Parser(file_path='path/to/your/file.835')
```

The parser systematically breaks down the 835 data into hierarchical layers, reflecting the structure of the EDI 835 file:

<img src="https://github.com/DHR-Health/py835/blob/main/835%20Structure.png">

1. **ISA (Interchange Control Header):**  
   The top-level layer is the `ISA` segment, which contains metadata about the interchange, such as sender/receiver information, control numbers, and transaction timestamps. This segment serves as a unique identifier for the file. You can retrieve the ISA header data as JSON using `edi_parser.isa` and as a Pandas DataFrame via `edi_parser.isa_table()`. This allows for easy analysis of interchange metadata, including file-level information.

2. **Functional Groups (GS):**  
   Within each `ISA` segment, there are one or more `GS` (Functional Group Header) segments. Functional groups organize related transaction sets under a specific purpose or business function, such as claims, remittance advice, or payment acknowledgments. You can retrieve information about the functional groups in JSON format using `edi_parser.functional_groups`, or as a Pandas DataFrame using `edi_parser.functional_groups_table()`. The functional groups table can be joined with the ISA table on the `'isa_id'` column for comprehensive data analysis across files.

3. **Statements (ST):**  
   Inside each functional group, `ST` segments define statements, also known as transaction sets. Each transaction set corresponds to a statement, bundling related claims, payments, or service details. One 835 file can have multiple transaction sets, which serve as logical groups for payment and claim details. You can extract transaction set information as JSON using `edi_parser.transaction_sets` and as a Pandas DataFrame via `edi_parser.transaction_sets_table()`. Transaction set data can be joined with the functional group data using the composite key `['isa_id', 'functional_group_id']`.

   * **TO DO:** Rename `edi_parser.transaction_sets` to `edi_parser.statements`.

4. **Claims (CLP):**  
   Each transaction set breaks down further into individual claims (`CLP` segments). Claims represent billing information for healthcare services rendered, including important details such as claim IDs, patient identifiers, the total amount billed, adjustments, payments made, and any denials or rejections. You can retrieve claim information as JSON using `edi_parser.claims` and as a Pandas DataFrame using `edi_parser.claims_table()`. Claims can be joined to transaction set data using the composite key `['isa_id', 'functional_group_id', 'statement_id']`.

    4a. **Claim Adjustments (CAS):**  
       Claims often have adjustments (`CAS` segments), which represent reductions or additions to the claim amount based on specific reasons like contractual obligations, patient responsibility, or denials. The parser extracts all adjustments, grouping them by claim, and allows you to retrieve this data in JSON or as a DataFrame via `edi_parser.claims_cas_table(flatten=True)`.

    4b. **Claim References (REF):**  
       The parser captures `REF` (Reference Identification) segments, which contain additional reference information related to claims. These may include provider identification numbers, patient account numbers, or other important reference codes. You can access reference data as JSON using `edi_parser.claims_refs` or as a Pandas DataFrame via `edi_parser.claims_refs_table()`. Each claim can have multiple references, so the parser supports flattening the references for easier joining: `edi_parser.claims_refs_table(flatten=True)`.

5. **Service Line Items (SVC):**  
   Within each claim, service line items (`SVC` segments) detail individual healthcare services or procedures performed during the treatment. The line item data includes service codes, charges, allowed amounts, and any related adjustments. You can extract service line data as JSON using `edi_parser.services` and as a Pandas DataFrame using `edi_parser.services_table()`. These can be linked to the claims table using the composite key `['isa_id', 'functional_group_id', 'statement_id', 'claim_id']`.

    5a. **Service Adjustments (CAS):**  
       Services often have adjustments (`CAS` segments), which represent reductions or additions to the service amount based on specific reasons like contractual obligations, patient responsibility, or denials. The parser extracts all adjustments, grouping them by service level, and allows you to retrieve this data in JSON or as a DataFrame via `edi_parser.services_cas_table(flatten=True)`.

    5b. **Service References (REF):**  
       The parser captures `REF` (Reference Identification) segments, which contain additional reference information related to each service within a claim. These may include provider identification numbers, patient account numbers, or other important reference codes. You can access reference data as JSON using `edi_parser.services_refs` or as a Pandas DataFrame via `edi_parser.services_refs_table()`. Each service can have multiple references, and the parser supports flattening the references for easier joining: `edi_parser.services_refs_table(flatten=True)`.

The parser ensures that all segments (ISA, GS, ST, CLP, SVC) are organized in a structured, hierarchical format for easy access and analysis. It also captures important references and adjustments at various levels using `REF` and `CAS` segments, further enhancing the breakdown of claims and services.

## Quick Export Transactions

The `.transactions` method in the `Parser` class is responsible for generating a consolidated DataFrame that includes the basic line items from the 835 file, specifically focusing on claims and service line data, **without** including adjustment (`CAS` segments) or reference (`REF` segments) information.

```python
from py835 import Parser

# Initialize the parser with the path to your EDI file
edi_parser = Parser(file_path='path/to/your/file.835')

# Get line item transactions as a Pandas DataFrame with descriptive column names
transactions_df = edi_parser.transactions(colnames=True)

# Display the DataFrame
print(transactions_df)
```

If you wish to include claim/service CAS or REF data, you can join the relevant Pandas DataFrames. Below is an example of merging service-level reference data (`REF` segments) with the basic transactions:

```python
from py835 import Parser

# Initialize the parser with the path to your EDI file
edi_parser = Parser(file_path='path/to/your/file.835')

# Get line item transactions as a Pandas DataFrame with descriptive column names
transactions_df = edi_parser.transactions(colnames=True)

# Include service-level REF data by flattening the references
services_refs = edi_parser.services_refs_table(flatten=True)

# Merge the transactions with service-level REF data
merged_df = transactions_df.merge(services_refs, on=['isa_id', 'functional_group_id', 'statement_id', 'claim_id', 'service_id'], how='left')

# Display the merged DataFrame
print(merged_df)
```

This example demonstrates how to include additional reference information for services by merging the basic transactions DataFrame with the service-level REF data. You can similarly merge other data, such as claim-level CAS (adjustments) or references, by adjusting the join conditions.

### Accessing Different Data Views

- **ISA Table:** Extract information from the `ISA` (Interchange Control Header) segment.
  ```python
  isa_df = edi_parser.isa_table(colnames=True)
  ```

- **Claims Table:** Get claims data extracted from `CLP` segments.
  ```python
  claims_df = edi_parser.claims_table(colnames=True)
  ```

- **Services Table:** Get service-level information from `SVC` segments.
  ```python
  services_df = edi_parser.services_table(colnames=True)
  ```

- **Claims CAS Table:** Get claim adjustment information from `CAS` segments.
  ```python
  claims_cas_df = edi_parser.claims_cas_table(colnames=True, flatten=True)
  ```

- **Service Referrals Table:** Extract references related to services (e.g., REF segments).
  ```python
  service_refs_df = edi_parser.services_refs_table(colnames=True, flatten=True)
  ```

### JSON Export

To export parsed data to JSON format:

```python
json_data = transactions_df.to_json(orient='records')
```

### Class Attributes

- `self.isa`: Extracts and stores data from the `ISA` segment.
- `self.functional_groups`: Contains data from `GS` segments (Functional Group Header).
- `self.transaction_sets`: Stores transaction-level information from `ST` segments.
- `self.claims`: Contains detailed claims data from `CLP` segments.
- `self.services`: Contains service-level information from `SVC` segments.
- `self.colnames`: Maps dynamic column names based on EDI segments for better readability.

## File Structure

- `Parser`: Main class responsible for loading, parsing, and organizing the EDI 835 file data.
- `transactions()`: Returns a DataFrame containing all transaction data, including claims and services.
- **Pivoting Capabilities:** Methods like `claims_refs_table()` and `services_refs_table()` allow for flexible pivoting and flattening of data.

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues.

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/my-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
