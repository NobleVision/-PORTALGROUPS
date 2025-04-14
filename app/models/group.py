class Group:
    def __init__(self, id, name, latitude=None, longitude=None, elevation=None, location_desc=None, subgroups=None):
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.location_desc = location_desc
        self.subgroups = subgroups if subgroups is not None else []

    def __repr__(self):
        return f"<Group id={self.id} name={self.name} lat={self.latitude} lon={self.longitude}>"
