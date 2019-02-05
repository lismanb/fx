from sqlalchemy import Column, Integer, String, Numeric, DateTime
from fx.fxrates import db

class Storage(db.Model):
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    currency = Column(String(3), index=True, nullable=False)
    rate = Column(Numeric(decimal_return_scale=8))
    amount = Column(Numeric(decimal_return_scale=8))
    amount_usd = Column(Numeric(decimal_return_scale=8))
    rate_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))