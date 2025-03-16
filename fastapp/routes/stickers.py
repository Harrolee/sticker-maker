from fasthtml.common import *
from fastapp.services.db import DbClient
from fastapp.services.storefront import StickerPublisher, StorefrontProduct
from fastapp.db.models import Sticker, StickerStatus
from sqlalchemy.orm import Session
from sqlalchemy import select
from PIL import Image, ImageOps
from io import BytesIO
import uuid
import os
from fastcore.parallel import threaded
from fastapp.make_sticker.main import stickerize

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
    async def post(sticker_name: str, image_input: UploadFile, session, app: FastHTML):
        basename = str(uuid.uuid4())[:4]
        bytes = await image_input.read()
        img = Image.open(BytesIO(bytes))
        img.thumbnail((1024, 1024))
        img = ImageOps.exif_transpose(img)
        input_path = f"{app.state.config.workspace_dir}/input/{basename}.png"
        img.save(input_path)
        
        # Create sticker record immediately
        with Session(app.state.db_client.engine) as db_session:
            new_sticker = Sticker(
                name=sticker_name,
                creator=session['user_id'],
                status=StickerStatus.PROCESSING,
                image_path=f"{app.state.config.workspace_dir}/output/{basename}.png"
            )
            db_session.add(new_sticker)
            db_session.commit()
            sticker_id = new_sticker.sticker_id

        # Start processing in background
        process_image(basename, sticker_name, app.state.config, sticker_id, app.state.db_client)
        
        return JSONResponse(
            content={"message": "Sticker creation started"},
            status_code=200,
            headers={"HX-Redirect": "/dashboard"}
        )

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
    return Article(
        H2('Step 1: Upload an image'),
        Form(hx_post="stickerize", hx_target="#main_content", 
             hx_encoding="multipart/form-data", 
             hx_trigger="submit",
             hx_indicator="#loading-spinner")(
            Input(type='text', id='sticker_name', name='sticker_name', accept='text/*'),
            Input(type='file', id='image_input', name='image_input', accept='image/*'),
            Button("Stickerize Image", type="submit"), 
        ),
        Div(
            Div("Processing image...", cls="spinner-text"),
            cls="spinner-container",
            id="loading-spinner",
            style="display:none"
        ),
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
def process_image(basename: str, sticker_name: str, config, sticker_id: int, db_client: DbClient):
    """Process image in background thread"""
    try:
        print(f"Starting to process sticker {sticker_id} with basename {basename}")
        stickerize(f"{basename}.png", sticker_name, config)
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