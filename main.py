import json
import os
import re
import subprocess
import gradio as gr
from ollama import Client
import ollama

version = "1.4"

# Load from env, default 127.0.0.1
funasrHost = os.environ.get("FUNASR_HOST", "127.0.0.1")
funasrPort = os.environ.get("FUNASR_PORT", "10095")
funasrSSL = os.environ.get("FUNASR_SSL", "0")
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

ollamaClient = Client(host="http://" + ollamaEndpoint)


def format_millis_to_time(millis):
    seconds, millis = divmod(millis, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


# Get text_seg and remove all inner spaces between CJK characters.
def remove_cjk_spaces(text):
    # 使用正则表达式匹配CJK字符之间的空格，并将其替换为空字符串
    return re.sub(r'(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]) ', '', text)

transcriptContent = ""

def transcript(files):
    # Change files name to "audio.mp3"
    newFile = os.path.dirname(files) + "/" + "audio.mp3"
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
        funasrSSL,
        "--audio_in",
        newFile,
    ]
    transcriptContent = ""
    print("Starting transcription process... " + newFile)

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    rows = json.loads(result.stdout.split("|||end|||")[0])
    # Loop rows
    for data in rows:
        # data["start"] is in milliseconds, convert to hh:mm:ss format
        startTime = format_millis_to_time(data["start"])
        # Get text_seg and remove all inner spaces between CJK characters.
        text = remove_cjk_spaces(data["text_seg"])
        punc = data["punc"]
        if text != "":
            # Add start time to text
            text = startTime + " " + text + punc
            # Add text to result
            transcriptContent += text + "\n"

    print("Transcription completed.")
    return transcriptContent


summarizedContent = ""


def summarize(raw_text, prompt):
    if raw_text == "":
        return "请先上传音频，得到转写文本。"
    promptPayload = raw_text + " " + prompt
    summarizedContent = ""

    print("Starting summarize process... ")
    try:
        stream = ollamaClient.generate(
            model=ollamaModel,
            prompt=promptPayload,
            stream=True,
            options={"num_ctx": 64000},
        )

        for chunk in stream:
            summarizedContent += chunk["response"]
            yield summarizedContent
    except ollama.ResponseError as e:
        print("Error:", e.error)
        summarizedContent += e.error
        yield summarizedContent


with gr.Blocks(title="Transcript Helper " + version) as demo:
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
