import re


class Validate:
    def __init__(self):
        pass

    def validate_user_id(self, user):
        pattern = r'^[a-zA-Z]+-[a-zA-Z]+-[0-9a-zA-Z]+$'
        return re.match(pattern, user) is not None

    def validate_national(self, data):
        pattern = r'^[a-zA-Z]+-[0-9]+$'
        return re.match(pattern, data)

    def validate_state(self, data):
        pattern = r'^[a-zA-Z]+-[0-9]+-[a-zA-Z]+$'
        return re.match(pattern, data)

    def validate_region(self, data):
        pattern = r'^[a-zA-Z]+-[0-9]+-[a-zA-Z]+-[a-zA-Z]+$'
        return re.match(pattern, data)

    def validate_group(self, data):
        pattern = r'^[a-zA-Z]+-[0-9]+-[a-zA-Z]+-[a-zA-Z]+-[a-zA-Z]+$'
        return re.match(pattern, data)

    def validate_location(self, data):
        pattern = r'^[a-zA-Z]+-[0-9]+-[a-zA-Z]+-[a-zA-Z]+-[a-zA-Z]+-[0-9]+$'
        return re.match(pattern, data)

