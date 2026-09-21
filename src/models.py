from pydantic import BaseModel, HttpUrl


class Book(BaseModel):
    title: str
    price_text: str
    price_gbp: float
    product_url: HttpUrl
    availability_text: str | None = None
    rating_text: str | None = None
    description: str | None = None
    source_page: HttpUrl
    fetched_at: str