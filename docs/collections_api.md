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
