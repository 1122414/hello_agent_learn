from reflection.ReflectionAgent import *
from reflection.memory import *
from HelloAgentsLLM import HelloAgentsLLM

if __name__ == "__main__":
    llm_client = HelloAgentsLLM()
    reflection_agent = ReflectionAgent(llm_client)
    reflection_agent.run("任务： 编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。")