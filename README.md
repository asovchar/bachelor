# Recommender system

LightFM recommender system

## Requirements
- make
- docker
- docker-compose

## Building and running
> All CLI arguments of the script can be passed as env variables with `RECOMMENDER_` prefix.
> For example `--redis-url` parameter is equivalent to `RECOMMENDER_REDIS_URL` env variable.
> By the way, `--help` option is available for every command

```bash
make docker-run
```

## Usage

| Method | Endpoint                             | Description                            |
|--------|--------------------------------------|----------------------------------------|
| PUT    | `/items/{item_id}`                   | Create or replace item                 |
| GET    | `/items/{item_id}`                   | Get item                               |
| DELETE | `/items/{item_id}`                   | Delete item                            |
| PUT    | `/users/{user_id}`                   | Create or replace user                 |
| GET    | `/users/{user_id}`                   | Get user                               |
| DELETE | `/users/{user_id}`                   | Delete user                            |
| POST   | `/users/{user_id}/iteract/{item_id}` | Save interaction between user and item |
| GET    | `/users/{user_id}/history`           | Get interaction history for user       |
| GET    | `/users/{user_id}/recommendations`   | Get recommendations for user           |

### Examples

Create or replace item
```
PUT /items/1
{
    "feature_ids": [3, 4]
}
```
```
202: Accepted
```

Get item
```
GET /items/1
```
```
{
    "data": {
        "id": 1,
        "embedding": [...],
        "features": [
            {
                "id": 3,
                "description": "distributions",
                "embedding": [...]
            },
            {
                "id": 4,
                "descrption": "normality",
                "embedding": [...]
            }
        ]
    }
}
```

Delete post
```
DELETE /items/1
```

Create or replace user
```
PUT /users/1
```
```
202: Accepted
```

Get user
```
GET /users/1
```
```
{
    "data": {
        "id": 1,
        "embedding": null,
        "features": []
    }
}
```

Delete user
```
DELETE /users/1
```

Save user-to-item interaction
```
POST /users/1/interact/1
```
```
202: Accepted
```

Get interaction history for user
```
GET /users/1/history?limit=10
```
```
{
    "data": [
        {
            "id": 62688
        },
        {
            "id": 63529
        },
        ...
    ]
}
```

Get recommendation for user
```
GET /users/1/recommendations?limit=10
```
```
{
    "data": [
        {
            "id": 61825
        },
        {
            "id": 39719
        },
        ...
    ]
}
```
