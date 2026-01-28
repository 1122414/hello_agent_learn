from ReActAgent import ReActAgent
from HelloAgentsLLM import HelloAgentsLLM
from tools.ToolExecutor import ToolExecutor
from tools.Search import search

if __name__ == "__main__":
  llm = HelloAgentsLLM()
  toolExecutor = ToolExecutor()
  search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
  toolExecutor.registerTool("Search", search_description, search)

  agent = ReActAgent(llm, toolExecutor)
  agent.run("华为最新手机型号及主要卖点")