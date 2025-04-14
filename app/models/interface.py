class Interface:
    def __init__(self, id, name, source_group=None, destination_group=None):
        self.id = id
        self.name = name
        self.source_group = source_group
        self.destination_group = destination_group

    def __repr__(self):
        return f"<Interface id={self.id} name={self.name} src={self.source_group} dst={self.destination_group}>"
