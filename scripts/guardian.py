#!/usr/bin/env python3
"""
Guardian - OpenClaw Watchdog Script
独立于主进程的守护脚本，用于检测主代理是否"当机"并自动熔断。

使用方法:
  1. chmod +x guardian.py
  2. 添加到 crontab: * * * * * /usr/bin/python3 /path/to/guardian.py

检测逻辑:
  - 读取会话日志，比较最后用户消息时间与最后AI回复时间
  - 如果用户消息后超过 TIMEOUT_MINUTES 分钟仍无AI回复，判定为当机
  - 检测配额是否耗尽（通过解析 openclaw status）
  - 检测复读现象（Jaccard 相似度检测最近 3 条回复）

熔断动作:
  1. 尝试 gateway restart
  2. 如果仍失败，切换到下一个模型
  3. 发送 WhatsApp 报警
"""

import os
import json
import time
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path

# ==================== 配置 ====================
OPENCLAW_HOME = Path.home() / ".openclaw"
WORKSPACE = OPENCLAW_HOME / "workspace"
SESSION_DIR = OPENCLAW_HOME / "agents" / "main" / "sessions"
STATE_FILE = WORKSPACE / "memory" / "guardian-state.json"
LOG_FILE = WORKSPACE / "memory" / "guardian.log"

TIMEOUT_MINUTES = 3  # 超过3分钟无响应判定为当机
COOLDOWN_MINUTES = 5  # 熔断后冷却时间，防止频繁切换
SIMILARITY_THRESHOLD = 0.85  # Jaccard 相似度阈值（超过此值判定为复读）
RECENT_MESSAGES_COUNT = 3  # 检测最近N条消息

# WhatsApp 报警配置（留空则不发送）
WHATSAPP_ADMIN = os.getenv("GUARDIAN_ADMIN_PHONE", "")  # 管理员手机号

# 模型优先级列表 (按顺序尝试)
MODEL_FALLBACK_ORDER = [
    "google-antigravity/claude-opus-4-5-thinking",
    "google-antigravity/gemini-3-pro-high",
    "google-antigravity/gemini-3-flash",
    "minimax-portal/MiniMax-M2.1",
    "glm/glm-4.7",
]

# ==================== 工具函数 ====================

def log(message: str, level: str = "INFO"):
    """写入日志（带级别）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    print(log_entry.strip())
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[Guardian] Failed to write log: {e}")


def load_state() -> dict:
    """加载守护者状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "last_action_time": 0,
        "current_model_index": 0,
        "restart_count": 0,
        "switch_count": 0,
        "quota_warnings": 0,
        "repeat_detections": 0,
    }


