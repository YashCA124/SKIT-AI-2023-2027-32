from marshmallow import Schema, fields, pre_load


class AdminLoginRequest(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True, load_only=True)


class UserLoginRequest(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    latitude = fields.Float(allow_none=True, load_default=None)
    longitude = fields.Float(allow_none=True, load_default=None)

    @pre_load
    def strip_strings(self, data, **kwargs):
        if isinstance(data, dict):
            return {
                key: value.strip() if isinstance(value, str) else value
                for key, value in data.items()
            }
        return data


class RegistrationRequest(Schema):
    name = fields.String(required=True)
    email = fields.Email(required=True)
    phone_no = fields.String(required=True)
    password = fields.String(required=True, load_only=True)
    city = fields.String(allow_none=True, load_default=None)
    state = fields.String(allow_none=True, load_default=None)
    country = fields.String(allow_none=True, load_default=None)
    address = fields.String(allow_none=True, load_default=None)
    pincode = fields.String(allow_none=True, load_default=None)
    location_permission_granted = fields.Boolean(load_default=False)
    latitude = fields.Float(allow_none=True, load_default=None)
    longitude = fields.Float(allow_none=True, load_default=None)


class TokenResponse(Schema):
    access_token = fields.String(required=True)


class LocationOut(Schema):
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)


class UserOut(Schema):
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    role = fields.String(required=True)


class LoginResponse(Schema):
    message = fields.String(required=True)
    access_token = fields.String(required=True)
    refresh_token = fields.String(required=True)
    user = fields.Nested(UserOut, required=True)


class UserLoginResponse(LoginResponse):
    location_updated = fields.Boolean(required=True)
    current_location = fields.Nested(LocationOut, allow_none=True, load_default=None)
