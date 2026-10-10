# A Design is assessed by Checks, not by diff against the Reference answer

On Reveal of the Architecture Stage the app shows the Reference answer beside the user's Design and evaluates the Question's Checks against the user's Design. It does not list the Blocks and Connections the Reference answer has that the user's lacks. Two sound Designs for the same Question can differ in shape, so a diff against one reference reports valid answers as wrong; a Check tests a property that holds or fails whatever the shape.

This is why a Design is a structured model and not a drawing: Blocks and Connections carry properties (replication factor, partitioning, sync or async, protocol, read or write path) because Checks need them to evaluate.
