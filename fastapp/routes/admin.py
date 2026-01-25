from fasthtml.common import *
from fastapp.db.models import Sticker, StickerStatus, User
from fastapp.services.storefront import StickerPublisher, StorefrontProduct
from sqlalchemy.orm import Session
from sqlalchemy import select
from PIL import Image, ImageOps
from io import BytesIO
from starlette.requests import Request
from starlette.responses import FileResponse
import uuid
import os
import glob
from fastcore.parallel import threaded
from fastapp.make_sticker.main import stickerize, get_available_styles, DEFAULT_STYLE

# Simple admin check - in production, use proper role-based auth
ADMIN_USERS = os.environ.get('ADMIN_USERS', 'admin').split(',')

def is_admin(auth):
    """Check if user is an admin"""
    return auth in ADMIN_USERS

def setup_admin_routes(app: FastHTML, rt):
    @rt('/admin')
    def get(auth, app: FastHTML):
        if not auth:
            return RedirectResponse('/login', 303)
        if not is_admin(auth):
            return Titled("Access Denied", P("You don't have admin access."))

        return Titled(
            "Admin: Batch Sticker Creator",
            Div(
                A("← Back to Dashboard", href="/dashboard", cls="button"),
                cls="mb-4"
            ),
            batch_upload_form(),
            Div(id="batch-results"),
            admin_styles()
        )

    @rt('/admin/batch-upload')
    async def post(request: Request, app: FastHTML, session):
        auth = session.get('user_id')
        if not auth or not is_admin(auth):
            return JSONResponse({"error": "Unauthorized"}, status_code=403)

        form = await request.form()
        images = form.getlist('images')
        style = form.get('style', DEFAULT_STYLE)

        if not images:
            return Div(
                P("No images uploaded", cls="error-message"),
                id="batch-results"
            )

        # Create a batch ID to track this upload
        batch_id = str(uuid.uuid4())[:8]
        batch_dir = f"{app.state.config.workspace_dir}/batches/{batch_id}"
        os.makedirs(f"{batch_dir}/input", exist_ok=True)
        os.makedirs(f"{batch_dir}/output", exist_ok=True)

        items = []
        for image_input in images:
            item_id = str(uuid.uuid4())[:8]
            bytes_data = await image_input.read()
            img = Image.open(BytesIO(bytes_data))
            img.thumbnail((1024, 1024))
            img = ImageOps.exif_transpose(img)

            input_path = f"{batch_dir}/input/{item_id}.png"
            output_path = f"{batch_dir}/output/{item_id}.png"
            img.save(input_path)

            # Get original filename for sticker name
            original_filename = getattr(image_input, 'filename', item_id)
            sticker_name = os.path.splitext(original_filename)[0] if original_filename else item_id

            # Start background processing with selected style
            process_batch_item(batch_id, item_id, sticker_name, app.state.config, style)

            items.append({
                "item_id": item_id,
                "sticker_name": sticker_name,
                "status": "processing"
            })

        # Return the batch review UI
        return batch_status_ui(batch_id, items, app.state.config.workspace_dir)

    @rt('/admin/batch-status/{batch_id}')
    def get(batch_id: str, app: FastHTML, session):
        auth = session.get('user_id')
        if not auth or not is_admin(auth):
            return Div("Unauthorized", id="batch-results")

        batch_dir = f"{app.state.config.workspace_dir}/batches/{batch_id}"

        if not os.path.exists(batch_dir):
            return Div("Batch not found", id="batch-results")

        # Check what's in the input/output dirs
        input_files = glob.glob(f"{batch_dir}/input/*.png")
        items = []

        for input_path in input_files:
            item_id = os.path.splitext(os.path.basename(input_path))[0]
            output_path = f"{batch_dir}/output/{item_id}.png"

            status = "ready" if os.path.exists(output_path) else "processing"
            sticker_name = item_id  # Could store this in a metadata file

            items.append({
                "item_id": item_id,
                "sticker_name": sticker_name,
                "status": status
            })

        return batch_status_ui(batch_id, items, app.state.config.workspace_dir)

    @rt('/admin/batch-image/{batch_id}/{item_id}')
    def get(batch_id: str, item_id: str, app: FastHTML, session):
        """Serve processed batch images"""
        auth = session.get('user_id')
        if not auth or not is_admin(auth):
            return JSONResponse({"error": "Unauthorized"}, status_code=403)

        output_path = f"{app.state.config.workspace_dir}/batches/{batch_id}/output/{item_id}.png"
        if os.path.exists(output_path):
            return FileResponse(output_path, media_type="image/png")

        # Return input image if output not ready
        input_path = f"{app.state.config.workspace_dir}/batches/{batch_id}/input/{item_id}.png"
        if os.path.exists(input_path):
            return FileResponse(input_path, media_type="image/png")

        return JSONResponse({"error": "Image not found"}, status_code=404)

    @rt('/admin/publish-batch')
    async def post(request: Request, app: FastHTML, session):
        """Publish selected images from a batch"""
        auth = session.get('user_id')
        if not auth or not is_admin(auth):
            return JSONResponse({"error": "Unauthorized"}, status_code=403)

        form = await request.form()
        batch_id = form.get('batch_id')
        selected = form.getlist('selected')

        if not selected:
            return Div(
                P("No images selected for publishing", cls="error-message"),
                A("← Back to Admin", href="/admin", cls="button"),
                id="batch-results"
            )

        published = []
        for item_id in selected:
            output_path = f"{app.state.config.workspace_dir}/batches/{batch_id}/output/{item_id}.png"
            if not os.path.exists(output_path):
                continue

            # Get sticker name from form or use item_id
            sticker_name = form.get(f'name_{item_id}', item_id)

            # Create sticker record
            with Session(app.state.db_client.engine) as db_session:
                # Handle both numeric user_id (Auth0) and username (legacy)
                user = None
                try:
                    user_id = int(auth)
                    user = db_session.query(User).filter(User.user_id == user_id).first()
                except (ValueError, TypeError):
                    user = db_session.query(User).filter(User.username == auth).first()
                if not user:
                    continue

                # Copy to main output directory
                final_path = f"{app.state.config.workspace_dir}/output/{item_id}.png"
                import shutil
                shutil.copy(output_path, final_path)

                new_sticker = Sticker(
                    name=sticker_name,
                    creator=user.user_id,
                    status=StickerStatus.READY,
                    image_path=final_path
                )
                db_session.add(new_sticker)
                db_session.commit()
                sticker_id = new_sticker.sticker_id

                # Publish to storefront
                storefront_product = StorefrontProduct(
                    title=sticker_name,
                    description=f"Custom made {sticker_name} sticker",
                    redirect_url="http://www.localhost:5001",
                    image_url=final_path,
                    price=400
                )
                publisher = StickerPublisher(app.state.config)
                product_id, _ = publisher.publish_sticker(storefront_product)

                new_sticker.storefront_product_id = product_id
                db_session.commit()

                published.append(sticker_name)

        return Div(
            H3("Published Successfully!"),
            Ul(*[Li(name) for name in published]),
            Div(
                A("View Dashboard", href="/dashboard", cls="button"),
                A("Create More", href="/admin", cls="button", style="margin-left: 10px;"),
            ),
            id="batch-results"
        )

    @rt('/admin/delete-batch/{batch_id}')
    def delete(batch_id: str, app: FastHTML, session):
        """Delete an entire batch"""
        auth = session.get('user_id')
        if not auth or not is_admin(auth):
            return JSONResponse({"error": "Unauthorized"}, status_code=403)

        batch_dir = f"{app.state.config.workspace_dir}/batches/{batch_id}"
        if os.path.exists(batch_dir):
            import shutil
            shutil.rmtree(batch_dir)

        return Div(
            P("Batch deleted"),
            A("← Back to Admin", href="/admin", cls="button"),
            id="batch-results"
        )


