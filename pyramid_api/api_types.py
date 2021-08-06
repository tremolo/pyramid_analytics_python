import base64
import copy
from enum import IntEnum

from dataclasses import (
    dataclass,
    field
)
from typing import (
    Any,
    Dict,
    List,
    Optional
)

def default_field(obj):
    return field(default_factory=lambda: copy.copy(obj))


class ClientLicenseType(IntEnum):
    none = 0
    viewer = 100
    professional = 200    

class AdminType(IntEnum):
    none = 0
    domainadmin = 1
    enterpriseadmin = 2

class UserStatusID(IntEnum):
    disabled = 0
    enabled = 1


class ServerType(IntEnum):
    none = 0
    ms_olap = 1
    ms_olap_tabular = 2
    powerpivot = 3
    in_memory = 4
    sqlserver = 5
    mysql = 6
    monetdb = 7
    postgresql = 8
    oracle = 9
    db2 = 10
    teradata = 11
    drill = 12
    pa_imdb = 13
    redshift = 14
    presto = 15
    athena = 16
    bigquery = 17
    hive = 18
    salesforce = 19
    sap_hana = 20
    googleanalytics = 21
    mongodbbicx = 22
    sqlserverazure = 23
    snowflake = 24
    sybase = 25
    firebird = 26
    facebook = 27
    vertica = 28
    twitter = 29
    odbcserver = 30
    sharepoint = 31
    sap_bw = 32
    azureblobstorage = 33
    amazons3storage = 34
    greenplum = 35
    exasol = 36
    memsql = 37
    mariadb = 38
    netezza = 39
    glue = 40
    impala = 41
    azuresynapse = 42
    odbcdirectquery = 43
    as400 = 44


class ServerAuthenticationMethod(IntEnum):
    userpassword = 0
    globalactivedirectory = 1
    specificactivedirectory = 2
    serviceaccount = 3
    enduser = 4
    defaultawscredentialsproviderchain = 5
    keytab = 6
    snc = 7
    sap_logon_ticket = 8
    saml = 9


class AccessType(IntEnum):
    none = 0
    read = 1
    write = 2
    view = 3
    admin = 4


class SearchRootFolderType(IntEnum):
    private = 0
    public = 1
    group = 2
    oneoff = 3
    deletedcontent = 4
    crosstenant = 5
    recent = 6
    favorite = 7


class SearchMatchType(IntEnum):
    contains = 0
    notcontains = 1
    equals = 2
    startswith = 3
    endswith = 4


class ContentType(IntEnum):
    none = 0
    asset = 1
    calculation = 2
    datadiscovery = 3
    etlflow = 4
    folder = 5
    publisher = 6
    storyboard = 8

# NOT THE SAME AS ABOVE!?!?!?!?
class ContentItemObjectType(IntEnum):
    asset = 0
    publisher = 1
    storyboard = 2
    calculation = 3
    datadiscovery = 4


class MaterializedItemType(IntEnum):
    none = 0
    database = 1
    modelingmodel = 2
    server = 3
    machinelearningmodel = 4
    schedule = 5
    model = 6
    output = 7


class RoleAssignmentType(IntEnum):
    usedefaultbehavior = 0
    forcepackageroles = 1
    forceexternalroles = 2
    forceparentroles = 3


# subclassing enums only works in 3.8+ so we'll be redundant
class MaterializedRoleAssignmentType(IntEnum):
    usedefaultbehavior = 0
    forcepackageroles = 1
    forceexternalroles = 2
    forceparentroles = 3


class ValidRootFolderType(IntEnum):
    private = 0
    public = 1
    group = 2


@dataclass
class ItemId:
    id: str
    name: str = None

@dataclass
class Role:
    tenantId: str
    roleName: str
    roleId: str = None
    roleSettings: str = None
    isHidden: bool = False
    isPrivate: bool = False
    isGroupRole: bool = False
    

@dataclass
class User:
    tenantId: str
    userName: str
    roleIds: List[str] = default_field([])
    clientLicenseType: ClientLicenseType = 0
    id: str = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    proxyAccount: Optional[str] = None
    adminType: AdminType = 0
    statusID: int = 1
    createdDate: Optional[int] = 0
    lastLoginDate: Optional[int] = 0
    # optional
    adDomainName: Optional[str] = None
    principalName: Optional[str] = None
    # missing from official spec
    inheritanceType: Optional[str] = None
    secondaryMobilePhone: Optional[str] = None


