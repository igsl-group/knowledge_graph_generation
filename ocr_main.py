#!/usr/bin/python3

from absl import flags, app
import gradio as gr
from paddleocr import PPStructureV3

FLAGS = flags.FLAGS

def add_options():
  flags.DEFINE_string('host', default = '0.0.0.0', help = 'service host')
  flags.DEFINE_integer('port', default = 8081, help = 'service port')

def do_ocr(files, progress = gr.Progress()):
  pipeline = PPStructureV3()
  results = list()
  for f in progress.tqdm(files):
    output = pipeline.predict(input = f)
    markdown_list = []
    for res in output:
      md_info = res.markdown
      markdown_list.append(md_info)
    markdown = pipeline.concatenate_markdown_pages(markdown_list)
    results.append({'file_path': f, 'markdown': markdown})
  return results

def create_interface():
  with gr.Blocks() as demo:
    with gr.Column():
      with gr.Row(equal_height = True):
        files = gr.Files(label = 'files to upload', scale = 3)
        ocr_btn = gr.Button('ocr', scale = 1)
      with gr.Row():
        results = gr.JSON()
    ocr_btn.click(do_ocr, inputs = [files], outputs = [results], concurrency_limit = 64)
  return demo

def main(unused_argv):
  demo = create_interface()
  demo.launch(server_name = FLAGS.host,
              server_port = FLAGS.port,
              share = False,
              show_error = True,
              max_threads = 64)

if __name__ == "__main__":
  add_options()
  app.run(main)

