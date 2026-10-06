# Server-Side Vouch API

A lightweight **server-side vouch management system** that allows users to create, view, and rank vouches through **TagScript commands**.

The project demonstrates how a TagScript-based application can communicate with a remote API using TagScript's built-in `fetch` functionality. This allows the command layer to interact with persistent vouch data without requiring the Discord bot itself to maintain a traditional backend integration.

The system supports:

- Adding vouches for users
- Viewing a user's vouches
- Identifying users dynamically through mentions
- Validating user input
- Generating a vouch leaderboard
- Sending API requests directly from TagScript
- Separating command logic from API/data handling

---

## Architecture

The overall flow is:

```text
User
  │
  │ TagScript Command
  ▼
TagScript Processor
  │
  │ fetch()
  ▼
Vouch API
  │
  ├── Read vouches
  ├── Write vouches
  └── Generate leaderboard
  │
  ▼
Persistent Vouch Data
```

Instead of implementing the complete operation inside the Discord command itself, the TagScript layer acts as the **request interface**, while the API handles the underlying vouch operations.

This creates a simple separation between:

**TagScript → Request Construction → API → Data Operations → Response**

---

# TagScript

## What is TagScript?

**TagScript** is a lightweight templating and scripting language commonly used in Discord bots to create dynamic messages and commands.

Rather than writing a complete programming language implementation for every command, TagScript provides a collection of blocks that can perform operations such as:

- Reading arguments
- Accessing user information
- Conditional logic
- String manipulation
- Mathematical operations
- Variable assignment
- Stopping execution
- Making HTTP requests

This project makes extensive use of those capabilities to construct API requests dynamically.

For example:

```text
{user(id)}
```

can be used to retrieve a user's ID, while:

```text
{args(1)}
```

retrieves the first argument supplied to the command.

TagScript therefore acts as a lightweight command-processing layer on top of the API.

---

# API Integration Through TagScript

One of the main features of this project is the ability to communicate with the API directly from TagScript.

The implementation uses:

```text
{fetch:<URL>}
```

The `fetch` block performs an HTTP request to the specified API endpoint and returns the response.

For example:

```text
{fetch:https://vouch-api-a0hs.onrender.com/api?type=leaderboard}
```

This means the TagScript command does not need to manually implement an HTTP client.

The command can construct the required URL and allow the API to perform the actual operation.

This creates a lightweight architecture where:

```text
TagScript
    ↓
HTTP Request
    ↓
REST API
    ↓
Vouch Data
```

---

# Vouch API

The API provides the server-side interface for interacting with vouch data.

The primary endpoint is:

```text
/api
```

The behavior of the endpoint is controlled through query parameters.

For example:

```text
/api?user=123456&type=view
```

can be used to request vouch information for a particular user.

Similarly, an add operation can provide information about both the target user and the user submitting the vouch.

---

# Read and Write Implementation

The TagScript implementation is:

```text
{=(set_user):{target(id)}}

{=(target_clean):{replace(<@,):{replace(>,):{args(1)}}}}
{=(user_check):{math:{target_clean}*0}}

{stop({args(1)}==):Mention Someone}
{stop({user_check}!=0):Mention someone}

{=(set_type):{if({args(1)}==view):user={set_user}&type=view|user={set_user}&type=add&from={user(id)}}}
{=(final_type):{if({args(1)}==lb):type=leaderboard|{if({args(1)}==leaderboard):leaderboard|{set_type}}}}

{fetch:https://vouch-api-a0hs.onrender.com/api?{final_type}}
```

The implementation can be broken down into several stages.

---

## 1. Identifying the Target User

```text
{=(set_user):{target(id)}}
```

The first step is identifying the user that the command is operating on.

The `target` block resolves the target user, while:

```text
{target(id)}
```

extracts that user's ID.

The resulting value is stored in a TagScript variable:

```text
set_user
```

This variable can then be reused when constructing the API request.

Conceptually:

```text
Mentioned User
      ↓
target(id)
      ↓
set_user
      ↓
API user parameter
```

---

# 2. Cleaning the User Input

Discord mentions can be represented in a format similar to:

```text
<@123456789>
```

However, the API requires the underlying ID rather than the complete mention string.

The implementation therefore cleans the argument:

```text
{=(target_clean):{replace(<@,):{replace(>,):{args(1)}}}}
```

The nested `replace` operations remove the mention formatting.

For example:

```text
<@123456789>
```

becomes:

```text
123456789
```

This provides a clean value that can be used during validation.

---

# 3. Input Validation

The implementation then performs a lightweight validation check:

```text
{=(user_check):{math:{target_clean}*0}}
```

This uses TagScript's mathematical evaluation to determine whether the cleaned value can be processed as expected.

The command subsequently uses `stop` blocks:

```text
{stop({args(1)}==):Mention Someone}
```

and:

```text
{stop({user_check}!=0):Mention someone}
```

These prevent the API request from being executed when the required user argument is invalid.

The important idea is that invalid input is rejected **before an API request is made**.

---

# 4. Determining the Operation

The same command can perform different operations depending on the argument provided.

The implementation checks whether the first argument is:

```text
view
```

using:

```text
{=(set_type):{if({args(1)}==view):user={set_user}&type=view|user={set_user}&type=add&from={user(id)}}}
```

There are two possible paths.

### View

If the argument is:

```text
view
```

the generated request becomes:

```text
user=<target_id>&type=view
```

This tells the API to retrieve the vouch information associated with the target user.

### Add

Otherwise, the command constructs:

```text
user=<target_id>&type=add&from=<sender_id>
```

The `from` parameter is generated using:

```text
{user(id)}
```

which identifies the user executing the command.

This allows the API to distinguish between:

```text
Target user
```

and:

```text
User giving the vouch
```

---

