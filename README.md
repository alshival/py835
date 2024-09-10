<img src="DHR-Health-Logo.png" width="50%">



# py835 
**Python Package for Parsing 835 EDI Files**

`py835` is a Python package developed by DHR Health for parsing healthcare 835 EDI files. The package is built on top of the `pyx12` library and provides an easy-to-use function to parse EDI 835 files into structured data, which can be output in JSON format for further analysis or integration into other systems.

#### Key Features:
- **835 EDI File Parsing**: Automatically reads and parses 835 EDI files, which contain detailed information about healthcare payments and remittance advice.
- **Structured Output**: Each segment of the EDI file is broken down into its constituent elements, with segment IDs, element names, and values organized into a JSON-friendly format.
- **Error Handling**: Built-in error handling for parsing issues, leveraging `pyx12`'s robust error reporting.

#### How It Works:
- The package uses the `pyx12` library to handle the low-level parsing of EDI files.
- It iterates through each segment of the 835 file and extracts data, including segment IDs, element names, and values, organizing them into a structured format.
- The parsed output is returned as a Python list of dictionaries, each representing a segment with its elements, ready to be serialized into JSON or processed further.

#### Benefits:
- Simplifies the process of extracting and interpreting payment data from 835 files, enabling easier integration into your healthcare system workflows.
- Provides a clear and structured representation of complex EDI files, making it easier for developers and data teams to analyze remittance advice data.

## Installation
To install `py835`, run 
```
pip install git+https://github.com/DHR-Health/py835.git
```

## Usage 

The `py835.parse()` function reads an 835 EDI file and returns a detailed, structured representation of the file in JSON format. Each dictionary represents a segment of the EDI file and contains metadata about the segment along with its individual elements.

### Example Usage
```
import py835

# Parse an 835 file
result = py835.parse('path/to/your/file.835')
```

### Example Output
The output is a dictionary where the keys are Patient Control Numbers, and the values are lists of segments related to that patient.
```
{
    "R7836647": [
        {
            "segment_id": "CLP",
            "segment_name": "Claim Payment Information",
            "elements": [
                {"element_index": 1, "element_name": "Patient Control Number", "element_value": "R7836647"},
                {"element_index": 2, "element_name": "Claim Status Code", "element_value": "4"},
                {"element_index": 3, "element_name": "Total Claim Charge Amount", "element_value": "39.16"},
                ...
            ]
        },
        {
            "segment_id": "NM1",
            "segment_name": "Patient Name",
            "elements": [
                {"element_index": 1, "element_name": "Entity Identifier Code", "element_value": "QC"},
                {"element_index": 2, "element_name": "Patient Last Name", "element_value": "LOZANO MONTALVO"},
                ...
            ]
        },
        ...
    ],
    "R9876543": [
        // Segments for another patient
    ]
}

```