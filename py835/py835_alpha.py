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

            ##### Header
            if seg_id == 'ISA':
                isa_id = seg_data.get_value("ISA13")
                isa_data = {'isa_id':isa_id}
                isa_data.update(segment_data)

            ########## Start Functional Group
            if seg_id == 'GS':
                functional_group_id = seg_data.get_value("GS06")
                current_functional_group = {'isa_id': isa_id,'functional_group_id': functional_group_id}
                current_functional_group.update(segment_data)

            #################### Start of a Transaction Set
            if seg_id == 'ST':

                statement_refs = []

                statement_id = seg_data.get_value("ST02")
                statement_base = {'isa_id': isa_id, 'functional_group_id': functional_group_id,'statement_id': statement_id}
                current_statement = statement_base
                current_statement.update(segment_data)
                
            if seg_id in ['BPR','TRN']:
                current_statement.update(segment_data)
            if seg_id == 'REF' and seg_data.get_value('REF01') == 'EV':
                statement_ref = statement_base
                statement_ref.update(segment_data)
                statement_refs.append(statement_ref)
            if seg_id == 'REF' and seg_data.get_value('REF01') == 'F2':
                statement_ref = statement_base
                statement_ref.update(segment_data)
                statement_refs.append(statement_ref)
            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '405':
                current_statement.update(segment_data)
            if seg_id == 'N1':
                current_statement.update(
                    {x + '-' + seg_data.get_value("N101"): segment_data[x] for x in segment_data.keys()}
                )
            if seg_id == 'REF' and seg_data.get_value("REF01") in ['2U','TJ']:
                current_statement.update(
                    {x + '-' + seg_data.get_value("REF01"): segment_data[x] for x in segment_data.keys()}
                )
            if seg_id == 'LX':
                current_statement.update(segment_data)
            
            ######################################## Start of a new claim
            if seg_id == 'CLP':

                claim_refs = []
                claim_cass = []

                if current_claim is not None:
                    claims.append(current_claim)
                
                # Reset service-level context
                current_service = None 

                # Claim base
                claim_id = seg_data.get_value("CLP01")
                claim_base = {'isa_id': isa_id, 'functional_group_id': functional_group_id,'statement_id': statement_id, 'claim_id': claim_id}
                current_claim = claim_base
                current_claim.update(segment_data)

            if seg_id == 'CAS' and seg_data.get_value("CAS01") in['CO','OA','PR']:
                claim_cas = claim_base
                claim_cas.update(segment_data)
                claim_cass.append(claim_cas)
            
            if seg_id == 'NM1':
                current_claim.update(
                    {x+'-'+seg_data.get_value('NM101'): segment_data[x] for x in segment_data.keys()}
                )
            
            if seg_id == 'REF' and seg_data.get_value('REF01') not in  ['EV','F2']:
                if current_service is None:
                    if current_claim is not None:
                        claim_ref = claim_base
                        claim_ref.update(segment_data)
                        claim_refs.append(claim_ref)
                    else:
                        statement_ref = statement_base
                        statement_ref.update(segment_data)
                        statement_refs.append(statement_ref)
            if seg_id == 'DTM' and seg_data.get_value("DTM01") in ['232', '233', '050']:
                current_claim.update(
                    {codes.DTM01.get(seg_data.get_value("DTM01"),"DTM01"+seg_data.get_value("DTM01")+'-'+x): segment_data[x] for x in segment_data.keys()}
                )
            ################################################################################ Start a new service
            if seg_id == 'SVC':

                service_refs = [] 
                service_cass = []
                service_id =  seg_data.get_value("SVC01")
                service_base = {'isa_id': isa_id, 'functional_group_id': functional_group_id,'statement_id': statement_id, 'claim_id': claim_id, 'service_id': service_id}
                current_service = service_base
                current_service.update(segment_data)

            if seg_id == 'CAS':
                if current_service is None:
                    # This is a claim-level CAS. 
                    claim_cas = claim_base
                    claim_cas.update(segment_data)
                    claim_cass.append(claim_cas)
                else:
                    service_cas = service_base
                    service_cas.update(segment_data)
                    service_cass.append(service_cas)
            if seg_id == 'AMT':
                if current_service is None:
                    current_claim.update(segment_data)
                else:
                    current_service.update(segment_data)
            if seg_id == 'DTM' and seg_data.get_value("DTM01") == '472':
                current_service.update(
                    {codes.DTM01.get(seg_data.get_value("DTM01"),"DTM"+seg_data.get_value("DTM01"))+'-'+x: segment_data[x] for x in segment_data}
                )
            if seg_id == 'REF' and seg_data.get_value('REF01') not in  ['EV','F2']:
                if current_service is not None:
                    service_ref = service_base
                    service_ref.update(segment_data)
                    service_refs.append(service_ref)
            
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

                # Reset the variables
                current_service = None
                current_claim = None 
                current_statement = None
                statement_refs = []
                claim_refs = []
                service_refs = []

            ########## End Functional Group
            if seg_id == 'GE':
                current_functional_group.update(segment_data)
                functional_groups.append(current_functional_group)
                current_functional_group = None

        # Add to self. 
        self.isa = isa_data
        self.functional_groups = functional_groups 
        self.transaction_sets = statements 
        self.transaction_refs = statement_refs
        self.claims = claims 
        self.claims_refs = claim_refs
        self.claims_cas = claim_cass
        self.services = services 
        self.services_cas = service_cass


    def transactions(self):
        # Convert lists to DataFrames
        isa_data = pd.DataFrame([self.isa])  # Since isa_data is a dictionary, we put it in a list to create a single-row DataFrame
        functional_groups = pd.DataFrame(self.functional_groups)
        transaction_sets = pd.DataFrame(self.transaction_sets)
        claims = pd.DataFrame(self.claims)
        services = pd.DataFrame(self.services)

        # Join the DataFrames
        # 1. Join isa_data with functional_groups on 'isa_id'
        master_df = pd.merge(isa_data, functional_groups, on='isa_id', how='left')

        # 2. Join with transaction_sets on 'isa_id' and 'functional_group_id'
        master_df = pd.merge(master_df, transaction_sets, on=['isa_id', 'functional_group_id'], how='left')

        # 3. Join with claims on 'isa_id', 'functional_group_id', and 'statement_id'
        master_df = pd.merge(master_df, claims, on=['isa_id', 'functional_group_id', 'statement_id'], how='left')

        # 4. Join with services on 'isa_id', 'functional_group_id', 'statement_id', and 'claim_id'
        master_df = pd.merge(master_df, services, on=['isa_id', 'functional_group_id', 'statement_id', 'claim_id'], how='left')

        master_df['filename'] = os.path.basename(self.file_path)
        # Return the final master DataFrame
        return master_df
