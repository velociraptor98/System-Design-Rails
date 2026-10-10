# No user data is persisted

The app stores nothing about the user: no attempt history, no ratings, no scheduling state. A Practice session lives in memory and is discarded when closed. We considered attempt history with weakest-first scheduling and rejected it; the app is a place to practise, not a tracker.

Consequence: there is no database and no per-user data directory, and features that need memory across launches (progress, spaced repetition, resuming a session) are out of scope by design, not by omission.
