# API error responses

Every API response with an HTTP status from `400` to `599` uses this envelope:

```json
{
  "code": "EMAIL_ALREADY_USED",
  "detail": "Cet adresse email est déjà associée à un compte Niyya Women."
}
```

`code` is a stable machine-readable identifier. `detail` contains the human-readable message, structured validation errors, and any related metadata (such as `locked_until`).

## Codes

| Key | Meaning |
| --- | --- |
| `EMAIL_ALREADY_USED` | An email address is already attached to an account. |
| `EMAIL_ALREADY_VERIFIED` | The email address is already verified. |
| `EMAIL_NOT_ASSOCIATED` | The account has no email address. |
| `USERNAME_ALREADY_USED` | A username is already attached to an account. |
| `INVALID_CREDENTIALS` | Credentials or password input were rejected. |
| `ACCOUNT_LOCKED` | The account is temporarily locked; `detail` also includes `locked_until`. |
| `INVALID_OR_EXPIRED_CODE` | A verification or reset code is missing, invalid, or expired. |
| `VERIFICATION_ALREADY_PENDING` | An identity verification request is already pending. |
| `IDENTITY_ALREADY_VERIFIED` | The identity has already been approved. |
| `COMPANY_NOT_FOUND` | The requested company does not exist for the operation. |
| `COMPANY_ALREADY_EXISTS` | The account already owns a company. |
| `CONFIRMATION_REQUIRED` | A destructive operation needs explicit confirmation. |
| `REJECTION_REASON_REQUIRED` | A reason must be supplied when rejecting identity verification. |
| `RESOURCE_NOT_FOUND` | The requested resource does not exist. |
| `ACTION_NOT_ALLOWED` | The requested action is not allowed for this account or resource. |
| `VALIDATION_ERROR` | Request data failed validation. `detail` contains the field errors. |
| `AUTHENTICATION_REQUIRED` | Authentication is missing or invalid (HTTP 401). |
| `PERMISSION_DENIED` | The authenticated account lacks permission (HTTP 403). |
| `RESOURCE_CONFLICT` | The request conflicts with the current resource state (HTTP 409). |
| `TOO_MANY_REQUESTS` | The request was rate limited (HTTP 429). |
| `INTERNAL_SERVER_ERROR` | The server returned an HTTP 5xx error. |
| `REQUEST_ERROR` | An error status without a more specific code. |

Some authentication errors retain their established keys, including `ACCOUNT_DEACTIVATED` and `ACCOUNT_BANNED`.
