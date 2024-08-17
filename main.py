import gradio as gr 
def transcriptAndSummarize(audioPath: str):
    return audioPath


demo = gr.Interface(
    fn=transcriptAndSummarize,
    inputs=gr.Audio(
        label="音频文件",
        type="filepath",
        interactive=True,
    ),
    outputs=[
        gr.TextArea(
            label="转写",
            type="text",
        ),
        gr.TextArea(
            label="总结",
            type="text",
        ),
        ],
)
demo.launch()
