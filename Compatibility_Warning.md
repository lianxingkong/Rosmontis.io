# 兼容性问题

这里汇总了所有使用 非 onebot 接口的接口, 存在过时风险

## get_private_file_url

### 调用

参数: `file_id`: 文件唯一ID, 可以通过 `nonebot.adapters.onebot.v11.MessageEvent` 获取

期望的返回值: { "url": 文件可供下载的url, 字符串 }

### 受到影响的内容

`src/plugins/self_build_tts/message_handle.py`

1. function : qwen3_clone_got_ref_aud bot.call_api调用
2. function : qwen3_gen_got_file_obj bot.call_api调用

### 引入的依据

[napcat doc](https://napneko.github.io/onebot/api#%E6%96%87%E4%BB%B6%E7%9B%B8%E5%85%B3)