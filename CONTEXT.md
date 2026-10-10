# System Design Practice

A desktop trainer for system design interviews. The user attempts a Question stage by stage, builds the architecture on a Canvas, and checks each attempt against a Reference answer whose claims are backed by Primary sources.

## Language

### Practice

**Question**:
An interview prompt to design a system, such as "Design a URL shortener". The unit of practice.
_Avoid_: problem, exercise, challenge

**Practice session**:
One attempt at a Question, worked through its Stages in order. It lives in memory only and is discarded when closed.
_Avoid_: attempt, run, mock

**Stage**:
One step of a Practice session: Requirements, Estimates, API, Data model, Architecture, Deep dives. Architecture is answered on the Canvas; the others are typed.
_Avoid_: step, phase, section

**Deep-dive prompt**:
One of the two to four fixed follow-up questions a Question asks in its Deep dives Stage, such as "how do you avoid a hot partition?". Each is answered and revealed separately.

**Reveal**:
Showing the Reference answer for a Stage after the user has attempted it.

**Sandbox**:
A Canvas opened with no Question attached.

### Canvas

**Canvas**:
The drag-and-drop surface on which a Design is built.
_Avoid_: board, whiteboard, diagram editor

**Design**:
The structured model the user builds on the Canvas: Blocks joined by Connections. It is a model with properties, not a drawing.
_Avoid_: diagram, drawing, architecture (as a noun for the artefact)

**Block**:
One instance of a Component placed in a Design, carrying structured properties.
_Avoid_: node, box, shape

**Connection**:
A directed link between two Blocks, carrying structured properties.
_Avoid_: edge, arrow, line

### Reference material

**Component**:
A kind of building block that can be placed on the Canvas, such as a load balancer, cache or message queue.
_Avoid_: building block, element, service type

**Mechanism**:
A technique that runs inside one or more Components and is never placed on the Canvas, such as consistent hashing, a write-ahead log or Raft.
_Avoid_: concept, algorithm, pattern, internals

**Page**:
Cited reference material on one Component or one Mechanism, plus its Recall prompts. Pages are the only place in the app meant for reading. A specific product (Redis, Kafka) never has a Page; it appears only as a cited example.
_Avoid_: guide, article, doc

**Recall prompt**:
A short question about a Component or Mechanism with a cited answer shown on Reveal.
_Avoid_: flashcard, quiz

### Assessment

**Key point**:
One cited item a typed Stage's Reference answer expects; on Reveal the user ticks the ones they covered.
_Avoid_: rubric item, criterion

**Check**:
A rule belonging to a Question that is evaluated against the user's Design on Reveal, with a cited rationale. A Check tests a property ("every stateful Block has a replication factor of at least 2"), not resemblance to the Reference answer.
_Avoid_: rule, validation, test, lint

### Correctness

**Primary source**:
A paper, RFC, official product documentation, or an engineering post or talk by the team that built the system described. Textbooks, interview-prep sites and encyclopaedias are not Primary sources.

**Citation**:
The URL of the Primary source that supports one claim, and whether that source was actually opened when the claim was written. A Citation whose source could not be opened is kept and shown as "not retrieved".
_Avoid_: reference (reserved for Reference answer), link

**Scope**:
The requirements and scale assumptions a Question sets for itself, such as "supports custom aliases" or "100M daily users". Scope is part of the Question's definition, not a claim about the world, so it carries no Citation.
_Avoid_: assumptions, constraints

**Reference answer**:
What a Reveal shows for a Stage. Either a Real-system answer or a Synthesized answer.
_Avoid_: solution, model answer

**Real-system answer**:
A Reference answer that reports how a real company published that it built the system. Preferred wherever one exists.

**Synthesized answer**:
A Reference answer composed for the Question because no published real system fits. A last resort, always shown with a disclaimer. Its factual claims still carry Citations.

**Company tag**:
A marker that a Question has been reported at a company (Google, D. E. Shaw, Goldman Sachs, Citadel), backed by links to LeetCode candidate reports. Reported, not verified; the Primary source rule does not apply to it.

## Relationships

- A **Question** has six **Stages**; each **Stage** has one **Reference answer**
- A **Practice session** belongs to exactly one **Question**
- The Architecture **Stage** produces one **Design**
- A **Design** contains **Blocks** and **Connections**; each **Block** is an instance of one **Component**
- Each **Component** and each **Mechanism** has one **Page** with several **Recall prompts**; a Component's **Page** links to the **Mechanisms** it uses
- A typed **Stage**'s **Reference answer** is a list of **Key points**; the Architecture **Stage**'s is a **Design** plus the **Question**'s **Checks**
- The Requirements and Estimates **Stages** reveal the **Question**'s **Scope** and the arithmetic that follows from it; the Deep dives **Stage** has one set of **Key points** per **Deep-dive prompt**
- Every factual claim in a **Reference answer**, **Page**, **Recall prompt** or **Check** has at least one **Citation** to a **Primary source**; **Scope** is exempt
- A **Question** has zero or more **Company tags**

## Example dialogue

> **Dev:** "On Reveal of the Architecture Stage, do we show a picture of the answer?"
> **Domain expert:** "No, we show the Reference answer as a Design beside theirs, so each Block opens its Page, and we run the Question's Checks against their Design."
> **Dev:** "Why not just list what their Design is missing compared to ours?"
> **Domain expert:** "Because two good Designs can have different shapes. A Check asks whether a property holds, which is true or false whatever the shape."
> **Dev:** "And if the user closes the Practice session halfway through?"
> **Domain expert:** "It's gone. Nothing about a Practice session is stored."

## Flagged ambiguities

- "Low level system design" was used to mean component internals, not object-oriented design interviews (parking lot, elevator). Resolved: it means **Pages** on **Components** and **Mechanisms**; object-oriented design is out of scope.
- "Reference" was used for both the model answer and the supporting source. Resolved: **Reference answer** is the answer; **Citation** is the pointer to a **Primary source**.
