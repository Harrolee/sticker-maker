from fasthtml.common import *
icons = 'assets/icons'

def accordion(id, question, answer, question_cls="", answer_cls="", container_cls=""):
    return Div(
        Input(id=f"collapsible-{id}", type="checkbox", cls=f"collapsible-checkbox peer/collapsible hidden"),
        Label(
            P(question, cls=f"flex-grow {question_cls}"),
            Img(src=f"{icons}/plus-icon.svg", alt="Expand", cls=f"plus-icon w-6 h-6"),
            Img(src=f"{icons}/minus-icon.svg", alt="Collapse", cls=f"minus-icon w-6 h-6"),
            _for=f"collapsible-{id}",
            cls="flex items-center cursor-pointer py-4 lg:py-6 pl-6 lg:pl-8 pr-4 lg:pr-6"),
        P(answer, cls=f"overflow-hidden max-h-0 pl-6 lg:pl-8 pr-4 lg:pr-6 peer-checked/collapsible:max-h-[30rem] peer-checked/collapsible:pb-4 peer-checked/collapsible:lg:pb-6 transition-all duration-300 ease-in-out {answer_cls}"),
        cls=container_cls)