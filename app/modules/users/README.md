# Administrative user management (OICO-61, OICO-62 and OICO-63)

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

## Administrative updates (OICO-62 and OICO-63)

All PATCH operations require the real `user:manage` permission and resolve the
restaurant from the authenticated account. Missing or foreign users return 404.
An administrator cannot modify a superadministrator account. Responses use
`UserRead` and never expose passwords, hashes or token versions.

| Endpoint | Body | Behavior |
| --- | --- | --- |
| PATCH /api/v1/users/{user_id} | Optional name, email, phone_number, password | Preserve omitted fields; hash supplied passwords; normalize email |
| PATCH /api/v1/users/{user_id}/role | role_id | Replace the single role with one from the same restaurant |
| PATCH /api/v1/users/{user_id}/status | is_active | Activate or deactivate without deleting the user or history |

Profile updates reject unknown or protected fields. Explicit null is allowed only
for phone_number. Other input restrictions match creation. An empty profile PATCH
preserves the account. Duplicate email returns 409 and rejects all supplied changes.
The update locks and reloads the scoped user before mutation and commits atomically.

Every request to change the caller's own role returns 403, including the same role.
Assigning superadministrator returns 403. A missing or foreign role returns 404.
Repeating the target's existing role or status does not increment token_version.

Changing email, role or status increments token_version. Supplying a password
also increments it, even when the supplied password matches the previous one.
Name and phone changes preserve sessions. User inactivation preserves reservations
and their author references, rejects login and rejects existing access tokens.
Reactivation requires a new login and never restores previous tokens.

## JWT compatibility

Login now emits token_version from the stored account. Authentication requires
that version to be a nonnegative integer matching the account, resolves the user
by user_id and checks the email subject. This prevents an old email token from
identifying another account if the address is later reused.

Existing tokens without token_version return 401: users must sign in again after
deployment. No database migration is needed for this feature because the shared
User model already has token_version. The shared token encoder remains unchanged;
tests constructing valid tokens supply the current version explicitly.

`tests/modules/users/test_user_updates.py` covers partial updates, revocation,
protected roles and accounts, atomic rejection, history preservation and status
idempotency with real JWTs and PostgreSQL. Gherkin scenarios remain descriptive.

## Remaining HU-AUT-06 work

Physical deletion and general administrative audit logging remain outside this
delivery. Password recovery, public registration and logout are not implemented
by these subtasks. This implementation does not complete all of HU-AUT-06.
