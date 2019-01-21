import dataclasses

@dataclasses.dataclass
class Listing:
    ad_id: int
    url: str
    title: str
    description: str
    listing_id: int = dataclasses.field(default=None)
    contract_id: int = dataclasses.field(default=None)

@dataclasses.dataclass
class ListingWithChatId(Listing):
    chat_id: int = dataclasses.field(default=None)
    
    
@dataclasses.dataclass
class Contract:
    chat_id: int
    query: str
    is_active: bool
    contract_id: int = dataclasses.field(default=None)
    
    
