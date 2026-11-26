# U7. Who may receive what: authorization on the server, and side channels

**Reading time:** about 25 minutes for Parts 1 and 3 (estimate); Part 5, 5 minutes · **Builds on:** U6 (the stream each viewer receives), U2 (a check and an action separated by a wait) · **Related:** U10 (a user's API key), U11 (text that carries instructions) · **Feeds write-up chapters:** 8, and 7 for the server's half

**The question:** several people watch the same stream of events, but they may not all see the
same things. How does the service make sure that nobody receives what is not theirs, and that
nobody can work it out from what they do receive?

**First answer, before reading on:** where must the check "may this person receive this item"
run, and why is hiding the item in the page not enough? Name one thing a person could learn
without receiving any hidden item. A rough answer is enough; Part 5 is the stopping check.

**Reading path.** Part 1 is the general idea in seven sections (rewritten 2026-11-24 in the
form of U6: the concern first, a diagram, a summary table, standard terms). Part 3 is my Werewolf
system. Part 5 is the summary. This note is short on purpose.

**Scope.** This note is about authorization: what an identified viewer may receive.
Authentication (logging in, passwords, sessions, JWT, OAuth) is on my Heptabase cards and is
not repeated here; section 1.1 only places the two terms. My Werewolf system has no accounts,
so it gives me experience of authorization and of one simple credential, not of a login system.

**Enough for this pass (2026-11-22).** Explain my system without notes: who a viewer is, the
rule that decides what each viewer is sent, where the rule runs, one side channel that was
closed and one that was accepted, and one gap. Read Parts 1, 3 and 5.

**Core and detail.** The core is four ideas: authentication and authorization are separate
checks (1.1); the server enforces authorization for each item and each recipient at the moment
of sending, and denies by default (1.2); every path out of the server calls the same rule, at
one enforcement point (1.3); and a viewer can learn hidden facts through side channels
such as counts, timings and error wording (1.4). The check-then-act race (1.5) and the
credential in the browser (1.6) are detail.

## The whole idea

```text
                         the server holds everything
                                    │
        for each item, for each recipient, at the moment of sending:
                  "may THIS recipient receive THIS item?"
                 │                  │                   │
             customer A         customer B          support staff
          own conversation    own conversation    all conversations
                                                  and internal notes

what still leaks if only the items are filtered (side channels):
   a count that includes hidden items · ids with gaps · how long something took ·
   an error message that differs depending on hidden state
```

| Concept | The question it answers |
|---|---|
| Authentication and authorization | Who is this, and what may they receive? |
| Authorization at the moment of sending | Where does the check run, and what does it compare? |
| Every path out | Which other routes return the same data? |
| Side channel | What can a viewer work out without receiving a hidden item? |
| Check-then-act race | How can a limit be passed by two requests sent together? |
| Credential | What does the browser hold to prove who it is, and when may it throw that away? |

---

# Part 1 — Fundamentals

The example is the support assistant from U6 and U8 to U10, now used by many customers. Each
customer watches their own conversation with the agent. Support staff can watch any
conversation, and they also see internal notes that the agent and other staff write. All of it
travels as events on a stream, as in U6.

## 1.1 Authentication and authorization

A server answers two separate questions about every request.

| | Authentication | Authorization |
| :--- | :--- | :--- |
| Question | Who is making this request? | What may this identity do or receive? |
| Input | A credential carried by the request: a session cookie, a token, an API key | The identity, the action, and the item it concerns |
| Failure status | 401: no valid credential | 403: the identity is known, and the action is not allowed |

A service can do the first correctly and still fail the second. A customer who is logged in
correctly and receives another customer's conversation is an authorization failure. The
standard name for this class of fault is **broken access control**.

```text
Request ──> Authentication ──> Authorization ──> Data
            "Who is this?"     "May they have THIS item?"

A valid login answers only the first question.
```

Authorization covers both what an identity may receive and what it may do. This note
concentrates on what a recipient may receive. The same rules apply to actions: the server
checks each write as it checks each read.

### Common ways to express who may do what

| Model | The rule is based on | Example |
| :--- | :--- | :--- |
| Ownership | Whether the item belongs to the requester | A customer may read their own conversation |
| Role-based access control (RBAC) | A role given to the identity | Anyone with the role "staff" may read internal notes |
| Attribute-based access control (ABAC) | Properties of the identity, the item and the situation | Staff may read a conversation only while they are assigned to it |

Most products combine them. The support product uses ownership for customers and a role for
staff.

### The most common mistake: IDOR

A route takes an item's id from the request and returns the item without checking whether the
requester is allowed to have it.

```text
GET /conversations/1041     → the customer's own conversation
GET /conversations/1042     → another customer's conversation, returned all the same
```

The server knows who the customer is (authentication) and never checks whether they may have
conversation 1042 (authorization). This fault is called an **insecure direct object reference**
(IDOR).

The reply did not go to the wrong browser. The server put the wrong data into the reply to the
right browser.

### Two ways to apply the check (revised 2026-11-25)

Conversations of different customers are stored in the same database table.

| Conversation id | Owner |
| :--- | :--- |
| 1041 | Customer A |
| 1042 | Customer B |

When customer A requests conversation 1042, the server can apply the rule in two ways.

| Approach | How it works | Reply to A |
| :--- | :--- | :--- |
| Load, then check | Load conversation 1042, compare its owner with A, refuse | 403 |
| Scope the query | Load conversation 1042 only if its owner is A. No row comes back | 404 |

Both apply the same rule. The difference is whether it is applied after the data is loaded or
while it is loaded. The 404 has one more benefit: it does not tell A that conversation 1042
exists.

### Making the check hard to leave out

If every route writes its own check, a programmer can forget one. The rule can be applied in
one place instead:

- **A shared data-access function.** Every route loads a conversation through one function,
  and that function always adds the owner filter.
- **Row-level security (RLS).** The database itself refuses rows that do not belong to the
  current user.

A long random id makes an item harder to find and does not replace the check. Ids appear in
logs, browser history and shared links.

### How this relates to tenant isolation

In a system used by many customers or organisations (tenants), each tenant must be kept from
another tenant's data. This is called **tenant isolation**. The owner filter above is one way
to do it when tenants share tables. Other ways put each tenant's data in its own schema or its
own database.

Authorization covers more than tenant isolation. Inside one tenant, different users may be
allowed different things: a customer may read their own conversation and not the staff's
internal notes on it. That needs the per-item rule of 1.2.

```text
                     Authorization
            What may this requester receive or do?
                          │
          ┌───────────────┴────────────────┐
   Across tenants                    Inside one tenant
   May customer A have               May customer A read the staff
   customer B's data?                notes on their own conversation?
          │                                │
   Typical rule: ownership           Typical rule: a role, or an
   (the item's owner is the          attribute of the item or the
   requester)                        situation
```

Tenant isolation is the left branch. IDOR is the fault of a missing or wrong check on one
item, and it can occur on either branch. The ways to apply a rule (check after loading, scope
the query, row-level security, one shared function) serve both branches.

*Cards:* "Authentication and Authorization"; for authentication itself, "JWT (JSON Web Token)",
"Cookies", "Managing User Sessions", "Oauth2", "Role-Based Access Control (RBAC) in Auth.js".

## 1.2 Authorization: controlling what the server sends

(Revised 2026-11-25.) Three rules apply when a server sends data, and they matter most on a
connection that stays open, such as SSE or a WebSocket. All three are needed.

| Rule | Name | Example |
| :--- | :--- | :--- |
| The server decides what to send. The page hiding something is not a protection | Server-side enforcement | Staff notes must not reach a customer's browser, even if the page would hide them |
| The permission must still be true at the moment of sending | Checking at the moment of use | A staff member who loses the staff role stops receiving internal notes, even if their stream stays open |
| If no rule allows it, it is not sent | Deny by default | A new event type with no audience defined is sent to nobody |

The three rules answer where the check runs, when it runs, and what happens when no rule
grants access.

### Rule 1: enforce on the server

A support conversation holds customer messages and internal staff notes. The customer may see
only the messages.

```text
Correct:

Server ── filter ──> Browser          The staff notes never leave the server.


Incorrect:

Server ───────────> Browser ── hide ──> Screen
                       │
                       └── The notes are in the browser's memory and in the Network
                           tab of its developer tools. The user can read them there.
```

Whatever reaches the browser has been disclosed. Hiding an element in the page changes what is
drawn, not what the user can read. So the server decides what the recipient may receive before
it sends anything. This is **server-side enforcement**.

### Rule 2: the permission must be true at the moment of sending

What a recipient may receive can change while a connection is open.

```text
10:00   A staff member opens a stream. They hold the role "staff".
10:05   The role is removed: they have left the support team.
10:06   A new internal note is written.

Using the permission from 10:00:   the note is sent      (incorrect)
Using the permission at 10:06:     the note is not sent  (correct)
```

Checking only when the connection opens is not enough. There are several ways to meet the
rule:

- check the permission before sending each item
- keep a stored copy of the permission and discard it when the permission changes
- close the affected connection when access is taken away

The requirement is that an out-of-date decision is never used to send new data. It does not
require a database query for every item.

A condition that changes between the time it is checked and the time the result is used is a
**time-of-check to time-of-use** problem (TOCTOU). Section 1.5 shows the same problem for
limits.

### Rule 3: deny by default

The server records who may receive each type of event. That set of recipients is the event
type's **audience**.

```text
Event type          Audience (table on the server)
──────────────────────────────────────────────────
customer_message    The conversation's participants
internal_note       Staff
refund_decision     (not defined)
```

A developer added `refund_decision` and forgot to give it an audience.

| Design | A type with no audience | Result of the mistake |
| :--- | :--- | :--- |
| Allow by default | Is sent to everyone | A leak, found only when someone notices it |
| Deny by default, checked when sending | Is sent to nobody | A missing item, found at once only if the refusal is logged or raised as an error |
| Deny by default, also checked when the service starts | The service does not start | An error, found at once by the developer |

**Deny by default** means access has to be granted by a rule. A missing rule never grants it.
The start-up check is an addition that makes the forgotten rule visible before the service
accepts any request.

A related term is **failing closed**: when the check itself cannot run, for example because
the service that holds permissions is unreachable, the answer is "no".

```text
No rule exists for this item    → deny by default
The check could not be run      → fail closed
```

Both choose refusal when permission cannot be established.

### The three rules together

```text
                 New event, about to go to one recipient
                              │
   ┌── On the server (rule 1) ┼──────────────────────────────────┐
   │                          ▼                                  │
   │        Does a rule exist for this event type?  ── no ──┐    │
   │        (rule 3: deny by default)                       │    │
   │                          │ yes                         ▼    │
   │                          ▼                        Do not    │
   │        May this recipient have it, as things      send      │
   │        stand now?  (rule 2)   ── no, or the check ──▲       │
   │                          │       could not run              │
   └──────────────────────────┼──────────────────────────────────┘
                              │ yes
                              ▼
                     Send to the recipient
```

## 1.3 Every path out needs the rule

The live stream is seldom the only way data leaves the server. This note calls each such way a
**path out**. Every path out needs the same authorization rule.

```text
                        ┌── Live stream
                        ├── Catch-up after a reconnect (U6)
Protected data ─────────┼── Status or summary ("3 new messages")
                        ├── History, export or download
                        ├── Search
                        └── A model's prompt (retrieval)
```

A path added later is the usual place where the rule is forgotten.

### One enforcement point

| Design | How the rule is applied | Risk |
| :--- | :--- | :--- |
| A filter written separately in each route | Each route has its own copy of the logic | The copies stop matching as each is edited separately, and a new route may have none |
| One function that every route calls | A single place decides "may this recipient receive this item" | Low. A new route still has to call it |

The second design is **centralised authorization**: one enforcement point for the rule. The
principle that every access must pass through the check, with no path around it, is called
**complete mediation**. One enforcement point also makes the rule testable in one place.

### The same rule in retrieval for a model

A model application that searches documents for a user has the same problem.

```text
No filter, or a filter by instruction to the model (incorrect):

Search all documents ──> passages ──> prompt ──> model ──> answer
                                         │
                                         └── includes a passage the user may not read;
                                             the model can repeat it


Filter at retrieval (correct):

Search only documents this user may read ──> passages ──> prompt ──> model ──> answer
```

The filter "which documents may this user read" is applied on the server, before any passage
reaches the prompt. Filtering in the search itself is the usual way, because a filter applied
after the search can leave too few passages. Asking the model not to reveal a passage is the
equivalent of hiding in the page: the model has already received the data.

## 1.4 Side channels

A **side channel** lets someone learn a hidden fact indirectly, when the protected item itself
is never sent. (Opening revised 2026-11-25.)

Events in a support conversation are numbered in order:

```text
The server holds:        41, 42, 43, 44, 45
The customer receives:   41, 42,         45
```

The customer cannot read events 43 and 44, and can still tell that two events were withheld.
Correct authorization stops the protected data from being sent. It does not by itself stop
facts about that data from showing in what is sent.

| Side channel | Example | Fix |
| :--- | :--- | :--- |
| Counts | The customer has received 5 events and the status route reports 7 | Count only the events this recipient may receive |
| Ids in order | Gaps in the event ids show that hidden events exist | A separate numbering for each recipient |
| Timing | A reply takes 30 seconds longer when a staff member reviews it first | Hold every reply to the same fixed time |
| Error replies | 403 for a conversation that exists and 404 for one that does not; or "being reviewed by staff" against "nothing to answer yet" | The same status and the same message in both cases |

### Finding one

Ask one question of every path out of the server (1.3):

> Does anything in this reply change depending on something this recipient may not know?

"Anything" includes the fields, the status code, the wording, how long the reply took and
whether a reply came at all.

### Two patterns for closing one

The exact fix depends on the case. The fixes fall into two patterns.

| Pattern | Idea | Rows above |
| :--- | :--- | :--- |
| Compute from what this recipient may receive | A value derived from the data (a count, a newest id, a list, a total) is calculated over the filtered set, not the full set | Counts, ids in order |
| Make the reply the same whatever the hidden fact is | The message, the status code or the time taken does not vary with the hidden fact | Timing, error replies |

### Close it or accept it

Closing a side channel has a cost: a second numbering, a slower product, a less helpful error.
Whether to close one rests on two questions: how much does the leaked fact matter, and what
does it cost to stop the leak? A minor leak can be accepted. An accepted side channel is
written down with its reason, so that it is a decision and not an oversight.

### Check

A customer's page polls a status route that returns the id of the newest event in their
conversation. The stream itself is filtered correctly. What can the customer learn, and what is
the fix?

<details><summary>Answer</summary>

When the newest id rises and no event arrives on the stream, something hidden was written, and
the customer knows when. The fix is to return the newest id among the events this customer may
receive. The status route is a second path out (1.3), and its value was computed over hidden
items (1.4). One side channel remains after the fix: the customer's own ids still have gaps,
which is the "ids in order" row, to be closed or accepted separately.

</details>

## 1.5 Enforcing a limit: the check-then-act race (detail)

Some rules about what a user may do are limits: three free drafts per question, one use per
coupon, a balance that may not go below zero. These are usually called business rules or
quotas, and they are enforced on the server like any authorization rule. A limit is enforced by
reading a value, comparing it and then acting. If a second request reads the value after the
first request has compared it, and before the first has written the new value, both pass.

```text
Limit: 3 drafts. Count so far: 2.

Time    Request A                    Request B
 1      Read count: 2
 2      2 < 3, allowed
 3                                   Read count: 2
 4                                   2 < 3, allowed
 5      Call the model (slow)        Call the model (slow)
 6      Write count: 3
 7                                   Write count: 3

Result: 4 drafts were made, and the count says 3.
```

This is a **check-then-act race**, a case of **time-of-check to time-of-use** (TOCTOU, 1.2).
It happens whenever two requests can overlap between the check and the update:

- With several server processes, or several servers sharing one database, two requests run at
  the same moment (parallelism). With threads, they run at the same moment, or the system
  switches from one to the other at any instruction (in Python, threads take turns). In both
  cases the overlap needs no wait at all.
- In a single-threaded asynchronous server, the requests take turns, and a switch happens only
  where the running request waits, for a model call or a database query. U2 covers why.

### Where it appears

| Limit | What two simultaneous requests do |
| :--- | :--- |
| A coupon that may be claimed once | Both claim it |
| Stock of one item | Both buy it |
| A balance that may not go below zero | Both withdraw |
| A quota or rate limit | Both read the same count, both are allowed, and the limit is exceeded by one |

### Remedies

All of them make the check and the update **atomic**: one step that no other request can run
in the middle of.

| Remedy | How it works | Fits when |
| :--- | :--- | :--- |
| An atomic conditional update (compare-and-set) | One database statement: `UPDATE ... SET count = count + 1 WHERE count < 3`, then read how many rows changed | The count lives in a database |
| A unique constraint | The database rejects a second row for the same coupon and user | "At most once" rules |
| A lock | Only one request at a time may run the check and the update. A lock inside one process does not protect across several processes or servers; there it must be a database row lock or a distributed lock | Several steps must happen together |
| No wait between check and update | In a single-threaded server, code with no `await` between the two cannot be interrupted | The count lives in one process's memory, and there is one process |

### Reserve first, then work

The slow work goes after the reservation, not between the check and the update.

```text
1. Check the limit and take one unit, as one step.
2. Do the slow work (the model call).
3. If the work fails, give the unit back.
```

## 1.6 Holding a credential in the browser (detail)

After authentication, the browser has to prove who it is on every later request. It does so
with a **credential** that it stores and sends each time. The usual credential is a **bearer
token**: a long random string that the server created and can recognise. Whoever presents it is
treated as its owner, so it has to be hard to guess and hard to steal. A **session** is the
server's record that links such a token to an identity.

The alternative keeps no record. The token itself contains the identity and is signed by the
server, so the server checks the signature and looks nothing up. This is a JWT. Its payload
can be read by anyone who holds it, and it cannot be cancelled before it expires, which is why
such tokens are given a short life. (Added 2026-11-25; card "Sessions and JWTs: where the
identity is kept".)

A service without accounts can use the same mechanism. It gives the browser a token when the
user joins, and the token is the whole of the user's identity.

### Where the browser keeps it

| Storage | Readable by scripts in the page | Sent automatically with requests | Main risk |
| :--- | :--- | :--- | :--- |
| A cookie marked `HttpOnly` | No | Yes | Cross-site request forgery (CSRF): another site makes the browser send a request that carries the cookie |
| `localStorage` | Yes | No | Cross-site scripting (XSS): an injected script reads the token and sends it elsewhere |
| A variable in memory | Yes, while the page is open | No | The same XSS risk while the page is open. It is also lost on every reload, which is a usability cost |

An `HttpOnly` cookie is the usual choice for a session. `HttpOnly` stops an injected script
from reading the token and taking it away. It does not stop the script from using it: a script
running in the page can still send requests that carry the cookie. So the cookie limits what
XSS can do and does not remove the need to prevent XSS. `SameSite` reduces the CSRF risk.

### Cookie attributes

| Attribute | Effect |
| :--- | :--- |
| `HttpOnly` | Scripts in the page cannot read the cookie |
| `Secure` | The cookie is sent only over HTTPS |
| `SameSite` | Limits when a request started by another site carries the cookie. `Strict`: never. `Lax`: only when the user follows a link to the site. `None`: always, and it then requires `Secure` |
| `Path`, `Max-Age` | Limit which requests carry it and for how long |

### On the server

The server should store a hash of the token, not the token itself. A leaked database then
contains no value that works as a credential. The reason is the same as for passwords, and the
hash differs: a password is guessable and needs a slow, salted hash (bcrypt, argon2), while a
long random token cannot be guessed and a fast hash such as SHA-256 is enough.

### When the browser may delete its copy

Some pages keep their own copy of a credential, in `localStorage`, beside the cookie. Such a
page deletes its copy only after a definitive rejection, such as a 401 or 403 from the server.
It never deletes the copy after an inconclusive failure, such as a network error or a 502,
because the credential is still valid then. U6 section 1.8 explains the distinction.

*Cards:* "Sessions and JWTs: where the identity is kept", "Cookies", "Setting Cookie Params",
"Http-only Cookie auth with Next".

## 1.7 Deciding it for a new system

| Question | What the answer decides | Section |
| :--- | :--- | :--- |
| 1. Do all recipients receive the same data? | If yes, the filtering of 1.2 to 1.4 is not needed; limits and credentials still apply. If no, the rest applies | 1.1 |
| 2. What audiences exist, and is the rule ownership, a role, or attributes? | The access control model | 1.1 |
| 3. What is the audience of each kind of item, and what happens to an item with none? | The audience table, and deny by default | 1.2 |
| 4. Can a recipient's rights change while connected? | Whether the decision is made per item or once per connection | 1.2 |
| 5. Which paths out return this data, including counts, search and a model's prompt? | The list of places that must call the one enforcement point | 1.3 |
| 6. What counts, ids, timings and messages does a recipient see? | The side channels to close or accept | 1.4 |
| 7. Which rules are limits, and is there a wait between the check and the update? | Where a check-then-act race is possible, and its remedy | 1.5 |
| 8. What proves identity, and where is it stored? | The credential, its cookie attributes, and whether the server stores it hashed | 1.6 |

---

# Part 3 — My Werewolf system

A game has ten seats. Some are wolves, who know each other and talk privately at night. Some
seats have a night action whose result only that seat may know. Human players, AI seats and
spectators all follow the same game, and every engine change becomes a numbered event (U6). The
server must send each viewer only the events that viewer may know.

## 3.1 Who a viewer is

- **A seat token.** When a player joins, the server creates a random token (`uuid4`, 122 random
  bits) and remembers which seat it belongs to. There are no accounts and no passwords. This is
  a bearer token (1.6), and it is the whole of this system's authentication.
- **How it travels.** The server sets it as a cookie named for the game (`seat_<game id>`),
  `HttpOnly`, `SameSite=Lax`, limited to that game's path, valid for 24 hours. In production the
  cookie is also `Secure`. A cookie is used because the browser's stream API (`EventSource`)
  cannot set headers but does send cookies.
- **A spectator** is a request with no cookie. A spectator has no seat.
- **A wrong token** is refused with 403 on the stream, the status and the turn routes.

The cookie's attributes are those of 1.6. The token is in an `HttpOnly` cookie, so a script in
the page cannot read it, and `SameSite=Lax` limits requests started by other sites.

## 3.2 The rule: four audiences

This is the audience table of 1.2. In the terms of 1.1 the rule combines a role (the wolf
pack), ownership (the seat named on an event) and one attribute of the situation (whether the
game is over).

Every event type has one of four audiences, which the code calls **tiers**. The tier is not a
field on the event. It is a table on the server, keyed by the event's type (`EVENT_TIERS`), so
the page never receives it and cannot change it.

| Tier | Who receives it during the game | Examples |
|---|---|---|
| Public | Everyone, spectators included | A speech, a vote, the result of a night |
| Faction | The seats whose role is in the wolf pack | A wolf's private message, the pack's chosen target |
| Seat | The one seat named on the event | That seat's own role, its question, the result of its investigation |
| Observer | Nobody, until the game is over | Every seat's role, each seat's private reasoning, the memories an AI seat consulted |

One function, `entitled(event, seat, roles, game_over)`, turns a tier and a viewer's seat into
yes or no. A spectator passes only the public tier.

**Deny by default (1.2).** An event type with no entry in the table cannot be sent by mistake
as public: a check that runs when the server starts fails if any event type lacks a tier, so
the server does not start. A test checks the same.

## 3.3 Where the rule runs

**Server-side enforcement, at the moment of sending (1.2).** The session puts every event on
every viewer's queue without filtering. The filter runs in the stream route, immediately before
an event is written to that viewer's connection. The route looks up the viewer's seat again for
every event, because streams open before seats are dealt.

**The paths out (1.3).** `entitled` is the one enforcement point for three of the five paths
below. The other two keep hidden events back by their own means (gap 5).

| Path out | How hidden events are kept back |
|---|---|
| Live stream | `entitled` is called for each event and each viewer, at the moment of sending |
| Catch-up after a reconnect | The same call, over the saved log. The viewer's position never hides an event that had been withheld from them (U6) |
| Status request | The newest event number is computed with `entitled`; the list of seats that owe a turn shows only the viewer's own seat |
| Ledger of a running game | Does not call `entitled`. It reads only a fixed list of event types, all of them public |
| Replay | Does not call `entitled`. It is served only for a completed game, when everything is open |

There is no export or download route. I found no path on which hiding depends on the page.

## 3.4 The end of a game

When the game ends, every viewer becomes an observer: `entitled` returns yes for everything.
The stream route then sends each viewer the events that were withheld from them during the
game, which is how the roles and the private reasoning appear in the final reveal. A viewer who
connects after the end receives the whole log.

## 3.5 Side channels

An audit of the multiplayer game on 2026-10-15 looked for side channels (1.4). Each one found
was closed or accepted on purpose. The state today:

| Side channel | What a viewer could learn | State |
|---|---|---|
| The status's newest event number counted every event | It rose once for each private night action, so anyone polling it could count the night's actions | Closed: the number is the newest event this viewer may receive |
| The refusal to a turn sent at the wrong time | The wording differed depending on whether another seat owed a turn, which showed that a private actor was still acting | Closed: the message names only the caller's own seat |
| The list of seats that owe a turn | A pending night turn identifies a private actor | Closed: a viewer sees only their own seat in it |
| The night's progress bar | Which roles are alive and which seats act | Closed in most of it: the bar's total is the number of publicly alive seats, and a timer completes each unit after 20 to 30 seconds whether or not that seat acted. In the first 20 seconds the count is still a lower bound on how many seats act |
| The stream's event numbers | The numbers a viewer receives have gaps, and each gap counts the hidden events between | Accepted: reconnecting resumes from these numbers |
| The night's length | A night with a human night actor lasts longer than the 20 to 30 seconds of the bar | Accepted as a small leak |

## 3.6 The limit on drafts

A human player may ask the AI to draft their line, at most three times per question. Each draft
is a paid model call.

**The check-then-act race (1.5).** The count was once increased after the model answered, so
drafts sent together all passed the limit.

**The remedy: no wait between check and update, and reserve first.** Now the code compares the
count, increases it and marks the seat as drafting, with no wait between those steps, before it
calls the model. The server runs on one event loop, so no other request can run between them.
If the model call fails, the count is given back. A second draft sent while one is running is
refused with 409.

## 3.7 The page's copy of the token

The page keeps a copy of the seat token so that it can take the seat again if the cookie is
lost. It deletes the copy only after a definitive rejection (U6 1.8): the server answers 403,
404 or 410. After an inconclusive failure it keeps the copy and tries again after 5 seconds. Before this rule, any failed attempt deleted
the copy, and a network drop made a player a spectator for the rest of the game.

## 3.8 Known limitations

| Gap | Consequence | Possible direction |
|---|---|---|
| 1. The stream's event numbers have gaps where hidden events fell (3.5) | A viewer can count hidden events between two public ones | A numbering per viewer, with the reconnect position translated on the server |
| 2. The night's length shows a human night actor (3.5) | A viewer can tell that a human holds a night role | Hold every night to a fixed length; it slows the game |
| 3. The seat token is stored as plain text in the database, not as a hash, and the page's copy is in `localStorage`, which scripts in the page can read (1.6) | A leaked database, or a script injected into the page (cross-site scripting), gives the token, and with it the seat | Store a hash on the server; keep only the cookie |
| 4. The check that every event type has a tier is an `assert` | Python removes `assert` statements when run with `-O`; the server is not run that way, and a test checks the same thing | Raise an ordinary error |
| 5. The ledger and the replay keep hidden events back by their own means, not by `entitled`, so authorization is not fully centralised in `entitled` (1.3) | A change to either route has to keep its own condition right | Call `entitled` there too |
| 6. The release of withheld events at the end of a game does not call `entitled`; it relies on the game-over flag having been set first | Correct today; a change to that order would send withheld events early | Call `entitled` in that loop |
| 7. Whether every field of every public event is free of hidden information has not been audited as a whole | One case is tested: a concealed death does not show the role | A test over all public event types |
| 8. No rate limits on any route | A client can poll or reconnect as fast as it likes (U15) | A limit at the proxy |

---

# Part 4 — Design choices

**Where is the decision made?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Filter per event and per viewer, when sending | Always uses the viewer's current seat; one rule | The check runs for every event and every viewer | Yes |
| One prepared stream per audience | Fewer checks | Several streams to keep consistent; a viewer who changes audience has to change stream | No |
| Send everything and hide in the page | The simplest | Not a protection: the data has been received | Never for hidden information |

**Where is an item's audience recorded?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| A table on the server, by event type | The page never sees it; a missing entry is found at startup | The audience cannot vary between two events of one type, except by the seat named on the event | Yes |
| A field on each event | Each event can differ | The field must be removed before sending, and a wrong value is found only when it leaks | No |

---

# Part 5 — Review

## In 30 seconds

Authentication says who is asking; authorization says what they may receive. The server decides
for each item and each recipient at the moment of sending, from an audience table that the
client never sees, and an item with no audience is not sent. Every route that returns the data
needs the same rule: catch-up, status, history, search, and the passages retrieved for a model's
prompt. A viewer can still learn hidden facts from counts, ids, timings and error wording; each
of these is closed or accepted on purpose. A limit is checked and updated in one step, reserved
before the slow work and given back on failure, so that two requests sent together cannot both
pass (the check-then-act race). A page deletes a stored credential only after a definitive
rejection.

## My Werewolf system in one paragraph

A viewer is identified by a random seat token in an `HttpOnly` cookie; a request without one is
a spectator. Every event type has one of four audiences in a table on the server: public, the
wolf pack, one seat, or nobody until the game ends. The stream route calls one function for
each event and each viewer immediately before sending, and the catch-up and the status use the
same function. At the end of a game everything is released to everyone. An audit closed three
side channels (the status's event number, the wording of a refusal, the list of seats that owe
a turn) and the progress bar was designed to hide who acts at night. Two are accepted: the gaps
in the stream's event numbers, and the length of a night with a human actor. The weak points:
the token is stored unhashed, two routes keep hidden events back by their own means, and there
are no rate limits.

## Stopping check

In two minutes, without the note: who a viewer is; the four audiences; where the rule runs and
why it is not in the page; one side channel that was closed and one that was accepted; one gap.
If those connect, this pass is done.

## Problems

**Problem A.** A product sends notifications to many users from one service, over a stream.
Some notifications are for one user, some for a team, some for everyone. Say where the
filtering happens and why, and name two side channels to check.

**Problem B.** A "claim this coupon" route sometimes lets one coupon be claimed twice under
load. Explain the cause and the fix.

**Problem C.** A draft sentence for the write-up: "The server cannot leak a wolf's identity."
What is supported, what is not, and what is the accurate wording?

---

# Appendix A — Answers to the problems

**Problem A.** On the server, for each notification and each connected user, at the moment of
sending, from an audience recorded with the notification's type or target (user, team,
everyone). Not in the page, because a received notification can be read whether or not it is
displayed. The check uses the user's team membership as it is at that moment, since a user can
leave a team while connected. The catch-up after a reconnect and the "unread" count need the
same rule. Two side channels: an unread count or a newest id that includes notifications the
user may not receive, and ids with gaps that show how many notifications other users received.

**Problem B.** The route reads "is the coupon unclaimed", then waits (a database write, a
payment call), then marks it claimed. Two requests sent together both read "unclaimed" before
either marks it. The fix is to make the check and the claim one step: a single database
statement that updates the row only if it is still unclaimed and reports whether it changed a
row, or a unique constraint on the claim. If later work fails, the claim is released.

**Problem C.** Supported: wolf-only and seat-only events are sent only to the viewers entitled
to them, on the stream, the catch-up and the status, and tests cover each audience. Not
supported: "cannot". Two side channels are accepted (gaps in the event numbers, the length of a
night), the fields of public events have not been audited as a whole, and the seat token is
stored unhashed. Accurate wording: "The server decides, for each event and each viewer, whether
to send it, so a wolf's private events reach only the wolves. Two indirect signals remain by
choice: the event numbers have gaps, and a night with a human actor lasts longer."

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read on 2026-11-22),
**test** (named, not run for this note), **doc** (a written record, not re-read in the code).
"The audit" is `frontend/docs/multiplayer-audit-2026-10-15.md`. Paths are from the repository
root.*