def batch_upload_form():
    """Multi-file upload form with style selection"""
    # Build style options for the dropdown
    style_options = [
        Option(s['label'], value=s['value'], selected=(s['value'] == DEFAULT_STYLE))
        for s in get_available_styles()
    ]

    return Article(
        H2('Upload Images for Batch Processing'),
        Form(
            hx_post="/admin/batch-upload",
            hx_target="#batch-results",
            hx_encoding="multipart/form-data",
            hx_indicator="#upload-spinner"
        )(
            Div(
                Label("Processing Style:", fr="style"),
                Select(*style_options, id='style', name='style'),
                P("Choose 'Artistic Filter' options for non-AI processing", cls="hint-text"),
                cls="form-group"
            ),
            Div(
                Label("Select multiple images:", fr="images"),
                Input(
                    type='file',
                    id='images',
                    name='images',
                    accept='image/*',
                    multiple=True
                ),
                cls="form-group"
            ),
            Button("Process All Images", type="submit", cls="button"),
        ),
        Div(
            Div("Uploading and processing...", cls="spinner-text"),
            cls="spinner-container",
            id="upload-spinner",
            style="display:none"
        ),
        Style("""
            .hint-text {
                font-size: 0.85rem;
                color: #888;
                margin-top: 0.25rem;
            }
            .form-group select {
                width: 100%;
                padding: 0.5rem;
                border: 1px solid #444;
                border-radius: 4px;
                background: var(--bg-color);
                color: var(--text-color);
            }
        """),
        id="upload-form"
    )


