# Message Subscription

## When To Use

Read this file when adding:

- a subscription center page
- publish-success subscription prompts
- order or payment follow-up subscriptions
- chat message notification prompts
- subscription status indicators

## Core Model

- Keep a configurable map of subscription keys to WeChat template ids.
- Keep status loading and authorization requests inside one subscription hook or helper.
- Query current status from the backend when the app needs to show remaining counts or rejected state.
- Report authorization results back to the backend after each request.

## Request Rules

- Never request more than three template ids in a single `uni.requestSubscribeMessage` call.
- Batch longer flows into groups of three or fewer.
- Reload status after each batch.

## Rejection Flow

- If the request result contains rejection, guide the user to settings.
- Use `openSetting` with subscription support when the platform supports it.
- Refresh subscription status after the settings round trip.

## Good Trigger Points

- after publish success for content that can receive comments or replies
- after successful payment for order, delivery, or draw-result updates
- inside chat when the user wants unread message reminders
- on a dedicated subscription center page

## Configuration Rules

- Keep template ids configurable.
- Do not hardcode project-specific template ids as universal conventions.
- Keep channel grouping and copywriting local to the product.

## Existing Code Boundary

- Do not retrofit old flows with subscription prompts unless the user asked for that change.
- Apply subscription guidance to new flows or user-requested modifications only.
