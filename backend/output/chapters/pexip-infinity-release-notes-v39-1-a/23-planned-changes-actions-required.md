---
title: "Planned changes / actions required"
slug: /pexipinfinityreleasenotesv391a/planned-changes-actions-required
sidebar_position: 23
---

## Planned changes / actions required
| Feature                                                                                 | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|-----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OTJ: Microsoft Teams domain change                                                      | In Q1 2026 Microsoft will start transitioning Teams links from teams.microsoft.com to teams.cloud.microsoft . One- Touch Join will automatically support invitations using teams.cloud.microsoft after upgrading to v39 , but if you use any custom rules that use teams.microsoft.com , you must update them manually to use the new format.                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Deprecation of insecure transport for LDAP                                              | The Allow insecure transport option for LDAP integrations (available when configuring LDAP sync sources and LDAP- based authentication for the Administrator interface) is being deprecated and will be removed in a future release. Customers should migrate to TLS-based LDAP integration.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Remove support for VMware ESXi 6.7                                                      | Support for VMware ESXi 6.7 will be removed in a future release. When this occurs, Pexip will support VMware installation on ESXi 7.0 and 8.0.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Remove support for AVX                                                                  | In 2027 we intend to cease support for the AVX instruction set on Pexip Infinity Conferencing Nodes. AVX2 and AVX512 will continue to be supported. This means that any Conferencing Nodes based on Intel Sandy Bridge or Ivy Bridge will cease to work. These parts were last sold in 2015 and Intel ended support in 2020. Any newer hardware that has been deployed with a VMware virtual hardware revision older than 11 will need to be updated to a newer virtual hardware revision.                                                                                                                                                                                                                                                                                                                   |

# Use of application impersonation in One-Touch Join and Secure Scheduler for Exchange

In a future release we will remove the OAuth (delegate access with a service account) Authentication method option when configuring a Secure Scheduler for Exchange Integration. This is because from February 2025 Microsoft disabled Application Impersonation role assignments to service accounts (for more information, see Microsoft's announcement). Therefore:

- One-Touch Join customers using O365 with an OTJ Exchange Integration must migrate to using Graph API instead. For full instructions, see [Migrating from EWS API to Graph API for One-Touch Join](#).
- Secure Scheduler for Exchange customers still using O365 with a service account to access equipment resources and mailboxes must migrate to using app permissions instead. For full instructions, see [Configuring Office 365 for](#).

# Secure Scheduler for Exchange: deprecation of {{start_time}} and {{end_time}} variables

In a future release we will remove the `{{start_time}}` and `{{end_time}}` variables from the following Secure Scheduler for Exchange jinja2 template fields:

- Accept new single meeting template
- Accept edited single meeting template
- Accept new recurring meeting template
- Accept edited occurrence template
- Accept edited recurring meeting template

# Deprecation of password-based authentication for the Teams Connector CVI

Certificate-based authentication (CBA) is now the default method to authenticate the Teams Connector CVI application towards MS Graph. You can still use the previous password-based authentication method, but we plan to deprecate it in a future release, thus we recommend using CBA for new installations, or migrating to CBA as soon as practicable when upgrading existing deployments.

# Deprecation of v1 legacy themes

We plan to deprecate legacy style "version 1" themes in a future release. If you still use v1 themes you should plan to move to using "version 2" themes instead, which have been available since version 18 of Pexip Infinity.

# Deprecation of Webapp2

Webapp2 is being deprecated, and from January 2027 will no longer be included with Pexip Infinity. If this will impact your deployment, please contact your Pexip authorized support representative.

![Image](/img/docs/pexip-infinity-release-notes-v39-1-a/image_000013_b50a20bca6b97386ab4df2d64a811efcb960cd9cd35cffdc5eec5fdb7eb61a60.png)

# Issues fixed in version 39
