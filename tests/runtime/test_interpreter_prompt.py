from __future__ import annotations
import sys, tempfile, unittest
from hive_runtime.interpreter import InterpreterAdapter
from hive_runtime.errors import RpcProtocolError


def python_server(source: str): return (sys.executable, "-u", "-c", source)


class InterpreterPromptTests(unittest.TestCase):
    def test_prompt_uses_acp_content_block_and_validates_stop_reason(self):
        server = r'''
import json, sys
for line in sys.stdin:
 m=json.loads(line); method=m.get("method")
 if method=="initialize": print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"protocolVersion":1,"agentInfo":{"name":"fake"},"agentCapabilities":{}}}),flush=True)
 elif method=="session/new": print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"sessionId":"s1"}}),flush=True)
 elif method=="session/prompt":
  assert m["params"]["sessionId"]=="s1" and m["params"]["prompt"]==[{"type":"text","text":"build it"}]
  print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"stopReason":"end_turn"}}),flush=True)
 elif method=="session/close": print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{}}),flush=True)
'''
        adapter=InterpreterAdapter(python_server(server),timeout=1)
        try:
            adapter.start()
            with tempfile.TemporaryDirectory() as tmp: session=adapter.create_session(tmp)
            self.assertEqual(adapter.prompt(session,"build it").stop_reason,"end_turn")
            adapter.close_session(session)
        finally: adapter.close()

    def test_empty_prompt_rejected_before_rpc(self):
        adapter=InterpreterAdapter(("unused",))
        adapter._sessions.add("s")
        with self.assertRaises(ValueError): adapter.prompt("s","  ")

    def test_malformed_prompt_result_fails_closed(self):
        server=r'''
import json,sys
for line in sys.stdin:
 m=json.loads(line); method=m.get("method")
 if method=="initialize": print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"protocolVersion":1,"agentInfo":{"name":"fake"},"agentCapabilities":{}}}),flush=True)
 elif method=="session/new": print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{"sessionId":"s"}}),flush=True)
 elif method=="session/prompt": print(json.dumps({"jsonrpc":"2.0","id":m["id"],"result":{}}),flush=True)
'''
        adapter=InterpreterAdapter(python_server(server),timeout=1)
        try:
            adapter.start()
            with tempfile.TemporaryDirectory() as tmp: s=adapter.create_session(tmp)
            with self.assertRaises(RpcProtocolError): adapter.prompt(s,"x")
        finally: adapter.close()

if __name__=="__main__": unittest.main()
