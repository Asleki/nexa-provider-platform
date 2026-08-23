"""Execution facts deliberately preserve proposal vs official-name separation."""
from .naming import physical_feature_names
from .refinement import landform_extents

def execution_plan():
    return {'geographic_name_inserts':physical_feature_names(),'landform_extent_candidates':landform_extents(),'auto_gazette':False,'existing_hydrology_geometry_replacement':False}
