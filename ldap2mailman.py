# ldap2mailman 0.1, an LDAP to Mailman3 syncer.
# Copyright (C) 2022 Sebastián Santisi <ssantisi@fi.uba.ar>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>. 

from config import config
    
import ldap
from mailmanclient import Client
import sys

log_level = 0
def log(level, msg):
    if level > log_level:
        return
    print(msg)


def main():
    c = ldap.initialize(config['ldap_server'])
    if config['use_kerberos']:
        c.sasl_gssapi_bind_s()
    else:
        c.simple_bind_s(config['admin_user'], config['admin_password'])
    
    client = Client(config['rest_uri'], config['rest_user'], config['rest_password'])
    
    lists = set()
    users_by_groups = {}
    groups_by_gidnumber = {}

    log(2, 'Retrieving LDAP groups...')
    for dn,data in c.search_s('ou=groups,%s' % (config['base']), ldap.SCOPE_SUBTREE, '(objectclass=posixgroup)', ['cn', 'gidNumber', 'memberUid']):
        gid = str(data['cn'][0], 'utf8')
        gidnumber = int(data['gidNumber'][0])
        log(3, 'Processing %s group...' % gid)
    
        groups_by_gidnumber[gidnumber] = gid

        try:
            _ = client.get_list('%s@%s' % (gid, config['lists_domain']))
        except:
            log(3, 'Group %s not in lists' % gid)
            continue
    
        log(2, 'Group %s present in lists, adding to process' % gid)

        lists.add(gid)

        if 'memberUid' in data:
            for uid in data['memberUid']:
                uid = str(uid, 'utf8')
                log(3, 'Adding user %s to %s group' % (uid, gid))
                users_by_groups.setdefault(gid, []).append(uid)

    log(2, 'Retrieved groups, found: %s' % ', '.join(lists))

    mails_by_uid = {}
    uids_by_mail = {}

    log(2, 'Retrieving LDAP users...')
    for dn,data in c.search_s('ou=people,%s' % (config['base']), ldap.SCOPE_SUBTREE, '(objectclass=posixaccount)', ['uid', 'gidNumber', 'mail']):
        uid = str(data['uid'][0], 'utf8')
        gidnumber = int(data['gidNumber'][0])

        if 'mail' not in data:
            log(3, 'User %s has not mail' % uid)
            continue
    
        mail = str(data['mail'][0], 'utf8')

        gid = groups_by_gidnumber[gidnumber]

        log(3, 'Found user %s with group %s and mail %s' % (uid, gid, mail))
    
        mails_by_uid[uid] = mail
        uids_by_mail[mail] = uid
    
        users_by_groups.setdefault(gid, []).append(uid)
   
    log(2, 'Processing lists suscriptions...')
    for gid in lists:
        l = client.get_list('%s@%s' % (gid, config['lists_domain']))
    
        log(2, 'Adding members to %s@%s list...' % (gid, config['lists_domain']))
        for uid in users_by_groups[gid]:
            log(3, 'Checking if %s already in list...' % uid)
            if not l.is_member(mails_by_uid[uid]):
                log(1, 'Adding %s as a member of %s@%s' % (uid, gid, config['lists_domain']))
                l.subscribe(mails_by_uid[uid], pre_verified=True, pre_confirmed=True, pre_approved=True, send_welcome_message=False)
   
        log(2, 'Removing members from %s@%s list...' % (gid, config['lists_domain']))
        for m in l.members:
            mail = m.rest_data['email']
            log(3, 'Checking if %s not in %s group...' % (mail, gid))
    
            if mail in config['exclude_mails']:
                log(3, 'Ignoring %s' % mail)
                continue
    
            if mail not in uids_by_mail or uids_by_mail[mail] not in users_by_groups[gid]:
                log(1, 'Removing %s as member of %s@%s' % (mail, gid, config['lists_domain']))
                l.unsubscribe(mail)
    
    everyone = None
    try: everyone = client.get_list(config['catchall_list'])
    except: pass
    
    if everyone:
        log(3, 'Found catchall list')
        log(2, 'Adding members to %s catchall list...' % config['catchall_list'])
        for mail in uids_by_mail:
            log(3, 'Checking if %s already in list...' % uids_by_mail[mail])
            if not everyone.is_member(mail):
                log(1, 'Adding %s as a member of %s' % (uids_by_mail[mail], config['catchall_list']))
                everyone.subscribe(mail, pre_verified=True, pre_confirmed=True, pre_approved=True, send_welcome_message=False)
    
        log(2, 'Removing members from %s catchall list...' % (config['lists_domain']))
        for m in everyone.members:
            mail = m.rest_data['email']
            log(3, 'Checking if %s not in LDAP...' % mail)
    
            if mail in config['exclude_mails']:
                log(3, 'Ignoring %s' % mail)
                continue
    
            if mail not in uids_by_mail:
                log(1, 'Removing %s as member of %s' % (mail, config['catchall_list']))
                everyone.unsubscribe(mail)

    c.unbind_s()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h':
            print('Usage: %s [-v]\n-v,-vv,-vvv: Level of verbosity' % sys.argv[0])
            sys.exit(0)
        if sys.argv[1].startswith('-v'):
            log_level = len(sys.argv[1]) - 1

    main()
