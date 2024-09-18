from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("."))
template_html = env.get_template('template_html.j2')
OPENAI_MODEL = "gpt-4o"