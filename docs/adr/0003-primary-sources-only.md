# Technical content cites Primary sources only

Every factual claim in the app carries a Citation to a Primary source: a paper, RFC, official product documentation, or an engineering post or talk by the team that built the system. Textbooks and interview-prep material (DDIA, Alex Xu, Hello Interview, ByteByteGo, Wikipedia) are excluded even as further reading, so that anything the app asserts can be checked against the people who built or specified the thing.

Reference answers follow from this: a Real-system answer, reporting how a company published that it built the system, is preferred; a Synthesized answer is a last resort and is shown with a disclaimer.

A Citation is the source's URL and nothing more; we considered storing a verbatim quote and a locator with each one and chose not to. When a source exists but could not be opened while the claim was written (paywall, blocked fetch), the claim is kept and its Citation is shown as "not retrieved", so the reader knows that claim was not checked against the source.

Consequences: some Questions have no single tidy answer, and a claim with no Primary source at all is left out. Two things are exempt. A Question's Scope (its requirements and scale assumptions) defines the Question and asserts nothing about the world. Company tags rest on LeetCode candidate reports, because no company publishes its interview questions, and are shown as reported, not verified.