def save_state(state: dict):
    """保存守护者状态"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"Failed to save state: {e}", "ERROR")


def get_latest_session_file() -> Path | None:
    """获取最新的会话文件"""
    if not SESSION_DIR.exists():
        return None
    
    sessions = list(SESSION_DIR.glob("*.jsonl"))
    if not sessions:
        return None
    
    # 按修改时间排序，取最新的
    sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return sessions[0]


def parse_session_log(session_file: Path) -> tuple[datetime | None, datetime | None, list[str]]:
    """
    解析会话日志，返回 (最后用户消息时间, 最后AI回复时间, 最近N条AI回复内容)
    """
    last_user_time = None
    last_ai_time = None
    recent_ai_messages = []
    
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    role = entry.get("role", "")
                    timestamp = entry.get("timestamp") or entry.get("ts")
                    
                    if not timestamp:
                        continue
                    
                    # 解析时间戳
                    if isinstance(timestamp, (int, float)):
                        dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e12 else timestamp)
                    else:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    
                    if role == "user":
                        last_user_time = dt
                    elif role == "assistant":
                        last_ai_time = dt
                        # 提取消息内容
                        content = entry.get("content", "")
                        if isinstance(content, list):
                            # 处理多部分内容
                            text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                            content = " ".join(text_parts)
                        if content:
                            recent_ai_messages.append(content)
                        
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue
                    
    except Exception as e:
        log(f"Failed to parse session log: {e}", "ERROR")
    
    # 只保留最近的 N 条消息
    recent_ai_messages = recent_ai_messages[-RECENT_MESSAGES_COUNT:]
    
    return last_user_time, last_ai_time, recent_ai_messages


def jaccard_similarity(text1: str, text2: str) -> float:
    """计算两段文本的 Jaccard 相似度"""
    # 简单分词（按空格和标点）
    def tokenize(text):
        return set(re.findall(r'\w+', text.lower()))
    
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union) if union else 0.0


def detect_repetition(messages: list[str]) -> bool:
    """检测是否存在复读现象"""
    if len(messages) < 2:
        return False
    
    # 检测相邻消息的相似度
    for i in range(len(messages) - 1):
        similarity = jaccard_similarity(messages[i], messages[i + 1])
        if similarity > SIMILARITY_THRESHOLD:
            log(f"Repetition detected: similarity={similarity:.2f} between messages {i} and {i+1}", "WARN")
            return True
    
    return False


def is_agent_frozen() -> bool:
    """
    检测主代理是否当机
    条件: 用户发消息后超过 TIMEOUT_MINUTES 分钟仍无AI回复
    """
    session_file = get_latest_session_file()
    if not session_file:
        log("No session file found, assuming agent is OK")
        return False
    
    last_user_time, last_ai_time, _ = parse_session_log(session_file)
    
    if not last_user_time:
        log("No user message found, assuming agent is OK")
        return False
    
    now = datetime.now()
    
    # 如果没有AI回复，或者AI回复在用户消息之前
    if not last_ai_time or last_ai_time < last_user_time:
        time_since_user = (now - last_user_time).total_seconds() / 60
        if time_since_user > TIMEOUT_MINUTES:
            log(f"FROZEN DETECTED: User message at {last_user_time}, no AI reply for {time_since_user:.1f} minutes", "ERROR")
            return True
    
    return False


def check_repetition() -> bool:
    """检测复读现象"""
    session_file = get_latest_session_file()
    if not session_file:
        return False
    
    _, _, recent_messages = parse_session_log(session_file)
    return detect_repetition(recent_messages)


def check_quota() -> tuple[bool, str]:
    """
    检测配额是否耗尽
    返回: (配额是否正常, 状态消息)
    """
    try:
        result = subprocess.run(
            ["openclaw", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout + result.stderr
        
        # 解析配额信息（根据实际输出格式调整）
        # 示例匹配: "Quota: 1000/10000" 或 "quota exhausted"
        if re.search(r'quota\s+(exhausted|exceeded|depleted)', output, re.IGNORECASE):
            log("Quota exhausted detected!", "ERROR")
            return False, "Quota exhausted"
        
        quota_match = re.search(r'quota[:\s]+(\d+)\s*/\s*(\d+)', output, re.IGNORECASE)
        if quota_match:
            used = int(quota_match.group(1))
            total = int(quota_match.group(2))
            percentage = (used / total) * 100 if total > 0 else 0
            
            if percentage > 90:
                log(f"Quota critically low: {used}/{total} ({percentage:.1f}%)", "WARN")
                return False, f"Quota low: {percentage:.1f}%"
            elif percentage > 75:
                log(f"Quota warning: {used}/{total} ({percentage:.1f}%)", "WARN")
        
        return True, "Quota OK"
        
    except subprocess.TimeoutExpired:
        log("openclaw status timeout", "WARN")
        return True, "Status check timeout"
    except Exception as e:
        log(f"Failed to check quota: {e}", "ERROR")
        return True, "Status check failed"


def send_whatsapp_alert(message: str):
    """发送 WhatsApp 报警"""
    if not WHATSAPP_ADMIN:
        log("WhatsApp admin phone not configured, skipping alert", "WARN")
        return
    
    try:
        # 使用 openclaw CLI 发送消息
        result = subprocess.run(
            [
                "openclaw", "message", "send",
                "--channel", "whatsapp",
                "--target", WHATSAPP_ADMIN,
                "--message", f"🚨 Guardian Alert:\n{message}"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            log(f"WhatsApp alert sent to {WHATSAPP_ADMIN}", "INFO")
        else:
            log(f"Failed to send WhatsApp alert: {result.stderr}", "ERROR")
            
    except Exception as e:
        log(f"WhatsApp alert error: {e}", "ERROR")


def run_command(cmd: list[str], timeout: int = 30) -> tuple[bool, str]:
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def restart_gateway() -> bool:
    """尝试重启 Gateway"""
    log("Attempting gateway restart...", "INFO")
    success, output = run_command(["openclaw", "gateway", "restart"])
    if success:
        log("Gateway restart successful", "INFO")
    else:
        log(f"Gateway restart failed: {output}", "ERROR")
    return success


def switch_model(model: str) -> bool:
    """切换到指定模型"""
    log(f"Switching model to: {model}", "INFO")
    success, output = run_command(["openclaw", "models", "set", model])
    if success:
        log(f"Model switched to {model}", "INFO")
    else:
        log(f"Model switch failed: {output}", "ERROR")
    return success


def get_next_model(state: dict) -> str | None:
    """获取下一个可用的模型"""
    current_index = state.get("current_model_index", 0)
    next_index = (current_index + 1) % len(MODEL_FALLBACK_ORDER)
    state["current_model_index"] = next_index
    return MODEL_FALLBACK_ORDER[next_index]


# ==================== 主逻辑 ====================

def main():
    log("Guardian check started", "INFO")
    
    state = load_state()
    
    # 检查冷却时间
    last_action = state.get("last_action_time", 0)
    if time.time() - last_action < COOLDOWN_MINUTES * 60:
        log(f"In cooldown period, skipping (last action {int((time.time() - last_action) / 60)} min ago)", "INFO")
        return
    
    # 1. 检测配额
    quota_ok, quota_msg = check_quota()
    if not quota_ok:
        state["quota_warnings"] = state.get("quota_warnings", 0) + 1
        alert_msg = f"Quota issue detected: {quota_msg}\nTotal warnings: {state['quota_warnings']}"
        log(alert_msg, "WARN")
        send_whatsapp_alert(alert_msg)
        save_state(state)
        return
    
    # 2. 检测复读
    if check_repetition():
        state["repeat_detections"] = state.get("repeat_detections", 0) + 1
        alert_msg = f"Repetition detected in recent messages!\nTotal detections: {state['repeat_detections']}"
        log(alert_msg, "WARN")
        send_whatsapp_alert(alert_msg)
        # 复读可能需要重启
        restart_gateway()
        state["last_action_time"] = time.time()
        save_state(state)
        return
    
    # 3. 检测是否当机
    if not is_agent_frozen():
        log("Agent is responsive, all good!", "INFO")
        return
    
    # ========== 熔断流程 ==========
    log("🚨 INITIATING FAILOVER SEQUENCE 🚨", "ERROR")
    
    # Step 1: 尝试重启
    state["restart_count"] = state.get("restart_count", 0) + 1
    if restart_gateway():
        alert_msg = f"Agent was frozen. Gateway restarted successfully.\nRestart count: {state['restart_count']}"
        log(alert_msg, "WARN")
        send_whatsapp_alert(alert_msg)
        state["last_action_time"] = time.time()
        save_state(state)
        return
    
    # Step 2: 切换模型
    next_model = get_next_model(state)
    if next_model:
        state["switch_count"] = state.get("switch_count", 0) + 1
        if switch_model(next_model):
            log(f"Switched to {next_model}, attempting restart...", "WARN")
            restart_gateway()
            alert_msg = f"Agent frozen. Switched to {next_model}.\nStats: restarts={state['restart_count']}, switches={state['switch_count']}"
            send_whatsapp_alert(alert_msg)
    
    state["last_action_time"] = time.time()
    save_state(state)
    
    # Step 3: 最终报警
    final_alert = f"⚠️ CRITICAL: Agent failover attempted.\nModel: {next_model}\nRestarts: {state['restart_count']}\nSwitches: {state['switch_count']}"
    log(final_alert, "ERROR")
    send_whatsapp_alert(final_alert)


if __name__ == "__main__":
    main()
