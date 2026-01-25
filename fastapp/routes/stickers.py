from fasthtml.common import *
from fastapp.services.db import DbClient
from fastapp.services.storefront import StickerPublisher, StorefrontProduct
from fastapp.db.models import Sticker, StickerStatus, User
from sqlalchemy.orm import Session
from sqlalchemy import select
from PIL import Image, ImageOps
from io import BytesIO
import uuid
import os
from typing import List
from fastcore.parallel import threaded
from starlette.requests import Request
from fastapp.make_sticker.main import stickerize, get_available_styles, DEFAULT_STYLE


def get_user_id_from_session(db_session, session_user_id) -> int | None:
    """Get user_id from session value (could be username string or user_id int)"""
    # If it's already an integer, it's the user_id directly (Auth0 login)
    if isinstance(session_user_id, int):
        return session_user_id

    # Try to convert to int (might be stored as string)
    try:
        return int(session_user_id)
    except (ValueError, TypeError):
        pass

    # Otherwise look up by username (legacy username/password login)
    user = db_session.query(User).filter(User.username == session_user_id).first()
    return user.user_id if user else None

def setup_sticker_routes(app: FastHTML, rt):
    @rt('/')
    def get(auth):
        if not auth: return RedirectResponse('/login', 303)
        
        return Titled("Create Sticker",
            Div(
                Grid(
                    A("View Your Stickers", href="/dashboard", cls="button")
                ),
                image_upload()
            )
        )

    @rt('/stickerize')
    async def post(sticker_name: str, image_input: UploadFile, session, app: FastHTML, style: str = None):
        basename = str(uuid.uuid4())[:4]
        bytes = await image_input.read()
        img = Image.open(BytesIO(bytes))
        img.thumbnail((1024, 1024))
        img = ImageOps.exif_transpose(img)
        input_path = f"{app.state.config.workspace_dir}/input/{basename}.png"
        img.save(input_path)

        # Use default style if not provided
        if not style:
            style = DEFAULT_STYLE

        # Create sticker record immediately
        with Session(app.state.db_client.engine) as db_session:
            user_id = get_user_id_from_session(db_session, session['user_id'])
            if not user_id:
                return JSONResponse({"error": "User not found"}, status_code=400)

            new_sticker = Sticker(
                name=sticker_name,
                creator=user_id,
                status=StickerStatus.PROCESSING,
                image_path=f"{app.state.config.workspace_dir}/output/{basename}.png"
            )
            db_session.add(new_sticker)
            db_session.commit()
            sticker_id = new_sticker.sticker_id

        # Start processing in background with selected style
        process_image(basename, sticker_name, app.state.config, sticker_id, app.state.db_client, style)

        return JSONResponse(
            content={"message": "Sticker creation started"},
            status_code=200,
            headers={"HX-Redirect": "/dashboard"}
        )

    @rt('/stickerize/batch')
    async def post(request: Request, app: FastHTML, session):
        """
        Batch endpoint for processing multiple images.

        curl -X POST http://localhost:5001/stickerize/batch \
            -F "images=@image1.png" \
            -F "images=@image2.png" \
            -F "publish=false" \
            -F "style=filter"
        """
        form = await request.form()
        images = form.getlist('images')
        publish = form.get('publish', 'false').lower() == 'true'
        style = form.get('style', DEFAULT_STYLE)

        if not images:
            return JSONResponse({"error": "No images provided"}, status_code=400)

        results = []
        for image_input in images:
            basename = str(uuid.uuid4())[:8]
            bytes_data = await image_input.read()
            img = Image.open(BytesIO(bytes_data))
            img.thumbnail((1024, 1024))
            img = ImageOps.exif_transpose(img)
            input_path = f"{app.state.config.workspace_dir}/input/{basename}.png"
            output_path = f"{app.state.config.workspace_dir}/output/{basename}.png"
            img.save(input_path)

            # Derive sticker name from filename or use basename
            original_filename = getattr(image_input, 'filename', basename)
            sticker_name = os.path.splitext(original_filename)[0] if original_filename else basename

            sticker_id = None
            if publish:
                with Session(app.state.db_client.engine) as db_session:
                    user_id = get_user_id_from_session(db_session, session['user_id'])
                    if not user_id:
                        continue  # Skip this image if user not found

                    new_sticker = Sticker(
                        name=sticker_name,
                        creator=user_id,
                        status=StickerStatus.PROCESSING,
                        image_path=output_path
                    )
                    db_session.add(new_sticker)
                    db_session.commit()
                    sticker_id = new_sticker.sticker_id

            # Start processing in background with selected style
            process_image_batch(
                basename, sticker_name, app.state.config,
                sticker_id, app.state.db_client if publish else None, publish, style
            )

            results.append({
                "basename": basename,
                "sticker_name": sticker_name,
                "output_path": output_path,
                "sticker_id": sticker_id,
                "publish": publish,
                "style": style
            })

        return JSONResponse({
            "message": f"Processing {len(results)} images",
            "results": results
        })

    @rt('/process-status/{basename}')
    def get_process_status(basename: str, session):
        """Endpoint to check processing status"""
        return processing_preview(basename, session['sticker_name'], session['sticker_url'])

    @rt('/preview/{sticker_id}')
    def get(sticker_id: int, app: FastHTML):
        """Preview a sticker"""
        with Session(app.state.db_client.engine) as session:
            sticker = session.get(Sticker, sticker_id)
            if not sticker:
                return Div("Sticker not found", id="preview-area")
            
            return Div(
                H2(f"Preview: {sticker.name}"),
                Figure(
                    Img(src=sticker.image_path, alt=f"Preview of {sticker.name}"),
                    Figcaption(f"Sticker ID: {sticker.sticker_id}")
                ),
                id="preview-area"
            )

