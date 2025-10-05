# API Documentation for Voice Picker Backend

## Worker Endpoints

### Create Worker
- **POST** `/workers`
- **Body:**
  - `name` (str, required)
  - `team_id` (int, optional)
  - `pin` (int, required)
  - `voice_ref` (str, optional)
  - `role` (str, optional, default: 'picker')
- **Response:** Worker object
- **Description:** Creates a new worker. If `team_id` or `pin` are not provided, they are auto-assigned.

### Get All Workers
- **GET** `/workers`
- **Query:** `team_id` (int, optional)
- **Response:** List of Worker objects
- **Description:** Returns all workers, optionally filtered by team.

### Get Worker by ID
- **GET** `/workers/{worker_id}`
- **Response:** Worker object
- **Description:** Returns a worker by their ID.

### Update Worker by ID
- **PATCH** `/workers/{worker_id}`
- **Body:** Any updatable worker fields
- **Response:** Updated Worker object
- **Description:** Updates a worker by their ID.

### Delete Worker by ID
- **DELETE** `/workers/{worker_id}`
- **Response:** None
- **Description:** Deletes a worker by their ID.

### Get Worker by Pin
- **GET** `/workers/pin/{pin}`
- **Response:** Worker object
- **Description:** Returns a worker by their pin.

### Update Worker by Pin
- **PATCH** `/workers/pin/{pin}`
- **Body:** Any updatable worker fields
- **Response:** Updated Worker object
- **Description:** Updates a worker by their pin.

### Delete Worker by Pin
- **DELETE** `/workers/pin/{pin}`
- **Response:** None
- **Description:** Deletes a worker by their pin.

### Login
- **POST** `/login`
- **Body:**
  - `name` (str, required)
  - `pin` (int, required)
- **Response:** `{ "token": <token> }`
- **Description:** Authenticates a worker and returns a token.

---

## Config Endpoints

### Get Config
- **GET** `/config`
- **Response:**
  - `team_size_cap` (int)
  - `pin_min` (int)
  - `pin_max` (int)
- **Description:** Returns current system configuration values.

### Update Config
- **PATCH** `/config`
- **Body:** Any of:
  - `team_size_cap` (int)
  - `pin_min` (int)
  - `pin_max` (int)
- **Response:** Confirmation and updated values
- **Description:** Updates system configuration values.

---

## Notes
- All endpoints return errors in standard FastAPI format.
- Extend config endpoints for more settings as needed.
- All endpoints are ready for dashboard or frontend integration.
