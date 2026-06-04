# pyrefly: ignore [missing-import]


from langgraph.graph import StateGraph,START,END
from backend.src.graph.nodes import index_video_node,audio_content_node
from backend.src.graph.state import VideoAuditState

def create_graph():
   
   builder = StateGraph(VideoAuditState)

   # add node
   builder.add_node("indexer",index_video_node)
   builder.add_node("auditor",audio_content_node)

   # add edges 
   builder.add_edge(START,"indexer")
   builder.add_edge("indexer", "auditor")
   builder.add_edge("auditor",END)

   graph = builder.compile() 
   return graph 


app = create_graph()