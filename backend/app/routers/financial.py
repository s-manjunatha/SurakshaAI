from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional

from app.database import get_db
from app.auth import get_current_user, require_permission
from app.models import User, Transaction, BankAccount
from app.schemas import TransactionResponse, PaginatedResponse

router = APIRouter(prefix="/financial", tags=["Financial Crime"])


@router.get("/transactions", response_model=PaginatedResponse)
async def list_transactions(
    suspicious_only: bool = False, fir_id: Optional[UUID] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("read:financial")),
):
    query = select(Transaction)
    if suspicious_only:
        query = query.where(Transaction.is_suspicious == True)
    if fir_id:
        query = query.where(Transaction.fir_id == fir_id)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Transaction.transaction_date.desc()).offset((page - 1) * page_size).limit(page_size))

    items = []
    for t in result.scalars():
        from_acc = to_acc = None
        if t.from_account_id:
            fa = (await db.execute(select(BankAccount.account_number).where(BankAccount.id == t.from_account_id))).scalar()
            from_acc = fa
        if t.to_account_id:
            ta = (await db.execute(select(BankAccount.account_number).where(BankAccount.id == t.to_account_id))).scalar()
            to_acc = ta
        items.append(TransactionResponse(
            id=t.id, amount=float(t.amount), transaction_date=t.transaction_date,
            transaction_type=t.transaction_type, is_suspicious=t.is_suspicious,
            suspicion_reason=t.suspicion_reason, from_account=from_acc, to_account=to_acc,
        ))

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=max(1, (total + page_size - 1) // page_size))


@router.get("/flagged-accounts")
async def flagged_accounts(db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("read:financial"))):
    result = await db.execute(select(BankAccount).where(BankAccount.is_flagged == True).limit(50))
    return [{"id": str(a.id), "account_number": a.account_number, "bank_name": a.bank_name, "holder": a.account_holder_name} for a in result.scalars()]


@router.get("/suspicious-patterns")
async def suspicious_patterns(db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("read:financial"))):
    result = await db.execute(text("""
        SELECT ba.account_number, ba.bank_name, COUNT(t.id) as tx_count,
               SUM(t.amount) as total_amount, COUNT(*) FILTER (WHERE t.is_suspicious) as suspicious_count
        FROM bank_accounts ba
        JOIN transactions t ON t.from_account_id = ba.id OR t.to_account_id = ba.id
        WHERE t.transaction_date >= NOW() - INTERVAL '30 days'
        GROUP BY ba.id, ba.account_number, ba.bank_name
        HAVING COUNT(*) FILTER (WHERE t.is_suspicious) > 0 OR SUM(t.amount) > 1000000
        ORDER BY suspicious_count DESC, total_amount DESC
        LIMIT 20
    """))
    return [{"account": r[0], "bank": r[1], "transactions": r[2], "total_amount": float(r[3]), "suspicious": r[4]} for r in result.all()]
