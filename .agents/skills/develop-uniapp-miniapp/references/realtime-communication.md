# Realtime Communication

## When To Use

Read this file when adding or modifying:

- chat
- unread counters
- live notifications
- presence indicators
- push-plus-polling flows

## Recommended Shape

- One app-level WebSocket manager.
- One or more page-level hooks that bind typed handlers.
- Optional store for shared unread state.
- Optional polling fallback for state that must refresh even if push events are missed.

## WebSocket Manager Responsibilities

- connect
- disconnect
- reconnect with backoff or bounded retries
- heartbeat or ping/pong
- event subscription and unsubscription
- connection-status inspection

## Page Binding Rules

- Bind handlers on `onShow`.
- Unbind on `onHide` and `onUnload`.
- Keep handler registration close to the page or hook that owns the UI response.
- Prefer typed message conversion before rendering.

## Chat Page Split

Keep these concerns separate:

- conversation detail loading
- message pagination
- local optimistic send state
- input and panel state
- scroll anchoring
- media upload and send
- realtime event binding

## Fallback Strategy

- Use polling only for critical summary state such as unread counts when the backend does not push every state transition.
- Keep polling intervals conservative.
- Stop polling when the app is backgrounded if the state can wait.

## Existing Code Boundary

- Do not force a repo to adopt realtime primitives if it already uses a different stable pattern.
- Reuse the current manager and handler shape whenever possible.
