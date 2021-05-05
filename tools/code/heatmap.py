'''
converts video to frames and saves images by different interval, or overlap, etc
'''
import folium
from folium import plugins
from folium.plugins import HeatMap
import csv

# class plitterMap():
#     def __int__(self, file_path):
#         self.data = file_path
#         df = []
#         with open(self.data) as f:
#             reader = csv.reader(f)
#                 for row in reader:
#                     df_row = []
#                     df_row.append(row[0])
#                     df_row.append(row[0])
#                     df_row.append(row[0])
#                     df.append(row)
#         self.tooltip = df[0][0]

#     def loadMap():
#       self.map = folium.Map(location=[float(row[1]), float(row[2])], zoom_start = 18)

    
#     def loadGpsLoc():
        
#     folium.Marker([float(row[1]), float(row[2])], popup="<i>"+row[0]+"</i>", tooltip=tooltip, icon=icon_circle).add_to(rangsit_map)

# rangsit_map