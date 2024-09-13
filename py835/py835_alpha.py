import pyx12
import pyx12.error_handler
import pyx12.x12context
import pyx12.params
import random
import string
from io import StringIO
import pandas as pd 

def generate_id():
    # Define the character set: digits and uppercase letters
    characters = string.ascii_letters + string.digits
    
    # Generate four segments, each with six random characters
    segments = [''.join(random.choice(characters) for _ in range(6)) for _ in range(4)]
    
    # Join the segments with dashes
    api_key = '-'.join(segments)
    
    return api_key

current_state = {
    'header': None,
    'functional_group':None,
    'statement':None,
    'claim':None,
    'service':None
}

class Element:
    def __init__(self,child,value,segment):
        if segment.id in ['REF','CAS','DTM','NM1','N1','AMT','SVC','BPR']:
            self.id = child.id + '-'+ segment.seg_data.get_value(segment.id+'01')
        else:
            self.id = child.id
        self.name = child.name
        self.value = value

class Segment:
    def __init__(self,segment):
        self.segment_id = generate_id()
        self.elements = []
        self.cas = []
        
        for child in segment.x12_map_node.children:
            self.elements.append(
                Element(child,segment.seg_data.get_value(child.id),segment)
            )

class CAS:
    def __init__(self,segment):
        self.segment_id = generate_id()
        self.segments = []
    def update(self,segment):
        self.segments.append(Segment(segment))

class Service:
    def __init__(self):
        self.service_id = generate_id()
        self.segments = []
        
    def update(self,segment):
        self.segments.append(Segment(segment))

    
class Claim:
    def __init__(self):
        self.claim_id = generate_id()
        self.segments = []
        self.SERVICES = []
        

    def update(self,segment):
        self.segments.append(Segment(segment))

    def append(self,service):
        self.SERVICES.append(service)
    
class Statement:
    def __init__(self):
        self.statement_id = generate_id()
        self.segments = []
        self.CLAIMS = []
        

    def update(self,segment):
        self.segments.append(Segment(segment))

    def append(self,claim):
        self.CLAIMS.append(claim)
    
class Functional_Group:
    def __init__(self):
        self.functional_group_id = generate_id()
        self.segments = []
        self.STATEMENTS = []
        
    def update(self,segment):
        self.segments.append(Segment(segment))

    def append(self,statement):
        self.STATEMENTS.append(statement)
    
class Header:
    def __init__(self):
        self.header_id = generate_id()
        self.segments = []
        self.FUNCTIONAL_GROUPS = []

    def update(self,segment):
        self.segments.append(Segment(segment))

    def append(self,functional_group):
        self.FUNCTIONAL_GROUPS.append(functional_group)
    