**Who a viewer is (3.1)**

- The token is `str(uuid4())`: **code** `server/game/lobby.py` (join), `server/routes/games.py`
  (`create_game`)
- The cookie's settings: **code** `server/routes/_shared.py` (`set_seat_cookie`); `Secure` in
  production: **code** `.env.production` (`SEAT_COOKIE_SECURE=true`); **test**
  `tests/server/test_http_api.py` (`test_join_sets_an_httponly_seat_cookie_matching_the_body_token`,
  `test_seat_cookie_secure_flag_is_an_env_knob`)
- A spectator has no seat; a wrong token is 403: **code** `server/game/game_session.py`
  (`seat_of_viewer`), `server/routes/games.py` (`_proven_seat`); **test**
  `test_events_and_status_reject_a_forged_cookie`, `test_turns_demand_a_proven_seat`

**The rule (3.2)**

- `entitled` and its four branches: **code** `server/game/entitlement.py`; **test**
  `tests/server/test_game_session.py` (`test_public_reaches_everyone_including_spectators`,
  `test_faction_reaches_wolves_only`, `test_seat_reaches_the_named_recipient_only`,
  `test_observer_reaches_nobody_live_and_everybody_after_game_over`)
- The tier table and the startup check: **code** `server/schemas/events.py` (`EVENT_TIERS`, the
  two `assert` lines after it); **test** `tests/server/test_event_schema_contract.py`,
  `tests/server/test_translator.py` (`test_every_emitted_type_is_tier_registered`)

