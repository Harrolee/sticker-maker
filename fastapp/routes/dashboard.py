from fasthtml.common import *
from fastapp.db.models import Sticker, StickerStatus, User
from sqlalchemy.orm import Session
from sqlalchemy import select
import os

# Simple admin check - matches admin.py
ADMIN_USERS = os.environ.get('ADMIN_USERS', 'admin').split(',')

def setup_dashboard_routes(app: FastHTML, rt):
    @rt("/dashboard")
    def get(auth, app: FastHTML):
        if not auth: return RedirectResponse('/login', 303)

        db_client = app.state.db_client

        with Session(db_client.engine) as session:
            # Look up user_id from username
            user = session.query(User).filter(User.username == auth).first()
            if not user:
                return Titled("Dashboard", P("User not found. Please log in again."))

            user_stickers = session.execute(
                select(Sticker).where(Sticker.creator == user.user_id)
            ).scalars().all()
        
        # Build action buttons
        action_buttons = [A("Create New Sticker", href="/", cls="button")]
        if auth in ADMIN_USERS:
            action_buttons.append(A("Admin: Batch Upload", href="/admin", cls="button", style="margin-left: 10px;"))

        return Titled(
            f"Your Stickers",
            Div(
                Div(*action_buttons),
                Div(
                    H3("Drafts"),
                    Ul(
                        *[sticker_to_li(s, app) for s in user_stickers if not s.storefront_product_id],
                        id="drafts-list"
                    ),
                    H3("Published"),
                    Ul(
                        *[sticker_to_li(s, app) for s in user_stickers if s.storefront_product_id],
                        id="published-list"
                    ),
                    id="sticker-list"
                ),
                Div(id="preview-area")
            )
        )

    @rt("/sticker-status/{sticker_id}")
    def get(sticker_id: int, app: FastHTML):
        """Endpoint to check individual sticker status"""
        with Session(app.state.db_client.engine) as session:
            sticker = session.get(Sticker, sticker_id)
            return sticker_to_li(sticker, app)

def sticker_to_li(sticker: Sticker, app: FastHTML):
    """Convert a Sticker model to a list item for display"""
    if sticker.status == StickerStatus.PROCESSING:
        return Li(
            f"{sticker.name} ",
            Span("(Processing...)", cls="processing-status"),
            id=f"sticker-{sticker.sticker_id}",
            hx_get=f"/sticker-status/{sticker.sticker_id}",
            hx_trigger="every 3s",
            hx_target=f"#sticker-{sticker.sticker_id}",
            hx_swap="outerHTML",
            cls="sticker-processing"
        )
    
    status = "published" if sticker.storefront_product_id else "draft"
    
    if sticker.status == StickerStatus.ERROR:
        status_text = Span("(Error during processing)", cls="error-status")
        return Li(
            f"{sticker.name} ", status_text,
            id=f"sticker-{sticker.sticker_id}",
            cls=f"sticker-{status}"
        )
    
    # Only show edit/preview for published stickers
    if status == "published":
        edit = AX('Edit', f'/sticker/{sticker.sticker_id}', 'sticker-editor')
        preview = AX('Preview', f'/preview/{sticker.sticker_id}', 'preview-area')
        storefront_link = A('View on Storefront', href=f"https://{app.state.config.sell_app_storefront_name}/product/{sticker.storefront_product_id}", cls="storefront-link")
        
        return Li(
            f"{sticker.name} ",
            Div(edit, ' | ', preview, ' | ', storefront_link),
            id=f"sticker-{sticker.sticker_id}",
            cls=f"sticker-{status}"
        )
    else:
        # For draft stickers that are ready, show they're ready to be published
        if sticker.status == StickerStatus.READY:
            return Li(
                f"{sticker.name} ",
                Span("(Ready to publish)", cls="ready-status"),
                id=f"sticker-{sticker.sticker_id}",
                cls=f"sticker-{status}"
            )
        # For other draft statuses, just show the name
        return Li(
            f"{sticker.name}",
            id=f"sticker-{sticker.sticker_id}", 
            cls=f"sticker-{status}"
        ) 