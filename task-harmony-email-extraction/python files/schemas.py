from pydantic import BaseModel
from typing import Optional

class EmailExtraction(BaseModel):
    id: str
    product_line: Optional[str]
    origin_port_code: Optional[str]
    origin_port_name: Optional[str]
    destination_port_code: Optional[str]
    destination_port_name: Optional[str]
    incoterm: Optional[str]
    cargo_weight_kg: Optional[float]
    cargo_cbm: Optional[float]
    is_dangerous: Optional[bool]
