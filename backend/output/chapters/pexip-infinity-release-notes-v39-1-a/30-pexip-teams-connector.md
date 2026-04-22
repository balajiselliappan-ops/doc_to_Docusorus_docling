---
title: "Pexip Teams Connector"
slug: /pexipinfinityreleasenotesv391a/pexip-teams-connector
sidebar_position: 30
---

## Pexip Teams Connector

|   Ref # | Limitation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|   35285 | Participants connected via Azure Communication Services (ACS) will not see video from participants joining via CVI as "trusted". We are working with Microsoft to address the issue that these participants are filtered out. A temporary workaround is to configure your system so that CVI participants connect as normal/untrusted guests, and ensure that someone admits them from the lobby. Please contact your Pexip authorized support representative for assistance and refer to issue #35285. |

|   34367 | A Microsoft Teams Room that joins a VMR as a Guest is not treated as a Guest. For example, it will not be muted if "mute all Guests" is triggered. |
|   27854 | In a large Teams meeting you may see a discrepancy in the participant count on Pexip versus that which is reported on the Teams side. We are working with Microsoft to resolve this. |
