import asyncio
from typing import Dict

import httpx

from . import config

_semaphore_websearch = asyncio.Semaphore(50)  # 网络搜索最大并发


async def call_web_search(
        query: str,
        freshness: str,
        summary: bool = True,
        count: int = 10,
        timeout: float = config.websearch_timeout
) -> Dict:
    """
    异步调用 Web Search API（兼容 httpx）

    Args:
        query: 搜索关键词
        summary: 是否返回摘要（默认 True）
        count: 返回结果数量（默认 10）
        timeout: 请求超时时间（默认 60秒）
        freshness: 搜索指定时间范围内的网页 [noLimit,oneDay,oneWeek,oneMonth,oneYear]

    Returns:
        (数据清洗后的)字典，若出错则包含 error 字段, 成功为 success 字段
    """
    headers = {
        "Authorization": f"Bearer {config.websearch_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "summary": summary,
        "count": count,
        "freshness": freshness,
    }
    async with _semaphore_websearch:
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    config.websearch_base_url,
                    headers=headers,
                    json=payload  # httpx 会自动序列化字典为 JSON
                )
                response.raise_for_status()
                raw_data = response.json()
                data = {}
                _ids = 0
                for d in raw_data['data']["webPages"]["value"]:
                    # 数据清洗, 字段更易于阅读
                    data[_ids] = f"标题: {d['name']}\n, url: {d['url']}, 总结: {d['summary']}"
                    _ids += 1
                return {"success": data}
            except httpx.TimeoutException:
                return {"error": "请求超时"}
            except httpx.HTTPStatusError as e:
                return {"error": f"HTTP 错误 {e.response.status_code}: {e.response.text}"}
            except KeyError as e:
                return {"error": f"keyError: {e}"}
            except Exception as e:
                return {"error": f"请求异常: {str(e)}"}


async def run_code_in_e2b(code: str, requirements: list, timeout: int = 120):
    await _bucket_e2b.acquire()
    async with _semaphore_e2b:
        try:
            if config.e2b_api_url != "" and config.e2b_api_url is not None:
                sandbox = await asyncio.wait_for(
                    AsyncSandbox.create(api_key=config.e2b_api_key, api_url=config.e2b_api_url, timeout=timeout),
                    timeout=60)
            else:
                sandbox = await asyncio.wait_for(
                    AsyncSandbox.create(api_key=config.e2b_api_key, timeout=timeout),
                    timeout=60)
        except asyncio.TimeoutError as e:
            logger.error(f"fail to create sandbox: TimeoutError: {e}")
            return -1
        except Exception as e:
            logger.error(f"fail to create sandbox: Exception: {e}")
            return -1

        if len(requirements) != 0:
            cmds = f"pip install {' '.join(requirements)}"
            await sandbox.commands.run(cmds, timeout=timeout)

        exec_codes = await sandbox.run_code(code)
        await sandbox.kill()
        return exec_codes.logs.stdout


def get_current_time():
    """
    获取当前的系统时间，格式为：YYYY-MM-DD HH:MM:SS
    例如：2025-03-07 14:30:00
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
