import re
from typing import TypedDict, List
from state import AgentState
from config import *
from search_attraction import get_attraction
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

llm = ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL,api_key=API_KEY, temperature=0)

def understand_query_node(state: AgentState) -> dict:
  """
  理解用户意图，改写为更好的关键词
  """
  user_message = state["messages"][-1].content
  understand_prompt = f"""分析用户的查询："{user_message}"
  请完成两个任务：
  1. 简洁总结用户想要了解什么
  2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

  格式：
  理解：[用户需求总结]
  搜索词：[最佳搜索关键词]"""

  response = llm.invoke([SystemMessage(content=understand_prompt)])
  response_text = response.content

  # 解析LLM的输出，提取搜索关键词
  search_query = user_message # 默认使用原始查询
  if "搜索词：" in response_text:
      search_query = response_text.split("搜索词：")[1].strip()
    
  return {
      "user_query": response_text,
      "search_query": search_query,
      "step": "understood",
      "messages": [AIMessage(content=f"我将为您搜索：{search_query}")]
  }

def tavily_search_node(state: AgentState) -> dict:
    search_query = state["search_query"]
    try:
      result = get_attraction(search_query)
      return {
            "search_results": result,
            "step": "searched",
            "messages": [AIMessage(content="✅ 搜索完成！正在整理答案...")]
        }
    except Exception as e:
       return {
            "search_results": f"搜索失败：{e}",
            "step": "search_failed",
            "messages": [AIMessage(content="❌ 搜索遇到问题...")]
        }

def generate_answer_node(state: AgentState) -> dict:
    """步骤3：基于搜索结果生成最终答案"""
    if state["step"] == "search_failed":
        # 如果搜索失败，执行回退策略，基于LLM自身知识回答
        fallback_prompt = f"搜索API暂时不可用，请基于您的知识回答用户的问题：\n用户问题：{state['user_query']}"
        response = llm.invoke([SystemMessage(content=fallback_prompt)])
    else:
        # 搜索成功，基于搜索结果生成答案
        answer_prompt = f"""基于以下搜索结果为用户提供完整、准确的答案：
用户问题：{state['user_query']}
搜索结果：\n{state['search_results']}
请综合搜索结果，提供准确、有用的回答..."""
        response = llm.invoke([SystemMessage(content=answer_prompt)])
    
    return {
        "final_answer": response.content,
        "step": "completed",
        "messages": [AIMessage(content=response.content)]
    }

def create_search_assistant():
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)
    
    # 设置线性流程
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)
    
    # 编译图
    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app

if __name__ == "__main__":
    app = create_search_assistant()
    inputs = {"messages": [HumanMessage(content="明天我要去北京，天气怎么样？有合适的景点吗")]}

    config = {"configurable": {"thread_id": "test_12345"}}

    for output in app.stream(inputs, config=config):
      for key, value in output.items():
          print(f"Finished Node: {key}")
          print(f"State Update: {value}")
          print("----")

    app.invoke({"messages": inputs})