def batch_status_ui(batch_id: str, items: list, workspace_dir: str):
    """UI to show batch processing status and allow review"""
    all_ready = all(item['status'] == 'ready' for item in items)
    any_processing = any(item['status'] == 'processing' for item in items)

    # Build grid of images
    image_cards = []
    for item in items:
        item_id = item['item_id']
        sticker_name = item['sticker_name']
        status = item['status']

        if status == 'ready':
            card = Div(
                Div(
                    Input(
                        type="checkbox",
                        name="selected",
                        value=item_id,
                        checked=True,
                        id=f"check_{item_id}"
                    ),
                    Label(fr=f"check_{item_id}", cls="checkbox-label"),
                    cls="card-checkbox"
                ),
                Img(
                    src=f"/admin/batch-image/{batch_id}/{item_id}",
                    alt=sticker_name,
                    cls="batch-image"
                ),
                Input(
                    type="text",
                    name=f"name_{item_id}",
                    value=sticker_name,
                    placeholder="Sticker name",
                    cls="name-input"
                ),
                cls="batch-card ready"
            )
        else:
            card = Div(
                Div(cls="processing-overlay"),
                Img(
                    src=f"/admin/batch-image/{batch_id}/{item_id}",
                    alt=sticker_name,
                    cls="batch-image processing"
                ),
                P(f"{sticker_name} - Processing...", cls="processing-text"),
                cls="batch-card processing"
            )

        image_cards.append(card)

    # Polling for updates if still processing
    polling_attrs = {}
    if any_processing:
        polling_attrs = {
            'hx_get': f'/admin/batch-status/{batch_id}',
            'hx_trigger': 'every 3s',
            'hx_target': '#batch-results',
            'hx_swap': 'outerHTML'
        }

    return Div(
        H3(f"Batch: {batch_id}"),
        P(f"{len(items)} images - {'Processing...' if any_processing else 'Ready for review'}"),
        Form(
            hx_post="/admin/publish-batch",
            hx_target="#batch-results"
        )(
            Hidden(name="batch_id", value=batch_id),
            Div(*image_cards, cls="batch-grid"),
            Div(
                Button(
                    "Publish Selected",
                    type="submit",
                    cls="button",
                    disabled=any_processing
                ),
                Button(
                    "Delete Batch",
                    hx_delete=f"/admin/delete-batch/{batch_id}",
                    hx_target="#batch-results",
                    hx_confirm="Are you sure you want to delete this batch?",
                    cls="button delete-btn"
                ),
                cls="batch-actions"
            ) if all_ready else Div(
                P("Waiting for processing to complete..."),
                cls="batch-actions"
            )
        ),
        id="batch-results",
        **polling_attrs
    )


