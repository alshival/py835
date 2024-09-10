import pyx12
import pyx12.error_handler
import pyx12.x12context
import pyx12.params
import os
import json

def parse(file_path):
    # Initialize X12 parsing context
    params = pyx12.params.params()
    # Error handler to capture parsing issues
    errh = pyx12.error_handler.errh_null()

    # Dictionary to group data by Patient Control Number
    grouped_by_patient = {}

    # Open the EDI file
    with open(file_path, 'r') as edi_file:
        context_reader = pyx12.x12context.X12ContextReader(params, errh, edi_file)
        current_patient_control_number = None

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

            # If this is a CLP segment, extract the Patient Control Number
            if seg_id == "CLP":
                # The Patient Control Number is typically the first element (index 1)
                current_patient_control_number = seg_data.get_value("CLP01")
                
                # Ensure the control number exists in the dictionary
                if current_patient_control_number not in grouped_by_patient:
                    grouped_by_patient[current_patient_control_number] = []

            # Add the segment to the current patient's group
            if current_patient_control_number:
                grouped_by_patient[current_patient_control_number].append(segment_dict)

    # Convert the result to JSON and return
    return grouped_by_patient