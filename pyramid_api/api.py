from dataclasses import asdict
import json
import logging
from typing import (
    Any,
    Dict,
    List,
    Union
)

import requests
from requests.exceptions import HTTPError

from .api_types import (
    AccessType,
    ContentFolder,
    NotificationIndicatorsResult,
    MaterializedItemObject,
    MaterializedRoleAssignmentType,
    ModifiedItemsResult,
    NewTenant,
    User,
    Role,
    SearchMatchType,
    Server,
    TenantData,
)

LOG = logging.getLogger(__name__)

##
# --- Auth ---
##

class Grant:
    domain: str = None
    token: str = None

    def get_api(self) -> 'API':
        return API(self)


class PasswordGrant(Grant):
    username: str
    password: str

    def __init__(self, domain: str, username: str, password: str):
        self.domain = domain
        self.username = username
        self.password = password


class TokenGrant(Grant):
    
    def __init__(self, domain: str, token: str):
        self.domain = domain
        self.token = token


##
# --- Exceptions ---
##

class APIException(Exception):
    pass


##
# --- API ---
##

class API:

    domain: str = None
    token: str = None
    debug: bool = False
    called_endpoints = None

    def __init__(self, credential: Grant):
        if LOG.getEffectiveLevel() is logging.DEBUG:
            self.called_endpoints = set()
            LOG.warn('LogLevel is Debug! API will log ALL requests and responses!')
            LOG.warn('Unless you are debugging you do not want this!')
        if isinstance(credential, PasswordGrant):
            self.authenticate(credential)
        elif isinstance(credential, TokenGrant):
            self.validate_grant(credential)

    def _call_api(self, endpoint: str, data: Any, method: str = 'POST'):
        if self.called_endpoints != None:
            self.called_endpoints.add(endpoint)
        res = requests.request(
            method=method,
            url=f'{self.domain}{endpoint}',
            json=data
        )
        LOG.debug(f'{endpoint}')
        LOG.debug(json.dumps(data, indent=2))
        try:
            res.raise_for_status()
        except HTTPError as her:
            LOG.error(her)
            LOG.error(f'error content: {res.text}')
            raise her
        LOG.debug(f'status -> {res.status_code}')
        try:
            _json = res.json()
            LOG.debug(json.dumps(_json, indent=2))
            return _json
        except:
            LOG.debug(res.text)
            return res.text

    def _call_expect_modified(self, ep: str, data: Any) -> ModifiedItemsResult: 
        res = self._call_api(ep, data)
        return ModifiedItemsResult(**res['data'])

    def _call_expect_query_res(self, ep: str, data: Any) -> List[MaterializedItemObject]:
        res = self._call_api(ep, data)
        return [MaterializedItemObject(**i) for i in res['data']]
    ##
    # --- Utils ---
    ##


    def __ignore_self(self, locals: Dict):
        return {k:v for k, v in locals.items() if k != 'self'}

    def __ignore_nulls(self, d: Dict):
        return {k: v for k, v in d.items() if v != None}

    ##
    # --- Auth ---
    ##

    def authenticate(self, credential: PasswordGrant):
        self.domain = credential.domain
        try:
            self.token = self._call_api(
                '/API2/auth/authenticateUser',
                {
                    'data': {
                        'userName': credential.username,
                        'password': credential.password
                    }
                }
            )
        except HTTPError as err:
            raise APIException('Invalid Credentials') from err

    def validate_grant(self, credential: TokenGrant):
        self.domain = credential.domain
        self.token = credential.token
        try:
            self.getMe()
        except HTTPError as err:
            raise APIException('Invalid Token') from err

    ##
    # --- Identity ---
    ##

    def getMe(self) -> User: # user_id
        res = self._call_api(
            '/API2/access/getMe',
            {
                'auth': self.token
            })
        return User(**res['data'])

    ##
    # --- Notifications ---
    ##

    def getNotificationIndicators(self, user_id: str) -> NotificationIndicatorsResult:
        res = self._call_api(
            '/API2/notification/getNotificationIndicators',
            {
                'auth': self.token,
                'userId': user_id
            })
        return NotificationIndicatorsResult(**res['data'])

    ##
    # --- Content ---
    ##

    def getUserPublicRootFolder(self, user_id: str) -> ContentFolder:
        res = self._call_api(
            '/API2/content/getUserPublicRootFolder',
            {
                'auth': self.token,
                'userId': user_id
            })
        return ContentFolder(**res['data'])

    def getPrivateRootFolder(self, user_id: str) -> ContentFolder:
        res = self._call_api(
            '/API2/content/getPrivateRootFolder',
            {
                'auth': self.token,
                'userId': user_id
            })
        return ContentFolder(**res['data'])

    def getPrivateFolderForUser(self, user_id: str) -> ContentFolder:
        res = self._call_api(
            '/API2/content/getPrivateFolderForUser',
            {
                'auth': self.token,
                'userId': user_id
            })
        return ContentFolder(**res['data'])

    def getUserGroupRootFolder(self, user_id: str) -> ContentFolder:
        res = self._call_api(
            '/API2/content/getUserGroupRootFolder',
            {
                'auth': self.token,
                'userId': user_id
            })
        return ContentFolder(**res['data'])

    def getFolderItems(self, user_id: str, folder_id) -> List[ContentFolder]:
        res = self._call_api(
            '/API2/content/getFolderItems',
            {
                'auth': self.token,
                'userId': user_id,
                'folderId': folder_id
        })
        return [ContentFolder(**i) for i in res['data']]

    ##
    # --- Management ---
    ##

    ## Tenant

    def createTenant(
        self,
        tenant: NewTenant
    ) -> ModifiedItemsResult:

        return  self._call_expect_modified(
            '/API2/access/createTenant',
            {
                'auth': self.token,
                'tenant': asdict(tenant)
        })


    def getTenantByName(self, name: str) -> TenantData:
        res = self._call_api(
            '/API2/access/getTenantByName',
            {
                'auth': self.token,
                'tenantName': name
        })
        return TenantData(**res['data'])

    def deleteTenants(
        self,
        tenant_ids: List[str],
        delete_users: bool,
        delete_servers: bool
    ) -> ModifiedItemsResult:

        return self._call_expect_modified(
            '/API2/access/deleteTenants',
            {
                'auth': self.token,
                'data': {
                    'tenantIds': tenant_ids,
                    'deleteUsers': delete_users,
                    'deleteServers': delete_servers
                }
        })

    ## Role

    def createRole(
        self,
        role: Role
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/access/createRole',
            {
                'auth': self.token,
                'roleData': asdict(role)
            }
        )

    ## User

    def createUserDb(self, user: User) -> ModifiedItemsResult:
        # See User for signature
        return self._call_expect_modified(
            '/API2/access/createUserDb',
            {
                'auth': self.token,
                'user': self.__ignore_nulls(asdict(user))
        })


    ## Server
    def createDataServer(self, server: Server) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/createDataServer',
            {
                'auth': self.token,
                'serverData': self.__ignore_nulls(asdict(server))
        })

    def addRoleToServer(self, server_id: str, role_id: str, access_type: AccessType) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/addRolesToServer',
            {
                'auth': self.token,
                'itemRoles': {
                    'itemId': server_id,
                    'itemRolePairList': [{
                        'roleId': role_id,
                        'accessType': access_type
                    }]
                }
        })

    def recognizeDataBase(self, server_id: str, db_name: str) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/recognizeDataBase',
            {
                'auth': self.token,
                'dataBaseRecognitionObject': {
                    'serverId': server_id,
                    'dbName': db_name
                }
        })
    
    def findServerByName(self, name: str, query_type: SearchMatchType = 1
        ) -> List[MaterializedItemObject]:
        
        return self._call_expect_query_res(
            '/API2/dataSources/findServerByName',
            {
                'auth': self.token,
                'searchCriteria': {
                    'searchValue': name,
                    'searchMatchType': query_type
                }
        })
    
    def importModel(
        self,
        server_id: str,
        file_obj: Any,
        role_type: MaterializedRoleAssignmentType = 0,
        roles: List[str] = None
    ) -> bool: 
        body = {
            'fileZippedData': file_obj,
            'databaseId': server_id,
            'materializedRoleAssignmentType': role_type,
            'rolesIds' : roles
        }
        if role_type != 2:
            del body['rolesIds']

        return self._call_api(
            '/API2/dataSources/importModel', {
                'modelApiObject': body
            }
        )
        

    ##
    # --- Tasks ---
    ##

    # TODO Write Tests

    def reRunTask(self, task_id: str) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/tasks/reRunTask',
            {
                'auth': self.token,
                'taskId': task_id
        })

    def runSchedule(self, schedule_id: str, check_triggers=True) -> str: # id
        return self._call_api(
            '/API2/tasks/runSchedule',
            {
                'auth': self.token,
                'data':{
                    'scheduleId': schedule_id,
                    'checkTriggers': check_triggers
                }
        })
