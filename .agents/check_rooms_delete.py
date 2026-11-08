import json
import re
import sys

def check_delete():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        # 1. Check run_command tool
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            delete_patterns = [
                r"\b(rm|rmdir|unlink|del|erase|rd)\b",
                r"\bRemove-Item\b",
                r"\bri\b",
                r"\bgit\s+rm\b",
            ]
            has_delete_cmd = any(re.search(pat, cmd, re.IGNORECASE) for pat in delete_patterns)
            targets_rooms = bool(re.search(r"(\b|[\\/])rooms([\\/]|\b)", cmd, re.IGNORECASE))

            if has_delete_cmd and targets_rooms:
                print(json.dumps({
                    "decision": "ask",
                    "reason": f"Tool '{tool_name}' is attempting to delete files inside the 'rooms' directory. User confirmation required."
                }))
                return

        # 2. Check any tool call with arguments referencing deletion in 'rooms'
        for k, v in args.items():
            if isinstance(v, str):
                if re.search(r"(\b|[\\/])rooms([\\/]|\b)", v, re.IGNORECASE) and any(
                    word in v.lower() for word in ["delete", "remove", "unlink"]
                ):
                    print(json.dumps({
                        "decision": "ask",
                        "reason": f"Operation involving deletion inside 'rooms' detected in parameter '{k}'. User confirmation required."
                    }))
                    return

        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # On error, allow execution without blocking unexpectedly
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    check_delete()
