import csv
import os 

BASE_DIR = os.path.dirname(__file__)

def import_csv_to_dict(file_path):
    """Import a CSV file and return a dictionary."""
    data_dict = {}

    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data_dict[row['Code']] = row['Description']

    return data_dict

# Example usage:
# file_path = 'your_file.csv'
# result_dict = import_csv_to_dict(file_path)
# print(result_dict)

##########################################################################################
# Codes
##########################################################################################
DTM01 = {
    '036': 'Coverage Expiration',
    '050': 'Received',
    '150': 'Service Period Start',
    '151': 'Service Period End',
    '232': 'Claim Statement Period Start',
    '233': 'Claim Statement Period End',
    '405': 'Production',
    '472': 'Service Period'
}


# Pulled some of these from here: 
# https://aging.ohio.gov/wps/wcm/connect/gov/bee80467-6343-48cc-8d2a-fedfbe4fc185/ODA835-5010.pdf?MOD=AJPERES&CONVERT_TO=url&CACHEID=ROOTWORKSPACE.Z18_K9I401S01H7F40QBNJU3SO1F56-bee80467-6343-48cc-8d2a-fedfbe4fc185-newl.nS
REF01 = {
    '0B': 'State License Number',
    '0K': 'Policy Form Identifying Number',
    '1A': 'Blue Cross Provider Number',
    '1B': 'Blue Shield Provider Number',
    '1C': 'Medicare Provider Number',
    '1D': 'Medicaid Provider Number',
    '1G': 'Provider UPIN Number',
    '1H': 'CHAMPUS Identification Number',
    '1J': 'Facility ID Number',
    '1L': 'Group or Policy Number',
    '1S': 'Ambulatory Patient Group Number',
    '1W': 'Member Identification Number',
    '28': 'Employee Identification Number',
    '2U': 'Payer Identification Number',
    '6P': 'Group Number',
    '6R': 'Provider Control Number',
    '9A': 'Repriced Claim Reference Number',
    '9C': 'Adjusted Repriced Claim Reference Number',
    'APC': 'Ambulatory Payment Classification',
    'BB': 'Authorization Number',
    'CE': 'Class of Contract Code',
    'D3': 'National Council for Prescription Drug Programs Pharmacy Number',
    'E9': 'Attachment Code',
    'EA': 'Medical Record Identification Number',
    'EO': 'Submitter Identification Number',
    'EV': 'Production',
    'F2': 'Version Code',
    'F8': 'Original Reference Number',
    'G1': 'Prior Authorization Number',
    'G2': 'Provider Commercial Number',
    'G3': 'Predetermination of Benefits Identification Number',
    'HPI': 'Centers for Medicare and Medicaid Services National Provider Identifier',
    'IG': 'Insurance Policy Number',
    'LU': 'Location Number',
    'NF': 'National Association of Insurance Commissioners Code',
    'PQ': 'Payee Identification',
    'RB': 'Rate code number',
    'SY': 'Social Security Number',
    'TJ': 'Federal Taxpayer\'s Identification Number'
}

cas_descriptions = {
    "CAS01": {
        "CO": "Contractual Obligations",
        "CR": "Correction and Reversals",
        "OA": "Other Adjustments",
        "PI": "Payer Initiated Reductions",
        "PR": "Patient Responsibility"
    },
    "CAS02": "Adjustment Reason Code",
    "CAS03": "Adjustment Amount",
    "CAS04": "Quantity",
    "CAS05": "Reserved",
    "CAS06": "Reserved",
    "CAS07": "Reserved",
    "CAS08": "Reserved",
    "CAS09": "Reserved",
    "CAS10": "Reserved",
    "CAS11": "Reserved",
    "CAS12": "Reserved",
    "CAS13": "Reserved",
    "CAS14": "Reserved",
    "CAS15": "Reserved",
    "CAS16": "Reserved",
    "CAS17": "Reserved",
    "CAS18": "Reserved",
    "CAS19": "Reserved"
}

ref_descriptions = {
    "REF01": {
        "EV": "Enrollment Verification Number",
        "F2": "Provider Commercial Number",
        "2U": "Payer Identification Number",
        "TJ": "Federal Taxpayer’s Identification Number",
        "1L": "Group or Policy Number",
        "EA": "Medical Record Identification Number",
        "CE": "Class of Contract Code",
        "F8": "Original Reference Number",
        "IG": "Insurance Policy Number",
        "SY": "Social Security Number",
        "XZ": "Medicaid Provider Number",
        "D9": "Claim Number",
        "G1": "Prior Authorization Number",
        # Add more REF01 codes
    },
    "REF02": "Reference Identification",
    "REF03": "Additional Reference Information",
    "REF04": "Reserved"
}



claim_adjustment_group_codes = import_csv_to_dict(os.path.join(BASE_DIR,'codes','claim_adjustment_group_codes.csv'))

claim_adjustment_reason_codes = import_csv_to_dict(os.path.join(BASE_DIR,'codes','claim_adjustment_reason_codes.csv'))

