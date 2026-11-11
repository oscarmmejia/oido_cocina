# Administrative user listing and creation (OICO-61)

GET and POST `/api/v1/users` reuse the canonical `User` and `Role` models,
Pydantic schemas and shared services. Both operations require JWT authentication
and the real `user:manage` permission. Restaurant scope comes from the persisted
authenticated user, rather than a restaurant identifier selected by the client.

## API contract

| Method | Input | Success |
| --- | --- | --- |
| GET /api/v1/users | Query parameters `page` and `page_size` | 200 with `items`, `total`, `page` and `page_size` |
| POST /api/v1/users | `name`, `email`, `password`, `role_id`; optional `phone_number` | 201 with public user fields |

GET starts at page 1 with 20 users per page. Page and page size must be positive
integers; maximum page size is 100. Unknown query parameters, including
`restaurant_id`, return 422 through the existing pagination schema.

Results include active and inactive users from the authenticated restaurant,
ordered by user ID. The total uses the same restaurant scope as the results.
A page beyond the results returns an empty `items` list while preserving the total.

Example GET response for an account with no other restaurant users:

```json
{
  "items": [
    {
      "id": 1,
      "restaurant_id": 1,
      "role_id": 1,
      "name": "Manager",
      "email": "manager@example.com",
      "phone_number": null,
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

The example IDs are illustrative; role IDs do not grant permissions automatically.

POST requires an existing role from the authenticated restaurant. A role belonging
to another restaurant or a missing role returns 404. Assigning the shared
superadministrator role returns 403. Unknown and protected body fields, such as
`restaurant_id`, `is_active` or `password_hash`, return 422.

Emails are normalized to lowercase. The shared `uq_users_email_lower` PostgreSQL
index enforces global case-insensitive uniqueness, including across restaurants.
An email collision returns 409 with no insert. Passwords use the shared
`app.core.passwords.hash_password` helper and work with the integrated login.

Both operations expose only `id`, `restaurant_id`, `role_id`, `name`, `email`,
`phone_number` and `is_active`. Passwords, hashes, token versions and tokens are
excluded. Missing, invalid, expired or inactive authentication returns 401; missing
permission or invalid restaurant association returns 403. Errors use the shared
`ErrorResponse` envelope. Swagger at `/docs` documents responses and query limits.

Business error messages produced by the users service are in Spanish. Error
codes, JSON keys and permission names remain unchanged. Some authentication and
permission errors still use English messages from shared infrastructure; those
modules are not translated or overridden by this feature.

## Routing and service responsibilities

`app/modules/users/routes/` exposes the existing POST router from
`app/api/users.py` and adds GET. The application registers this router once.
The existing POST delegates through its existing controller to `create_user`;
GET delegates directly to `list_users`. No duplicate creation implementation
or alternative authentication is introduced.

The services take a previously authorized restaurant ID. They implement scoped
queries, pagination, validation, hashing and transaction handling; they do not
authenticate requests. Callers must use the shared identity and permission checks.

## Verification

`tests/modules/users/test_user_routes.py` exercises the API using real JWT login
and the real permission checker. It covers listing, defaults, pagination,
restaurant isolation, public fields, creation, duplicate email, invalid inputs,
401 and 403, plus the OpenAPI contract and one route per operation.
Existing `tests/test_auth_integration.py` also covers cross-restaurant roles and
superadministrator creation rejection.

Schema and service tests remain in `tests/modules/users/`. The Gherkin file
`tests/features/users.feature` documents acceptance scenarios in Spanish using
the `# language: es` directive; it is not executed
by a BDD runner.

Run tests only against the local disposable PostgreSQL database
`oido_cocina_test`, with no fallback to development. Exclude
`tests/database/test_migrations.py` when migrations are not authorized. No new
models, tables, environment variables or migrations are required by OICO-61.

## Remaining HU-AUT-06 work

OICO-61 provides listing and creation. User profile updates, role and status
changes, logical deactivation, physical deletion and administrative audit logging
belong to other subtasks. This implementation does not complete all of HU-AUT-06.
