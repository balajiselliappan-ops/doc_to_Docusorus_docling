---
title: "Upgrading from version 35 or later to version 39.1"
slug: /pexipinfinityreleasenotesv391a/upgrading-from-version-35-or-later-to-version-391
sidebar_position: 7
---

## Upgrading from version 35 or later to version 39.1
When the upgrade process starts, the Management Node is upgraded first. Then up to 10 Conferencing Nodes are selected and are automatically placed into maintenance mode. When all calls have finished on a node that is in maintenance mode, that node is upgraded and then put back into active service. Another Conferencing Node is then selected, placed into maintenance mode and upgraded, and so on until all Conferencing Nodes have been upgraded.

If all of the calls on a Conferencing Node that is in maintenance mode have not cleared after 1 hour, the node is taken out of maintenance mode and put at the back of the queue of nodes to be upgraded. A further attempt to upgrade that node will be made after all other nodes have been upgraded (or had upgrade attempts made). Up to 10 Conferencing Nodes may simultaneously be in maintenance mode or in the process of being upgraded at any one time.

Alternatively, to avoid unpredictable system behavior due to Conferencing Nodes running conflicting software versions, you may want to manually put all of your Conferencing Nodes into maintenance mode before initiating the upgrade process. This will allow all existing calls to finish, but will not admit any new calls. You should then actively monitor your Conferencing Nodes' status and manually take each node out of maintenance mode after it has been upgraded to the new software version, so that the system can start taking new calls again on those upgraded nodes.

If you are upgrading from versions prior to v32, you must remove any existing MD5/SHA1 certificates, except root certificates, and replace them with new certificates before upgrading to v32 or later.