@dataclass
class Server:
    port: int
    serverName: str
    id: Optional[str] = None
    serverType: ServerType = 0
    serverIp: Optional[str] = None
    instanceName: Optional[str] = None
    writeCapable: int = 0
    optionalParameters: Optional[str] = None
    securedByUser: bool = False
    serverAuthenticationMethod: ServerAuthenticationMethod = 0
    userName: Optional[str] = None
    password: Optional[str] = None
    tenantId: Optional[str] = None
    additionalServerProperties: Dict = default_field({})
    useGlobalAccount: bool = False
    pulseClient: Optional[str] = None
    defaultDatabaseName: Optional[str] = None
    overlayPyramidSecurity: bool = False
    serverIpAndInstanceName: Optional[str] = None

@dataclass
class TenantSettings:
    showGroupFolder: Optional[bool] = None
    allowWebhookChannels: Optional[bool] = None

@dataclass
class TenantData:
    id: Optional[str]
    name: Optional[str]
    viewerSeats: Optional[int] = 0
    usedViewerSeats: Optional[int] = 0
    proSeats: Optional[int] = 0
    usedProSeats: Optional[int] = 0
    tenantSettings: Optional[TenantSettings] = None
    pulseKey: Optional[str] = None
    selectedUserDefaultsId: Optional[str] = None
    selectedUserDefaultsName: Optional[str] = None
    defaultThemeId: Optional[str] = None
    defaultAiServer: Optional[str] = None
    userDefaultsOverridable: Optional[bool] = None


@dataclass
class NewTenant:
    id: str
    name: str
    viewerSeats: int = 0
    proSeats: int = 0
    showGroupFolder: bool = False



@dataclass
class NotificationIndicatorsResult:
    models: Optional[int]
    subscriptions: Optional[int]
    alerts: Optional[int]
    publications: Optional[int]
    conversations: Optional[int]


@dataclass
class NewFolder:
    parentFolderId: str
    folderName: str
    folderId: Optional[str] = None


@dataclass
class SearchParams:
    searchString: str
    filterTypes: List[ContentType]
    searchMatchType: SearchMatchType = SearchMatchType.contains
    searchRootFolderType: SearchRootFolderType = SearchRootFolderType.public
    startCreatedDate: Optional[str] = None
    endCreatedDate: Optional[str] = None
    startModifiedDate: Optional[str] = None
    endModifiedDate: Optional[str] = None
    server: Optional[str] = None
    model: Optional[str] = None
    dataBase: Optional[str] = None
    isAdvancedSearch: bool = False
    folderPathToSearch: Optional[str] = None


@dataclass
class ConnectionStringProperties:
    id: Optional[str] = None
    modelId: Optional[str] = None
    modelName: Optional[str] = None
    serverId: Optional[str] = None
    serverName: Optional[str] = None
    dataBaseId: Optional[str] = None
    dataBaseName: Optional[str] = None
    connectionStringType: Optional[ServerType] = 0
    isDynamicModel: Optional[bool] = False
    modelParamsStatus: Optional[str] = None
    securityHash: Optional[str] = None

@dataclass
class ContentItem:
    id: Optional[str]
    parentId: Optional[str]
    caption: Optional[str]
    itemType: Optional[int]
    contentType: Optional[ContentType]
    createdBy: Optional[str] = None
    createdDate: Optional[int] = None
    version: Optional[str] = None
    modifiedDate: Optional[str] = None
    tenantId: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ModifiedItemsResult:
    success: bool
    modifiedList: List[ItemId] = default_field([])
    errorMessage: str = None


@dataclass
class MaterializedItemObject:
    itemId: str
    itemCaption: str = None
    itemType: MaterializedItemType = 0


@dataclass
class PieApiObject:
    rootFolderId: str
    fileZippedData: str # base64 encoded string of the file
    clashDefaultOption: int = 1
    rolesAssignmentType: RoleAssignmentType = RoleAssignmentType.forceparentroles
    roleIds: List[str] = None  # only relevent to RoleAssignmentType.ForceExternalRoles

    @staticmethod
    def dataFromPath(path_: str):
        with open(path_, 'rb') as f:
            bytes_ =  f.read()
            return bytes_.decode('ascii') 


@dataclass
class ImportApiResultObject:
    importDscMap: List[Dict] = default_field([])
    failedItems: List[Dict] = default_field([])
