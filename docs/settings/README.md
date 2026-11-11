# Restaurant settings API examples

These examples document GET and PATCH `/api/v1/settings`. Swagger UI is available
at `/docs` and the OpenAPI document at `/openapi.json` on the API server.

## Prerequisites and authentication

Use an API instance explicitly configured for a disposable test environment
(`oido_cocina_test`), with an existing active account associated with a restaurant.
PATCH requires the persisted `settings:update` permission. GET requires a valid
authenticated restaurant association. No permission overrides are needed.

The response examples assume restaurant 1 is named `Test restaurant` and initially
has the configuration in **Read settings**. Each update example starts from that
same initial configuration, independently of the other examples. Real restaurant
IDs, names and current values may differ.

From PowerShell, authenticate without placing a password in the command history:

```powershell
$baseUrl = 'http://127.0.0.1:8000/api/v1'
$credential = Get-Credential
$login = Invoke-RestMethod -Method Post -Uri "$baseUrl/auth/login" -ContentType 'application/x-www-form-urlencoded' -Body @{
    username = $credential.UserName
    password = $credential.GetNetworkCredential().Password
}
$headers = @{ Authorization = "Bearer $($login.access_token)" }
```

Do not print or commit credentials or tokens. The base URL must identify the
intended test instance; these requests modify the signed-in user's restaurant.

To read settings:

```powershell
Invoke-RestMethod -Method Get -Uri "$baseUrl/settings" -Headers $headers | ConvertTo-Json -Depth 5
```

To execute any PATCH example below, save its **Request body** JSON to a temporary
file outside the repository, then use its path:

```powershell
$requestPath = Read-Host 'Path to the request JSON file'
try {
    Invoke-RestMethod -Method Patch -Uri "$baseUrl/settings" -Headers $headers -ContentType 'application/json' -InFile $requestPath | ConvertTo-Json -Depth 5
} catch {
    $_.ErrorDetails.Message
}
```

Successful requests return HTTP 200. Invalid request fields and invalid resulting
schedules return HTTP 422, using the existing shared error contract. Error messages
below preserve the API's current language.

## Fields and schedule rules

PATCH accepts only `time_zone`, `courtesy_minutes`, `slot_minutes`,
`min_break_between_shifts`, `day_of_week`, `period`, `open_time`, `close_time`
and `kitchen_close_time`. The full GET response also contains read-only fields:
`id`, `name`, `is_active` and `direction`. Do not send those fields or
`restaurant_id` in PATCH. Unknown fields return 422.

Omitted fields are preserved. Explicit null is accepted for
`min_break_between_shifts`, `day_of_week`, `period` and the three time fields.
It is rejected for `time_zone`, `courtesy_minutes` and `slot_minutes`.
Courtesy must be nonnegative and `slot_minutes`, the default reservation duration,
must be positive. Minimum break is nonnegative when present; day of week is 1–7
when present. Time zone and period retain their existing model length limits.

There is one schedule in `Restaurant`, with no split periods or separate hours
table. A closing time earlier than opening belongs to the following day.
Opening and closing cannot be equal: continuous 24-hour operation is unsupported.
The kitchen cannot close after the restaurant; there is no mandatory 30-minute
margin. Nullable times remain allowed. Without an opening time, the two closing
times are compared within the same day; without a closing time, the existing
service does not compare the closing times.

PATCH validates the combination of sent and stored values before saving. Invalid
requests leave all fields unchanged, including otherwise valid fields in the same
request. A query parameter or token restaurant claim does not select a different
restaurant: scope comes from the persisted authenticated user.

## Read settings

GET `/api/v1/settings`.

### Response: 200

```json
{
  "id": 1,
  "name": "Test restaurant",
  "time_zone": "Europe/Madrid",
  "is_active": true,
  "courtesy_minutes": 5,
  "slot_minutes": 60,
  "min_break_between_shifts": 30,
  "day_of_week": 5,
  "period": "evening",
  "open_time": "12:00:00",
  "close_time": "23:00:00",
  "kitchen_close_time": "22:00:00",
  "direction": "Example address"
}
```