**Where the rule runs (3.3, 3.4)**

- Every event queued for every viewer; the filter at sending; the catch-up loop; the release at
  game over: **code** `server/game/game_session.py` (`_deliver`), `server/routes/games.py`
  (`_sse`: `may_see`, `cursor_skips`); **test** `test_sse_replays_the_whole_log_after_game_over`,
  `test_postgame_reconnect_cursor_does_not_skip_the_withheld_backlog`
- The status: **code** `server/routes/_shared.py` (`live_status`); **test**
  `test_status_last_seq_counts_only_what_the_viewer_may_see`,
  `test_status_only_exposes_the_viewers_own_pending_turn`
- The ledger reads named public types; the replay is for completed games only: **code**
  `server/game/ledger.py` (`ledger_days`), `server/storage/replay_service.py` (`get_replay`)

**Side channels (3.5)**

- The status number and the refusal wording, closed: **doc** the audit, findings 1 and 2
  (commits `cc0325c2`, `0082952b`); **code** `live_status`, `GameSession.submit_turn`; **test**
  `test_turn_without_a_pending_request_is_409`
- The progress bar: **code** `server/game/pacing.py` (module docstring, `PacingTracker`); **test**
  `test_pacing_totals_are_the_publicly_alive_seats_and_shrink_with_every_death`
- The stream's numbers and the night's length, accepted: **doc** the audit, "Accepted or left",
  findings 1 and 3; **code** `server/routes/games.py` (`_frame` writes the global number)

**The draft limit (3.6)**

- Three per question; compare, increase and mark with no wait between; given back on failure:
  **code** `server/game/game_session.py` (`draft_line`, `DRAFTS_PER_TURN`); **doc** the audit,
  finding 4 (commit `7ed36d7e`); **test** `test_drafting_credits_the_wait_and_caps_the_turn`

**The page's copy (3.7)**

- Deleted only on 403, 404 or 410: **code** `frontend/src/lib/request.ts`
  (`ApiError.refusesToken`), `frontend/src/lib/storage.ts`; **doc** the audit, finding 11 (commit
  `5b4186d2`); **test** `frontend/src/lib/request.test.ts`

**Not established**

- Whether nights with different living roles differ measurably in length.
- Whether every public event's fields are free of hidden information.
- The planning outline for this note lists the night's length among the closed side channels.
  The audit records it as accepted, and I found no code that holds a night to a fixed length.