class Parser:
    def __init__(self,filepath):
        self.filepath = filepath
        self.unpack()
        
    def load_file_content(self):
        with open(self.filepath, 'r') as edi_file:
            return edi_file.read()

    def load_context(self):
        params = pyx12.params.params()
        errh = pyx12.error_handler.errh_null()
        edi_file_stream = StringIO(self.load_file_content())
        return pyx12.x12context.X12ContextReader(params, errh, edi_file_stream)

    def unpack(self):
        current_state['header'] = Header()
        reader = self.load_context()
        for segment in reader.iter_segments():
            if segment.id == 'GS':  # Begin functional group
                if current_state['functional_group'] is not None:
                    current_state['header'].append(current_state['functional_group'])
                current_state['service'] = None
                current_state['claim'] = None 
                current_state['statement'] = None 
                current_state['functional_group'] = Functional_Group()
                current_state['functional_group'].update(segment)
                
            elif segment.id == 'ST':  # Begin statement
                # Ensure that the functional group does not append to statements
                if current_state['statement'] is not None:
                    current_state['functional_group'].append(current_state['statement'])
                current_state['service'] = None
                current_state['claim'] = None 
                current_state['statement'] = Statement()
                current_state['statement'].update(segment)
            elif segment.id == 'CLP':
                if current_state['claim'] is not None:
                    current_state['statement'].append(current_state['claim'])
                current_state['service'] = None 
                current_state['claim'] = Claim()
                current_state['claim'].update(segment)
            elif segment.id == 'SVC':
                if current_state['service'] is not None:
                    current_state['claim'].append(current_state['service'])
                current_state['service'] = Service()
                current_state['service'].update(segment)
            elif segment.id == 'SE': # End of a statement
                
                current_state['statement'].update(segment)
                current_state['functional_group'].append(current_state['statement'])
                current_state['statement'] = None
                current_state['claim'] = None 
                current_state['service'] = None  
            elif segment.id == 'GE': # End of a functional group
                
                current_state['functional_group'].update(segment)
                current_state['header'].append(current_state['functional_group'])
                current_state['functional_group'] = None
                current_state['statement'] = None
                current_state['claim'] = None 
                current_state['service'] = None  

            else:
                if current_state['service'] is not None:
                    current_state['service'].update(segment)
                elif current_state['claim'] is not None:
                    current_state['claim'].update(segment)
                elif current_state['statement'] is not None:
                    current_state['statement'].update(segment)
                elif current_state['functional_group'] is not None:
                    current_state['functional_group'].update(segment)
                else: current_state['header'].update(segment)

        self.HEADER = current_state['header']

        # Generate pandas dataframes
        class PandasClass:
            def __init__(self,header):
                self.HEADER = [] 
                self.FUNCTIONAL_GROUPS = [] 
                self.STATEMENTS = [] 
                self.CLAIMS = [] 
                self.SERVICES = [] 
                self.generate_dfs(header)

            def generate_dfs(self,header):
                header_id = header.header_id
                for seg_head in header.segments:
                    head_data = []
                    for seg_el in seg_head.elements:
                        el = {'header_id': header_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                        head_data.append(el)
                    head_df = pd.DataFrame(head_data)
                    if not head_df.empty:
                        self.HEADER.append(head_df)
                for group in header.FUNCTIONAL_GROUPS:
                    functional_group_id = group.functional_group_id

                    for seg_group in group.segments:
                        group_data =[]
                        for seg_el in seg_group.elements:
                            el = {'header_id': header_id, 'functional_group_id': functional_group_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                            group_data.append(el)
                        group_df = pd.DataFrame(group_data)
                        if not group_df.empty:
                            self.FUNCTIONAL_GROUPS.append(group_df)

                    for statement in group.STATEMENTS:
                        statement_id = statement.statement_id 
                        for seg_statement in statement.segments:
                            statement_data = []
                            for seg_el in seg_statement.elements:
                                el = {'header_id': header_id, 'functional_group_id': functional_group_id,'statement_id':statement_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                                statement_data.append(el)
                            statement_df = pd.DataFrame(statement_data)
                            if not statement_df.empty:
                                self.STATEMENTS.append(statement_df)

                        for claim in statement.CLAIMS:
                            claim_id = claim.claim_id
                            for seg_claim in claim.segments:
                                claim_data = []
                                for seg_el in seg_claim.elements:
                                    el = {'header_id': header_id, 'functional_group_id': functional_group_id,'statement_id':statement_id,'claim_id':claim_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                                    claim_data.append(el)
                                claim_df = pd.DataFrame(claim_data)
                                if not claim_df.empty:
                                    self.CLAIMS.append(claim_df)

                            for service in claim.SERVICES:
                                service_id = service.service_id
                                for seg_service in service.segments:
                                    service_data = []
                                    for seg_el in seg_service.elements:
                                        el = {'header_id': header_id, 'functional_group_id': functional_group_id,'statement_id':statement_id,'claim_id':claim_id,'service_id':service_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                                        service_data.append(el)
                                    service_df = pd.DataFrame(service_data)
                                    if not service_df.empty:
                                        self.SERVICES.append(service_df)
                self.HEADER = pd.concat(self.HEADER,ignore_index=True)
                self.FUNCTIONAL_GROUPS = pd.concat(self.FUNCTIONAL_GROUPS,ignore_index=True)
                self.STATEMENTS = pd.concat(self.STATEMENTS,ignore_index=True)
                self.CLAIMS = pd.concat(self.CLAIMS,ignore_index=True)
                self.SERVICES = pd.concat(self.SERVICES,ignore_index=True)

        self.pandas = PandasClass(self.HEADER)

    def financial_report(self):
        # Prepare header 
        header = self.pandas.HEADER.copy()
        header['id-name'] = 'HEADER ' + header['id']+' '+header['name']
        header = header[['header_id','id-name','value']].pivot(
            index='header_id',
            columns='id-name',
            values='value'
        )

        df = header

        functional_groups = self.pandas.FUNCTIONAL_GROUPS.copy()
        functional_groups['id-name'] = 'TRANSACTION ' + functional_groups['id']+' '+ functional_groups['name']
        functional_groups = functional_groups[['header_id','functional_group_id','id-name','value']].pivot(
            index = ['header_id','functional_group_id'],
            columns = 'id-name',
            values= 'value'
        ).reset_index()

        df = df.merge(
            functional_groups,
            on = ['header_id'],
            how = 'left'
        ).reset_index()

        statements = self.pandas.STATEMENTS.copy()
        if not statements.empty:
            statements['id-name'] = 'STATEMENT ' + statements['id']+' '+statements['name']
            statements = statements[['header_id','functional_group_id','statement_id','id-name','value']].pivot(
                index = ['header_id','functional_group_id','statement_id'],
                columns = 'id-name',
                values = 'value'
            ).reset_index()
            df = df.merge(
                statements,
                on = ['header_id','functional_group_id'],
                how = 'left'
            ).reset_index()

        claims = self.pandas.CLAIMS.copy()
        if not claims.empty:
            claims['id-name'] = 'CLAIM ' + claims['id']+' '+claims['name']
            claims = claims[['header_id','functional_group_id','statement_id','claim_id','id-name','value']].pivot(
                index = ['header_id','functional_group_id','statement_id','claim_id'],
                columns = 'id-name',
                values = 'value'
            ).reset_index()

            df = df.merge(
                claims,
                on = ['header_id','functional_group_id','statement_id'],
                how = 'left'
            )

        services = self.pandas.SERVICES.copy()
        if not services.empty:
            services['id-name'] = 'SERVICE ' + services['id'] + ' ' + services['name']
            services = services[['header_id','functional_group_id','statement_id','claim_id','service_id','id-name','value']].pivot(
                index = ['header_id','functional_group_id','statement_id','claim_id','service_id'],
                columns = 'id-name',
                values = 'value'
            ).reset_index()

            df = df.merge(
                services,
                on = ['header_id','functional_group_id','statement_id','claim_id'],
                how = 'left'
            )

        return df

