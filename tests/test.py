import logging
from uuid import uuid4

import pytest

from ..pyramid_api.api import (
    PasswordGrant,
    TokenGrant,
    API as PyramidAPI
)

from ..pyramid_api.api_types import (
    AccessType,
    ContentFolder,
    ClientLicenseType,
    UserStatusID,
    NotificationIndicatorsResult,
    User,
    MaterializedItemObject,
    ModifiedItemsResult,
    Role,
    SearchMatchType,
    Server,
    ServerType,
    NewTenant,
    TenantData,
)

LOG = logging.getLogger(__name__)

# Credentials / Options
DOMAIN = 'http://localhost:9081'
USER = 'admin'
# PW = 'wrong'
PW = 'admin'
TOKEN = 'lx8p37Yzqwj26ofVxbHD4j/3Ky79rNOUAGkGOqxjFtNEn0/FKrfc+nIrzppDrtlHyRSitxnYv6d1kQBDvQe2Zk99YyI9Dgz3Vj/QKLE+f0Im8UTILfnN95WJ4+l/SBEcHVOLnMFC2u7dW8OQNyZq2JUqbJT1gR4YcMIZBqTXVu1Rb/NdRLa1AUHMVl3m6H+ijQUo7E/l1UyItqgiVXcJbI+J+Ie6oGildOclD1icu79niXJKh3SES0ukf3c6V6W/cZIEqf8BZ94KQAPNsYP+Vtm+9PM046QAVBHr86xp09rSBcEuS9qE5gQRBUcPWlTiPRCHnY4Wp1z4wQnynSgVsjkcobVKgHUDmmVEX65SxpDQRELeTpv98lQUS8EKL+tbVJoeVLA/vGwe1H7lK8dM7A=='
# TOKEN = ''


# Test Values

TENANT_NAME = '_T_valid-tenant-name'

ADMIN_ROLE_NAME = '_T_important-role'
ADMIN_ROLE_ID = ''
ADMIN_USER_NAME = '_T_an-admin-user'
USER_ROLE_NAME = '_T_not-important-role'
USER_ROLE_ID = ''

# global test objects instead of proper fixtures as I am lazy.

API: PyramidAPI = None
USER_OBJ: User = None
TENANT_OBJ: TenantData = None

# Tests ...

def test__grants():
    global API
    assert(isinstance(API := PasswordGrant(DOMAIN, USER, PW).get_api(), PyramidAPI))
    # assert(isinstance(API := TokenGrant(DOMAIN, TOKEN).get_api(), PyramidAPI))


def test__get_user():

    global USER_OBJ        
    assert(isinstance(
        USER_OBJ := API.getMe(),
        User)
    )

def test__notifications_status():
    assert(isinstance(
        API.getNotificationIndicators(USER_OBJ.id),
        NotificationIndicatorsResult
    ))


def test__content_get_folders():

    assert(isinstance(
        folder := API.getUserPublicRootFolder(USER_OBJ.id),
        ContentFolder
    ))
    
    assert(isinstance(
        API.getPrivateRootFolder(USER_OBJ.id),
        ContentFolder
    ))

    assert(isinstance(
        API.getPrivateFolderForUser(USER_OBJ.id),
        ContentFolder
    ))

    assert(isinstance(
        API.getUserGroupRootFolder(USER_OBJ.id),
        ContentFolder
    ))

    for i in API.getFolderItems(USER_OBJ.id, folder.id):
        assert(isinstance(
            i,
            ContentFolder
        ))

def test__tenancy_create():
    assert(isinstance(
        API.createTenant(
            NewTenant(
                str(uuid4()),
                TENANT_NAME,
                1,
                0,
                True)),
        ModifiedItemsResult
    ))

    global TENANT_OBJ
    assert(isinstance(
        TENANT_OBJ := API.getTenantByName(TENANT_NAME),
        TenantData
    ))

    assert(TENANT_OBJ.name == TENANT_NAME)


def test__role_create():
    assert(isinstance(
        res := API.createRole(
            Role(
                TENANT_OBJ.id,
                ADMIN_ROLE_NAME
            )
        ),
        ModifiedItemsResult
    ))
    global ADMIN_ROLE_ID
    ADMIN_ROLE_ID = res.modifiedList[0].get('id');


def test__user_create():
    user_req: User = User(
        TENANT_OBJ.id,
        ADMIN_USER_NAME,
        password='somepassword',
        roleIds=[ADMIN_ROLE_ID],
        clientLicenseType=ClientLicenseType.viewer,
    )
    assert(isinstance(
            result := API.createUserDb(user_req),
            ModifiedItemsResult
        ))

    assert(result.success == True)


def test__data_source_create():
    _SRV_NAME = 'fake-internal-imdb'
    server_req: Server = Server(**{
        'serverName': _SRV_NAME,
        'serverType': ServerType.pa_imdb,
        'serverIp': '127.0.0.1',
        'port': 3308,
        'serverAuthenticationMethod': 0,
        'userName': '',
        'password': '',
        'tenantId': '0bd28c30-a313-4f37-9646-46c16b1f6a72'
    })
    assert(isinstance(
            result := API.createDataServer(server_req),
            ModifiedItemsResult
        ))
    assert(result.success == True)

    ds_id = result.modifiedList[0].get('id');
    assert(isinstance(
            result := API.addRoleToServer(
                ds_id,
                ADMIN_ROLE_ID,
                AccessType.admin
            ),
            ModifiedItemsResult
        ))
    assert(result.success == True)

    assert(isinstance(
            result := API.recognizeDataBase(
                ds_id,
                'somedb'
            ),
            ModifiedItemsResult
        ))
    # TODO make this work with a real external DB
    assert(result.success == False)

    assert(isinstance(
            result := API.findServerByName(
                _SRV_NAME,
                SearchMatchType.contains
            ),
            list
        ))
    all_ids = [r.itemId for r in result]
    assert(ds_id in all_ids)

    assert(isinstance(
            result := API.findServerByName(
                'fake-server-name',
                SearchMatchType.equals
            ),
            list
        ))
    assert(len(result) == 0)


def test__tenancy_delete():
    assert(isinstance(
            result := API.deleteTenants([TENANT_OBJ.id], True, True),
            ModifiedItemsResult
        ))

    assert(result.success == True)

def test__report__called_apis():
    if not API.called_endpoints:
        return
    for i in sorted(list(API.called_endpoints)):
        LOG.debug(i)

# assert(isinstance())
