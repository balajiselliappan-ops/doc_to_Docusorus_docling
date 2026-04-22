---
title: "Known Issues"
slug: /pexipinfinityreleasenotesv391a/known-issues
sidebar_position: 30
---

## Known Issues

| Ref # | Limitation |
|-------|----------|
| 42379 | The time-based conference media statistics / graphs introduced in version 36.0 are not present in version 36.1 and later when reviewing participant / conference history in the Administrator interface. |
| 30756 | Under certain circumstances, when a Conferencing Node is handling calls that include presentation, the observed media load may exceed 100%. |
| 27534 | A Pexip app that is paired to another video device (such as a SIP endpoint) cannot be used to connect to a Media Playback Service. |
| 24607 | Changes to cloud bursting configuration may result in an administrator.configuration log message that GCP private key configuration was changed even when it was not. |
| 24424 | Only 3 of the assigned DNS servers will be used by the Management Node or by a Conferencing Node (as configured in its associated system location). |
| 19176 | Changing the IP address of the Management Node and then manually rebooting before completing the installation wizard may result in failed connectivity to Conferencing Nodes. To work around this, you must ensure that you re-run and fully complete the installation wizard after changing the Management Node configuration. |
| 16232 | The Call-id is not logged on an administrative event when a Guest joins a conference and all Guests are muted. |
| 16119 | "License limit reached" alarms are not lowered as expected, even though an appropriate "Alarm lowered" message is logged. |
| 15943 | "Connectivity lost between nodes" alarms are not recorded in the alarm history ( History & Logs > Alarm History ). |
| 13305 | The G.719 codec is not currently supported for SIP. |
| 12218 | In some call scenarios that take a long time for the call setup to complete (for example calls that involve ICE, a Conferencing Node behind static NAT, and where the client is also behind a NAT) any audio prompts (such as requests to enter a PIN) may be played too early and the client may not hear all of the message. |
| 7906 | If a caller dials into a Virtual Reception and enters the number of the conference they want to join, but there are insufficient hardware resources available to join the caller to that conference, the caller is disconnected from the Virtual Reception. |
| 6739 | Any changes made to VMR configuration -such as updating the participant limit -while the conference is ongoing do not take immediate effect, and may result in conference separation (i.e. new participants will join a separate VMR from those that are currently connected). All participants must disconnect from the conference for the change to take effect. |
| 5601 | When changing the certificates in a chain, a reboot of the associated Conferencing Nodes may be required if the changes do not produce the desired effect. |

![Image](/img/docs/pexip-infinity-release-notes-v39-1-a/image_000015_1d6066ec0717a3cb5f4ddf1f5ebf32ecf92b223070405d27b79dc2fd45cc20f5.png)
