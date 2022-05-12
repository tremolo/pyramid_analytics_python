from dataclasses import asdict
import json
from json.decoder import JSONDecodeError
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
    ConnectionStringProperties,
    ContentItem,
    ContentType,
    ContentItemObjectType,
    ImportApiResultObject,
    ItemId,
    NotificationIndicatorsResult,
    MaterializedItemObject,
    MaterializedRoleAssignmentType,
    ModifiedItemsResult,
    NewFolder,
    NewTenant,
    PieApiObject,
    QueryExportData,
    User,
    Role,
    SearchParams,
    SearchMatchType,
    Server,
    ServerDetails,
    TenantData,
    ValidRootFolderType,
    MasterFlowValidationResult,
    ItemRolePair
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
            if 'error' in _json:
                raise APIException(f'Unexpected error returned from server: {_json.get("error")}')
            LOG.debug(json.dumps(_json, indent=2))
            return _json
        except JSONDecodeError:
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

    # to call any API that has not been explicitly defined
    # you can add an explicit API method later :-)
    #
    # api.generic('/API2/access/getUsersByName', {
    #   itemId:'abcd'
    # })
    def generic(self, apiName: str, parameters: Dict) -> Any:
        allParameters = {
            'auth': self.token
        }
        allParameters.update(parameters)
        res = self._call_api(
            apiName,
            allParameters
        )
        return res['data']

    ##
    # --- Access ---
    ##

    def getUsersByName(self, userName) -> List[User]:
        res = self._call_api(
            '/API2/access/getUsersByName',
            {
                'auth': self.token,
                'userName': userName
            }
        )
        return [User(**i) for i in res['data']]

    def getUsersByRole(self, roleId) -> List[User]:
        res = self._call_api(
            '/API2/access/getUsersByRole',
            {
                'auth': self.token,
                'roleId': roleId
            }
        )
        return [User(**i) for i in res['data']]

    def addUserToRole(self, userId: str, roleId: str)-> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/access/addUserToRole', {
                'auth': self.token,
                'addUserRoleData': {
                    'userId': userId,
                    'roleId': roleId
                }
            }
        )

    def addUsersToRole(self, userIds: List[str], roleId: str)-> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/access/addUsersToRole', {
                'auth': self.token,
                'addUsersRoleData': {
                    'userIds': userIds,
                    'roleId': roleId
                }
            }
        )
        # res = self._call_api(
        #     '/API2/access/getUsersByRole',
        #     {
        #         'auth': self.token,
        #         'roleId': roleId
        #     }
        # )
        # return [User(**i) for i in res['data']]
        
        
    ## identity ---

    def getMe(self) -> User: # user_id
        res = self._call_api(
            '/API2/access/getMe',
            {
                'auth': self.token
            })
        return User(**res['data'])

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
            raise err

    def authenticateAs(self, userIdentity: str):
        try:
            userToken = self._call_api(
                '/API2/auth/authenticateUserByToken',
                {
                    'data': {
                        'userIdentity': userIdentity,
                        'token': self.token
                    }
                }
            )
        except HTTPError as err:
            raise err
        # new API object for the new user
        return API(TokenGrant(domain = self.domain, token = userToken))

    def validate_grant(self, credential: TokenGrant):
        self.domain = credential.domain
        self.token = credential.token
        try:
            self.getMe()
        except HTTPError as err:
            raise APIException('Invalid Token') from err

    ##
    # --- Notifications ---
    ##

    def getNotificationIndicators(self, userId: str) -> NotificationIndicatorsResult:
        res = self._call_api(
            '/API2/notification/getNotificationIndicators',
            {
                'auth': self.token,
                'userId': userId
            })
        return NotificationIndicatorsResult(**res['data'])

    ##
    # --- Content ---
    ##

    def createNewFolder(self, new_folder: NewFolder) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/content/createNewFolder', {
                'auth': self.token,
                'folderTenantObject': self.__ignore_nulls(asdict(new_folder))
            }
        )

    def purgeContentItems(self, itemIds: List[str]) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/content/purgeContentItems', {
                'auth': self.token,
                'itemIds': itemIds
            }
        )


    def softDeleteContentItems(self, itemIds: List[str]) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/content/softDeleteContentItems', {
                'auth': self.token,
                'itemIds': itemIds
            }
        )

    def findContentItem(self, params: SearchParams) -> List[ContentItem]:
        res = self._call_api(
            '/API2/content/findContentItem',
            {
                'auth': self.token,
                'searchParams': self.__ignore_nulls(asdict(params))
            })
        return [ContentItem(**i) for i in res['data']]


    def getContentItemMetaData(self, itemId: str) -> ContentItem:
        res = self._call_api(
            '/API2/content/getContentItemMetaData',
            {
                'auth': self.token,
                'itemId': itemId
            })
        return ContentItem(**res['data'])


    def getContentItemSecurityRoles(self, itemId: str) -> List[Role]:
        res = self._call_api(
            '/API2/content/getContentItemSecurityRoles',
            {
                'auth': self.token,
                'contentItemId': itemId
            })
        return [Role(**i) for i in res['data']]


    def getUserPublicRootFolder(self, userId: str) -> ContentItem:
        res = self._call_api(
            '/API2/content/getUserPublicRootFolder',
            {
                'auth': self.token,
                'userId': userId
            })
        return ContentItem(**res['data'])

    def getPrivateRootFolder(self, userId: str) -> ContentItem:
        res = self._call_api(
            '/API2/content/getPrivateRootFolder',
            {
                'auth': self.token,
                'userId': userId
            })
        return ContentItem(**res['data'])

    def getPrivateFolderForUser(self, userId: str) -> ContentItem:
        res = self._call_api(
            '/API2/content/getPrivateFolderForUser',
            {
                'auth': self.token,
                'userId': userId
            })
        return ContentItem(**res['data'])

    def getPublicOrGroupFolderByTenantId(
        self,
        tenantId: str,
        rootFolderType: ValidRootFolderType = ValidRootFolderType.public
    ) -> ContentItem:

        res = self._call_api(
            '/API2/content/getPublicOrGroupFolderByTenantId',
            {
                'auth': self.token,
                'folderTenantObject': {
                    'validRootFolderType': rootFolderType,
                    'tenantId': tenantId
                }
            })
        return ContentItem(**res['data'])

    def getUserGroupRootFolder(self, userId: str) -> ContentItem:
        res = self._call_api(
            '/API2/content/getUserGroupRootFolder',
            {
                'auth': self.token,
                'userId': userId
            })
        return ContentItem(**res['data'])

    def getFolderItems(self, folderId) -> List[ContentItem]:
        res = self._call_api(
            '/API2/content/getFolderItems',
            {
                'auth': self.token,
                'folderId': folderId
            })
        return [ContentItem(**i) for i in res['data']]

    def addRoleToItem(
        self,
        itemId: str,
        roleId: str,
        accessType: AccessType = AccessType.read,
        propagateRoles: bool = False
        ) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/content/addRoleToItem',
            {
                'auth': self.token,
                'roleToItemApiData': {
                    'itemId': itemId,
                    'roleId': roleId,
                    'accessType': accessType,
                    'propagateRoles': propagateRoles
                }
        })

    def importContent(self, obj: PieApiObject) -> ImportApiResultObject:
        res = self._call_api(
            '/API2/content/importContent', {
                'auth': self.token,
                'pieApiObject': self.__ignore_nulls(asdict(obj))
            }
        )
        return ImportApiResultObject(**res['data'])

    # Tenant

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

    def getAllTenants(self) -> List[TenantData]:
        res = self._call_api(
            '/API2/access/getAllTenants',
            {
                'auth': self.token
        })
        return TenantData(**res['data'])

    def getTenantByName(self, name: str) -> List[TenantData]:
        res = self._call_api(
            '/API2/access/getTenantByName',
            {
                'auth': self.token,
                'tenantName': name
        })
        return TenantData(**res['data'])

    def getDefaultTenant(
        self
    ) -> str:
        res = self._call_api(
            '/API2/access/getDefaultTenant',
            {
                'auth': self.token
            })
        return res['data']

    def deleteTenants(
        self,
        tenantIds: List[str],
        delete_users: bool,
        delete_servers: bool
    ) -> ModifiedItemsResult:

        return self._call_expect_modified(
            '/API2/access/deleteTenants',
            {
                'auth': self.token,
                'data': {
                    'tenantIds': tenantIds,
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

    def deleteRole(
        self,
        roleId: str
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/access/deleteRole',
            {
                'auth': self.token,
                'roleId': roleId
            }
        )

    def getAllRoles(self) -> List[ItemId]:    
        res = self._call_api(
            '/API2/access/getAllRoles',
            {
                'auth': self.token
            }
        )
        return [ItemId(**i) for i in res['data']]

    ## User

    def createUserDb(self, user: User) -> ModifiedItemsResult:
        # See User for signature
        return self._call_expect_modified(
            '/API2/access/createUserDb',
            {
                'auth': self.token,
                'user': self.__ignore_nulls(asdict(user))
        })


    def deleteUser(
        self,
        userId: str
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/access/deleteUser',
            {
                'auth': self.token,
                'userId': userId
            }
        )


    ## dataSources
    
    ## Server
    def createDataServer(self, server: Server) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/createDataServer',
            {
                'auth': self.token,
                'serverData': self.__ignore_nulls(asdict(server))
        })
    
    def getServerDataById(self, dataServerId: str) -> Server:
        res = self._call_api(
            '/API2/dataSources/getServerDataById',
            {
                'auth': self.token,
                'dataServerId': dataServerId
        })
        return ServerDetails(**res['data'])

    def deleteDataSource(
        self,
        sourceId: str
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/dataSources/deleteDataSource',
            {
                'auth': self.token,
                'sourceId': sourceId
            }
        )

    def addRolesToServer(self, serverId: str, rolesAndAccess: List[ItemRolePair]) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/addRolesToServer',
            {
                'auth': self.token,
                'itemRoles': {
                    'itemId': serverId,
                    # 'serverId': serverId,
                    'itemRolePairList': [self.__ignore_nulls(asdict(i)) for i in rolesAndAccess]
                    # [
                    #     ItemRolePair(roleId, accessType)
                    # ]
                }
        })

    def addRolesToDataBase(
        self,
        databaseId: str,
        rolesAndAccess: List[ItemRolePair]
        # roleId: str,
        # accessType: AccessType = AccessType.read
    ) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/addRolesToDataBase',
            {
                'auth': self.token,
                'itemRoles': {
                    'itemId': databaseId,
                    # 'databaseId': databaseId,
                    'itemRolePairList': [self.__ignore_nulls(asdict(i)) for i in rolesAndAccess]
                    # [
                    #     ItemRolePair(roleId, accessType)
                    # ]
                }
        })

    def addRolesToModel(
        self,
        modelId: str,
        rolesAndAccess: List[ItemRolePair]
        # roleId: str,
        # accessType: AccessType = AccessType.read
    ) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/addRolesToDataBase',
            {
                'auth': self.token,
                'itemRoles': {
                    'itemId': modelId,
                    # 'modelId': modelId,
                    'itemRolePairList': [self.__ignore_nulls(asdict(i)) for i in rolesAndAccess]
                    # [
                    #     ItemRolePair(roleId, accessType)
                    # ]
                }
        })

    def addRolesToModelAndBubbleUp(
        self,
        modelId: str,
        rolesAndAccess: List[ItemRolePair]
        # roleId: str,
        # accessType: AccessType = AccessType.read
    ) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/addRolesToItemAndBubbleUp',
            {
                'auth': self.token,
                'itemRoles': {
                    'itemId': modelId,
                    # 'modelId': modelId,
                    'itemRolePairList': [self.__ignore_nulls(asdict(i)) for i in rolesAndAccess]
                    # [
                    #     ItemRolePair(roleId, accessType)
                    # ]
                }
        })


    def addRolesToServerAndPropagate(
        self,
        serverId: str,
        rolesAndAccess: List[ItemRolePair]
        # roleId: str,
        # accessType: AccessType = AccessType.read
    ) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/addRolesToItemAndPropagate',
            {
                'auth': self.token,
                'itemRoles': {
                    'itemId': serverId,
                    # 'serverId': serverId,
                    'itemRolePairList': [self.__ignore_nulls(asdict(i)) for i in rolesAndAccess]
                    # [
                    #     ItemRolePair(roleId, accessType)
                    # ]
                }
        })

    

    def changeDataSource(self, oldConnection: str, newConnection: str, itemId: str) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/dataSources/changeDataSource',
            {
                'auth': self.token,
                'dscApiData': {
                    'fromConnId': oldConnection,
                    'toConnId': newConnection,
                    'itemId': itemId
                }
        })

    
    def getDataSourcesByTenant(self, tenantId: str) -> List[MaterializedItemObject]:
        res = self._call_api(
            '/API2/dataSources/getDataSourcesByTenant',
            {
                'auth': self.token,
                'tenantId': tenantId
        })
        return [MaterializedItemObject(**i) for i in res['data']]
    

    def getAllConnectionStrings(self) -> List[ConnectionStringProperties]:
        res = self._call_api(
            '/API2/dataSources/getAllConnectionStrings',
            {
                'auth': self.token
        })
        return [ConnectionStringProperties(**i) for i in res['data']]
    
    def getItemConnectionString(
        self,
        itemId: str,
        itemType: ContentItemObjectType,
    ) -> List[ConnectionStringProperties]:

        res = self._call_api(
            '/API2/dataSources/getItemConnectionString',
            {
                'auth': self.token,
                'pyramidItemIdentifier': {
                    'itemId': itemId,
                    'itemTypeObject': itemType
                }
        })
        return [ConnectionStringProperties(**i) for i in res['data']]


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
        databaseId: str,
        pieObj: Any,
        roleAssignmentType: MaterializedRoleAssignmentType = 0,
        roles: List[str] = None
    ) -> str: 
        body = {
            'fileZippedData': pieObj,
            'databaseId': databaseId,
            'materializedRoleAssignmentType': roleAssignmentType,
            'rolesIds' : roles
        }
        if roleAssignmentType != 2:
            del body['rolesIds']

        res = self._call_api(
            '/API2/dataSources/importModel', {
                'modelApiObject': body,
                'auth': self.token
            }
        )
        # returns {'data': '36da9e00-f31d-424c-a247-576402695fd6'}
        # connectionStringId
        return res['data']


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

    def deleteDataBase(
        self,
        databaseId: str
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/dataSources/deleteDataBase',
            {
                'auth': self.token,
                'databaseId': databaseId
            }
        )

    def validateMasterFlow(
        self,
        itemId: str,
        executionTitle: str = 'validation'
    ) -> MasterFlowValidationResult:   
        res =  self._call_api(
            '/API2/dataSources/validateMasterFlow',
            {
                'auth': self.token,
                'validateMasterFlowObject': {
                    'itemId': itemId,
                    'executionTitle': executionTitle
                }
            }
        )
        return MasterFlowValidationResult(**res['data'])

    def updateSourceNodeConnection(
        self,
        dataFlowNodeId: str,
        itemId: str,
        serverId: str = None,
        databaseName: str = None
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/dataSources/updateSourceNodeConnection',
            {
                'auth': self.token,
                'dataFlowNodeId': dataFlowNodeId,
                'serverId': serverId,
                'databaseName': databaseName,
                'itemId': itemId,
            }
        )

    def updateTargetNodeConnection(
        self,
        dataFlowNodeId: str,
        itemId: str,
        serverId: str = None,
        databaseName: str = None,
        useExistingDatabase: bool = True
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/dataSources/updateTargetNodeConnection',
            {
                'auth': self.token,
                'dataFlowNodeId': dataFlowNodeId,
                'serverId': serverId,
                'databaseName': databaseName,
                'useExistingDatabase': useExistingDatabase,
                'itemId': itemId,
            }
        )


    def updateVariableConnection(
        self,
        dataFlowNodeId: str,
        variableName: str,
        serverId: str = None,
        databaseName: str = None
    ) -> ModifiedItemsResult:    
        return self._call_expect_modified(
            '/API2/dataSources/updateVariableConnection',
            {
                'auth': self.token,
                'dataFlowNodeId': dataFlowNodeId,
                'serverId': serverId,
                'databaseName': databaseName,
                'variableName': variableName,
            }
        )

    ##
    # --- Tasks ---
    ##

    # TODO Write Tests

    def reRunTask(self, taskId: str) -> ModifiedItemsResult:
        return self._call_expect_modified(
            '/API2/tasks/reRunTask',
            {
                'auth': self.token,
                'taskId': taskId
        })

    def runSchedule(self, scheduleId: str, check_triggers=True) -> str: # id
        return self._call_api(
            '/API2/tasks/runSchedule',
            {
                'auth': self.token,
                'data':{
                    'scheduleId': scheduleId,
                    'checkTriggers': check_triggers
                }
        })

    ##
    # --- Query ---
    ##

    def extractQueryResult(self, queryData: QueryExportData) -> str:
        res = self._call_api(
            '/API2/query/extractQueryResult',
            {
                'auth': self.token,
                'data':  self.__ignore_nulls(asdict(queryData))
            })
        return res['data']
