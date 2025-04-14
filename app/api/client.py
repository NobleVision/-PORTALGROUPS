import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

# Suppress InsecureRequestWarning globally
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DXNetOpsAPIClient:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv("DX_NETOPS_HOST")
        self.username = os.getenv("DX_NETOPS_USERNAME")
        self.password = os.getenv("DX_NETOPS_PASSWORD")
        self.da_host = os.getenv("DX_DA_HOST")
        if not all([self.host, self.username, self.password]):
            raise ValueError("Missing DX NetOps credentials in environment variables.")

    def get_pc_id_from_da_id(self, da_id):
        url = f"{self.host}/pc/center/webservice/datasources/dataSourceId/3/itemids"
        headers = {"Content-Type": "application/xml"}
        body = f"""<LocalIDs>
  <LocalID ID="{da_id}"/>
</LocalIDs>"""
        response = requests.post(
            url,
            data=body,
            headers=headers,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=False
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
        item_id_elem = root.find(".//ItemIDResult")
        if item_id_elem is not None:
            return item_id_elem.attrib.get("ItemID")
        return None

    def get_group_info(self, pc_id):
        url = f"{self.host}/pc/center/webservice/groups/groupItemId/{pc_id}"
        response = requests.get(
            url,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=False
        )
        response.raise_for_status()
        return response.text

    def update_group_coordinates(self, pc_id, longitude, latitude, group_name, elevation=0, location_desc=""):
        """
        Update group coordinates using a POST request and longitude/latitude/location as attributes.
        Returns (response_text, debug_info) on error for debugging.
        """
        url = f"{self.host}/pc/center/webservice/groups/groupItemId/{pc_id}"
        headers = {"Content-Type": "application/xml"}
        # All fields as attributes, matching the working Postman example
        body = f"""<GroupTree path="/All Groups/WEATHERMAP">
  <Group version="1.0.0" name="{group_name}" type="site" desc="" longitude="{longitude}" latitude="{latitude}" elevation="{elevation}" location="{location_desc}" id="{pc_id}">
  </Group>
</GroupTree>"""
        try:
            response = requests.post(
                url,
                data=body,
                headers=headers,
                auth=HTTPBasicAuth(self.username, self.password),
                verify=False
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            debug_info = (
                f"\n--- DX NetOps REST Debug ---\n"
                f"Method: POST\n"
                f"URL: {url}\n"
                f"Headers: {headers}\n"
                f"Body:\n{body}\n"
                f"Status Code: {getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'}\n"
                f"Response Content:\n{getattr(e.response, 'text', str(e)) if hasattr(e, 'response') else str(e)}\n"
                f"---------------------------\n"
            )
            raise RuntimeError(f"{e}\n{debug_info}")

    def update_interface_connectsto(self, interface_id, connects_to):
        """
        Update the ConnectsTo field for an interface via the DA REST endpoint.
        """
        if not self.da_host:
            raise ValueError("Missing DA host in environment variables (DX_DA_HOST).")
        url = f"{self.da_host}/rest/ports/customattributes/{interface_id}"
        headers = {"Content-Type": "application/xml"}
        body = f"""<PortCustomAttributes version='1.0.0'>
    <ConnectsTo>{connects_to}</ConnectsTo>
</PortCustomAttributes>"""
        response = requests.put(
            url,
            data=body,
            headers=headers,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=False
        )
        response.raise_for_status()
        return response.text

    def fetch_interfaces_csv(self, da_id, start_time, end_time):
        """
        Fetch interface data for a group (DA ID) and time range from the OData API (CSV format).
        Returns a list of dicts, one per interface.
        """
        # OData URL2 as described in the user message
        url = (
            f"{self.host}/pc/odata/api/groups"
            "?$apply=groupby((portmfs/ID), aggregate(portmfs(im_Availability with average as Value, im_UtilizationIn with average as Value1, im_PctDiscards with average as Value2, im_PctErrors with average as Value3, im_UtilizationOut with average as Value4)))"
            "&$expand=interfaces"
            "&$select=ID,Name,Longitude,Latitude,LocationDesc,GroupPathLocation,interfaces/ID,interfaces/Name,interfaces/SpeedIn,interfaces/SpeedOut,interfaces/AlternateName,interfaces/ConnectsTo"
            f"&$filter=((substringof('{da_id}:', GroupPathLocationIDs) eq true) and (GroupType eq 'site'))"
            "&$format=text/csv"
            f"&starttime={start_time}&endtime={end_time}&resolution=HOUR&$top=500"
        )
        response = requests.get(
            url,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=False
        )
        response.raise_for_status()
        # Parse CSV
        import csv
        from io import StringIO
        csv_text = response.text
        reader = csv.DictReader(StringIO(csv_text))
        interfaces = []
        for row in reader:
            # Only include rows with an interface ID
            if row.get("interfaces/ID"):
                interfaces.append({
                    "group_id": row.get("ID"),
                    "group_name": row.get("Name"),
                    "interface_id": row.get("interfaces/ID"),
                    "interface_name": row.get("interfaces/Name"),
                    "connects_to": row.get("interfaces/ConnectsTo"),
                    "speed_in": row.get("interfaces/SpeedIn"),
                    "speed_out": row.get("interfaces/SpeedOut"),
                    "alternate_name": row.get("interfaces/AlternateName"),
                })
        return interfaces
