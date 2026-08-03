# Auth And Transport

For early-stage apps or complete feature slices, read `mature-miniapp-patterns.md` before adding a new request/session path so transport, stores, and page-level API modules remain coherent.

## Layering

- Keep endpoint definitions in `api`.
- Keep session lifecycle in a session store.
- Keep the request pipeline in a request client or low-level util.
- Keep page code free from repeated header, retry, token, or loading logic.

## Recommended Flow

1. Acquire a platform login credential if the app uses silent login.
2. Exchange that credential for a session token or session payload.
3. Persist token and profile in the session store.
4. Route all authenticated requests through one request client.

## Request Client Responsibilities

- prepend the base URL
- inject auth headers when needed
- optionally run a preflight such as handshake or client readiness
- show and hide loading when explicitly requested
- normalize error extraction
- handle 401 retries without duplicating refresh logic across pages

## 401 Strategy

- Use a single in-flight refresh or re-login gate.
- Queue concurrent retries behind that gate.
- Retry the original request at most once after refresh.
- Clear invalid auth state if refresh fails.

## Optional Security Layers

These are project choices, not universal rules:

- handshake before protected requests
- signed headers
- client id and client secret
- nonce and timestamp
- environment-only debug headers
- banned-user handling

Keep them configurable and do not hardcode them as universal conventions.

## Upload

- Use `uni.uploadFile` for file uploads.
- Reuse the same auth context as normal requests.
- Keep upload response parsing in one helper.
- Separate media picking from actual upload orchestration.

## Existing Code Boundary

- Do not replace an existing request client unless the user asked for that refactor.
- Extend the current transport layer in place when possible.
