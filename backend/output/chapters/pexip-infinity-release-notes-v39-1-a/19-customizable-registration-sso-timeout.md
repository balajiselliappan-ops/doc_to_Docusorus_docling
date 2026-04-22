---
title: "Customizable registration SSO timeout"
slug: /pexipinfinityreleasenotesv391a/customizable-registration-sso-timeout
sidebar_position: 19
---

## Customizable registration SSO timeout

| Feature | Description |
|--------|-------------|
| Customizable registration SSO timeout | For SAML Identity Providers that do not support the `SessionNotOnOrAfter` attribute for customizing session timeouts (such as Microsoft Entra ID), there is now support for an alternative `SessionDuration` custom attribute. |

| Administrative improvements: vendor details for registered devices; upload progress bar, changing order of aliases | This release contains the following administrative improvements: l The registration status and registration history pages now include vendor information for the registered device. l All cosmetic references to Microsoft Lync have been removed from the Administrator interface, and thus all labels and messages now refer to only Microsoft Skype for Business / SfB. l When uploading an upgrade package, Administrators are now presented with a progress bar. l When configuring a service with multiple aliases, administrators can now change the order in which the list of aliases appears. |
