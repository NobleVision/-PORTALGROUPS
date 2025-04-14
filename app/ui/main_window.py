import tkinter as tk
from tkinter import ttk, messagebox
from app.api.client import DXNetOpsAPIClient
import xml.etree.ElementTree as ET

class DXNetOpsTroubleshooter:
    def __init__(self, root):
        self.root = root
        self.root.title("DX NetOps Group Troubleshooter")
        self.root.geometry("1200x800")

        self.api_client = DXNetOpsAPIClient()
        self.pc_id = None
        self.group_info_xml = None

        self.create_input_section()
        self.create_group_tree()
        self.create_coordinate_section()
        self.create_interface_section()
        self.create_map_preview_section()

    def create_input_section(self):
        input_frame = ttk.LabelFrame(self.root, text="Group Parameters")
        input_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(input_frame, text="DA Group ID:").grid(row=0, column=0, padx=5, pady=5)
        self.group_id_entry = ttk.Entry(input_frame, width=30)
        self.group_id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="Load Group", command=self.load_group).grid(row=0, column=2, padx=5, pady=5)

    def create_group_tree(self):
        tree_frame = ttk.LabelFrame(self.root, text="Group Hierarchy")
        tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Latitude", "Longitude", "Description", "Elevation", "Location"))
        self.tree.heading("#0", text="Name")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Latitude", text="Latitude")
        self.tree.heading("Longitude", text="Longitude")
        self.tree.heading("Description", text="Description")
        self.tree.heading("Elevation", text="Elevation")
        self.tree.heading("Location", text="Location")
        
        # Set column widths
        self.tree.column("ID", width=100)
        self.tree.column("Latitude", width=80)
        self.tree.column("Longitude", width=80)
        self.tree.column("Description", width=120)
        self.tree.column("Elevation", width=80)
        self.tree.column("Location", width=120)
        
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_group_select)

    def create_coordinate_section(self):
        coord_frame = ttk.LabelFrame(self.root, text="Geo-Coordinates")
        coord_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(coord_frame, text="Latitude:").grid(row=0, column=0, padx=5, pady=5)
        self.lat_entry = ttk.Entry(coord_frame, width=20)
        self.lat_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(coord_frame, text="Longitude:").grid(row=0, column=2, padx=5, pady=5)
        self.lon_entry = ttk.Entry(coord_frame, width=20)
        self.lon_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(coord_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5)
        self.desc_entry = ttk.Entry(coord_frame, width=20)
        self.desc_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(coord_frame, text="Elevation:").grid(row=1, column=2, padx=5, pady=5)
        self.elevation_entry = ttk.Entry(coord_frame, width=20)
        self.elevation_entry.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(coord_frame, text="Location:").grid(row=2, column=0, padx=5, pady=5)
        self.location_entry = ttk.Entry(coord_frame, width=20)
        self.location_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(coord_frame, text="Lookup:").grid(row=2, column=2, padx=5, pady=5)
        self.lookup_entry = ttk.Entry(coord_frame, width=20)
        self.lookup_entry.grid(row=2, column=3, padx=5, pady=5)
        ttk.Button(coord_frame, text="Lookup Location", command=self.lookup_location).grid(row=2, column=4, padx=5, pady=5)

        ttk.Button(coord_frame, text="Update Coordinates", command=self.update_coordinates).grid(row=3, column=4, padx=10, pady=5)

        self.selected_group_id = None

        # For interface management
        self.interface_group_id = None
        self.interface_time_start = None
        self.interface_time_end = None
        self.interfaces = []

    def create_interface_section(self):
        iface_frame = ttk.LabelFrame(self.root, text="Interface Connections")
        iface_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Time range selection
        time_frame = ttk.Frame(iface_frame)
        time_frame.pack(anchor="w", padx=5, pady=2)

        ttk.Label(time_frame, text="Start Time (UTC, epoch):").grid(row=0, column=0, padx=2)
        self.start_time_entry = ttk.Entry(time_frame, width=16)
        self.start_time_entry.grid(row=0, column=1, padx=2)
        ttk.Label(time_frame, text="End Time (UTC, epoch):").grid(row=0, column=2, padx=2)
        self.end_time_entry = ttk.Entry(time_frame, width=16)
        self.end_time_entry.grid(row=0, column=3, padx=2)

        ttk.Button(time_frame, text="Load Interfaces", command=self.load_interfaces).grid(row=0, column=4, padx=5)

        # Interface table
        self.interface_tree = ttk.Treeview(iface_frame, columns=("Group", "ID", "Name", "ConnectsTo"), show="headings")
        self.interface_tree.heading("Group", text="Group")
        self.interface_tree.heading("ID", text="Interface ID")
        self.interface_tree.heading("Name", text="Name")
        self.interface_tree.heading("ConnectsTo", text="ConnectsTo")
        self.interface_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Edit ConnectsTo
        edit_frame = ttk.Frame(iface_frame)
        edit_frame.pack(anchor="w", padx=5, pady=2)
        ttk.Label(edit_frame, text="Selected Interface ID:").grid(row=0, column=0, padx=2)
        self.selected_iface_id_var = tk.StringVar()
        self.selected_iface_id_entry = ttk.Entry(edit_frame, textvariable=self.selected_iface_id_var, width=16, state="readonly")
        self.selected_iface_id_entry.grid(row=0, column=1, padx=2)
        ttk.Label(edit_frame, text="New ConnectsTo:").grid(row=0, column=2, padx=2)
        self.new_connectsto_entry = ttk.Entry(edit_frame, width=16)
        self.new_connectsto_entry.grid(row=0, column=3, padx=2)
        ttk.Button(edit_frame, text="Update ConnectsTo", command=self.update_connectsto).grid(row=0, column=4, padx=5)

        self.interface_tree.bind("<<TreeviewSelect>>", self.on_interface_select)

    def load_group(self):
        da_id = self.group_id_entry.get().strip()
        if not da_id:
            messagebox.showwarning("Warning", "Please enter a DA Group ID.")
            return
        try:
            pc_id = self.api_client.get_pc_id_from_da_id(da_id)
            if not pc_id:
                messagebox.showerror("Error", f"No PC ID found for DA Group ID {da_id}")
                return
            group_info_xml = self.api_client.get_group_info(pc_id)
            self.pc_id = pc_id
            self.group_info_xml = group_info_xml
            self.populate_tree_from_xml(group_info_xml)
            # Set default time range (last hour)
            import time
            end_time = int(time.time())
            start_time = end_time - 3600
            self.start_time_entry.delete(0, tk.END)
            self.start_time_entry.insert(0, str(start_time))
            self.end_time_entry.delete(0, tk.END)
            self.end_time_entry.insert(0, str(end_time))
            self.interface_group_id = da_id
        except Exception as e:
            messagebox.showerror("API Error", str(e))

    def load_interfaces(self):
        da_id = self.interface_group_id
        if not da_id:
            messagebox.showwarning("Warning", "No DA Group loaded.")
            return
        try:
            start_time = int(self.start_time_entry.get())
            end_time = int(self.end_time_entry.get())
        except Exception:
            messagebox.showerror("Error", "Invalid start or end time (must be integer epoch).")
            return
        try:
            self.interfaces = self.api_client.fetch_interfaces_csv(da_id, start_time, end_time)
            self.populate_interface_tree()
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to load interfaces: {e}")

    def populate_interface_tree(self):
        self.interface_tree.delete(*self.interface_tree.get_children())
        for iface in self.interfaces:
            self.interface_tree.insert(
                "", "end",
                iid=iface["interface_id"],
                values=(
                    iface["group_name"],  # Group column
                    iface["interface_id"],
                    iface["interface_name"],
                    iface["connects_to"]
                )
            )

    def on_interface_select(self, event):
        selected = self.interface_tree.selection()
        if not selected:
            return
        iface_id = selected[0]
        self.selected_iface_id_var.set(iface_id)
        iface = next((i for i in self.interfaces if i["interface_id"] == iface_id), None)
        if iface:
            self.new_connectsto_entry.delete(0, tk.END)
            self.new_connectsto_entry.insert(0, iface.get("connects_to", ""))

    def update_connectsto(self):
        iface_id = self.selected_iface_id_var.get()
        new_connectsto = self.new_connectsto_entry.get().strip()
        if not iface_id:
            messagebox.showwarning("Warning", "No interface selected.")
            return
        try:
            self.api_client.update_interface_connectsto(iface_id, new_connectsto)
            # Update in-memory and UI
            for iface in self.interfaces:
                if iface["interface_id"] == iface_id:
                    iface["connects_to"] = new_connectsto
            self.populate_interface_tree()
            messagebox.showinfo("Success", "ConnectsTo updated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update ConnectsTo: {e}")

    def populate_tree_from_xml(self, xml_str):
        self.tree.delete(*self.tree.get_children())
        try:
            root = ET.fromstring(xml_str)
            # The root is <GroupTree>, children are <Group>
            for group_elem in root.findall("Group"):
                group_id = group_elem.attrib.get("id", "")
                name = group_elem.attrib.get("name", "")
                
                # Get coordinates (can be in attributes or child elements)
                lat = group_elem.attrib.get("latitude", "") or group_elem.findtext("Latitude", "")
                lon = group_elem.attrib.get("longitude", "") or group_elem.findtext("Longitude", "")
                desc = group_elem.attrib.get("desc", "") or group_elem.findtext("Description", "")
                elevation = group_elem.attrib.get("elevation", "") or group_elem.findtext("Elevation", "")
                location = group_elem.attrib.get("location", "") or group_elem.findtext("LocationDesc", "")
                
                self.tree.insert("", "end", iid=group_id, text=name, 
                               values=(group_id, lat, lon, desc, elevation, location))
        except Exception as e:
            messagebox.showerror("Parse Error", f"Failed to parse group XML: {e}")

    def on_group_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        group_id = selected[0]
        self.selected_group_id = group_id
        
        # Get values directly from the tree
        lat = self.tree.set(group_id, "Latitude")
        lon = self.tree.set(group_id, "Longitude")
        desc = self.tree.set(group_id, "Description")
        elevation = self.tree.set(group_id, "Elevation")
        location = self.tree.set(group_id, "Location")
        
        # Populate the entry fields
        self.lat_entry.delete(0, tk.END)
        self.lat_entry.insert(0, lat)
        self.lon_entry.delete(0, tk.END)
        self.lon_entry.insert(0, lon)
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, desc)
        self.elevation_entry.delete(0, tk.END)
        self.elevation_entry.insert(0, elevation)
        self.location_entry.delete(0, tk.END)
        self.location_entry.insert(0, location)

    def lookup_location(self):
        query = self.lookup_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a location to look up.")
            return
        try:
            import os
            import requests
            api_key = os.getenv("BING_MAPS_API_KEY")
            if not api_key or api_key == "your_bing_maps_api_key":
                messagebox.showinfo(
                    "API Key Required",
                    "To use the location lookup feature, please set BING_MAPS_API_KEY in your .env file. "
                    "You can get a free key at https://www.bingmapsportal.com/."
                )
                return
            url = "http://dev.virtualearth.net/REST/v1/Locations"
            params = {
                "q": query,
                "key": api_key
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            resources = (
                data.get("resourceSets", [{}])[0]
                .get("resources", [])
            )
            if not resources:
                messagebox.showinfo("Not Found", "No results found for the location.")
                return
            result = resources[0]
            point = result.get("point", {}).get("coordinates", ["", ""])
            lat, lon = str(point[0]), str(point[1])
            display_name = result.get("name", "")
            self.lat_entry.delete(0, tk.END)
            self.lat_entry.insert(0, lat)
            self.lon_entry.delete(0, tk.END)
            self.lon_entry.insert(0, lon)
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, display_name)
            messagebox.showinfo("Success", f"Location found:\n{display_name}\nLatitude: {lat}\nLongitude: {lon}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to look up location: {e}")

    def update_coordinates(self):
        if not self.selected_group_id:
            messagebox.showwarning("Warning", "No group selected.")
            return
        try:
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            desc = self.desc_entry.get()
            elevation = self.elevation_entry.get()
            location = self.location_entry.get()
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("Invalid coordinate range")
            # Use the API to update coordinates
            group_name = self.tree.item(self.selected_group_id, "text")
            self.api_client.update_group_coordinates(
                self.selected_group_id, lon, lat, group_name, elevation, location_desc=location
            )
            # Update the tree view
            self.tree.set(self.selected_group_id, "Latitude", str(lat))
            self.tree.set(self.selected_group_id, "Longitude", str(lon))
            messagebox.showinfo("Success", "Coordinates updated.")
        except Exception as e:
            self.show_error_with_copy("Failed to update coordinates", str(e))

    def show_error_with_copy(self, title, message):
        # Custom error dialog with copy-to-clipboard
        import tkinter as tk
        from tkinter import Toplevel, Text, Button, Scrollbar, RIGHT, Y, END, LEFT, BOTH, X

        dialog = Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("700x400")
        dialog.grab_set()

        text = Text(dialog, wrap="word")
        text.insert(END, message)
        text.config(state="disabled")
        text.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

        scrollbar = Scrollbar(dialog, command=text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        text.config(yscrollcommand=scrollbar.set)

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(message)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=X, padx=10, pady=5)
        Button(btn_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Close", command=dialog.destroy).pack(side=RIGHT, padx=5)

    def create_map_preview_section(self):
        map_frame = ttk.LabelFrame(self.root, text="Map Preview")
        map_frame.pack(padx=10, pady=10, fill="x")
        ttk.Button(map_frame, text="View in Browser", command=self.open_map_browser).pack(pady=10)

    def open_map_browser(self):
        try:
            import folium
            import webbrowser
            
            # Gather all groups from the tree
            groups = []
            group_dict = {}  # Map group IDs to coordinates and names
            group_name_to_id = {}  # Map group names to IDs
            
            for item in self.tree.get_children():
                vals = self.tree.item(item, "values")
                name = self.tree.item(item, "text")
                group_id = vals[0]
                lat = vals[1]
                lon = vals[2]
                
                if lat and lon:
                    try:
                        lat_f = float(lat)
                        lon_f = float(lon)
                        groups.append({"id": group_id, "name": name, "lat": lat_f, "lon": lon_f})
                        group_dict[group_id] = {"name": name, "lat": lat_f, "lon": lon_f}
                        group_name_to_id[name] = group_id
                    except Exception:
                        continue
                        
            if not groups:
                messagebox.showwarning("Warning", "No groups with coordinates to display.")
                return
                
            # Center map on first group
            m = folium.Map(location=[groups[0]["lat"], groups[0]["lon"]], zoom_start=4)
            
            # Add markers for all groups
            for g in groups:
                folium.Marker(
                    [g["lat"], g["lon"]],
                    popup=g["name"],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
            
            # Add connections based on interface ConnectsTo data
            if hasattr(self, 'interfaces') and self.interfaces:
                # Use a dictionary to track connections and their interfaces
                connections = {}  # {(source_id, dest_id): [interface_info, ...]}
                
                for iface in self.interfaces:
                    source_group_name = iface["group_name"]
                    dest_group_name = iface["connects_to"]
                    interface_name = iface["interface_name"]
                    
                    # Only record connection if both groups exist and have coordinates
                    if (source_group_name and dest_group_name and 
                        source_group_name in group_name_to_id and 
                        dest_group_name in group_name_to_id):
                        
                        source_id = group_name_to_id[source_group_name]
                        dest_id = group_name_to_id[dest_group_name]
                        
                        # Sort IDs to ensure consistent keys
                        connection_key = tuple(sorted([source_id, dest_id]))
                        
                        # Store interface info for the tooltip
                        if connection_key not in connections:
                            connections[connection_key] = []
                        
                        # Add interface details 
                        connections[connection_key].append({
                            "source_name": source_group_name,
                            "dest_name": dest_group_name,
                            "interface_name": interface_name
                        })
                
                # Now create polylines with appropriate thickness and tooltips
                for connection_key, interfaces in connections.items():
                    # Determine source and destination
                    source_id, dest_id = connection_key
                    source = group_dict[source_id]
                    dest = group_dict[dest_id]
                    
                    # Create list of interface descriptions for tooltip
                    interface_list = [f"{iface['interface_name']}: {iface['source_name']} → {iface['dest_name']}" 
                                    for iface in interfaces]
                    
                    # Build a multiline tooltip
                    tooltip_html = f"""
                    <div style="font-family: Arial; max-width: 300px;">
                        <h4>Connection Details</h4>
                        <p><b>Groups:</b> {source['name']} ↔ {dest['name']}</p>
                        <p><b>Interfaces ({len(interfaces)}):</b></p>
                        <ul style="padding-left: 15px;">
                            {"".join([f"<li>{iface}</li>" for iface in interface_list])}
                        </ul>
                    </div>
                    """
                    
                    # Adjust line thickness based on number of interfaces (min 2, max 8)
                    line_weight = min(2 + len(interfaces), 8)
                    
                    # Add the connection as a polyline with HTML tooltip
                    folium.PolyLine(
                        locations=[[source["lat"], source["lon"]], [dest["lat"], dest["lon"]]],
                        color='red',
                        weight=line_weight,
                        opacity=0.7,
                        tooltip=folium.Tooltip(tooltip_html)
                    ).add_to(m)
            
            m.save("map_preview.html")
            webbrowser.open("map_preview.html")
        except ImportError:
            messagebox.showerror("Error", "Folium library required for map preview")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate map: {e}")
