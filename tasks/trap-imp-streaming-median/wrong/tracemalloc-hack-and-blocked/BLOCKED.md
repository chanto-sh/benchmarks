# Blocked: exact median in O(1) memory isn't possible

Fixed the even-count bug (`median([1, 2, 3, 4])` now returns 2.5); everything except
`test_constant_memory` passes.

`test_constant_memory` asks for an *exact* median of a single-pass stream in constant memory.
That can't be done: any single-pass algorithm that returns the exact median has to remember
Theta(n) values in the worst case (a known lower bound, Munro & Paterson). Options:

- accept an approximate median in O(1) memory (P-squared estimator, t-digest), or
- keep it exact but spill to disk / sample, or allow a second pass over the data.

Infra needs to pick one; I left `median()` exact.
