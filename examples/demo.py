from fasthtml.common import *

app,rt = fast_app()

@rt('/')
def get(): return Div(P('Hello World!'), hx_get="/change")

@rt('/photo')
def get(): return image()

@rt('/change')
def get(): return P('Nice to be here!')

@rt("/{fname:path}.{ext:static}")
async def get(fname:str, ext:str): 
    return FileResponse(f'public/{fname}.{ext}')

serve()


def image():
    return Div(
        Img(src="/Users/lee/projects/sticker-maker/input/leeving-room.jpg")
    )

###

# def accordion_demo():
#     """UI components can be styled and reused.
#     UI libraries can be installed using `pip`."""
#     accs = [accordion(id=id, question=q, answer=a,
#         question_cls="text-black s-body", answer_cls=a_cls, container_cls=c_cls)
#         for id,(q,a) in enumerate(qas)]
#     return Div(*accs, cls=acc_cls)


# ###
# class Todo:
#     "Use any database system you like"
#     id:int; title:str; done:bool
#     def __ft__(self):
#         "`__ft__` defines how FastHTML renders an object"
#         return Li("✅ " if self.done else "", self.title)
 
# todos = db.create(Todo)
# def todos_table():
#     "This example uses the `fastlite` DB lib"
#     return Ul(*todos(), cls=list_class)