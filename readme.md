## Server-Side Vouch API

A server-side API implementation for **collecting, reading, and managing vouches** using TagScript. The implementation uses TagScript’s built-in `fetch` feature to communicate directly with the API, allowing vouch data to be read and written **without requiring a separate backend**.

### Vouch API: Read & Write

The following TagScript implementation supports viewing a user's vouches and adding new vouches:

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

The script identifies the target user, validates the mention, and dynamically determines whether the request should **read existing vouches (`view`) or write a new vouch (`add`)**. The resulting parameters are then sent directly to the API through TagScript's `fetch` functionality.

This enables TagScript commands to interact with the vouch database directly, without requiring an additional application server or backend layer.

### Vouch Leaderboard

A leaderboard can be retrieved directly from the API using:

```text
{fetch:https://vouch-api-a0hs.onrender.com/api?type=leaderboard}
```

This endpoint retrieves the leaderboard data from the vouch API, allowing the most-vouched users to be displayed directly through a TagScript command.

### Architecture

```text
TagScript Command
       ↓
TagScript Fetch
       ↓
Vouch API
       ↓
Vouch Data
```

The approach keeps the implementation lightweight by using TagScript as the interface layer while the API handles the underlying vouch data operations.
