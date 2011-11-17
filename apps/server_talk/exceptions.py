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
