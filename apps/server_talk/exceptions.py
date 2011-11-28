class ServerTalkException(Exception):
    pass


class AnnounceClientError(ServerTalkException):
    pass
    
    
class NoSuchNode(ServerTalkException):
    pass


class HeartbeatError(ServerTalkException):
    pass


class InventoryHashError(ServerTalkException):
    pass


class ResourceListError(ServerTalkException):
    '''
    Raise when the client node is unable or receives bad data calling
    the resource-list service 
    '''

class NetworkResourceNotFound(ServerTalkException):
    pass


class NetworkResourceDownloadError(ServerTalkException):
    pass
