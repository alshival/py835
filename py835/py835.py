import pyx12
import pyx12.error_handler
import pyx12.x12context
import pyx12.params
import pyx12.x12file
import os
import json

def parse(file_path):

    # Initialize X12 parsing context
    params = pyx12.params.params()
    # Error handler to capture parsing issues
    errh = pyx12.error_handler.errh_null()
    
    result = []

    # Open the EDI file
    with open(file_path, 'r') as edi_file:
        context_reader = pyx12.x12context.X12ContextReader(params, errh, edi_file)

        # Iterate over segments
        for seg in context_reader.iter_segments():
            seg_node = seg.x12_map_node
            seg_data = seg.seg_data
            seg_id = seg_node.id
            seg_name = seg.x12_map_node.name
            
            segment_dict = {
                "segment_id": seg_id,
                "segment_name": seg_name,
                "elements": []
            }
            
            children = seg_node.children
            # Iterate over elements in the segment
            for idx in range(1, len(seg_data) + 1):
                element_value = seg_data.get_value(f"{seg_id}{str(idx).zfill(2)}")
                element_name = children[idx - 1].name
                element_dict = {
                    "element_index": idx,
                    "element_name": element_name,
                    "element_value": element_value
                }
                segment_dict["elements"].append(element_dict)
            
            result.append(segment_dict)

    # Convert result to JSON string and return
    return result