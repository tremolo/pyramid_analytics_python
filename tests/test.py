import json
import logging
import os
from typing import (
    List
)
from uuid import uuid4

import pytest

from ..pyramid_api.api import (
    PasswordGrant,
    TokenGrant,
    API as PyramidAPI
)

from ..pyramid_api.api_types import (
    AccessType,
    AdminType,
    ConnectionStringProperties,
    ContentItem,
    ContentItemObjectType,
    ContentType,
    ClientLicenseType,
    ImportApiResultObject,
    RoleAssignmentType,
    UserStatusID,
    NotificationIndicatorsResult,
    User,
    MaterializedItemObject,
    ModifiedItemsResult,
    NewFolder,
    PieApiObject,
    Role,
    SearchMatchType,
    SearchParams,
    SearchRootFolderType,
    Server,
    ServerType,
    NewTenant,
    TenantData,
    ValidRootFolderType,
)

LOG = logging.getLogger(__name__)

# Credentials / Options

def get_from_env_or_settings(key, settings, _default=None):
    return os.environ.get(key) or settings.get(key, _default)

__settings = {}
try:
    with open('test_settings.json') as f:
        __settings = json.load(f)
except Exception:
    print('No test settings file found, only environment available')

DOMAIN = get_from_env_or_settings('pyramid_server_url', __settings, 'http://localhost:8181')
USER = get_from_env_or_settings('pyramid_server_admin_user', __settings, 'admin')
PW = get_from_env_or_settings('pyramid_server_admin_password', __settings, '')

# Test Values

TENANT_NAME = '_T_valid-tenant-name'
NEW_TENANT_ID = ''

ADMIN_ROLE_NAME = '_T_important-role'
ADMIN_ROLE_ID = ''
ADMIN_USER_NAME = 't_admin'
ADMIN_USER_PW = 'password'
USER_ROLE_NAME = '_T_not-important-role'
USER_ROLE_ID = ''


# integration only (requires PG)
PIE_PATH_DASH = get_from_env_or_settings(
    'pie_path_dash',
    __settings,
    './tests/content/TimeSeriesRadar.pie'
)
PIE_PATH_MODEL = get_from_env_or_settings(
    'pie_path_model',
    __settings,
    './tests/content/TSR_Model.pie'
)


PIE_CONTENT_NAME = get_from_env_or_settings('pie_content_name', __settings, 'TimeSeriesRadar')

# Postgres DataSource info
PG_NAME = 'TEST_POSTGRES'
PG_HOST = get_from_env_or_settings('postgres_host', __settings, '127.0.0.1')
PG_PORT = get_from_env_or_settings('postgres_port', __settings, '6549')
PG_USER = get_from_env_or_settings('postgres_user', __settings, 'postgres')
PG_PASSWORD = get_from_env_or_settings('postgres_pw', __settings, None)
PG_DB_NAME = get_from_env_or_settings('postgres_database', __settings, 'test_db')
PG_TABLE_NAME = get_from_env_or_settings('postgres_database', __settings, 'timeseries')
PG_DATABASE_ID = ''

# global test objects instead of proper fixtures as I am lazy.

API: PyramidAPI = None
USER_OBJ: User = None
TENANT_OBJ: TenantData = None

# Tests ...

@pytest.mark.unit
@pytest.mark.integration
def test__grants():
    global API
    assert(isinstance(API := PasswordGrant(DOMAIN, USER, PW).get_api(), PyramidAPI))
    # assert(isinstance(API := TokenGrant(DOMAIN, TOKEN).get_api(), PyramidAPI))


@pytest.mark.unit
@pytest.mark.integration
def test__get_user():

    global USER_OBJ        
    assert(isinstance(
        USER_OBJ := API.getMe(),
        User)
    )

@pytest.mark.unit
@pytest.mark.integration
def test__notifications_status():
    assert(isinstance(
        API.getNotificationIndicators(USER_OBJ.id),
        NotificationIndicatorsResult
    ))


@pytest.mark.unit
@pytest.mark.integration
def test__content_get_folders():

    assert(isinstance(
        folder := API.getUserPublicRootFolder(USER_OBJ.id),
        ContentItem
    ))
    
    assert(isinstance(
        API.getPrivateRootFolder(USER_OBJ.id),
        ContentItem
    ))

    assert(isinstance(
        API.getPrivateFolderForUser(USER_OBJ.id),
        ContentItem
    ))

    assert(isinstance(
        API.getUserGroupRootFolder(USER_OBJ.id),
        ContentItem
    ))

    for i in API.getFolderItems(USER_OBJ.id, folder.id):
        assert(isinstance(
            i,
            ContentItem
        ))

@pytest.mark.unit
@pytest.mark.integration
def test__tenancy_create():
    global NEW_TENANT_ID
    NEW_TENANT_ID = str(uuid4())
    assert(isinstance(
        API.createTenant(
            NewTenant(
                NEW_TENANT_ID,
                TENANT_NAME,
                1,
                1,
                True)),
        ModifiedItemsResult
    ))

    global TENANT_OBJ
    assert(isinstance(
        TENANT_OBJ := API.getTenantByName(TENANT_NAME),
        TenantData
    ))

    assert(TENANT_OBJ.name == TENANT_NAME)


