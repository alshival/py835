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

class Element:
    def __init__(self,child,value):
        self.id = child.id
        self.name = child.name
        self.value = value

class Segment:
    def __init__(self,segment):
        self.segment_id = generate_id()
        self.elements = []

        for child in segment.x12_map_node.children:
            self.elements.append(
                Element(child,segment.seg_data.get_value(child.id))
            )

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
        current_header = Header()
        current_functional_group = None 
        current_statement = None 
        current_claim = None 
        current_service = None

        reader = self.load_context()
        for segment in reader.iter_segments():
            
            # We unpack from the inside, out
            if current_service:
                current_service.update(segment)
            elif current_claim:
                current_claim.update(segment)
            elif current_statement:
                current_statement.update(segment)
            elif current_functional_group:
                current_functional_group.update(segment)
            else:
                current_header.update(segment)

            
            # Handle headers
            if segment.id == 'GS':
                if current_functional_group is not None:
                    current_header.append(current_functional_group)
                current_service = None 
                current_claim = None 
                current_statement = None 
                current_functional_group = Functional_Group()
            elif segment.id == 'ST':
                if current_statement is not None:
                    current_functional_group.append(current_statement)
                current_service = None 
                current_claim = None 
                current_statement = Statement()
            elif segment.id == 'CLP':
                if current_claim is not None:
                    current_statement.append(current_claim)
                current_service = None 
                current_claim = Claim()
            elif segment.id == 'SVC':
                # Append last service 
                if current_service:
                    current_claim.append(current_service)
                current_service = Service()
            if segment.id == 'SE': # End of statement
                # Append last service:
                if current_service:
                    current_claim.append(current_service)
                    current_service = None 
                # Append last claim:
                if current_claim:
                    current_statement.append(current_claim)
                    current_claim = None 
                if current_statement:
                    current_functional_group.append(current_statement)
                    current_statement = None
            if segment.id == 'GE': # End functional group 
                current_header.append(current_functional_group)
                current_functional_group = None

        self.HEADER = current_header

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
                for seg_group in header.segments:
                    data = []
                    for seg_el in seg_group.elements:
                        el = {'header_id': header_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                        data.append(el)
                    df = pd.DataFrame(data)
                    if not df.empty:
                        self.HEADER.append(df)
                for group in header.FUNCTIONAL_GROUPS:
                    functional_group_id = group.functional_group_id

                    for seg_statement in group.segments:
                        group_data =[]
                        for seg_el in seg_statement.elements:
                            el = {'header_id': header_id, 'functional_group_id': functional_group_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                            group_data.append(el)
                        df = pd.DataFrame(group_data)
                        if not df.empty:
                            self.FUNCTIONAL_GROUPS.append(df)

                    for statement in group.STATEMENTS:
                        statement_id = statement.statement_id 
                        for seg_group in group.segments:
                            statement_data = []
                            for seg_el in seg_group.elements:
                                el = {'header_id': header_id, 'functional_group_id': functional_group_id,'statement_id':statement_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                                statement_data.append(el)
                            df = pd.DataFrame(statement_data)
                            if not df.empty:
                                self.STATEMENTS.append(df)

                        for claim in statement.CLAIMS:
                            claim_id = claim.claim_id
                            for seg_claim in claim.segments:
                                claim_data = []
                                for seg_el in seg_claim.elements:
                                    el = {'header_id': header_id, 'functional_group_id': functional_group_id,'statement_id':statement_id,'claim_id':claim_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                                    claim_data.append(el)
                                df = pd.DataFrame(claim_data)
                                if not df.empty:
                                    self.CLAIMS.append(df)

                            for service in claim.SERVICES:
                                service_id = service.service_id
                                for seg_service in service.segments:
                                    service_data = []
                                    for seg_el in seg_service.elements:
                                        el = {'header_id': header_id, 'functional_group_id': functional_group_id,'statement_id':statement_id,'claim_id':claim_id,'service_id':service_id,'id':seg_el.id,'name':seg_el.name,'value':seg_el.value}
                                        service_data.append(el)
                                    df = pd.DataFrame(service_data)
                                    if not df.empty:
                                        self.SERVICES.append(df)
                self.HEADER = pd.concat(self.HEADER,ignore_index=True)
                self.FUNCTIONAL_GROUPS = pd.concat(self.FUNCTIONAL_GROUPS,ignore_index=True)
                self.STATEMENTS = pd.concat(self.STATEMENTS,ignore_index=True)
                self.CLAIMS = pd.concat(self.CLAIMS,ignore_index=True)
                self.SERVICES = pd.concat(self.SERVICES,ignore_index=True)

        self.pandas = PandasClass(self.HEADER)

    def financial_report(self):
        print("test")