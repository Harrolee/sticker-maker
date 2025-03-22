from fasthtml.common import *
icons = 'assets/icons'

def accordion(id, question, answer, question_cls="", answer_cls="", container_cls=""):
    base_container = "bg-[#2a2a2a] rounded-lg shadow-lg border-l-4 border-[#ff3c3c] mb-4 transition-all duration-300 hover:transform hover:translate-x-2"
    base_label = "flex items-center cursor-pointer py-4 lg:py-6 pl-6 lg:pl-8 pr-4 lg:pr-6 text-[#f4f4f4] hover:text-[#ffd700]"
    base_question = "flex-grow font-bold uppercase tracking-wider"
    base_answer = "overflow-hidden max-h-0 pl-6 lg:pl-8 pr-4 lg:pr-6 text-[#f4f4f4]/80 peer-checked/collapsible:max-h-[30rem] peer-checked/collapsible:pb-4 peer-checked/collapsible:lg:pb-6 transition-all duration-300 ease-in-out"
    
    return Div(
        Input(id=f"collapsible-{id}", type="checkbox", cls=f"collapsible-checkbox peer/collapsible hidden"),
        Label(
            P(question, cls=f"{base_question} {question_cls}"),
            Img(src=f"{icons}/plus-icon.svg", alt="Expand", cls=f"plus-icon w-6 h-6 filter invert"),
            Img(src=f"{icons}/minus-icon.svg", alt="Collapse", cls=f"minus-icon w-6 h-6 filter invert"),
            _for=f"collapsible-{id}",
            cls=f"{base_label}"),
        P(answer, cls=f"{base_answer} {answer_cls}"),
        cls=f"{base_container} {container_cls}")