def admin_styles():
    """Admin-specific styles"""
    return Style("""
        .batch-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .batch-card {
            background: var(--secondary-bg);
            border-radius: 8px;
            padding: 10px;
            position: relative;
        }

        .batch-card.ready {
            border: 2px solid var(--accent);
        }

        .batch-card.processing {
            border: 2px solid var(--primary);
            opacity: 0.7;
        }

        .batch-image {
            width: 100%;
            height: 150px;
            object-fit: contain;
            background: #111;
            border-radius: 4px;
        }

        .batch-image.processing {
            filter: grayscale(50%);
        }

        .processing-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            z-index: 1;
        }

        .card-checkbox {
            position: absolute;
            top: 15px;
            right: 15px;
            z-index: 2;
        }

        .card-checkbox input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .name-input {
            width: 100%;
            margin-top: 10px;
            padding: 8px;
            border: 1px solid #444;
            border-radius: 4px;
            background: var(--bg-color);
            color: var(--text-color);
        }

        .processing-text {
            text-align: center;
            color: var(--primary);
            font-style: italic;
            margin-top: 10px;
        }

        .batch-actions {
            margin-top: 20px;
            display: flex;
            gap: 10px;
        }

        .delete-btn {
            background: #666;
        }

        .delete-btn:hover {
            background: var(--primary);
        }

        .mb-4 {
            margin-bottom: 1rem;
        }

        .error-message {
            color: var(--primary);
            padding: 10px;
            background: rgba(255, 60, 60, 0.1);
            border-radius: 4px;
            margin-bottom: 10px;
        }
    """)


@threaded
def process_batch_item(batch_id: str, item_id: str, sticker_name: str, config, style: str = None):
    """Process a single batch item in background with selected style"""
    try:
        batch_dir = f"{config.workspace_dir}/batches/{batch_id}"
        input_path = f"{batch_dir}/input/{item_id}.png"
        output_path = f"{batch_dir}/output/{item_id}.png"

        # Run stickerize with batch-specific paths
        # We need to temporarily override paths or use absolute paths
        from PIL import Image
        from fastapp.make_sticker.rm_background import remove_background
        from fastapp.make_sticker.cartoonize_image import cartoonize
        from fastapp.make_sticker.filters import FILTER_STYLES, apply_artistic_filter
        from fastapp.make_sticker.lift import lift
        from fastapp.make_sticker.border import create_solid_border, EdgeRoughness
        from fastapp.make_sticker.tab import create_organic_tab

        # Default style if not provided
        if style is None:
            style = DEFAULT_STYLE

        print(f"Processing batch item {batch_id}/{item_id} with style '{style}'")

        # Run the pipeline manually with absolute paths
        # Create intermediate paths
        cartoonize_input = f"{batch_dir}/intermediate/{item_id}_cartoonize.png"
        rm_bg_input = f"{batch_dir}/intermediate/{item_id}_rm_bg.png"
        lift_input = f"{batch_dir}/intermediate/{item_id}_lift.png"
        border_input = f"{batch_dir}/intermediate/{item_id}_border.png"
        tab_input = f"{batch_dir}/intermediate/{item_id}_tab.png"

        import os
        os.makedirs(f"{batch_dir}/intermediate", exist_ok=True)

        # Remove background
        path = remove_background(input_path, cartoonize_input, config)

        # Apply stylization (AI cartoonize or non-AI filter)
        if style == 'cartoonize':
            # Use AI-based cartoonizer (Replicate model)
            path = cartoonize(path, rm_bg_input, config)
        else:
            # Use non-AI filter
            filter_func = FILTER_STYLES.get(style, apply_artistic_filter)
            path = filter_func(path, rm_bg_input, config)

        # Remove background again (after stylization)
        path = remove_background(path, lift_input, config)

        # Lift/enlarge
        path = lift(path, border_input)

        # Add borders (black outline then light blue)
        path = create_solid_border(path, tab_input, roughness=EdgeRoughness.MID, width=2, color=(0, 0, 0))
        path = create_solid_border(path, tab_input, roughness=EdgeRoughness.MID, width=5, color=(173, 216, 230))

        # Add tab with name
        result_path = create_organic_tab(path, output_path, tab_text=sticker_name)

        # Handle case where tab creation fails (no edge points)
        if result_path is None:
            # Fall back to saving without tab
            import shutil
            shutil.copy(path, output_path)
            print(f"Warning: Could not create tab for {item_id}, saving without tab")
        print(f"Completed batch item {batch_id}/{item_id}")

    except Exception as e:
        print(f"Error processing batch item {batch_id}/{item_id}: {str(e)}")
        import traceback
        traceback.print_exc()
