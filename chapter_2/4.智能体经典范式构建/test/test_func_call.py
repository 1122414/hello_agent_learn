import json
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from config import *

# ==========================================
# 1. 定义工具 (Tools)
# ==========================================

@tool
def add(a: int, b: int) -> int:
    """计算两个数字相加"""
    print(f"\n[系统日志] 正在调用工具 add: {a} + {b}")
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """计算两个数字相乘"""
    print(f"\n[系统日志] 正在调用工具 multiply: {a} * {b}")
    return a * b

# 创建一个字典，方便后续根据函数名字符串找到对应的函数对象
tools = [add, multiply]
tool_map = {t.name: t for t in tools}

# ==========================================
# 2. 初始化模型并绑定工具
# ==========================================

llm = ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL,api_key=API_KEY, temperature=0)
llm_with_tools = llm.bind_tools(tools)

# ==========================================
# 3. 模拟 Agent 执行循环 (The Loop)
# ==========================================

def run_agent_demo(query):
    print(f"=== 用户提问: {query} ===")
    
    # 步骤 A: 初始化对话历史
    messages = [HumanMessage(content=query)]
    
    # 步骤 B: 第一次调用 LLM (看看它想不想用工具)
    # 此时 LLM 可能会返回一个带有 tool_calls 的 AIMessage
    ai_msg = llm_with_tools.invoke(messages)
    
    # 将 AI 的回复 (包含它的思考或工具调用请求) 加入历史
    messages.append(ai_msg)

    # 步骤 C: 检查是否触发了工具调用
    if ai_msg.tool_calls:
        print(f"[AI 决定] 需要调用 {len(ai_msg.tool_calls)} 个工具...")
        
        # --- 核心循环开始 ---
        for tool_call in ai_msg.tool_calls:
            # 1. 解析工具调用的元数据
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"] # 重要！这是上下文匹配的ID
            
            # 2. 找到对应的 Python 函数
            selected_tool = tool_map[tool_name]
            
            # 3. 执行函数 (Execute)
            try:
                # invoke 会自动处理参数解包
                tool_output = selected_tool.invoke(tool_args)
            except Exception as e:
                tool_output = f"Error: {str(e)}"
            
            print(f"[工具输出] 结果是: {tool_output}")
            
            # 4. 构建 ToolMessage (Feed Back)
            # 必须包含 tool_call_id，这样 LLM 才知道这个结果对应哪次请求
            tool_msg = ToolMessage(
                content=str(tool_output),
                tool_call_id=tool_call_id
            )
            
            # 5. 将工具结果加入对话历史
            messages.append(tool_msg)
        # --- 核心循环结束 ---

        # 步骤 D: 第二次调用 LLM (让它根据工具结果生成最终回复)
        print("\n[系统日志] 将工具结果回传给 LLM，正在生成最终答案...")
        final_response = llm_with_tools.invoke(messages)
        
        print(f"=== 最终回答: {final_response.content} ===")
    else:
        # 如果不需要工具，直接打印回复
        print(f"=== 最终回答: {ai_msg.content} ===")

# ==========================================
# 4. 运行测试
# ==========================================

if __name__ == "__main__":
    # 测试一个需要两步计算的问题：(10 + 5) * 3
    # LLM 通常会先算加法，再算乘法，或者一次性发出两个调用（取决于模型智力）
    run_agent_demo("请计算 10 加 5 的结果，然后再乘以 3 是多少？")