@pytest.mark.unit
@pytest.mark.integration
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
    ADMIN_ROLE_ID = res.modifiedList[0].get('id')


@pytest.mark.unit
@pytest.mark.integration
def test__user_create():
    user_req: User = User(
        TENANT_OBJ.id,
        ADMIN_USER_NAME,
        password=ADMIN_USER_PW,
        roleIds=[ADMIN_ROLE_ID],
        adminType=AdminType.domainadmin,
        clientLicenseType=ClientLicenseType.professional,
    )
    assert(isinstance(
            result := API.createUserDb(user_req),
            ModifiedItemsResult
        ))

    assert(result.success == True)


@pytest.mark.integration
def test__data_source_create_PG():
    server_req: Server = Server(**{
        'serverName': PG_NAME,
        'serverType': ServerType.postgresql,
        'serverIp': PG_HOST,
        'port': PG_PORT,
        'serverAuthenticationMethod': 0,
        'userName': PG_USER,
        'password': PG_PASSWORD,
        'tenantId': NEW_TENANT_ID,
        'defaultDatabaseName': PG_DB_NAME
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
                PG_DB_NAME
            ),
            ModifiedItemsResult
        ))
    assert(result.success == True)
    databaseId: str = result.modifiedList[0].get('id')
    assert(databaseId)
    global PG_DATABASE_ID
    PG_DATABASE_ID = databaseId

    assert(isinstance(
            result := API.findServerByName(
                PG_NAME,
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

@pytest.mark.unit
@pytest.mark.integration
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
        'tenantId': NEW_TENANT_ID
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


@pytest.mark.integration
def test__upload_content():
    # make a folder in public content for the Content
    publicRoot: ContentItem = API.getPublicOrGroupFolderByTenantId(tenantId=NEW_TENANT_ID)
    new_folder_id = str(uuid4())
    folder_create_operation: ModifiedItemsResult = API.createNewFolder(
        NewFolder(
            folderId=new_folder_id,
            folderName='somechild',
            parentFolderId=publicRoot.id
    ))
    assert(folder_create_operation.success == True)
    # import the content
    importResult = API.importContent(
        PieApiObject(
            new_folder_id,
            PieApiObject.dataFromPath(PIE_PATH_DASH)
    ))
    assert(isinstance(importResult, ImportApiResultObject))
    # The return from the server is currently bugged and does 
    # notifiy the client of which IDs were created for the content
    res: ModifiedItemsResult = API.addRoleToItem(
        new_folder_id,
        ADMIN_ROLE_ID,
        AccessType.admin,
        True
    )
    assert(res.success == True)

    # # change the datasource to this tenant's connection
    result: List[MaterializedItemObject] = API.findServerByName(
        PG_NAME,
        SearchMatchType.contains
    )
    pg_server_id: str = result[0].itemId

    modelId = API.importModel(
            PG_DATABASE_ID,
            PieApiObject.dataFromPath(PIE_PATH_MODEL)
            # RoleAssignmentType.forceexternalroles,
            # [ADMIN_ROLE_ID]
    )
    assert(importResult)
    res = API.addRoleToModel(modelId, ADMIN_ROLE_ID, AccessType.write)
    assert(res.success == True)

    params = SearchParams(**{
        "searchString":PIE_CONTENT_NAME,
		"filterTypes":[ContentType.datadiscovery],
		"searchMatchType": SearchMatchType.equals,
		"searchRootFolderType": SearchRootFolderType.public
    })
    results: List[ContentItem] =  API.findContentItem(params)
    assert(len(results) > 0)
    assert(results[0].caption == PIE_CONTENT_NAME)
    LOG.debug(results[0])
    content_id = results[0].id

    props: ConnectionStringProperties = API.getItemConnectionString(
        content_id,
        ContentItemObjectType.datadiscovery
    )
    # old_connection_id = props[0].serverId
    old_connection_id = props[0].id
    
    res: ModifiedItemsResult = API.changeDataSource(
        old_connection_id,
        modelId,
        content_id
    )
    assert(res.success == True)


@pytest.mark.unit
@pytest.mark.integration
def test__get_content():
    pass


# @pytest.mark.unit
# @pytest.mark.integration
# def test__tenancy_delete():
#     assert(isinstance(
#             result := API.deleteTenants([TENANT_OBJ.id], True, True),
#             ModifiedItemsResult
#         ))

#     assert(result.success == True)

@pytest.mark.purge
def test__purge_remove_tenant():
    api = PasswordGrant(DOMAIN, USER, PW).get_api()
    tenant = api.getTenantByName(TENANT_NAME)
    api.deleteTenants([tenant.id], True, True)


@pytest.mark.unit
@pytest.mark.integration
def test__report__called_apis():
    if not API.called_endpoints:
        return
    for i in sorted(list(API.called_endpoints)):
        LOG.debug(i)

# assert(isinstance())
