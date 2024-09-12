import pyx12
import pyx12.error_handler
import pyx12.x12context
import pyx12.params
import pandas as pd
from io import StringIO
import os
import json  # Add this for final JSON conversion
from . import codes
import re 
import secrets
import string 

BASE_DIR = os.path.dirname(__file__)

def generate_custom_string():
    # Define the character set (letters and digits)
    characters = string.ascii_letters + string.digits

    # Generate 4 random segments with varying lengths
    segments = [
        ''.join(secrets.choice(characters) for _ in range(8)),
        ''.join(secrets.choice(characters) for _ in range(6)),
        ''.join(secrets.choice(characters) for _ in range(10)),
        ''.join(secrets.choice(characters) for _ in range(12))
    ]
    
    # Join the segments with dashes
    random_string = '-'.join(segments)
    
    return random_string
class Parser:
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
        statement_refs = []
        claims = []
        claim_refs = []
        claim_cass = []
        services = []
        service_refs = [] 
        service_cass = []
        colnames = set()
        ref_colnames = {}
        cas_colnames = {} 
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

            ##### Header
            if seg_id == 'ISA':
                isa_id = generate_custom_string()
                isa_data = {'isa_id':isa_id}
                isa_data.update(segment_data)
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
            ########## Start Functional Group
            if seg_id == 'GS':
                functional_group_id = generate_custom_string()
                current_functional_group = {'isa_id': isa_id,'functional_group_id': functional_group_id}
                current_functional_group.update(segment_data)
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
            #################### Start of a Transaction Set
            if seg_id == 'ST':

                statement_id = generate_custom_string()
                statement_base = {'isa_id': isa_id, 'functional_group_id': functional_group_id,'statement_id': statement_id}
                current_statement = statement_base.copy()
                current_statement.update(segment_data)
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
            if seg_id in ['BPR','TRN']:
                current_statement.update(segment_data)
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
            if seg_id == 'REF' and seg_data.get_value('REF01') == 'EV':
                statement_ref = statement_base.copy()
                statement_ref.update(segment_data)
                statement_refs.append(statement_ref)
                # Save column names to ref colnames
                ref_colnames.update({
                    seg_data.get_value("REF01"):{child.id: child.id +'-'+child.name for child in seg_node.children}
                })
            if seg_id == 'REF' and seg_data.get_value('REF01') == 'F2':
                statement_ref = statement_base.copy()
                statement_ref.update(segment_data)
                statement_refs.append(statement_ref)
                # Save column names
                # Save column names to ref colnames
                ref_colnames.update({
                    seg_data.get_value("REF01"):{child.id: child.id +'-'+child.name for child in seg_node.children}
                })
            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '405':
                current_statement.update(
                    {x+'-'+seg_data.get_value("DTM01"): segment_data[x] for x in segment_data.keys()}
                )
                # Save column names
                colnames = colnames.union(set((child.id+'-'+seg_data.get_value("DTM01"), child.id+'-'+seg_data.get_value("DTM01") + codes.DTM01.get(seg_data.get_value("DTM01"),child.id+'-'+child.name)) for child in seg_node.children))
            if seg_id == 'N1':
                current_statement.update(
                    {x + '-' + seg_data.get_value("N101"): segment_data[x] for x in segment_data.keys()}
                )
                # Save column names
                colnames = colnames.union(set((child.id+'-'+seg_data.get_value("N101"), child.id +'-'+seg_data.get_value("N101")+'-' + child.name) for child in seg_node.children))
            if seg_id == 'REF' and seg_data.get_value("REF01") in ['2U','TJ']:
                current_statement.update(
                    segment_data
                )
                # Save column names
                # Save column names to ref colnames
                ref_colnames.update({
                    seg_data.get_value("REF01"):{child.id: child.id +'-'+child.name for child in seg_node.children}
                })
            if seg_id == 'LX':
                current_statement.update(segment_data)
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
            ######################################## Start of a new claim
            if seg_id == 'CLP':

                if current_claim is not None:
                    claims.append(current_claim)
                
                # Reset service-level context
                current_service = None 

                # Claim base
                claim_id = generate_custom_string()
                claim_base = {'isa_id': isa_id, 'functional_group_id': functional_group_id,'statement_id': statement_id, 'claim_id': claim_id}
                current_claim = claim_base.copy()
                current_claim.update(segment_data)
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
            if seg_id == 'CAS' and seg_data.get_value("CAS01") in['CO','OA','PR']:
                claim_cas = claim_base.copy()
                claim_cas.update(segment_data)
                claim_cass.append(claim_cas)
                # Save column names to ref colnames
                cas_colnames.update({
                    seg_data.get_value("CAS01"):{child.id: child.id +'-'+child.name for child in seg_node.children}
                })
            if seg_id == 'NM1':
                current_claim.update(
                    {x+'-'+seg_data.get_value('NM101'): segment_data[x] for x in segment_data.keys()}
                )
                # Save column names
                colnames = colnames.union(set((child.id+'-'+seg_data.get_value("NM101"), child.id+'-'+seg_data.get_value('NM101') +'-'+ child.name) for child in seg_node.children))
            
            if seg_id == 'REF' and seg_data.get_value('REF01') not in  ['EV','F2']:
                if current_service is None:
                    if current_claim is not None:
                        claim_ref = claim_base.copy()
                        claim_ref.update(segment_data)
                        claim_refs.append(claim_ref)
                    else:
                        statement_ref = statement_base.copy()
                        statement_ref.update(segment_data)
                        statement_refs.append(statement_ref)
                # Save column names
                # Save column names to ref colnames
                ref_colnames.update({
                    seg_data.get_value("REF01"):{child.id: child.id +'-'+child.name for child in seg_node.children}
                })
            if seg_id == 'DTM' and seg_data.get_value("DTM01") in ['232', '233', '050']:
                current_claim.update(
                    {x+'-'+seg_data.get_value("DTM01"):segment_data[x] for x in segment_data.keys()}
                )
                # Save column names
                colnames = colnames.union(set((child.id+'-'+seg_data.get_value("DTM01"), child.id+'-'+seg_data.get_value("DTM01") + codes.DTM01.get(seg_data.get_value("DTM01"),child.id+'-'+child.name)) for child in seg_node.children))
            ################################################################################ Start a new service
            if seg_id == 'SVC':
                # Append the last service 
                if current_service:
                    services.append(current_service)
                service_id =  generate_custom_string()
                service_base = {'isa_id': isa_id, 'functional_group_id': functional_group_id,'statement_id': statement_id, 'claim_id': claim_id, 'service_id': service_id}
                current_service = service_base.copy()
                current_service.update(segment_data)
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
            if seg_id == 'CAS':
                if current_service is None:
                    # This is a claim-level CAS. 
                    claim_cas = claim_base.copy()
                    claim_cas.update(segment_data)
                    claim_cass.append(claim_cas)
                else:
                    service_cas = service_base.copy()
                    service_cas.update(segment_data)
                    service_cass.append(service_cas)
                # Save column names to ref colnames
                cas_colnames.update({
                    seg_data.get_value("CAS01"):{child.id: child.id +'-'+child.name for child in seg_node.children}
                })
            if seg_id == 'AMT':
                if current_service is None:
                    current_claim.update(
                        {x+'-Claim':segment_data[x] for x in segment_data.keys()}
                    )
                    # Save column names
                    colnames = colnames.union(set((child.id+'-Claim', child.id +'-Claim-'+ child.name) for child in seg_node.children))
                else:
                    current_service.update(
                        {x+'-Service':segment_data[x] for x in segment_data.keys()}
                    )
                    # Save column names
                    colnames = colnames.union(set((child.id+'-Service', child.id +'-Service-'+ child.name) for child in seg_node.children))
            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '472':
                current_service.update(
                    {x+'-'+seg_data.get_value("DTM01"):segment_data[x] for x in segment_data.keys()}
                )
                # Save column names
                colnames = colnames.union(set((child.id+'-'+seg_data.get_value("DTM01"), child.id+'-'+seg_data.get_value("DTM01") + codes.DTM01.get(seg_data.get_value("DTM01"),child.id+'-'+child.name)) for child in seg_node.children))

            if seg_id == 'REF' and seg_data.get_value('REF01') not in  ['EV','F2']:
                if current_service is not None:
                    service_ref = service_base.copy()
                    service_ref.update(segment_data)
                    service_refs.append(service_ref)
                # Save column names
                # Save column names to ref colnames
                ref_colnames.update({
                    seg_data.get_value("REF01"):{child.id: child.id +'-'+child.name for child in seg_node.children}
                })
            ######################################## End of Transaction Set
            if seg_id == 'SE':
                # Append the last service 
                if current_service:
                    services.append(current_service)
                # Append the last claim
                if current_claim:
                    claims.append(current_claim)
                # Append the last statement to the functional group
                if current_statement:
                    statements.append(current_statement)

                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))

                # Reset the variables
                current_service = None
                current_claim = None 
                current_statement = None
            ########## End Functional Group
            if seg_id == 'GE':
                current_functional_group.update(segment_data)
                functional_groups.append(current_functional_group)
                current_functional_group = None
                # Save column names
                colnames = colnames.union(set((child.id, child.id +'-'+ child.name) for child in seg_node.children))
        # Add to self. 
        self.isa = isa_data
        self.functional_groups = functional_groups 
        self.transaction_sets = statements 
        self.transaction_refs = statement_refs
        self.claims = claims 
        self.claims_refs = claim_refs
        self.claims_cas = claim_cass
        self.services = services 
        self.services_refs = service_refs
        self.services_cas = service_cass
        self.colnames = dict(colnames)
        self.ref_colnames = ref_colnames
        self.cas_colnames = cas_colnames

    def isa_table(self,colnames=False):
        isa_data = pd.DataFrame([self.isa])
        isa_data['filename'] = os.path.basename(self.file_path)
        if colnames:
            isa_data = isa_data.rename(self.colnames,axis = 1)
        return isa_data
    def functional_groups_table(self,colnames = False):
        functional_groups = pd.DataFrame(self.functional_groups)
        if colnames:
            functional_groups = functional_groups.rename(self.colnames,axis = 1)
        return functional_groups
    
    def transaction_sets_table(self,colnames=False):
        transaction_sets = pd.DataFrame(self.transaction_sets)
        if colnames:
            transaction_sets = transaction_sets.rename(self.colnames,axis = 1)
        return transaction_sets
    
    def claims_table(self,colnames=False):
        claims = pd.DataFrame(self.claims)
        if colnames:
            claims = claims.rename(self.colnames,axis=1)
        return claims 
    
    def services_table(self,colnames=False):
        services = pd.DataFrame(self.services)
        if colnames:
            services = services.rename(self.colnames,axis=1)
        return services

    def transactions(self,colnames=False):
        # Convert lists to DataFrames
        isa_data = self.isa_table()  
        functional_groups = self.functional_groups_table()
        transaction_sets = self.transaction_sets_table()
        claims = self.claims_table()
        services = self.services_table()

        # Join the DataFrames
        # 1. Join isa_data with functional_groups on 'isa_id'
        master_df = pd.merge(isa_data, functional_groups, on='isa_id', how='left')

        if not transaction_sets.empty:
            # 2. Join with transaction_sets on 'isa_id' and 'functional_group_id'
            master_df = pd.merge(master_df, transaction_sets, on=['isa_id', 'functional_group_id'], how='left')

        if not claims.empty:
            # 3. Join with claims on 'isa_id', 'functional_group_id', and 'statement_id'
            master_df = pd.merge(master_df, claims, on=['isa_id', 'functional_group_id', 'statement_id'], how='left')

        # 4. Join with services on 'isa_id', 'functional_group_id', 'statement_id', and 'claim_id'
        if not services.empty:
            master_df = pd.merge(master_df, services, on=['isa_id', 'functional_group_id', 'statement_id', 'claim_id'], how='left')

        if colnames:
            master_df = master_df.rename(self.colnames,axis=1)
        # Return the final master DataFrame
        return master_df
    
    def parse_refs_data(self, data, colnames=False, flatten=False):
        # Create DataFrame from the provided data
        refs = pd.DataFrame(data)
        if not refs.empty:
            # List of identifier columns
            id_vars = ['isa_id', 'functional_group_id', 'statement_id', 'claim_id']
            if 'service_id' in refs.columns:
                id_vars = ['isa_id', 'functional_group_id', 'statement_id', 'claim_id', 'service_id']

            # Pivot the table if flatten flag is True
            if flatten:
                # Pivot the DataFrame on REF01 and other REF columns (REF02, REF03, etc.)
                pivoted_refs = refs.pivot_table(
                    index=id_vars,
                    columns='REF01',  # Column to pivot on (e.g., '1L', 'EA', 'CE')
                    values=[col for col in refs.columns if col.startswith('REF') and col not in id_vars + ['REF01']],
                    aggfunc='first'  # Use 'first' to take the first non-null value for duplicates
                )

                # Flatten the MultiIndex columns if needed
                pivoted_refs.columns = [f'{col}_{val}' for col, val in pivoted_refs.columns]
                pivoted_refs = pivoted_refs.reset_index(drop=False)

                # Rename columns if `colnames=True`
                if colnames:
                    # Create a renaming dictionary
                    rename_dict = {
                        f'{col}_{val}': f'{col}_{val} {codes.ref_descriptions["REF01"].get(val, val)} - {codes.ref_descriptions.get(col, col)}'
                        for col, val in (x.split("_") for x in pivoted_refs.columns if re.search('.*REF.*', x))
                    }

                    # Rename the columns using the created dictionary
                    pivoted_refs = pivoted_refs.rename(rename_dict, axis=1)

                return pivoted_refs
            
            if colnames:
                rename_dict = {
                    f'{col}': f'{col} {codes.ref_descriptions['REF01'].get(col,col)} = {codes.ref_descriptions.get(col, col)}'
                    for col in [col for col in refs.columns if col.startswith('REF') and col not in id_vars + ['REF01']]
                }
                refs = refs.rename(rename_dict,axis=1)

        # Return the original table if flatten is False
        return refs

    def claims_refs_table(self, colnames=False, flatten=False):
        result = self.parse_refs_data(self.claims_refs,colnames,flatten)
        return result

    def services_refs_table(self, colnames=False, flatten=False):
        result = self.parse_refs_data(self.services_refs,colnames,flatten)
        return result

    def parse_cas_data(self, data, colnames=False, flatten=False):
        # Create DataFrame from the provided data
        claim_cas = pd.DataFrame(data)

        if not claim_cas.empty:
            # List of identifier columns
            id_vars = ['isa_id', 'functional_group_id', 'statement_id', 'claim_id']
            if 'service_id' in claim_cas.columns:
                id_vars = ['isa_id', 'functional_group_id', 'statement_id', 'claim_id', 'service_id']
            # Pivot the table if flatten flag is True
            if flatten:
                # Pivot the DataFrame on CAS01 and other CAS columns (CAS02, CAS03, etc.)
                pivoted_claim_cas = claim_cas.pivot_table(
                    index=id_vars,
                    columns='CAS01',  # Column to pivot on (e.g., 'OA', 'PR')
                    values=[col for col in claim_cas.columns if col.startswith('CAS') and col not in id_vars + ['CAS01']],
                    aggfunc='first'  # Use 'first' to take the first non-null value for duplicates
                )

                # Flatten the MultiIndex columns if needed
                pivoted_claim_cas.columns = [f'{col}_{val}' for col, val in pivoted_claim_cas.columns]
                pivoted_claim_cas = pivoted_claim_cas.reset_index(drop=False)
                # Rename columns if `colnames=True`
                if colnames:
                    # Create a renaming dictionary
                    rename_dict = {
                        f'{col}_{val}': f'{col}_{val} {codes.cas_descriptions["CAS01"].get(val, val)} - {codes.cas_descriptions.get(col, col)}'
                        for col, val in (x.split("_") for x in pivoted_claim_cas.columns if re.search('.*CAS.*', x))
                    }

                    # Rename the columns using the created dictionary
                    pivoted_claim_cas = pivoted_claim_cas.rename(rename_dict, axis=1)

                return pivoted_claim_cas
            if colnames:
                rename_dict = {
                    col: f'{col} {codes.cas_descriptions['CAS01'].get(col,col)} - {codes.cas_descriptions.get(col, col)}'
                    for col in (col for col in claim_cas.columns if col.startswith('CAS') and col not in id_vars + ['CAS01'])
                }
                claim_cas = claim_cas.rename(rename_dict,axis=1)

        # Return the original table if flatten is False
        return claim_cas


    def claims_cas_table(self, colnames=False, flatten=False):
        result = self.parse_cas_data(self.claims_cas,colnames,flatten)
        return result
    
    def services_cas_table(self,colnames=False,flatten=False):
        result = self.parse_cas_data(self.services_cas,colnames,flatten)
        return result