# 5. Leaderboard Routing

The implementation also supports a leaderboard operation.

```text
{=(final_type):{if({args(1)}==lb):type=leaderboard|{if({args(1)}==leaderboard):leaderboard|{set_type}}}}
```

This checks for leaderboard-related arguments and changes the generated API query accordingly.

Instead of requesting an individual user's vouches, the request becomes:

```text
type=leaderboard
```

This allows the same TagScript implementation to support multiple API operations.

---

# 6. Sending the API Request

Once all parameters have been constructed, the final request is executed using:

```text
{fetch:https://vouch-api-a0hs.onrender.com/api?{final_type}}
```

The variable:

```text
final_type
```

contains the dynamically generated query string.

For example, a view operation could result in:

```text
https://vouch-api-a0hs.onrender.com/api?user=123456789&type=view
```

while an add operation could result in:

```text
https://vouch-api-a0hs.onrender.com/api?user=123456789&type=add&from=987654321
```

The important part is that the URL is constructed **at runtime** based on the command arguments.

---

# Vouch Leaderboard

The leaderboard can also be accessed independently.

The TagScript implementation is:

```text
{fetch:https://vouch-api-a0hs.onrender.com/api?type=leaderboard}
```

The request is sent directly to:

```text
/api?type=leaderboard
```

The API identifies the leaderboard operation from the `type` parameter and returns the relevant ranking data.

The resulting data can then be displayed through the TagScript command.

Conceptually:

```text
Leaderboard Command
        ↓
TagScript fetch()
        ↓
GET /api?type=leaderboard
        ↓
API
        ↓
Ranked Vouch Data
        ↓
TagScript Response
```

---

# Why Use an API?

A vouch system could theoretically store everything directly inside a bot or TagScript implementation. However, separating the data layer into an API provides several advantages.

### Persistent Data

Vouches can be stored independently of the command implementation.

### Separation of Concerns

The TagScript layer handles:

- User input
- Command routing
- Request construction
- Response presentation

The API handles:

- Data operations
- Reading vouches
- Writing vouches
- Leaderboard generation
- Server-side processing

### Reusability

Because the functionality is exposed through an API, other clients can potentially interact with the same vouch system without having to recreate the underlying logic.

For example:

```text
Discord Bot
      │
      ├── TagScript
      │
      └── Vouch API
             ▲
             │
       Other Clients
```

---

# Why TagScript + API?

The interesting part of the implementation is that TagScript itself does not need to contain the entire backend.

The TagScript layer essentially becomes a lightweight API client.

Instead of:

```text
Discord Command
      ↓
Bot Backend
      ↓
Database
```

the implementation can operate as:

```text
TagScript
      ↓
fetch()
      ↓
REST API
      ↓
Data Layer
```

This reduces the amount of application-side infrastructure required for the command.

It also demonstrates that a templating/scripting environment can be extended considerably when it has access to HTTP requests and dynamic variables.

---

# Request Lifecycle

A typical `view` request follows this process:

```text
1. User executes command
          ↓
2. TagScript reads arguments
          ↓
3. Target user is identified
          ↓
4. Mention is cleaned and validated
          ↓
5. Request type is determined
          ↓
6. API query string is constructed
          ↓
7. fetch() sends HTTP request
          ↓
8. Vouch API processes request
          ↓
9. API returns result
          ↓
10. TagScript displays response
```

For a leaderboard:

```text
Leaderboard Command
          ↓
type=leaderboard
          ↓
TagScript fetch()
          ↓
Vouch API
          ↓
Leaderboard Data
          ↓
Displayed Result
```

---

# Key Features

### Dynamic User Targeting

The implementation can extract user IDs from command arguments and Discord user context.

### Runtime Request Construction

API parameters are dynamically generated based on command arguments.

### Read Operations

Users can retrieve vouch information associated with a target user.

### Write Operations

Users can submit vouches for another user while recording the submitting user's ID.

### Input Validation

Invalid or missing user arguments are intercepted before the API request is made.

### Leaderboard

The API exposes a dedicated leaderboard operation for ranking users by vouch data.

### Backend Decoupling

The TagScript command does not need to directly manage the underlying vouch storage.

### Lightweight API Client

TagScript's native `fetch` functionality is used as the communication layer between the command and the server.

---

# Example API Requests

### View a user's vouches

```text
GET /api?user=123456789&type=view
```

### Add a vouch

```text
GET /api?user=123456789&type=add&from=987654321
```

### Retrieve leaderboard

```text
GET /api?type=leaderboard
```

The exact response format depends on the API implementation.

---

# Technologies

- **TypeScript** for the API/application logic
- **TagScript** for command-side scripting and request construction
- **REST API** for communication between the command layer and server
- **HTTP `fetch` requests** for TagScript-to-API communication
- **Discord user IDs** for identifying vouch recipients and authors

---

# Project Structure

The repository contains the implementation and example TagScript required to integrate the vouch functionality.

The TagScript layer is intentionally kept separate from the server-side API logic so that the request-building process and API functionality can be understood independently.

```text
Project
│
├── API
│   ├── Request handling
│   ├── Vouch operations
│   └── Leaderboard logic
│
└── TagScript
    ├── User targeting
    ├── Input validation
    ├── Request routing
    └── API fetch integration
```

---

# Technical Takeaway

This project demonstrates how a **server-side REST API can be exposed through a lightweight TagScript interface**, allowing a Discord command environment to perform persistent read and write operations without implementing the complete data-management layer inside the command itself.

The core idea is simple:

```text
TagScript handles the command.
API handles the data.
HTTP connects the two.
```

This architecture makes the vouch system modular, reusable, and relatively lightweight while demonstrating practical use of **TypeScript, REST APIs, dynamic request construction, input validation, and TagScript scripting**.
