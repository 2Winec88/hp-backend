# Collections API

Base prefix: `/api/v1/collections/`.

## Endpoints

```http
GET /api/v1/collections/item-categories/
GET /api/v1/collections/item-categories/{id}/

GET    /api/v1/collections/user-items/
POST   /api/v1/collections/user-items/
GET    /api/v1/collections/user-items/{id}/
PATCH  /api/v1/collections/user-items/{id}/
DELETE /api/v1/collections/user-items/{id}/

GET    /api/v1/collections/collections/
POST   /api/v1/collections/collections/
GET    /api/v1/collections/collections/{id}/
PATCH  /api/v1/collections/collections/{id}/
DELETE /api/v1/collections/collections/{id}/

GET    /api/v1/collections/collection-items/
POST   /api/v1/collections/collection-items/
GET    /api/v1/collections/collection-items/{id}/
PATCH  /api/v1/collections/collection-items/{id}/
DELETE /api/v1/collections/collection-items/{id}/

GET    /api/v1/collections/branch-items/
POST   /api/v1/collections/branch-items/
GET    /api/v1/collections/branch-items/{id}/
PATCH  /api/v1/collections/branch-items/{id}/
DELETE /api/v1/collections/branch-items/{id}/

GET    /api/v1/collections/donor-groups/
POST   /api/v1/collections/donor-groups/
GET    /api/v1/collections/donor-groups/{id}/
PATCH  /api/v1/collections/donor-groups/{id}/
DELETE /api/v1/collections/donor-groups/{id}/

GET    /api/v1/collections/donor-group-members/
POST   /api/v1/collections/donor-group-members/
GET    /api/v1/collections/donor-group-members/{id}/
PATCH  /api/v1/collections/donor-group-members/{id}/
DELETE /api/v1/collections/donor-group-members/{id}/

GET    /api/v1/collections/donor-group-items/
POST   /api/v1/collections/donor-group-items/
GET    /api/v1/collections/donor-group-items/{id}/
PATCH  /api/v1/collections/donor-group-items/{id}/
DELETE /api/v1/collections/donor-group-items/{id}/

GET    /api/v1/collections/courier-profiles/
POST   /api/v1/collections/courier-profiles/
GET    /api/v1/collections/courier-profiles/{id}/
PATCH  /api/v1/collections/courier-profiles/{id}/
DELETE /api/v1/collections/courier-profiles/{id}/

GET    /api/v1/collections/meeting-place-proposals/
POST   /api/v1/collections/meeting-place-proposals/
GET    /api/v1/collections/meeting-place-proposals/{id}/
PATCH  /api/v1/collections/meeting-place-proposals/{id}/
DELETE /api/v1/collections/meeting-place-proposals/{id}/

GET    /api/v1/collections/polls/
POST   /api/v1/collections/polls/
GET    /api/v1/collections/polls/{id}/
PATCH  /api/v1/collections/polls/{id}/
DELETE /api/v1/collections/polls/{id}/
POST   /api/v1/collections/polls/{id}/repost/
POST   /api/v1/collections/polls/from-place-proposals/

GET    /api/v1/collections/poll-options/
POST   /api/v1/collections/poll-options/
GET    /api/v1/collections/poll-options/{id}/
PATCH  /api/v1/collections/poll-options/{id}/
DELETE /api/v1/collections/poll-options/{id}/

GET    /api/v1/collections/poll-votes/
POST   /api/v1/collections/poll-votes/
GET    /api/v1/collections/poll-votes/{id}/
PATCH  /api/v1/collections/poll-votes/{id}/
DELETE /api/v1/collections/poll-votes/{id}/
```

## Permissions

- Item categories: public read-only.
- User items: public read; authenticated users create their own items; only the owner updates or deletes.
- Collections: public read; active organization members create; the author or an active organization manager updates or deletes.
- Collection items: public read; the collection author or an active organization manager creates, updates, or deletes.
- Branch items: public read; only an active manager of the branch organization creates, updates, or deletes.
- Donor groups: public read; the collection author or an active organization manager creates, updates, or deletes.
- Donor group members: public read; the collection author or an active organization manager manages members. Accepting a donor group invitation also creates membership.
- Donor group items: public read; the collection author or an active organization manager links user items and selected quantities.
- Invitations: use `/api/v1/communications/invitations/` with `target_type = "donor_group"`.
- Courier profiles: public read; authenticated users create their own profile; only the owner updates or deletes.
- Meeting place proposals: public read; donor group members create proposals; the proposal author, collection author, or organization manager updates or deletes.
- Polls: public read; donor group polls are managed by the collection author or organization manager; news polls are managed by the news author or organization manager.
- Poll options: public read; only the corresponding poll manager creates, updates, or deletes options.
- Poll votes: authenticated users see and manage only their own votes; donor group polls accept votes only from donor group members.
- New open donor group polls create in-app notifications and push delivery tasks for donor group members.

## Payloads

User item:

```json
{
  "category": 1,
  "quantity": 2,
  "description": "Optional note"
}
```

Collection:

```json
{
  "organization": 1,
  "branch": 1,
  "geodata": 1,
  "title": "Winter help",
  "description": "Warm clothes and blankets",
  "status": "draft",
  "starts_at": "2026-06-01T10:00:00+05:00",
  "ends_at": "2026-06-30T18:00:00+05:00"
}
```

Collection item:

```json
{
  "collection": 1,
  "category": 1,
  "quantity_required": 10,
  "description": "5 liter bottles preferred"
}
```

Branch item:

```json
{
  "branch": 1,
  "category": 1,
  "description": "Accepted at this branch"
}
```

Donor group:

```json
{
  "collection": 1,
  "title": "Central pickup group"
}
```

Donor group invitation:

```json
{
  "target_type": "donor_group",
  "target_id": 1,
  "invited_user": 2,
  "send_email": false,
  "send_push": true
}
```

Donor group item:

```json
{
  "donor_group": 1,
  "user_item": 1,
  "quantity": 2
}
```

Courier profile:

```json
{
  "car_name": "Lada Largus"
}
```

Meeting place proposal:

```json
{
  "donor_group": 1,
  "geodata": 1,
  "street": "Lenina, 1",
  "description": "Main entrance"
}
```

Poll:

```json
{
  "donor_group": 1,
  "news": null,
  "title": "Pickup time",
  "description": "",
  "kind": "date",
  "status": "open",
  "closes_at": "2026-06-01T10:00:00+05:00"
}
```

`kind` values: `text`, `date`, `place`. `status` values: `draft`, `open`, `closed`.

Poll option:

```json
{
  "poll": 1,
  "text": "Saturday",
  "starts_at": "2026-06-06T12:00:00+05:00",
  "ends_at": null,
  "geodata": null,
  "place_street": "",
  "place_description": "",
  "sort_order": 0
}
```

For `text` polls, `text` is required. For `date` polls, `starts_at` is required. For `place` polls, provide at least one place field: `geodata`, `place_street`, or `place_description`.

Vote:

```json
{
  "poll": 1,
  "option": 1
}
```

Repost poll without zero-vote options:

```http
POST /api/v1/collections/polls/{id}/repost/
```

```json
{
  "title": "Pickup time, second round",
  "status": "open",
  "closes_at": "2026-06-02T10:00:00+05:00"
}
```

Create a place poll from donor group proposals:

```http
POST /api/v1/collections/polls/from-place-proposals/
```

```json
{
  "donor_group": 1,
  "title": "Meeting place",
  "description": "",
  "status": "open",
  "proposal_ids": [1, 2, 3]
}
```

If `proposal_ids` is omitted, all proposals from the donor group become poll options.
