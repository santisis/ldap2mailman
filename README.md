ldap2mailman
============

ldap2mailman is an LDAP to Mailman3 synchronizer. It pairs groups in the LDAP
with lists in the Mailman3. If an LDAP group matches an existing Maiman3 list,
then the program syncs the Mailman3 subscriptions with the users in the group.

Key features:

*   The program can connect with LDAP using LDAP credentials or using GSSAPI
    and Kerberos tickets.

*   It uses the Mailman3 REST API to connect with the Mailman3.

*   It permits preventing certain addresses from being unsubscribed from the
    list even when they aren't on the LDAP (useful for moderation and
    administration).

*   The program could also maintain a catchall list where everyone with an
    email on the LDAP is subscribed to.

It has been tested in production with OpenLDAP and MIT Kerberos with a Mailman3
3.3.5 server.

Usage
-----

The program is written in Python 3 and only requires `mailmanclient` and `ldap`
packages to run.

If using GSSAPI authentication, it requires `libsasl2-modules-gssapi-mit`
installed on the system.

When invoked, the program performs the sync between LDAP and Mailman3:

`$ python3 ldap2mailman.py`

by default, it runs quietly, but verbosity could be increased with `-v`, `-vv`
and `-vvv`:

`$ python3 ldap2mailman.py -vv`

Configuration
-------------

ldap2maiman requires a `config.py` configuration file. A `config.py.example`
file is provided.

LDAP schema
-----------

The program assumes a `posixGroup` schema for groups, where a group has a
`cn`, a `gidNumber` and a list of `memberUid` and a `posixAccount` plus
`inetOrgPerson` to users, where a user has a `uid`, a `gidNumber` and a `mail`
attributes.

A user could be part of a group by having its `gidNumber` set to a certain
primary group or by having their `uid` as a `memberUid` attribute for its
secondary group/s.

If a user doesn't have a `mail` attribute, it is ignored by the process.

LDAP to Mailman
---------------

For the program to pair LDAP with Mailman it requires that the `group` found in
the LDAP matches a `group@listsdomain` in the Mailman. If an LDAP group doesn't
match a list in the Mailman it will be ignored, in the same way if a Mailman list
doesn't match any LDAP group it will be ignored too. In order to be part of the
sync process, both LDAP group and Mailman list with the same name must exist.

For all the users present in the LDAP group, the program checks if they're
already subscribed to the Mailman list and if not, it will subscribe to it. For all
the email addresses already subscribed to the Mailman list, the program checks
if they're still present in the LDAP group and unsubscribe it if not. There's a
config parameter to define mail addresses that must be left subscribed to the
list, being ignored when unsubscribing missing LDAP users.

If the config defines a catchall list, all the users, whether or not they have
been included as part of a list, will be synced to this list.

License
-------

ldap2mailman was written by Sebastián Santisi and it's free software licensed
under the terms of the GPL license.
