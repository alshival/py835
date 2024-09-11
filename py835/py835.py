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


##########################################################################################
# Codes
##########################################################################################
dtm_codes = {
    '405': 'Production',
    '036': 'Coverage',
    '232': 'Statement',
    '233': 'Statement',
    '050': 'Claim Received',
    '150':'Service Date',
    '151': 'Service Date',
    '472': 'Service Date'
}
ref_codes = {
    'EV': "Payer Identification",
    'F2': "Version",
    'LU': "Service",
    '1S': 'Service',
    'APC': 'Service',
    'RB': 'Service',
    'PQ': 'Payee Identification',
    'HPI': 'Provider',
    'SY': 'Provider',
    'TJ': 'Provider',
    '1C': 'Provider',
    '1G': 'Provider',
    '0K': 'Policy',
    '1L': 'Other',
    '1W': 'Other',
    'F8': 'Other',
    'IG': 'Other'
}

##########################################################################################
# Parser
##########################################################################################

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
            # Standard
            attributes_dict = attributes_dict.union(set((child.id, child.name) for child in seg_node.children if seg.id not in ['REF','N1','NM1','DTM']))
            # Flagged
            attributes_dict = attributes_dict.union(set((child.id + str(seg.seg_data.get_value(seg.id+"01")), child.name) for child in seg_node.children if seg.id in ['REF','N1','NM1']))
            # Dates
            attributes_dict = attributes_dict.union(
                set(
                    ( child.id + str(dtm_codes[seg.seg_data.get_value(seg.id+"01")]), child.name ) 
                    for child in seg_node.children if seg.id == 'DTM'))
        self.attrs = dict(attributes_dict)

    def transactions(self, column_names=False):
        # Extract transaction data from the context reader
        flattened_data = []
        global_info = {}
        
        # Initialize containers for transactions, claims, and service lines
        current_transaction = None
        current_claim = None
        current_se = None
        current_cas = None
        claims = []
        current_service_line = None

        # Rewind the context_reader
        self.load_context()

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

            # Handle global info (ISA level)
            if seg_id == "ISA":
                global_info.update(segment_data)
            if seg_id == "DTM":
                # Global date
                date_data = dict(zip([i + dtm_codes[seg_data.get_value("DTM01")] for i in segment_data.keys()], segment_data.values()))
                if seg_data.get_value("DTM01") == "405":
                    global_info.update(date_data)
                if seg_data.get_value("DTM01") == "036":
                    current_transaction.update(date_data)
                if seg_data.get_value("DTM01") in ["232", "233", "050", "150", "151", "472"]:
                    current_claim.update(date_data)
            if seg_id == "REF":
                if seg_data.get_value("REF01") in ["EV", "PQ"]:
                    global_info.update(
                        dict(zip([i + seg_data.get_value("REF01") for i in segment_data.keys()], segment_data.values()))
                    )
                if seg_data.get_value("REF01") in ["0K"]:
                    current_claim.update(
                        dict(zip([i + seg_data.get_value("REF01") for i in segment_data.keys()], segment_data.values()))
                    )
            # Handle transaction-level data (ST-SE)
            if seg_id == "GS":
                current_transaction = {
                    **global_info,
                    **segment_data
                }
            if seg_id == "ST":
                current_transaction.update(segment_data)
            if seg_id == "BPR":
                current_transaction.update(segment_data)

            # Start a new claim
            if seg_id == "CLP":
                current_claim = {**segment_data}
                current_service_line = None  # Reset current service line at new claim level
            elif seg_id == "NM1":
                current_claim.update(
                    dict(zip([i + seg_data.get_value("NM101") for i in segment_data.keys()], segment_data.values()))
                )
            elif seg_id == "CAS":
                if current_service_line is not None:
                    current_service_line.update({x+'service':segment_data[x] for x in segment_data.keys()})
                else:
                    current_claim.update({x+'claim':segment_data[x] for x in segment_data.keys()})
            elif seg_id == "SVC":
                # Start a new service line within the claim
                current_service_line = {**segment_data}
                claims.append({
                    **current_claim,        # Include all claim-level data
                    **current_service_line  # Include all service line (SVC) data
                })
            elif seg_id == "SE":
                # Store SE segment information
                current_se = {**segment_data}

                # Attach SE info to each claim and append to flattened_data
                for claim in claims:
                    flattened_data.append({
                        **current_transaction,  # Include all transaction-level data
                        **claim,                # Include claim and service line data
                        **current_se            # Attach SE info to each claim
                    })

                # Clear claims and reset current_transaction for the next iteration
                claims = []
                current_transaction = None
                current_claim = None
                current_se = None
                current_cas = None
                current_service_line = None

        # Create the DataFrame from the flattened data
        df = pd.DataFrame(flattened_data)

        # If column_names is True, replace the column names using the attributes dictionary
        if column_names:
            df = df.rename(columns=lambda col: col + ' - ' + self.attrs.get(col, col))

        return df
