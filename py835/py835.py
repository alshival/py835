import pyx12
import pyx12.error_handler
import pyx12.x12context
import pyx12.params
import pandas as pd
from io import StringIO
import os
import json  # Add this for final JSON conversion
from . import codes

BASE_DIR = os.path.dirname(__file__)

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
        colnames = set()    
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
            
            #### ISA (Interchange Control Header)
            if seg_id == 'ISA':
                final_json['ISA'] = segment_data
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

            if seg_id == 'GS':
                # Start a new functional group
                current_functional_group = {
                    'FunctionalGroupData': segment_data,
                    'Statements': []
                }
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

            #### Start of a new Statement (ST)
            if seg_id == 'ST':
                # Store the previous statement and reset
                if current_statement:
                    current_functional_group['Statements'].append(current_statement)

                current_statement = {
                    'StatementData': segment_data,
                    'Claims': []
                }
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

            # Add BPR, TRN, REF, and DTM to the current statement
            if seg_id in ['BPR', 'TRN']:
                current_statement['StatementData'].update(segment_data)
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

            if seg_id == 'REF' and seg_data.get_value("REF01") == 'EV':
                current_statement['StatementData'].update(
                    {codes.REF01.get(seg_data.get_value("REF01"), "REF01" + seg_data.get_value("REF01"))+'-'+x: segment_data[x] for x in segment_data.keys()}
                )
                # Gather attributes:
                colnames = colnames.union(
                    set(
                        (codes.REF01.get(seg_data.get_value("REF01"),"REF01"+seg_data.get_value("REF01")) +'-'+child.id, child.name) 
                        for child in seg_node.children
                        ))

            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '405':
                current_statement['StatementData'].update(segment_data)
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

            if seg_id == 'N1':
                if seg_data.get_value("N101") == 'PR':
                    pe = False
                    current_statement['StatementData'].update(
                        {x + '-Payer': segment_data[x] for x in segment_data.keys()}
                    )
                    # Gather attributes:
                    colnames = colnames.union(set((child.id+'-Payer', child.name) for child in seg_node.children))
                elif seg_data.get_value("N101") == 'PE':
                    pe = True
                    current_statement['StatementData'].update(
                        {x + '-Payee': segment_data[x] for x in segment_data.keys()}
                    )
                    # Gather attributes:
                    colnames = colnames.union(set((child.id+'-Payee', child.name) for child in seg_node.children))

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

                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

            if seg_id == 'NM1':
                # Patient Info
                current_claim['ClaimData'].update(
                    {x + f'-{seg_data.get_value("NM101")}': segment_data[x] for x in segment_data.keys()}
                )
                # Gather attributes:
                colnames = colnames.union(set((child.id + f'-{seg_data.get_value("NM101")}', child.name) for child in seg_node.children))

            if seg_id == 'REF' and seg_data.get_value("REF01") in ['EA', '6P', '28', 'F8', 'CE', '1L']:
                current_claim['ClaimData'].update(
                    {codes.REF01.get(seg_data.get_value("REF01"), "REF01" + seg_data.get_value("REF01")): segment_data[x] for x in segment_data.keys()}
                )
                # Gather attributes:
                colnames = colnames.union(
                    set(
                        (codes.REF01.get(seg_data.get_value("REF01"),"REF01"+seg_data.get_value("REF01")) +'-'+child.id, child.name) 
                        for child in seg_node.children)
                    )

            if seg_id == 'DTM' and seg_data.get_value("DTM01") in ['232', '233', '050']:
                current_claim['ClaimData'].update(
                    {codes.DTM01.get(seg_data.get_value("DTM01"), "DTM01" + seg_data.get_value("DTM01") +'-'+x): segment_data[x] for x in segment_data.keys()}
                )
                # Gather attributes:
                colnames = colnames.union(
                    set(
                        (codes.DTM01.get(seg_data.get_value("DTM01"),"DTM01" + seg_data.get_value("DTM01"))+'-'+child.id,child.name)
                         for child in seg_node.children)
                    )


            #### Service (SVC)
            if seg_id == 'SVC':
                # Start a new service within the claim
                current_service = segment_data
                current_claim['Services'].append(current_service)
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

            # CAS (Claim and Service-Level Adjustments)
            if seg_id == 'CAS':
                if current_service is None:
                    # This is a claim-level CAS
                    new_insert = {f'CAS-{seg_data.get_value("CAS01")}-Claim-{x}': segment_data[x] for x in segment_data.keys()}
                    new_insert.update({
                            f'CAS-{seg_data.get_value("CAS01")}-Claim-CAS01-Description': codes.claim_adjustment_group_codes.get(seg_data.get_value("CAS01"),None)
                        })
                    
                    current_claim['ClaimData'].update(
                        new_insert
                    )
                    # Gather attributes:
                    colnames = colnames.union(set((f'CAS-{seg_data.get_value("CAS01")}-Claim-{child.id}', child.name) for child in seg_node.children))
                else:
                    # This is a service-level CAS
                    new_insert = {f'CAS-{seg_data.get_value("CAS01")}-Service-{x}': segment_data[x] for x in segment_data.keys()}
                    current_service.update(
                        new_insert
                    )
                    # Gather attributes:
                    colnames = colnames.union(set((f'CAS-{seg_data.get_value("CAS01")}-Service-{child.id}', child.name) for child in seg_node.children))

            # AMT (Monetary Amount)
            if seg_id == 'AMT':
                if current_service is None:
                    # This is a claim-level AMT
                    current_claim['ClaimData'].update(
                        {f'AMT-{seg_data.get_value("AMT01")}-Claim-'+x: segment_data[x] for x in segment_data.keys()}
                    )
                    # Gather attributes:
                    colnames = colnames.union(set((f'AMT-{seg_data.get_value("AMT01")}-Claim-'+child.id, child.name) for child in seg_node.children))
                else:
                    # This is a service-level AMT
                    current_service.update(
                        {f'AMT-{seg_data.get_value("AMT01")}-Service'+'-'+x: segment_data[x] for x in segment_data.keys()}
                    )
                    # Gather attributes:
                    colnames = colnames.union(set((f'AMT-{seg_data.get_value("AMT01")}-Service-'+child.id, child.name) for child in seg_node.children))

            # Handle DTM within SVC (Service Date)
            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '472':
                current_service.update(
                    {codes.DTM01.get(seg_data.get_value("DTM01"), "DTM" + seg_data.get_value("DTM01")): segment_data[x] for x in segment_data.keys()}
                )
                # Gather attributes:
                colnames = colnames.union(
                    set(
                        (codes.DTM01.get(seg_data.get_value("DTM01"),"DTM01" + seg_data.get_value("DTM01"))+'-'+child.id,child.name)
                         for child in seg_node.children)
                    )

            #### End of Claim
            if seg_id == 'SE':
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))
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
                current_functional_group['FunctionalGroupData'].update(segment_data)
                
                # Gather attributes:
                colnames = colnames.union(set((child.id, child.name) for child in seg_node.children))

                functional_groups.append(current_functional_group)
                current_functional_group = None

        # Add the last functional group
        final_json['FunctionalGroups'] = functional_groups

        # Store the parsed JSON structure
        self.json = final_json
        # Store the attributes (Column names)
        self.colnames = {x:f'{x} {dict(colnames)[x]}' for x in dict(colnames).keys()}
        self.colnames = {key: self.colnames[key] for key in sorted(self.colnames)}

    def generate_ISA_table(self,colnames=False):
        isa_data = self.json.get('ISA',{})
        isa_df = pd.DataFrame([isa_data])
        isa_df['ISA_ID'] = isa_df['ISA13']
        isa_df['file'] = self.file_path
        if colnames:
            isa_df = isa_df.rename(self.colnames,axis=1)
        return isa_df
    
    def generate_functional_group_table(self,colnames=False):
        functional_groups = self.json.get('FunctionalGroups', [])
        
        # Flatten each functional group data and include the ISA_ID
        fg_data = []
        isa_id = self.json['ISA'].get('ISA13')
        
        for fg in functional_groups:
            fg_record = fg['FunctionalGroupData']
            fg_record['ISA_ID'] = isa_id  # Link to ISA table
            fg_data.append(fg_record)
        
        fg_df = pd.DataFrame(fg_data)
        if colnames:
            fg_df = fg_df.rename(self.colnames,axis=1)
        return fg_df
    
    def generate_statement_table(self,colnames=False):
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
        if colnames:
            statements_df = statements_df.rename(self.colnames,axis=1)
        # Handle codes
        return statements_df
    
    def generate_claim_table(self,colnames=False):
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
        if colnames:
            claims_df = claims_df.rename(self.colnames,axis=1)
        return claims_df
    def generate_service_table(self,colnames=False):
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

        # # Handle codes
        # encoded_col = 'CAS-CO-Service-CAS01'
        # translations = services_df[encoded_col].apply(lambda x: codes.claim_adjustment_group_codes.get(x,x))
        # loc = services_df.columns.get_loc(encoded_col)+1
        # services_df.insert(loc = loc, column=encoded_col+'-description',value = translations)
        # encoded_col = 'CAS-P-Service-CAS01'
        # translations = services_df[encoded_col].apply(lambda x: codes.claim_adjustment_group_codes.get(x,x))
        # loc = services_df.columns.get_loc(encoded_col)+1
        # services_df.insert(loc = loc, column=encoded_col+'-description',value = translations)

        if colnames:
            services_df = services_df.rename(self.colnames,axis=1)
        return services_df
    
    def transactions(self,colnames=False):
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

        if colnames:
            full_transactions = full_transactions.rename(self.colnames,axis=1)
        # Return the final merged DataFrame
        return full_transactions