## Complete update

PATCH `/api/v1/settings`. The response includes the complete settings, including preserved fields.

### Request body

```json
{
  "time_zone": "Europe/Madrid",
  "courtesy_minutes": 10,
  "slot_minutes": 90,
  "min_break_between_shifts": 30,
  "day_of_week": 5,
  "period": "evening",
  "open_time": "20:00:00",
  "close_time": "03:00:00",
  "kitchen_close_time": "02:00:00"
}
```

### Response: 200

```json
{
  "id": 1,
  "name": "Test restaurant",
  "time_zone": "Europe/Madrid",
  "is_active": true,
  "courtesy_minutes": 10,
  "slot_minutes": 90,
  "min_break_between_shifts": 30,
  "day_of_week": 5,
  "period": "evening",
  "open_time": "20:00:00",
  "close_time": "03:00:00",
  "kitchen_close_time": "02:00:00",
  "direction": "Example address"
}
```

## Partial update

PATCH `/api/v1/settings`. The response includes the complete settings, including preserved fields.

### Request body

```json
{
  "courtesy_minutes": 10
}
```

### Response: 200

```json
{
  "id": 1,
  "name": "Test restaurant",
  "time_zone": "Europe/Madrid",
  "is_active": true,
  "courtesy_minutes": 10,
  "slot_minutes": 60,
  "min_break_between_shifts": 30,
  "day_of_week": 5,
  "period": "evening",
  "open_time": "12:00:00",
  "close_time": "23:00:00",
  "kitchen_close_time": "22:00:00",
  "direction": "Example address"
}
```

## Overnight update

PATCH `/api/v1/settings`. The response includes the complete settings, including preserved fields.

### Request body

```json
{
  "open_time": "20:00:00",
  "close_time": "03:00:00",
  "kitchen_close_time": "02:00:00"
}
```

### Response: 200

```json
{
  "id": 1,
  "name": "Test restaurant",
  "time_zone": "Europe/Madrid",
  "is_active": true,
  "courtesy_minutes": 5,
  "slot_minutes": 60,
  "min_break_between_shifts": 30,
  "day_of_week": 5,
  "period": "evening",
  "open_time": "20:00:00",
  "close_time": "03:00:00",
  "kitchen_close_time": "02:00:00",
  "direction": "Example address"
}
```

## Negative courtesy

PATCH `/api/v1/settings`. The entire request is rejected; the initial settings are preserved.

### Request body

```json
{
  "courtesy_minutes": -1
}
```

### Response: 422

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Los datos enviados no son válidos."
  }
}
```

## Equal opening and closing

PATCH `/api/v1/settings`. The entire request is rejected; the initial settings are preserved.

### Request body

```json
{
  "open_time": "20:00:00",
  "close_time": "20:00:00",
  "courtesy_minutes": 10
}
```

### Response: 422

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "La hora de cierre debe ser posterior a la apertura; no pueden coincidir."
  }
}
```

## Kitchen closes too late

PATCH `/api/v1/settings`. The entire request is rejected; the initial settings are preserved.

### Request body

```json
{
  "open_time": "20:00:00",
  "close_time": "03:00:00",
  "kitchen_close_time": "04:00:00",
  "courtesy_minutes": 10
}
```

### Response: 422

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "El cierre de cocina no puede ser posterior al cierre del local."
  }
}
```

## Verification and other errors

`tests/test_settings_routes.py` extracts the JSON request and response blocks from
these sections and executes the requests through the API's TestClient, using real
JWT login and PostgreSQL `oido_cocina_test`. It verifies status codes, response
bodies, persisted settings and rejection without partial changes. It also checks
that OpenAPI publishes the same examples. This verifies the HTTP examples; it
does not execute the PowerShell commands or use a live network server.

Missing, invalid or expired authentication returns 401. Missing PATCH permission
or an invalid restaurant association returns 403. A missing restaurant returns
404. Unexpected server errors use the shared 500 response. These errors are
documented in OpenAPI and covered where applicable by the existing API tests.

No new tables, configuration variables or migrations are needed for these
examples. Do not run migrations as part of this verification.
