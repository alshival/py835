import pyx12
import pyx12.error_handler
import pyx12.x12context
import pyx12.params
import pandas as pd
from io import StringIO
import os 

# Get the absolute path to the 'codes' directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CODES_DIR = os.path.join(BASE_DIR, 'codes')

class EDI835Parser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_content = self.load_file_content()
        self.load_context()
        self.attributes()

    def load_file_content(self):
        # Load the entire file content into memory
        with open(self.file_path, 'r') as edi_file:
            return edi_file.read()

    def load_context(self):
        # Initialize X12 parsing context and create context reader from in-memory file content
        params = pyx12.params.params()
        errh = pyx12.error_handler.errh_null()

        # Use StringIO to simulate a file object from the string content
        edi_file_stream = StringIO(self.file_content)
        self.context_reader = pyx12.x12context.X12ContextReader(params, errh, edi_file_stream)

    def patients(self):
        # Extract patient data from the context reader
        patient_data = []
        current_patient_control_number = None

        # Rewind the context_reader
        self.load_context()

        # Iterate through segments to extract patient information
        for seg in self.context_reader.iter_segments():
            seg_node = seg.x12_map_node
            seg_data = seg.seg_data
            seg_id = seg_node.id

            # Check if it's a CLP segment (patient financial information)
            if seg_id == "CLP":
                current_patient_control_number = seg_data.get_value("CLP01")
                patient_info = {
                    "Patient Control Number": current_patient_control_number
                }

            # If it's an NM1 segment with QC qualifier (patient name)
            if seg_id == "NM1" and seg_data.get_value("NM101") == "QC":
                patient_name = {
                    "Patient Last Name": seg_data.get_value("NM103"),
                    "Patient First Name": seg_data.get_value("NM104")
                }
                patient_info.update(patient_name)

                # Append patient data when both CLP and NM1 (with QC) are found
                if current_patient_control_number:
                    patient_data.append(patient_info)

        return pd.DataFrame(patient_data)
    
    def attributes(self):
        attributes_dict = set()
        for seg in self.context_reader.iter_segments():
            seg_node = seg.x12_map_node
            # Collect attributes for analysis (optional)
            attributes_dict = attributes_dict.union(set((child.id, child.name) for child in seg_node.children))
        self.attrs = dict(attributes_dict)

    def transactions(self,column_names=False):
        # Extract transaction data from the context reader
        transactions_data = []
        current_patient_control_number = None
        current_clp_segment = None

        # Rewind the context_reader
        self.load_context()


        # Initialize a list to hold the flattened data for the DataFrame
        flattened_data = []

        # Initialize containers for transactions, claims, and service lines
        current_transaction = None
        current_claim = None

        for seg in self.context_reader.iter_segments():
            seg_node = seg.x12_map_node
            seg_data = seg.seg_data
            seg_id = seg_node.id

            # Create a dictionary for the current segment's data using dynamic IDs from segment children
            segment_data = dict(
                zip(
                    [child.id for child in seg_node.children],
                    [seg_data.get_value(child.id) for child in seg_node.children]
                )
            )

            # Handle transaction-level data (ST-SE)
            if seg_id == "ST":
                # Start a new transaction, initialize claims list
                current_transaction = {
                    **segment_data,  # Include all dynamic IDs and values from ST segment
                    "Payer Information": {},
                    "Payee Information": {}
                }

            elif seg_id == "CLP":
                # Start a new claim, initialize service lines list
                current_claim = {
                    **segment_data,  # Include all dynamic IDs and values from CLP segment
                    "Service Lines": []  # Initialize empty list for service lines
                }

            elif seg_id == "SVC":
                # Create a flattened entry by combining data from the transaction, claim, and service line
                service_line_entry = {
                    **current_transaction,  # Include all transaction-level data
                    **current_claim,        # Include all claim-level data
                    **segment_data          # Include all service line (SVC) data
                }

                # Append this flattened service line entry to the list for DataFrame creation
                flattened_data.append(service_line_entry)

            elif seg_id == "NM1":
                # Capture patient information when NM101 (entity identifier code) is "QC" (indicating the patient)
                if segment_data.get("NM101") == "QC":
                    current_claim.update({
                        "Patient Last Name": segment_data.get("NM103"),
                        "Patient First Name": segment_data.get("NM104"),
                        "Patient Middle Name": segment_data.get("NM105"),
                        "Patient Name Suffix": segment_data.get("NM107")
                    })
                # Optionally, capture provider information when NM101 == "82" (provider)
                elif segment_data.get("NM101") == "82":
                    current_claim.update({
                        "Provider Last Name": segment_data.get("NM103"),
                        "Provider First Name": segment_data.get("NM104"),
                        "Provider Identifier": segment_data.get("NM109")
                    })

            elif seg_id == "N1":
                # Capture payer or payee information
                if segment_data.get("N101") == "PR":  # Payer information
                    current_transaction["Payer Information"] = {
                        "Payer Name": segment_data.get("N102"),
                        "Payer Identifier": segment_data.get("N104")
                    }
                elif segment_data.get("N101") == "PE":  # Payee information
                    current_transaction["Payee Information"] = {
                        "Payee Name": segment_data.get("N102"),
                        "Payee Identifier": segment_data.get("N104")
                    }

            elif seg_id == 'PER':
                # Check if contact info should belong to the payer or payee
                if current_transaction["Payer Information"]:
                    current_transaction["Payer Information"].update(segment_data)
                elif current_transaction["Payee Information"]:
                    current_transaction["Payee Information"].update(segment_data)
        # Create the DataFrame from the flattened data
        df = pd.DataFrame(flattened_data)

        # If column_names is True, replace the column names using the attributes dictionary
        if column_names:
            df = df.rename(columns=lambda col: self.attrs.get(col, col))

        return df
