from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def paginate(db: Session, query: Select, page: int = 1, page_size: int = 20) -> dict:
	page = max(page, 1)
	page_size = min(max(page_size, 1), 100)
	total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
	items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
	return {"total": total, "page": page, "page_size": page_size, "items": items}
