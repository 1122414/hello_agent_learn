import operator
from typing import Annotated, Literal, TypedDict, Union

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver # 用于记忆（可选）

from config import *

# ==========================================
# 1. 定义工具 (跟之前一样)
# ==========================================
@tool
def add(a: int, b: int) -> int:
    """计算两个数字相加"""
    print(f"  [工具执行] add({a}, {b})")
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """计算两个数字相乘"""
    print(f"  [工具执行] multiply({a}, {b})")
    return a * b

tools = [add, multiply]

# ==========================================
# 2. 定义 State (状态)
# ==========================================
# 这是一个类型定义，告诉图：我们的状态就是一串消息列表
# add_messages 是一个 reducer，确保新消息是"追加"而不是"覆盖"
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# ==========================================
# 3. 初始化组件
# ==========================================

# A. 模型
llm = ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL,api_key=API_KEY, temperature=0)
llm_with_tools = llm.bind_tools(tools)

# B. 节点函数：调用模型
def call_model(state: AgentState):
    # 获取当前所有的消息
    messages = state["messages"]
    # 调用模型
    response = llm_with_tools.invoke(messages)
    # 返回的内容会自动被 add_messages 追加到 state 中
    return {"messages": [response]}

# C. 预构建组件：工具节点
# 这一行代码替代了上个 Demo 中那个巨大的 for 循环和 try-except
tool_node = ToolNode(tools)

# ==========================================
# 4. 构建图 (The Graph)
# ==========================================
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", call_model) # 思考节点
workflow.add_node("tools", tool_node)  # 行动节点 (ToolNode)

# 设置起始点
workflow.add_edge(START, "agent")

# 这里路由可以自定义
# def my_custom_router(state):
#     last_message = state["messages"][-1]
    
#     # 1. 如果想调工具，还是去工具节点
#     if last_message.tool_calls:
#         return "tools"
    
#     # 2. 【关键】如果没有调工具，但包含了代码块，转去审查节点！
#     elif "```python" in last_message.content:
#         return "reviewer_node"
        
#     # 3. 只有当审查通过，或者只是普通闲聊时，才真正结束
#     else:
#         return END

# # 在图中应用
# workflow.add_conditional_edges("agent", my_custom_router)

# 设置条件边 (核心逻辑)
# 从 agent 出来后，自动判断去哪里：
# - 如果 LLM 想调工具 -> 去 "tools" 节点
# - 如果 LLM 说完了 -> 去 END
workflow.add_conditional_edges(
    "agent",
    tools_condition, 
)

# 设置闭环边
# 工具执行完后，必须把结果扔回给 agent 让它继续思考
workflow.add_edge("tools", "agent")

# 编译图
app = workflow.compile()

# ==========================================
# 5. 执行
# ==========================================

def run_langgraph_demo():
    print("=== LangGraph Agent 启动 ===")
    
    query = "请计算 10 加 5 的结果，然后再乘以 3 是多少？"
    inputs = {"messages": [HumanMessage(content=query)]}
    
    # stream_mode="values" 会打印状态更新的过程
    for event in app.stream(inputs, stream_mode="values"):
        # 获取最新的一条消息
        current_message = event["messages"][-1]
        
        # 打印日志辅助理解
        if current_message.type == "human":
            print(f"\n[用户]: {current_message.content}")
        elif current_message.type == "ai":
            if current_message.tool_calls:
                print(f"[AI 思考]: 我需要调用工具 {current_message.tool_calls[0]['name']}")
            else:
                print(f"[AI 回复]: {current_message.content}")
        elif current_message.type == "tool":
            # ToolNode 自动生成了 ToolMessage
            print(f"[系统]: 工具执行完毕，结果已存入 State")

if __name__ == "__main__":
    run_langgraph_demo()