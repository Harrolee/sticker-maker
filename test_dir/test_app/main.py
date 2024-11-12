from fasthtml.common import *

app,rt = fast_app()

@rt('/dot-relative-import')
def get():
    from .module_one.rugged import log_hi
    return log_hi()


@rt('/relative-import')
def get():
    from module_one.rugged import log_hi
    return log_hi()


@rt('/absolute-import')
def get():
    from test_app.module_one.rugged import log_hi
    return log_hi()

serve()