
## Endpoints for the next routes:

| Operation        | Method | URL          | Description                                                      |
|------------------|--------|--------------|------------------------------------------------------------------|
| `list`           | GET    | `/route/`    | Retrieves a list of all available resourses                      |
| `retrieve`       | GET    | `/route/id/` | Retrieves information about specific resource <br>identified by `id` |
| `create`         | POST   | `/route/`    | Creates a new resource                                           |
| `update`         | PUT    | `/route/id/` | Updates an existing resource identified by `id`                  |
| `partial update` | PATCH  | `/route/id/` | Partially updates an existing resource identified by `id`        |
| `destroy`        | DELETE | `/route/id/` | Deletes an existing resource identified by its `id`              |


### /api/users/

### /api/groups/

### /api/permissions/ 

_Query parameters_:
> `search`: filters permissions by name.

_Example_:
```
GET /api/permissions/?search=course
```

### /api/partners/ 

For teachers and owners queryset is already filtered to only show their partners.

_Query parameters_:
> `search`: filters partners by name or legal entity. <br>
> `status`: filters partners by their status. <br>
> `date`: filters partners by the date.

_Example_:
```
GET /api/partners/?search=Партнер 1&status=active&date=2020-01-02
```

### /api/employees/ 

For teachers and owners queryset is already filtered to only show their partner's employees.

_Query parameters_:
> `partner_id`: specific partner's employees to retrieve. <br>
> `course_id`: filters employees by the accessible course's id. <br>
> `search`: filters employees by user's first name, last name, patronymic or email. <br>
> `status`: filters employees by their status. <br>
> `group`: filters employees by their group membership.

_Example_:
```
GET /api/employees/?partner_id=1
GET /api/employees/?course_id=1
GET /api/employees/?search=Иван&status=active
```

### /api/branches/ 

For teachers and owners queryset is already filtered to only show their partner's branches.

_Query parameters_:
> `partner_id`: specific partner's branches to retrieve. <br>
> `search`: filters branches by name. <br>
> `status`: filters branches by their status. <br>
> `date`: filters branches by the opening dat

_Example_:
```
GET /api/branches/?search=Филиал 1&status=active&date=2020-12-11
```

### /api/courses/ 

For teachers queryset is already filtered to only show courses that they have access to.

_Query parameters_:
> `teacher`: filters courses by teacher id to ones that they have access to.
> `search`: filters courses by name. <br>
> `status`: filters courses by their status. <br>
> `category`: filters courses by category. <br>
> `age`: filters courses by age to ones where provided age is in the course's age range.

_Example_:
```
GET /api/courses/?search=Курс 1&age=12
```

### /api/categories/ 

### /api/lessons/ 

_Query parameters_:
> `course_id`: filters lessons by course id.

_Example_:
```
GET /api/lessons/?course_id=1
```

-----------------------
    
## Other routes:

### GET /api/user-group-permissions/
Authenticated Only.

Returns:

- 200 OK 
```
{
    "group_name": name of the user's group,
    "permissions": list of permissions of that group,
    "partner_id": partner's id that user belong to
}
```
- 404 Not Found (if user don't have a group)
```
{
    'error': 'User is not part of any group'
}
```

### POST /auth/token/
JWT Authorization.

After successful authorization stores the access and refresh tokens in cookies with the next settings:

- `httponly=True` <br>
- `secure=not settings.DEBUG`, cookies only sent over HTTPS in _production_ environment <br>
- `samesite='Strict'` <br>
- `expires`, lifetime of token <br>
- `path`, to divide when to send tokens where<br>
    - */api* - for access token to send it only to require access to data. <br>
    - */auth* - for refresh token to send it only to get a new access token and don't send it each request with all cookies.

ACCESS_TOKEN_LIFETIME = 5 minutes <br>
REFRESH_TOKEN_LIFETIME = 1 day <br>
(*settings.py - SIMPLE_JWT*)

Receives:

- email
- password

Returns:

- 200 OK 
```
Cookies example:
    access_token=jwt; Path=/api; Secure; HttpOnly; Expires=Wed, 22 May 2024 21:17:34 GMT;

    refresh_token=jwt; Path=/auth; Secure; HttpOnly; Expires=Thu, 23 May 2024 21:12:33 GMT;

Data:
{
    "detail": "Tokens set in cookies"
}
```
- 401 Unauthorized
```
{
    "detail": "No active account found with the given credentials"
}
```

### POST /auth/token/refresh/
Set in cookies a new _access token_ by _refresh token_ from cookies.

Returns:

- 200 OK
```
Cookies example:
    access_token=jwt; Path=/api; Secure; HttpOnly; Expires=Wed, 22 May 2024 21:17:34 GMT;

Data:
{
    "detail": "Tokens set in cookies"
}
```
- 401 Unauthorized
```
{
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
}
```

-------------------
### POST /api/session/login/
Session Authorization.

Receives:

- email
- password

Returns:

- 200 OK
```
{
    "message": "Login successful"
}
```
- 401 Unauthorized
```
{
    "error": "Invalid Credentials"
}
```

### POST /api/session/logout/
Session Logout.

Returns:

- 200 OK
```
{
    "message": "Logout successful"
}
```

