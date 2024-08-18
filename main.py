import json
from pathlib import Path
import subprocess
import gradio as gr

funasrHost = "127.0.0.1"
funasrPort = "10095"
ollamaEndpoint = "127.0.0.1:11434"
defaultPrompt = "请凝练总结出上述文本内容。要有条理，用语准确精练。"


def transcript(files):
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
        files,
    ]
    print("Starting transcription process... " + files)

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    print("Transcription completed.")
    print(result.stdout)

    # Get string between "|start|" and "|end|"
    transcriptContent = result.stdout.split("|start|")[1].split("|end|")[0]

    return transcriptContent


def summarize(raw_text, prompt):
    # curl http://localhost:11434/api/generate -d '{"model":"llama3.1","stream":false,"prompt":"xxxx"}'
    promptPayload = raw_text + " " + prompt
    cmd = [
        "curl",
        "http://" + ollamaEndpoint + "/api/generate",
        "-d",
        '{"model":"llama3.1","stream":false,"prompt":"' + promptPayload + '"}',
    ]
    print("Starting transcription process... ")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    print("Transcription completed. ")
    data = json.loads(result.stdout)
    return data["response"]


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
                waveform_options={"sample_rate": 16000},
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
        summaryTextarea = gr.TextArea(
            label="总结",
            type="text",
        )

    audioUpload.upload(transcript, audioUpload, transcriptTextarea)
    transcriptTextarea.change(
        summarize, [transcriptTextarea, promptTextarea], summaryTextarea
    )

demo.launch()