def image_upload():
    # Build style options for the dropdown
    style_options = [
        Option(s['label'], value=s['value'], selected=(s['value'] == DEFAULT_STYLE))
        for s in get_available_styles()
    ]

    return Article(
        H2('Step 1: Upload an image'),
        Form(hx_post="stickerize", hx_target="#main_content",
             hx_encoding="multipart/form-data",
             hx_trigger="submit",
             hx_indicator="#loading-spinner")(
            Div(
                Label("Sticker Name:", fr="sticker_name"),
                Input(type='text', id='sticker_name', name='sticker_name', placeholder="Enter sticker name"),
                cls="form-group"
            ),
            Div(
                Label("Style:", fr="style"),
                Select(*style_options, id='style', name='style'),
                P("Choose 'Artistic Filter' options if you prefer non-AI processing", cls="hint-text"),
                cls="form-group"
            ),
            Div(
                Label("Image:", fr="image_input"),
                Input(type='file', id='image_input', name='image_input', accept='image/*'),
                cls="form-group"
            ),
            Button("Stickerize Image", type="submit"),
        ),
        Div(
            Div("Processing image...", cls="spinner-text"),
            cls="spinner-container",
            id="loading-spinner",
            style="display:none"
        ),
        Style("""
            .form-group {
                margin-bottom: 1rem;
            }
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: bold;
            }
            .form-group select, .form-group input[type='text'] {
                width: 100%;
                padding: 0.5rem;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            .hint-text {
                font-size: 0.85rem;
                color: #666;
                margin-top: 0.25rem;
            }
        """),
        id="main_content"
    )

def processing_preview(basename: str, sticker_name: str, sticker_url):
    """Shows a loading state while checking if processing is complete"""
    if os.path.exists(sticker_url):
        return Article(
            H2('Sticker Created!', id="narrator"),
            Figure(
                Img(src=sticker_url, alt="stickerized image"), 
                id="displayed-image"
            ), 
            id="main_content"
        )
    else:
        return Article(
            Div(
                f"Creating {sticker_name} sticker...",
                id="processing-status",
                hx_get=f"/process-status/{basename}",
                hx_trigger="every 3s",
                hx_target="#main_content"
            ),
            id="main_content"
        )

@threaded
def process_image(basename: str, sticker_name: str, config, sticker_id: int, db_client: DbClient, style: str = None):
    """Process image in background thread"""
    try:
        print(f"Starting to process sticker {sticker_id} with basename {basename} using style '{style}'")
        stickerize(f"{basename}.png", sticker_name, config, style=style)
        print(f"Stickerize completed for {sticker_id}")

        # Update status when complete and automatically publish to storefront
        with Session(db_client.engine) as session:
            sticker = session.get(Sticker, sticker_id)
            sticker.status = StickerStatus.READY

            # Automatically publish to storefront
            storefront_product = StorefrontProduct(
                title=sticker_name,
                description=f"Custom made {sticker_name} sticker",
                redirect_url="http://www.localhost:5001",
                image_url=sticker.image_path,
                price=400
            )
            publisher = StickerPublisher(config)
            product_id, _ = publisher.publish_sticker(storefront_product)

            # Update sticker with storefront info
            sticker.storefront_product_id = product_id
            session.commit()
            print(f"Updated sticker {sticker_id} status to READY and published to storefront")

    except Exception as e:
        print(f"Error processing sticker {sticker_id}: {str(e)}")
        print(f"Error type: {type(e)}")

        with Session(db_client.engine) as session:
            sticker = session.get(Sticker, sticker_id)
            sticker.status = StickerStatus.ERROR
            sticker.error_message = str(e)
            session.commit()


@threaded
def process_image_batch(basename: str, sticker_name: str, config, sticker_id: int | None, db_client: DbClient | None, publish: bool, style: str = None):
    """Process image in background thread with optional DB/storefront publish"""
    try:
        print(f"Starting batch processing for {basename} (publish={publish}, style={style})")
        stickerize(f"{basename}.png", sticker_name, config, style=style)
        print(f"Stickerize completed for {basename}")

        if publish and db_client and sticker_id:
            with Session(db_client.engine) as session:
                sticker = session.get(Sticker, sticker_id)
                sticker.status = StickerStatus.READY

                storefront_product = StorefrontProduct(
                    title=sticker_name,
                    description=f"Custom made {sticker_name} sticker",
                    redirect_url="http://www.localhost:5001",
                    image_url=sticker.image_path,
                    price=400
                )
                publisher = StickerPublisher(config)
                product_id, _ = publisher.publish_sticker(storefront_product)

                sticker.storefront_product_id = product_id
                session.commit()
                print(f"Published sticker {sticker_id} to storefront")

    except Exception as e:
        print(f"Error processing {basename}: {str(e)}")
        if publish and db_client and sticker_id:
            with Session(db_client.engine) as session:
                sticker = session.get(Sticker, sticker_id)
                sticker.status = StickerStatus.ERROR
                sticker.error_message = str(e)
                session.commit() 