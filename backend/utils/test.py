import numpy as np
import json
from backend.utils.dataStructure import ProjectFilesGraph

file_path = '/Users/rainy/pythonProjects/d3_demo/static/resources/json/input/android/android_12.0.0/wifi.json'
with open(file_path, 'r') as file:
    json_object = json.load(file)
# g = ProjectFilesGraph([0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
#                       [{'src': 1, 'target': 2}, {'src': 2, 'target': 3}, {'src': 3, 'target': 4},
#                        {'src': 3, 'target': 5}])
g = ProjectFilesGraph(json_object['variables'], json_object['cells'])
print(g.is_circle_exist())
