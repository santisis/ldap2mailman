ldap2mailman
============

ldap2mailman is a LDAP to Mailman3 syncer. It pairs groups in the LDAP with
lists in the Mailman3. If a LDAP group match an existing Maiman3 list, then the
program syncs the Mailman3 subscriptions with the users in the group.

The program can connect with LDAP using LDAP credentials or using GSSAPI and
Kerberos tickets. It uses the Mailman3 REST API to connect with the Mailman3.
It permits to prevent certain addresses to be unsubscribed in the lists even
when they aren't on the LDAP (useful to moderation and adminstration). The
program could also mantain a catchall list where everyone with an email on the
LDAP is subscribed.

It has been tested in production with OpenLDAP and MIT Kerberos with a Mailman3
3.3.5 server.

Usage
-----

The program is written in Python 3 and only requires `mailmanclient` and `ldap`
packages to run.

If using GSSAPI authentication it requires `libsasl2-modules-gssapi-mit`
installed on system.

When invoked the program performs the sync between LDAP and Mailman3:

`$ python3 ldap2mailman.py`

by default it runs quietly, but verbosity could be increased with `-v`, `-vv`
and `-vvv`:

`$ python3 ldap2mailman.py -vv`

Configuration
-------------

ldap2maiman requires a `config.py` configuration file. A `config.py.example`
file is provided

LDAP schema
-----------

The program asumes a `posixGroup` schema for groups, where a group has an `cn`,
a `gidNumber` and a list of `memberUid` and a `posixAccount` plus
`inetOrgPerson` to users, where a user has a `uid`, a `gidNumber` and a `mail`
attributes.

An user could be part of a group or by having its `gidNumber` set to a certain
primary group or by having their `uid` is a `memberUid` attribute of its
secondary group/s.

If a user doesn't have a `mail` attribute it is ignored by the process.

LDAP to Mailman
---------------

For the program to pair LDAP with Mailman it requires that the `group` found in
the LDAP matches a `group@listdomains` in Mailman. If a LDAP group doesn't
match a list in Mailman it will be ignored, in the same way, if a Mailman list
doesn't match any LDAP group it will be ignored too. In order to be part of the
sync process both LDAP group and Mailman list with the same name must exist.

For all the users present in the LDAP group, the program checks if they're
subscribed to the Mailman list and if not it will subscribed it. For all the
email address already subscribed to the Mailman list the program checks if
they're still present in the LDAP group and unsuscribe it if not. There's a
config parameter to define mail addresses that could be subscribed on list
and will be ignored when unsubscribing missing LDAP users.

If the config defines a catchall list all the users, wheter or not they have
been included as part of a list will be synced to this list.

License
-------

ldap2mailman was written by Sebastián Santisi and it's free software licensed
under the terms of the GPL license.
