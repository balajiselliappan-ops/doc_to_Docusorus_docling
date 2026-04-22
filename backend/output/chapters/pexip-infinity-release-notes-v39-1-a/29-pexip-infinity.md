---
title: "Pexip Infinity"
slug: /pexipinfinityreleasenotesv391a/pexip-infinity
sidebar_position: 29
---

## Pexip Infinity
| Ref # | Limitation                                                                                                                                                                                                                                                                                                                                                         |
|-------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 46568 | Outbound calls to RTMP participants that cannot be reached remain in a "connecting" state and do not disconnect cleanly when the TCP connection times out.                                                                                                                                                                                                         |
| 46353 | The configured Guests-only timeout and Last participant backstop timeout do not apply to direct media calls, meaning these calls are not automatically disconnected when only one participant remains.                                                                                                                                                             |
