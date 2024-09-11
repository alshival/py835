import pyx12
import pyx12.error_handler
import pyx12.x12context
import pyx12.params
import pandas as pd
from io import StringIO
import os
import json  # Add this for final JSON conversion

##########################################################################################
# Codes
##########################################################################################
dtm_codes = {
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
ref_codes = {
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


class EDI835Parser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_content = self.load_file_content()
        self.load_context()
        self.parse()

    def load_file_content(self):
        with open(self.file_path, 'r') as edi_file:
            return edi_file.read()

    def load_context(self):
        params = pyx12.params.params()
        errh = pyx12.error_handler.errh_null()
        edi_file_stream = StringIO(self.file_content)
        self.context_reader = pyx12.x12context.X12ContextReader(params, errh, edi_file_stream)

    def parse(self):
        self.load_context()

        # Final JSON structure to be returned
        final_json = {
            'ISA': {},
            'FunctionalGroups': []
        }

        current_statement = None
        current_claim = None
        current_service = None

        functional_groups = []
        statements = []
        claims = []
        services = []

        for seg in self.context_reader.iter_segments():
            seg_node = seg.x12_map_node
            seg_data = seg.seg_data
            seg_id = seg.id

            # Create a dictionary for the current segment's data using dynamic IDs from segment children
            segment_data = dict(
                zip(
                    [child.id for child in seg_node.children],
                    [seg_data.get_value(child.id).strip() if seg_data.get_value(child.id) is not None else None for child in seg_node.children]
                )
            )
            attributes = set()
            #### ISA (Interchange Control Header)
            if seg_id == 'ISA':
                final_json['ISA'] = segment_data

            if seg_id == 'GS':
                # Start a new functional group
                current_functional_group = {
                    'FunctionalGroupData': segment_data,
                    'Statements': []
                }
                functional_groups.append(current_functional_group)

            #### Start of a new Statement (ST)
            if seg_id == 'ST':
                # Store the previous statement and reset
                if current_statement:
                    current_functional_group['Statements'].append(current_statement)

                current_statement = {
                    'StatementData': segment_data,
                    'Claims': []
                }

            # Add BPR, TRN, REF, and DTM to the current statement
            if seg_id in ['BPR', 'TRN']:
                current_statement['StatementData'].update(segment_data)

            if seg_id == 'REF' and seg_data.get_value("REF01") == 'EV':
                current_statement['StatementData'].update(
                    {ref_codes.get(seg_data.get_value("REF01"), "REF01" + seg_data.get_value("REF01"))+'-'+x: segment_data[x] for x in segment_data.keys()}
                )

            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '405':
                current_statement['StatementData'].update(segment_data)

            if seg_id == 'N1':
                if seg_data.get_value("N101") == 'PR':
                    pe = False
                    current_statement['StatementData'].update(
                        {x + '-Payer': segment_data[x] for x in segment_data}
                    )
                elif seg_data.get_value("N101") == 'PE':
                    pe = True
                    current_statement['StatementData'].update(
                        {x + '-Payee': segment_data[x] for x in segment_data}
                    )

            #### Claim (CLP)
            if seg_id == 'CLP':
                # Add prior claim to the list if it exists
                if current_claim is not None:
                    current_statement['Claims'].append(current_claim)

                # Reset service-level context
                current_service = None

                # Create new claim using the segment data
                current_claim = {
                    'ClaimData': segment_data,
                    'Services': []
                }

            if seg_id == 'NM1':
                # Patient Info
                current_claim['ClaimData'].update(
                    {x + f'-{seg_data.get_value("NM101")}': segment_data[x] for x in segment_data.keys()}
                )

            if seg_id == 'REF' and seg_data.get_value("REF01") in ['EA', '6P', '28', 'F8', 'CE', '1L']:
                current_claim['ClaimData'].update(
                    {ref_codes.get(seg_data.get_value("REF01"), "REF01" + seg_data.get_value("REF01")): segment_data[x] for x in segment_data.keys()}
                )

            if seg_id == 'DTM' and seg_data.get_value("DTM01") in ['232', '233', '050']:
                current_claim['ClaimData'].update(
                    {dtm_codes.get(seg_data.get_value("DTM01"), "DTM01" + seg_data.get_value("DTM01")): segment_data[x] for x in segment_data.keys()}
                )

            #### Service (SVC)
            if seg_id == 'SVC':
                # Start a new service within the claim
                current_service = segment_data
                current_claim['Services'].append(current_service)

            # CAS (Claim and Service-Level Adjustments)
            if seg_id == 'CAS':
                if current_service is None:
                    # This is a claim-level CAS
                    current_claim['ClaimData'].update(
                        {f'CAS-{seg_data.get_value("CAS01")}-Claim': f'{seg_data.get_value("CAS02")} {seg_data.get_value("CAS03")}'}
                    )
                else:
                    # This is a service-level CAS
                    current_service.update(
                        {f'CAS-{seg_data.get_value("CAS01")}-Service': f'{seg_data.get_value("CAS02")} {seg_data.get_value("CAS03")}'}
                    )

            # AMT (Monetary Amount)
            if seg_id == 'AMT':
                if current_service is None:
                    # This is a claim-level AMT
                    current_claim['ClaimData'].update(
                        {f'AMT-{seg_data.get_value("AMT01")}-Claim': seg_data.get_value("AMT02")}
                    )
                else:
                    # This is a service-level AMT
                    current_service.update(
                        {f'AMT-{seg_data.get_value("AMT01")}-Service': seg_data.get_value("AMT02")}
                    )

            # Handle DTM within SVC (Service Date)
            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '472':
                current_service.update(
                    {dtm_codes.get(seg_data.get_value("DTM01"), "DTM" + seg_data.get_value("DTM01")): segment_data[x] for x in segment_data.keys()}
                )

            #### End of Claim
            if seg_id == 'SE':
                # Append the last service to the claim
                if current_service:
                    current_claim['Services'].append(current_service)

                # Append the last claim to the statement
                if current_claim:
                    current_statement['Claims'].append(current_claim)

                # Append the last statement to the functional group
                if current_statement:
                    current_functional_group['Statements'].append(current_statement)

                # Reset variables for the next iteration
                current_service = None
                current_claim = None
                current_statement = None

            #### End of Functional Group (GE)
            if seg_id == 'GE':
                functional_groups.append(current_functional_group)
                current_functional_group = None

        # Add the last functional group
        final_json['FunctionalGroups'] = functional_groups

        # Store the parsed JSON structure
        self.json = final_json

    def generate_ISA_table(self):
        isa_data = self.json.get('ISA',{})
        isa_df = pd.DataFrame([isa_data])
        isa_df['ISA_ID'] = isa_df['ISA13']
        isa_df['file'] = self.file_path

        return isa_df
    
    def generate_functional_group_table(self):
        functional_groups = self.json.get('FunctionalGroups', [])
        
        # Flatten each functional group data and include the ISA_ID
        fg_data = []
        isa_id = self.json['ISA'].get('ISA13')
        
        for fg in functional_groups:
            fg_record = fg['FunctionalGroupData']
            fg_record['ISA_ID'] = isa_id  # Link to ISA table
            fg_data.append(fg_record)
        
        fg_df = pd.DataFrame(fg_data)
        
        return fg_df
    
    def generate_statement_table(self):
        statements_data = []
        isa_id = self.json['ISA'].get('ISA13')
        
        for fg in self.json.get('FunctionalGroups', []):
            fg_id = fg['FunctionalGroupData'].get('GS06')  # Example of Functional Group Control Number
            
            for statement in fg.get('Statements', []):
                statement_record = statement['StatementData']
                statement_record['ISA_ID'] = isa_id
                statement_record['FunctionalGroup_ID'] = fg_id  # Link to Functional Group
                statements_data.append(statement_record)
        
        statements_df = pd.DataFrame(statements_data)
        
        return statements_df
    
    def generate_claim_table(self):
        claim_data = []
        isa_id = self.json['ISA'].get('ISA13')
        
        for fg in self.json.get('FunctionalGroups', []):
            fg_id = fg['FunctionalGroupData'].get('GS06')
            
            for statement in fg.get('Statements', []):
                statement_id = statement['StatementData'].get('ST02')  # Example of Transaction Set Control Number
                
                for claim in statement.get('Claims', []):
                    claim_record = claim['ClaimData']
                    claim_record['ISA_ID'] = isa_id
                    claim_record['FunctionalGroup_ID'] = fg_id
                    claim_record['Statement_ID'] = statement_id  # Link to Statement
                    claim_data.append(claim_record)
        
        claims_df = pd.DataFrame(claim_data)
        
        return claims_df
    def generate_service_table(self):
        service_data = []
        isa_id = self.json['ISA'].get('ISA13')
        
        for fg in self.json.get('FunctionalGroups', []):
            fg_id = fg['FunctionalGroupData'].get('GS06')
            
            for statement in fg.get('Statements', []):
                statement_id = statement['StatementData'].get('ST02')
                
                for claim in statement.get('Claims', []):
                    claim_id = claim['ClaimData'].get('CLP01')  # Example of Claim ID
                    
                    for service in claim.get('Services', []):
                        service_record = service
                        service_record['ISA_ID'] = isa_id
                        service_record['FunctionalGroup_ID'] = fg_id
                        service_record['Statement_ID'] = statement_id
                        service_record['Claim_ID'] = claim_id  # Link to Claim
                        service_data.append(service_record)
        
        services_df = pd.DataFrame(service_data)
        
        return services_df
    
    def transactions(self):
        # Generate individual tables
        isa_df = self.generate_ISA_table()
        fg_df = self.generate_functional_group_table()
        statements_df = self.generate_statement_table()
        claims_df = self.generate_claim_table()
        services_df = self.generate_service_table()

        # Perform SQL-like joins using pandas merge
        # Step 1: Join ISA with Functional Groups
        isa_fg = pd.merge(isa_df, fg_df, left_on='ISA_ID', right_on='ISA_ID', how='inner')

        # Step 2: Join Functional Groups with Statements
        isa_fg_statements = pd.merge(isa_fg, statements_df, left_on=['ISA_ID', 'GS06'], right_on=['ISA_ID', 'FunctionalGroup_ID'], how='inner')

        # Step 3: Join Statements with Claims
        isa_fg_statements_claims = pd.merge(isa_fg_statements, claims_df, left_on=['ISA_ID', 'GS06', 'ST02'], right_on=['ISA_ID', 'FunctionalGroup_ID', 'Statement_ID'], how='inner')

        # Step 4: Join Claims with Services (line items)
        full_transactions = pd.merge(isa_fg_statements_claims, services_df, left_on=['ISA_ID', 'GS06', 'ST02', 'CLP01'], right_on=['ISA_ID', 'FunctionalGroup_ID', 'Statement_ID', 'Claim_ID'], how='inner')

        # Return the final merged DataFrame
        return full_transactions
