from dotenv import load_dotenv
import json
import os
import datetime
from langchain_community.tools import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, chain


load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")


tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
    # include_domains=[...],
    # exclude_domains=[...],
    # name="...",            # overwrite default tool name
    # description="...",     # overwrite default tool description
    # args_schema=...,       # overwrite default args_schema: BaseModel
)


# tool.invoke({"query": "What happened at the last wimbledon"})
# This is usually generated by a model, but we'll create a tool call directly
# for demo purposes.
model_generated_tool_call = {
    "args": {"query": "euro 2024 host nation"},
    "id": "1",
    "name": "tavily",
    "type": "tool_call",
}
tool_msg = tool.invoke(model_generated_tool_call)

# The content is a JSON string of results
print(tool_msg.content[:400])


# Abbreviate the results for demo purposes
print(
    json.dumps(
        {k: str(v)[:200] for k, v in tool_msg.artifact.items()},
        indent=2
    )
)


llm = ChatOpenAI(
    model_name='deepseek-chat',
    openai_api_key=deepseek_api_key,
    openai_api_base='https://api.deepseek.com/v1/',
    max_tokens=1024,
    temperature=0.7
)


today = datetime.datetime.today().strftime("%D")
prompt = ChatPromptTemplate(
    [
        ("system", f"You are a helpful assistant. The date today is {today}."),
        ("human", "{user_input}"),
        ("placeholder", "{messages}"),
    ]
)

# specifying tool_choice will force the model to call this tool.
llm_with_tools = llm.bind_tools([tool])

llm_chain = prompt | llm_with_tools


@chain
def tool_chain(user_input: str, config: RunnableConfig):
    input_ = {"user_input": user_input}
    ai_msg = llm_chain.invoke(input_, config=config)
    tool_msgs = tool.batch(ai_msg.tool_calls, config=config)
    return llm_chain.invoke(
        {**input_, "messages": [ai_msg, *tool_msgs]},
        config=config
    )


tool_chain.invoke("who won the last womens singles wimbledon")
