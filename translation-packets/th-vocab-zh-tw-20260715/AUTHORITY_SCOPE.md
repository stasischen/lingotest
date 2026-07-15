# TH 5,000 zh-TW Viewer Candidate — Authority Scope

This is a proposal-only Lingotest review surface. It does not edit or promote
the current `content-th` dictionary inventory or identity lanes, so the mutable
current-language authority registry is non-load-bearing for this packet.

The bounded input is instead pinned directly to immutable committed artifacts:

- Yaitron NDJSON SHA-256:
  `b6b60ace9d3baf1a694ca0aebd86aa07172883056bcdbbb7b1ba5945c5736171`
  (the same frozen Yaitron source hash used by the TH vocabulary taxonomy
  source-repair packets; upstream commit `c3182dfaa744951c9ce48dbcf60b9106195949b9`).
- TH 5,000 candidate ledger SHA-256:
  `5663e40d715dc0eb72797254c69cebbeaf450c183271366329d9eb125eb7bd37`
  (content-th commit `27cf05529f7d4e529cd31b764bb3848ed2d4f781`).
- V160+delta projection SHA-256:
  `2dc3b8207a713980833f80feccb40e3b0f3cf9c4ae1aedd8ec0b67fc5cfecfb2`.
- Existing 733-row reviewed/rechecked sidecars SHA-256:
  `9bb4906a671bdac0e6965dd7a4a520abce6a7139ed81fa9f47b0b3e79d803d9a`
  and
  `8ba43e088525d3c0f9e5da419232d4858d396e05d5dd554d4250e8b4d6aab7a9`.

The new 4,267 zh-TW rows remain `authored_needs_review`, then
`semantic_pass_native_pending` only after independent review. This scope grants
no native approval, runtime admission, or production promotion.
