"""Private dashboard API for a logged-in user — saved articles (bookmarks)
and the watchlist architecture-only placeholder (see backend/README.md's
"News Portal (Public)" / private dashboard section). Every route here
requires a valid session (`get_current_user`); there is no anonymous
access, unlike everything under /api/news.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.news import to_news_item
from app.database.session import get_db
from app.models.user import User
from app.schemas.user_dashboard import SavedArticlesOut, WatchlistAddRequest, WatchlistOut
from app.services.entity_repository import get_entities_for_articles
from app.services.news_repository import get_article_by_id
from app.services.saved_article_repository import list_saved_articles, save_article, unsave_article
from app.services.watchlist_repository import add_watchlist_symbol, list_watchlist_symbols, remove_watchlist_symbol

router = APIRouter(prefix="/api/user", tags=["user"])

MAX_WATCHLIST_SYMBOLS = 50


@router.get("/bookmarks", response_model=SavedArticlesOut)
async def get_bookmarks(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SavedArticlesOut:
    articles = await list_saved_articles(db, user.id)
    entities = await get_entities_for_articles(db, [a.id for a in articles])
    return SavedArticlesOut(items=[to_news_item(a, entities=entities.get(a.id)) for a in articles])


@router.post("/bookmarks/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_bookmark(
    article_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    article = await get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No article with id {article_id}")
    await save_article(db, user_id=user.id, article_id=article_id)


@router.delete("/bookmarks/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(
    article_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> None:
    await unsave_article(db, user_id=user.id, article_id=article_id)


@router.get("/watchlist", response_model=WatchlistOut)
async def get_watchlist(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> WatchlistOut:
    symbols = await list_watchlist_symbols(db, user.id)
    return WatchlistOut(symbols=symbols)


@router.post("/watchlist", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: WatchlistAddRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WatchlistOut:
    existing = await list_watchlist_symbols(db, user.id)
    if len(existing) >= MAX_WATCHLIST_SYMBOLS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Watchlist is capped at {MAX_WATCHLIST_SYMBOLS} symbols")

    await add_watchlist_symbol(db, user_id=user.id, symbol=payload.symbol.upper())
    symbols = await list_watchlist_symbols(db, user.id)
    return WatchlistOut(symbols=symbols)


@router.delete("/watchlist/{symbol}", response_model=WatchlistOut)
async def remove_from_watchlist(
    symbol: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> WatchlistOut:
    await remove_watchlist_symbol(db, user_id=user.id, symbol=symbol.upper())
    symbols = await list_watchlist_symbols(db, user.id)
    return WatchlistOut(symbols=symbols)
