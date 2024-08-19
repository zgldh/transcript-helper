import json
import os
import subprocess
import gradio as gr

# Load from env, default 127.0.0.1
funasrHost = os.environ.get("FUNASR_HOST", "127.0.0.1")
funasrPort = os.environ.get("FUNASR_PORT", "10095")
ollamaEndpoint = os.environ.get("OLLAMA_ENDPOINT", "127.0.0.1:11434")
ollamaModel = os.environ.get("OLLAMA_MODEL", "llama3.1")
defaultPrompt = os.environ.get(
    "DEFAULT_PROMPT",
    """请仔细分析上述口头对话录音，并按照以下类别进行详细总结：
1. **主题概述**：识别对话的主要主题或议题，并给出简短描述。
2. **关键观点**：列出对话中每个参与者的主要观点或论据。
3. **问题与解决方案**：识别对话中提出的问题以及提出的解决方案或建议。
4. **情感倾向**：分析对话中的情感色彩，如积极、消极或中立，并指出哪些部分体现了这些情感。
5. **决策与行动**：总结对话中做出的任何决定或计划采取的行动。
6. **未解决的问题**：指出对话中尚未解决或需要进一步讨论的问题。
7 **其他**: 上述总结中没有包含到的对话部分，用精炼的语言总结出来。
请确保总结中包含所有关键信息，同时去除重复或不相关的细节。总结应该清晰、有条理，并易于理解。对话中可能有多个主题，不要遗漏任何一个。""",
)


def transcript(files):
    # Change files name to "audio.mp3"
    parts = files.split("/")
    parts[-1] = "audio.mp3"
    newFile = "/".join(parts)
    os.rename(files, newFile)

    # Call another python script to get the transcript
    cmd = [
        "python",
        "funasr_wss_client.py",
        "--host",
        funasrHost,
        "--port",
        funasrPort,
        "--mode",
        "offline",
        "--ssl",
        "0",
        "--audio_in",
        newFile,
    ]
    print("Starting transcription process... " + newFile)

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    print("Transcription completed.")

    # Get string between "|start|" and "|end|"
    transcriptContent = result.stdout.split("|start|")[1].split("|end|")[0]

    return transcriptContent


summarizedContent = ""
def summarize(raw_text, prompt):
    if raw_text == "":
        return "请先上传音频，得到转写文本。"
    promptPayload = raw_text + " " + prompt
    payload = json.dumps(
        {
            "model": ollamaModel,
            "stream": True,
            "prompt": promptPayload,
            "options": {"num_ctx": 32000},
        }
    )
    cmd = [
        "curl",
        "http://" + ollamaEndpoint + "/api/generate",
        "-d",
        payload,
    ]
    summarizedContent = ""
    print("Starting transcription process... ")
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # 循环读取输出
    try:
        while True:
            # 读取一行输出
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(output.strip())  # 打印输出，去掉末尾的换行符
                data = json.loads(output.strip())
                summarizedContent += data["response"]
                yield summarizedContent
    except KeyboardInterrupt:
        # 处理键盘中断，例如Ctrl+C
        process.kill()
        summarizedContent += "\nInterrupted"
        yield summarizedContent
    finally:
        # 等待进程结束
        process.wait()
        print("Transcription completed. ")
        summarizedContent += "\n(End)"
        yield summarizedContent


with gr.Blocks() as demo:
    gr.Markdown("上传音频文件，生成转写文本，并且做出总结。")
    with gr.Column():
        with gr.Row():
            audioUpload = gr.Audio(
                label="上传音频文件",
                sources=["upload"],
                interactive=True,
                editable=False,
                type="filepath",
                format="mp3",
            )
            promptTextarea = gr.TextArea(
                label="总结提示词",
                type="text",
                value=defaultPrompt,
            )
        transcriptTextarea = gr.TextArea(
            label="转写",
            type="text",
        )
        summaryTextarea = gr.Markdown(label="总结", show_label=True)
        reSummaryButton = gr.Button(
            "重新总结",
            variant="primary",
        )

    audioUpload.upload(transcript, audioUpload, transcriptTextarea)
    transcriptTextarea.change(
        summarize, [transcriptTextarea, promptTextarea], summaryTextarea
    )
    reSummaryButton.click(
        summarize, [transcriptTextarea, promptTextarea], summaryTextarea
    )

demo.launch()
