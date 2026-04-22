---
title: "How to upgrade"
slug: /pexipinfinityreleasenotesv391a/how-to-upgrade
sidebar_position: 8
---

## How to upgrade
When upgrading, please note that:
- A Management Node upgrade may take a long time, potentially up to 1 hour. Do not reboot the Management Node under any circumstances. If you are concerned about the time the upgrade is taking, please contact your Pexip authorized support representative.
- There is normally no need to reboot a Conferencing Node. If a Conferencing Node appears to be stuck for over 1 hour then contact your Pexip authorized support representative - do not reboot the node.
- If you experience issues when upgrading, contact your Pexip authorized support representative - do not attempt to roll back to VM snapshots without first contacting them.
- When upgrading from version 38.x or earlier, all Conferencing Nodes must have completed upgrade before any nodes become available. If a Conferencing Node appears to have failed upgrade then contact your Pexip authorized support representative.

To upgrade Pexip Infinity software from v35.0 or later to v39.1:
1. Before upgrading an on-premises deployment, we recommend that you use your hypervisor's snapshot functionality to take a full VMware/Hyper-V snapshot of the Management Node. We recommend that you do not take a snapshot of your Conferencing Nodes - you can simply redeploy them from the Management Node (after it has been rolled back) in the unlikely event that this is required.


Before upgrading a cloud-based deployment (Azure, AWS, GCP or Oracle), you should backup the Management Node via Pexip Infinity's inbuilt mechanism (Utilities > Backup/Restore).

2. Download the Pexip Infinity upgrade package for v39.1 from the Pexip download page.

3. Before upgrading, ensure that all "always-on" Conferencing Nodes are powered on and are reachable (i.e. no Connectivity Loss errors), and are all running the same version from which you are upgrading. You do not need to power on any cloud bursting nodes.

4. From the Pexip Infinity Administrator interface, go to Utilities > Upgrade.

5. Select Choose File and browse to the location of the upgrade package.

Status -
]pexip[
History & Logs -
Upgrade
Upgrade package
System -
Platform - Call Control-
![Image](/img/docs/pexip-infinity-release-notes-v39-1-a/image_000003_b50a20bca6b97386ab4df2d64a811efcb960cd9cd35cffdc5eec5fdb7eb61a60.png)
Choose File Pexip_Infinity_v20_UPGRADE_45400.tar
![Image](/img/docs/pexip-infinity-release-notes-v39-1-a/image_000004_97545d1fe895e9915e9eb6a7550cec698c08d8f56148845948e00b0c9af6a9b7.png)

6. Select Continue. There is a short delay while the upgrade package is uploaded. After the upgrade package has been uploaded, you are presented with a confirmation page showing details of the existing software version and the upgrade version.

7. To proceed, select Start upgrade. You are taken to the Upgrade Status page, showing the current upgrade status of the Management Node and all Conferencing Nodes. This page automatically refreshes every 5 seconds.

8. When the upgrade completes, all nodes will show a status of No upgrade in progress and have the new Installed version. Uploading the upgrade package to the Management Node again via Utilities > Upgrade will skip over any nodes that have already been upgraded.

9. If you have Pexip CVI for Microsoft Teams you must also upgrade your associated Teams Connector deployment in Azure to the same version as your Pexip Infinity deployment (including minor/"dot" releases). Full instructions are available at [https://docs.pexip.com/admin/teams_managing.htm#upgrading](https://docs.pexip.com/admin/teams_managing.htm#upgrading).

If you are using VMware snapshots for backup purposes, we recommend that you delete those snapshots after approximately two weeks, providing your upgraded system is operating as expected. This is because Virtual Machines, in general, should not run with snapshots over time.

For full details on upgrading Pexip Infinity, see Upgrading the Pexip Infinity platform.
