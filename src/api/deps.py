from fastapi import Request


def get_llm(request: Request):
    return request.state.llm

def get_db(request: Request):
    return request.state.db